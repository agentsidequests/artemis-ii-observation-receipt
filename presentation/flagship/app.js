'use strict';
// Teaching models are explicitly separate from the frozen scientific calculations.
const ArtemisFlagship = (() => {
  const modes=['explore','play','use','inspect'];
  const events=Object.freeze([ [3,2],[8,8],[13,4],[18,6],[23,1],[28,9],[33,5],[38,3],[43,8],[48,2],[53,7],[58,4] ].map(([time,signal])=>Object.freeze({time,signal})));
  function partition(boundary){
    if(!['file','capture','action'].includes(boundary))throw Error('Unknown demonstration split.');
    const files=[];
    for(const action of ['A','B'])for(const key of [1,2])for(const [i,format]of ['NEF','Raw TIFF','Processed TIFF'].entries()){
      const test=boundary==='file'?i===2:boundary==='capture'?key===2:action==='B';
      files.push({id:action+'.'+key+'.'+i,action,capture:action+'.'+key,format,partition:test?'test':'train'});
    }
    const train=files.filter(x=>x.partition==='train'),test=files.filter(x=>x.partition==='test');
    const captures=new Set(train.map(x=>x.capture)),actions=new Set(train.map(x=>x.action));
    let sameCapture=0,sameActionOnly=0,isolated=0;
    for(const file of test){if(captures.has(file.capture))sameCapture++;else if(actions.has(file.action))sameActionOnly++;else isolated++;}
    return {boundary,train,test,sameCapture,sameActionOnly,isolated,example:'invented',model_trained:false,accuracy:null,physical_independence:false};
  }
  function completion(k,e){
    if(!Number.isInteger(k)||k<0||k>4193)throw Error('Assumed field count must be an integer from 0 to 4,193.');
    const all=e.cascade.find(x=>x.id==='all_fields'),named=e.cascade.find(x=>x.id==='tagged_fields');
    if(!all||!named||all.numerator!==1553||all.denominator!==7606||named.numerator!==1553||named.denominator!==3413)throw Error('Unqualified field population.');
    return {k,recorded:all.numerator,total:all.denominator,unknown:4193,numerator:1553+k,percent:100*(1553+k)/7606,knownPercent:100*1553/7606,assumedPercent:100*k/7606,majority:1553+k>7606/2,source_edited:false,confidence_interval:false,content_validated:false};
  }
  function recorder(coverage,threshold){
    if(![0,20,40,60].includes(coverage)||![1,4,7,10].includes(threshold))throw Error('Unknown invented recorder setting.');
    const rows=events.map(e=>({...e,outcome:e.time>=coverage?'off':e.signal<threshold?'weak':'recorded'}));
    const counts=Object.fromEntries(['off','weak','recorded'].map(k=>[k,rows.filter(e=>e.outcome===k).length]));
    return {coverage,threshold,rows,counts,total:12,example:'invented',physical_calibration:false,rate_estimate:null};
  }
  function mode(id){if(!modes.includes(id))throw Error('Unknown experience section.');return id;}
  function snapshot(state){
    mode(state.mode);partition(state.split);
    if(!Number.isInteger(state.k)||state.k<0||state.k>4193)throw Error('Invalid lesson assumption.');
    recorder(state.coverage,state.threshold);
    return {schema:'artemis-teaching-settings-v1',edition:'v10',mode:state.mode,split:state.split,assumed_blank_sunset:state.k,invented_recorder:{coverage_seconds:state.coverage,arbitrary_signal_rule:state.threshold},scientific_result:false,source_edited:false,personal_data:false};
  }
  return {modes,partition,completion,recorder,mode,snapshot};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=ArtemisFlagship;
if(typeof document!=='undefined'&&document.getElementById('f-experience')){
  const F=ArtemisFlagship,el=id=>document.getElementById(id),fmt=x=>x.toLocaleString('en-US');
  const state={mode:'explore',split:'file',k:0,coverage:40,threshold:4};
  const panes=[...document.querySelectorAll('[data-f-pane]')];
  function displayMode(id){
    F.mode(id);state.mode=id;
    for(const pane of panes)pane.hidden=pane.dataset.fPane!==id;
    document.querySelectorAll('[data-f-nav]').forEach(link=>{if(link.dataset.fNav===id)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});
    el('f-current-section').textContent=id[0].toUpperCase()+id.slice(1);
    if(id==='inspect')el('technical-notebook').open=true;
  }
  function targetForHash(hash){
    if(hash.startsWith('#view='))return el('workspace');
    try{return el(decodeURIComponent(hash.slice(1)));}catch{return null;}
  }
  function route(hash,focus=false){
    const target=targetForHash(hash),pane=target?.closest('[data-f-pane]');
    if(pane){displayMode(pane.dataset.fPane);for(let p=target;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
      if(focus){const heading=target.matches('h1,h2,h3,summary,button')?target:target.querySelector('h1,h2,h3,summary,button');if(heading){if(!heading.matches('button,summary'))heading.tabIndex=-1;heading.focus({preventScroll:true});}target.scrollIntoView({block:'start'});}
      return true;
    }
    if(hash===''||hash==='#main'){displayMode('explore');return true;}
    return false;
  }
  // Reveal a section before any legacy focus or source-jump handler touches it.
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[href^="#"]');
    if(link){const hash=link.getAttribute('href');if(route(hash,false)&&F.modes.includes(hash.slice(1))){event.preventDefault();if(location.hash===hash)route(hash,true);else location.hash=hash;}}
    const control=event.target.closest('button');if(!control)return;
    if(['open-workspace','o-full-compare'].includes(control.id)){displayMode('inspect');location.hash='#workspace';}
    if(control.id==='go-sunset-counting'){displayMode('explore');location.hash='#sunset-counting';}
    if(control.id==='return-to-story'){event.preventDefault();event.stopImmediatePropagation();location.hash='#sunset-counting';route('#sunset-counting',true);}
  },true);
  window.addEventListener('hashchange',()=>route(location.hash,true));
  el('f-reset-lessons').addEventListener('click',()=>{state.split='file';state.k=0;state.coverage=40;state.threshold=4;el('f-unknown-k').value='0';el('f-coverage').value='40';el('f-threshold').value='4';renderSplit();renderCompletion();renderRecorder();el('f-reset-status').textContent='All three learning experiments reset. Your saved evidence view A is unchanged.';});
  function renderSplit(){
    const p=F.partition(state.split);
    document.querySelectorAll('[data-f-split]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.fSplit===state.split)));
    for(const [id,rows]of [['f-train-files',p.train],['f-test-files',p.test]]){
      const nodes=rows.map(file=>{const card=document.createElement('div');card.className='f-file f-family-'+file.action.toLowerCase();const icon=document.createElement('span');icon.className='f-file-image';icon.setAttribute('aria-hidden','true');icon.textContent=file.action==='A'?'◔':'◑';const name=document.createElement('b');name.textContent=file.capture;const format=document.createElement('small');format.textContent=file.format;card.append(icon,name,format);return card;});el(id).replaceChildren(...nodes);
    }
    el('f-split-result').textContent=state.split==='file'?p.sameCapture+' of '+p.test.length+' test files share a capture key with training.':state.split==='capture'?p.sameActionOnly+' of '+p.test.length+' test files still share a sequence with training.':p.isolated+' of '+p.test.length+' test files are separated at both declared layers.';
    el('f-split-why').textContent={file:'Different formats associated with the same capture key appear on both sides. A new filename alone does not test a new sequence.',capture:'No capture key crosses the boundary. But both captures from sequence A, and both from B, are split across practice and exam. The sequence relationship still crosses.',action:'All files from A are in practice; all files from B are in the exam. That removes these capture and sequence crossings. It does not certify independence or model performance.'}[state.split];
    el('f-split-takeaway').textContent={file:'Try keeping each capture together. Is that enough for the new-sequence question?',capture:'Now keep the whole sequence together. Watch what is removed, and what that still cannot prove.',action:'The question chooses the boundary. A new sequence is not automatically a new observing event.'}[state.split];
    el('f-split-capture-n').textContent=p.sameCapture;el('f-split-action-n').textContent=p.sameActionOnly;el('f-split-isolated-n').textContent=p.isolated;
  }
  document.querySelectorAll('[data-f-split]').forEach(b=>b.addEventListener('click',()=>{state.split=b.dataset.fSplit;renderSplit();}));
  function renderCompletion(){
    const c=F.completion(state.k,E);el('f-unknown-output').textContent=fmt(c.k);
    el('f-known-bar').style.width=c.knownPercent+'%';el('f-assumed-bar').style.width=c.assumedPercent+'%';
    el('f-completion-bar').setAttribute('aria-label','Hypothetical completed Sunset field share '+c.percent.toFixed(3)+' percent; '+fmt(c.recorded)+' recorded Sunset plus '+fmt(c.k)+' assumed from blanks, out of '+fmt(c.total)+'. Not a confidence interval.');
    el('f-completion-result').textContent=c.percent.toFixed(3)+'% under this completion.';
    el('f-completion-equation').textContent='('+fmt(c.recorded)+' + '+fmt(c.k)+') / '+fmt(c.total)+' × 100 = '+c.percent.toFixed(3)+'%';
    el('f-completion-why').textContent=(c.k===0?'No blank is assigned Sunset.':fmt(c.k)+' blank fields are assumed Sunset; '+fmt(c.unknown-c.k)+' are assumed other names.')+' '+(c.majority?'This hypothetical completion exceeds half of the fields.':'This hypothetical completion does not exceed half of the fields.')+' This is an assumption, not an image-content finding.';
  }
  el('f-unknown-k').addEventListener('input',()=>{state.k=Number(el('f-unknown-k').value);renderCompletion();});
  document.querySelectorAll('[data-f-unknown]').forEach(b=>b.addEventListener('click',()=>{state.k=Number(b.dataset.fUnknown);el('f-unknown-k').value=String(state.k);renderCompletion();}));
  function svg(tag,attrs,text){const node=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))node.setAttribute(k,String(v));if(text!==undefined)node.textContent=text;return node;}
  function renderRecorder(){
    const r=F.recorder(state.coverage,state.threshold),marks=el('f-recorder-marks'),nodes=[],x=t=>60+t*10,y=s=>210-s*17;
    nodes.push(svg('rect',{x:60,y:32,width:r.coverage*10,height:178,class:'f-on-time'}));
    for(const s of [0,5,10]){nodes.push(svg('line',{x1:60,x2:660,y1:y(s),y2:y(s),class:'f-grid-line'}),svg('text',{x:45,y:y(s)+4,'text-anchor':'end',class:'f-axis'},s));}
    nodes.push(svg('line',{x1:60,x2:660,y1:y(r.threshold),y2:y(r.threshold),class:'f-rule-line'}));
    for(const t of [0,20,40,60])nodes.push(svg('text',{x:x(t),y:233,'text-anchor':'middle',class:'f-axis'},t+' s'));
    nodes.push(svg('text',{x:60,y:19,class:'f-axis'},'Invented signal level'),svg('text',{x:660,y:255,'text-anchor':'end',class:'f-axis'},'Time in the invented minute'));
    for(const event of r.rows){const cx=x(event.time),cy=y(event.signal),title=event.time+' seconds, signal '+event.signal+': '+{off:'recorder off',weak:'below the rule',recorded:'recorded'}[event.outcome];let point;
      if(event.outcome==='recorded')point=svg('circle',{cx,cy,r:7,class:'f-point recorded'});
      else if(event.outcome==='weak')point=svg('path',{d:'M'+cx+' '+(cy-8)+'l8 14h-16Z',class:'f-point weak'});
      else point=svg('path',{d:'M'+(cx-6)+' '+(cy-6)+'l12 12m0-12l-12 12',class:'f-point off'});
      point.appendChild(svg('title',{},title));nodes.push(point);
    }
    marks.replaceChildren(...nodes);el('f-recorder-result').textContent=r.counts.recorded+' recorded. '+(12-r.counts.recorded)+' leave no detection in this toy.';
    el('f-recorder-why').textContent=r.counts.off+' occur while the recorder is off; '+r.counts.weak+' are inside its on-time but below its invented signal rule. The world still contains the same 12 signals. No physical rate or Artemis sensitivity is calculated.';
    el('f-recorder-chart-desc').textContent=el('f-recorder-why').textContent+' The shaded recording interval ends at '+r.coverage+' seconds; the dashed signal rule is '+r.threshold+' arbitrary units.';
    el('f-recorder-table').replaceChildren(...r.rows.map(row=>{const tr=document.createElement('tr');for(const value of [row.time,row.signal,{off:'Recorder off',weak:'Below the signal rule',recorded:'Recorded'}[row.outcome]]){const td=document.createElement('td');td.textContent=value;tr.appendChild(td);}return tr;}));
  }
  for(const id of ['f-coverage','f-threshold'])el(id).addEventListener('change',()=>{state.coverage=Number(el('f-coverage').value);state.threshold=Number(el('f-threshold').value);renderRecorder();});
  el('f-recorder-reset').addEventListener('click',()=>{state.coverage=40;state.threshold=4;el('f-coverage').value='40';el('f-threshold').value='4';renderRecorder();});
  function download(kind){const evidence=kind==='evidence',value=evidence?JSON.stringify(E,null,2):JSON.stringify(F.snapshot(state),null,2);el('f-download-fallback').value=value;const url=URL.createObjectURL(new Blob([value+'\n'],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=evidence?'artemis-evidence-excerpt-v10.json':'artemis-teaching-settings-v10.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1500);el('f-download-status').textContent='Download requested for '+(evidence?'the frozen evidence excerpt':'the current teaching settings')+'. If your browser blocks it, expand the copyable JSON below. No data was sent.';}
  el('f-download-evidence').addEventListener('click',()=>download('evidence'));el('f-download-lessons').addEventListener('click',()=>download('lessons'));
  renderSplit();renderCompletion();renderRecorder();el('f-download-fallback').value=JSON.stringify(F.snapshot(state),null,2);
  route(location.hash,false)||displayMode('explore');
  document.body.classList.add('f-ready');
}
