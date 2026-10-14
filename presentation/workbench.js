'use strict';
// Interaction receipts describe views of existing evidence, never new scientific verdicts.
const EvidenceWorkbench = (() => {
  const fields = ['decision','context','fanunit','relation','cascade','rank','budget','concentration','attention','amplitude','claim','trace'];
  const base = {decision:'inventory',context:'context',fanunit:'products',relation:'capture',cascade:'all_fields',rank:'actions',budget:0,concentration:'raw',attention:0,amplitude:250,claim:'relationship',trace:'original'};
  function options(e) {
    return {decision:e.decisions.map(x=>x.id),context:['context','planned'],fanunit:['products','exposures','actions'],relation:['capture','action'],cascade:e.cascade.map(x=>x.id),rank:['actions','products'],budget:[0,47,48],concentration:['raw','fractional','collapsed'],attention:e.attention.timeline.map((_,i)=>i),amplitude:e.recovery.curve.map(x=>x.requested_integrated_dn_per_frame),claim:['relationship','selection','weighting','detection'],trace:['original','conditional']};
  }
  function validate(value,e) {
    if(!value || typeof value!=='object' || Array.isArray(value) || Object.keys(value).length!==fields.length || Object.keys(value).some(k=>!fields.includes(k))) throw Error('Unknown or incomplete view controls.');
    const allowed=options(e);
    for(const k of fields) if(!allowed[k].includes(value[k])) throw Error('Unsupported view setting: '+k+'.');
    return Object.fromEntries(fields.map(k=>[k,value[k]]));
  }
  function decode(hash,e,identity) {
    if(!hash.startsWith('#view=')) return null;
    if(hash.length>4000) throw Error('Saved view is too long.');
    let saved;
    try {saved=JSON.parse(decodeURIComponent(hash.slice(6)));} catch {throw Error('Saved view is not valid JSON.');}
    if(!saved || saved.version!==1 || saved.evidence_sha256!==identity || Object.keys(saved).sort().join(',')!=='evidence_sha256,state,version') throw Error('Saved view has an unsupported version or a different evidence identity.');
    return validate(saved.state,e);
  }
  function encode(state,e,identity) {
    return '#view='+encodeURIComponent(JSON.stringify({version:1,evidence_sha256:identity,state:validate(state,e)}));
  }
  function summarize(state,e) {
    validate(state,e);
    const cascade=e.cascade.find(x=>x.id===state.cascade),robust=e.robustness.scenarios.find(x=>x.reassignment_budget===state.budget),record=e.audit_trail[state.trace],recovery=e.recovery.curve.find(x=>x.requested_integrated_dn_per_frame===state.amplitude);
    const concentrationKey={raw:'raw_concentration_equivalent_windows',fractional:'fractional_concentration_equivalent_windows',collapsed:'collapsed_fractional_concentration_equivalent_windows'}[state.concentration],concentration=e.concentration[concentrationKey],anchor=e.attention.timeline[state.attention];
    return [
      {id:'fanout',label:'Sunset footprint',value:e.fanout[state.context][state.fanunit].toLocaleString('en-US')+' '+state.fanunit,context:state.context==='context'?'Conservative connected context':'Eight-minute plan window',source:'fanout',pointer:'/segments',ceiling:'One schedule entry, not a physical independence certificate.'},
      {id:'relation',label:'Test products without a training match',value:(state.relation==='capture'?e.relationship.action_only_linked_test_products:e.relationship.action_isolated_test_products)+' / '+e.relationship.test_products.toLocaleString('en-US'),context:state.relation==='capture'?'Protected relation: exact capture key':'Protected relation: complete original action',source:'relationship',pointer:'/structural_isolation',ceiling:'Constructed canary, not observed NASA splitting or model harm.'},
      {id:'selection',label:'Recorded Sunset share',value:(100*cascade.numerator/cascade.denominator).toFixed(3)+'%',context:cascade.unit+'; '+cascade.population,source:'selection',pointer:cascade.pointer,ceiling:'Recorded metadata membership, not image-content prevalence.'},
      {id:'rank',label:'Larger scheduled window',value:state.rank==='actions'?'Guided Discussion':'Earthset',context:'Original planned-window '+state.rank,source:'rank',pointer:'/product_reversal_examples/0',ceiling:'Archive prominence, not scientific importance.'},
      {id:'robustness',label:'Possible selected-byte share',value:(100*robust.lower.numerator/robust.total_weight).toFixed(6)+'% to '+(100*robust.upper.numerator/robust.total_weight).toFixed(6)+'%',context:'Fixed nonblank subset; combined bytes; at most '+state.budget+' hypothetical field changes',source:'robustness',pointer:'/reassignment_sensitivity/'+(81+2*[0,1,25,47,48,50,100,200].indexOf(state.budget)),ceiling:'Separate endpoint witnesses, not errors or a confidence interval.'},
      {id:'trace',label:'Action-isolated test products',value:record.action_isolated_test_products+' / '+record.test_products.toLocaleString('en-US'),context:state.trace==='original'?'Original frozen cohort':'Conditional one-action withholding',source:e.audit_trail[state.trace+'_source'],pointer:e.audit_trail[state.trace+'_pointer'],ceiling:'Constructed split; original grouping remains order-sensitive.'},
      {id:'concentration',label:'Concentration-equivalent window units',value:'Actions '+concentration.actions.toFixed(3)+'; products '+concentration.products.toFixed(3)+'; bytes '+concentration.archive_size_bytes.toFixed(3),context:state.concentration+' overlap policy; 36 original scheduled windows',source:'concentration',pointer:'/metrics/'+concentrationKey,ceiling:'Descriptive concentration, not effective sample size or independent events.'},
      {id:'attention',label:'Selected transcript anchor',value:anchor.utc,context:anchor.phase,source:'attention',pointer:'/timeline/'+state.attention,ceiling:'Changing attention state, not a numbered event or detection probability.'},
      {id:'recovery',label:'Synthetic clip-native recovery',value:recovery.recovered+' / '+recovery.trials,context:state.amplitude.toLocaleString('en-US')+' requested digital counts / frame',source:'recovery',pointer:'/recovery_curve/'+e.recovery.curve.indexOf(recovery),ceiling:'Uncalibrated synthetic units, not event photometry or flux.'}
    ];
  }
  function receipt(state,saved,e,identity) {
    return {kind:'READ_ONLY_VIEW_RECEIPT',version:1,evidence_sha256:identity,state:validate(state,e),saved_comparison:saved?validate(saved,e):null,panels:summarize(state,e).map(p=>({...p,source_identity:e.sources[p.source]})),limits:'Build-time snapshot and selected controls only. No source changed, scientific claim upgraded, independent replay or human acceptance established.'};
  }
  return {fields,base,validate,decode,encode,summarize,receipt};
})();
if(typeof module!=='undefined' && module.exports) module.exports=EvidenceWorkbench;

if(typeof document!=='undefined' && document.getElementById('workspace')) {
  const W=EvidenceWorkbench,identity=document.getElementById('evidence-identity').textContent.trim();
  let saved=null,lastControl=null;
  $('open-workspace').hidden=true;
  function openWorkspace(){if($('technical-notebook'))$('technical-notebook').open=true;$('workspace').open=true;$('workspace').querySelector('summary').focus();}
  $('open-workspace').addEventListener('click',openWorkspace);
  $('go-sunset-counting').addEventListener('click',()=>{$('counting-title').focus();$('sunset-counting').scrollIntoView({block:'start'});});
  $('return-to-story').addEventListener('click',()=>{(lastControl||document.querySelector('[data-decision="inventory"]')).focus();});
  const attrs={decision:'data-decision',context:'data-context',fanunit:'data-fanunit',relation:'data-relation',cascade:'data-cascade',rank:'data-rank',budget:'data-budget',concentration:'data-concentration',attention:'data-attention',claim:'data-claim',trace:'data-trace'};
  function view() {
    const state={...W.base};
    for(const [k,attr]of Object.entries(attrs)) {const b=document.querySelector('['+attr+'][aria-pressed="true"]');if(b)state[k]=['budget','attention'].includes(k)?Number(b.getAttribute(attr)):b.getAttribute(attr);}
    state.amplitude=Number($('amplitude').value);return W.validate(state,E);
  }
  function apply(state) {
    W.validate(state,E);context=state.context;fanunit=state.fanunit;
    renderDecision(state.decision);renderFanout();renderRelationship(state.relation);renderCascade(state.cascade);renderRanking(state.rank);renderRobustness(state.budget);renderConcentration(state.concentration);renderAttention(state.attention);$('amplitude').value=String(state.amplitude);renderRecovery(state.amplitude);renderClaim(state.claim);renderTrace(state.trace);
    if(state.budget!==0)$('robustness').open=true;
    update();
  }
  function update() {
    const state=view(),rows=W.summarize(state,E),before=saved?W.summarize(saved,E):null;
    const changed=saved?W.fields.filter(k=>state[k]!==saved[k]):[];
    const names={decision:'research question',context:'Sunset context boundary',fanunit:'Sunset footprint unit',relation:'protected relationship',cascade:'Sunset counting choice',rank:'window ranking unit',budget:'hypothetical change budget',concentration:'overlap policy',attention:'transcript anchor',amplitude:'synthetic signal amplitude',claim:'recommendation',trace:'trace population'};
    $('view-summary').textContent='Current view: '+E.decisions.find(x=>x.id===state.decision).title+' '+(saved?(changed.length?'Changed controls: '+changed.map(k=>names[k]).join(', ')+'.':'All controls match saved view A.'):'Save a view if you want to keep it beside another. Use “Change Sunset counting” for the four clearly labeled choices.');
    $('restore-view').disabled=!saved;$('clear-view').disabled=!saved;$('open-workspace').hidden=!saved;
    $('comparison-rows').innerHTML=rows.map((r,i)=>'<tr><th scope="row">'+escapeText(r.label)+'</th><td>'+(before?'<b>'+escapeText(before[i].value)+'</b><small>'+escapeText(before[i].context)+'</small>':'No view saved')+'</td><td><b>'+escapeText(r.value)+'</b><small>'+escapeText(r.context)+'</small></td><td>'+(before?(r.value===before[i].value && r.context===before[i].context?'Unchanged':'Different setting or accounting result. Read both contexts; no automatic subtraction.'):'Save a view to compare.')+'<small>'+escapeText(r.ceiling)+'</small></td></tr>').join('');
    const output=W.receipt(state,saved,E,identity);$('view-receipt').value=JSON.stringify(output,null,2);
    document.dispatchEvent(new CustomEvent('evidence-viewchange',{detail:{state,saved}}));
  }
  $('save-view').addEventListener('click',()=>{saved=view();update();$('workspace-status').textContent='Saved as A. Next: choose “Change Sunset counting” to reach the four counting choices. B follows your next choice; the source evidence stays unchanged.';});
  $('restore-view').addEventListener('click',()=>{if(saved){apply(saved);$('workspace-status').textContent='Restored saved view A. No source evidence changed.';}});
  $('clear-view').addEventListener('click',()=>{saved=null;update();$('workspace-status').textContent='Comparison cleared. Current story settings retained.';});
  $('reset-view').addEventListener('click',()=>{apply(W.base);$('workspace-status').textContent='Story controls reset. Saved comparison retained.';});
  $('view-link').addEventListener('click',()=>{const url=new URL(location.href);url.hash=W.encode(view(),E,identity);$('saved-view-link').value=url.href;$('saved-view-link').hidden=false;$('saved-view-link').focus();$('saved-view-link').select();$('workspace-status').textContent='View address ready to copy. It works only for this exact evidence edition at the same reachable file or URL. It uploads nothing.';});
  $('download-view').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([$('view-receipt').value],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='artemis-ii-view-receipt.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$('workspace-status').textContent='Download requested. If blocked, expand the receipt below and copy its JSON.';});
  function sources() {
    const query=$('source-search').value.trim().toLowerCase(),entries=Object.entries(E.sources).filter(([key,s])=>(key+' '+s.path+' '+s.sha256).toLowerCase().includes(query));
    $('source-search-results').innerHTML=entries.map(([key])=>'<details class="source-note"><summary>'+escapeText(key.replaceAll('_',' '))+'</summary>'+sourceCard(key,'/')+'</details>').join('');
    $('source-search-count').textContent=entries.length+' of '+Object.keys(E.sources).length+' sources'+(entries.length?'':'. No matches. Try a filename, source key or hash; clear the search to recover.');
  }
  $('source-search').addEventListener('input',sources);$('clear-source-search').addEventListener('click',()=>{$('source-search').value='';sources();$('source-search').focus();});
  document.addEventListener('click',event=>{const control=event.target.closest('[data-decision],[data-context],[data-fanunit],[data-relation],[data-cascade],[data-rank],[data-budget],[data-concentration],[data-attention],[data-claim],[data-trace]');if(control){lastControl=control;update();}});
  $('amplitude').addEventListener('change',()=>{lastControl=$('amplitude');update();});
  function load() {try {const state=W.decode(location.hash,E,identity);if(state){apply(state);openWorkspace();$('workspace-status').textContent='Loaded source-matched saved view. This is a view, not a scientific result.';}}catch(error){openWorkspace();$('workspace-status').textContent=error.message+' Current controls retained; reset the view to recover.';}}
  window.addEventListener('hashchange',load);update();sources();load();
}
