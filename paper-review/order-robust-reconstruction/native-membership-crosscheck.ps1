$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$result = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'result.json') -Raw | ConvertFrom-Json -DateKind String
$sourceContractPath = Join-Path $taskRoot 'paper-review/identity-census/contract.json'
if ((Get-FileHash -LiteralPath $sourceContractPath).Hash.ToLowerInvariant() -cne '37ac81034766d2222fb632eba0e8ab2ca3a16c7f68e078a899716a2d3cc6e5ad') { throw 'Independent source contract changed' }
$sourceContract = Get-Content -LiteralPath $sourceContractPath -Raw | ConvertFrom-Json -DateKind String
function Read-Pinned($record) {
    $path = Join-Path $taskRoot $record.path
    if ((Get-Item -LiteralPath $path).Length -ne $record.bytes -or
        (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -cne $record.sha256) { throw "Source pin changed: $($record.path)" }
    Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -DateKind String
}
$receiptA = Read-Pinned $sourceContract.inputs[0]
$receiptE = Read-Pinned $sourceContract.inputs[1]
$sources = @{}
foreach ($page in (@($receiptE.atlas_pages) + @($receiptA.atlas_pages))) {
    $payload = Read-Pinned ([pscustomobject]@{path=$page.response_path;bytes=$page.response_bytes;sha256=$page.response_sha256})
    foreach ($hit in $payload.hits.hits) {
        if ($sources.ContainsKey($hit._id)) { throw 'Duplicate source native ID' }
        $sources[$hit._id] = $hit._source
    }
}
$fieldMap = @{
    serial='img_surface:Instrument_Information/img_surface:instrument_serial_number'
    file_number='cots_camera:File_Information/cots_camera:file_number'
    shutter_count='cots_camera:Camera_Properties/cots_camera:shutter_count'
    iso='img:ISO/img:iso_number'
    focal_length='img:Optical_Properties/img:focal_length'
    shooting_mode='cots_camera:Camera_Settings/cots_camera:shooting_mode'
    auto_bracket_order='cots_camera:Exposure/cots_camera:auto_bracket_order'
    bracket_value='cots_camera:Exposure/cots_camera:exposure_bracket_value'
    flight_day='msn:Mission_Information/msn:flight_day_number'
    activity_id='msn_surface:Observational_Intent/msn_surface:activity_id'
    target_id='msn_surface:Observational_Intent/msn_surface:target_id'
}
$patternSpec = Read-Pinned $sourceContract.inputs[4]
$allowedPatterns = @($patternSpec.expanded_patterns | ForEach-Object { $_ -join ',' })
$sourceKeyMembers = @{}
foreach ($identifier in $sources.Keys) {
    $source = $sources[$identifier]
    $keyValues = @(foreach ($field in $sourceContract.strict_fields) {
        if ($field -ceq 'utc') { $source.gather.time.start_time }
        else {
            $value = $source.pds4_label.($fieldMap[$field])
            if (@($value).Count -ne 1 -or $value[0] -isnot [string]) { throw 'Frozen source lost strict-key eligibility' }
            $value[0]
        }
    })
    $sourceKey = ConvertTo-Json -InputObject $keyValues -Compress
    if (-not $sourceKeyMembers.ContainsKey($sourceKey)) { $sourceKeyMembers[$sourceKey] = [System.Collections.Generic.HashSet[string]]::new() }
    [void]$sourceKeyMembers[$sourceKey].Add($identifier)
}
$manifestPin = $sourceContract.inputs[2]
$manifestPath = Join-Path $taskRoot $manifestPin.path
if ((Get-Item -LiteralPath $manifestPath).Length -ne $manifestPin.bytes -or
    (Get-FileHash -LiteralPath $manifestPath).Hash.ToLowerInvariant() -cne $manifestPin.sha256) { throw 'Original manifest changed' }
$manifest = @(Import-Csv -LiteralPath $manifestPath)
$baselineByCapture = @{}
$baselineByAction = @{}
foreach ($row in $manifest) {
    $baselineByCapture[$row.capture_identity] = $row.action_id
    if (-not $baselineByAction.ContainsKey($row.action_id)) { $baselineByAction[$row.action_id] = [System.Collections.Generic.HashSet[string]]::new() }
    [void]$baselineByAction[$row.action_id].Add($row.capture_identity)
}
$candidateByCapture = @{}
$candidateRows = @{}
$familyById = @{}
$nativeIds = [System.Collections.Generic.HashSet[string]]::new()
$alternatives = 0
$nativePaths = 0
foreach ($family in $result.families) {
    if ($allowedPatterns -cnotcontains ($family.slots.metadata.bracket_value -join ',')) { throw 'Unsupported bracket pattern' }
    $familyById[$family.family_id] = $family
    $nativePaths += $family.native_path_count
    $first = $family.slots[0].metadata
    $times = @()
    $product = 1
    $position = 0
    foreach ($slot in $family.slots) {
        $meta = $slot.metadata
        $slotKeyValues = @(foreach ($field in $sourceContract.strict_fields) { $meta.$field })
        $slotKey = ConvertTo-Json -InputObject $slotKeyValues -Compress
        if (-not $sourceKeyMembers.ContainsKey($slotKey) -or
            @(Compare-Object @($sourceKeyMembers[$slotKey]) @($slot.members.product_id)).Count) { throw 'A native slot alternative was omitted, added or selected' }
        $product *= $slot.members.Count
        if ($slot.members.Count -gt 1) { $alternatives++ }
        if ([int64]$meta.shutter_count -ne [int64]$first.shutter_count + $position -or
            [int64]$meta.file_number -ne [int64]$first.file_number + $position) { throw 'Nonconsecutive counter path' }
        foreach ($field in @('serial','iso','focal_length')) { if ($meta.$field -cne $first.$field) { throw 'Mixed path settings' } }
        if ($meta.auto_bracket_order -cne '0,-,+' -or -not $meta.shooting_mode.Contains('Exposure Bracketing')) { throw 'Wrong mode/order' }
        if ($meta.utc -cnotmatch '(Z|[+-]\d{2}:\d{2})$') { throw 'Unqualified UTC offset' }
        $times += [datetimeoffset]::Parse($meta.utc, [cultureinfo]::InvariantCulture)
        foreach ($member in $slot.members) {
            if (-not $sources.ContainsKey($member.product_id)) { throw 'Unknown native source ID' }
            $source = $sources[$member.product_id]
            $filename = $source.gather.pds_archive.file_name
            if (-not $filename.StartsWith($member.capture_key + '_', [System.StringComparison]::Ordinal)) { throw 'Changed capture stem' }
            if ($source.gather.time.start_time -cne $meta.utc) { throw 'Changed recorded UTC' }
            foreach ($field in $fieldMap.Keys | Where-Object { $_ -notin @('flight_day','activity_id','target_id') }) {
                $actual = $source.pds4_label.($fieldMap[$field])
                if (@($actual).Count -ne 1 -or $actual[0] -cne $meta.$field) { throw "Changed source field: $field" }
            }
            foreach ($field in @('flight_day','activity_id','target_id')) {
                $actual = ConvertTo-Json -InputObject $source.pds4_label.($fieldMap[$field]) -Compress
                $copied = ConvertTo-Json -InputObject $member.side_metadata.$field -Compress
                if ($actual -cne $copied) { throw "Side-field loss or selection: $field" }
            }
            $expectedActions = @(if ($baselineByCapture.ContainsKey($member.capture_key)) { $baselineByCapture[$member.capture_key] })
            if (@(Compare-Object $expectedActions @($member.baseline_action_ids)).Count) { throw 'Changed baseline-action relationship' }
            if ($candidateByCapture.ContainsKey($member.capture_key) -and $candidateByCapture[$member.capture_key] -cne $family.family_id) { throw 'Snapshot unexpectedly contains a competing path' }
            $candidateByCapture[$member.capture_key] = $family.family_id
            [void]$nativeIds.Add($member.product_id)
            $candidateRows[$family.family_id + '|' + $position + '|' + $member.product_id] = [pscustomobject]@{family=$family;slot=$slot;member=$member}
        }
        $position++
    }
    if ($product -ne $family.native_path_count) { throw 'Native alternatives lost' }
    $expectedStatus = if ($product -gt 1) { 'IDENTITY_ALTERNATIVES_ABSTAIN' } else { 'UNAMBIGUOUS_METADATA_SEQUENCE' }
    if ($family.status -cne $expectedStatus) { throw 'Snapshot family ambiguity is misclassified' }
    for ($i=1; $i -lt $times.Count; $i++) { if ($times[$i] -lt $times[$i-1]) { throw 'Nonmonotone recorded times' } }
    if (($times[-1] - $times[0]).TotalSeconds -gt 10) { throw 'Span ceiling exceeded' }
}
$unambiguousBaseline = 0
$ambiguousBaseline = 0
foreach ($actionId in $baselineByAction.Keys) {
    $familyIds = @($baselineByAction[$actionId] | ForEach-Object {
        if (-not $candidateByCapture.ContainsKey($_)) { throw 'Baseline capture excluded without accounting' }
        $candidateByCapture[$_]
    } | Sort-Object -Unique)
    if ($familyIds.Count -ne 1) { throw 'Baseline action split across candidate families' }
    $family = $familyById[$familyIds[0]]
    if ($family.slots.Count -ne $baselineByAction[$actionId].Count) { throw 'Changed baseline action size' }
    if ($family.status -ceq 'UNAMBIGUOUS_METADATA_SEQUENCE') { $unambiguousBaseline++ } else { $ambiguousBaseline++ }
}
$csvRows = @(Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'membership.csv'))
$seenRows = [System.Collections.Generic.HashSet[string]]::new()
foreach ($row in $csvRows) {
    $rowKey = $row.family_id + '|' + $row.slot + '|' + $row.product_id
    if (-not $candidateRows.ContainsKey($rowKey) -or -not $seenRows.Add($rowKey)) { throw 'CSV omission, extra or duplicate member' }
    $expected = $candidateRows[$rowKey]
    if ($row.status -cne $expected.family.status -or $row.capture_key -cne $expected.member.capture_key) { throw 'Changed CSV status or capture identity' }
    foreach ($field in @('serial','file_number','shutter_count','utc','bracket_value')) { if ($row.$field -cne $expected.slot.metadata.$field) { throw 'CSV lexical-value drift' } }
}
$checks = [ordered]@{
    source_native_ids=$sources.Count; families=$result.families.Count; native_paths=$nativePaths
    exported_unique_native_ids=$nativeIds.Count; csv_rows=$csvRows.Count; csv_unique_members=$seenRows.Count
    multi_id_slots=$alternatives; baseline_actions=$baselineByAction.Count
    baseline_unambiguous=$unambiguousBaseline; baseline_identity_ambiguous=$ambiguousBaseline
}
$expected = @(10329,2174,2225,7655,7655,7655,23,2166,2165,1)
$i=0
foreach ($check in $checks.GetEnumerator()) { if ($check.Value -ne $expected[$i]) { throw "Native recount mismatch: $($check.Key)" }; $i++ }
if ($candidateRows.Count -ne $seenRows.Count) { throw 'Incomplete CSV membership' }
[ordered]@{status='PASS_NATIVE_SOURCE_MEMBERSHIP_AND_BASELINE_RECOUNT';checks=$checks;
    limits='Independently checks source fields, all matching-ID slot alternatives, counter/time/bracket constraints, original baseline coverage and CSV members. Not an independent enumeration of every full-snapshot path or physical validation.'} | ConvertTo-Json -Depth 5
