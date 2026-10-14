param([switch]$Check)
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskContract = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract.json') -Raw | ConvertFrom-Json
$taskResult = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'result.json') -Raw | ConvertFrom-Json
$taskPath = Join-Path $taskRoot $taskContract.source.path
$taskDigest = (Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ((Get-Item -LiteralPath $taskPath).Length -ne $taskContract.source.bytes -or $taskDigest -ne $taskContract.source.sha256) {
    throw 'Native oracle source identity mismatch'
}
function Sum-Weights($items) {
    [decimal]$sum = 0
    foreach ($item in $items) { $sum += [decimal]$item }
    return $sum
}
function Assert-Equal($actual, $expected, $label) {
    if ($actual -ne $expected) { throw "Native mismatch: $label" }
}
$taskRows = @(Import-Csv -LiteralPath $taskPath)
Assert-Equal $taskRows.Count 22818 'product count'
Assert-Equal (@($taskRows.product_id | Select-Object -Unique).Count) 22818 'unique products'
$taskFields = @($taskRows | Group-Object capture_identity | ForEach-Object {
    $group = $_.Group
    if ($group.Count -ne 3) { throw 'Incomplete native representation group' }
    $source = @($group | Where-Object collection_id -eq 'data_source')
    $raw = @($group | Where-Object collection_id -eq 'data_raw')
    $processed = @($group | Where-Object collection_id -eq 'data_processed')
    if ($source.Count -ne 1 -or $raw.Count -ne 1 -or $processed.Count -ne 1) { throw 'Native representation parity failure' }
    if (@($group.target_id | Select-Object -Unique).Count -ne 1) { throw 'Native target conflict' }
    [pscustomobject]@{
        identity=$_.Name; target=$source[0].target_id
        exposure_fields=[decimal]1; products=[decimal]3
        data_source_bytes=[decimal]$source[0].archive_size_bytes
        data_raw_bytes=[decimal]$raw[0].archive_size_bytes
        data_processed_bytes=[decimal]$processed[0].archive_size_bytes
        all_representation_bytes=(Sum-Weights $group.archive_size_bytes)
    }
})
Assert-Equal $taskFields.Count 7606 'exposure fields'
Assert-Equal (@($taskFields | Where-Object target -eq '').Count) 4193 'blank fields'
Assert-Equal (@($taskFields | Where-Object target -eq 'Sunset').Count) 1553 'Sunset fields'
$taskChecks = 0
$taskSummaries = foreach ($taskUnit in $taskContract.units) {
    $all = @($taskFields)
    $known = @($all | Where-Object target -ne '')
    $positive = @($all | Where-Object target -eq 'Sunset' | Sort-Object @{Expression={$_.$taskUnit};Descending=$true}, identity)
    $negative = @($all | Where-Object { $_.target -ne '' -and $_.target -ne 'Sunset' } | Sort-Object @{Expression={$_.$taskUnit};Descending=$true}, identity)
    $blanks = @($all | Where-Object target -eq '' | Sort-Object @{Expression={$_.$taskUnit};Descending=$true}, identity)
    $total = Sum-Weights $all.$taskUnit
    $taggedTotal = Sum-Weights $known.$taskUnit
    $sunsetTotal = Sum-Weights $positive.$taskUnit
    $blankTotal = Sum-Weights $blanks.$taskUnit
    $saved = @($taskResult.units | Where-Object unit -eq $taskUnit)[0]
    Assert-Equal $total $saved.completion.total_weight "$taskUnit total"
    Assert-Equal $sunsetTotal $saved.completion.known_target_weight "$taskUnit known target"
    Assert-Equal $blankTotal $saved.completion.blank_weight "$taskUnit blank"
    Assert-Equal ($sunsetTotal + $blankTotal) $saved.completion.upper.numerator "$taskUnit completion upper"
    Assert-Equal $taggedTotal $saved.selected.total_weight "$taskUnit frozen selection"
    $remaining = $sunsetTotal
    $picked = 0
    $previous = $null
    foreach ($f in $positive) {
        if (2*$remaining -le $taggedTotal) { break }
        $previous = $remaining
        $remaining -= $f.$taskUnit
        $picked++
    }
    Assert-Equal $picked $saved.majority_sensitivity.minimum_fields_to_lose_strict_majority "$taskUnit majority minimum"
    Assert-Equal $remaining $saved.majority_sensitivity.after.numerator "$taskUnit majority endpoint"
    if ($picked -gt 0) {
        if (2*$previous -le $taggedTotal -or 2*$remaining -gt $taggedTotal) { throw 'Native majority predecessor failure' }
        Assert-Equal (($positive | Select-Object -First $picked).identity -join '|') ($saved.majority_sensitivity.reassigned_ids -join '|') "$taskUnit witness identities"
    }
    $budgets = foreach ($target in $taskContract.completion_width_targets) {
        $unresolved = $blankTotal
        $count = 0
        $prior = $null
        foreach ($f in $blanks) {
            if ($unresolved*$target.denominator -le $total*$target.numerator) { break }
            $prior = $unresolved
            $unresolved -= $f.$taskUnit
            $count++
        }
        $budgetSaved = $saved.completion_budgets.($target.name)
        Assert-Equal $count $budgetSaved.minimum_fields_resolved_equal_field_cost "$taskUnit width minimum"
        Assert-Equal $unresolved $budgetSaved.remaining_width.numerator "$taskUnit residual mass"
        if ($count -gt 0 -and $prior*$target.denominator -le $total*$target.numerator) { throw 'Native width predecessor failure' }
        [pscustomobject]@{name=$target.name;minimum_fields=$count;remaining_unknown_weight=$unresolved}
    }
    foreach ($r in $taskContract.recorded_field_reassignment_budgets) {
        $down = Sum-Weights (@($positive | Select-Object -First $r).$taskUnit)
        $up = Sum-Weights (@($negative | Select-Object -First $r).$taskUnit)
        foreach ($population in @('full_cohort','frozen_nonblank_subset')) {
            $savedInterval = @($taskResult.reassignment_sensitivity | Where-Object { $_.unit -eq $taskUnit -and $_.population -eq $population -and $_.reassignment_budget -eq $r })
            Assert-Equal $savedInterval.Count 1 'unique interval'
            $unknownMass = if ($population -eq 'full_cohort') { $blankTotal } else { [decimal]0 }
            Assert-Equal ($sunsetTotal-$down) $savedInterval[0].lower.numerator 'sensitivity lower'
            Assert-Equal ($sunsetTotal+$unknownMass+$up) $savedInterval[0].upper.numerator 'sensitivity upper'
            $taskChecks++
        }
    }
    [pscustomobject]@{unit=$taskUnit;total_weight=$total;known_target_weight=$sunsetTotal;blank_weight=$blankTotal;
        selected_weight=$taggedTotal;minimum_fields_to_lose_strict_majority=$picked;after_majority_weight=$remaining;
        completion_budgets=@($budgets)}
}
$taskNative = [ordered]@{
    pass=$true;source_sha256=$taskDigest;source_products=$taskRows.Count;exposure_fields=$taskFields.Count
    unit_count=@($taskSummaries).Count;sensitivity_interval_checks=$taskChecks;units=@($taskSummaries)
    arithmetic='PowerShell decimal sums, native CSV grouping and sorting; no imported Python functions'
    independence='Partial: shared source and membership/weight assumptions; implementation-diverse recount, not independent scientific validation'
    new_pixel_bytes_opened=0
}
$taskText = ($taskNative | ConvertTo-Json -Depth 8) + "`n"
$taskNativePath = Join-Path $PSScriptRoot 'native-crosscheck.json'
if ($Check) {
    if (-not (Test-Path -LiteralPath $taskNativePath) -or (Get-Content -LiteralPath $taskNativePath -Raw) -cne $taskText) {
        throw 'Native crosscheck saved-artifact drift'
    }
} else {
    [IO.File]::WriteAllText($taskNativePath, $taskText, [Text.UTF8Encoding]::new($false))
}
[pscustomobject]@{pass=$true;units=$taskNative.unit_count;interval_checks=$taskChecks;mode=$(if ($Check) {'check'} else {'write'})} | ConvertTo-Json
