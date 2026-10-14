"""Conditional five-key exclusion; frozen science receipts are never replaced."""

import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / 'paper-review/downstream-sensitivity'
sys.path.insert(0, str(ROOT / 'src'))
from src import stage11r_hierarchical_test_isolation as relationship
from src import stage11t_opportunity_concentration as opportunity
from src import stage11u_selection_weighting_cascade as weighting
from src import stage11v_target_completion_bounds as completion
from src import stage10w_target_tag_selection as selection


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_csv(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def verify_pin(pin):
    payload = (ROOT / pin['path']).read_bytes()
    if len(payload) != pin['bytes'] or hashlib.sha256(payload).hexdigest() != pin['sha256']:
        raise ValueError('Frozen input changed: ' + pin['path'])


def close_tree(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and set(actual) == set(expected) and all(close_tree(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(close_tree(a, b) for a, b in zip(actual, expected))
    if type(expected) is float:
        return type(actual) in [int, float] and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
    return type(actual) is type(expected) and actual == expected


def exclude_action(manifest, assignments, memberships, action_id, expected_captures):
    """Return filtered views without modifying input dictionaries or group keys."""
    by_product = {row['product_id']: row for row in manifest}
    assigned = {row['product_id']: row for row in assignments}
    if len(by_product) != len(manifest) or len(assigned) != len(assignments) or set(by_product) != set(assigned):
        raise ValueError('Duplicate or incomplete product/assignment join')
    for identifier, row in by_product.items():
        if any(row[field] != assigned[identifier][field] for field in ['capture_identity', 'action_id', 'temporal_cluster_5s']):
            raise ValueError('Assignment relationship differs from manifest')
    removed = [row for row in manifest if row['action_id'] == action_id]
    if not removed or {row['capture_identity'] for row in removed} != set(expected_captures):
        raise ValueError('Wrong action or capture-key exclusion')
    for capture in expected_captures:
        layers = [row for row in removed if row['capture_identity'] == capture]
        if len(layers) != 3 or {row['collection_id'] for row in layers} != {'data_source', 'data_raw', 'data_processed'}:
            raise ValueError('Partial or repeated representation exclusion')
        if any(row['capture_identity'] == capture and row['action_id'] != action_id for row in manifest):
            raise ValueError('A removed capture has another action owner')
    removed_ids = {row['product_id'] for row in removed}
    retained = [row for row in manifest if row['product_id'] not in removed_ids]
    retained_assignments = [row for row in assignments if row['product_id'] not in removed_ids]
    retained_memberships = [row for row in memberships if row['action_id'] != action_id]
    if not retained or any(row['action_id'] == action_id for row in retained + retained_assignments + retained_memberships):
        raise ValueError('Empty or incomplete withheld view')
    return retained, retained_assignments, retained_memberships, removed


def opportunity_metrics(manifest, memberships):
    """Compose unchanged Stage 11T primitives in memory; no source-path mutation."""
    totals = opportunity.action_totals(manifest)
    windows, action_windows = opportunity.active_memberships(memberships)
    raw_denominators = {action: 1 for action in action_windows}
    fractional_denominators = {action: len(orders) for action, orders in action_windows.items()}
    raw = opportunity.weighted_groups(windows, totals, raw_denominators)
    fractional = opportunity.weighted_groups(windows, totals, fractional_denominators)
    clusters, window_clusters = opportunity.collapse_same_name_windows(windows)
    action_clusters = {action: {window_clusters[order] for order in orders} for action, orders in action_windows.items()}
    collapsed = opportunity.weighted_groups(clusters, totals, {action: len(groups) for action, groups in action_clusters.items()})
    expected = {unit: sum(totals[action][unit] for action in action_windows) for unit in opportunity.UNITS}
    conservation = {unit: {'expected_unique_total': expected[unit],
                            'fractional_window_total': sum(group[unit] for group in fractional),
                            'collapsed_fractional_total': sum(group[unit] for group in collapsed),
                            'window_match': math.isclose(expected[unit], sum(group[unit] for group in fractional), rel_tol=0.0, abs_tol=1e-6),
                            'collapsed_match': math.isclose(expected[unit], sum(group[unit] for group in collapsed), rel_tol=0.0, abs_tol=1e-6)}
                    for unit in opportunity.UNITS}
    names = Counter(window['plan_target_name'] for window in windows.values())
    collapsed_names = Counter(group['plan_target_name'] for group in clusters.values())
    return {'active_windows': len(windows), 'exact_plan_names': len(names), 'unique_active_actions': len(action_windows),
            'raw_concentration_equivalent_windows': opportunity.concentration_metrics(raw),
            'fractional_concentration_equivalent_windows': opportunity.concentration_metrics(fractional),
            'collapsed_same_name_clusters': len(clusters),
            'collapsed_fractional_concentration_equivalent_windows': opportunity.concentration_metrics(collapsed),
            'replication_debt': {'exact_windows_k2': opportunity.replication_debt(dict(names), 2),
                                 'exact_windows_k3': opportunity.replication_debt(dict(names), 3),
                                 'collapsed_clusters_k2': opportunity.replication_debt(dict(collapsed_names), 2),
                                 'collapsed_clusters_k3': opportunity.replication_debt(dict(collapsed_names), 3)},
            'exact_name_window_counts': dict(sorted(names.items())), 'collapsed_name_cluster_counts': dict(sorted(collapsed_names.items())),
            'fractional_conservation': conservation, 'same_name_overlap_collapses': len(windows) - len(clusters)}


def metrics(manifest, assignments, memberships):
    coverage, examples, cameras = selection.derive(manifest)
    return {'relationship': relationship.analyze_assignments(assignments),
            'selection': {'coverage': coverage, 'activity_examples': examples, 'camera_coverage': cameras},
            'opportunity_weighting': opportunity_metrics(manifest, memberships),
            'selection_weighting': weighting.derive(manifest), 'field_completion': completion.derive(manifest)}


def conclusion_flags(result):
    weight = result['selection_weighting']
    strict = weight['strict_tagged_weighting_panel']
    tiers = weight['collection_byte_sensitivity']
    raw = result['opportunity_weighting']['raw_concentration_equivalent_windows']
    return {
        'zero_action_isolated_test_products': result['relationship']['action_isolated_test_products'] == 0,
        'tagged_subset_incomplete_and_activity_structured': result['selection']['coverage']['target_tag_blank'] > 0
            and result['selection']['coverage']['zero_coverage_activities'] > 0 and result['selection']['coverage']['full_coverage_activities'] > 0,
        'selected_sunset_action_minority_byte_majority': strict['sunset_share_of_selected_actions'] < .5 < strict['sunset_share_of_tagged_bytes'],
        'source_tier_sunset_minority_raw_processed_majorities': tiers['data_source']['sunset_share'] < .5
            and tiers['data_raw']['sunset_share'] > .5 and tiers['data_processed']['sunset_share'] > .5,
        'most_sunset_tagged_keys_from_24_sunset_activity': weight['activity_structure_attribution']['share_of_sunset_tagged_exposures_from_activity'] > .5,
        'outside_24_sunset_activity_byte_share_below_half': weight['activity_structure_attribution']['outside_activity']['sunset_share_of_tagged_bytes'] < .5,
        'raw_window_concentration_action_above_product_above_byte': raw['actions'] > raw['products'] > raw['archive_size_bytes'],
        'sunset_field_completion_interval_spans_half': result['field_completion']['sunset']['lower_share_full_cohort'] < .5
            < result['field_completion']['sunset']['upper_share_full_cohort'],
    }


def flattened(value, prefix=''):
    if isinstance(value, dict):
        return {key: cell for name, child in value.items() for key, cell in flattened(child, prefix + '.' + name if prefix else name).items()}
    if type(value) in [bool, int, float, str] or value is None:
        return {prefix: value}
    return {}


def comparison_rows(baseline, withheld):
    old, changed = flattened(baseline), flattened(withheld)
    if set(old) != set(changed):
        raise ValueError('Metric schema changed across the sensitivity')
    return [{'metric': name, 'baseline': old[name], 'withheld': changed[name],
             'delta': changed[name] - old[name] if type(old[name]) in [int, float] and type(changed[name]) in [int, float] else None,
             'changed': old[name] != changed[name]} for name in sorted(old)]


def replay():
    contract = load_json(OWNER / 'contract.json')
    if any(value is not False for value in contract['limits'].values()) or contract['effects'] != {
        'network_requests': 0, 'new_image_bytes': 0, 'outreach': False, 'publication': False, 'remote_push': False}:
        raise ValueError('Sensitivity cannot grant adoption, scientific or external-effect authority')
    for pin in contract['input_pins']:
        verify_pin(pin)
    candidate = load_json(ROOT / 'paper-review/order-robust-reconstruction/result.json')
    families = [family for family in candidate['families'] if any(contract['action_id'] in member['baseline_action_ids']
                for slot in family['slots'] for member in slot['members'])]
    if len(families) != 1 or families[0]['status'] != 'IDENTITY_ALTERNATIVES_ABSTAIN':
        raise ValueError('The selected original action is not the declared withheld family')
    manifest = load_csv(ROOT / 'results/stage10o-product-relationship-manifest.csv')
    assignments = load_csv(ROOT / 'results/stage11l-split-assignments.csv')
    memberships = load_csv(ROOT / 'results/stage10z-action-plan-membership.csv')
    retained, selected_assignments, selected_memberships, removed = exclude_action(manifest, assignments, memberships, contract['action_id'], contract['capture_keys'])
    if len(removed) != contract['expected_removed_products'] or len(manifest) != 22818 or len(retained) != 22803:
        raise ValueError('Conditional product count changed')
    baseline, withheld = metrics(manifest, assignments, memberships), metrics(retained, selected_assignments, selected_memberships)
    expected = {
        'relationship': load_json(ROOT / 'results/stage11r-hierarchical-isolation.json')['structural_isolation'],
        'opportunity_weighting': load_json(ROOT / 'results/stage11t-result.json')['metrics'],
        'selection_weighting': load_json(ROOT / 'results/stage11u-selection-weighting-cascade.json')['metrics'],
        'field_completion': load_json(ROOT / 'results/stage11v-result.json')['metrics'],
        'selection': {name: load_json(ROOT / 'results/stage10w-result.json')[name] for name in ['coverage','activity_examples','camera_coverage']},
    }
    baseline_checks = {name: close_tree(baseline[name], values) for name, values in expected.items()}
    if not all(baseline_checks.values()):
        raise ValueError('Unchanged baseline calculation does not match canonical receipts: ' + str(baseline_checks))
    byte_totals = {collection: sum(int(row['archive_size_bytes']) for row in removed if row['collection_id'] == collection)
                   for collection in ['data_source','data_raw','data_processed']}
    by_product = {row['product_id']: row for row in assignments}
    removed_witnesses = [{**row, **{field: by_product[row['product_id']][field] for field in [
        'product_key_partition','action_key_partition','temporal_5s_key_partition']}} for row in removed]
    old_flags, new_flags = conclusion_flags(baseline), conclusion_flags(withheld)
    return {'status': 'VERIFIED_CONDITIONAL_ONE_ACTION_WITHHOLDING_SENSITIVITY', 'contract': contract,
            'baseline_replay_checks': baseline_checks,
            'removal': {'action_id': contract['action_id'], 'capture_keys': contract['capture_keys'], 'products': len(removed),
                        'bytes_by_collection': byte_totals, 'archive_bytes': sum(byte_totals.values()),
                        'original_plan_orders': sorted({row['plan_order'] for row in memberships if row['action_id'] == contract['action_id']}),
                        'original_target_fields': sorted({row['target_id'] for row in removed}),
                        'original_activity_fields': sorted({row['activity_id'] for row in removed}),
                        'product_key_partitions': dict(sorted(Counter(by_product[row['product_id']]['product_key_partition'] for row in removed).items())),
                        'witnesses': removed_witnesses},
            'baseline': baseline, 'conditional_withheld': withheld,
            'conclusions': {name: {'baseline': old_flags[name], 'withheld': new_flags[name], 'same_boolean_disposition': old_flags[name] == new_flags[name]}
                            for name in old_flags},
            'comparison': comparison_rows(baseline, withheld),
            'scope_checks': {'active_window_names_unchanged': baseline['opportunity_weighting']['exact_name_window_counts'] == withheld['opportunity_weighting']['exact_name_window_counts'],
                             'replication_debt_unchanged': baseline['opportunity_weighting']['replication_debt'] == withheld['opportunity_weighting']['replication_debt'],
                             'completion_budgets_unchanged': baseline['field_completion']['deterministic_completion_budgets'] == withheld['field_completion']['deterministic_completion_budgets']},
            'limits': contract['limits'], 'effects': contract['effects'],
            'detection_disposition': 'Protected detection receipts remain byte-identical and are not recomputed; no detection-completeness or flux claim is upgraded.',
            'provenance': {'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'input_pins': contract['input_pins']}}


def artifacts(result):
    json_bytes = (json.dumps(result, indent=2, allow_nan=False) + '\n').encode('utf-8')
    comparison = io.StringIO(newline='')
    writer = csv.DictWriter(comparison, fieldnames=['metric','baseline','withheld','delta','changed'], lineterminator='\n')
    writer.writeheader()
    writer.writerows(result['comparison'])
    witnesses = io.StringIO(newline='')
    rows = result['removal']['witnesses']
    writer = csv.DictWriter(witnesses, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return {'result.json': json_bytes, 'comparison.csv': comparison.getvalue().encode('utf-8'),
            'withheld-products.csv': witnesses.getvalue().encode('utf-8')}


def run(mode):
    result = replay()
    outputs = artifacts(result)
    for name, data in outputs.items():
        path = OWNER / name
        if path.exists() and path.read_bytes() != data:
            raise ValueError('Existing differing artifact; no overwrite: ' + name)
        if mode == '--check' and not path.exists():
            raise ValueError('Missing sensitivity artifact: ' + name)
    if mode == '--write':
        for name, data in outputs.items():
            path = OWNER / name
            if not path.exists():
                with path.open('xb') as stream:
                    stream.write(data)
    return {'status': result['status'], 'baseline_replay_checks': result['baseline_replay_checks'],
            'removed_products': result['removal']['products'], 'removed_bytes': result['removal']['archive_bytes'],
            'conclusions': result['conclusions'], 'scope_checks': result['scope_checks'],
            'artifact_hashes': {name: hashlib.sha256(data).hexdigest() for name,data in outputs.items()}}


if __name__ == '__main__':
    if sys.argv[1:] not in [['--write'],['--check']]:
        raise SystemExit('Use --write for absent/identical artifacts or --check for read-only replay')
    print(json.dumps(run(sys.argv[1]), indent=2, allow_nan=False))
