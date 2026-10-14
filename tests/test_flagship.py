"""V10 teaching/carrier checks, not learning, taste or scientific acceptance."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]

class FlagshipTests(unittest.TestCase):
    def test_all_models_and_invalid_inputs(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node is needed for the pure presentation model.')
        r=subprocess.run([node,str(ROOT/'presentation/flagship/test.cjs'),str(ROOT)],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        d=json.loads(r.stdout);self.assertEqual(d['cases'],4217);self.assertEqual(d['negatives'],13)

    def test_unique_ids_and_routes(self):
        class Nodes(HTMLParser):
            def __init__(self):super().__init__();self.ids=[];self.links=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if 'id' in a:self.ids.append(a['id'])
                if a.get('href','').startswith('#'):self.links.append(a['href'][1:])
        p=Nodes()
        for name in ['doors.html','play.html','use.html','inspect.html']:
            p.feed((ROOT/'presentation/flagship'/name).read_text(encoding='utf-8'))
        p.feed((ROOT/'presentation/observatory/index.html').read_text(encoding='utf-8'))
        p.feed((ROOT/'presentation/index.template.html').read_text(encoding='utf-8'))
        self.assertEqual(len(p.ids),len(set(p.ids)))
        ids=set(p.ids)|{'explore','f-inspect'}
        for target in p.links:self.assertIn(target,ids,target)
        # The assembled carrier can collide with an otherwise valid legacy ID.
        candidates=[ROOT/'Artemis-II-Interactive-Science-v10-2026-10-14.html',ROOT/'presentation/preview/Artemis-II-Interactive-Science-v10-2026-10-14.html']
        built=next((f for f in candidates if f.is_file()),None)
        self.assertIsNotNone(built,'Build the actual carrier before milestone validation.')
        full=Nodes();full.feed(built.read_text(encoding='utf-8'))
        self.assertEqual(len(full.ids),len(set(full.ids)),'Duplicate ID in assembled page')
        for target in full.links:self.assertIn(target,set(full.ids),target)

    def test_claim_boundaries_and_optional_exact_depth(self):
        t=(ROOT/'presentation/flagship/play.html').read_text(encoding='utf-8')
        for s in ['not running an AI model','not an observed NASA split','filename/order conditioned','not prove physical independence','not a confidence interval','recorded names may themselves be wrong','invented demonstration','No toy setting corresponds','two-capture sequences are invented','new camera sequence','different goal']:
            self.assertIn(s.lower(),t.lower())
        self.assertEqual(t.count('class="f-depth"'),3)
        self.assertIn('4,307 same-capture + 204 same-action-only + 0 action-isolated',t)
        use=(ROOT/'presentation/flagship/use.html').read_text(encoding='utf-8')
        self.assertIn('id="f-package-link"',use)
        self.assertNotIn('href="Artemis-II-Public-Candidate-v10-2026-10-14.zip"',use)

    def test_no_network_tracking_or_em_dash(self):
        for p in (ROOT/'presentation/flagship').iterdir():
            if not p.is_file():continue
            t=p.read_text(encoding='utf-8')
            for token in ['fetch(', 'localStorage', 'XMLHttpRequest', 'setInterval(', chr(0x2014)]:self.assertNotIn(token,t,p.name)
        css=(ROOT/'presentation/flagship/style.css').read_text(encoding='utf-8')
        for token in [':focus-visible','prefers-reduced-motion','@media print','.f-pane[hidden]']:
            self.assertIn(token,css)
        def luminance(h):
            values=[int(h[i:i+2],16)/255 for i in (1,3,5)]
            return sum((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)*w for v,w in zip(values,(.2126,.7152,.0722)))
        # Critical new solid-color text/focus pairs, not a complete WCAG audit.
        for fg,bg in [('#17252d','#f6f3eb'),('#a03c2c','#f6f3eb'),('#536168','#f6f3eb'),('#17252d','#ffba9d'),('#c5d8df','#112f3d'),('#f6f3eb','#173747'),('#ffba9d','#112f3d')]:
            a,b=sorted([luminance(fg),luminance(bg)])
            self.assertGreaterEqual((b+.05)/(a+.05),4.5,(fg,bg))
        js=(ROOT/'presentation/flagship/app.js').read_text(encoding='utf-8')
        self.assertIn("hash.startsWith('#view=')",js);self.assertIn("window.addEventListener('hashchange'",js)

    def test_builder_guards_existing_notebook_and_legacy(self):
        t=(ROOT/'tools/build_flagship.mjs').read_text(encoding='utf-8')
        self.assertIn("assert.equal(notebook(page),notebook(base)",t)
        self.assertIn('tools/build_observatory.mjs',t)
        self.assertIn("model_trained:false",t)
        self.assertIn("source_data_sha256:sha(read('presentation/data.json'))",t)

    def test_separate_public_and_private_scientific_pins(self):
        digest=hashlib.sha256((ROOT/'presentation/data.json').read_bytes()).hexdigest()
        self.assertIn(digest,{'7803dbb704bbbbfe1479d8db33e3cd1279103e2b77150f67a8256bc236c0ab2a','d41fe206bf1ece970c11e7a96e47e4ba605e97eec7f75a1d553a83e26160d3e1'})

if __name__=='__main__':unittest.main()
