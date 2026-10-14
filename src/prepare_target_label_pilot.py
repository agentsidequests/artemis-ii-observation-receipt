"""Prepare a purposeful, metadata-only proposal. No pixels, network or annotations."""

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREP = Path('target-label-audit/pilot-prep')
COLLECTIONS = ('data_source', 'data_raw', 'data_processed')
QUEUE_FIELDS = ('audit_id', 'phase', 'concept_status', 'render_status', 'decision_status')
STEWARD_FIELDS = (
    'audit_id', 'phase', 'capture_identity', 'action_id', 'camera_serial',
    'activity_id', 'snapshot_target_field', 'selection_bucket', 'coverage_regime',
    'flight_day', 'exposure_position', 'bracket_value', 'selection_reason',
    'source_product_id', 'source_url', 'source_label_url', 'source_archive_size_bytes',
    'raw_product_id', 'raw_url', 'raw_label_url', 'raw_archive_size_bytes',
    'processed_product_id', 'processed_url', 'processed_label_url', 'processed_archive_size_bytes',
    'url_status', 'image_content_status', 'image_hash_status', 'secondary_targets_status',
)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def pinned(root, relative, expected):
    payload = (root / relative).read_bytes()
    if sha(payload) != expected:
        raise ValueError('Pinned source changed: ' + relative)
    return payload


def csv_bytes(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def load_inputs(root):
    policy = json.loads((root / PREP / 'policy.json').read_text(encoding='utf-8'))
    if (policy['current_pixel_budget_bytes'] != 0 or policy['future_preview_ceiling_is_authorized']
            or policy['probability_sample_drawn'] or policy['images_labeled'] or policy['qualified_rubric_accepted']):
        raise ValueError('Metadata-only proposal cannot declare execution or acceptance')
    payload = pinned(root, policy['source_manifest'], policy['source_manifest_sha256'])
    if len(payload) != policy['source_manifest_bytes']:
        raise ValueError('Manifest byte count changed')
    anchor = json.loads(pinned(root, policy['archive_anchor'], policy['archive_anchor_sha256']))
    plan = json.loads(pinned(root, policy['target_plan'], policy['target_plan_sha256']))
    sunset = [x['target_properties'] for x in plan if x.get('target_properties', {}).get('target_name') == 'Sunset']
    if len(sunset) != 1 or sunset[0]['order'] != 24:
        raise ValueError('Native Sunset plan anchor is not unique')
    if not any(x.get('kind') == 'science_label' and x.get('url', '').startswith(policy['archive_base'] + '/') for x in anchor['files']):
        raise ValueError('Archive base lacks its pinned native locator anchor')
    rows = list(csv.DictReader(io.StringIO(payload.decode('utf-8'))))
    groups = defaultdict(dict)
    for row in rows:
        capture, collection = row['capture_identity'], row['collection_id']
        if collection not in COLLECTIONS or collection in groups[capture]:
            raise ValueError('Unexpected or duplicate capture representation')
        if int(row['archive_size_bytes']) <= 0:
            raise ValueError('Missing native product size')
        groups[capture][collection] = row
    if len(groups) != 7606 or any(set(g) != set(COLLECTIONS) for g in groups.values()):
        raise ValueError('Complete-action frame or three-representation parity changed')
    source_rows = [g['data_source'] for g in groups.values()]
    if sum(bool(r['target_id'].strip()) for r in source_rows) != 3413:
        raise ValueError('Tag-presence frame changed')
    excluded = {x['product_id'].split('_', 1)[0] for x in anchor['files'] if x.get('kind') == 'browse_image'}
    return policy, groups, source_rows, excluded


def bucket(row):
    value = row['target_id'].strip()
    return 'sunset_recorded_tag' if value == 'Sunset' else 'other_recorded_tag' if value else 'blank_recorded_tag'


def product_url(row, policy):
    identifier = row['product_id']
    if not identifier.startswith(policy['product_id_prefix']):
        raise ValueError('Unknown product identifier carrier')
    path = identifier[len(policy['product_id_prefix']):]
    if not path.startswith('/artemis2_crew_camera/' + row['collection_id'] + '/') or '..' in path.split('/'):
        raise ValueError('Product path not within the admitted collection')
    return policy['archive_base'] + path


def choose_panel(source_rows, policy, excluded):
    activity_rows = defaultdict(list)
    for row in source_rows:
        activity_rows[row['activity_id']].append(row)
    regimes = {}
    for activity, values in activity_rows.items():
        tagged = sum(bool(r['target_id'].strip()) for r in values)
        regimes[activity] = 'zero' if tagged == 0 else 'complete' if tagged == len(values) else 'partial'
    quotas = policy['phase_quotas']
    if sum(quotas.values()) != 24 or Counter(policy['slot_cycle'] * 6) != Counter(quotas):
        raise ValueError('Slot cycle does not reproduce the frozen phase quotas')
    selected, used_actions = [], set()
    for phase in policy['phases']:
        seen = [set() for _ in range(6)]
        for wanted in policy['slot_cycle'] * 6:
            options = [r for r in source_rows if bucket(r) == wanted and r['action_id'] not in used_actions
                       and (not policy['exclude_known_browse_captures_from_archive_anchor'] or r['capture_identity'] not in excluded)]
            if not options:
                raise ValueError('Panel coverage is infeasible; do not pad or reuse an action')
            def features(r):
                return (r['camera_serial'], regimes[r['activity_id']], r['activity_id'], r['target_id'],
                        r['product_id'].split('/')[-2], r['bracket_value'])
            def rank(r):
                novelty = tuple(int((wanted, value) not in seen[i]) for i, value in enumerate(features(r)))
                tie = sha((policy['tie_rank_prefix'] + r['capture_identity']).encode('utf-8'))
                return tuple(-n for n in novelty) + (tie, r['capture_identity'])
            row = min(options, key=rank)
            values = features(row)
            novelty = [i for i, value in enumerate(values) if (wanted, value) not in seen[i]]
            for i, value in enumerate(values):
                seen[i].add((wanted, value))
            used_actions.add(row['action_id'])
            selected.append({'row': row, 'phase': phase, 'bucket': wanted, 'regime': regimes[row['activity_id']],
                             'reason': 'metadata novelty axes=' + ','.join(map(str, novelty)) + '; deterministic tie rank; no content inference'})
    # Opaque sequential IDs do not carry stratum or original capture identity.
    selected.sort(key=lambda x: (sha(('opaque-order-v1|' + x['row']['capture_identity']).encode('utf-8')), x['row']['capture_identity']))
    for number, item in enumerate(selected, 1):
        item['audit_id'] = f'A2P-{number:03d}'
    if len(selected) != policy['proposal_exposures']:
        raise ValueError('Proposed panel count changed')
    return selected


def build(root=ROOT):
    input_names = ['results/stage10o-product-relationship-manifest.csv', 'evidence/stage8b/source-manifest.json',
                   'corpus/artemis2_outgoing_target_request.json', (PREP / 'policy.json').as_posix(),
                   (PREP / 'reviewer-packet-template.md').as_posix(), 'src/prepare_target_label_pilot.py',
                   'ARTEMIS-II-TARGET-LABEL-AUDIT-PROTOCOL.md']
    before = {name: sha((root / name).read_bytes()) for name in input_names}
    policy, groups, source_rows, excluded = load_inputs(root)
    selected = choose_panel(source_rows, policy, excluded)
    steward, queue = [], []
    costs = {phase: {c: 0 for c in COLLECTIONS} for phase in policy['phases']}
    for item in selected:
        row = item['row']
        record = {k: row[k] for k in ('capture_identity', 'action_id', 'camera_serial', 'activity_id', 'exposure_position', 'bracket_value')}
        record.update(audit_id=item['audit_id'], phase=item['phase'], snapshot_target_field=row['target_id'],
                      selection_bucket=item['bucket'], coverage_regime=item['regime'], flight_day=row['product_id'].split('/')[-2],
                      selection_reason=item['reason'], url_status='DERIVED_NATIVE_PATH_NOT_LIVE_CHECKED',
                      image_content_status='NOT_INSPECTED_FOR_PREPARATION', image_hash_status='UNACQUIRED_UNKNOWN',
                      secondary_targets_status='NATIVE_LABEL_CHECK_PENDING')
        for collection, prefix in zip(COLLECTIONS, ('source', 'raw', 'processed')):
            product = groups[row['capture_identity']][collection]
            url = product_url(product, policy)
            size = int(product['archive_size_bytes'])
            record.update({prefix + '_product_id': product['product_id'], prefix + '_url': url,
                           prefix + '_label_url': url.rsplit('.', 1)[0] + '.xml', prefix + '_archive_size_bytes': size})
            costs[item['phase']][collection] += size
        steward.append(record)
        if item['phase'] == 'CALIBRATION_PROPOSED':
            queue.append(dict(audit_id=item['audit_id'], phase=item['phase'], concept_status='RUBRIC_NOT_ACCEPTED',
                              render_status='NO_IMAGE_BUNDLE', decision_status='NOT_REVIEWED'))
    table = ['| Proposed panel | Exposures | Source bytes (GB) | Raw bytes (GB) | Processed bytes (GB) |',
             '| --- | ---: | ---: | ---: | ---: |']
    for phase in policy['phases'] + ['TOTAL']:
        values = costs[phase] if phase != 'TOTAL' else {c: sum(v[c] for v in costs.values()) for c in COLLECTIONS}
        count = sum(x['phase'] == phase for x in selected) if phase != 'TOTAL' else len(selected)
        table.append('| ' + phase + f' | {count} | ' + ' | '.join(f'{values[c]:,} ({values[c]/1e9:.3f})' for c in COLLECTIONS) + ' |')
    template = (root / PREP / 'reviewer-packet-template.md').read_text(encoding='utf-8')
    replacements = {'PROPOSAL_COUNT': len(selected), 'ACTION_COUNT': len({r['action_id'] for r in steward}),
                    'QUEUE_COUNT': len(queue), 'RESERVED_COUNT': len(selected)-len(queue), 'COST_TABLE': '\n'.join(table)}
    for key, value in replacements.items():
        template = template.replace('{{' + key + '}}', str(value))
    if '{{' in template:
        raise ValueError('Unresolved reviewer-packet placeholder')
    artifacts = {'reviewer-packet.md': template.encode('utf-8'), 'reviewer-queue.csv': csv_bytes(queue, QUEUE_FIELDS),
                 'steward-crosswalk.csv': csv_bytes(steward, STEWARD_FIELDS)}
    receipt = {
        'status': policy['status'], 'proposal_count': len(steward), 'distinct_actions': len({r['action_id'] for r in steward}),
        'reviewer_queue_count': len(queue), 'confirmation_reserve_count': len(steward)-len(queue),
        'phase_bucket_counts': {p: dict(Counter(r['selection_bucket'] for r in steward if r['phase'] == p)) for p in policy['phases']},
        'phase_camera_counts': {p: dict(Counter(r['camera_serial'] for r in steward if r['phase'] == p)) for p in policy['phases']},
        'phase_coverage_regimes': {p: dict(Counter(r['coverage_regime'] for r in steward if r['phase'] == p)) for p in policy['phases']},
        'native_representation_bytes': costs, 'excluded_known_browse_capture_ids': sorted(excluded),
        'exclusion_history_scope': 'Pinned Stage 8B browse manifest only; not a whole-history independence certificate',
        'source_hashes': before,
        'artifacts': {name: {'bytes': len(payload), 'sha256': sha(payload)} for name, payload in artifacts.items()},
        'effects': {'pixel_bytes_acquired': 0, 'probability_sample_drawn': False, 'content_labels_assigned': False,
                    'reviewers_assigned': False, 'external_contact': False, 'public_release': False},
        'unverified': ['concept rubric', 'independent content reference', 'image/display hashes', 'rendering and masking',
                       'secondary targets', 'live URL reachability and size', 'preview availability and size',
                       'reviewer qualification/acceptance', 'probability inference', 'human first use'],
    }
    if before != {name: sha((root / name).read_bytes()) for name in input_names}:
        raise ValueError('Input generation changed during preparation')
    artifacts['preparation-receipt.json'] = (json.dumps(receipt, indent=2, ensure_ascii=True) + '\n').encode('utf-8')
    return artifacts, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Create missing canonical proposal artifacts; refuse differing existing bytes')
    parser.add_argument('--check', action='store_true', help='Compare canonical artifacts with deterministic replay; no writes')
    args = parser.parse_args()
    if args.write and args.check:
        parser.error('Select write or check, not both')
    artifacts, receipt = build()
    if (ROOT / PREP).resolve() != ROOT / PREP:
        raise ValueError('Canonical preparation directory is redirected')
    # Validate every target before any write. No overwrite or crash-atomicity claim.
    for name, payload in artifacts.items():
        path = ROOT / PREP / name
        if path.is_symlink() or (path.exists() and path.read_bytes() != payload):
            raise ValueError('Existing artifact differs; version/reconcile instead of overwriting: ' + name)
        if args.check and not path.is_file():
            raise ValueError('Canonical artifact missing: ' + name)
    if args.write:
        for name, payload in artifacts.items():
            path = ROOT / PREP / name
            if not path.exists():
                with path.open('xb') as stream:
                    stream.write(payload)
    print(json.dumps({k: receipt[k] for k in ['status', 'proposal_count', 'distinct_actions', 'reviewer_queue_count',
                                              'confirmation_reserve_count', 'native_representation_bytes', 'effects']}, ensure_ascii=True))


if __name__ == '__main__':
    main()
