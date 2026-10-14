"""Lossless, order-invariant metadata sequence candidate. No physical merge."""

import copy
import csv
import hashlib
import io
import itertools
import json
import math
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src.camera_identity_alias_census import ROOT, checked_json, key, load_manifest, load_snapshot, normalize, verify_bytes
from stage10a_metadata_integrity import integer, normalize_hit
from stage10c_camera_action_integrity import bracket_from_sequence, detect_complete_brackets

OWNER = ROOT / 'paper-review/order-robust-reconstruction'
DEFAULT_BUDGET = {'maximum_native_paths': 100000, 'maximum_paths_per_start_pattern': 512}


def explicit_time(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except (ValueError, AttributeError, TypeError, OverflowError):
        return None


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), ensure_ascii=True).encode('utf-8')).hexdigest()


def reconstruct(hits, strict_fields, bracket_contract, budget=None):
    """Enumerate native paths, then retain lossless families and ambiguity components."""
    budget = DEFAULT_BUDGET if budget is None else budget
    if any(type(budget.get(name)) is not int or budget[name] < 1 for name in DEFAULT_BUDGET):
        raise ValueError('Invalid positive integer complexity budget')
    records, legacy, parsed_times, keys = {}, {}, {}, {}
    excluded = []
    index = defaultdict(list)
    for hit in hits:
        record = normalize(hit)
        identifier = record['product_id']
        if identifier in records:
            raise ValueError('Duplicate native ID')
        records[identifier] = record
        item = normalize_hit(hit)
        legacy[identifier] = item
        signature = key(record, strict_fields)
        time = explicit_time(record['utc'])
        shutter, file_number = integer(record['shutter_count']), integer(record['file_number'])
        reason = ('UNKEYABLE_METADATA' if signature is None else
                  'INVALID_OR_NAIVE_TIME' if time is None else
                  'UNQUALIFIED_COUNTER' if shutter is None or file_number is None or shutter < 0 or file_number < 0 else None)
        if reason:
            excluded.append({'product_id': identifier, 'reason': reason})
            continue
        keys[identifier], parsed_times[identifier] = signature, time
        index[(record['serial'], shutter, file_number)].append(identifier)
    for bucket in index.values():
        bucket.sort()
    patterns = sorted({tuple(pattern) for pattern in bracket_contract['allowed_bracket_sequences']})
    if any(not pattern or pattern[0] != '0' for pattern in patterns):
        raise ValueError('Every pattern must begin at zero')
    path_map = defaultdict(set)
    total_paths = 0
    for start in sorted(keys):
        first = records[start]
        if first['bracket_value'] != '0':
            continue
        shutter, file_number = integer(first['shutter_count']), integer(first['file_number'])
        for pattern in patterns:
            candidates = [[start]]
            for offset, bracket in enumerate(pattern[1:], 1):
                bucket = index.get((first['serial'], shutter + offset, file_number + offset), [])
                candidates.append([identifier for identifier in bucket
                                   if records[identifier]['bracket_value'] == bracket
                                   and all(legacy[identifier][field] == legacy[start][field]
                                           for field in bracket_contract['same_fields'])])
            if any(not slot for slot in candidates):
                continue
            possible_paths = math.prod(map(len, candidates))
            if possible_paths > budget['maximum_paths_per_start_pattern']:
                raise ValueError('Per-start complexity budget exceeded; no partial result')
            for path in itertools.product(*candidates):
                times = [parsed_times[identifier] for identifier in path]
                if any(a > b for a, b in zip(times, times[1:])):
                    continue
                window = [legacy[identifier] for identifier in path]
                if bracket_from_sequence(window, list(pattern), bracket_contract) is None:
                    continue
                family_key = tuple(keys[identifier] for identifier in path)
                path_map[family_key].add(tuple(path))
                total_paths += 1
                if total_paths > budget['maximum_native_paths']:
                    raise ValueError('Total complexity budget exceeded; no partial result')
    families = []
    native_to_family = defaultdict(set)
    all_native_paths = set()
    for family_key, path_set in sorted(path_map.items()):
        family_id = 'metadata-path-' + stable_hash(family_key)
        slot_ids = [sorted({path[position] for path in path_set}) for position in range(len(family_key))]
        if len(path_set) != math.prod(map(len, slot_ids)):
            raise ValueError('Non-Cartesian alternatives cannot be represented as independent slots')
        slots = []
        for signature, alternatives in zip(family_key, slot_ids):
            slots.append({'metadata': dict(zip(strict_fields, signature)),
                          'members': [{'product_id': identifier, 'capture_key': records[identifier]['capture_key'],
                                       'side_metadata': records[identifier]['side_metadata']} for identifier in alternatives]})
            for identifier in alternatives:
                native_to_family[identifier].add(family_id)
        all_native_paths.update(path_set)
        families.append({'family_id': family_id, 'slots': slots, 'native_path_count': len(path_set),
                         'identity_alternative_slots': sum(len(slot) > 1 for slot in slot_ids),
                         'status': 'IDENTITY_ALTERNATIVES_ABSTAIN' if any(len(slot) > 1 for slot in slot_ids) else 'UNAMBIGUOUS_METADATA_SEQUENCE',
                         'competition_component_id': None})
    adjacency = {family['family_id']: set() for family in families}
    for memberships in native_to_family.values():
        for family_id in memberships:
            adjacency[family_id].update(memberships - {family_id})
    components, seen = [], set()
    for family_id in sorted(adjacency):
        if family_id in seen or not adjacency[family_id]:
            continue
        stack, connected = [family_id], set()
        while stack:
            current = stack.pop()
            if current not in connected:
                connected.add(current)
                stack.extend(adjacency[current] - connected)
        seen.update(connected)
        component_id = 'competition-' + stable_hash(sorted(connected))
        members = sorted(connected)
        shared_ids = sorted(identifier for identifier, memberships in native_to_family.items()
                            if len(memberships & connected) > 1)
        components.append({'component_id': component_id, 'family_ids': members, 'shared_native_ids': shared_ids})
    component_by_family = {family_id: component['component_id'] for component in components for family_id in component['family_ids']}
    for family in families:
        if family['family_id'] in component_by_family:
            family['status'] = 'COMPETING_PATHS_ABSTAIN'
            family['competition_component_id'] = component_by_family[family['family_id']]
    used_ids = set(native_to_family)
    output = {'families': families, 'competition_components': components,
              'unkeyable_or_unqualified': sorted(excluded, key=lambda row: row['product_id']),
              'native_ids_without_complete_path': sorted(set(records) - used_ids),
              'summary': {'input_native_ids': len(records), 'native_complete_paths': len(all_native_paths),
                          'metadata_path_families': len(families), 'family_status_counts': dict(sorted(Counter(f['status'] for f in families).items())),
                          'native_ids_with_complete_path': len(used_ids), 'unqualified_input_ids': len(excluded),
                          'competition_components': len(components)}}
    assert_invariants(output)
    return output


def assert_invariants(result):
    admitted_ids, withheld_ids = set(), set()
    by_id = {family['family_id']: family for family in result['families']}
    if len(by_id) != len(result['families']):
        raise ValueError('Duplicate family ID')
    native_memberships = defaultdict(set)
    for family in result['families']:
        for slot in family['slots']:
            for member in slot['members']:
                native_memberships[member['product_id']].add(family['family_id'])
    # Independently verify component coverage with union-find, not stored flags.
    parent = {identifier: identifier for identifier in by_id}
    def find(identifier):
        while parent[identifier] != identifier:
            parent[identifier] = parent[parent[identifier]]
            identifier = parent[identifier]
        return identifier
    for memberships in native_memberships.values():
        ordered = sorted(memberships)
        for identifier in ordered[1:]:
            parent[find(identifier)] = find(ordered[0])
    partitions = defaultdict(set)
    for identifier in parent:
        partitions[find(identifier)].add(identifier)
    actual_components = {tuple(sorted(group)) for group in partitions.values() if len(group) > 1}
    declared_components = [tuple(component['family_ids']) for component in result['competition_components']]
    if len(set(declared_components)) != len(declared_components) or set(declared_components) != actual_components:
        raise ValueError('Incomplete or invented competition components')
    component_members = {identifier for group in actual_components for identifier in group}
    for family in result['families']:
        member_ids = [m['product_id'] for slot in family['slots'] for m in slot['members']]
        if len(set(member_ids)) != len(member_ids):
            raise ValueError('A native ID appears in multiple slots')
        is_competing = family['family_id'] in component_members
        alternatives = any(len(slot['members']) > 1 for slot in family['slots'])
        expected = 'COMPETING_PATHS_ABSTAIN' if is_competing else 'IDENTITY_ALTERNATIVES_ABSTAIN' if alternatives else 'UNAMBIGUOUS_METADATA_SEQUENCE'
        if family['status'] != expected:
            raise ValueError('Ambiguous path was admitted')
        if family['native_path_count'] != math.prod(len(slot['members']) for slot in family['slots']):
            raise ValueError('Native alternatives lost')
        if expected == 'UNAMBIGUOUS_METADATA_SEQUENCE':
            if admitted_ids & set(member_ids):
                raise ValueError('Admitted families overlap')
            admitted_ids.update(member_ids)
        else:
            withheld_ids.update(member_ids)
    if admitted_ids & withheld_ids:
        raise ValueError('An admitted native ID also belongs to an ambiguous path')
    for component in result['competition_components']:
        members = set(component['family_ids'])
        actual_shared = sorted(identifier for identifier, memberships in native_memberships.items() if len(memberships & members) > 1)
        if component['component_id'] != 'competition-' + stable_hash(component['family_ids']) or component['shared_native_ids'] != actual_shared:
            raise ValueError('Competition identity or shared-record inventory changed')
        if any(by_id[identifier]['competition_component_id'] != component['component_id'] for identifier in members):
            raise ValueError('Family/component relationship changed')


def native_paths(result):
    return {tuple(m['product_id'] for m in path)
            for family in result['families']
            for path in itertools.product(*(slot['members'] for slot in family['slots']))}


def replay():
    contract = checked_json(OWNER / 'contract.json')
    if contract['version'] != '1.0' or any(value is not False for value in contract['limits'].values()):
        raise ValueError('Candidate cannot promote physical validity, adoption or scientific acceptance')
    if contract['effects'] != {'network_requests': 0, 'new_image_bytes': 0, 'outreach': False, 'publication': False, 'remote_push': False}:
        raise ValueError('External effect or new-image authority is not supplied by this candidate')
    for pin in contract['input_pins']:
        verify_bytes(pin)
    source_contract = checked_json(ROOT / contract['input_pins'][0]['path'])
    hits, records, sources = load_snapshot(source_contract)
    manifest = load_manifest(source_contract)
    bracket_contract = copy.deepcopy(checked_json(ROOT / 'spec/stage10c.json')['complete_bracket_contract'])
    bracket_contract['allowed_bracket_sequences'] = checked_json(ROOT / 'spec/stage10j.json')['expanded_patterns']
    result = reconstruct(hits, source_contract['strict_fields'], bracket_contract, contract['budget'])
    orders = [('original', hits), ('reversed', list(reversed(hits))),
              ('product_id_sorted', sorted(hits, key=lambda hit: hit['_id']))]
    for seed in contract['order_checks']['shuffled_seeds']:
        changed = list(hits)
        random.Random(seed).shuffle(changed)
        orders.append((f'shuffled_seed_{seed}', changed))
    pivot = len(hits) // 3
    orders.append(('rotated', hits[pivot:] + hits[:pivot]))
    order_checks = []
    digest = stable_hash(result)
    for name, changed in orders:
        candidate = result if name == 'original' else reconstruct(changed, source_contract['strict_fields'], bracket_contract, contract['budget'])
        if candidate != result:
            raise ValueError('Order-invariance counterexample: ' + name)
        order_checks.append({'order': name, 'pass': True, 'result_sha256': digest})
    legacy = [normalize_hit(hit) for hit in hits]
    baseline = detect_complete_brackets(legacy, bracket_contract)
    if len(baseline) != 2166 or len({name for action in baseline for name in action['file_names']}) != 7606:
        raise ValueError('Frozen original algorithm does not replay')
    id_by_file = {record['file_name']: record['product_id'] for record in records}
    candidate_paths = native_paths(result)
    path_to_family = {path: family for family in result['families']
                      for path in itertools.product(*(tuple(m['product_id'] for m in slot['members']) for slot in family['slots']))}
    baseline_paths = [tuple(id_by_file[name] for name in action['file_names']) for action in baseline]
    exclusions = []
    status_counts = Counter()
    for path in baseline_paths:
        if path in candidate_paths:
            status_counts[path_to_family[path]['status']] += 1
        else:
            times = [explicit_time(next(record['utc'] for record in records if record['product_id'] == identifier)) for identifier in path]
            if any(time is None for time in times) or any(a > b for a, b in zip(times, times[1:])):
                reason = 'ADDED_EXPLICIT_NONDECREASING_TIME_GATE'
            else:
                raise ValueError('Unexplained exclusion of a frozen baseline native path')
            exclusions.append({'native_ids': list(path), 'reason': reason})
    baseline_family_ids = {path_to_family[path]['family_id'] for path in baseline_paths if path in candidate_paths}
    result.update({'status': 'ORDER_INVARIANT_METADATA_CANDIDATE_NOT_ADOPTED',
                   'contract': contract, 'order_checks': order_checks,
                   'baseline_comparison': {'frozen_actions': len(baseline), 'frozen_capture_keys': 7606,
                                           'baseline_native_paths_by_candidate_status': dict(sorted(status_counts.items())),
                                           'explicit_baseline_exclusions': exclusions,
                                           'candidate_families_without_baseline_path': sum(f['family_id'] not in baseline_family_ids for f in result['families'])},
                   'claim_limits': contract['limits'], 'effects': contract['effects'],
                   'provenance': {'source_census_contract': source_contract, 'request_response_sources': sources,
                                  'candidate_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                  'manifest_hash': source_contract['inputs'][2]['sha256']}})
    for family in result['families']:
        for slot in family['slots']:
            for member in slot['members']:
                rows = manifest.get(member['capture_key'], [])
                member['baseline_action_ids'] = sorted({row['action_id'] for row in rows})
    return result


def csv_bytes(result):
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(['family_id', 'status', 'competition_component_id', 'slot', 'native_path_count', 'product_id', 'capture_key',
                     'serial', 'file_number', 'shutter_count', 'utc', 'bracket_value', 'original_target_fields_json',
                     'original_activity_fields_json', 'baseline_action_ids_json'])
    for family in result['families']:
        for position, slot in enumerate(family['slots']):
            for member in slot['members']:
                metadata, side = slot['metadata'], member['side_metadata']
                writer.writerow([family['family_id'], family['status'], family['competition_component_id'], position,
                                 family['native_path_count'], member['product_id'], member['capture_key'], metadata['serial'],
                                 metadata['file_number'], metadata['shutter_count'], metadata['utc'], metadata['bracket_value'],
                                 json.dumps(side['target_id']), json.dumps(side['activity_id']), json.dumps(member.get('baseline_action_ids', []))])
    return output.getvalue().encode('utf-8')


def artifact_bytes(result):
    return {'result.json': (json.dumps(result, indent=2, allow_nan=False) + '\n').encode('utf-8'),
            'membership.csv': csv_bytes(result)}


def artifacts(mode, expected_old_hashes=None):
    result = replay()
    outputs = artifact_bytes(result)
    for name, data in outputs.items():
        path = OWNER / name
        old = path.read_bytes() if path.is_file() else None
        if mode == '--refresh':
            if not expected_old_hashes or set(expected_old_hashes) != set(outputs) or old is None or hashlib.sha256(old).hexdigest() != expected_old_hashes[name]:
                raise ValueError('Owned artifact identity mismatch; no refresh writes')
        elif old is not None and old != data:
            raise ValueError('Existing different artifact; no overwrite: ' + name)
        if mode == '--check' and not path.is_file():
            raise ValueError('Missing artifact: ' + name)
    if mode in ['--write', '--refresh']:
        for name, data in outputs.items():
            path = OWNER / name
            if mode == '--refresh' or not path.exists():
                with path.open('wb' if mode == '--refresh' else 'xb') as stream:
                    stream.write(data)
    return {'status': result['status'], 'summary': result['summary'], 'baseline_comparison': result['baseline_comparison'],
            'order_checks': len(result['order_checks']), 'artifacts': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in outputs.items()}}


if __name__ == '__main__':
    arguments = sys.argv[1:]
    if len(arguments) == 3 and arguments[0] == '--refresh':
        expected = dict(zip(['result.json', 'membership.csv'], arguments[1:]))
        response = artifacts('--refresh', expected)
    elif arguments in [['--write'], ['--check']]:
        response = artifacts(arguments[0])
    else:
        raise SystemExit('Use --write, --check, or --refresh with exact prior result and CSV SHA-256 values')
    print(json.dumps(response, indent=2, allow_nan=False))
