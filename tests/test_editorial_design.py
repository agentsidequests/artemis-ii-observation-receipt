"""Editorial/source-bound visual checks, not human or scientific acceptance."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

from src import render_editorial_figures as R

ROOT=Path(__file__).resolve().parents[1]
FIGURES=ROOT/'presentation/editorial/figures'


def lum(color):
    values=[int(color[i:i+2],16)/255 for i in [1,3,5]]
    values=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
    return sum(v*w for v,w in zip(values,[.2126,.7152,.0722]))


class EditorialTests(unittest.TestCase):
    def test_svg_rebuild_and_source_identities(self):
        R.build(check=True)
        m=json.loads((FIGURES/'manifest.json').read_bytes())
        self.assertFalse(m['new_science'])
        self.assertEqual(18,len(m['files']))
        self.assertEqual(m['values_sha256'],hashlib.sha256((ROOT/'presentation/figure-reading-values.json').read_bytes()).hexdigest())
        for row in m['source_receipts']:
            self.assertEqual(row['sha256'],hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest())

    def test_numeric_display_is_bound_to_original_values_not_new_estimates(self):
        values=json.loads((ROOT/'presentation/figure-reading-values.json').read_bytes())
        for figure in values['figures']:
            for mobile in [False,True]:
                svg=R.render(figure,mobile).decode()
                for row in figure['rows']:
                    if row['value'] is not None:
                        value=f"{row['value']:,}" if isinstance(row['value'],int) else f"{row['value']:.3f}"
                        self.assertIn(value,svg)
        self.assertIn('marker: 50%',(FIGURES/'figure-02-phone.svg').read_text(encoding='utf-8'))
        self.assertIn('0–36',(FIGURES/'figure-05-phone.svg').read_text(encoding='utf-8'))

    def test_all_svg_text_is_inside_declared_vertical_geometry(self):
        ns={'s':'http://www.w3.org/2000/svg'}
        for p in FIGURES.glob('*.svg'):
            root=ET.fromstring(p.read_bytes())
            width,height=map(float,root.attrib['viewBox'].split()[2:])
            self.assertEqual(width,720 if 'phone' in p.name else 1200)
            self.assertEqual(root.attrib['role'],'img')
            self.assertTrue(root.find('s:title',ns).text)
            self.assertTrue(root.find('s:desc',ns).text)
            for node in root.findall('.//s:text',ns):
                self.assertLess(float(node.attrib['y']),height-10)
                self.assertGreaterEqual(float(node.attrib['font-size']),28 if 'phone' in p.name else 23)
                self.assertGreaterEqual(float(node.attrib['x']),0)
                self.assertLessEqual(float(node.attrib['x']),width)
            self.assertNotIn(chr(0x2014),p.read_text(encoding='utf-8'))
            self.assertNotIn('<script',p.read_text(encoding='utf-8'))
            self.assertNotIn('href=',p.read_text(encoding='utf-8'))

    def test_text_palette_contrast(self):
        paper=lum(R.PAPER)
        for color in [R.INK,R.MUTED,R.TEAL,R.INDIGO,*R.COLORS]:
            self.assertGreaterEqual((paper+.05)/(lum(color)+.05),4.5,color)

    def test_png_sharing_copies_retain_exact_svg_source_identity(self):
        m=json.loads((FIGURES/'png-manifest.json').read_bytes())
        self.assertEqual(18,len(m['files']))
        for row in m['files']:
            self.assertEqual(row['sha256'],hashlib.sha256((FIGURES/row['path']).read_bytes()).hexdigest())
            self.assertEqual(row['svg_sha256'],hashlib.sha256((FIGURES/row['svg_source']).read_bytes()).hexdigest())
            self.assertEqual(row['width'],1440 if 'phone' in row['path'] else 2400)

    def test_artifact_embeds_current_figures_and_has_native_navigation(self):
        p=ROOT/'Artemis-II-Essay-2026-10-13.html'
        if not p.exists():p=ROOT/'presentation/preview'/p.name
        page=p.read_text(encoding='utf-8')
        self.assertEqual(18,page.count('data:image/svg+xml;base64,'))
        self.assertEqual(5,page.count('class="chapter-start"'))
        for identifier in ['observation','counting','evaluation','detection','next']:
            self.assertIn('href="#'+identifier+'"',page)
            self.assertIn('id="'+identifier+'"',page)
        self.assertIn('prefers-reduced-motion',page)
        self.assertIn('Exact transcript times and intervals',page)
        self.assertIn('Pilot specification: fields, failure rules and validation',page)
        self.assertNotIn('<script',page)
        self.assertNotIn('<link',page)
        # One stylesheet owns the reading surface. Legacy styles previously
        # left a dark header under dark text despite valid individual rules.
        css=(ROOT/'presentation/editorial/reader.css').read_text(encoding='utf-8')
        self.assertEqual(page.split('<style>',1)[1].split('</style>',1)[0],css)
        self.assertNotIn('background:#122c39',page)

    def test_hard_negative_source_drift_stops_generation(self):
        from unittest.mock import patch
        old=R.ROOT
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'presentation').mkdir()
            values=json.loads((old/'presentation/figure-reading-values.json').read_bytes())
            values['sources']=[dict(path='changed.json',sha256='0'*64)]
            (root/'presentation/figure-reading-values.json').write_text(json.dumps(values))
            (root/'changed.json').write_bytes(b'changed')
            with patch.object(R,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'Unqualified figure source'):R.build()


if __name__=='__main__':unittest.main()
