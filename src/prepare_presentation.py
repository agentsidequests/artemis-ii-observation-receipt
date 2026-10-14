"""Compile bounded presentation excerpts from pinned, already-qualified receipts."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'observation-receipt'
sys.path.insert(0, str(APP / 'src'))
from observation_receipt import robustness
from observation_receipt.evaluator import evaluate_case

PINS = {
    'fanout': ('presentation/sources/fanout.json', 'b2bad4bc8ab5b308c5eec0b68fe9c54e070191185599bcca55676c0bb595c87e'),
    'relationship': ('presentation/sources/relationship.json', '939eb2da472c32ad570fb5230ba49d8e0ffa178e70fbff7bb595c10bf3cbd81b'),
    'selection': ('presentation/sources/selection.json', '7f2ddb8b91ef4f3a84e2271ac9640b5d78b23e963e0b94f19b42c9ecb9f7a212'),
    'concentration': ('presentation/sources/concentration.json', '067991afba7cff379a7d9520b73a1f70a8abc6e243528ce513ffecb77b213cab'),
    'attention': ('presentation/sources/attention.json', 'd4a86b02479c3940104f562874d66f40eaf5b4a3b25ba6b6d542a66cf161fd23'),
    'recovery': ('results/stage11q-injection-recovery.json', 'f8fc492f620a834aa05768e6a7318402188729a0ee60ba60f70c531cbf4585d0'),
    'screen': ('results/stage11p-overlap-pixel-screen.json', '7ab93b078e45fc5b381faa861373ccf51a2918a833dad0d5bff13fe810191af2'),
    'events': ('results/stage11n-result.json', '930be47399e76dde2b72bbf21422e1ea21598115dff362afe869570eccb25ae5'),
    'flash_case': ('observation-receipt/cases/artemis-ii-flashes/case.json', '2603b1bf433dbe886fd6f6413ce8a7e2028988b1de6f04806aa1ba7b0266bada'),
    'conditional': ('paper-review/downstream-sensitivity/result.json', '88c5451bed59ef2536c790459b3fffc92d566e93069349826f2a85e02adb79bf'),
    'robustness': ('paper-review/tag-weight-robustness/result.json', 'afa22634e5bd5883d6bf5b22b76a708df3f7c976011786e94c045ef695a64c76'),
    'readiness': ('presentation/sources/task-readiness.json', 'c7904c05e52798fed4c8dc78243c6e2bcf63f1cccff34e1d6675416e52cc286a'),
    'rank': ('presentation/sources/weighting-reversal.json', '0c312fd2285dd4ea9a65a5e465408abada013c348eb89667dd55b17bf3ec6b1c'),
    'identity_boundary': ('paper-review/identity-census/result.json', '4dedc409a22c6e4e0c24b387dec08644500d96231feab8941d27e24d4ee62f69'),
    'steward_case': ('observation-receipt/cases/artemis-ii-identity-confirmed/case.json', '69103e34043f8c7f0863f59b904ee59c79282294e697548db28b65dd745b8c24'),
    'steward_statement': ('observation-receipt/cases/artemis-ii-identity-confirmed/sources/steward-confirmation.json', 'edadc3e2dbba41506ddb3990e352b1324d951f22eba472c3e695196ded36d86e'),
}


def serialized(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def prepare(root=ROOT):
    parsed, sources = {}, {}
    for name, (relative, digest) in PINS.items():
        data = (root / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Qualified presentation input changed: ' + relative)
        parsed[name] = json.loads(data)
        sources[name] = {'path': relative, 'bytes': len(data), 'sha256': digest,
                         'verification': 'exact bytes at preparation; not independent scientific acceptance'}
    app = root / 'observation-receipt'
    rcase = json.loads((app / 'cases/artemis-ii-robustness/case.json').read_bytes())
    bound = robustness.evaluate(rcase, app)
    flash = evaluate_case(parsed['flash_case'], app)
    steward = evaluate_case(parsed['steward_case'], app)
    if not steward['pass'] or len(steward['steward_links'])!=1 or steward['steward_links'][0]['statement'] != parsed['steward_statement']['statement']:
        raise ValueError('Current steward relationship did not verify against its exact group and statement')
    if not flash['pass'] or not bound['pass']:
        raise ValueError('Existing app consumer did not pass')
    for name in ['fanout', 'relationship', 'selection', 'concentration', 'attention', 'recovery', 'screen', 'robustness', 'readiness', 'rank']:
        if parsed[name]['pass'] is not True:
            raise ValueError('Rejected parent receipt cannot be a presentation source')
    if parsed['conditional']['status'] != 'VERIFIED_CONDITIONAL_ONE_ACTION_WITHHOLDING_SENSITIVITY':
        raise ValueError('Conditional receipt status is not qualified')
    if parsed['identity_boundary']['status'] != 'VERIFIED_FROZEN_METADATA_CANDIDATE_LINKAGE_CENSUS':
        raise ValueError('Identity diagnostic status is not qualified')
    relation = parsed['relationship']['structural_isolation']
    if relation['test_products'] != sum(relation[k] for k in ['capture_linked_test_products', 'action_only_linked_test_products', 'action_isolated_test_products']):
        raise ValueError('Relationship bins do not conserve the fixed test population')
    if parsed['conditional']['baseline']['relationship'] != {k: relation[k] for k in parsed['conditional']['baseline']['relationship']}:
        raise ValueError('Audit-trail baseline does not match the original receipt')
    metrics = parsed['selection']['metrics']
    chosen = metrics['strict_tagged_weighting_panel']
    selected = metrics['selection_panel']
    cascade = [
        {'id': 'all_fields', 'label': 'All target fields', 'numerator': selected['sunset_tagged_source_exposures'], 'denominator': metrics['all_cohort']['source_exposures'], 'unit': 'native target fields', 'population': 'full frozen cohort; recorded Sunset memberships only; blanks unknown', 'pointer': '/metrics/selection_panel/sunset_tag_occupancy_all_source_exposures'},
        {'id': 'tagged_fields', 'label': 'Nonblank fields', 'numerator': chosen['sunset_tagged_exposures'], 'denominator': chosen['tagged_exposures'], 'unit': 'native target fields', 'population': 'original nonblank target-field subset', 'pointer': '/metrics/strict_tagged_weighting_panel/sunset_share_of_tagged_exposures'},
        {'id': 'tagged_actions', 'label': 'Selected actions', 'numerator': chosen['sunset_tagged_actions'], 'denominator': chosen['selected_actions'], 'unit': 'original reconstructed actions', 'population': 'actions with any original nonblank target field', 'pointer': '/metrics/strict_tagged_weighting_panel/sunset_share_of_selected_actions'},
        {'id': 'tagged_bytes', 'label': 'Selected bytes', 'numerator': chosen['sunset_tagged_archive_size_bytes'], 'denominator': chosen['tagged_archive_size_bytes'], 'unit': 'combined representation bytes', 'population': 'products attached to original nonblank target fields', 'pointer': '/metrics/strict_tagged_weighting_panel/sunset_share_of_tagged_bytes'},
    ]
    for item in cascade:
        if not 0 <= item['numerator'] <= item['denominator']:
            raise ValueError('Invalid cascade ratio')
    combined = next(s for s in bound['analysis']['units'] if s['unit'] == 'all_representation_bytes')
    scenario = [b for b in bound['analysis']['reassignment_sensitivity'] if
                b['unit'] == 'all_representation_bytes' and b['population'] == 'frozen_nonblank_subset' and b['reassignment_budget'] in [0, 47, 48]]
    if [b['reassignment_budget'] for b in scenario] != [0, 47, 48]:
        raise ValueError('Missing declared presentation sensitivity')
    witnesses = [bound['fields'][identifier] for identifier in combined['majority_sensitivity']['reassigned_ids']]
    current_late = next(w for w in parsed['flash_case']['observation_windows'] if w['id'] == 'later-saw3-30fps')
    clock_finding = next(f for f in flash['findings'] if f['rule_kind'] == 'window_after_boundary')
    if clock_finding['gap_seconds'] != 913 or 'background-photo' not in clock_finding['proposition']:
        raise ValueError('Clock semantics regressed to an event/ledger bound')
    concentration = parsed['concentration']['metrics']
    cohort = metrics['all_cohort']
    context = parsed['fanout']['segments']['conservative_connected_context']
    ranking=parsed['rank']['product_reversal_examples'][0]
    windows=[{'name':ranking['more_actions_name'],'plan_order':ranking['more_actions_order'],
              'actions':ranking['more_actions_actions'],'products':ranking['more_actions_products']},
             {'name':ranking['more_products_name'],'plan_order':ranking['more_products_order'],
              'actions':ranking['more_products_actions'],'products':ranking['more_products_products']}]
    for window in windows:
        if window['products'] % (3*window['actions']):raise ValueError('Noninteger bracket mechanism')
        window['representations_per_key']=3
        window['keys_per_action']=window['products']//(3*window['actions'])
        window['products_per_action']=window['products']//window['actions']
    tasks=parsed['readiness']['task_matrix']
    if [tasks[i]['task'] for i in [0,3,4]] != ['archive_retrieval_and_footprint_audit','supervised_archive_target_classification','new_sunset_event_generalization']:
        raise ValueError('Task-map positions changed')
    diagnostic=parsed['identity_boundary']['conditional_algorithm_diagnostic']
    order_summary={name:{key:branch[key] for key in ['actions','admitted_raw_keys']} for name,branch in
                   [('baseline',diagnostic['baseline']),('reversed_input_order',diagnostic['reversed_input_order']['summary'])]}
    decisions=[
        {'id':'inventory','label':'Audit download burden','title':'Files are a useful unit for a file question.',
         'result':'The frozen inventory can describe retrieval burden and representation membership. It cannot certify independent observations.',
         'unit':'Named archive products and bytes', 'next':'Replay the frozen inventory. Rebuild the declared query if the archive changes.',
         'ceiling':'Metadata accounting only. Original action/capture groups are filename/order-conditioned, not physically validated.',
         'source':'readiness','pointer':'/task_matrix/0','excerpt':tasks[0],'route':'#relationships','route_label':'Inspect the hierarchy'},
        {'id':'generalization','label':'Evaluate a new Sunset','title':'A held-out file is not a held-out Sunset.',
         'result':'The plan supplies one scheduled Sunset event. It cannot supply an internal two-sided new-Sunset-event evaluation.',
         'unit':'A justified whole event, not sibling files','next':'Obtain a second comparable event or a justified external dataset. Within-event prediction is a different, conditional task.',
         'ceiling':'Schedule entries do not certify statistical independence; geometry, target construction and deployment still need qualification.',
         'source':'readiness','pointer':'/task_matrix/4','excerpt':tasks[4],'route':'#relationships','route_label':'Inspect the split canary'},
        {'id':'prevalence','label':'Estimate target prevalence','title':'Recorded tags do not reveal the full image population.',
         'result':'Blank target fields remain unknown. Filtering them out changes the population; recorded navigation fields are not validated image-content labels.',
         'unit':'A declared population and accepted target concept','next':'Separate predicting a recorded field from recognizing appearance or physical identity. Establish reference judgments and a probability audit before estimating label quality or prevalence.',
         'ceiling':'Completion width is not a confidence interval. A blank-only audit cannot validate recorded tags.',
         'source':'readiness','pointer':'/task_matrix/3','excerpt':tasks[3],'route':'#selection','route_label':'Inspect selection and weights'},
        {'id':'flash','label':'Interpret a flash null or rate','title':'A null is useful only at a demonstrated sensitivity.',
         'result':'The overlapping clip-native screen does not demonstrate exclusionary sensitivity. Human observation conditions also changed.',
         'unit':'Calibrated detection and brightness-conditioned effective area-time','next':'Qualify sensitivity, coverage, timing and dependence before an exclusion or calibrated rate. Inspect the synthetic recovery limits and separate human-state anchors.',
         'ceiling':'No event photometry, calibrated human threshold, exact flash location or lunar impact flux is supported here.',
         'source':'recovery','pointer':'/recovery_curve','excerpt':parsed['recovery']['recovery_curve'],
         'route':'#detection','route_label':'Inspect detection opportunity'},
    ]
    data = {
        'version': '1.2.0', 'status': 'LOCAL_UNACCEPTED_PUBLICATION_CANDIDATE',
        'sources': sources, 'source_scope': 'Original frozen filename/order-conditioned cohort; physical identity unvalidated. Excerpts select already-qualified receipt fields, not new scientific measurements.',
        'fanout': {'context': {k: context[k] for k in ['actions', 'exposures', 'products']},
                   'planned': {k: parsed['fanout']['segments']['scheduled_window'][k] for k in ['actions', 'exposures', 'products']},
                   'scheduled_events': 1, 'pointer': '/segments', 'source': 'fanout'},
        'relationship': {**relation, 'pointer': '/structural_isolation', 'source': 'relationship'},
        'cascade': cascade,
        'decisions':decisions,
        'steward_confirmation':{**steward['steward_links'][0],'source':'steward_statement','pointer':'/statement',
                                'original_cohort_members':['art002e015991'],'confirmed_candidate_pairs':1,'remaining_candidate_pairs':23},
        'rank_comparison':{'windows':windows,'source':'rank','pointer':'/product_reversal_examples/0',
                           'excerpt':ranking,'reversed_pairs':parsed['rank']['metrics']['action_product_reversed_pairs'],
                           'comparable_pairs':parsed['rank']['metrics']['action_product_strictly_comparable_pairs']},
        'audit_trail':{'original':relation,'conditional':parsed['conditional']['conditional_withheld']['relationship'],
                      'original_source':'relationship','original_pointer':'/structural_isolation',
                      'conditional_source':'conditional','conditional_pointer':'/conditional_withheld/relationship',
                      'removed_action':parsed['conditional']['removal']['action_id'],
                      'removed_products':parsed['conditional']['removal']['products'],
                      'order_summary':order_summary,'order_source':'identity_boundary',
                      'order_pointer':'/conditional_algorithm_diagnostic',
                      'conclusions':parsed['conditional']['conclusions'],
                      'qualification':'Original grouping is source-order sensitive. The separate abstaining candidate is not adopted. This is one-action withholding, not physical identity or all-ambiguity robustness.'},
        'context_influence': [{'label': 'Actions', 'share': context['actions'] / cohort['actions']},
                              {'label': 'Products', 'share': context['products'] / cohort['products']},
                              {'label': 'Bytes', 'share': context['archive_size_bytes'] / cohort['archive_size_bytes']}],
        'robustness': {'scenarios': scenario, 'majority': combined['majority_sensitivity'], 'witnesses': witnesses,
                       'completion': combined['completion'], 'completion_5pp': combined['completion_budgets']['5pp'],
                       'exposure_5pp': bound['analysis']['units'][0]['completion_budgets']['5pp'],
                       'manifest': bound['sources']['manifest'], 'manifest_parent': bound['source_manifest_locator'],
                       'source': 'robustness', 'pointer': '/units/5'},
        'concentration': {k: concentration[k] for k in ['active_windows', 'exact_plan_names', 'raw_concentration_equivalent_windows', 'fractional_concentration_equivalent_windows', 'collapsed_fractional_concentration_equivalent_windows', 'same_name_overlap_collapses', 'replication_debt']},
        'attention': {'timeline': parsed['attention']['timeline'], 'deltas': parsed['attention']['deltas_seconds'], 'source': 'attention', 'pointer': '/timeline'},
        'recovery': {'curve': parsed['recovery']['recovery_curve'], 'trials': parsed['recovery']['injection_model']['trial_count'],
                     'frames': parsed['recovery']['baseline']['frames'], 'source': 'recovery', 'pointer': '/recovery_curve'},
        'footprint': {k: parsed['screen']['lunar_footprint'][k] for k in ['apparent_width_pixels', 'apparent_height_pixels']},
        'flash_findings': flash['findings'],
        'events': parsed['events']['witness_metrics'],
        'clock': {'photo_epoch': parsed['flash_case']['facts']['annotation_base_image_utc'],
                  'later_video_start': current_late['start_utc'], 'gap_seconds': clock_finding['gap_seconds'],
                  'all_event_coverage': 'UNESTABLISHED', 'source': 'flash_case',
                  'photo_pointer': '/facts/annotation_base_image_utc'},
        'conditional': {'source': 'conditional', 'pointer': '/comparison',
                        'status': 'Separate one-original-action withholding; unadopted reconstruction and physical identity unresolved.'},
        'forbidden_promotions': ['observed errors', 'physical identities', 'physical prevalence', 'model harm', 'effective sample size',
                                'event photometry', 'human thresholds', 'flash locations', 'crater confirmation', 'calibrated impact flux',
                                'NASA endorsement', 'global novelty', 'scientific acceptance'],
    }
    return serialized(data)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    payload = prepare()
    destination = ROOT / 'presentation/data.json'
    if args.check:
        if not destination.is_file() or destination.read_bytes() != payload:
            raise ValueError('Presentation excerpt drift; regenerate only after explicit source qualification')
    else:
        destination.write_bytes(payload)
    print(json.dumps({'pass': True, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
                      'new_science': False, 'mode': 'check' if args.check else 'prepare'}))


if __name__ == '__main__': main()
