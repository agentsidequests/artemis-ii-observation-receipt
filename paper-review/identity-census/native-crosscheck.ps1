$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$contract = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract.json') -Raw | ConvertFrom-Json -DateKind String
$retained = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'result.json') -Raw | ConvertFrom-Json -DateKind String
function Read-PinnedJson($path, $bytes, $sha256) {
    $resolved = Join-Path $taskRoot $path
    if ((Get-Item -LiteralPath $resolved).Length -ne $bytes -or
        (Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sha256) {
        throw "Input custody mismatch: $path"
    }
    Get-Content -LiteralPath $resolved -Raw | ConvertFrom-Json -DateKind String
}
$receiptA = Read-PinnedJson $contract.inputs[0].path $contract.inputs[0].bytes $contract.inputs[0].sha256
$receiptE = Read-PinnedJson $contract.inputs[1].path $contract.inputs[1].bytes $contract.inputs[1].sha256
$labelKeys = @(
    'img_surface:Instrument_Information/img_surface:instrument_serial_number',
    'cots_camera:File_Information/cots_camera:file_number',
    'cots_camera:Camera_Properties/cots_camera:shutter_count',
    'img:ISO/img:iso_number',
    'img:Optical_Properties/img:focal_length',
    'cots_camera:Camera_Settings/cots_camera:shooting_mode',
    'cots_camera:Exposure/cots_camera:auto_bracket_order',
    'cots_camera:Exposure/cots_camera:exposure_bracket_value'
)
$records = @(foreach ($page in (@($receiptE.atlas_pages) + @($receiptA.atlas_pages))) {
    $payload = Read-PinnedJson $page.response_path $page.response_bytes $page.response_sha256
    if ($payload.hits.total.relation -cne 'eq' -or $payload.hits.hits.Count -ne $page.hits) { throw 'Page completeness mismatch' }
    foreach ($hit in $payload.hits.hits) {
        $source = $hit._source
        if ($source.bundle_id -cne 'artemis2_crew_camera' -or $source.collection_id -cne 'data_raw') { throw 'Wrong raw scope' }
        $filename = $source.gather.pds_archive.file_name
        if ($filename -cnotmatch '^(art002e\d+)_nk[a-z0-9]+_raw_v01\.tif$' -or $hit._id.Split('/')[-1] -cne $filename) { throw 'Identifier mapping mismatch' }
        $stem = $Matches[1]
        $values = @(foreach ($name in $labelKeys) {
            $value = $source.pds4_label.$name
            if ($null -eq $value -or @($value).Count -ne 1 -or $value[0] -isnot [string] -or [string]::IsNullOrWhiteSpace($value[0])) { throw 'Unkeyable record in this frozen inventory' }
            $value[0]
        })
        $utc = $source.gather.time.start_time
        if ($utc -isnot [string] -or [string]::IsNullOrWhiteSpace($utc)) { throw 'Unkeyable recorded UTC' }
        [pscustomobject]@{
            stem = $stem; identifier = $hit._id; serial = $values[0]; file = $values[1]; shutter = $values[2]; utc = $utc
            strict_key = (ConvertTo-Json -InputObject @($values[0], $values[1], $values[2], $utc, $values[3], $values[4], $values[5], $values[6], $values[7]) -Compress)
            core_key = (ConvertTo-Json -InputObject @($values[0], $values[1], $values[2], $utc) -Compress)
            sort_key = (ConvertTo-Json -InputObject @($values[0], $(if ([int64]$values[2] -eq 0) { -1L } else { [int64]$values[2] })) -Compress)
            day = $source.pds4_label.'msn:Mission_Information/msn:flight_day_number'[0]
            target = (ConvertTo-Json -InputObject $source.pds4_label.'msn_surface:Observational_Intent/msn_surface:target_id' -Compress)
        }
    }
})
$strict = @($records | Group-Object strict_key -CaseSensitive | Where-Object Count -gt 1)
$core = @($records | Group-Object core_key -CaseSensitive | Where-Object Count -gt 1)
$ties = @($records | Group-Object sort_key -CaseSensitive | Where-Object Count -gt 1)
$manifestPin = $contract.inputs[2]
$manifestPath = Join-Path $taskRoot $manifestPin.path
if ((Get-Item -LiteralPath $manifestPath).Length -ne $manifestPin.bytes -or
    (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $manifestPin.sha256) { throw 'Manifest custody mismatch' }
$manifestRows = @(Import-Csv -LiteralPath $manifestPath)
$membership = @{}
foreach ($row in $manifestRows) { $membership[$row.capture_identity] = $true }
$byMembership = @{ '0' = 0; '1' = 0; '2' = 0 }
foreach ($group in $strict) {
    $present = @($group.Group | Where-Object { $membership.ContainsKey($_.stem) }).Count
    $byMembership[[string]$present]++
}
$checks = [ordered]@{
    raw_records = $records.Count
    unique_raw_identifiers = @($records.identifier | Sort-Object -Unique).Count
    strict_candidate_groups = $strict.Count
    strict_candidate_records = [int](($strict | Measure-Object Count -Sum).Sum)
    core_candidate_groups = $core.Count
    day4_candidate_groups = @($strict | Where-Object { $_.Group[0].day -ceq '4' }).Count
    day6_candidate_groups = @($strict | Where-Object { $_.Group[0].day -ceq '6' }).Count
    serial3920019_candidate_groups = @($strict | Where-Object { $_.Group[0].serial -ceq '3920019' }).Count
    candidate_target_conflicts = @($strict | Where-Object { @($_.Group.target | Sort-Object -Unique).Count -gt 1 }).Count
    candidate_groups_no_counted_key = $byMembership['0']
    candidate_groups_one_counted_key = $byMembership['1']
    candidate_groups_two_counted_keys = $byMembership['2']
    manifest_products = $manifestRows.Count
    manifest_capture_keys = $membership.Count
    manifest_actions = @($manifestRows.action_id | Sort-Object -Unique).Count
    tied_sort_keys = $ties.Count
    records_in_ties = [int](($ties | Measure-Object Count -Sum).Sum)
    ties_with_different_recorded_times = @($ties | Where-Object { @($_.Group.utc | Sort-Object -Unique).Count -gt 1 }).Count
    ties_with_different_file_numbers = @($ties | Where-Object { @($_.Group.file | Sort-Object -Unique).Count -gt 1 }).Count
    ties_spanning_flight_days = @($ties | Where-Object { @($_.Group.day | Sort-Object -Unique).Count -gt 1 }).Count
}
$expected = @(10329,10329,24,48,24,21,3,24,21,23,1,0,22818,7606,2166,101,222,77,77,0)
$index = 0
foreach ($check in $checks.GetEnumerator()) {
    if ($check.Value -ne $expected[$index]) { throw "Independent recount failed: $($check.Key)=$($check.Value)" }
    $index++
}
$actualPairs = @($strict | ForEach-Object { (@($_.Group.stem | Sort-Object) -join '|') } | Sort-Object)
$retainedPairs = @($retained.witnesses | ForEach-Object { (@($_.records.capture_key | Sort-Object) -join '|') } | Sort-Object)
if (@(Compare-Object $actualPairs $retainedPairs).Count -ne 0) { throw 'Retained candidate witness set differs from independent source recount' }
[ordered]@{
    status = 'PASS_IMPLEMENTATION_DIVERSE_SOURCE_RECOUNT'
    checks = $checks
    limits = 'Independently recounts frozen metadata, pair membership and numeric sort-key ties. Does not implement action reconstruction, certify physical identity or independently establish source truth.'
} | ConvertTo-Json -Depth 5
