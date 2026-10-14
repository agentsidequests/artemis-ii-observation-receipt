"""Prepare a portable app fixture from two immutable local analysis receipts."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / 'observation-receipt/cases/artemis-ii-identity'
PINS = {
    'paper-review/downstream-sensitivity/result.json': '88c5451bed59ef2536c790459b3fffc92d566e93069349826f2a85e02adb79bf',
    'paper-review/order-robust-reconstruction/result.json': 'cee99d8716d628b70191e682af118e61ff2f78b5018066df424fb023f19a4d34',
}


def serialized(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def prepare():
    inputs = {}
    for path, digest in PINS.items():
        payload = (ROOT / path).read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError('Frozen analysis input changed: ' + path)
        inputs[path] = payload
    sensitivity = json.loads(inputs['paper-review/downstream-sensitivity/result.json'])
    candidate = json.loads(inputs['paper-review/order-robust-reconstruction/result.json'])
    action = sensitivity['removal']['action_id']
    families = [f for f in candidate['families'] if any(action in m['baseline_action_ids'] for s in f['slots'] for m in s['members'])]
    if len(families) != 1 or families[0]['status'] != 'IDENTITY_ALTERNATIVES_ABSTAIN':
        raise ValueError('Expected one unresolved original family')
    ambiguous = [s for s in families[0]['slots'] if len(s['members']) > 1]
    if len(ambiguous) != 1:
        raise ValueError('Expected one alternative slot')
    excerpt = {'parent_path': 'paper-review/order-robust-reconstruction/result.json',
               'parent_sha256': PINS['paper-review/order-robust-reconstruction/result.json'],
               'family': families[0], 'alternatives': [m['capture_key'] for m in ambiguous[0]['members']],
               'scope': 'Exact derived family excerpt, not physical identity validation. Parent is verified by the private preparation command, not bundled or independently reconstructed by the portable app.'}
    files = {'sources/downstream-sensitivity.json': inputs['paper-review/downstream-sensitivity/result.json'],
             'sources/metadata-family-excerpt.json': serialized(excerpt)}
    def artifact(identifier, name, producer):
        data = files['sources/' + name]
        return {'id': identifier, 'path': 'cases/artemis-ii-identity/sources/' + name,
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                'media_type': 'application/json', 'producer': producer, 'archive': 'Frozen local analysis',
                'derivation_state': 'derived'}
    definitions = [
        ('products','Product rows','selection_weighting/all_cohort/products','count',1,0),
        ('captures','Native capture keys','selection/coverage/source_exposures','count',1,0),
        ('actions','Original reconstructed actions','selection_weighting/all_cohort/actions','count',1,0),
        ('test','Test products','relationship/test_products','count',1,0),
        ('capture_linked','Capture-linked test products','relationship/capture_linked_test_products','count',1,0),
        ('action_linked','Additional action-only-linked test products','relationship/action_only_linked_test_products','count',1,0),
        ('isolated','Action-isolated test products','relationship/action_isolated_test_products','count',1,0),
        ('tagged','Nonblank source target fields','selection/coverage/target_tag_present','count',1,0),
        ('blank','Blank source target fields','selection/coverage/target_tag_blank','count',1,0),
        ('zero_activities','Zero-coverage activities','selection/coverage/zero_coverage_activities','count',1,0),
        ('full_activities','Full-coverage activities','selection/coverage/full_coverage_activities','count',1,0),
        ('sunset_action','Sunset share of selected actions','selection_weighting/strict_tagged_weighting_panel/sunset_share_of_selected_actions','percent',100,3),
        ('sunset_byte','Sunset share of combined selected bytes','selection_weighting/strict_tagged_weighting_panel/sunset_share_of_tagged_bytes','percent',100,3),
        ('source_byte','Sunset share of selected source bytes','selection_weighting/collection_byte_sensitivity/data_source/sunset_share','percent',100,3),
        ('raw_byte','Sunset share of selected raw bytes','selection_weighting/collection_byte_sensitivity/data_raw/sunset_share','percent',100,3),
        ('processed_byte','Sunset share of selected processed bytes','selection_weighting/collection_byte_sensitivity/data_processed/sunset_share','percent',100,3),
        ('activity_share','Sunset-tagged keys supplied by 24_Sunset','selection_weighting/activity_structure_attribution/share_of_sunset_tagged_exposures_from_activity','percent',100,3),
        ('outside_byte','Sunset byte share outside 24_Sunset','selection_weighting/activity_structure_attribution/outside_activity/sunset_share_of_tagged_bytes','percent',100,3),
        ('window_actions','Raw action-weighted concentration index','opportunity_weighting/raw_concentration_equivalent_windows/actions','index',1,3),
        ('window_products','Raw product-weighted concentration index','opportunity_weighting/raw_concentration_equivalent_windows/products','index',1,3),
        ('window_bytes','Raw byte-weighted concentration index','opportunity_weighting/raw_concentration_equivalent_windows/archive_size_bytes','index',1,3),
        ('completion_lower','Sunset field-completion lower bound','field_completion/sunset/lower_share_full_cohort','percent',100,3),
        ('completion_upper','Sunset field-completion upper bound','field_completion/sunset/upper_share_full_cohort','percent',100,3),
    ]
    metrics = [{'id': i, 'label': label, 'pointer': '/' + pointer, 'unit': unit, 'scale': scale, 'places': places}
               for i,label,pointer,unit,scale,places in definitions]
    def condition(metric, op, value=None, other=None):
        return {'metric_id': metric, 'op': op, **({'other_metric_id': other} if other else {'value': value})}
    predicates = [
        ('zero_action_isolated_test_products','Zero action-isolated test products',[condition('isolated','eq',0)]),
        ('tagged_subset_incomplete_and_activity_structured','Incomplete, activity-structured target-field selection',[condition('blank','gt',0),condition('zero_activities','gt',0),condition('full_activities','gt',0)]),
        ('selected_sunset_action_minority_byte_majority','Sunset action minority and combined-byte majority',[condition('sunset_action','lt',50),condition('sunset_byte','gt',50)]),
        ('source_tier_sunset_minority_raw_processed_majorities','Source-tier minority and raw/processed majorities',[condition('source_byte','lt',50),condition('raw_byte','gt',50),condition('processed_byte','gt',50)]),
        ('most_sunset_tagged_keys_from_24_sunset_activity','Most Sunset-tagged keys supplied by 24_Sunset',[condition('activity_share','gt',50)]),
        ('outside_24_sunset_activity_byte_share_below_half','Outside-activity Sunset byte share below half',[condition('outside_byte','lt',50)]),
        ('raw_window_concentration_action_above_product_above_byte','Raw concentration orders action above product above byte',[condition('window_actions','gt',other='window_products'),condition('window_products','gt',other='window_bytes')]),
        ('sunset_field_completion_interval_spans_half','Field-completion interval spans half',[condition('completion_lower','lt',50),condition('completion_upper','gt',50)]),
    ]
    ceiling = 'One conditional original-cohort view, not replaced counts, physical identity, target truth, model-performance harm, independent-event counts, calibrated impact flux or scientific acceptance.'
    case = {
        'receipt_version': '0.3.0', 'case_id': 'artemis-ii-one-action-identity-sensitivity',
        'title': 'One ambiguity. Two accounting views.',
        'summary': 'Withhold one original five-frame action without choosing between metadata alternatives or replacing the original receipts.',
        'viewer_context': {'key_distinction': 'Frozen original and conditional view are different populations. Eight predicates from one treatment are not eight independent replications. Physical identity remains unresolved.'},
        'artifacts': [artifact('sensitivity','downstream-sensitivity.json','Local source-pinned conditional calculation'),artifact('identity-excerpt','metadata-family-excerpt.json','Local lossless metadata-path excerpt')],
        'facts': {}, 'candidates': [], 'observation_windows': [], 'measurement_function': {},
        'identity_groups': [{'id':'final-slot','label':'Final-slot metadata alternatives','state':'unresolved','basis':'metadata_candidate',
                             'source_artifact_id':'identity-excerpt','alternatives_pointer':'/alternatives',
                             'source_locator':'Family ' + families[0]['family_id'] + ', final slot; nine exact recorded fields',
                             'note':'No representative selected. The whole original five-frame action is withheld only in the conditional comparison. Other withheld families are outside this comparison.'}],
        'conditional_comparisons': [{'id':'one-action','label':'One original five-frame action withheld', 'source_artifact_id':'sensitivity',
                                    'original_pointer':'/baseline','conditional_pointer':'/conditional_withheld',
                                    'original_label':'Frozen original cohort','conditional_label':'Conditional: one action withheld',
                                    'treatment':'Exclude only action ' + action + ': five original capture keys, all 15 representation rows and its two scheduled memberships. Keep surviving fields, splits and group keys fixed. Add no alternative IDs or new families.',
                                    'metrics':metrics, 'claim_ceiling':ceiling}],
        'claims': [{'id':'physical-identity','proposition':'These alternatives establish one physically validated identity',
                    'rule':{'kind':'identity_resolution_gate','group_id':'final-slot'},'claim_ceiling':'Matching metadata is an unresolved candidate, not a byte or physical-identity certificate.'}] +
                  [{'id': identifier,'proposition':label,'rule':{'kind':'conditional_comparison_gate','comparison_id':'one-action','conditions':conditions},'claim_ceiling':ceiling}
                   for identifier,label,conditions in predicates],
        'expected_findings': {'physical-identity':'BLOCKED_IDENTITY_UNRESOLVED', **{i:'SUPPORTED_CONDITIONAL_STABILITY' for i,_,_ in predicates}},
        'claim_ceiling': ceiling,
        'next_steps': ['Obtain qualified source-lineage and physical-grouping review before resolving identity.',
                       'Keep original numbers and this conditional sensitivity distinct in any private narrative.',
                       'A surviving predicate is not an adopted reconstruction or permission to publish.'],
    }
    files['case.json'] = serialized(case)
    return files


def run(mode):
    files = prepare()
    for name, payload in files.items():
        path = OWNER / name
        if path.exists() and path.read_bytes() != payload:
            raise ValueError('Existing different demo artifact; no overwrite: ' + name)
        if mode == '--check' and not path.exists():
            raise ValueError('Demo artifact absent: ' + name)
    if mode == '--write':
        for name, payload in files.items():
            path = OWNER / name
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(payload)
    return {name: {'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()} for name,payload in files.items()}


if __name__ == '__main__':
    if sys.argv[1:] not in [['--write'],['--check']]:
        raise SystemExit('Use --write for absent/identical fixture files or --check for read-only replay')
    print(json.dumps(run(sys.argv[1]), indent=2))
