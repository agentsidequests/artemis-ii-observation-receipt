// Deterministic view-state checks in a minimal DOM double, not human or rendered acceptance.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(process.argv[2]||path.join(__dirname,'..'));
const data=JSON.parse(fs.readFileSync(path.join(root,'presentation/data.json'),'utf8'));
const elements=new Map();
function node(id){if(!elements.has(id))elements.set(id,{id,textContent:'',innerHTML:'',style:{},attrs:{},hidden:false,value:'',listeners:{},dataset:{},setAttribute(k,v){this.attrs[k]=v;},getAttribute(k){return this.attrs[k];},addEventListener(k,fn){this.listeners[k]=fn;},add(option){this.options??=[];this.options.push(option);},focus(){this.focused=true;}});return elements.get(id);}
node('evidence-data').textContent=JSON.stringify(data);
const document={getElementById:node,querySelectorAll(){return [];},createElement(){return {click(){}};}};
const realm={document,Option:function(label,value){this.label=label;this.value=value;},console,URL:{createObjectURL(){return 'blob:test';},revokeObjectURL(){}},Blob:function(){},setTimeout(fn){fn();}};
vm.createContext(realm);vm.runInContext(fs.readFileSync(path.join(root,'presentation/story.js'),'utf8'),realm);
const call=script=>vm.runInContext(script,realm);
let states=0;
for(const d of data.decisions){call('renderDecision('+JSON.stringify(d.id)+')');assert(node('decision-panel').innerHTML.includes(d.title));assert(node('decision-panel').innerHTML.includes('Next defensible step'));states++;}
for(const mode of ['actions','products']){call('renderRanking('+JSON.stringify(mode)+')');assert.equal(node('rank-winner').textContent,mode==='actions'?'Guided Discussion':'Earthset');assert(node('rank-bars').attrs['aria-label'].includes('not scientific importance'));states++;}
for(const mode of ['original','conditional']){call('renderTrace('+JSON.stringify(mode)+')');const r=data.audit_trail[mode];assert(node('trace-equation').textContent.startsWith(r.test_products.toLocaleString('en-US')));assert.deepEqual(JSON.parse(node('trace-excerpt').textContent),r);assert(node('trace-order').innerHTML.includes('not adopted'));states++;}
for(const context of ['context','planned'])for(const unit of ['products','exposures','actions']){
  call('context='+JSON.stringify(context)+';fanunit='+JSON.stringify(unit)+';renderFanout()');assert.equal(node('fan-count').textContent,data.fanout[context][unit].toLocaleString('en-US'));states++;
}
for(const mode of ['capture','action']){
  call('renderRelationship('+JSON.stringify(mode)+')');assert.equal(node('linked-count').textContent,mode==='capture'?'4,307':'4,511');assert.equal(node('unlinked-count').textContent,mode==='capture'?'204':'0');states++;
}
for(const item of data.cascade){call('renderCascade('+JSON.stringify(item.id)+')');assert.equal(node('cascade-share').textContent,(100*item.numerator/item.denominator).toFixed(3)+'%');assert(node('cascade-population').textContent.includes(item.population));states++;}
for(const b of data.robustness.scenarios){
  call('renderRobustness('+b.reassignment_budget+')');assert.equal(node('robust-range').textContent,(100*b.lower.numerator/b.total_weight).toFixed(6)+'%–'+(100*b.upper.numerator/b.total_weight).toFixed(6)+'%');assert(node('robust-exact').textContent.includes(b.total_weight.toLocaleString('en-US')));assert(node('robust-outcome').textContent.includes(b.reassignment_budget===48?'not guaranteed':'guaranteed'));states++;
}
for(const mode of ['raw','fractional','collapsed']){call('renderConcentration('+JSON.stringify(mode)+')');assert(node('concentration-bars').attrs['aria-label'].includes('Not effective sample size'));states++;}
for(let index=0;index<data.attention.timeline.length;index++){call('renderAttention('+index+')');assert.equal(node('attention-quote').textContent,data.attention.timeline[index].source_text);states++;}
for(const point of data.recovery.curve){call('renderRecovery('+point.requested_integrated_dn_per_frame+')');assert(node('recovery-count').textContent.startsWith(point.recovered+' / '+point.trials));assert(node('recovery-percent').innerHTML.startsWith((100*point.recovered/point.trials).toFixed(1)+'%'));states++;}
for(const mode of ['relationship','selection','weighting','detection']){call('renderClaim('+JSON.stringify(mode)+')');assert(node('claim-panel').innerHTML.includes('What remains open'));assert(node('claim-panel').innerHTML.includes('Exact source locator'));states++;}
let rejected=0;
for(const statement of ['renderDecision("approved")','renderRanking("scientific_value")','renderTrace("physical")','renderRelationship("physical")','renderCascade("all_content")','renderRobustness(49)','renderRobustness(-1)','renderConcentration("independent")','renderAttention(-1)','renderAttention(12)','renderRecovery(17000)','renderClaim("confirmed")','sourceCard("missing","/")']){assert.throws(()=>call(statement));rejected++;}
const witness=data.robustness.witnesses[0];node('robust-witness').listeners.click({target:{closest(){return {dataset:{witness:witness.id}};}}});assert(node('witness-source').focused);assert(node('witness-source').innerHTML.includes(witness.products.data_raw.id));assert(node('witness-source').innerHTML.includes(String(witness.products.data_source.row)));
assert(node('robust-witness').innerHTML.includes(data.robustness.witnesses[47].id));
assert.equal(data.clock.all_event_coverage,'UNESTABLISHED');assert.equal(data.clock.gap_seconds,913);
assert(node('steward-panel').innerHTML.includes('art002e009301'));assert(node('steward-panel').innerHTML.includes('art002e015991'));assert(node('steward-panel').innerHTML.includes('019A0860.NEF'));assert.equal(JSON.parse(node('steward-excerpt').textContent).local_byte_identity_verified,false);assert(node('steward-panel').innerHTML.includes('Only <code>art002e015991</code>'));
console.log(JSON.stringify({pass:true,view_states:states,rejected_modes:rejected,witness_source_focus:true,steward_statement_scope:true,evidence_layer:'deterministic DOM-double logic, not actual-surface or human evidence'}));
