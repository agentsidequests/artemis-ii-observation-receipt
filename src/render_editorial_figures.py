"""Owned source-bound SVG charts. No acquisition or scientific recomputation."""
from pathlib import Path
import hashlib
import html
import json
import re
import textwrap
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'presentation/editorial/figures'
INK, MUTED, TEAL, INDIGO, LINE, PAPER = '#182c43', '#4e6176', '#066b70', '#514496', '#c9d5df', '#eff4f8'
COLORS = [TEAL, INDIGO, '#935122']


class Canvas:
    def __init__(self, mobile, title, description):
        self.mobile, self.w = mobile, 720 if mobile else 1200
        self.m = 38 if mobile else 58
        self.label = 32 if mobile else 27
        self.small = 28 if mobile else 23
        self.parts = []
        self.title, self.description = title, description
        self.y = self.wrap(self.m, 65, title, size=43 if mobile else 45, color=INK, weight='600') + 14

    def text(self, x, y, value, size=None, color=INK, weight='400', anchor='start'):
        size = size or self.label
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(str(value))}</text>')

    def wrap(self, x, y, value, width=None, size=None, color=MUTED, weight='400'):
        size = size or self.small
        width = width or self.w - x - self.m
        # Conservative font-width budget; actual surfaces remain a separate gate.
        lines = textwrap.wrap(value, width=max(12, int(width/(size*.59))), break_long_words=False, break_on_hyphens=False)
        for line in lines:
            if len(line)*size*.59 > width+1:
                raise ValueError('Unbreakable label exceeds declared width: '+line)
            self.text(x, y, line, size, color, weight)
            y += size*1.45
        return y

    def line(self, x1, y1, x2, y2, color=LINE, width=2, dash=''):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')

    def rect(self, x, y, width, height, fill, radius=0):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}"/>')

    def circle(self, x, y, r, fill):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>')

    def subtitle(self, value):
        self.y = self.wrap(self.m, self.y, value) + 18

    def bar(self, label, value, maximum, color=TEAL, suffix='%', detail='', precision=3):
        self.text(self.m, self.y, label, self.label, INK, '500')
        fmt = f'{value:.{precision}f}' if precision else f'{int(value):,}'
        self.text(self.w-self.m, self.y, fmt+suffix, self.label+3, color, '600', 'end')
        self.y += 23
        x, width, height = self.m, self.w-2*self.m, 14 if self.mobile else 17
        self.rect(x, self.y, width, height, '#dce5ec', height/2)
        self.rect(x, self.y, width*value/maximum, height, color, height/2)
        if getattr(self, 'marker', None) is not None:
            mx=x+width*self.marker/maximum
            self.line(mx,self.y-9,mx,self.y+height+9,MUTED,2,'4 4')
        self.y += 51 if self.mobile else 47
        if detail:
            self.y = self.wrap(self.m, self.y, detail)+14

    def axis(self, maximum, suffix=''):
        self.text(self.m, self.y, '0'+suffix, self.small, MUTED)
        self.text(self.w-self.m, self.y, f'{maximum:,}'+suffix, self.small, MUTED, anchor='end')
        self.y += 48

    def footer(self, note):
        self.y += 10
        self.line(self.m, self.y, self.w-self.m, self.y)
        self.y = self.wrap(self.m, self.y+42, note)+18
        height = int(self.y+12)
        content = ''.join(self.parts)
        if chr(0x2014) in content:
            raise ValueError('Em dash')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 {self.w} {height}" width="{self.w}" height="{height}">'
                f'<title id="title">{html.escape(self.title)}</title><desc id="desc">{html.escape(self.description)}</desc>'
                f'<rect width="{self.w}" height="{height}" fill="{PAPER}"/>'
                f'<g font-family="Arial, sans-serif">{content}</g></svg>\n').encode()


def render(f, mobile):
    number, rows = f['number'], f['rows']
    titles = {1:'One Sunset, four counts', 2:'A filter changes the answer', 3:'Same context, different weight',
              4:'Two windows, two winners', 5:'How evenly is the archive spread?', 6:'Different files, related observations',
              7:'The crew changed how they watched', 8:'Add a task map, not a new archive', 9:'Ready for which question?'}
    c = Canvas(mobile, titles[number], f['note'])
    if number == 1:
        c.subtitle('The connected Sunset context, under the original frozen reconstruction.')
        labels = ['Scheduled event', 'Camera actions', 'Capture keys', 'Archive products']
        notes = ['One event is represented repeatedly.', 'Five exposure keys per action.', 'Three archived versions per key.', 'More records do not create more events.']
        for i, r in enumerate(rows):
            y = c.y
            c.circle(c.m+12, y+15, 8, COLORS[i%3])
            if i < 3:
                c.line(c.m+12, y+27, c.m+12, y+132, LINE, 3)
                # Small fan-out cue represents branching, not a quantitative area scale.
                for delta in [-7, 0, 7]:
                    c.line(c.m+12, y+110, c.m+12+delta, y+126, LINE, 2)
            c.text(c.m+49, y+34, f"{r['value']:,}", 52 if mobile else 58, COLORS[i%3], '600')
            if mobile:
                c.text(c.m+49, y+77, labels[i], 32, INK, '500')
                c.y = c.wrap(c.m+49, y+117, notes[i], size=c.small)+23
            else:
                c.text(c.m+315, y+34, labels[i], 32, INK, '500')
                c.y = c.wrap(c.m+315, y+77, notes[i], size=c.small)+38
        return c.footer(f['note']+' Branching is schematic, not proportional area.')
    if number == 2:
        c.marker=50
        c.subtitle('Sunset share: first choose the population, then choose the counting unit.')
        c.text(c.m, c.y, 'Keep only filled-in target fields', c.label, INK, '600'); c.y += 65
        for r in rows[:2]:
            label = 'All target fields' if r is rows[0] else 'Nonblank target fields'
            c.bar(label, r['value'], 100, TEAL, detail=r['detail'])
        c.axis(100, '%')
        c.line(c.m, c.y-16, c.w-c.m, c.y-16)
        c.text(c.m, c.y+25, 'Inside that selected population', c.label, INK, '600'); c.y += 86
        for i,r in enumerate(rows[2:]):
            c.bar(['Actions','Exposures','Products','Bytes'][i], r['value'], 100, COLORS[i%3])
        c.axis(100, '%')
        return c.footer('All bars: 0–100%; dashed marker: 50%. The byte majority is not present in every representation layer. '+f['note'])
    if number == 3:
        c.subtitle('Share of the whole reconstructed cohort assigned to the connected Sunset context.')
        for i,r in enumerate(rows):
            c.bar(r['label'], r['value'], 25, COLORS[i], detail=r['detail'])
        c.axis(25, '%')
        return c.footer('Common scale: 0–25%. '+f['note'])
    if number == 4:
        c.subtitle('Compare within each counting unit. Both panels describe the same two windows.')
        for group, maximum, heading in [(rows[:2],80,'Count actions: Guided Discussion leads'),(rows[2:],1000,'Count products: Earthset leads')]:
            c.y = c.wrap(c.m, c.y, heading, size=c.label, color=INK, weight='600')+30
            for i,r in enumerate(group):
                c.bar(r['label'].split(': ',1)[1],r['value'],maximum,COLORS[i],suffix='',precision=0)
            c.axis(maximum)
            c.y += 15
        c.y = c.wrap(c.m,c.y,'Guided Discussion: three exposure keys per action, nine products. Earthset: five exposure keys, fifteen products.')+15
        return c.footer(f['note'])
    if number == 5:
        c.subtitle('Concentration-equivalent window units. This is an evenness index, not a count of independent events.')
        headings = ['Original memberships', 'Share overlapping memberships', 'Also combine same-name overlaps']
        for policy in range(3):
            c.y = c.wrap(c.m,c.y,headings[policy],size=c.label,color=INK,weight='600')+25
            for i,r in enumerate(rows[policy*3:policy*3+3]):
                c.bar(['Actions','Products','Bytes'][i],r['value'],36,COLORS[i],suffix=' units')
            c.axis(36)
        return c.footer('All index tracks: 0–36. Equal original membership weights would give 36. '+f['note'])
    if number == 6:
        c.subtitle('Groups appearing in both training and test, under a constructed split. Zero is a pass only for the declared layer.')
        for i,r in enumerate(rows):
            c.y = c.wrap(c.m,c.y,r['label'],size=c.label,color=INK,weight='600')+18
            counts = re.findall(r'([\d,]+) / ([\d,]+)',r['detail'])
            for j,(n,total) in enumerate(counts):
                c.text(c.m+16,c.y,'Camera actions' if j==0 else 'Five-second groups',c.small,MUTED)
                c.text(c.w-c.m,c.y,f'{n} / {total}',c.small,TEAL if n=='0' else INDIGO,'600','end')
                c.y += 44
            c.line(c.m,c.y,c.w-c.m,c.y);c.y += 54
        return c.footer(f['note'])
    if number == 7:
        c.subtitle('Retained transcript anchors, 7 April 2026. Spacing shows sequence, not elapsed time.')
        for i,r in enumerate(rows):
            y=c.y;report=i in [0,4,8]
            c.circle(c.m+8,y-9,8,INDIGO if report else TEAL)
            if i<8:c.line(c.m+8,y+5,c.m+8,y+(113 if mobile else 67),LINE,3)
            label='Candidate after ground query' if i==7 else r['label']
            if mobile:
                c.text(c.m+39,y,label,30,INK,'500')
                c.text(c.m+39,y+44,r['detail'],28,MUTED)
                c.y+=119
            else:
                c.text(c.m+44,y,label,28,INK,'500')
                c.text(c.w-c.m,y,r['detail'],27,MUTED,anchor='end');c.y+=76
        return c.footer(f['note'])
    if number == 8:
        c.subtitle('Different layers answer different questions. The proposed companion preserves the archive’s existing identity.')
        explanations=[('PDS4 archive','Which product is this, and where did it come from?'),
                      ('Training-data concepts','What is the task, sample, label and split role?'),
                      ('Task companion','Which captures and actions are related, and what must stay together?'),
                      ('Window memberships','Keep zero, one or many links; do not force a single owner.')]
        for i,(label,detail) in enumerate(explanations):
            c.text(c.m,c.y,label,c.label,COLORS[i%3],'600');c.y+=48
            c.y=c.wrap(c.m,c.y,detail,size=c.label)+26
            c.line(c.m,c.y,c.w-c.m,c.y);c.y+=50
        return c.footer(f['note'])
    if number == 9:
        c.subtitle('A useful archive does not have one universal ready/not-ready state.')
        for i,r in enumerate(rows):
            c.y=c.wrap(c.m,c.y,r['label'],size=c.label,color=INK,weight='600')+12
            status,detail=r['detail'].split('. ',1)
            c.y=c.wrap(c.m,c.y,status, size=c.label,color=TEAL if i<2 else INDIGO,weight='500')
            c.y=c.wrap(c.m,c.y+10,detail,size=c.small)+24
            c.line(c.m,c.y,c.w-c.m,c.y);c.y+=45
        return c.footer(f['note'])
    raise ValueError('Unowned figure')


def build(check=False):
    values_path=ROOT/'presentation/figure-reading-values.json'
    values=json.loads(values_path.read_bytes())
    for row in values['sources']:
        if hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Unqualified figure source: '+row['path'])
    outputs={}
    for f in values['figures']:
        for mobile in [False,True]:
            name=f"figure-{f['number']:02}-{'phone' if mobile else 'desktop'}.svg"
            outputs[name]=render(f,mobile)
    manifest=dict(version='editorial-v6',new_science=False,
                  values_sha256=hashlib.sha256(values_path.read_bytes()).hexdigest(),
                  source_receipts=values['sources'],
                  files=[dict(path=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in outputs.items()])
    outputs['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    OUT.mkdir(parents=True,exist_ok=True)
    for name,data in outputs.items():
        if check:
            if (OUT/name).read_bytes()!=data:raise ValueError('Figure build drift: '+name)
        else:(OUT/name).write_bytes(data)
    print(json.dumps(dict(pass_=True,svg_figures=18,new_science=False,check=check)))


if __name__=='__main__':build('--check' in sys.argv)
