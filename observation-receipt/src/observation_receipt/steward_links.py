"""Preserve a scoped steward statement separately from local byte verification."""
from datetime import datetime
import html
from .comparisons import pointer, read_source, valid_pointer


def validate(case, artifact_ids, errors):
    if 'steward_links' not in case:
        return
    if case.get('receipt_version') != '0.4.0':
        errors.append('Steward links require receipt_version 0.4.0')
        return
    links=case['steward_links']
    if not isinstance(links,list) or not links or any(not isinstance(v,dict) for v in links):
        errors.append('Steward links must be a nonempty object array')
        return
    ids=[v.get('id') for v in links]
    if any(not isinstance(v,str) or not v for v in ids) or len(set(ids)) != len(ids):
        errors.append('Steward links require distinct string IDs')
    groups={g['id'] for g in case.get('identity_groups',[]) if isinstance(g,dict) and isinstance(g.get('id'),str)}
    for link in links:
        if set(link) != {'id','group_id','source_artifact_id','statement_pointer'}:
            errors.append('Steward links cannot contain literal identities, selected representatives or unsupported fields')
        if not isinstance(link.get('group_id'),str) or link.get('group_id') not in groups:
            errors.append('Steward link group_id does not resolve')
        if not isinstance(link.get('source_artifact_id'),str) or link.get('source_artifact_id') not in artifact_ids:
            errors.append('Steward link source_artifact_id does not resolve')
        else:
            artifact=next(a for a in case['artifacts'] if a['id']==link['source_artifact_id'])
            if not artifact.get('path'):
                errors.append('Steward link requires a pinned local artifact')
        if not valid_pointer(link.get('statement_pointer')):
            errors.append('Steward link statement_pointer must be a JSON pointer')


def build(case, root, checks, groups):
    artifacts={a['id']:a for a in case['artifacts']}
    integrity={c['id']:c for c in checks}
    result=[]
    for link in case.get('steward_links',[]):
        group=next(g for g in groups if g['id']==link['group_id'])
        data=read_source(artifacts[link['source_artifact_id']],root,integrity)
        if data is None or not group['integrity_verified']:
            result.append({**link,'status':'BLOCKED_STEWARD_SOURCE_INTEGRITY','integrity_verified':False,'statement':None})
            continue
        statement=pointer(data,link['statement_pointer'])
        required={'evidence_class','source_owner','date_utc','native_identifiers','relationship','reported_original_filename',
                  'archive_source_url','local_byte_identity_verified','checksums_supplied','other_pairs_confirmed',
                  'denominators_changed','publication_permission_established','scope'}
        if not isinstance(statement,dict) or set(statement)!=required:
            raise ValueError('Steward statement shape is not qualified')
        if statement['evidence_class']!='archive_steward_correspondence' or statement['relationship']!='identical_images_reported_by_steward':
            raise ValueError('Unsupported steward evidence class or relationship')
        members=statement['native_identifiers']
        if not isinstance(members,list) or len(members)!=2 or any(not isinstance(v,str) or not v for v in members) or len(set(members))!=2 or set(members)!=set(group['alternatives']):
            raise ValueError('Steward statement must match exactly the two source-bound alternatives')
        for name in ['local_byte_identity_verified','checksums_supplied','other_pairs_confirmed','denominators_changed','publication_permission_established']:
            if statement[name] is not False:
                raise ValueError('Steward-only link cannot promote byte verification, other pairs, counts or publication')
        for name in ['source_owner','date_utc','reported_original_filename','archive_source_url','scope']:
            if not isinstance(statement[name],str) or not statement[name].strip():
                raise ValueError('Steward statement requires nonempty source/locator/qualification fields')
        if datetime.fromisoformat(statement['date_utc'].replace('Z','+00:00')).tzinfo is None:
            raise ValueError('Steward date must include its timezone')
        if not statement['archive_source_url'].startswith('https://'):
            raise ValueError('Steward archive locator must be an HTTPS pointer')
        result.append({**link,'status':'STEWARD_CONFIRMED_IDENTICAL_IMAGES','integrity_verified':True,
                       'statement':statement,'representative_selected':False,'counts_recomputed':False,
                       'email_authentication_performed_by_app':False})
    return result


def markdown(receipt):
    lines=[]
    for link in receipt.get('steward_links',[]):
        lines.extend(['## Steward confirmation, not local byte verification','',f"State: `{link['status']}`",''])
        if link['statement'] is None:
            lines.extend(['Confirmation unavailable: pinned statement or alternative-source integrity did not verify.',''])
            continue
        s=link['statement']
        lines.extend([f"Catalogue IDs: {', '.join(s['native_identifiers'])}",'',
                      f"Steward-reported original filename: `{s['reported_original_filename']}`",'',
                      f"Source: {s['source_owner']}, {s['date_utc']}",'',s['scope'],'',
                      'Both IDs and original counts are retained. No representative selected or denominator recomputed.',
                      'The app checks this authored extract and its group binding, not email authentication or NEF byte equality.','',
                      f"Archive locator supplied by steward: {s['archive_source_url']}",''])
    return '\n'.join(lines)


def render(receipt):
    blocks=[]
    esc=html.escape
    for link in receipt.get('steward_links',[]):
        if link['statement'] is None:
            blocks.append('<section id="steward-confirmation"><h2>Steward evidence could not be verified</h2><p>No confirmation values are shown: pinned statement or alternative-source integrity failed.</p></section>')
            continue
        s=link['statement']
        ids=''.join('<li><code>'+esc(v)+'</code></li>' for v in s['native_identifiers'])
        blocks.append('<section id="steward-confirmation"><p class="eyebrow">Current source-identity evidence</p>'
                      '<h2>Two catalogue IDs. One steward-confirmed image.</h2>'
                      '<article class="identity-card"><span class="status other">Steward confirmation received</span>'
                      '<ul class="identity-alternatives">'+ids+'</ul><h3>Reported original filename: <code>'+esc(s['reported_original_filename'])+'</code></h3>'
                      '<p>'+esc(s['source_owner'])+' · '+esc(s['date_utc'])+'</p><p>'+esc(s['scope'])+'</p>'
                      '<p><strong>Both native IDs and original counts are retained.</strong> No representative is selected and no denominator is recomputed.</p>'
                      '<details><summary>Inspect the source statement and remaining proof gaps</summary><dl>'
                      '<dt>Evidence class</dt><dd>Archive-steward correspondence, not independently measured file-byte identity</dd>'
                      '<dt>Source artifact and pointer</dt><dd><code>'+esc(link['source_artifact_id'])+' '+esc(link['statement_pointer'])+'</code></dd>'
                      '<dt>Local NEF-byte equality</dt><dd>Not verified; no checksums supplied</dd>'
                      '<dt>Public JPEG processing</dt><dd>Exact transformation recipe remains unresolved</dd>'
                      '<dt>Archive locator</dt><dd><a href="'+esc(s['archive_source_url'],quote=True)+'">Open the steward-supplied NEF record</a></dd>'
                      '</dl><p>The app checks a hash-pinned authored extract and its exact group binding. It does not authenticate email, download pixels or compare NEF bytes. Private correspondence is not automatically public material.</p></details></article></section>')
    return ''.join(blocks)
