// Reuse the qualified v8 build, then replace only its reader entry and reader controller.
// No network, source conversion, new scientific calculation or publication.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
const args=process.argv.slice(2);
function option(name){const i=args.indexOf(name);if(i<0||!args[i+1])throw Error('Missing '+name);return args[i+1];}
const root=fs.realpathSync(option('--root')),output=path.resolve(option('--output')),marked=fs.realpathSync(option('--marked'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=f=>fs.readFileSync(path.join(root,f)),text=f=>bytes(f).toString('utf8');
const sourceFiles=['presentation/observatory/index.html','presentation/observatory/style.css','presentation/observatory/app.js','presentation/reader.js'];
const images=[
  {path:'presentation/media/art002e009301-nasa-public.jpg',sha256:'1bb6387479474ea44221dbb7627f603bf3ceb6e3c6ce2af5a75e7b50147bfe17',token:'__ECLIPSE_IMAGE__',mime:'image/jpeg',role:'Public-release eclipse JPEG; editorial context, not a flash image.'},
  {path:'corpus/evidence/stage8b/art002e012264_nkd5015_prc_v01.png',sha256:'8b3eb98c789f69019a2a989d5e63d181dc6abe22fb4a0eb206114e616aa85433',token:'__LUNAR_IMAGE__',mime:'image/png',role:'Existing NASA/PDS browse image, unchanged. Display-only zoom; not a Sunset image or new measurement.'}
];
for(const source of images)assert.equal(sha(bytes(source.path)),source.sha256,'Unqualified image: '+source.path);
const baseArgs=[path.join(root,'tools/build_presentation.mjs'),'--root',root,'--output',output,'--marked',marked];
if(args.includes('--check'))baseArgs.push('--check');
const built=spawnSync(process.execPath,baseArgs,{encoding:'utf8'});
assert.equal(built.status,0,'Base build failed: '+built.stderr);
const oldPage=text(path.relative(root,path.join(output,'Artemis-II-Interactive-Presentation-2026-10-13.html')));
const eclipse=bytes(images[0].path).toString('base64');
const oldEntry=text('presentation/reader-opening.html').replace('__ECLIPSE_IMAGE__','data:image/jpeg;base64,'+eclipse);
assert.equal(oldPage.split(oldEntry).length,2,'V8 reader entry is not unique.');
let newEntry=text('presentation/observatory/index.html');
for(const source of images)newEntry=newEntry.replaceAll(source.token,'data:'+source.mime+';base64,'+bytes(source.path).toString('base64'));
const reader=text('presentation/reader.js'),modelBoundary="if(typeof document!=='undefined'&&document.getElementById('sunset-counting')){";
assert.equal(reader.split(modelBoundary).length,2,'Reader model boundary changed.');
const model=reader.split(modelBoundary)[0],controller=model+'\n'+text('presentation/observatory/app.js');
assert.equal(oldPage.split('<script>'+reader+'</script>').length,2,'Old reader controller changed.');
let page=oldPage.replace(oldEntry,newEntry).replace('<script>'+reader+'</script>','<script>'+controller+'</script>');
page=page.replace('<body>','<body class="observatory-edition">');
page=page.replace('</style>','\n'+text('presentation/observatory/style.css')+'</style>');
page=page.replace('<title>Artemis II: One Moon. Thousands of files. How much evidence?</title>','<title>Look closer | Artemis II interactive field guide</title>');
const headerStart=page.indexOf('<header class="masthead">'),headerEnd=page.indexOf('</header>',headerStart)+9;
assert(headerStart>0&&headerEnd>headerStart,'Missing masthead');
page=page.slice(0,headerStart)+'<header class="masthead"><a class="wordmark" href="#main">ARTEMIS II<span>The archive, explored · by agentsidequests</span></a><nav aria-label="Story chapters"><a href="#one-sunset">Unfold the archive</a><a href="#sunset-counting">Change the count</a><a href="#technical-notebook" data-reveal="technical-notebook">Technical notebook</a></nav><button class="o-motion" id="o-motion" aria-pressed="false">Reduce motion</button></header>'+page.slice(headerEnd);
page=page.replace('Reader-first edition v8','Interactive field guide v9');
assert(!/__\w+__/.test(page),'Unresolved token');assert(!page.includes('\u2014'),'Forbidden punctuation');
const notebook=s=>s.slice(s.indexOf('<details id="technical-notebook">'),s.indexOf('</details></main>')+10);
assert(notebook(oldPage).length>10000);assert.equal(notebook(page),notebook(oldPage),'Technical notebook changed');
const filename='Artemis-II-Interactive-Field-Guide-v9-2026-10-14.html';
const manifest={edition:'v9',new_science:false,publicly_published:false,source_data_sha256:sha(bytes('presentation/data.json')),base_v8_page_sha256:sha(Buffer.from(oldPage)),technical_notebook_sha256:sha(Buffer.from(notebook(page))),media:images.map(({token,mime,...s})=>({...s,bytes:bytes(s.path).length,credit:'NASA / NASA PDS',unchanged:true})),sources:sourceFiles.map(p=>({path:p,bytes:bytes(p).length,sha256:sha(bytes(p))})),files:[{path:filename,bytes:Buffer.byteLength(page),sha256:sha(Buffer.from(page))}]};
for(const [name,b]of [[filename,Buffer.from(page)],['observatory-manifest.json',Buffer.from(JSON.stringify(manifest,null,2)+'\n')]]){
  const target=path.join(output,name);
  if(args.includes('--check'))assert(fs.existsSync(target)&&fs.readFileSync(target).equals(b),'Build drift: '+name);
  else fs.writeFileSync(target,b);
}
console.log(JSON.stringify({pass:true,...manifest},null,2));
