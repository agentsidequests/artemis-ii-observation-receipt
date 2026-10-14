"""Read-only consumer of a frozen, assumption-bound target-weight analysis."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

UNITS = ('exposure_fields', 'products', 'data_source_bytes', 'data_raw_bytes',
         'data_processed_bytes', 'all_representation_bytes')
BUDGETS = (0, 1, 25, 47, 48, 50, 100, 200)
POPULATIONS = ('full_cohort', 'frozen_nonblank_subset')
COLLECTIONS = ('data_source', 'data_raw', 'data_processed')
QUALIFIED_SOURCE_SHA256 = {
    'contract': '8930e45b9e01be7c7887ae3fbb905be81dd3d0dbcb46cde9d9a7c66a8ac850bf',
    'result': 'afa22634e5bd5883d6bf5b22b76a708df3f7c976011786e94c045ef695a64c76',
    'manifest': '8edd58437cc609229edb5abb41c4e00048bb420354f1ac17a269da92c17e4729',
}
FORBIDDEN = {'observed_tag_errors', 'validated_content_labels', 'physical_prevalence',
             'statistical_confidence_interval', 'audit_sample_size', 'actual_audit_or_pixel_access',
             'cost_optimal_under_heterogeneous_cost', 'physical_identity_or_independence',
             'nasa_acceptance_or_global_novelty', 'replacement_of_existing_scientific_receipts'}
ASSUMPTIONS = {
    'blank_membership': 'unconstrained binary membership for one target value',
    'recorded_membership': 'fixed at r=0; at most r binary target memberships may be reassigned in each separate sensitivity extremum',
    'selection': 'original nonblank query frozen; a reassigned recorded field stays nonblank',
    'weights': 'positive fixed integer archive-accounting weights, not scientific value or exposure time',
    'resolution_cost': 'one unit per individual field; real viewing, adjudication, retrieval and support costs unknown',
    'grouping': 'original frozen filename/order-conditioned capture keys; physical identity unvalidated',
}


def serialize(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def read_artifact(artifact, root):
    if set(artifact) != {'path', 'bytes', 'sha256'}:
        raise ValueError('Source descriptor must contain only path, bytes and sha256')
    if type(artifact['bytes']) is not int or artifact['bytes'] <= 0:
        raise ValueError('Source byte length must be a positive integer')
    digest = artifact['sha256']
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Source SHA-256 must be 64 lowercase hex characters')
    if not isinstance(artifact['path'], str) or not artifact['path'] or Path(artifact['path']).is_absolute():
        raise ValueError('Source path must be relative to the supplied root')
    path = (root / artifact['path']).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError('Source path escapes the supplied root') from exc
    payload = path.read_bytes()
    if len(payload) != artifact['bytes'] or hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError('Source integrity mismatch; requalify explicitly: ' + artifact['path'])
    return payload


def fields_from_manifest(payload):
    grouped = {}
    product_ids = set()
    for number, row in enumerate(csv.DictReader(io.StringIO(payload.decode('utf-8'))), 2):
        identifier, product, collection = row['capture_identity'], row['product_id'], row['collection_id']
        if not identifier or not product or product in product_ids or collection not in COLLECTIONS:
            raise ValueError('Invalid or duplicate source identity')
        product_ids.add(product)
        size = int(row['archive_size_bytes'])
        if size <= 0:
            raise ValueError('Archive weights must be positive integers')
        item = grouped.setdefault(identifier, {'id': identifier, 'action': row['action_id'],
                                  'activity': row['activity_id'], 'target': row['target_id'],
                                  'products': {}})
        if collection in item['products'] or any(item[k] != row[v] for k, v in
                                                [('action', 'action_id'), ('activity', 'activity_id'), ('target', 'target_id')]):
            raise ValueError('Inconsistent representation or capture metadata')
        item['products'][collection] = {'id': product, 'row': number, 'bytes': size}
    if not grouped or any(set(f['products']) != set(COLLECTIONS) for f in grouped.values()):
        raise ValueError('Incomplete three-representation inventory')
    for f in grouped.values():
        sizes = [f['products'][c]['bytes'] for c in COLLECTIONS]
        f['weights'] = dict(zip(UNITS, [1, 3, *sizes, sum(sizes)]))
    return dict(sorted(grouped.items()))


def _ratio(value, numerator, denominator):
    if type(value.get('numerator')) is not int or type(value.get('denominator')) is not int:
        raise ValueError('Ratio decisions require exact integers')
    if (value['numerator'], value['denominator']) != (numerator, denominator) or denominator <= 0:
        raise ValueError('Saved ratio does not match the source recount')


def validate_accounting(result, fields):
    """Consumer parity checks, not an independent scientific oracle."""
    summaries = result['units']
    intervals = result['reassignment_sensitivity']
    if [s['unit'] for s in summaries] != list(UNITS) or len(intervals) != 96:
        raise ValueError('Incomplete saved calculation panel')
    keyed = {}
    for b in intervals:
        key = (b['unit'], b['population'], b['reassignment_budget'])
        if type(b['reassignment_budget']) is not int or key in keyed:
            raise ValueError('Duplicate or invalid saved scenario')
        keyed[key] = b
    expected_keys = {(u, p, r) for u in UNITS for p in POPULATIONS for r in BUDGETS}
    if set(keyed) != expected_keys:
        raise ValueError('Saved scenarios do not match the declared controls')
    for (unit, population, budget), b in keyed.items():
        selected = [f for f in fields.values() if population == 'full_cohort' or f['target']]
        order = lambda subset: sorted(subset, key=lambda f: (-f['weights'][unit], f['id']))
        positives = order([f for f in selected if f['target'] == 'Sunset'])
        negatives = order([f for f in selected if f['target'] and f['target'] != 'Sunset'])
        total = sum(f['weights'][unit] for f in selected)
        known = sum(f['weights'][unit] for f in positives)
        blank = sum(f['weights'][unit] for f in selected if not f['target'])
        lower = known - sum(f['weights'][unit] for f in positives[:budget])
        upper = known + blank + sum(f['weights'][unit] for f in negatives[:budget])
        if any(type(b[k]) is not int or b[k] != v for k, v in
               [('total_weight', total), ('known_target_weight', known), ('blank_weight', blank)]):
            raise ValueError('Saved denominator or partition weight mismatch')
        for name, value in [('lower', lower), ('upper', upper), ('width', upper - lower)]:
            _ratio(b[name], value, total)
        if (b['lower_reassigned_ids'] != [f['id'] for f in positives[:budget]] or
                b['upper_reassigned_ids'] != [f['id'] for f in negatives[:budget]] or
                b['extrema_are_separate_witnesses'] is not True):
            raise ValueError('Saved endpoint witness mismatch')
    for summary in summaries:
        unit = summary['unit']
        if summary['completion'] != keyed[(unit, 'full_cohort', 0)] or summary['selected'] != keyed[(unit, 'frozen_nonblank_subset', 0)]:
            raise ValueError('Summary/baseline panel disagreement')
        weight = lambda f: f['weights'][unit]
        descending = lambda subset: sorted(subset, key=lambda f: (-weight(f), f['id']))
        selected = [f for f in fields.values() if f['target']]
        positives = descending([f for f in selected if f['target'] == 'Sunset'])
        total = sum(map(weight, selected))
        known = sum(map(weight, positives))
        majority = summary['majority_sensitivity']
        minimum = 0
        remaining = known
        while 2 * remaining > total:
            remaining -= weight(positives[minimum])
            minimum += 1
        if type(majority['minimum_fields_to_lose_strict_majority']) is not int or majority['minimum_fields_to_lose_strict_majority'] != minimum:
            raise ValueError('Majority minimum mismatch')
        if majority['reassigned_ids'] != [f['id'] for f in positives[:minimum]] or majority['initial_strict_majority'] is not (2 * known > total):
            raise ValueError('Majority witness mismatch')
        _ratio(majority['original'], known, total)
        _ratio(majority['after'], remaining, total)
        if minimum:
            _ratio(majority['predecessor'], remaining + weight(positives[minimum - 1]), total)
        elif majority['predecessor'] is not None:
            raise ValueError('Unexpected majority predecessor')
        blanks = descending([f for f in fields.values() if not f['target']])
        full_total = sum(weight(f) for f in fields.values())
        for label, denominator in [('10pp', 10), ('5pp', 20), ('1pp', 100)]:
            entry = summary['completion_budgets'][label]
            _ratio(entry['target_width'], 1, denominator)
            residual = sum(map(weight, blanks))
            n = 0
            while residual * denominator > full_total:
                residual -= weight(blanks[n])
                n += 1
            if type(entry['minimum_fields_resolved_equal_field_cost']) is not int or entry['minimum_fields_resolved_equal_field_cost'] != n:
                raise ValueError('Completion minimum mismatch')
            if entry['resolved_ids'] != [f['id'] for f in blanks[:n]] or entry['real_resolution_or_cost_optimality'] is not False:
                raise ValueError('Completion witness mismatch')
            _ratio(entry['remaining_width'], residual, full_total)
            if n:
                _ratio(entry['predecessor_width'], residual + weight(blanks[n - 1]), full_total)
            elif entry['predecessor_width'] is not None:
                raise ValueError('Unexpected completion predecessor')


def evaluate(case, root):
    required = {'case_kind', 'case_version', 'case_id', 'title', 'sources', 'defaults'}
    if set(case) != required or case['case_kind'] != 'tag_weight_robustness' or case['case_version'] != '1.0.0':
        raise ValueError('Use the separate tag-weight case v1.0.0 contract')
    if not isinstance(case['title'], str) or not case['title'] or case['case_id'] != 'artemis-ii-tag-weight-robustness':
        raise ValueError('Invalid robustness case identity')
    defaults = case['defaults']
    if (set(defaults) != {'unit', 'population', 'budget'} or defaults['unit'] not in UNITS or
            defaults['population'] not in POPULATIONS or type(defaults['budget']) is not int or defaults['budget'] not in BUDGETS):
        raise ValueError('Choose a declared unit, population and hypothetical budget')
    if set(case['sources']) != {'contract', 'result', 'manifest'}:
        raise ValueError('All three frozen source artifacts are required')
    payloads = {name: read_artifact(artifact, root) for name, artifact in case['sources'].items()}
    if any(case['sources'][name]['sha256'] != digest for name, digest in QUALIFIED_SOURCE_SHA256.items()):
        raise ValueError('Changed source snapshot requires explicit code/case qualification; editing the case hash alone is insufficient')
    contract, result = (json.loads(payloads[name]) for name in ['contract', 'result'])
    if (contract['target'] != 'Sunset' or contract['units'] != list(UNITS) or
            contract['recorded_field_reassignment_budgets'] != list(BUDGETS) or
            contract['assumptions'] != ASSUMPTIONS):
        raise ValueError('Unsupported target, control panel or cost assumption')
    for declaration in [contract['forbidden_claims'], result['forbidden_claims']]:
        if set(declaration) != FORBIDDEN or any(v is not False for v in declaration.values()):
            raise ValueError('Unsupported scientific declaration')
    if (result['evidence_state'] != 'COMPUTED_ASSUMPTION_BOUND_METADATA_SENSITIVITY' or
            type(result['new_pixel_bytes_opened']) is not int or result['new_pixel_bytes_opened'] != 0 or
            result['source_or_prior_receipts_modified'] is not False or
            result['claim_ceiling'] != contract['claim_ceiling']):
        raise ValueError('Unsupported result scope or claim ceiling')
    source = contract['source']
    if (source['bytes'] != len(payloads['manifest']) or source['sha256'] != hashlib.sha256(payloads['manifest']).hexdigest() or
            result['source_identity'] != {**source, 'match': True} or result['id'] != contract['id'] or result['pass'] is not True):
        raise ValueError('Analysis/source identity disagreement')
    fields = fields_from_manifest(payloads['manifest'])
    partition = {'products': len(fields) * 3, 'exposure_fields': len(fields),
                 'recorded_fields': sum(bool(f['target']) for f in fields.values()),
                 'blank_fields': sum(not f['target'] for f in fields.values()),
                 'recorded_sunset_fields': sum(f['target'] == 'Sunset' for f in fields.values())}
    if result['partition'] != partition or contract['frozen_partition'] != partition:
        raise ValueError('Frozen partition mismatch')
    validate_accounting(result, fields)
    return {'case_kind': case['case_kind'], 'case_version': case['case_version'], 'case_id': case['case_id'],
            'title': case['title'], 'pass': True, 'verification': 'SOURCE_VERIFIED_AT_BUILD_AND_ACCOUNTING_RECOUNTED',
            'defaults': defaults, 'sources': case['sources'], 'analysis': result, 'fields': fields,
            'assumptions': contract['assumptions'], 'source_manifest_locator': source['path'],
            'acceptance': 'Consumer parity only; uncoached comprehension, accessibility conformance and scientific acceptance unverified.'}


def csv_text(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def export_rows(receipt):
    endpoints = []
    for index, b in enumerate(receipt['analysis']['reassignment_sensitivity']):
        for endpoint in ['lower', 'upper']:
            endpoints.append({'unit': b['unit'], 'population': b['population'], 'hypothetical_budget': b['reassignment_budget'],
                              'endpoint': endpoint, 'numerator': b[endpoint]['numerator'], 'denominator': b['total_weight'],
                              'separate_witness': 'true', 'observed_error': 'false',
                              'result_pointer': f'/reassignment_sensitivity/{index}/{endpoint}'})
    fields = []
    for f in receipt['fields'].values():
        for collection, product in f['products'].items():
            fields.append({'capture_identity': f['id'], 'original_action_id': f['action'], 'activity_id': f['activity'],
                           'original_target': f['target'], 'collection': collection, 'product_id': product['id'],
                           'archive_bytes': product['bytes'], 'manifest_csv_row': product['row'],
                           'manifest_parent': receipt['source_manifest_locator'],
                           'manifest_sha256': receipt['sources']['manifest']['sha256'], 'physical_identity_validated': 'false'})
    witnesses = []
    for index, b in enumerate(receipt['analysis']['reassignment_sensitivity']):
        for endpoint in ['lower', 'upper']:
            for rank, identifier in enumerate(b[endpoint + '_reassigned_ids'], 1):
                f = receipt['fields'][identifier]
                witnesses.append({'unit': b['unit'], 'population': b['population'], 'hypothetical_budget': b['reassignment_budget'],
                                  'endpoint': endpoint, 'rank': rank, 'capture_identity': identifier,
                                  'original_action_id': f['action'], 'activity_id': f['activity'], 'original_target': f['target'],
                                  'counterfactual_target': 'non-Sunset nonblank' if endpoint == 'lower' else 'Sunset',
                                  'weight': f['weights'][b['unit']], 'result_pointer': f'/reassignment_sensitivity/{index}/{endpoint}_reassigned_ids/{rank-1}',
                                  'manifest_csv_rows': '|'.join(str(f['products'][c]['row']) for c in COLLECTIONS),
                                  'kind': 'hypothetical_reassignment_not_observed_error'})
    return endpoints, fields, witnesses


def write_bundle(receipt, output):
    template = Path(__file__).with_name('robustness-viewer.html').read_text(encoding='utf-8')
    data = json.dumps(receipt, separators=(',', ':'), ensure_ascii=False, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    atlas = Path(__file__).with_name('assumption-atlas.js').read_text(encoding='utf-8')
    page = template.replace('__RECEIPT_DATA__', data).replace('__ATLAS_SCRIPT__', atlas)
    endpoints, fields, witnesses = export_rows(receipt)
    content = {'index.html': page.encode('utf-8'), 'receipt.json': serialize(receipt),
               'bound-endpoints.csv': csv_text(endpoints), 'source-fields.csv': csv_text(fields),
               'reassignment-witnesses.csv': csv_text(witnesses)}
    manifest = {'case_id': receipt['case_id'], 'files': [{'path': name, 'bytes': len(payload),
                'sha256': hashlib.sha256(payload).hexdigest()} for name, payload in sorted(content.items())]}
    content['manifest.json'] = serialize(manifest)
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in content.items():
        (output / name).write_bytes(payload)
    return {name: output / name for name in content}
