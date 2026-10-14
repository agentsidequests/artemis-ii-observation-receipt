// Optional local rendering tool. No acquisition, publication, or evidence mutation.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import crypto from 'node:crypto';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const outputArg = process.argv.indexOf('--output');
const output = outputArg < 0 ? path.join(root, 'preview') : path.resolve(process.argv[outputArg + 1]);
if (!output.startsWith(root + path.sep)) throw Error('Reading output must remain inside the selected source checkout.');
const markedArg = process.argv.indexOf('--marked');
if (markedArg < 0 || !process.argv[markedArg + 1]) throw Error('Supply --marked with an existing marked 17.0.5 module path. No automatic installation.');
const {marked} = await import(pathToFileURL(fs.realpathSync(process.argv[markedArg + 1])));
const entries = [['README.md', 'index.html', 'guide'], ['PUBLIC-ANALYSIS-DRAFT.md', 'essay.html', 'essay'],
                 ['ARTEMIS-II-TWO-GATE-SPECIALIST-REVIEW-PACKET.md', 'specialist-packet.html', 'packet']];
const escape = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const css = `
*{box-sizing:border-box}body{margin:0;background:#f6f4ed;color:#202c36}
header{padding:16px 24px;background:#152c3d;color:#fff;font:14px/1.5 system-ui,sans-serif}header a{color:#f0dfaf}
main{max-width:930px;margin:40px auto;padding:0 32px 56px}article{font:18px/1.7 Georgia,serif}
.guide article,.packet article{font:16px/1.65 system-ui,sans-serif}
h1{font:600 44px/1.14 Georgia,serif;letter-spacing:-.025em;margin:0 0 30px}
h2{font:650 25px/1.3 system-ui,sans-serif;margin:54px 0 20px;border-top:1px solid #c9cdc9;padding-top:24px}
h3{font:650 19px/1.35 system-ui,sans-serif;margin-top:32px}p{margin:0 0 22px}
a{color:#175c82;text-underline-offset:3px}a:focus-visible,.table-wrap:focus-visible{outline:3px solid #b07822;outline-offset:4px}
blockquote{margin:28px 0;padding:12px 24px;border-left:4px solid #bc9149;background:#eceee8}
blockquote p{margin:8px 0}img{display:block;width:100%;height:auto;margin:30px 0 20px}
code{font:13px/1.4 ui-monospace,Consolas,monospace;overflow-wrap:anywhere;background:#e8ebe7;padding:2px 4px}
pre{overflow:auto;padding:18px;background:#e8ebe7}pre code{padding:0}li{margin:8px 0}
.table-wrap{overflow-x:auto;margin:24px 0 30px;border:1px solid #c9cdc9;border-radius:4px}
table{border-collapse:collapse;width:100%;min-width:560px;font:14px/1.5 system-ui,sans-serif}
th{background:#dce5e7;text-align:left}td,th{padding:12px 14px;border-bottom:1px solid #c9cdc9;vertical-align:top}
tbody tr:nth-child(even){background:#eeeee7}footer{font:13px/1.5 system-ui,sans-serif;color:#4b5a62;border-top:1px solid #c9cdc9;padding-top:20px;overflow-wrap:anywhere}
@media(max-width:600px){main{margin:28px auto;padding:0 18px 40px}h1{font-size:34px}article{font-size:17px}h2{font-size:23px}header{padding:12px 18px}}
@media print{body{background:white}header{color:#202c36;background:white}main{max-width:none;padding:0}h2{break-after:avoid}img,tr{break-inside:avoid}table{min-width:0}.table-wrap{overflow:visible}a{color:inherit}}
`;
const outputs = [];
for (const [source, filename, kind] of entries) {
  const bytes = fs.readFileSync(path.join(root, source));
  let text = bytes.toString('utf8');
  if (text.includes('\u2014')) throw Error('Em dash in reading source: ' + source);
  const images = [...text.matchAll(/!\[([^\]]*)\]\(([^)]+)\)/g)];
  if (kind === 'essay' && images.length !== 9) throw Error('Expected nine original figures');
  for (const [match, alt, name] of images) {
    if (!/^Artemis-II-Chart-[1-9]-[A-Za-z-]+\.png$/.test(name)) throw Error('Unqualified image: ' + name);
    const payload = fs.readFileSync(path.join(root, name));
    if (payload.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a') throw Error('Not PNG');
    text = text.replace(match, `![${alt}](data:image/png;base64,${payload.toString('base64')})`);
  }
  let body = marked.parse(text, {gfm:true});
  if (/<script\b|<iframe\b|\son\w+\s*=/i.test(body)) throw Error('Executable content rejected');
  body = body.replace(/href="(?!https?:|data:|mailto:|#)([^"]+)"/g, (_, href) => `href="../${href}"`);
  body = body.replace(/<table>/g, '<div class="table-wrap" tabindex="0" role="region" aria-label="Scrollable evidence table"><table>').replace(/<\/table>/g, '</table></div>');
  const title = bytes.toString('utf8').split('\n')[0].replace(/^# /, '');
  const sourceHash = crypto.createHash('sha256').update(bytes).digest('hex');
  const page = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>${escape(title)}</title><style>${css}</style></head><body class="${kind}"><header>LOCAL PUBLICATION CANDIDATE • agentsidequests • October 13, 2026<br>Not published or specialist-approved. <a href="index.html">Start here</a> · <a href="essay.html">Essay</a> · <a href="flashes/index.html">Flash demo</a> · <a href="identity-confirmed/index.html">Current identity</a> · <a href="robustness/index.html">Robustness</a> · <a href="../Artemis-II-Interactive-Presentation-2026-10-13.html">Presentation</a></header><main><article>${body}</article><footer>Reading export of <a href="../${escape(source)}">${escape(source)}</a>. Source SHA-256: ${sourceHash}. Original figures are embedded unchanged. MIT covers original project material only; third-party terms remain applicable.</footer></main></body></html>\n`;
  outputs.push([filename, Buffer.from(page)]);
}
fs.mkdirSync(output, {recursive:true});
for (const [filename, payload] of outputs) {
  const target = path.join(output, filename);
  if (fs.existsSync(target) && !fs.readFileSync(target).equals(payload)) throw Error('Existing differing export: ' + filename);
}
for (const [filename, payload] of outputs) {
  const target = path.join(output, filename);
  if (!fs.existsSync(target)) fs.writeFileSync(target, payload, {flag:'wx'});
  console.log(JSON.stringify({filename,bytes:payload.length,sha256:crypto.createHash('sha256').update(payload).digest('hex')}));
}
