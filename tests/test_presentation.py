"""Source binding, narrative coverage, packaging and preserved claim ceilings."""
import copy
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from src import prepare_presentation as P

ROOT=Path(__file__).resolve().parents[1]


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=P.prepare()
        cls.data=json.loads(cls.payload)
        cls.template=(ROOT/'presentation/index.template.html').read_text(encoding='utf-8')
        cls.essay=(ROOT/'PUBLIC-ANALYSIS-DRAFT.md').read_text(encoding='utf-8')
        cls.packet=(ROOT/'ARTEMIS-II-TWO-GATE-SPECIALIST-REVIEW-PACKET.md').read_text(encoding='utf-8')

    def test_prepared_excerpt_replays_exactly(self):
        self.assertEqual(self.payload,(ROOT/'presentation/data.json').read_bytes())
        self.assertEqual(self.payload,P.prepare())

    def test_all_parent_source_identities_match_actual_bytes(self):
        for source in self.data['sources'].values():
            payload=(ROOT/source['path']).read_bytes()
            self.assertEqual(len(payload),source['bytes'])
            self.assertEqual(hashlib.sha256(payload).hexdigest(),source['sha256'])

    def test_first_parent_drift_stops_before_a_presentation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            target=root/P.PINS['fanout'][0]
            target.parent.mkdir(parents=True)
            target.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Qualified presentation input changed'):P.prepare(root)

    def test_selected_cascade_values_and_population_labels_are_not_substituted(self):
        by_id={entry['id']:entry for entry in self.data['cascade']}
        self.assertEqual((1553,7606),(by_id['all_fields']['numerator'],by_id['all_fields']['denominator']))
        self.assertEqual((1553,3413),(by_id['tagged_fields']['numerator'],by_id['tagged_fields']['denominator']))
        self.assertEqual((311,915),(by_id['tagged_actions']['numerator'],by_id['tagged_actions']['denominator']))
        self.assertEqual((409399017151,781104206358),(by_id['tagged_bytes']['numerator'],by_id['tagged_bytes']['denominator']))
        self.assertEqual(4,len({entry['population'] for entry in by_id.values()}))

    def test_split_bins_conserve_one_frozen_test_population(self):
        r=self.data['relationship']
        self.assertEqual(4511,r['test_products'])
        self.assertEqual(4307+204+0,r['test_products'])
        self.assertEqual(0,r['action_isolated_test_products'])

    def test_fanout_keeps_one_scheduled_event_and_distinct_boundaries(self):
        f=self.data['fanout']
        self.assertEqual(1,f['scheduled_events'])
        for context in ['planned','context']:
            self.assertEqual(f[context]['products'],f[context]['actions']*5*3)
        self.assertEqual(2535,f['planned']['products'])
        self.assertEqual(4290,f['context']['products'])

    def test_majority_witness_is_source_linked_and_cardinality_minimal(self):
        r=self.data['robustness']
        self.assertEqual(48,len(r['witnesses']))
        self.assertEqual(29,len({f['action'] for f in r['witnesses']}))
        self.assertEqual(19001826912,sum(f['weights']['all_representation_bytes'] for f in r['witnesses']))
        self.assertGreater(2*r['majority']['predecessor']['numerator'],r['majority']['denominator'])
        self.assertLessEqual(2*r['majority']['after']['numerator'],r['majority']['denominator'])

    def test_blank_completion_remains_a_separate_r0_equal_cost_job(self):
        r=self.data['robustness']
        self.assertEqual(3747,r['completion_5pp']['minimum_fields_resolved_equal_field_cost'])
        self.assertEqual(3813,r['exposure_5pp']['minimum_fields_resolved_equal_field_cost'])
        self.assertFalse(r['completion_5pp']['real_resolution_or_cost_optimality'])
        for phrase in ['equal individual-field cost','r = 0','not statistical sample sizes']:
            self.assertIn(phrase,self.template.lower())

    def test_clock_is_current_photo_semantics_not_legacy_ledger(self):
        c=self.data['clock']
        self.assertEqual('2026-04-07T01:04:00Z',c['photo_epoch'])
        self.assertEqual('2026-04-07T01:19:13Z',c['later_video_start'])
        self.assertEqual('UNESTABLISHED',c['all_event_coverage'])
        self.assertNotIn('annotation_ledger_utc',json.dumps(c))
        self.assertIn('not a ledger-creation time',self.template)

    def test_detection_exposes_uncalibrated_synthetic_units_and_real_anchors(self):
        r=self.data['recovery']
        self.assertEqual(1458,r['trials'])
        self.assertEqual(900,r['frames'])
        self.assertTrue(all(p['recovered']==0 for p in r['curve'][:-1]))
        self.assertEqual(9,r['curve'][-1]['recovered'])
        self.assertEqual(162,r['curve'][-1]['trials'])
        self.assertEqual(12,len(self.data['attention']['timeline']))
        for phrase in ['not astronomical brightness','not a numbered event assignment','non-exclusionary','physical distance-advantage']:
            self.assertIn(phrase,self.template)

    def test_source_note_pointers_resolve_without_promoting_parent_pass_flags(self):
        for key,pointer in re.findall(r'data-source="([^"]+)" data-pointer="([^"]+)"',self.template):
            value=json.loads((ROOT/self.data['sources'][key]['path']).read_bytes())
            for part in pointer.strip('/').split('/'):
                value=value[int(part)] if isinstance(value,list) else value[part]
        self.assertIn('scientific/institutional acceptance',self.template)

    def test_essay_and_packet_carry_the_same_new_result_and_cost_ceiling(self):
        for text in [self.essay,self.packet]:
            for phrase in ['49.980167%','50.030744%','3,747','3,813','equal','not','48']:
                self.assertIn(phrase,text)
            self.assertNotIn('\u2014',text)
        self.assertIn('smallest majority-changing perturbation',self.essay)
        self.assertIn('No audit, error rate or required statistical sample size',self.packet)

    def test_all_required_chapters_and_handoffs_exist(self):
        for identifier in ['decisions','relationships','selection','weighting','robustness','concentration','detection','recommendations','audit-trail','inspect']:
            self.assertIn('id="'+identifier+'"',self.template)
        self.assertIn('Artemis-II-Essay-2026-10-13.html',self.template)
        self.assertIn('Artemis-II-Specialist-Review-2026-10-13.html',self.template)

    def test_offline_focus_reduced_motion_and_no_em_dashes(self):
        css=(ROOT/'presentation/styles.css').read_text(encoding='utf-8')
        js=(ROOT/'presentation/story.js').read_text(encoding='utf-8')
        self.assertIn('prefers-reduced-motion',css)
        self.assertIn(':focus-visible',css)
        self.assertIn('<noscript>',self.template)
        self.assertIn('connect-src \'none\'',self.template)
        self.assertNotIn('<script src=',self.template)
        self.assertNotIn('fetch(',js)
        for text in [css,js,self.template]:self.assertNotIn('\u2014',text)

    def test_package_is_explicit_private_scope_not_whole_repository_intake(self):
        self.skipTest('Private delivery packager is intentionally not exported; the public inventory and extracted links have separate checks.')

    def test_complete_package_contains_the_presentations_local_reader_hops(self):
        self.skipTest('Private delivery packager is intentionally not exported; public rendered links are checked in the distributed package.')


    def test_question_first_front_door_has_four_bounded_routes(self):
        self.assertEqual(['inventory','generalization','prevalence','flash'],[d['id'] for d in self.data['decisions']])
        self.assertLess(self.template.index('id="decisions"'),self.template.index('id="relationships"'))
        for item in self.data['decisions']:
            for key in ['result','unit','next','ceiling','source','pointer','excerpt','route']:self.assertTrue(item[key])
            value=json.loads((ROOT/self.data['sources'][item['source']]['path']).read_bytes())
            for part in item['pointer'].strip('/').split('/'):
                value=value[int(part)] if isinstance(value,list) else value[part]
            self.assertEqual(value,item['excerpt'])

    def test_rank_reversal_is_exact_and_representation_multiplier_is_constant(self):
        windows=self.data['rank_comparison']['windows']
        self.assertEqual([(76,684,3,9),(60,900,5,15)],[(w['actions'],w['products'],w['keys_per_action'],w['products_per_action']) for w in windows])
        self.assertTrue(all(w['representations_per_key']==3 for w in windows))
        self.assertIn('multiply both protocols equally',self.template)
        self.assertIn('unequal relative influence comes from bracket length',self.template)

    def test_actual_audit_excerpt_matches_original_and_distinct_conditional_receipts(self):
        trail=self.data['audit_trail']
        for mode in ['original','conditional']:
            value=json.loads((ROOT/self.data['sources'][trail[mode+'_source']]['path']).read_bytes())
            for part in trail[mode+'_pointer'].strip('/').split('/'):value=value[part]
            self.assertEqual(value,trail[mode])
        self.assertEqual(4511,trail['original']['test_products'])
        self.assertEqual(4509,trail['conditional']['test_products'])
        self.assertEqual(15,trail['removed_products'])
        self.assertEqual(2134,trail['order_summary']['reversed_input_order']['actions'])
        self.assertIn('not physical identity or all-ambiguity robustness',trail['qualification'])

    def test_causal_weighting_precedes_advanced_majority_in_both_reading_routes(self):
        self.assertLess(self.template.index('id="weighting"'),self.template.index('id="robustness"'))
        self.assertIn('<details id="robustness"',self.template)
        self.assertLess(self.essay.index('## Change the noun, change the winner'),self.essay.index('## A majority is not a margin of safety'))
        self.assertIn('Crossing 50% does not by itself change the target ranking',self.template)

    def test_snapshot_sources_match_saved_git_bytes_without_rewriting_historical_receipts(self):
        self.skipTest('Private source history is intentionally not imported; exported snapshots retain their own pinned byte identities.')

    def test_no_script_recovery_is_visible_before_the_interactive_entry(self):
        self.assertLess(self.template.index('<noscript>'),self.template.index('<main'))
        self.assertIn('complete illustrated essay',self.template.split('<noscript>',1)[1].split('</noscript>',1)[0])

    def test_preexisting_scientific_panels_equal_the_prior_complete_presentation(self):
        self.skipTest('Private predecessor commit is unavailable in the public export; source-to-projection numerical conservation is checked by the export review.')

    def test_all_other_pins_app_sources_and_figures_keep_saved_git_bytes(self):
        self.skipTest('Private predecessor commit is unavailable; exported provenance and the nine-figure conservation check own this boundary.')

    def test_current_statement_is_source_bound_and_does_not_recount(self):
        link=self.data['steward_confirmation']
        self.assertEqual(16,len(self.data['sources']))
        self.assertEqual('STEWARD_CONFIRMED_IDENTICAL_IMAGES',link['status'])
        self.assertEqual(['art002e009301','art002e015991'],link['statement']['native_identifiers'])
        self.assertEqual(['art002e015991'],link['original_cohort_members'])
        self.assertEqual(23,link['remaining_candidate_pairs'])
        self.assertFalse(link['statement']['local_byte_identity_verified'])
        self.assertIn('id="steward-evidence"',self.template)
        self.assertIn('Observation-Receipt-Identity-Confirmed-2026-10-13.html',self.template)
        self.assertIn('I sent JPL a narrow question:',self.essay)
        self.assertIn('That exchange resolved one relationship, not the whole reconstruction.',self.essay)
        self.assertIn('I asked JPL whether two catalogue IDs represented the same exposure',self.template)
        for text in [self.essay,self.packet]:
            for phrase in ['019A0860.NEF','13 October','JPL','Checksums' if text is self.essay else 'checksums']:
                self.assertIn(phrase,text)

    def test_bundle_contains_current_case_but_not_private_mail_intake(self):
        self.skipTest('Private delivery packager is not exported; public package boundary checks cover the current case and omitted email intake.')


if __name__=='__main__':unittest.main()
