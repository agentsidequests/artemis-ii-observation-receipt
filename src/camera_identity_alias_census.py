"""Offline camera-metadata linkage and conditional action-finder diagnostics."""

import copy
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / 'paper-review/identity-census'
sys.path.insert(0, str(ROOT / 'src'))
from stage10a_metadata_integrity import normalize_hit  # Existing oracle adapter.
from stage10a_metadata_integrity import integer
from stage10c_camera_action_integrity import detect_complete_brackets

FIELDS = {
    'serial': 'img_surface:Instrument_Information/img_surface:instrument_serial_number',
    'file_number': 'cots_camera:File_Information/cots_camera:file_number',
    'shutter_count': 'cots_camera:Camera_Properties/cots_camera:shutter_count',
    'iso': 'img:ISO/img:iso_number',
    'focal_length': 'img:Optical_Properties/img:focal_length',
    'shooting_mode': 'cots_camera:Camera_Settings/cots_camera:shooting_mode',
    'auto_bracket_order': 'cots_camera:Exposure/cots_camera:auto_bracket_order',
    'bracket_value': 'cots_camera:Exposure/cots_camera:exposure_bracket_value',
    'flight_day': 'msn:Mission_Information/msn:flight_day_number',
    'activity_id': 'msn_surface:Observational_Intent/msn_surface:activity_id',
    'target_id': 'msn_surface:Observational_Intent/msn_surface:target_id',
}


def checked_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def verify_bytes(record):
    payload = (ROOT / record['path']).read_bytes()
    if len(payload) != record['bytes'] or hashlib.sha256(payload).hexdigest() != record['sha256']:
        raise ValueError('Source-byte custody mismatch: ' + record['path'])
    return payload


def one(value):
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], str) or not value[0].strip():
        return None
    return value[0]


def normalize(hit):
    source = hit['_source']
    if source.get('bundle_id') != 'artemis2_crew_camera' or source.get('collection_id') != 'data_raw':
        raise ValueError('Wrong raw-product scope')
    identifier = hit['_id']
    filename = source['gather']['pds_archive']['file_name']
    basename = identifier.rsplit('/', 1)[-1]
    match = re.fullmatch(r'(art002e\d+)_nk[a-z0-9]+_raw_v01\.tif', filename)
    if not match or basename != filename:
        raise ValueError('Raw identifier/filename mapping changed')
    label = source.get('pds4_label', {})
    record = {'product_id': identifier, 'capture_key': match[1], 'file_name': filename,
              'utc': source['gather']['time']['start_time'],
              **{field: one(label.get(key)) for field, key in FIELDS.items()},
              'side_metadata': {field: label.get(FIELDS[field]) for field in ['flight_day', 'activity_id', 'target_id']}}
    if record['flight_day'] not in [str(day) for day in range(1, 11)]:
        raise ValueError('Unqualified flight day')
    return record


def key(record, fields, semantic_utc=False):
    values = []
    for field in fields:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            return None
        if field == 'utc' and semantic_utc:
            try:
                time = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return None
            if time.tzinfo is None:
                return None
            value = time.astimezone(timezone.utc).isoformat(timespec='microseconds')
        values.append(value)
    return tuple(values)


def groups(records, fields, semantic_utc=False):
    buckets = defaultdict(list)
    for record in records:
        signature = key(record, fields, semantic_utc)
        if signature is not None:
            buckets[signature].append(record)
    return [sorted(bucket, key=lambda r: r['product_id']) for signature, bucket in sorted(buckets.items()) if len(bucket) > 1]


def load_snapshot(contract):
    for record in contract['inputs']:
        verify_bytes(record)
    receipts = [checked_json(ROOT / contract['inputs'][index]['path']) for index in [0, 1]]
    pages = receipts[1]['atlas_pages'] + receipts[0]['atlas_pages']  # Exact Stage 10J input order.
    hits, sources = [], []
    for page in pages:
        request = {'path': page['request_path'], 'bytes': page['request_bytes'], 'sha256': page['request_sha256']}
        response = {'path': page['response_path'], 'bytes': page['response_bytes'], 'sha256': page['response_sha256']}
        verify_bytes(request)
        parsed = json.loads(verify_bytes(response))
        section = parsed.get('hits', {})
        total = section.get('total', {})
        expected_total = contract['expected_day_counts'][str(page['flight_day'])] if 'flight_day' in page else contract['expected_day_counts']['6']
        if total.get('relation') != 'eq' or total.get('value') != expected_total or len(section.get('hits', [])) != page['hits']:
            raise ValueError('Incomplete frozen metadata page')
        hits.extend(section['hits'])
        sources.extend([request, response])
    records = [normalize(hit) for hit in hits]
    if len(records) != contract['expected_raw_records'] or len({r['product_id'] for r in records}) != len(records):
        raise ValueError('Raw inventory or unique-ID check failed')
    if len({r['capture_key'] for r in records}) != len(records):
        raise ValueError('Capture-stem inventory is not one-to-one with raw rows')
    if {str(day): sum(r['flight_day'] == str(day) for r in records) for day in range(1, 11)} != contract['expected_day_counts']:
        raise ValueError('Day coverage changed')
    return hits, records, sources


def load_manifest(contract):
    path = ROOT / contract['inputs'][2]['path']
    by_capture = defaultdict(list)
    with path.open(encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            by_capture[row['capture_identity']].append(row)
    actions = {row['action_id'] for rows in by_capture.values() for row in rows}
    counts = {'products': sum(map(len, by_capture.values())), 'capture_keys': len(by_capture), 'actions': len(actions)}
    if counts != contract['expected_manifest']:
        raise ValueError('Original counted cohort changed')
    for rows in by_capture.values():
        if len(rows) != 3 or {r['collection_id'] for r in rows} != {'data_source', 'data_raw', 'data_processed'} or len({r['action_id'] for r in rows}) != 1:
            raise ValueError('Unqualified manifest capture relationship')
    return by_capture


def action_summary(brackets):
    return {'actions': len(brackets), 'admitted_raw_keys': len({name for action in brackets for name in action['file_names']}),
            'patterns': dict(sorted(Counter(','.join(action['bracket_values']) for action in brackets).items())),
            'activity_fractures': sum(action['activity_facet_fracture'] for action in brackets),
            'target_presence_fractures': sum(action['target_presence_fracture'] for action in brackets),
            'target_value_fractures': sum(action['target_value_fracture'] for action in brackets)}


def action_signature(action):
    return (action['serial'], tuple(action['shutter_counts']), tuple(action['file_numbers']), tuple(action['bracket_values']), action['start_time'], action['end_time'])


def admitted_tag_counts(brackets, legacy):
    names = {name for action in brackets for name in action['file_names']}
    selected = [record for record in legacy if record['file_name'] in names]
    return {'admitted_raw_keys': len(names), 'nonblank_target_keys': sum(bool(record['target_id']) for record in selected),
            'target_values': dict(sorted(Counter(record['target_id'] for record in selected if record['target_id']).items()))}


def sort_tie_profile(records):
    buckets = defaultdict(list)
    for record in records:
        counter = integer(record['shutter_count'])
        if record['serial'] is not None and counter is not None:
            buckets[(record['serial'], counter or -1)].append(record)
    ties = [bucket for bucket in buckets.values() if len(bucket) > 1]
    return {'tied_sort_keys': len(ties), 'records_in_ties': sum(map(len, ties)),
            'ties_with_different_recorded_times': sum(len({r['utc'] for r in group}) > 1 for group in ties),
            'ties_with_different_file_numbers': sum(len({r['file_number'] for r in group}) > 1 for group in ties),
            'ties_spanning_flight_days': sum(len({r['flight_day'] for r in group}) > 1 for group in ties),
            'ties_by_camera': dict(sorted(Counter(group[0]['serial'] for group in ties).items())),
            'scope': 'The incumbent numeric shutter sort key, not a physical identity key or error rate'}


def diagnostic(hits, records, contract):
    base = checked_json(ROOT / 'spec/stage10c.json')['complete_bracket_contract']
    base = copy.deepcopy(base)
    base['allowed_bracket_sequences'] = checked_json(ROOT / 'spec/stage10j.json')['expanded_patterns']
    legacy = [normalize_hit(hit) for hit in hits]
    original = detect_complete_brackets(legacy, base)
    if len(original) != 2166 or action_summary(original)['admitted_raw_keys'] != 7606:
        raise ValueError('Unchanged action-finder baseline does not replay')
    baseline_names = {name for action in original for name in action['file_names']}
    original_signatures = {action_signature(action) for action in original}
    comparison = {}
    exact_groups = groups(records, contract['strict_fields'])
    for choice in ['minimum_product_id', 'maximum_product_id']:
        remove_ids = {r['product_id'] for group in exact_groups for r in (group[1:] if choice == 'minimum_product_id' else group[:-1])}
        changed = [old for old, record in zip(legacy, records) if record['product_id'] not in remove_ids]
        actions = detect_complete_brackets(changed, base)
        names = {name for action in actions for name in action['file_names']}
        added = [action for action in actions if action_signature(action) not in original_signatures]
        comparison[choice] = {'summary': action_summary(actions), 'admitted_target_fields': admitted_tag_counts(actions, changed), 'input_records_removed_conditionally': len(remove_ids),
                              'newly_admitted_raw_keys': len(names - baseline_names), 'previous_raw_keys_not_retained': len(baseline_names - names),
                              'added_camera_sequence_witnesses': added}
    reversed_actions = detect_complete_brackets(list(reversed(legacy)), base)
    reversed_names = {name for action in reversed_actions for name in action['file_names']}
    return {'baseline': action_summary(original), 'baseline_target_fields': admitted_tag_counts(original, legacy), 'conditional_representative_choices': comparison,
            'reversed_input_order': {'summary': action_summary(reversed_actions), 'admitted_target_fields': admitted_tag_counts(reversed_actions, legacy), 'admitted_identifier_symmetric_difference': len(baseline_names ^ reversed_names)},
            'interpretation': 'Unmodified algorithm replay under conditional record treatment and input-order perturbation; not corrected physical actions, actual leakage, source identity or a change to the counted cohort'}


def replay():
    contract = checked_json(OWNER / 'contract.json')
    hits, records, sources = load_snapshot(contract)
    manifest = load_manifest(contract)
    exact = groups(records, contract['strict_fields'])
    core = groups(records, contract['core_fields'])
    semantic = groups(records, contract['strict_fields'], semantic_utc=True)
    witnesses = []
    membership_counts = Counter()
    for index, group in enumerate(exact, 1):
        present = [r for r in group if r['capture_key'] in manifest]
        membership_counts[str(len(present))] += 1
        conflicts = [field for field in ['flight_day', 'activity_id', 'target_id'] if len({json.dumps(r['side_metadata'][field], sort_keys=True) for r in group}) > 1]
        witnesses.append({'group_id': f'candidate-{index:03d}', 'key': {field: group[0][field] for field in contract['strict_fields']},
                          'side_metadata_conflicts': conflicts,
                          'records': [{**r, 'manifest_product_rows': len(manifest.get(r['capture_key'], [])),
                                       'manifest_action_ids': sorted({row['action_id'] for row in manifest.get(r['capture_key'], [])})} for r in group]})
    return {'status': 'VERIFIED_FROZEN_METADATA_CANDIDATE_LINKAGE_CENSUS', 'scope': contract['scope'],
            'raw_records': len(records), 'unique_raw_product_ids': len({r['product_id'] for r in records}),
            'strict_key_eligible_records': sum(key(r, contract['strict_fields']) is not None for r in records),
            'strict_candidate_groups': len(exact), 'strict_candidate_group_sizes': dict(sorted(Counter(str(len(g)) for g in exact).items())),
            'strict_candidate_records': sum(map(len, exact)), 'distinct_strict_metadata_keys': len({key(r, contract['strict_fields']) for r in records if key(r, contract['strict_fields']) is not None}),
            'core_candidate_groups': len(core), 'semantic_utc_candidate_groups': len(semantic),
            'candidate_groups_by_day': dict(sorted(Counter(group[0]['flight_day'] for group in exact).items())),
            'candidate_groups_by_camera': dict(sorted(Counter(group[0]['serial'] for group in exact).items())),
            'candidate_groups_by_number_of_counted_capture_keys': dict(sorted(membership_counts.items())),
            'candidate_groups_with_side_metadata_conflicts': sum(bool(w['side_metadata_conflicts']) for w in witnesses),
            'original_manifest': contract['expected_manifest'], 'witnesses': witnesses,
            'incumbent_sort_ties': sort_tie_profile(records),
            'conditional_algorithm_diagnostic': diagnostic(hits, records, contract),
            'claim_limits': contract['limits'], 'effects': contract['effects'],
            'provenance': {'contract': contract, 'request_and_response_sources': sources,
                           'offline_replay_command': 'python -B -m src.camera_identity_alias_census'}}


if __name__ == '__main__':
    result = replay()
    if sys.argv[1:] == ['--csv']:
        output = io.StringIO(newline='')
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow(['candidate_group','capture_key','product_id','serial','file_number','shutter_count','utc','iso','focal_length','shooting_mode','auto_bracket_order','bracket_value','flight_day','recorded_primary_targets_json','recorded_activities_json','manifest_product_rows','manifest_action_ids_json','side_metadata_conflicts','status'])
        for group in result['witnesses']:
            for record in group['records']:
                writer.writerow([group['group_id'],record['capture_key'],record['product_id'],record['serial'],record['file_number'],record['shutter_count'],record['utc'],record['iso'],record['focal_length'],record['shooting_mode'],record['auto_bracket_order'],record['bracket_value'],record['flight_day'],json.dumps(record['side_metadata']['target_id']),json.dumps(record['side_metadata']['activity_id']),record['manifest_product_rows'],json.dumps(record['manifest_action_ids']),';'.join(group['side_metadata_conflicts']),'METADATA_MATCH_CANDIDATE_NOT_PHYSICAL_IDENTITY'])
        print(output.getvalue(), end='')
    elif not sys.argv[1:]:
        print(json.dumps(result, indent=2, allow_nan=False))
    else:
        raise SystemExit('Only offline JSON replay or --csv witness export is supported')
