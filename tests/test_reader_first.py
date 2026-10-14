"""Owner-observed findability repair and faithful dual-altitude presentation."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ReaderFirstTests(unittest.TestCase):
    def test_reader_choices_and_no_unlike_subtraction(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node needed for this interaction check only.')
        p=subprocess.run([node,str(ROOT/'presentation/test-reader.cjs'),str(ROOT)],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(json.loads(p.stdout)['comparisons'],16)

    def test_saved_view_has_a_real_next_control_not_an_unfindable_instruction(self):
        template=(ROOT/'presentation/index.template.html').read_text(encoding='utf-8')
        workbench=(ROOT/'presentation/workbench.js').read_text(encoding='utf-8')
        opening=(ROOT/'presentation/reader-opening.html').read_text(encoding='utf-8')
        self.assertIn('id="go-sunset-counting"',template)
        self.assertIn("$('go-sunset-counting').addEventListener",workbench)
        self.assertIn('id="counting-title" tabindex="-1"',opening)
        self.assertIn('Try 2, then 4.',opening)
        self.assertIn('This step is optional.',opening)

    def test_technical_notebook_retains_all_old_panels_and_source_owner(self):
        template=(ROOT/'presentation/index.template.html').read_text(encoding='utf-8')
        self.assertIn('<details id="technical-notebook">',template)
        for name in ['workspace','relationships','selection','weighting','robustness','concentration','detection','audit-trail','recommendations','inspect']:
            self.assertIn('id="'+name+'"',template)
        opening=(ROOT/'presentation/reader-opening.html').read_text(encoding='utf-8')
        for phrase in ['filename/order conditioned','not a fully validated physical census','not a local NEF checksum comparison','Only the second ID occurs in our counted cohort','other 23 candidate pairs remain unconfirmed','No new flash is identified here','camera task need not wait for flash calibration']:
            self.assertIn(phrase.lower(),opening.lower())

    def test_editorial_photo_is_pinned_and_credited_not_relicensed(self):
        b=(ROOT/'presentation/media/art002e009301-nasa-public.jpg').read_bytes()
        self.assertEqual(len(b),75677)
        self.assertEqual(hashlib.sha256(b).hexdigest(),'1bb6387479474ea44221dbb7627f603bf3ceb6e3c6ce2af5a75e7b50147bfe17')
        self.assertEqual(b[:2],b'\xff\xd8')
        note=(ROOT/'presentation/media/README.md').read_text(encoding='utf-8')
        self.assertIn('Not licensed under this project',note)
        self.assertIn('processing-equivalent',note)

    def test_reader_has_no_network_storage_or_forbidden_punctuation(self):
        for name in ['reader-opening.html','reader.css','reader.js']:
            t=(ROOT/'presentation'/name).read_text(encoding='utf-8')
            for token in ['fetch(', 'localStorage', 'XMLHttpRequest',chr(0x2014)]:self.assertNotIn(token,t)
        css=(ROOT/'presentation/reader.css').read_text(encoding='utf-8')
        for token in ['prefers-reduced-motion',':focus-visible','@media(max-width:650px)']:self.assertIn(token,css)

    def test_opening_ids_are_unique_and_proof_sources_resolve(self):
        class Nodes(HTMLParser):
            def __init__(self):super().__init__();self.ids=[];self.pointers=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if 'id' in a:self.ids.append(a['id'])
                if 'data-source' in a:self.pointers.append((a['data-source'],a['data-pointer']))
        p=Nodes();p.feed((ROOT/'presentation/reader-opening.html').read_text(encoding='utf-8'));p.feed((ROOT/'presentation/index.template.html').read_text(encoding='utf-8'))
        self.assertEqual(len(p.ids),len(set(p.ids)))
        e=json.loads((ROOT/'presentation/data.json').read_bytes())
        for key,pointer in p.pointers:
            v=json.loads((ROOT/e['sources'][key]['path']).read_bytes())
            for bit in pointer.strip('/').split('/'):v=v[int(bit)] if isinstance(v,list) else v[bit]


if __name__=='__main__':unittest.main()
