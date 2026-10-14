[CmdletBinding()]
param([string]$Root)

$ErrorActionPreference = 'Stop'
if (-not $Root) { $Root = Join-Path $PSScriptRoot '../..' }
$Root = [IO.Path]::GetFullPath($Root)
$path = Join-Path $Root 'results/stage10o-product-relationship-manifest.csv'
$expectedHash = '8EDD58437CC609229EDB5ABB41C4E00048BB420354F1AC17A269DA92C17E4729'
if ((Get-Item -LiteralPath $path).Length -ne 10072026 -or (Get-FileHash -LiteralPath $path).Hash -ne $expectedHash) {
    throw 'Frozen relationship manifest changed.'
}
$counts = New-Object 'System.Collections.Generic.Dictionary[string,int]' ([StringComparer]::Ordinal)
$identities = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
$total = $blank = 0
foreach ($row in (Import-Csv -LiteralPath $path -Encoding utf8)) {
    if (-not [string]::Equals($row.collection_id, 'data_source', [StringComparison]::Ordinal)) { continue }
    if (-not $row.capture_identity -or -not $identities.Add($row.capture_identity)) { throw 'Source capture is empty or repeated.' }
    $total++
    if ([string]::IsNullOrEmpty($row.target_id)) { $blank++; continue }
    if (-not $counts.ContainsKey($row.target_id)) { $counts.Add($row.target_id, 0) }
    $counts[$row.target_id]++
}
$sunset = $counts['Sunset']
if ($total -ne 7606 -or $blank -ne 4193 -or $sunset -ne 1553 -or $counts.Count -ne 23) { throw 'Frozen count oracle failed.' }
$budgets = [ordered]@{}
foreach ($denominator in @(10, 20, 100)) {
    $remaining = [Math]::Floor($total / $denominator)
    $budgets["1/$denominator"] = [ordered]@{ resolved = $blank - $remaining; remaining = $remaining }
}
$bounds = [ordered]@{}
foreach ($value in ($counts.Keys | Sort-Object -CaseSensitive)) {
    $bounds[$value] = [ordered]@{ observed = $counts[$value]; lower_count = $counts[$value]; upper_count = $counts[$value] + $blank }
}
$tipping = [int]([Math]::Floor($total / 2) + 1 - $sunset)
[ordered]@{
    oracle = 'implementation-diverse frozen-metadata recount, not independent science validation'
    powershell = $PSVersionTable.PSVersion.ToString()
    script_sha256 = (Get-FileHash -LiteralPath $PSCommandPath).Hash
    source_sha256 = $expectedHash
    source_exposures = $total; nonblank_target_fields = $total - $blank; blank_target_fields = $blank
    bounds_by_field_value = $bounds
    sunset_lower_share = $sunset / $total; sunset_upper_share = ($sunset + $blank) / $total
    sunset_strict_majority_additional_count = $tipping
    deterministic_completion_budgets = $budgets
    pixel_payloads_read = $false
} | ConvertTo-Json -Depth 6 -Compress
