"""Source-frozen interactive field guide. Not human comprehension or taste proof."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ObservatoryTests(unittest.TestCase):
    def test_pure_models_and_rejections(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node required for presentation models.')
        p=subprocess.run([node,str(ROOT/'presentation/observatory/test.cjs'),str(ROOT)],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        result=json.loads(p.stdout);self.assertEqual(result['states'],55);self.assertEqual(result['negatives'],20)

    def test_new_entry_has_unique_ids_and_no_legacy_control_collision(self):
        class Nodes(HTMLParser):
            def __init__(self):super().__init__();self.ids=[];self.sources=[];self.claims=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if 'id' in a:self.ids.append(a['id'])
                if 'data-source' in a:self.sources.append((a['data-source'],a['data-pointer']))
                if 'data-claim' in a:self.claims.append(a['data-claim'])
        entry=(ROOT/'presentation/observatory/index.html').read_text(encoding='utf-8')
        p=Nodes();p.feed(entry);p.feed((ROOT/'presentation/index.template.html').read_text(encoding='utf-8'))
        self.assertEqual(len(p.ids),len(set(p.ids)))
        self.assertEqual(p.claims,['relationship','selection','weighting','detection'])
        e=json.loads((ROOT/'presentation/data.json').read_bytes())
        for key,pointer in p.sources:
            v=json.loads((ROOT/e['sources'][key]['path']).read_bytes())
            for bit in pointer.strip('/').split('/'):v=v[int(bit)] if isinstance(v,list) else v[bit]

    def test_ceilings_survive_at_the_new_entry(self):
        t=(ROOT/'presentation/observatory/index.html').read_text(encoding='utf-8')
        for phrase in ['filename','input order','physical independence certificate','not the true share','not the entire mission archive','no source record changes','other 23 candidate pairs','do not subtract','not a completed catalogue fix','cannot date','camera task need not wait','not NASA-endorsed']:
            # Some clock text is in the controller, but must be source-visible in the same entry build.
            combined=t+(ROOT/'presentation/observatory/app.js').read_text(encoding='utf-8')
            self.assertIn(phrase.lower(),combined.lower())

    def test_new_interaction_no_network_storage_scoring_or_em_dash(self):
        for name in ['index.html','style.css','app.js']:
            t=(ROOT/'presentation/observatory'/name).read_text(encoding='utf-8')
            for token in ['fetch(','localStorage','XMLHttpRequest','setInterval(',chr(0x2014)]:self.assertNotIn(token,t)
        css=(ROOT/'presentation/observatory/style.css').read_text(encoding='utf-8')
        for token in ['prefers-reduced-motion',':focus-visible','object-fit:contain','@media print']:self.assertIn(token,css)
        def luminance(h):
            rgb=[int(h[i:i+2],16)/255 for i in (1,3,5)]
            linear=[c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4 for c in rgb]
            return sum(c*w for c,w in zip(linear,(0.2126,0.7152,0.0722)))
        # Bounded critical solid-color pairs, not all composited UI or WCAG certification.
        for fg,bg in [('#17252d','#f6f3eb'),('#536168','#f6f3eb'),('#8d3024','#f0eee6'),('#ffb493','#132d39'),('#b7cdd3','#132d39'),('#c5d8dd','#142c36'),('#17252d','#ffba9d')]:
            a,b=sorted([luminance(fg),luminance(bg)]);self.assertGreaterEqual((b+.05)/(a+.05),4.5,(fg,bg))
        html=(ROOT/'presentation/observatory/index.html').read_text(encoding='utf-8')
        self.assertIn('<caption>',html);self.assertIn('aria-labelledby="o-field-title o-field-desc"',html)
        self.assertNotIn('data-claim=',html)

    def test_browse_image_is_existing_exact_bytes(self):
        p=ROOT/'corpus/evidence/stage8b/art002e012264_nkd5015_prc_v01.png'
        b=p.read_bytes();self.assertEqual(len(b),8842542)
        self.assertEqual(hashlib.sha256(b).hexdigest(),'8b3eb98c789f69019a2a989d5e63d181dc6abe22fb4a0eb206114e616aa85433')

    def test_builder_preserves_legacy_and_pins_both_media(self):
        t=(ROOT/'tools/build_observatory.mjs').read_text(encoding='utf-8')
        self.assertIn("assert.equal(notebook(page),notebook(oldPage)",t)
        self.assertIn("'presentation/reader.js'",t)
        self.assertIn('8b3eb98c789f69019a2a989d5e63d181dc6abe22fb4a0eb206114e616aa85433',t)
        self.assertIn('1bb6387479474ea44221dbb7627f603bf3ceb6e3c6ce2af5a75e7b50147bfe17',t)

if __name__=='__main__':unittest.main()
