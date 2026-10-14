"""Reader-only revision guards; these do not prove scientific or human acceptance."""
import hashlib
import json
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReaderRevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = json.loads((ROOT/'presentation/figure-reading-values.json').read_text(encoding='utf-8'))
        cls.figures = {f['number']: f for f in cls.values['figures']}

    def test_source_receipt_hashes_and_no_science_claim(self):
        self.assertFalse(self.values['new_science'])
        self.assertEqual(7,len(self.values['sources']))
        for s in self.values['sources']:
            self.assertEqual(s['sha256'],hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest())

    def test_mobile_values_are_bound_to_receipts(self):
        def source(n):return json.loads((ROOT/'results'/n).read_text(encoding='utf-8'))
        e=source('stage11e-result.json');g=source('stage11g-result.json');u=source('stage11u-selection-weighting-cascade.json')
        self.assertEqual([1,e['context']['actions'],e['context']['exposures'],e['context']['products']],
                         [r['value'] for r in self.figures[1]['rows']])
        m=e['measures']
        self.assertEqual([m[k]*100 for k in ['action_share','product_share','total_byte_share']],
                         [r['value'] for r in self.figures[3]['rows']])
        rank=g['product_reversal_examples'][0]
        self.assertEqual([rank[k] for k in ['more_actions_actions','more_products_actions','more_actions_products','more_products_products']],
                         [r['value'] for r in self.figures[4]['rows']])
        metrics=u['metrics'];s=metrics['selection_panel'];w=metrics['strict_tagged_weighting_panel']
        expected=[s['sunset_tag_occupancy_all_source_exposures'],s['sunset_share_of_tagged_source_exposures']]
        expected += [w[k] for k in ['sunset_share_of_selected_actions','sunset_share_of_tagged_exposures','sunset_share_of_tagged_products','sunset_share_of_tagged_bytes']]
        self.assertEqual([v*100 for v in expected],[r['value'] for r in self.figures[2]['rows']])
        t=source('stage11t-result.json')['metrics']
        expected=[t[policy][key] for policy in ['raw_concentration_equivalent_windows','fractional_concentration_equivalent_windows','collapsed_fractional_concentration_equivalent_windows'] for key in ['actions','products','archive_size_bytes']]
        self.assertEqual(expected,[r['value'] for r in self.figures[5]['rows']])
        l=source('stage11l-result.json')['policies']
        for r,key in zip(self.figures[6]['rows'],['product_key','action_key','temporal_5s_key']):
            self.assertIn(f"{l[key]['crossing_action_groups']:,} / 2,166",r['detail'])
            self.assertIn(f"{l[key]['crossing_temporal_5s_groups']:,} / 816",r['detail'])
        anchors={r['id']:r['utc'][11:-1]+' UTC' for r in source('stage11s-result.json')['timeline']}
        for r in self.figures[7]['rows']:self.assertIn(r['detail'],anchors.values())

    def test_readable_geometry_and_explicit_scales(self):
        self.assertEqual(list(range(1,10)),sorted(self.figures))
        self.assertGreaterEqual(self.values['minimum_data_label_size'],32)
        for f in self.figures.values():
            b=(ROOT/'presentation/mobile'/f['filename']).read_bytes()
            self.assertEqual(b[:8],b'\x89PNG\r\n\x1a\n')
            width,height=struct.unpack('>II',b[16:24])
            self.assertEqual(width,720)
            self.assertGreater(height,800)
            self.assertTrue(f['note'])
        for r in self.figures[2]['rows']:self.assertEqual(r['maximum'],100)
        self.assertIn("target_id IS NOT NULL AND target_id <> ''",self.figures[2]['scale'])
        self.assertIn('not elapsed time',self.figures[7]['scale'])
        self.assertIn('unmatched is an alternative',self.figures[8]['note'])

    def test_desktop_defect_guard(self):
        renderer=(ROOT/'src/render_public_analysis_charts.py').read_text(encoding='utf-8')
        self.assertNotIn('independence baseline',renderer)
        self.assertNotIn('value / 55.0',renderer)
        self.assertIn('action-count reference',renderer)
        self.assertIn("target_id IS NOT NULL AND target_id <> ''",renderer)
        self.assertIn('0–100% tracks; markers 50%',renderer)

    def test_mobile_assets_have_byte_preserving_git_rule_and_lf_values(self):
        self.assertEqual('* -text',(ROOT/'presentation/mobile/.gitattributes').read_text(encoding='utf-8').strip())
        self.assertNotIn(b'\r\n',(ROOT/'presentation/figure-reading-values.json').read_bytes())
        renderer=(ROOT/'src/render_mobile_analysis_charts.py').read_text(encoding='utf-8')
        self.assertIn('newline="\\n"',renderer)
        self.assertIn('Unbreakable figure text exceeds its declared width',renderer)

    def test_native_phone_selection_and_text_fallback(self):
        compiled=ROOT/'Artemis-II-Essay-2026-10-13.html'
        if not compiled.exists():compiled=ROOT/'presentation/preview/Artemis-II-Essay-2026-10-13.html'
        page=compiled.read_text(encoding='utf-8')
        self.assertEqual(9,page.count('<picture>'))
        self.assertEqual(9,page.count('<source media="(max-width:650px)"'))
        self.assertEqual(9,page.count('<details class="figure-values">'))
        self.assertIn('Reader edition 14 October 2026',page)
        self.assertNotIn('Original figure bytes embedded unchanged',page)
        self.assertNotIn('\u2014',page)

    def test_worked_examples_and_pilot_feasibility_are_early_and_explicit(self):
        essay=(ROOT/'PUBLIC-ANALYSIS-DRAFT.md').read_text(encoding='utf-8')
        self.assertLess(essay.index('76 to 60'),essay.index('## NASA already has a family tree'))
        self.assertLess(essay.index('all 4,511 held-out products'),essay.index('## Relationship'))
        self.assertIn('separately owned feasibility stage',essay)
        self.assertIn('Missing historical calibration cannot be reconstructed by adding metadata',essay)
        self.assertIn('camera-task pilot',essay)


if __name__=='__main__':unittest.main()
