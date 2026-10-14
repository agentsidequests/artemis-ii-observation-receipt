const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');
const root=process.argv[2]||path.resolve(__dirname,'..');
const R=require(path.join(root,'presentation/reader.js'));
const e=JSON.parse(fs.readFileSync(path.join(root,'presentation/data.json')));
const expected={all_fields:[1553,7606],tagged_fields:[1553,3413],tagged_actions:[311,915],tagged_bytes:[409399017151,781104206358]};
for(const id of R.choices){const d=R.describe(id,e);assert.deepEqual([d.numerator,d.denominator],expected[id]);assert.equal(d.percent,100*d.numerator/d.denominator);assert(d.limit);assert(d.population);assert(d.pointer);assert.equal(d.unknown_percent>0,id==='all_fields');}
for(const a of R.choices)for(const b of R.choices){const c=R.comparison(a,b,e);assert.equal(c.numeric_difference,null);assert.equal(c.same_choice,a===b);if(a!==b)assert.match(c.reason,/Different populations or accounting units/);}
assert.throws(()=>R.describe('unknown',e),/Unknown/);
assert.equal(R.describe('all_fields',e).unknown_percent,100*4193/7606);
console.log(JSON.stringify({pass:true,reader_choices:4,comparisons:16,unknown_choice_rejected:true,values_bound_to_existing_excerpt:true}));
