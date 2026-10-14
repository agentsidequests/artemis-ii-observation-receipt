"""Readable, offline exports of original and conditional views."""

import html


def display(metric, field, delta=False):
    value = metric[field]
    places = metric.get('places', 3)
    if metric['unit'] in {'count', 'bytes'}:
        text = f'{value:+,}' if delta and value else f'{value:,}'
    else:
        text = f'{value:+,.{places}f}' if delta and value else f'{value:,.{places}f}'
    if delta:
        return text + (' pp' if metric['unit'] == 'percent' else '')
    return text + ('%' if metric['unit'] == 'percent' else '')


def csv_rows(receipt):
    rows = []
    for comparison in receipt.get('conditional_comparisons', []):
        for metric in comparison['metrics']:
            rows.append({'comparison_id':comparison['id'], 'metric_id':metric['id'], 'label':metric['label'],
                         'unit':metric['unit'], 'original':metric['original'], 'conditional':metric['conditional'],
                         'delta':metric['delta'], 'delta_unit':metric['delta_unit'],
                         'source_artifact_id':comparison['source_artifact_id'],
                         'original_pointer':comparison['original_pointer'] + metric['pointer'],
                         'conditional_pointer':comparison['conditional_pointer'] + metric['pointer'],
                         'scale':metric.get('scale',1), 'replaces_original':False})
    return rows


def markdown(receipt):
    lines = []
    if receipt.get('identity_groups'):
        lines.extend((['## Historical metadata alternatives retained', '', 'The frozen metadata-only gate is preserved below. Current steward evidence is shown separately; local byte equality remains unverified. No representative is selected.', ''] if receipt.get('steward_links') else ['## Unresolved identities', '', 'Metadata alternatives are not physically validated duplicates. No representative is selected.', '']))
        for group in receipt['identity_groups']:
            lines.extend([f"### {group['label']}", '', f"State: `{group['status']}`", '',
                          'Alternatives: ' + (', '.join(group['alternatives']) or 'Unavailable: source integrity blocked'),
                          '', f"Source: {group['source_artifact_id']} at {group['alternatives_pointer']}", '', group.get('note',''), ''])
    for comparison in receipt.get('conditional_comparisons', []):
        lines.extend(['## Original preserved; conditional view compared', '', comparison['label'], '',
                      f"State: `{comparison['status']}`", '', comparison['treatment'], '',
                      'This view does not replace the original. Percentage deltas are percentage points.', '',
                      f"| Metric | Unit | {comparison['original_label']} | {comparison['conditional_label']} | Change |",
                      '| --- | --- | ---: | ---: | ---: |'])
        for metric in comparison['metrics']:
            lines.append(f"| {metric['label']} | {metric['unit']} | {display(metric,'original')} | {display(metric,'conditional')} | {display(metric,'delta',True)} |")
        if not comparison['integrity_verified']:
            lines.extend(['', 'Comparison unavailable: source integrity did not verify.'])
        lines.extend(['', 'One treatment and its predicates are not independent replications.', '', comparison['claim_ceiling'], ''])
    return '\n'.join(lines)


def render(receipt):
    esc = html.escape
    blocks = []
    if receipt.get('identity_groups'):
        cards = []
        for group in receipt['identity_groups']:
            alternatives = ''.join(f'<li><code>{esc(i)}</code></li>' for i in group['alternatives'])
            if not alternatives:
                alternatives = '<li>Unavailable: source integrity blocked.</li>'
            cards.append(f'<article class="identity-card"><span class="status blocked">{esc(group["status"])}</span>'
                         f'<h3>{esc(group["label"])}</h3><ul class="identity-alternatives">{alternatives}</ul>'
                         '<p><strong>No representative selected. Do not merge these identities.</strong></p>'
                         f'<p>{esc(group.get("note",""))}</p><details><summary>Inspect identity provenance</summary>'
                         f'<dl><dt>Source artifact</dt><dd>{esc(group["source_artifact_id"])}</dd>'
                         f'<dt>Source pointer</dt><dd><code>{esc(group["alternatives_pointer"])}</code></dd>'
                         f'<dt>Source locator</dt><dd>{esc(group.get("source_locator",""))}</dd>'
                         f'<dt>Basis</dt><dd>{esc(group["basis"])}, not physical validation</dd></dl></details></article>')
        heading = 'Historical metadata alternatives retained' if receipt.get('steward_links') else 'Unresolved means unresolved'
        eyebrow = 'Metadata-only identity boundary' if receipt.get('steward_links') else 'Identity boundary'
        blocks.append('<section id="identities"><p class="eyebrow">'+eyebrow+'</p><h2>'+heading+'</h2>'
                      '<p class="section-intro">Matching metadata supplies alternatives to inspect, not a license to pick an identity.</p>' + ''.join(cards) + '</section>')
    for comparison in receipt.get('conditional_comparisons', []):
        rows = ''.join(f'<tr><th scope="row">{esc(m["label"])}</th><td>{esc(m["unit"])}</td>'
                       f'<td class="number">{esc(display(m,"original"))}</td><td class="number conditional-value">{esc(display(m,"conditional"))}</td>'
                       f'<td class="number">{esc(display(m,"delta",True))}</td></tr>' for m in comparison['metrics'])
        if not comparison['integrity_verified']:
            rows = '<tr><td colspan="5">Comparison unavailable: source integrity did not verify. No numeric result is shown.</td></tr>'
        provenance = ''.join(f'<li><strong>{esc(m["label"])}</strong>: <code>{esc(m["pointer"])}</code>; scale {m.get("scale",1)}</li>' for m in comparison['metrics'])
        blocks.append('<section id="comparison"><p class="eyebrow">Conditional sensitivity</p>'
                      '<h2>Original preserved. Conditional view compared.</h2>'
                      f'<p class="section-intro">{esc(comparison["label"])}. These are two declared populations, not corrected physical counts.</p>'
                      f'<aside class="comparison-note"><strong>Treatment</strong><p>{esc(comparison["treatment"])}</p>'
                      '<p>One treatment, not independent replications. No original receipt is replaced.</p></aside>'
                      '<div class="table-wrap comparison-region" tabindex="0" role="region" aria-label="Original and conditional numeric comparison">'
                      '<table><caption>Exact source values are in the downloadable receipt and CSV. Display values are rounded. pp means percentage points.</caption>'
                      f'<thead><tr><th scope="col">Metric</th><th scope="col">Unit</th><th scope="col">{esc(comparison["original_label"])}</th>'
                      f'<th scope="col">{esc(comparison["conditional_label"])}</th><th scope="col">Change</th></tr></thead><tbody>{rows}</tbody></table></div>'
                      '<details class="comparison-provenance"><summary>Inspect comparison source paths and limits</summary>'
                      f'<dl><dt>Source artifact</dt><dd>{esc(comparison["source_artifact_id"])}</dd>'
                      f'<dt>Original root</dt><dd><code>{esc(comparison["original_pointer"])}</code></dd>'
                      f'<dt>Conditional root</dt><dd><code>{esc(comparison["conditional_pointer"])}</code></dd>'
                      '<dt>Replaces original</dt><dd>No</dd></dl>'
                      f'<ul class="source-paths">{provenance}</ul><p>{esc(comparison["claim_ceiling"])}</p></details></section>')
    return ''.join(blocks)
