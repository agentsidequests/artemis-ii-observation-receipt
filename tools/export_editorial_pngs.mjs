// Optional PNG sharing exports from the same editable SVG. No acquisition.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const args=process.argv.slice(2);
const option=n=>{const i=args.indexOf(n);if(i<0||!args[i+1])throw Error('Missing '+n);return args[i+1];};
const root=fs.realpathSync(option('--root'));
const require=createRequire(path.resolve(option('--sharp')));
const sharp=require(option('--sharp'));
const directory=path.join(root,'presentation/editorial/figures');
const rows=[];
for(const name of fs.readdirSync(directory).filter(n=>n.endsWith('.svg')).sort()){
  const source=fs.readFileSync(path.join(directory,name));
  const png=await sharp(source,{density:144}).png().toBuffer();
  const target=name.replace('.svg','.png');
  fs.writeFileSync(path.join(directory,target),png);
  const meta=await sharp(png).metadata();
  rows.push({path:target,bytes:png.length,sha256:crypto.createHash('sha256').update(png).digest('hex'),width:meta.width,height:meta.height,svg_source:name,svg_sha256:crypto.createHash('sha256').update(source).digest('hex')});
}
fs.writeFileSync(path.join(directory,'png-manifest.json'),JSON.stringify({version:'editorial-v6',new_science:false,files:rows},null,2)+'\n');
console.log(JSON.stringify({pass:true,png_figures:rows.length}));
