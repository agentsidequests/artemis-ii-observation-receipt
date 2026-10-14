// Buildless local presentation and synchronized reading exports. No publication.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';

const args=process.argv.slice(2);
function option(name){const i=args.indexOf(name);if(i<0||!args[i+1])throw Error('Missing '+name);return args[i+1];}
const root=fs.realpathSync(option('--root'));
const output=path.resolve(option('--output'));
const markedPath=fs.realpathSync(option('--marked'));
const {marked}=await import(pathToFileURL(markedPath));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const text=file=>fs.readFileSync(path.join(root,file),'utf8');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const dataBytes=fs.readFileSync(path.join(root,'presentation/data.json'));
assert.equal(sha(dataBytes),'d41fe206bf1ece970c11e7a96e47e4ba605e97eec7f75a1d553a83e26160d3e1','Unqualified presentation excerpt; replay and explicitly qualify changes');
const data=JSON.parse(dataBytes);
for(const [key,source] of Object.entries(data.sources)){
  const bytes=fs.readFileSync(path.join(root,source.path));
  assert.equal(bytes.length,source.bytes,key+' size');assert.equal(sha(bytes),source.sha256,key+' hash');
}
assert.equal(data.clock.all_event_coverage,'UNESTABLISHED');
assert.equal(data.clock.photo_epoch,'2026-04-07T01:04:00Z');
assert.equal(data.fanout.context.products,4290);assert.equal(data.fanout.scheduled_events,1);
assert.equal(data.relationship.capture_linked_test_products+data.relationship.action_only_linked_test_products+data.relationship.action_isolated_test_products,data.relationship.test_products);
assert.equal(data.robustness.witnesses.length,48);
for(const b of data.robustness.scenarios){for(const v of [b.lower.numerator,b.upper.numerator,b.total_weight])assert(Number.isSafeInteger(v));}
assert(data.robustness.scenarios.find(b=>b.reassignment_budget===47).lower.numerator*2>data.robustness.majority.denominator);
assert(data.robustness.scenarios.find(b=>b.reassignment_budget===48).lower.numerator*2<=data.robustness.majority.denominator);
const imageFile='presentation/media/art002e009301-nasa-public.jpg',imageBytes=fs.readFileSync(path.join(root,imageFile));
assert.equal(sha(imageBytes),'1bb6387479474ea44221dbb7627f603bf3ceb6e3c6ce2af5a75e7b50147bfe17','Unqualified editorial image');
const readerOpening=text('presentation/reader-opening.html').replace('__ECLIPSE_IMAGE__','data:image/jpeg;base64,'+imageBytes.toString('base64'));
const replacements={__STYLE__:text('presentation/styles.css')+'\n'+text('presentation/reader.css'),__SCRIPT__:text('presentation/story.js'),__WORKBENCH__:text('presentation/workbench.js'),__READER__:readerOpening,__READER_SCRIPT__:text('presentation/reader.js'),
  __DATA__:JSON.stringify(data).replaceAll('<','\\u003c').replaceAll('>','\\u003e').replaceAll('&','\\u0026'),
  __DATA_SHA__:sha(dataBytes),__CONTEXT_PRODUCTS__:data.fanout.context.products.toLocaleString('en-US'),
  __CONTEXT_ACTIONS__:data.fanout.context.actions.toLocaleString('en-US'),__CONTEXT_EXPOSURES__:data.fanout.context.exposures.toLocaleString('en-US')};
let page=text('presentation/index.template.html');
for(const [token,value] of Object.entries(replacements))page=page.replaceAll(token,value);
assert(!/__\w+__/.test(page),'Unresolved build token');assert(!page.includes('\u2014'),'Em dash');
const entries=new Map([['Artemis-II-Interactive-Presentation-2026-10-13.html',Buffer.from(page,'utf8')]]);
const readingStyle=`*{box-sizing:border-box}body{margin:0;background:#f4f1e8;color:#1a303b;font:18px/1.75 Georgia,serif}header{padding:17px 5vw;background:#122c39;color:#e1ece9;font:12px/1.6 ui-monospace,Consolas,monospace}main{max-width:970px;margin:40px auto;padding:0 30px 55px}h1{font:400 47px/1.13 Georgia,serif;letter-spacing:-.025em}h2{font:400 30px/1.3 Georgia,serif;border-top:1px solid #bcc9c6;padding-top:25px;margin-top:43px}h3{font:600 19px/1.4 system-ui,sans-serif}.packet{font:16px/1.7 system-ui,sans-serif}.packet h1{font-size:39px}a{color:#1b6178;text-underline-offset:4px}a:focus-visible,.table-region:focus-visible{outline:3px solid #985b16;outline-offset:4px}p{margin:0 0 22px}img{display:block;width:100%;height:auto;margin:27px 0}code{font:12px/1.65 ui-monospace,Consolas,monospace;overflow-wrap:anywhere}blockquote{margin:24px 0;padding:15px 23px;border-left:3px solid #24696c;background:#e8efe8}blockquote p{margin:0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e8efe8;padding:20px}.table-region{overflow:auto;margin:25px 0;border:1px solid #c0cfca}table{border-collapse:collapse;width:100%;min-width:620px;font:13px/1.6 system-ui,sans-serif}th,td{padding:13px 15px;border-bottom:1px solid #c0cfca;text-align:left;vertical-align:top}th{background:#ddeae3}footer{margin-top:35px;border-top:1px solid #bcc9c6;padding-top:20px;font:12px/1.65 system-ui,sans-serif;overflow-wrap:anywhere}li{margin:.55rem 0}@media(max-width:650px){main{padding:0 18px 40px;margin-top:27px}h1{font-size:35px}h2{font-size:27px}body{font-size:17px}.packet{font-size:15px}}@media print{body{background:white;color:black}header{background:white;color:black}main{max-width:none;margin:0;padding:0}h2,h3{break-after:avoid}tr,img{break-inside:avoid}.table-region{overflow:visible}table{min-width:0}}`;
const readingInputs=[['PUBLIC-ANALYSIS-DRAFT.md','Artemis-II-Essay-2026-10-13','essay'],['ARTEMIS-II-TWO-GATE-SPECIALIST-REVIEW-PACKET.md','Artemis-II-Specialist-Review-2026-10-13','packet']];
const figureStyle='figure{margin:27px 0}picture img{margin:0}.figure-values{margin:12px 0 28px;font:15px/1.65 system-ui,sans-serif}.figure-values summary{cursor:pointer;color:#1b6178;padding:8px 0}.figure-values summary:focus-visible{outline:3px solid #985b16;outline-offset:4px}.figure-values table{min-width:0}.figure-values th,.figure-values td{overflow-wrap:anywhere}@media(max-width:650px){.figure-values th,.figure-values td{padding:8px;font-size:13px}.figure-values{font-size:15px}}.proof-note{margin:22px 0 28px;padding:0 18px;border:1px solid #b8c9c4;border-radius:6px;background:#eaf0e9}.proof-note>summary{cursor:pointer;color:#1b6178;padding:13px 0;font:600 15px/1.55 system-ui,sans-serif}.proof-note>summary:focus-visible{outline:3px solid #985b16;outline-offset:4px}.proof-note[open]>summary{margin-bottom:14px;border-bottom:1px solid #c0cfca}.proof-note p{font-size:16px;line-height:1.7}.proof-note .table-region{margin:18px 0}.proof-note>p:last-child{margin-bottom:18px}@media(max-width:650px){.proof-note{padding:0 12px}.proof-note>summary{font-size:14px}.proof-note p{font-size:16px}}';
const documentSources=[];
const figureValues=JSON.parse(text('presentation/figure-reading-values.json'));
assert.equal(figureValues.figures.length,9);
for(const source of figureValues.sources)assert.equal(sha(fs.readFileSync(path.join(root,source.path))),source.sha256,'Figure source drift');
const figureSources=[];
const editorialDirectory='presentation/editorial/figures/';
const editorialManifest=JSON.parse(text(editorialDirectory+'manifest.json'));
assert.equal(editorialManifest.values_sha256,sha(fs.readFileSync(path.join(root,'presentation/figure-reading-values.json'))),'Editorial values drift');
for(const f of editorialManifest.files)assert.equal(sha(fs.readFileSync(path.join(root,editorialDirectory+f.path))),f.sha256,'Editorial asset drift');
const readingNav='<nav class="reading-nav" aria-label="Essay sections"><p>Read the argument</p><a href="#observation">What counts?</a><a href="#counting">Who gets a vote?</a><a href="#evaluation">What is held out?</a><a href="#detection">What could be seen?</a><a href="#next">What to publish next</a><p class="nav-note">The main story comes first. Open the proof panels for exact calculations and assumptions.</p></nav>';
for(const [source,stem,kind]of readingInputs){
  const raw=fs.readFileSync(path.join(root,source)),original=raw.toString('utf8');assert(!original.includes('\u2014'),source);
  const images=[...original.matchAll(/!\[([^\]]*)\]\(([^)]+)\)/g)];if(kind==='essay')assert.equal(images.length,9);
  let rendered=original,editable=original;
  for(const [match,alt,filename]of images){
    const matchNumber=filename.match(/^presentation\/editorial\/figures\/figure-(0[1-9])-desktop\.png$/);
    assert(matchNumber,'Unknown current figure path');
    const spec=figureValues.figures.find(f=>f.number===Number(matchNumber[1]));assert(spec,'Missing figure values');
    const historicalFilename=spec.filename;
    const bytes=fs.readFileSync(path.join(root,historicalFilename));assert.equal(bytes.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
    const mobilePath='presentation/mobile/'+historicalFilename,mobile=fs.readFileSync(path.join(root,mobilePath));
    assert.equal(mobile.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
    const editorialPath=editorialDirectory+'figure-'+String(spec.number).padStart(2,'0')+'-desktop.svg';
    const editorialMobilePath=editorialPath.replace('-desktop.svg','-phone.svg');
    const editorial=fs.readFileSync(path.join(root,editorialPath)),editorialMobile=fs.readFileSync(path.join(root,editorialMobilePath));
    const pngPath=editorialPath.replace('.svg','.png');
    assert(fs.existsSync(path.join(root,pngPath)),'Missing PNG sharing copy');
    const hasValues=spec.rows.some(r=>r.value!==null);
    const rows=spec.rows.map(r=>'<tr><th scope="row">'+esc(r.label)+'</th>'+(hasValues?'<td>'+esc(r.value===null?'':typeof r.value==='number'&&!Number.isInteger(r.value)?r.value.toFixed(3):r.value)+' '+esc(r.unit)+'</td>':'')+'<td>'+esc(r.detail)+'</td></tr>').join('');
    const scale=spec.number===5?'All index tracks 0–36 concentration-equivalent window units. Equal original membership weights would give 36.':spec.scale;
    const fallback='<details class="figure-values"><summary>Read figure '+spec.number+' data and limits</summary><p>'+esc(scale)+'</p><table><thead><tr><th>Measure</th>'+(hasValues?'<th>Value</th>':'')+'<th>Context</th></tr></thead><tbody>'+rows+'</tbody></table><p>'+esc(spec.note)+'</p></details>';
    rendered=rendered.replace(match,'<figure><picture><source media="(max-width:650px)" srcset="data:image/svg+xml;base64,'+editorialMobile.toString('base64')+'"><img src="data:image/svg+xml;base64,'+editorial.toString('base64')+'" alt="'+esc(alt)+'"></picture>'+fallback+'</figure>\n');
    figureSources.push({path:historicalFilename,sha256:sha(bytes),mobile_path:mobilePath,mobile_sha256:sha(mobile),editorial_path:editorialPath,editorial_sha256:sha(editorial),editorial_mobile_path:editorialMobilePath,editorial_mobile_sha256:sha(editorialMobile),sharing_png_path:pngPath,sharing_png_sha256:sha(fs.readFileSync(path.join(root,pngPath)))});
    editable=editable.replace(match,'!['+alt+']('+path.relative(output,path.join(root,pngPath)).replaceAll('\\','/')+')');
  }
  let body=marked.parse(rendered,{gfm:true});assert(!/<script\b|<iframe\b|\son\w+\s*=/i.test(body));
  body=body.replaceAll('<table>','<div class="table-region" tabindex="0" role="region" aria-label="Scrollable evidence table"><table>').replaceAll('</table>','</table></div>');
  if(kind==='essay'){
    for(const [heading,id]of [['Relationship: how one event becomes 4,290 products','observation'],['Selection: a blank label is not a negative example','counting'],['A clean split can still split the same observation','evaluation'],['Detection: the observer changed after the first flash','detection'],['NASA already has a family tree','next']]){
      const anchor='<h2>'+heading+'</h2>';assert(body.includes(anchor),'Missing reading chapter: '+heading);
      body=body.replace(anchor,'<h2 class="chapter-start" id="'+id+'">'+heading+'</h2>');
    }
  }
  const title=original.split('\n')[0].replace(/^# /,'');
  const footer='<footer>Source: '+esc(source)+'; SHA-256 '+sha(raw)+'. Source-bound desktop and phone figures embedded; expandable data equivalents included. Scientific receipt inputs unchanged. <a href="'+stem+'.md">Editable companion</a>. The package includes editable SVG and PNG sharing copies. Local evidence paths are locators, not the full scientific execution bundle. The presentation package supplies only its declared bounded replay.</footer>';
  const html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>'+esc(title)+'</title><style>'+text('presentation/editorial/reader.css')+'</style></head><body class="'+kind+'"><header><div class="masthead"><strong>Artemis II / Evidence essay</strong><span>Reader edition 14 October 2026</span></div><div class="edition-status">Local publication candidate. Not published or specialist-approved. <a href="Artemis-II-Interactive-Presentation-2026-10-13.html">Explore the calculations</a></div></header><main>'+(kind==='essay'?readingNav:'')+'<article>'+body+footer+'</article></main></body></html>\n';
  entries.set(stem+'.html',Buffer.from(html,'utf8'));entries.set(stem+'.md',Buffer.from(editable,'utf8'));
  documentSources.push({path:source,bytes:raw.length,sha256:sha(raw),reading:stem+'.html'});
}
const guide=text('presentation/GUIDE.md');assert(!guide.includes('\u2014'));entries.set('Artemis-II-Presentation-Guide-2026-10-13.md',Buffer.from(guide,'utf8'));
const manifest={version:data.version,private:true,new_science:false,reader_edition:'2026-10-14',reader_surface:'v8',editorial_media:[{path:imageFile,bytes:imageBytes.length,sha256:sha(imageBytes),credit:'NASA',source_page:'https://www.nasa.gov/image-detail/amf-art002e009301/',not_nef_processing_or_photometry:true}],figure_sources:figureSources,figure_values_sha256:sha(fs.readFileSync(path.join(root,'presentation/figure-reading-values.json'))),data:{path:'presentation/data.json',bytes:dataBytes.length,sha256:sha(dataBytes)},document_sources:documentSources,files:[...entries].map(([name,bytes])=>({path:name,bytes:bytes.length,sha256:sha(bytes)}))};
entries.set('presentation-manifest.json',Buffer.from(JSON.stringify(manifest,null,2)+'\n','utf8'));
fs.mkdirSync(output,{recursive:true});
for(const [name,bytes]of entries){const target=path.join(output,name);if(args.includes('--check'))assert(fs.existsSync(target)&&fs.readFileSync(target).equals(bytes),'Build drift: '+name);else fs.writeFileSync(target,bytes);}
console.log(JSON.stringify({pass:true,files:entries.size,output,main_sha256:sha(entries.get('Artemis-II-Interactive-Presentation-2026-10-13.html')),manifest},null,2));
