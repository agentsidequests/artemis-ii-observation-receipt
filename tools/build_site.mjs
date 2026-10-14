// A deployment projection over frozen, tested reading copies. No packages or network.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'site');
const version='1.0.0', repo='https://github.com/agentsidequests/artemis-ii-observation-receipt';
const primary='Artemis-II-Interactive-Science-v10-2026-10-14.html';
const seed=[primary,'Artemis-II-Essay-2026-10-13.html','Artemis-II-Specialist-Review-2026-10-13.html',
  'Observation-Receipt-Identity-Confirmed-2026-10-13.html','Observation-Receipt-Robustness-2026-10-13.html',
  'Artemis-II-Identity-Sensitivity-Viewer-2026-10-12.html','Artemis-II-Public-Candidate-Flash-Demo-2026-10-12.html'];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=name=>fs.readFileSync(path.join(root,name));
const release=JSON.parse(read('release/v1.0.0.json'));
assert.equal(release.version,version);
assert.equal(release.prototype_source_sha256,sha(read(primary)),'Frozen flagship drift');
const emitted=new Map(), sources=[], assets=new Map();
const emit=(name,bytes)=>{
  assert(!name.startsWith('/')&&!name.split('/').includes('..'),'Unsafe output path');
  const payload=Buffer.from(bytes);
  if(emitted.has(name))assert(emitted.get(name).equals(payload),'Conflicting output: '+name);
  emitted.set(name,payload);
};
const outputName=name=>name===primary?'index.html':name;
const linkToSource=(name,fragment='')=>repo+'/blob/v'+version+'/'+name.split('/').map(encodeURIComponent).join('/')+fragment;
const queue=[...seed], seen=new Set();
while(queue.length){
  const name=queue.shift();if(seen.has(name))continue;seen.add(name);
  assert(seed.includes(name),'Unexpected HTML publication surface: '+name);
  const original=read(name);sources.push({path:name,bytes:original.length,sha256:sha(original)});
  let html=original.toString('utf8');
  html=html.replaceAll('img-src data:',"img-src 'self' data:")
    .replace(/local publication candidate/gi,'Independent research prototype v1.0')
    .replaceAll('Not published or specialist-approved','Not specialist-approved')
    .replaceAll('Not published or specialist approved','Not specialist-approved')
    .replaceAll('Interactive Science for All · a local flagship prototype','Interactive Science for All · v1.0 research prototype');
  if(name===primary){
    assert.equal(html.split('<span id="f-package-link">').length,2);
    html=html.replace(/<span id="f-package-link">[^<]*<\/span>/,
      '<span id="f-package-link"><a href="'+repo+'/releases/tag/v'+version+'">Download the source and apps</a>, or <a href="'+repo+'">explore the GitHub repository</a>.</span>');
    html=html.replace('</head>','<meta name="description" content="Explore Artemis II photographs, try three interactive science experiments, and inspect the evidence behind the counts. Independent, open-source research prototype."><link rel="icon" href="/favicon.svg" type="image/svg+xml"></head>');
  }
  // Images keep their exact decoded bytes, but can load and cache separately.
  html=html.replace(/data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)/g,(all,format,data)=>{
    const bytes=Buffer.from(data,'base64');assert(bytes.toString('base64')===data,'Noncanonical image');
    const target='assets/'+sha(bytes)+'.'+(format==='jpeg'?'jpg':format);
    assets.set(target,bytes);return '/'+target;
  });
  const scripts=[];
  // Inspect markup only; JS strings can contain incomplete HTML templates.
  html=html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/g,block=>{scripts.push(block);return '__SCRIPT_'+(scripts.length-1)+'__';});
  html=html.replace(/\bhref="([^"#][^"]*)"/g,(all,value)=>{
    if(/^(https?:|data:|mailto:|\/)/.test(value))return all;
    const [target,fragment='']=value.split('#');
    const resolved=path.posix.normalize(path.posix.join(path.posix.dirname(name),decodeURIComponent(target)));
    assert(!resolved.startsWith('../')&&fs.existsSync(path.join(root,resolved)),'Missing linked source: '+name+' -> '+value);
    const tail=fragment?'#'+fragment:'';
    if(resolved===primary||resolved==='Artemis-II-Interactive-Presentation-2026-10-13.html')return 'href="/index.html'+tail+'"';
    if(seed.includes(resolved)){queue.push(resolved);return 'href="/'+outputName(resolved)+tail+'"';}
    return 'href="'+linkToSource(resolved,tail)+'"';
  });
  html=html.replace(/__SCRIPT_(\d+)__/g,(_,n)=>scripts[Number(n)]);
  assert(!html.includes('\u2014'),'Unexpected em dash in reading copy');
  emit(outputName(name),html);
}
for(const[name,bytes]of assets)emit(name,bytes);
emit('favicon.svg','<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#112b3b"/><circle cx="32" cy="32" r="19" fill="none" stroke="#ffbb9e" stroke-width="5"/><circle cx="47" cy="17" r="5" fill="#b6dfca"/></svg>\n');
emit('404.html','<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found | Artemis II</title><style>body{max-width:42rem;margin:15vh auto;padding:24px;background:#f4f3e9;color:#112b3b;font:1.25rem/1.6 Georgia,serif}a{color:#175f65}</style><h1>That page is not here.</h1><p>The investigation is still waiting for you.</p><p><a href="/">Return to Artemis II</a> · <a href="'+repo+'">Source and apps on GitHub</a></p></html>\n');
// No recursive deletion: refuse obsolete output so later releases cannot silently retain files.
if(fs.existsSync(out)){
  const walk=folder=>fs.readdirSync(folder,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(folder,e.name)):[path.relative(out,path.join(folder,e.name)).replaceAll('\\','/')]);
  for(const old of walk(out))assert(emitted.has(old)||old==='release.json','Obsolete output requires explicit review: '+old);
}
for(const[name,bytes]of emitted){const dest=path.join(out,name);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,bytes);}
const manifest={version,scientific_claim_change:false,model_trained:false,source_base:release.source_base,
  sources,files:[...emitted].map(([name,bytes])=>({path:name,bytes:bytes.length,sha256:sha(bytes)})).sort((a,b)=>a.path.localeCompare(b.path))};
fs.writeFileSync(path.join(out,'release.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({pass:true,version,files:emitted.size+1,bytes:[...emitted.values()].reduce((n,b)=>n+b.length,0),entry_bytes:emitted.get('index.html').length,images:assets.size}));
