'use strict';
// Presentation-only models. No scientific input or original denominator is edited.
const ArtemisObservatory = (() => {
  const levels = [
    {key:'scheduled_events',name:'scheduled Sunset',kicker:'The plan',explanation:'One Sunset entry in the observing plan. Changing the archive level does not add another scheduled event.',equation:'The event count stays 1.'},
    {key:'actions',name:'reconstructed camera sequences',kicker:'Groups in our reconstruction',explanation:'The connected observing context contains 286 sequences reconstructed from camera metadata. They are not 286 separate sunsets.',equation:'286 reconstructed actions in this declared context.'},
    {key:'exposures',name:'native capture keys',kicker:'The bracketed entries',explanation:'Each reconstructed sequence in this context has five entries at different exposure settings. A capture key is an archive identifier, not proof of physical uniqueness.',equation:'286 actions × 5 keys = 1,430 native keys.'},
    {key:'products',name:'related archive files',kicker:'The stored representations',explanation:'Each key has three stored forms: source NEF, raw TIFF and processed TIFF. Useful related files, not another scheduled Sunset.',equation:'1,430 keys × 3 representations = 4,290 products.'}
  ];
  function level(index,e){
    if(!Number.isInteger(index)||index<0||index>3)throw Error('Unknown archive level.');
    const row=levels[index];
    const count=index===0?e.fanout.scheduled_events:e.fanout.context[row.key];
    if(![1,286,1430,4290].includes(count)||count!==[1,286,1430,4290][index])throw Error('Unqualified connected-context counts.');
    return {...row,index,count,scheduled_events:e.fanout.scheduled_events,physical_census:false};
  }
  function cloud(count){
    if(![1,286,1430,4290].includes(count))throw Error('Unknown aggregate field size.');
    if(count===1)return [{cx:300,cy:220,r:48}];
    const radius=count===286?2.6:count===1430?1.6:1.04;
    return Array.from({length:count},(_,i)=>{const d=184*Math.sqrt((i+.5)/count),a=i*Math.PI*(3-Math.sqrt(5));return {cx:Number((300+d*Math.cos(a)).toFixed(3)),cy:Number((220+d*Math.sin(a)).toFixed(3)),r:radius};});
  }
  function photo(zoom,x,y){
    if(![1,1.75,2.5].includes(zoom)||![x,y].every(v=>Number.isFinite(v)&&v>=0&&v<=100))throw Error('Invalid photograph view.');
    return {zoom,x,y,transform:'translate('+((50-x)*(zoom-1))+'%, '+((50-y)*(zoom-1))+'%) scale('+zoom+')',position_enabled:zoom!==1,new_pixels:false};
  }
  function ranking(unit,e){
    if(!['actions','products'].includes(unit))throw Error('Unknown ranking unit.');
    const rows=e.rank_comparison.windows;
    for(const row of rows)if(row.actions*row.keys_per_action*row.representations_per_key!==row.products)throw Error('Unqualified ranking relation.');
    const maximum=Math.max(...rows.map(r=>r[unit]));
    return {unit,maximum,rows:rows.map(r=>({...r,value:r[unit],width:100*r[unit]/maximum})),winner:rows.reduce((a,b)=>a[unit]>b[unit]?a:b).name,source:e.rank_comparison.source,pointer:e.rank_comparison.pointer,scientific_importance:false};
  }
  const claims={
    pair:'Supported at this scope: JPL confirmed this one pair. The other 23 candidate pairs remain unconfirmed.',
    all:'Not supported: the reply resolves one pair, not all 24 candidates. Similar metadata in the other 23 pairs still requires its own evidence.',
    subtract:'Not supported: only art002e015991 is in the counted cohort. Its confirmed counterpart is outside it. We preserve the original totals instead of subtracting one.'
  };
  const flashes={
    attention:{status:'Documented context, unknown probability',title:'Attention changed during the observation.',text:'The transcript records changing attention and viewing conditions. It helps describe observation opportunity, but it does not tell us the chance of detecting a flash in each state or supply an independent witness count.'},
    camera:{status:'A bounded digital test, not flight calibration',title:'A camera null needs a sensitivity check.',text:'In one 15-second, 900-frame transcoded clip, synthetic signals at the lower tested amplitudes were not recovered. Even the largest tested level yielded 9 recoveries in 162 trials. Those are uncalibrated clip-native digital units, not astronomical brightness or a human detection threshold.'},
    clock:{status:'A photo epoch, not an all-event clock',title:'What was actually dated?',text:'The annotation photograph has a 01:04 UTC metadata time on 7 April 2026. That cannot date the ledger’s construction or bound all five accepted events. The later video starts at 01:19:13 UTC. The 913-second difference is metadata arithmetic, not established all-event coverage.'}
  };
  function claim(id){if(!Object.hasOwn(claims,id))throw Error('Unknown JPL claim.');return claims[id];}
  function flash(id){if(!Object.hasOwn(flashes,id))throw Error('Unknown flash question.');return {...flashes[id]};}
  return {level,cloud,photo,ranking,claim,flash};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=ArtemisObservatory;
if(typeof document!=='undefined'&&document.getElementById('observatory')){
  const O=ArtemisObservatory,R=ArtemisReader;
  const byId=id=>document.getElementById(id),format=value=>value.toLocaleString('en-US');
  let currentLevel=0,lastSaved=null;
  function setPressed(selector,attribute,value){document.querySelectorAll(selector).forEach(b=>b.setAttribute('aria-pressed',String(b.getAttribute(attribute)===String(value))));}
  function renderLevel(index){
    const row=O.level(index,E);currentLevel=index;
    setPressed('[data-level]','data-level',index);
    byId('o-level-kicker').textContent=row.kicker;byId('o-level-count').textContent=format(row.count);byId('o-level-name').textContent=row.name;byId('o-level-explanation').textContent=row.explanation;byId('o-level-equation').textContent=row.equation;
    byId('o-field-title').textContent=format(row.count)+' '+row.name+' in one connected context';
    const fragment=document.createDocumentFragment();
    for(const point of O.cloud(row.count)){const circle=document.createElementNS('http://www.w3.org/2000/svg','circle');for(const [k,v]of Object.entries(point))circle.setAttribute(k,String(v));fragment.appendChild(circle);}
    byId('o-record-marks').replaceChildren(fragment);
    byId('o-next-level').textContent=['Unfold to camera sequences →','Unfold to capture keys →','Unfold to archive files →','Return to one scheduled Sunset ↺'][index];
  }
  document.querySelectorAll('[data-level]').forEach(b=>b.addEventListener('click',()=>renderLevel(Number(b.dataset.level))));
  byId('o-next-level').addEventListener('click',()=>renderLevel((currentLevel+1)%4));
  const shortLabels={all_fields:'All entries, blanks included',tagged_fields:'Only named entries',tagged_actions:'Named reconstructed actions',tagged_bytes:'Combined named file bytes'};
  function renderCounts(id,saved){
    const row=R.describe(id,E);lastSaved=saved;
    byId('o-count-title').textContent=row.title;byId('o-count-explanation').textContent=row.description;byId('o-count-equation').textContent=row.short;byId('o-count-limit').textContent=row.limit;
    const fragment=document.createDocumentFragment();
    for(const key of R.choices){
      const d=R.describe(key,E),container=document.createElement('div');container.className='o-share-row'+(id===key?' is-current':'');container.dataset.accountingView=key;
      const label=document.createElement('div');label.className='o-share-label';
      const name=document.createElement('span');name.textContent=shortLabels[key]+(id===key?' · selected':'');
      const value=document.createElement('b');value.textContent=d.percent.toFixed(1)+'%';label.append(name,value);
      const track=document.createElement('div');track.className='o-share-track';track.setAttribute('role','img');track.setAttribute('aria-label',d.percent.toFixed(3)+' percent recorded Sunset share; '+format(d.numerator)+' of '+format(d.denominator)+'. '+d.unit+'. '+(d.unknown_percent?'Blank-name share '+d.unknown_percent.toFixed(3)+' percent remains unknown.':'Blanks are outside this selection.'));
      const sunset=document.createElement('span');sunset.className='o-share-sunset';sunset.style.width=d.percent+'%';
      const unknown=document.createElement('span');unknown.className='o-share-unknown';unknown.style.width=d.unknown_percent+'%';track.append(sunset,unknown);container.append(label,track);fragment.appendChild(container);
      document.querySelector('[data-share-value="'+key+'"]').textContent=d.percent.toFixed(1)+'%';
    }
    byId('o-all-shares').replaceChildren(fragment);
    byId('o-restore-a').disabled=!saved;
    if(saved){
      const c=R.comparison(saved.cascade,id,E),comparison=byId('o-comparison');comparison.hidden=false;comparison.replaceChildren();
      for(const [name,d]of [['A · saved counting choice',c.a],['B · current counting choice',c.b]]){const cell=document.createElement('div');cell.className='o-compare-cell';const label=document.createElement('span');label.textContent=name;const value=document.createElement('b');value.textContent=d.percent.toFixed(3)+'%';const unit=document.createElement('span');unit.textContent=d.unit;const ratio=document.createElement('span');ratio.textContent=format(d.numerator)+' / '+format(d.denominator);cell.append(label,value,unit,ratio);comparison.append(cell);}
      const caution=document.createElement('div');caution.className='o-compare-caution';caution.textContent=c.reason;comparison.append(caution);
      byId('o-compare-status').textContent='A is saved. Choose another counting rule above to change B. Restore A returns all saved technical controls; the photograph and unfolding scene are separate explanatory views.';
    }else{byId('o-comparison').hidden=true;byId('o-compare-status').textContent='Save this counting choice as A, then choose another rule above. No setup is needed to explore.';}
  }
  function renderRankingLab(unit){
    const r=O.ranking(unit,E),label=unit==='actions'?'reconstructed sequences':'archive files';
    byId('o-rank-scale').textContent='Scale: 0–'+format(r.maximum)+' '+label;
    byId('o-rank-bars').setAttribute('aria-label',r.rows.map(row=>row.name+': '+row.value+' '+label).join('; ')+'. Archive prominence, not scientific importance.');
    const fragment=document.createDocumentFragment();
    for(const row of r.rows){const group=document.createElement('div');group.className='o-rank-row';const heading=document.createElement('p');heading.textContent=row.name+' · '+format(row.value)+' '+label;const track=document.createElement('div');track.className='o-rank-track';const bar=document.createElement('span');bar.style.width=row.width+'%';track.append(bar);group.append(heading,track);fragment.append(group);}
    byId('o-rank-bars').replaceChildren(fragment);
    byId('o-rank-winner').textContent=r.winner+' has more '+label+'.';
    byId('o-rank-explanation').textContent=unit==='actions'?'76 is larger than 60. Each reconstructed sequence gets one count. Switch to files and the different bracket lengths change the ranking.':'Earthset contributes 900 files; Guided Discussion contributes 684. The ranking reverses. No observing window, source record or scientific importance changed.';
  }
  document.addEventListener('evidence-viewchange',event=>{renderCounts(event.detail.state.cascade,event.detail.saved);renderRankingLab(event.detail.state.rank);});
  byId('o-save-a').addEventListener('click',()=>byId('save-view').click());
  byId('o-restore-a').addEventListener('click',()=>{if(lastSaved)byId('restore-view').click();});
  byId('o-full-compare').addEventListener('click',()=>byId('open-workspace').click());
  function renderPhoto(){
    const p=O.photo(Number(byId('o-photo-zoom').value),Number(byId('o-photo-x').value),Number(byId('o-photo-y').value));
    byId('o-lunar-image').style.transform=p.transform;
    byId('o-photo-x').disabled=!p.position_enabled;byId('o-photo-y').disabled=!p.position_enabled;
    byId('o-photo-x-value').textContent=p.x+'%';byId('o-photo-y-value').textContent=p.y+'%';
    byId('o-photo-status').textContent=p.position_enabled?'Display zoom '+p.zoom+'×. Position controls move within this same stored photograph. No pixels, measurements or coordinates are added.':'Choose a closer view to activate the position controls. Display zoom adds no pixels.';
  }
  byId('o-photo-zoom').addEventListener('change',renderPhoto);
  ['o-photo-x','o-photo-y'].forEach(id=>byId(id).addEventListener('input',renderPhoto));
  byId('o-photo-reset').addEventListener('click',()=>{byId('o-photo-zoom').value='1';byId('o-photo-x').value='50';byId('o-photo-y').value='50';renderPhoto();});
  document.querySelectorAll('[data-o-claim]').forEach(b=>b.addEventListener('click',()=>{setPressed('[data-o-claim]','data-o-claim',b.dataset.oClaim);byId('o-claim-answer').textContent=O.claim(b.dataset.oClaim);}));
  document.querySelectorAll('[data-flash]').forEach(b=>b.addEventListener('click',()=>{const row=O.flash(b.dataset.flash);setPressed('[data-flash]','data-flash',b.dataset.flash);byId('o-flash-status').textContent=row.status;byId('o-flash-answer-title').textContent=row.title;byId('o-flash-answer').textContent=row.text;}));
  function reveal(id){
    const target=byId(id);if(!target)return;
    for(let node=target;node;node=node.parentElement)if(node.tagName==='DETAILS')node.open=true;
    const focus=target.tagName==='DETAILS'?target.querySelector('summary'):target.querySelector('h2,h3,button,summary');
    if(focus){if(!['BUTTON','SUMMARY'].includes(focus.tagName))focus.tabIndex=-1;focus.focus();}
    target.scrollIntoView({block:'start'});
  }
  document.querySelectorAll('[data-reveal]').forEach(link=>link.addEventListener('click',()=>reveal(link.dataset.reveal)));
  function revealHash(){if(location.hash.startsWith('#view='))return;let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}const target=byId(id);if(target&&byId('technical-notebook').contains(target))reveal(id);}
  window.addEventListener('hashchange',revealHash);revealHash();
  const media=window.matchMedia('(prefers-reduced-motion: reduce)'),motion=byId('o-motion');
  let requestedReduced=false;
  function renderMotion(){const reduced=media.matches||requestedReduced;document.body.classList.toggle('o-no-motion',reduced);motion.setAttribute('aria-pressed',String(reduced));motion.textContent=media.matches?'Reduced motion: system':requestedReduced?'Reduced motion: on':'Reduce motion';motion.disabled=media.matches;}
  motion.addEventListener('click',()=>{requestedReduced=!requestedReduced;renderMotion();});
  media.addEventListener('change',renderMotion);renderMotion();
  renderLevel(0);renderPhoto();
  const receipt=JSON.parse(byId('view-receipt').value);renderCounts(receipt.state.cascade,receipt.saved_comparison);renderRankingLab(receipt.state.rank);
}
