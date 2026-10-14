'use strict';
// Reader language and views of the same frozen evidence, not new scientific logic.
const ArtemisReader = (() => {
  const copy = {
    all_fields:{unit:'Share of all recorded target entries',title:'A blank name is still an unknown.',description:'1,553 entries are recorded as Sunset. Another 4,193 have no target name. Including the blanks gives 20.418%, but does not tell us the true share of photographs showing Sunset.',short:'1,553 recorded Sunset entries ÷ 7,606 target entries.',limit:'The population is our original reconstructed cohort. These are metadata fields, not independently validated image-content labels.'},
    tagged_fields:{unit:'Share of entries with a recorded target name',title:'The same 1,553 entries now get a bigger share.',description:'Leave the 4,193 blank entries out and only 3,413 entries remain in the total. The Sunset count has not grown. Its recorded share rises to 45.502% because we changed which records get counted.',short:'1,553 recorded Sunset entries ÷ 3,413 nonblank target entries.',limit:'This counts only records with a name. The excluded blanks are still unknown, not established non-Sunset images.'},
    tagged_actions:{unit:'Share of selected reconstructed camera sequences',title:'Now each camera sequence gets one vote.',description:'Among the 915 original reconstructed actions with any nonblank target entry, 311 are associated with recorded Sunset membership. That gives 33.989%. A sequence is a different unit from an entry, and neither is a count of independent events.',short:'311 Sunset-associated actions ÷ 915 selected original actions.',limit:'Selection is at the action level here. This is not a physical-event census, a corrected grouping or independently validated image content.'},
    tagged_bytes:{unit:'Share of combined file bytes for named target entries',title:'Larger files get more influence.',description:'Keep only entries with target names, then count the storage space attached to each. Sunset accounts for 52.413% of those bytes across the source, raw and processed formats. Counting storage rather than entries changes their influence. It does not make Sunset more scientifically important.',short:'409,399,017,151 Sunset-associated bytes ÷ 781,104,206,358 selected bytes.',limit:'A narrow majority of these selected bytes, not of the full archive or of independent observations. Different file representations can give different shares.'}
  };
  function describe(id,e) {
    const row=e.cascade.find(x=>x.id===id);if(!row||!copy[id])throw Error('Unknown reader counting choice.');
    const percent=100*row.numerator/row.denominator;
    const all=e.cascade.find(x=>x.id==='all_fields'),named=e.cascade.find(x=>x.id==='tagged_fields');
    return {...copy[id],id,numerator:row.numerator,denominator:row.denominator,percent,population:row.population,technical_unit:row.unit,pointer:row.pointer,unknown_percent:id==='all_fields'?100*(all.denominator-named.denominator)/all.denominator:0};
  }
  function comparison(a,b,e){return {a:describe(a,e),b:describe(b,e),same_choice:a===b,numeric_difference:null,reason:a===b?'The counting choice is unchanged.':'Different populations or accounting units. Read each denominator; this is not a physical increase and no percentage-point difference is computed.'};}
  return {describe,comparison,choices:Object.keys(copy)};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=ArtemisReader;
if(typeof document!=='undefined'&&document.getElementById('sunset-counting')){
  const R=ArtemisReader;
  function selected(){return document.querySelector('[data-cascade][aria-pressed="true"]').dataset.cascade;}
  function render(id,saved){
    const d=R.describe(id,E);$('reader-unit').textContent=d.unit;$('reader-share').textContent=d.percent.toFixed(3)+'%';
    $('reader-sunset-ring').setAttribute('stroke-dasharray',d.percent+' '+(100-d.percent));
    $('reader-unknown-ring').setAttribute('stroke-dasharray',d.unknown_percent+' '+(100-d.unknown_percent));
    $('reader-unknown-ring').style.strokeDashoffset=String(-(100-d.unknown_percent));
    document.querySelector('.reader-legend .other-key').parentElement.lastChild.textContent=id==='tagged_actions'?'Other selected sequences':id==='tagged_bytes'?'Other selected bytes':'Other named entries';
    $('reader-unknown-legend').hidden=d.unknown_percent===0;
    $('reader-share-svg').setAttribute('aria-label',d.percent.toFixed(3)+' percent recorded Sunset share. '+d.unit+'. '+(d.unknown_percent?'Blank entries remain unknown.':'Blanks are outside this selected view.'));
    $('reader-short-equation').textContent=d.short;$('reader-result-title').textContent=d.title;$('reader-result-copy').textContent=d.description;$('reader-result-limit').textContent=d.limit;
    document.querySelector('.reader-try').innerHTML='<strong>Current answer: '+d.percent.toFixed(3)+'%.</strong> '+(id==='all_fields'?'Try 2, then 4. First the population changes, then the unit. No record is edited.':'The chart and explanation below show what is counted. No record is edited.');
    $('reader-exact-ratio').textContent=n(d.numerator)+' / '+n(d.denominator)+' = '+d.percent.toFixed(3)+'% (rounded to three decimals).';
    $('reader-exact-context').textContent='Population: '+d.population+'. Original accounting unit: '+d.technical_unit+'. Source JSON pointer: '+d.pointer+'.';
    if(saved){const c=R.comparison(saved.cascade,id,E);$('reader-comparison').hidden=false;$('reader-comparison').innerHTML=[['A · saved',c.a],['B · current',c.b]].map(([label,v])=>'<div class="reader-comparison-cell"><span>'+label+'</span><b>'+v.percent.toFixed(3)+'%</b><span>'+escapeText(v.unit)+'</span></div>').join('')+'<div class="reader-comparison-warning">'+escapeText(c.reason)+'</div>';$('reader-comparison-status').textContent='A is saved. Change one of the four counting choices above; B follows it. Restore and the complete source-bound receipt are in the full comparison.';}
    else{$('reader-comparison').hidden=true;$('reader-comparison-status').textContent='Save this counting choice as A, then choose a different one above. This step is optional.';}
  }
  document.addEventListener('evidence-viewchange',event=>render(event.detail.state.cascade,event.detail.saved));
  $('reader-save').addEventListener('click',()=>{$('save-view').click();});
  $('reader-compare-open').addEventListener('click',()=>{$('open-workspace').click();});
  function reveal(id){const node=$(id);if(!node)return;let ancestor=node;while(ancestor){if(ancestor.tagName==='DETAILS')ancestor.open=true;ancestor=ancestor.parentElement;}if(node.tagName==='DETAILS'){node.querySelector('summary').focus();}else{const focus=node.querySelector('h2,h3,button,summary');if(focus){focus.tabIndex=-1;focus.focus();}}node.scrollIntoView({block:'start'});}
  document.querySelectorAll('[data-reveal]').forEach(link=>link.addEventListener('click',()=>reveal(link.dataset.reveal)));
  function revealHash(){if(location.hash.startsWith('#view='))return;let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}if(id&&$(id)&&$('technical-notebook').contains($(id)))reveal(id);}
  window.addEventListener('hashchange',revealHash);revealHash();render(selected(),null);
  const answers={
    attention:{title:"The observer's attention was not constant.",copy:'The transcript records changing attention and viewing conditions. Those anchors help describe observation opportunity. They do not give us a detection probability for each state or an independent witness count.'},
    camera:{title:'Not finding a flash does not prove the camera could have seen it.',copy:'In a bounded test on one 15-second, 900-frame transcoded clip, synthetic signals were not recovered at the lower tested digital amplitudes. Even the largest tested level yielded only 9 recoveries in 162 trials. Those are clip-native digital units, not astronomical brightness or a flight-camera calibration.'},
    clock:{title:'A timestamp can name the photograph, not the event.',copy:'The annotation photograph carries a 01:04 metadata time. That cannot tell us when the ledger was assembled or bound the timing of all five accepted events. The later video begins at 01:19:13. Their 913-second difference is metadata arithmetic, not a demonstrated gap covering every flash.'}
  };
  document.querySelectorAll('[data-flash-question]').forEach(button=>button.addEventListener('click',()=>{const id=button.dataset.flashQuestion,a=answers[id];$('reader-flash-heading').textContent=a.title;$('reader-flash-copy').textContent=a.copy;document.querySelectorAll('[data-flash-question]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));}));
}
