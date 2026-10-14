import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),out=path.join(root,'site');
const read=f=>fs.readFileSync(path.join(out,f)),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(read('release.json'));
test('deployment has no installation, runtime functions or paid service dependency',()=>{
  const config=JSON.parse(fs.readFileSync(path.join(root,'vercel.json')));
  assert.equal(config.framework,null);assert.equal(config.installCommand,'');assert.equal(config.outputDirectory,'site');
  assert.equal(config.buildCommand,'node tools/build_site.mjs');assert(!config.functions&&!config.crons);
  const headers=Object.fromEntries(config.headers[0].headers.map(x=>[x.key,x.value]));
  assert.match(headers['Content-Security-Policy'],/connect-src 'none'/);
  assert.match(headers['Content-Security-Policy'],/frame-ancestors 'none'/);
  assert.equal(headers['X-Content-Type-Options'],'nosniff');
});
test('release status retains independent prototype and scientific ceilings',()=>{
  const html=read('index.html').toString();
  assert.match(html,/Independent research prototype v1\.0/);assert.match(html,/Not specialist-approved/);
  assert(!html.includes('Not published or specialist-approved'));
  for(const id of ['explore','play','use','f-inspect','technical-notebook','sunset-counting'])assert(html.includes('id="'+id+'"'));
  assert.equal(manifest.scientific_claim_change,false);assert.equal(manifest.model_trained,false);
  assert.match(html,/hypothetical/i);assert.match(html,/not.*calibrated/i);
});
test('source download has a real named release destination, no nested phantom ZIP',()=>{
  const html=read('index.html').toString();
  assert.match(html,/https:\/\/github\.com\/agentsidequests\/artemis-ii-observation-receipt\/releases\/tag\/v1\.0\.0/);
  assert(!/href="[^"\n]*\.zip"/.test(html));
});
test('every published reading copy leaves obsolete local-candidate status behind',()=>{
  for(const row of manifest.files.filter(x=>x.path.endsWith('.html'))){
    assert(!/local publication candidate/i.test(read(row.path).toString()),row.path);
  }
});
test('every emitted file matches its digest, no unmanifested files',()=>{
  const files=[];const walk=p=>{for(const e of fs.readdirSync(p,{withFileTypes:true})){const f=path.join(p,e.name);if(e.isDirectory())walk(f);else files.push(path.relative(out,f).replaceAll('\\','/'));}};walk(out);
  assert.deepEqual(files.sort(),[...manifest.files.map(x=>x.path),'release.json'].sort());
  for(const row of manifest.files){const b=read(row.path);assert.equal(b.length,row.bytes,row.path);assert.equal(sha(b),row.sha256,row.path);}
});
test('all local HTML navigation and image assets exist inside the publish folder',()=>{
  for(const row of manifest.files.filter(x=>x.path.endsWith('.html'))){
    const html=read(row.path).toString().replace(/<script\b[^>]*>[\s\S]*?<\/script>/g,'');
    for(const m of html.matchAll(/\b(?:href|src)="([^"#][^"]*)"/g)){
      if(/^(https?:|data:|mailto:)/.test(m[1]))continue;
      const target=decodeURIComponent(m[1].split('#')[0]);const resolved=target==='/'?'index.html':target.replace(/^\//,'');
      assert(!resolved.includes('..'));assert(fs.existsSync(path.join(out,resolved)),row.path+' -> '+target);
    }
  }
});
test('separate image assets retain exact bytes from frozen inline originals',()=>{
  const expected=new Map();
  for(const row of manifest.sources){const original=fs.readFileSync(path.join(root,row.path));assert.equal(sha(original),row.sha256);
    for(const m of original.toString().matchAll(/data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)/g)){const b=Buffer.from(m[2],'base64');expected.set(sha(b),b);}}
  for(const row of manifest.files.filter(x=>x.path.startsWith('assets/'))){assert(expected.has(row.sha256));assert(read(row.path).equals(expected.get(row.sha256)));}
  assert(read('index.html').length<1000000,'Initial HTML should not contain the large inline photograph');
  assert(!read('index.html').toString().includes('data:image/png;base64,'));
});
test('repeated builds produce identical manifest and outputs',()=>{
  const before=read('release.json');const result=spawnSync(process.execPath,[path.join(root,'tools/build_site.mjs')],{encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);assert(read('release.json').equals(before));
  for(const row of manifest.files)assert.equal(sha(read(row.path)),row.sha256);
});
