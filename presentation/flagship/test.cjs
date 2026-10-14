'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(process.argv[2]||path.join(__dirname,'../..')),F=require(path.join(root,'presentation/flagship/app.js')),E=JSON.parse(fs.readFileSync(path.join(root,'presentation/data.json')));
let cases=0,negatives=0;
for(const boundary of ['file','capture','action']){
  const p=F.partition(boundary);assert.equal(p.train.length+p.test.length,12);assert.equal(new Set([...p.train,...p.test].map(x=>x.id)).size,12);
  const trainCaptures=new Set(p.train.map(x=>x.capture)),trainActions=new Set(p.train.map(x=>x.action));
  const expected=p.test.reduce((v,x)=>{v[trainCaptures.has(x.capture)?0:trainActions.has(x.action)?1:2]++;return v;},[0,0,0]);
  assert.deepEqual([p.sameCapture,p.sameActionOnly,p.isolated],expected);
  assert.deepEqual(expected,{file:[4,0,0],capture:[0,6,0],action:[0,0,6]}[boundary]);
  assert.equal(p.model_trained,false);assert.equal(p.accuracy,null);assert.equal(p.physical_independence,false);cases++;
}
const frozen=JSON.stringify(E);let previous=-Infinity;
for(let k=0;k<=4193;k++){
  const c=F.completion(k,E);assert.equal(c.total,7606);assert.equal(c.numerator,1553+k);assert.equal(c.percent,100*(1553+k)/7606);assert(c.percent>previous);previous=c.percent;
  assert.equal(c.majority,k>=2251);assert.equal(c.source_edited,false);assert.equal(c.confidence_interval,false);assert.equal(c.content_validated,false);cases++;
}
assert.equal(JSON.stringify(E),frozen);assert.equal(F.completion(0,E).percent.toFixed(3),'20.418');assert.equal(F.completion(4193,E).percent.toFixed(3),'75.546');
for(const coverage of [0,20,40,60])for(const threshold of [1,4,7,10]){
  const r=F.recorder(coverage,threshold);assert.equal(r.total,12);assert.equal(r.counts.off+r.counts.weak+r.counts.recorded,12);assert.equal(r.rows.length,12);
  for(const e of r.rows)assert.equal(e.outcome,e.time>=coverage?'off':e.signal<threshold?'weak':'recorded');
  assert.equal(r.physical_calibration,false);assert.equal(r.rate_estimate,null);assert.equal(r.example,'invented');cases++;
}
assert.deepEqual(F.recorder(40,4).counts,{off:4,weak:3,recorded:5});assert.equal(F.recorder(60,1).counts.recorded,12);assert.equal(F.recorder(60,10).counts.recorded,0);
for(const m of F.modes){assert.equal(F.mode(m),m);assert.equal(F.snapshot({mode:m,split:'action',k:2251,coverage:60,threshold:4}).scientific_result,false);cases++;}
const bad=structuredClone(E);bad.cascade.find(x=>x.id==='all_fields').denominator++;
for(const fn of [()=>F.partition('constructor'),()=>F.partition('new_event'),()=>F.mode('constructor'),()=>F.completion(-1,E),()=>F.completion(4194,E),()=>F.completion(.5,E),()=>F.completion(NaN,E),()=>F.completion('1',E),()=>F.completion(0,bad),()=>F.recorder(30,4),()=>F.recorder(60,2),()=>F.recorder('60',4),()=>F.snapshot({mode:'play',split:'file',k:Infinity,coverage:60,threshold:4})]){assert.throws(fn);negatives++;}
console.log(JSON.stringify({pass:true,cases,negatives,model_trained:false,new_science:false}));
