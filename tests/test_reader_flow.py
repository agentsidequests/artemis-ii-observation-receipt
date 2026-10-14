"""Bounded reader-flow conservation and native disclosure checks."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]


class Reading(HTMLParser):
    def __init__(self):
        super().__init__()
        self.details=[]
        self.in_article=False
        self.summary=False
        self.visible=[]
        self.proof_paragraphs=0
        self.proof_tables=0
        self.proofs=0
        self.images=0
        self.hidden_images=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='article':self.in_article=True
        if not self.in_article:return
        if tag=='details':
            kind=attrs.get('class','')
            self.details.append(kind)
            if kind=='proof-note':
                self.proofs+=1
                if 'open' in attrs:raise ValueError('Proof defaults open')
        if tag=='summary':self.summary=True
        if tag=='p' and 'proof-note' in self.details:self.proof_paragraphs+=1
        if tag=='table' and 'proof-note' in self.details:self.proof_tables+=1
        if tag=='img':
            self.images+=1
            self.hidden_images+=bool(self.details)
    def handle_endtag(self,tag):
        if tag=='details':
            if not self.details:raise ValueError('Unbalanced disclosure')
            self.details.pop()
        if tag=='summary':self.summary=False
        if tag=='article':self.in_article=False
    def handle_data(self,value):
        if self.in_article and (not self.details or self.summary and self.details==['proof-note']):
            self.visible.append(value)


class ReaderFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(ROOT/'PUBLIC-ANALYSIS-DRAFT.md').read_text(encoding='utf-8')
        cls.control=json.loads((ROOT/'tests/fixtures/reader-flow-article-baseline.json').read_text(encoding='utf-8'))
        path=ROOT/'Artemis-II-Essay-2026-10-13.html'
        if not path.exists():path=ROOT/'presentation/preview/Artemis-II-Essay-2026-10-13.html'
        cls.html=path.read_text(encoding='utf-8')
        cls.reader=Reading();cls.reader.feed(cls.html)
        cls.visible=re.sub(r'\s+',' ',''.join(cls.reader.visible))

    def test_all_numeric_tokens_and_source_links_survive(self):
        figures=json.loads((ROOT/'presentation/figure-reading-values.json').read_text(encoding='utf-8'))['figures']
        normalized=self.source
        for f in figures:
            current=f"presentation/editorial/figures/figure-{f['number']:02}-desktop.png"
            self.assertEqual(self.source.count(']('+current+')'),1)
            normalized=normalized.replace(current,f['filename'])
        # Map only the nine explicitly redesigned local figure links. Every
        # scientific value, public source URL and other locator is conserved.
        self.assertEqual(sorted(set(re.findall(r'\d+(?:[,.]\d+)*',normalized))),self.control['numbers'])
        self.assertEqual(sorted(set(re.findall(r'\]\(([^)]+)\)',normalized))),self.control['links'])

    def test_opening_is_rewritten_with_same_question_and_ending_is_preserved(self):
        opening=self.source.split('## Relationship:')[0]
        self.assertNotEqual(opening,self.control['opening'])
        for phrase in ['Before asking what it reveals, ask what counts as an observation',
                       'More files do not necessarily supply more',
                       'not independently validated physical counts','Neither describes a NASA model']:
            self.assertIn(phrase,opening)
        self.assertEqual(self.source[self.source.index('Compression can count bytes;'):self.source.index('\n---\n')],self.control['ending'])

    def test_nine_native_proofs_render_real_content(self):
        self.assertEqual(self.reader.proofs,9)
        self.assertEqual(self.reader.details,[])
        self.assertGreaterEqual(self.reader.proof_paragraphs,14)
        self.assertEqual(self.reader.proof_tables,2)
        self.assertIn('<strong>48 largest Sunset field weights</strong>',self.html)
        self.assertTrue(re.search(r'<td[^>]*>4,307 \+ 204 \+ 0</td>',self.html))
        self.assertNotIn('| Quantity | Original |',self.html)
        self.assertEqual(self.reader.images,9)
        self.assertEqual(self.reader.hidden_images,0)

    def test_decisive_limits_remain_in_closed_main_path(self):
        for phrase in ['source order and algorithm','This is our limitation',
                       'candidate was not adopted','Physical identity remains unresolved',
                       'no original totals were reduced','Checksums and JPEG processing remain unanswered',
                       'empty target field does not mean','not an image-level answer key',
                       'A Sunset target tag is not an event identifier.',
                       'does not hold in every representation layer','not detected errors',
                       'not an effective sample size','not an observed sampler',
                       'not a discovered scene boundary','not estimate per-state detection probability',
                       'local null is non-exclusionary','cannot certify ledger creation',
                       'Missing historical calibration cannot be reconstructed by adding metadata',
                       'for one frozen interval','not NASA-accepted guidance']:
            self.assertTrue(phrase in self.visible,phrase)

    def test_jpl_one_pair_and_cohort_custody_are_explicit(self):
        for phrase in ['13 October','019A0860.NEF','Both catalogue IDs remain in the evidence trail.',
                       'Only art002e015991 entered the original analysis cohort',
                       'That exchange resolved one relationship, not the whole reconstruction.']:
            self.assertTrue(phrase in self.visible,phrase)
        self.assertNotIn('Only the latter ID was counted; both stay.',self.source)

    def test_default_path_is_shorter_without_deleting_proofs(self):
        closed=re.sub(r'<details class="proof-note">.*?</details>','',self.source,flags=re.S)
        full=len(re.findall(r'\b[\w’\x27-]+\b',self.source))
        visible=len(re.findall(r'\b[\w’\x27-]+\b',closed))
        self.assertLess(visible,full*.85)
        self.assertGreater(visible,2500)
        self.assertIn('3,747',self.source)
        self.assertIn('1 − pⁿ − (1 − p)ⁿ',self.source)

    def test_withheld_camera_action_has_an_explicit_referent(self):
        proof=self.source.split('<summary>Proof: one-action withholding</summary>',1)[1].split('</details>',1)[0]
        self.assertIn('five-frame camera action containing `art002e015991`',proof)
        self.assertIn('five capture keys and fifteen product rows',proof)
        self.assertIn('Freeze surviving fields, split assignments, grouping keys and schedule intervals.',proof)
        self.assertNotIn('Withhold its five capture keys',proof)

    def test_hypothetical_majority_result_is_visible_before_its_proof(self):
        result='A separate hypothetical reassignment of the 48 highest-weight recorded Sunset fields to another nonblank target erases the selected-byte majority.'
        self.assertTrue(result in self.visible)
        self.assertLess(self.source.index(result),self.source.index('<summary>Proof: hypothetical 48-field majority boundary</summary>'))
        self.assertIn(result+' These are not detected errors. No source tag changes.',self.source)

    def test_camera_pilot_deliverables_are_visible_before_requirements(self):
        section=self.source.split('## What NASA could publish next',1)[1]
        opening=section.split('Together, these stages define four linked receipts:',1)[0]
        for phrase in ['one bounded pilot for a frozen crew-camera task',
                       'versioned relationship ledger', 'reproducible split',
                       'selection/weighting summaries from existing products',
                       'without asserting physical independence']:
            self.assertIn(phrase,opening)
            self.assertIn(phrase,self.visible)

    def test_detection_inventory_is_not_a_camera_pilot_prerequisite(self):
        self.assertIn('For the separate detection stage, first inventory calibration, live-time, area, timing and window records.',self.visible)
        self.assertIn('not a camera-task pilot prerequisite',self.visible)
        self.assertIn('Missing historical calibration cannot be reconstructed by adding metadata',self.visible)

    def test_pilot_burden_is_a_visible_acceptance_gate(self):
        for phrase in ['Report curation effort, specialist review time, update cost and unresolved cases.',
                       'independent user reproduces versioned receipts',
                       'responsible specialists accept the semantics',
                       'Do not scale it if the maintenance burden exceeds its decision value.']:
            self.assertIn(phrase,self.visible)

    def test_concentration_heading_does_not_imply_fewer_independent_windows(self):
        self.assertIn('## Thirty-six windows, unequal influence',self.source)
        self.assertIn('Thirty-six windows, unequal influence',self.visible)
        self.assertNotIn('Thirty-six windows can behave like fourteen',self.source)
        self.assertIn('byte weights, 14.703',self.visible)
        self.assertIn('not an effective sample size, independent-event count',self.visible)

    def test_native_controls_have_visible_focus_and_no_new_script(self):
        self.assertIn('.proof-note>summary:focus-visible{outline:3px',self.html)
        self.assertNotIn('<script',self.html)
        self.assertNotIn(chr(0x2014),self.source)

if __name__=='__main__':unittest.main()
