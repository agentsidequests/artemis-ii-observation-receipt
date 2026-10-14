'use strict';
// This is a read-only consumer of the prepared evidence excerpt, not a scientific estimator.
const E = JSON.parse(document.getElementById('evidence-data').textContent);
const $ = id => document.getElementById(id);
const n = value => value.toLocaleString('en-US');
const percentage = (numerator, denominator, places=3) => (100*numerator/denominator).toFixed(places);
const escapeText = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const time = utc => utc.slice(11).replace(/Z$/,'');
function pressed(attribute, selected) {
  document.querySelectorAll('['+attribute+']').forEach(button => button.setAttribute('aria-pressed', String(button.getAttribute(attribute) === String(selected))));
}
function sourceCard(key, pointer) {
  const source = E.sources[key];
  if (!source || typeof pointer !== 'string') throw Error('Unknown source binding');
  return '<div class="source-card"><b>Source locator and byte identity</b><code>'+escapeText(source.path)+'</code><code>JSON pointer: '+escapeText(pointer)+'</code><code>SHA-256: '+source.sha256+'</code><span>'+n(source.bytes)+' bytes. Pinned at build time; a locator is not the receipt content or independent scientific acceptance.</span></div>';
}

function renderDecision(mode) {
  const item=E.decisions.find(d=>d.id===mode);if(!item)throw Error('Undeclared research question');
  $('decision-panel').innerHTML='<h3>'+escapeText(item.title)+'</h3><div class="decision-result"><p>'+escapeText(item.result)+'</p><div><strong>Required unit</strong><p>'+escapeText(item.unit)+'</p></div><div><strong>Next defensible step</strong><p>'+escapeText(item.next)+'</p></div><div><strong>What this does not establish</strong><p>'+escapeText(item.ceiling)+'</p></div></div><a class="action secondary" href="'+item.route+'">'+escapeText(item.route_label)+'</a><details class="source-note"><summary>See the native receipt value and its source locator</summary><pre class="receipt-excerpt">'+escapeText(JSON.stringify(item.excerpt,null,2))+'</pre>'+sourceCard(item.source,item.pointer)+'<p>Pretty-printed JSON values from the pinned receipt. The pathway wording above is our qualified interpretation, not a new verdict engine or a NASA-approved task.</p></details>';
  pressed('data-decision',mode);
}
document.querySelectorAll('[data-decision]').forEach(button=>button.addEventListener('click',()=>renderDecision(button.dataset.decision)));

function renderSteward() {
  const link=E.steward_confirmation,s=link.statement;
  if(!link.integrity_verified||link.status!=='STEWARD_CONFIRMED_IDENTICAL_IMAGES'||!s)throw Error('Current steward statement is not qualified');
  $('steward-panel').innerHTML='<div class="ticket-mechanism"><div><p class="eyebrow">Both catalogue identifiers retained</p><p>'+s.native_identifiers.map(id=>'<code>'+escapeText(id)+'</code>').join('<br>')+'</p></div><div><p class="eyebrow">Steward-reported original filename</p><p><strong>'+escapeText(s.reported_original_filename)+'</strong></p></div></div><p>'+escapeText(s.source_owner)+' · '+escapeText(s.date_utc)+'</p><p><strong>One of 24 metadata candidate pairs is now steward-confirmed.</strong> The other 23 are not confirmed by this reply. Only <code>art002e015991</code> occurs in our counted cohort, so this does not justify subtracting from the original counts.</p><div class="warning"><strong>Confirmation is not a checksum.</strong><p>'+escapeText(s.scope)+'</p><p>The cataloguing explanation is likely; future documentation or mitigation is intended, not completed. The source-order limitation and original/conditional populations remain unchanged.</p></div>';
  $('steward-excerpt').textContent=JSON.stringify(s,null,2);
}

function renderRanking(mode) {
  if(!['actions','products'].includes(mode))throw Error('Undeclared ranking measure');
  const windows=E.rank_comparison.windows,max=Math.max(...windows.map(w=>w[mode]));
  const winner=windows.reduce((a,b)=>a[mode]>b[mode]?a:b);
  $('rank-bars').innerHTML=windows.map((w,index)=>'<div class="ranking-row"><div><span>'+escapeText(w.name)+'</span><b>'+n(w[mode])+' '+mode+'</b></div><div class="ranking-track"><div class="ranking-fill rank-'+index+'" style="width:'+(100*w[mode]/max)+'%"></div></div><p>'+n(w.actions)+' actions × '+w.keys_per_action+' keys × 3 representations = '+n(w.products)+' products</p></div>').join('');
  $('rank-bars').setAttribute('aria-label',windows.map(w=>w.name+': '+n(w[mode])+' '+mode).join('; ')+'. Original window memberships, not scientific importance.');
  $('rank-winner').textContent=winner.name;
  $('rank-exact').textContent=mode==='actions'?'76 > 60 reconstructed actions. Guided Discussion ranks higher.':'900 > 684 products. Earthset ranks higher. The records did not change.';
  $('rank-excerpt').textContent=JSON.stringify(E.rank_comparison.excerpt,null,2);
  pressed('data-rank',mode);
}
document.querySelectorAll('[data-rank]').forEach(button=>button.addEventListener('click',()=>renderRanking(button.dataset.rank)));

function renderTrace(mode) {
  if(!['original','conditional'].includes(mode))throw Error('Undeclared audit population');
  const trail=E.audit_trail,record=trail[mode];
  $('trace-population').textContent=mode==='original'?'Original frozen cohort / constructed product-ID split':'Conditional one-original-action withholding / original assignments retained';
  $('trace-equation').textContent=n(record.test_products)+' = '+n(record.capture_linked_test_products)+' + '+n(record.action_only_linked_test_products)+' + '+n(record.action_isolated_test_products);
  $('trace-condition').textContent=mode==='original'?'Test products = capture-linked + additional action-only-linked + action-isolated. Zero at the complete-action layer is a structural result, not measured leakage or model harm.':'Withhold only '+trail.removed_action+' and its '+n(trail.removed_products)+' products. The test denominator falls by two; the additional action-only bin remains 204. This does not resplit or replace the original reconstruction.';
  $('trace-excerpt').textContent=JSON.stringify(record,null,2);
  $('trace-source').innerHTML=sourceCard(trail[mode+'_source'],trail[mode+'_pointer']);
  const before=trail.order_summary.baseline,reverse=trail.order_summary.reversed_input_order;
  $('trace-order').innerHTML='<h4>The same source, in a different order</h4><p>'+n(before.actions)+' actions / '+n(before.admitted_raw_keys)+' keys become '+n(reverse.actions)+' / '+n(reverse.admitted_raw_keys)+' under input reversal.</p><p>'+escapeText(trail.qualification)+'</p>';
  pressed('data-trace',mode);
}
document.querySelectorAll('[data-trace]').forEach(button=>button.addEventListener('click',()=>renderTrace(button.dataset.trace)));
document.querySelectorAll('[data-source]').forEach(node => {node.innerHTML = sourceCard(node.dataset.source, node.dataset.pointer);});

let context='context', fanunit='products';
function renderFanout() {
  if (!['context','planned'].includes(context) || !['products','exposures','actions'].includes(fanunit)) throw Error('Unknown fan-out view');
  const value=E.fanout[context];
  const labels={products:'archive products', exposures:'native capture keys', actions:'original reconstructed actions'};
  $('fan-count').textContent=n(value[fanunit]);
  $('fan-label').textContent=labels[fanunit]+' in '+(context==='context'?'the conservative connected context':'the eight-minute plan window');
  $('fan-equation').textContent=n(value.actions)+' actions × 5 exposures × 3 representations = '+n(value.products)+' products. Scheduled Sunset events: '+E.fanout.scheduled_events+'.';
  pressed('data-context',context);pressed('data-fanunit',fanunit);
}
document.querySelectorAll('[data-context]').forEach(button => button.addEventListener('click',()=>{context=button.dataset.context;renderFanout();}));
document.querySelectorAll('[data-fanunit]').forEach(button => button.addEventListener('click',()=>{fanunit=button.dataset.fanunit;renderFanout();}));

function renderRelationship(mode) {
  if (!['capture','action'].includes(mode)) throw Error('Unknown protected relationship');
  const r=E.relationship, linked=mode==='capture'?r.capture_linked_test_products:r.capture_linked_test_products+r.action_only_linked_test_products;
  const notLinked=r.test_products-linked;
  $('linked-bar').style.width=percentage(linked,r.test_products,6)+'%';$('unlinked-bar').style.width=percentage(notLinked,r.test_products,6)+'%';
  $('linked-count').textContent=n(linked);$('unlinked-count').textContent=n(notLinked);
  $('linked-label').textContent=mode==='capture'?'test products sharing a capture key with training':'test products sharing a complete original action with training';
  $('unlinked-label').textContent=mode==='capture'?'test products with no matching capture key in training':'test products isolated at the original-action layer';
  $('relation-takeaway').textContent=mode==='capture'?'204 look new at the capture layer.':'None are new at the declared action layer.';
  $('relation-copy').textContent=mode==='capture'?'The 204 remaining products do not share an exact capture key with training. They still share a reconstructed complete camera action. A filename or capture-only check cannot establish new-action generalization.':'Every held-out product is connected to training at the reconstructed complete-action layer. That is an exact accounting result for this canary, not a measurement of model performance or scientific independence.';
  $('relation-chart').setAttribute('aria-label',n(linked)+' linked and '+n(notLinked)+' not linked among '+n(r.test_products)+' test products under the '+mode+' relation');
  pressed('data-relation',mode);
}
document.querySelectorAll('[data-relation]').forEach(button => button.addEventListener('click',()=>renderRelationship(button.dataset.relation)));

function renderCascade(mode) {
  const item=E.cascade.find(item=>item.id===mode);
  if (!item) throw Error('Unknown selection/weighting view');
  const share=percentage(item.numerator,item.denominator);
  $('cascade-share').textContent=share+'%';$('cascade-bar').style.width=share+'%';
  $('cascade-ratio').textContent=n(item.numerator)+' / '+n(item.denominator)+' '+item.unit;
  $('cascade-population').textContent='Population: '+item.population+'.';
  const interpretation={all_fields:'This is recorded Sunset membership across all fields. The blanks are unknown, not negative content labels.',tagged_fields:'The numerator stays 1,553. Filtering blanks changes the denominator to 3,413, so the recorded share rises.',tagged_actions:'This comparison counts original actions with any nonblank tag. An action count is not an exposure count or a physical-event count.',tagged_bytes:'Changing influence to combined attached bytes yields a narrow selected-byte majority. It is neither scientific value nor archive-wide content prevalence.'};
  $('cascade-meaning').textContent=interpretation[mode];
  $('cascade-pointer').textContent='Source: '+E.sources.selection.path+'; '+item.pointer;
  $('cascade-chart').setAttribute('aria-label',share+' percent recorded Sunset share; '+item.population+'; unit '+item.unit);
  pressed('data-cascade',mode);
}
document.querySelectorAll('[data-cascade]').forEach(button => button.addEventListener('click',()=>renderCascade(button.dataset.cascade)));

function renderRobustness(budget) {
  if (![0,47,48].includes(budget)) throw Error('Undeclared hypothetical budget');
  const b=E.robustness.scenarios.find(b=>b.reassignment_budget===budget);
  const lo=percentage(b.lower.numerator,b.total_weight,6),hi=percentage(b.upper.numerator,b.total_weight,6);
  $('robust-range').textContent=lo+'%–'+hi+'%';$('robust-span').style.left=lo+'%';$('robust-span').style.width=percentage(b.width.numerator,b.total_weight,6)+'%';
  const guaranteed=2*b.lower.numerator>b.total_weight;
  $('robust-outcome').textContent=(guaranteed?'Strict majority guaranteed':'Strict majority not guaranteed')+' under the declared at-most-'+budget+' model.';
  $('robust-exact').textContent='Lower '+n(b.lower.numerator)+' / '+n(b.total_weight)+'; upper '+n(b.upper.numerator)+' / '+n(b.total_weight)+'. Fixed selection and weights. Separate endpoint witnesses.';
  $('robust-chart').setAttribute('aria-label','Possible Sunset membership '+lo+' to '+hi+' percent. Strict majority '+(guaranteed?'guaranteed':'not guaranteed')+' under the at-most-'+budget+' hypothetical model');
  pressed('data-budget',budget);
}
document.querySelectorAll('[data-budget]').forEach(button => button.addEventListener('click',()=>renderRobustness(Number(button.dataset.budget))));
const majorityWitness=E.robustness.witnesses;
$('robust-witness').innerHTML=majorityWitness.map((f,index)=>'<tr><td>'+n(index+1)+'<br><code>'+escapeText(f.id)+'</code></td><td><code>'+escapeText(f.action)+'</code><br>'+escapeText(f.activity)+'</td><td>'+n(f.weights.all_representation_bytes)+'</td><td><button data-witness="'+escapeText(f.id)+'" aria-label="Inspect original source for '+escapeText(f.id)+'">Inspect source</button></td></tr>').join('');
$('robust-witness').addEventListener('click',event=>{
  const button=event.target.closest('[data-witness]');if(!button)return;
  const field=majorityWitness.find(f=>f.id===button.dataset.witness);if(!field)throw Error('Unknown witness');
  const node=$('witness-source');node.innerHTML='<h4>Original source: '+escapeText(field.id)+'</h4><p>Original target: '+escapeText(field.target)+'. Hypothetical witness only, not an observed error.</p><code>'+escapeText(E.robustness.manifest_parent)+'</code><p>Manifest SHA-256: <code>'+E.robustness.manifest.sha256+'</code></p>'+Object.entries(field.products).map(([collection,p])=>'<p><strong>'+escapeText(collection)+'</strong> · original CSV row '+p.row+' (header = row 1) · '+n(p.bytes)+' bytes<br><code>'+escapeText(p.id)+'</code></p>').join('');
  node.hidden=false;node.focus();
});

function renderConcentration(mode) {
  const keys={raw:'raw_concentration_equivalent_windows',fractional:'fractional_concentration_equivalent_windows',collapsed:'collapsed_fractional_concentration_equivalent_windows'};
  if (!Object.hasOwn(keys,mode)) throw Error('Unknown overlap policy');
  const weights=E.concentration[keys[mode]];
  const labels={actions:'Actions',products:'Products',archive_size_bytes:'Bytes'};
  $('concentration-bars').innerHTML=Object.entries(labels).map(([key,label])=>'<div class="concentration-row"><div><span>'+label+'</span><b>'+weights[key].toFixed(3)+' / 36</b></div><div class="concentration-track"><div style="width:'+percentage(weights[key],36,6)+'%"></div></div></div>').join('');
  $('concentration-bars').setAttribute('aria-label',Object.entries(labels).map(([key,label])=>label+': '+weights[key].toFixed(3)+' concentration-equivalent window units').join('; ')+'. '+mode+' policy. Not effective sample size.');
  pressed('data-concentration',mode);
}
document.querySelectorAll('[data-concentration]').forEach(button=>button.addEventListener('click',()=>renderConcentration(button.dataset.concentration)));

const timeline=E.attention.timeline;
$('attention-list').innerHTML=timeline.map((item,index)=>'<button data-attention="'+index+'" aria-pressed="'+String(index===0)+'"><span>'+escapeText(time(item.utc))+'</span><span>'+escapeText(item.phase)+'</span></button>').join('');
function renderAttention(index) {
  if (!Number.isInteger(index)||index<0||index>=timeline.length) throw Error('Unknown transcript anchor');
  const item=timeline[index];$('attention-phase').textContent=item.phase;$('attention-time').textContent=time(item.utc)+' UTC / 7 April 2026';$('attention-quote').textContent=item.source_text;$('attention-speaker').textContent='Transcript speaker: '+item.speaker+'. Exact source excerpt, not an independent event identification.';pressed('data-attention',index);
}
$('attention-list').addEventListener('click',event=>{const button=event.target.closest('[data-attention]');if(button)renderAttention(Number(button.dataset.attention));});

const curve=E.recovery.curve;
curve.forEach(point=>$('amplitude').add(new Option(n(point.requested_integrated_dn_per_frame),String(point.requested_integrated_dn_per_frame))));
function renderRecovery(amplitude) {
  const selected=curve.find(p=>p.requested_integrated_dn_per_frame===amplitude);if(!selected)throw Error('Undeclared synthetic level');
  const x=value=>64+(value/16000)*450,y=fraction=>222-fraction*180;
  const points=curve.map(point=>x(point.requested_integrated_dn_per_frame)+','+y(point.recovered/point.trials)).join(' ');
  const ticks=[0,.5,1].map(value=>'<line x1="64" x2="514" y1="'+y(value)+'" y2="'+y(value)+'" stroke="#c4cfcc"/><text x="53" y="'+(y(value)+4)+'" text-anchor="end" fill="#425b65" font-size="12">'+n(value*100)+'%</text>').join('');
  $('recovery-plot').innerHTML='<svg viewBox="0 0 560 300" role="img" aria-label="Synthetic recovery never reaches 50 percent: 0 of 162 trials through 12,000 requested digital counts and 9 of 162 at 16,000"><text x="64" y="24" fill="#425b65" font-size="12">Recovery under the frozen clip-native screen</text>'+ticks+'<polyline points="'+points+'" fill="none" stroke="#226c70" stroke-width="3"/>'+curve.map(point=>'<circle cx="'+x(point.requested_integrated_dn_per_frame)+'" cy="'+y(point.recovered/point.trials)+'" r="'+(point===selected?'6':'3')+'" fill="'+(point===selected?'#9b5b0c':'#226c70')+'"/>').join('')+'<text x="64" y="248" fill="#425b65" font-size="12">0</text><text x="514" y="248" text-anchor="end" fill="#425b65" font-size="12">16,000</text><text x="280" y="282" text-anchor="middle" fill="#425b65" font-size="12">Requested integrated digital counts / frame</text></svg>';
  $('recovery-percent').innerHTML=percentage(selected.recovered,selected.trials,1)+'%<span>clip-native recovery</span>';
  $('recovery-count').textContent=n(selected.recovered)+' / '+n(selected.trials)+' synthetic trials recovered at '+n(amplitude)+' requested integrated digital counts per frame. Realized median addition: '+n(selected.realized_added_dn_per_frame_median)+'.';
}
$('amplitude').addEventListener('change',()=>renderRecovery(Number($('amplitude').value)));

const claims={
  relationship:{title:'Protect the relation your score claims to generalize beyond.',result:'4,511 held-out products have zero isolation at the reconstructed complete-action layer in the frozen product-ID canary.',assumptions:'Original source order and grouping, one constructed split, exact ID relations. Physical identity and statistical independence remain unvalidated.',falsifier:'Fail a claimed protected split when siblings cross it or unknown/many-to-many relations are flattened. Recheck input order and preserve alternatives.',recommendation:'Publish official IDs, derived relation authority/version, complete membership, protected keys, split assignments, hashes and crossing violations. Withhold unresolved identities.',open:'Archive specialists must qualify native lineage, terms and carrier. No observed model harm or universal split rule is established.',source:'relationship',pointer:'/structural_isolation'},
  selection:{title:'Expose the population before interpreting its labels.',result:'3,413 of 7,606 original target fields are nonblank; filtering blanks raises recorded Sunset field share from 20.418% to 45.502%.',assumptions:'Recorded navigation fields, original cohort and exact nonblank predicate. Neither recorded tags nor blank completions are validated image-content labels.',falsifier:'Fail if blanks become negatives, tagged prevalence becomes archive prevalence, or excluded/unknown rows disappear from the receipt.',recommendation:'Publish population, query, attrition, label source/review state and coverage by camera/activity. Accept the concept and reference oracle before a probability audit.',open:'Reviewers must decide whether the task predicts an archive field, depicted appearance or context-assisted physical identity. No accuracy estimate or labeler intent is supplied.',source:'selection',pointer:'/metrics/selection_panel'},
  weighting:{title:'Declare which observation gets a vote.',result:'The original two-window example ranks Guided Discussion above Earthset by actions, but below it by products. The 3-key and 5-key protocols receive 9 and 15 products per action.',assumptions:'Original frozen planned-window memberships and filename/order-conditioned actions. Three representations multiply both protocols equally; bracket length changes relative influence. Byte counts also depend on file size.',falsifier:'Fail if units/populations change silently, overlap double-counts unique weights, a counterfactual is called an observed error, or a completion guarantee becomes a statistical sample size.',recommendation:'Record estimand, unit, population, overlap policy, influence and denominator. If a majority is part of the claim, add its hypothetical budget, source-linked minimum witness and predecessor. Keep completion costs separate.',open:'Specialists must judge task relevance, recorded-tag validation and real audit costs. Bytes are not scientific value, concentration is not effective sample size, and no rank reversal is inferred from majority loss.',source:'rank',pointer:'/product_reversal_examples/0'},
  detection:{title:'A null needs demonstrated sensitivity. A rate needs exposure.',result:'Human observation states changed. The local overlapping-clip screen recovered zero synthetic trials through 12,000 requested digital counts per frame and only 9/162 at 16,000.',assumptions:'A bounded reconstructed/transcoded clip and a synthetic injection family in uncalibrated digital units. Transcript anchors are not numbered event assignments.',falsifier:'Block an exclusionary null without demonstrated sensitivity at the claimed threshold. Block calibrated rate/flux without brightness-conditioned effective area-time and justified dependence.',recommendation:'Retain state-specific coverage, human attention/adaptation/prompt state, sensor calibration, timing, optical/window effects, false-positive review and a source-equivalent recovery surface.',open:'Lunar-impact specialists retain scientific acceptance. Event photometry, thresholds, exact locations, physical clustering, crater confirmation and calibrated flux remain unsupported.',source:'recovery',pointer:'/recovery_curve'}
};
function renderClaim(mode) {
  const claim=claims[mode];if(!claim)throw Error('Unknown claim function');
  const headings={result:'Bounded result',assumptions:'Material assumptions',falsifier:'When the receipt must fail',recommendation:'Explicit proposal',open:'What remains open'};
  $('claim-panel').innerHTML='<h3>'+escapeText(claim.title)+'</h3>'+Object.entries(headings).map(([key,label])=>'<div><strong>'+label+'</strong><p>'+escapeText(claim[key])+'</p></div>').join('')+'<div><strong>Exact source locator</strong>'+sourceCard(claim.source,claim.pointer)+'</div>';
  pressed('data-claim',mode);
}
document.querySelectorAll('[data-claim]').forEach(button=>button.addEventListener('click',()=>renderClaim(button.dataset.claim)));
$('source-inventory').innerHTML=Object.keys(E.sources).map(key=>sourceCard(key,'/')).join('');
$('download-data').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(E,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='artemis-ii-presentation-evidence.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
renderSteward();renderDecision('inventory');renderRanking('actions');renderTrace('original');renderFanout();renderRelationship('capture');renderCascade('all_fields');renderRobustness(0);renderConcentration('raw');renderAttention(0);renderRecovery(curve[0].requested_integrated_dn_per_frame);renderClaim('relationship');
