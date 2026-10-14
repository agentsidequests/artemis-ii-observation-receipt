'use strict';
const AssumptionAtlas = (() => {
  function verdict(b) {return 2*b.lower.numerator>b.total_weight?'ABOVE':2*b.upper.numerator<=b.total_weight?'NOT_ABOVE':'MIXED';}
  function select(a,unit,population,budget) {
    const b=a.reassignment_sensitivity.find(b=>b.unit===unit&&b.population===population&&b.reassignment_budget===budget);
    if(!b)throw Error('Unknown saved scenario.');return b;
  }
  function compare(a,b) {
    const matched=a.unit===b.unit&&a.population===b.population&&a.total_weight===b.total_weight;
    return {matched,lower_change_pp:matched?100*(b.lower.numerator-a.lower.numerator)/a.total_weight:null,upper_change_pp:matched?100*(b.upper.numerator-a.upper.numerator)/a.total_weight:null,message:matched?'Same unit, population and denominator. Endpoint changes are accounting differences, not probabilities.':'Unlike units or populations. No numeric difference is computed; compare the stated questions, not the shares as one estimand.'};
  }
  function decode(hash,a,identity) {
    if(!hash.startsWith('#scenario='))return null;
    if(hash.length>2000)throw Error('Scenario address too long.');
    let v;try{v=JSON.parse(decodeURIComponent(hash.slice(10)));}catch{throw Error('Invalid saved scenario JSON.');}
    if(!v||Object.keys(v).sort().join(',')!=='budget,population,result_sha256,unit,version'||v.version!==1||v.result_sha256!==identity)throw Error('Scenario source identity or version does not match this case.');
    return select(a,v.unit,v.population,v.budget);
  }
  return {verdict,select,compare,decode};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=AssumptionAtlas;
if(typeof document!=='undefined'&&document.getElementById('assumption-atlas')) {
  const atlas=document.getElementById('assumption-atlas'),status=document.getElementById('atlas-status');let pinned=null;
  atlas.hidden=false;
  function active() {return AssumptionAtlas.select(A,$('unit').value,$('population').value,Number($('budget').value));}
  function state(b) {return {version:1,result_sha256:D.sources.result.sha256,unit:b.unit,population:b.population,budget:b.reassignment_budget};}
  function update() {
    const b=active(),population=b.population,budgets=[0,1,25,47,48,50,100,200];
    $('atlas-population').textContent=population==='full_cohort'?'Full cohort: blank memberships remain unknown.':'Original nonblank subset: all selected fields stay nonblank.';
    $('atlas-body').innerHTML=Object.entries(units).map(([unit,label])=>'<tr><th scope="row">'+esc(label)+'</th>'+budgets.map(r=>{
      const s=AssumptionAtlas.select(A,unit,population,r),v=AssumptionAtlas.verdict(s),lo=100*s.lower.numerator/s.total_weight,hi=100*s.upper.numerator/s.total_weight,chosen=s===b;
      return '<td><button data-scenario="'+A.reassignment_sensitivity.indexOf(s)+'" aria-pressed="'+chosen+'" aria-label="'+esc(label)+', '+population+', at most '+r+' hypothetical changes: '+lo.toFixed(6)+' to '+hi.toFixed(6)+' percent, '+v+'"><span class="atlas-code">'+(v==='ABOVE'?'Above half':v==='NOT_ABOVE'?'Not above':'Straddles')+'</span><span class="atlas-mini" aria-hidden="true"><i style="left:'+lo+'%;width:'+(hi-lo)+'%"></i></span><span>'+lo.toFixed(2)+'–'+hi.toFixed(2)+'%</span></button></td>';
    }).join('')+'</tr>').join('');
    $('restore-scenario').disabled=!pinned;$('clear-scenario').disabled=!pinned;
    const c=pinned?AssumptionAtlas.compare(pinned,b):null;
    $('scenario-comparison').innerHTML=pinned?'<h3>Saved A and current B</h3><p>'+esc(c.message)+'</p><dl><dt>Saved A</dt><dd>'+esc(units[pinned.unit])+'; '+esc(pinned.population)+'; r = '+pinned.reassignment_budget+'; '+pct(pinned.lower)+'% to '+pct(pinned.upper)+'%; denominator '+num(pinned.total_weight)+'</dd><dt>Current B</dt><dd>'+esc(units[b.unit])+'; '+esc(b.population)+'; r = '+b.reassignment_budget+'; '+pct(b.lower)+'% to '+pct(b.upper)+'%; denominator '+num(b.total_weight)+'</dd>'+(c.matched?'<dt>Endpoint change, B minus A</dt><dd>Lower '+c.lower_change_pp.toFixed(6)+' pp; upper '+c.upper_change_pp.toFixed(6)+' pp. Separate marginal endpoints, not a paired event measurement.</dd>':'')+'</dl>':'<p>Pin a scenario, then change the unit, population or hypothetical budget. The app computes differences only when unit, population and denominator match.</p>';
    $('scenario-receipt').value=JSON.stringify({kind:'READ_ONLY_SCENARIO_COMPARISON',version:1,sources:D.sources,saved:pinned?{state:state(pinned),result:pinned,pointer:'/reassignment_sensitivity/'+A.reassignment_sensitivity.indexOf(pinned)}:null,current:{state:state(b),result:b,pointer:'/reassignment_sensitivity/'+A.reassignment_sensitivity.indexOf(b)},comparison:c,limits:'Hypothetical metadata membership. No observed errors, probability, content validation, independent events or scientific acceptance.'},null,2);
  }
  // Retain native-button focus while the selected matrix is rebuilt.
  $('atlas-body').addEventListener('click',event=>{const button=event.target.closest('[data-scenario]');if(!button)return;const index=Number(button.dataset.scenario),b=A.reassignment_sensitivity[index];if(!b)return;$('unit').value=b.unit;$('population').value=b.population;$('budget').value=String(b.reassignment_budget);render();update();const replacement=$('atlas-body').querySelector('[data-scenario="'+index+'"]');if(replacement)replacement.focus();status.textContent='Selected saved scenario '+index+'. Read its exact integer endpoints and source-linked witnesses below.';});
  $('pin-scenario').addEventListener('click',()=>{pinned=active();update();status.textContent='Saved comparison A. Change a control or select an atlas cell for B.';});
  $('restore-scenario').addEventListener('click',()=>{if(!pinned)return;$('unit').value=pinned.unit;$('population').value=pinned.population;$('budget').value=String(pinned.reassignment_budget);render();update();status.textContent='Restored saved scenario A. Sources unchanged.';});
  $('clear-scenario').addEventListener('click',()=>{pinned=null;update();status.textContent='Saved comparison cleared. Current scenario retained.';});
  $('scenario-address').addEventListener('click',()=>{const url=new URL(location.href);url.hash='#scenario='+encodeURIComponent(JSON.stringify(state(active())));$('scenario-link').value=url.href;$('scenario-link').hidden=false;$('scenario-link').focus();$('scenario-link').select();status.textContent='Address ready to copy. It requires this exact saved source at the same reachable file or URL; no upload occurred.';});
  for(const id of ['unit','population','budget'])$(id).addEventListener('change',update);
  for(const id of ['try-crossing','reset'])$(id).addEventListener('click',update);
  function load() {try {const b=AssumptionAtlas.decode(location.hash,A,D.sources.result.sha256);if(b){$('unit').value=b.unit;$('population').value=b.population;$('budget').value=String(b.reassignment_budget);render();update();atlas.open=true;status.textContent='Loaded source-matched scenario. This is not a new scientific verdict.';}}catch(e){atlas.open=true;status.textContent=e.message+' Current scenario retained. Reset to recorded baseline to recover.';}}
  window.addEventListener('hashchange',load);update();load();
}
