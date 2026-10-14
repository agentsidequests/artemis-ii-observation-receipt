param([switch]$WriteAbsent)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$contract = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract.json') -Raw | ConvertFrom-Json -DateKind String
$result = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'result.json') -Raw | ConvertFrom-Json -DateKind String
function Require($condition, $message) { if (-not $condition) { throw $message } }
function Near($actual, $expected, $message) { Require ([math]::Abs($actual - $expected) -le 1e-10 * [math]::Max(1, [math]::Abs($expected))) $message }
foreach ($pin in $contract.input_pins) {
    $path = Join-Path $taskRoot $pin.path
    Require ((Get-Item -LiteralPath $path).Length -eq $pin.bytes) "Input length changed: $($pin.path)"
    Require ((Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ceq $pin.sha256) "Input hash changed: $($pin.path)"
}
$sourcePath = Join-Path $taskRoot 'src/camera_sequence_downstream_sensitivity.py'
Require ((Get-FileHash -LiteralPath $sourcePath).Hash.ToLowerInvariant() -ceq $result.provenance.source_sha256) 'Wrapper bytes differ from the receipt'
$manifest = @(Import-Csv -LiteralPath (Join-Path $taskRoot 'results/stage10o-product-relationship-manifest.csv'))
$assignments = @(Import-Csv -LiteralPath (Join-Path $taskRoot 'results/stage11l-split-assignments.csv'))
$memberships = @(Import-Csv -LiteralPath (Join-Path $taskRoot 'results/stage10z-action-plan-membership.csv'))
$witnesses = @(Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'withheld-products.csv'))
$products = [System.Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
$assigned = [System.Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach ($row in $manifest) { $products.Add($row.product_id, $row) }
foreach ($row in $assignments) { $assigned.Add($row.product_id, $row) }
Require ($products.Count -eq $assigned.Count) 'Manifest/assignment population mismatch'
foreach ($row in $manifest) {
    Require ($assigned.ContainsKey($row.product_id)) 'Missing assignment'
    foreach ($field in @('capture_identity', 'action_id', 'temporal_cluster_5s')) {
        Require ($row.$field -ceq $assigned[$row.product_id].$field) 'Relationship field changed'
    }
}
$removed = @($manifest | Where-Object action_id -CEQ $contract.action_id)
$retained = @($manifest | Where-Object action_id -CNE $contract.action_id)
$retainedAssignments = @($assignments | Where-Object action_id -CNE $contract.action_id)
$retainedMemberships = @($memberships | Where-Object action_id -CNE $contract.action_id)
Require ($manifest.Count -eq 22818 -and $retained.Count -eq 22803 -and $removed.Count -eq 15 -and $witnesses.Count -eq 15) 'Wrong withholding population'
$witnessIds = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($row in $witnesses) {
    Require ($witnessIds.Add($row.product_id)) 'Duplicate witness'
    Require ($products.ContainsKey($row.product_id)) 'Invented witness'
    Require ($row.action_id -ceq $contract.action_id) 'Wrong witness action'
    foreach ($field in $manifest[0].PSObject.Properties.Name) {
        Require ($row.$field -ceq $products[$row.product_id].$field) "Witness field changed: $field"
    }
    foreach ($field in @('product_key_partition', 'action_key_partition', 'temporal_5s_key_partition')) {
        Require ($row.$field -ceq $assigned[$row.product_id].$field) 'Original partition field changed'
    }
}
foreach ($row in $removed) { Require ($witnessIds.Contains($row.product_id)) 'Omitted removal witness' }
foreach ($key in $contract.capture_keys) {
    $layers = @($removed | Where-Object capture_identity -CEQ $key)
    Require ($layers.Count -eq 3) 'Wrong capture multiplicity'
    foreach ($tier in @('data_source', 'data_raw', 'data_processed')) {
        Require (@($layers | Where-Object collection_id -CEQ $tier).Count -eq 1) 'Wrong representation multiplicity'
    }
}
$trainCaptures = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$trainActions = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($row in $retainedAssignments) {
    if ($row.product_key_partition -ceq 'train') {
        [void]$trainCaptures.Add($row.capture_identity)
        [void]$trainActions.Add($row.action_id)
    }
}
$bins = [ordered]@{test_products=0; capture_linked_test_products=0; action_only_linked_test_products=0; action_isolated_test_products=0}
foreach ($row in $retainedAssignments) {
    if ($row.product_key_partition -cne 'test') { continue }
    $bins.test_products++
    if ($trainCaptures.Contains($row.capture_identity)) { $bins.capture_linked_test_products++ }
    elseif ($trainActions.Contains($row.action_id)) { $bins.action_only_linked_test_products++ }
    else { $bins.action_isolated_test_products++ }
}
foreach ($field in $bins.Keys) { Require ($bins[$field] -eq $result.conditional_withheld.relationship.$field) "Relationship recount differs: $field" }
$source = @($retained | Where-Object collection_id -CEQ 'data_source')
$tagged = @($source | Where-Object { $_.target_id -cne '' })
$sunset = @($source | Where-Object target_id -CEQ 'Sunset')
$coverage = $result.conditional_withheld.selection.coverage
Require ($source.Count -eq $coverage.source_exposures -and $tagged.Count -eq $coverage.target_tag_present -and ($source.Count - $tagged.Count) -eq $coverage.target_tag_blank -and $sunset.Count -eq $coverage.sunset_tagged_exposures) 'Source field recount differs'
$actions = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$selectedActions = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$sunsetActions = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($row in $source) { [void]$actions.Add($row.action_id) }
foreach ($row in $tagged) { [void]$selectedActions.Add($row.action_id) }
foreach ($row in $sunset) { [void]$sunsetActions.Add($row.action_id) }
Require ($actions.Count -eq 2165 -and $source.Count -eq 7601) 'Retained action/key count differs'
$panel = $result.conditional_withheld.selection_weighting.strict_tagged_weighting_panel
Near ($sunsetActions.Count / $selectedActions.Count) $panel.sunset_share_of_selected_actions 'Action share differs'
$tierBytes = [ordered]@{}
$removedBytes = [ordered]@{}
[long]$allSelectedBytes = 0
[long]$allSunsetBytes = 0
foreach ($tier in @('data_source', 'data_raw', 'data_processed')) {
    [long]$selectedBytes = 0
    [long]$sunsetBytes = 0
    [long]$withheldBytes = 0
    foreach ($row in $retained) {
        if ($row.collection_id -ceq $tier -and $row.target_id -cne '') {
            $selectedBytes += [long]$row.archive_size_bytes
            if ($row.target_id -ceq 'Sunset') { $sunsetBytes += [long]$row.archive_size_bytes }
        }
    }
    foreach ($row in $removed) { if ($row.collection_id -ceq $tier) { $withheldBytes += [long]$row.archive_size_bytes } }
    $removedBytes[$tier] = $withheldBytes
    Require ($withheldBytes -eq $result.removal.bytes_by_collection.$tier) 'Removed bytes differ'
    $tierBytes[$tier] = [ordered]@{selected=$selectedBytes; sunset=$sunsetBytes; sunset_share=$sunsetBytes / $selectedBytes}
    Near ($sunsetBytes / $selectedBytes) $result.conditional_withheld.selection_weighting.collection_byte_sensitivity.$tier.sunset_share 'Tier byte share differs'
    $allSelectedBytes += $selectedBytes
    $allSunsetBytes += $sunsetBytes
}
Require ($allSelectedBytes -eq $panel.tagged_archive_size_bytes -and $allSunsetBytes -eq $panel.sunset_tagged_archive_size_bytes) 'Selected byte totals differ'
Near ($allSunsetBytes / $allSelectedBytes) $panel.sunset_share_of_tagged_bytes 'Combined byte share differs'
$bounds = $result.conditional_withheld.field_completion.sunset
Near ($sunset.Count / $source.Count) $bounds.lower_share_full_cohort 'Lower completion bound differs'
Near (($sunset.Count + $source.Count - $tagged.Count) / $source.Count) $bounds.upper_share_full_cohort 'Upper completion bound differs'
$majorityNeeded = [math]::Floor($source.Count / 2) + 1 - $sunset.Count
Require ($majorityNeeded -eq $result.conditional_withheld.field_completion.sunset_majority.additional_blank_memberships_needed) 'Majority tipping point differs'
$windows = @($retainedMemberships | Where-Object { $_.plan_order -cne '' } | Group-Object plan_order)
Require ($windows.Count -eq 36) 'Active window count changed'
$originalMembership = @($memberships | Where-Object action_id -CEQ $contract.action_id)
Require ($originalMembership.Count -eq 2 -and @($originalMembership | Where-Object plan_order -CEQ '28').Count -eq 1 -and @($originalMembership | Where-Object plan_order -CEQ '29').Count -eq 1) 'Original overlap differs'
Require (@($originalMembership | Where-Object plan_target_name -CNE 'Moon').Count -eq 0) 'Affected plan target differs'
$record = [ordered]@{
    status='VERIFIED_IMPLEMENTATION_DIVERSE_ROW_RECOUNT'
    verified_input_pins=$contract.input_pins.Count
    exact_witness_rows=$witnesses.Count
    retained_products=$retained.Count
    retained_capture_keys=$source.Count
    retained_actions=$actions.Count
    relationship_bins=$bins
    source_field_counts=[ordered]@{tagged=$tagged.Count; blank=$source.Count-$tagged.Count; sunset=$sunset.Count}
    selected_action_counts=[ordered]@{selected=$selectedActions.Count; sunset=$sunsetActions.Count}
    selected_bytes_by_tier=$tierBytes
    removed_bytes_by_tier=$removedBytes
    combined_selected_bytes=$allSelectedBytes
    combined_sunset_bytes=$allSunsetBytes
    completion_majority_needed=$majorityNeeded
    retained_active_windows=$windows.Count
    affected_original_plan_orders=@('28','29')
    independence_limit='Native CSV field, identity, split-bin, count, byte, share, bound and overlap recount only. Does not independently reconstruct camera paths, derive concentration/cluster formulas or validate physical identity, content labels or scientific acceptance.'
    script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash.ToLowerInvariant()
}
$payload = [Text.UTF8Encoding]::new($false).GetBytes(($record | ConvertTo-Json -Depth 8).Replace("`r`n", "`n") + "`n")
$outputPath = Join-Path $PSScriptRoot 'native-crosscheck.json'
if (Test-Path -LiteralPath $outputPath) {
    Require ([Convert]::ToBase64String([IO.File]::ReadAllBytes($outputPath)) -ceq [Convert]::ToBase64String($payload)) 'Existing native receipt differs; refusing overwrite'
} elseif ($WriteAbsent) {
    $stream = [IO.File]::Open($outputPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    try { $stream.Write($payload, 0, $payload.Length) } finally { $stream.Dispose() }
} else { throw 'Native receipt absent; use -WriteAbsent after reviewing scope' }
$record | ConvertTo-Json -Depth 8
