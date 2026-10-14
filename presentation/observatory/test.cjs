'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(process.argv[2]||path.join(__dirname,'../..'));
const O=require(path.join(root,'presentation/observatory/app.js'));
const R=require(path.join(root,'presentation/reader.js'));
const E=JSON.parse(fs.readFileSync(path.join(root,'presentation/data.json')));
let states=0,negatives=0;
for(let i=0;i<4;i++){
  const row=O.level(i,E),points=O.cloud(row.count);assert.equal(row.count,[1,286,1430,4290][i]);assert.equal(row.scheduled_events,1);assert.equal(row.physical_census,false);assert.equal(points.length,row.count);
  // SVG names matter: x/y silently put every circle at the origin in a browser.
  const seen=new Set();
  for(const p of points){assert.deepEqual(Object.keys(p).sort(),['cx','cy','r']);assert(Number.isFinite(p.cx)&&p.cx>=110&&p.cx<=490);assert(Number.isFinite(p.cy)&&p.cy>=30&&p.cy<=410);assert(p.r>0);seen.add(p.cx+','+p.cy);}
  assert.equal(seen.size,points.length);states++;
}
const bad=structuredClone(E);bad.fanout.context.products++;
for(const f of [()=>O.level(-1,E),()=>O.level(4,E),()=>O.level('1',E),()=>O.level(3,bad),()=>O.cloud(42),()=>O.cloud(Infinity)]){assert.throws(f);negatives++;}
for(const zoom of [1,1.75,2.5])for(const x of [0,50,100])for(const y of [0,50,100]){const p=O.photo(zoom,x,y);assert.equal(p.new_pixels,false);assert.equal(p.position_enabled,zoom!==1);assert(p.transform.startsWith('translate(')&&p.transform.endsWith('scale('+zoom+')'));states++;}
assert.equal(O.photo(1,100,0).transform,'translate(0%, 0%) scale(1)');
assert.equal(O.photo(2.5,0,100).transform,'translate(75%, -75%) scale(2.5)');
for(const values of [[0,50,50],[3,50,50],[1.75,-1,50],[1.75,50,101],[1.75,NaN,50],[1.75,50,Infinity]]){assert.throws(()=>O.photo(...values));negatives++;}
for(const unit of ['actions','products']){const r=O.ranking(unit,E);assert.equal(r.winner,unit==='actions'?'Guided Discussion':'Earthset');assert.equal(r.scientific_importance,false);assert.equal(r.maximum,unit==='actions'?76:900);assert.equal(r.rows.length,2);assert(r.rows.every(x=>x.width>0&&x.width<=100));states++;}
const wrongRank=structuredClone(E);wrongRank.rank_comparison.windows[0].products++;
assert.throws(()=>O.ranking('bytes',E));assert.throws(()=>O.ranking('products',wrongRank));negatives+=2;
for(const id of ['pair','all','subtract']){assert.equal(typeof O.claim(id),'string');states++;}
assert.match(O.claim('all'),/Not supported/);assert.match(O.claim('subtract'),/outside it/);
for(const id of ['attention','camera','clock']){const f=O.flash(id);assert(f.status&&f.title&&f.text);states++;}
assert.match(O.flash('clock').text,/cannot date/);assert.match(O.flash('camera').text,/uncalibrated/);
for(const id of ['constructor','__proto__','missing']){assert.throws(()=>O.claim(id));assert.throws(()=>O.flash(id));negatives+=2;}
for(const a of R.choices)for(const b of R.choices){assert.equal(R.comparison(a,b,E).numeric_difference,null);states++;}
console.log(JSON.stringify({pass:true,states,negatives,svg_coordinate_contract:true,physical_census:false,new_science:false}));
