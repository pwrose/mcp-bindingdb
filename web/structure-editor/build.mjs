import fs from 'node:fs';
import path from 'node:path';
import {gzipSync,gunzipSync} from 'node:zlib';
import {build} from 'vite';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
process.chdir(fileURLToPath(new URL('.',import.meta.url)));

const cwd=process.cwd();
await build({configFile:false,build:{lib:{entry:path.resolve('ui/bridge.js'),name:'BindingDBBridge',formats:['iife'],fileName:()=> 'bridge.js'},outDir:'.bridge',emptyOutDir:true,minify:true}});
const gzip=data=>gzipSync(data,{level:9}).toString('base64');
const files={};
function walk(dir){for(const d of fs.readdirSync(dir,{withFileTypes:true}).sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0)){const p=path.join(dir,d.name);if(d.isDirectory())walk(p);else if(!/devmode|package\.json/.test(p)){const rel=path.relative('vendor/jsme',p);const data=fs.readFileSync(p);files[rel.replace(/\.gz$/,'')]=(rel.endsWith('.gz')?gunzipSync(data):data).toString('base64');}}}
walk('vendor/jsme');
for(const [name,b64] of Object.entries(files)){if(name.endsWith('.js')){let code=Buffer.from(b64,'base64').toString();for(const image of ['clear.cache.gif','40BAF81124143A595056A9CCA0E9DBBA.cache.png']){if(files[image])code=code.replaceAll(image,'data:image/'+(image.endsWith('.gif')?'gif':'png')+';base64,'+files[image]);}files[name]=Buffer.from(code).toString('base64');}}
let bootstrap=Buffer.from(files['jsme.nocache.js'],'base64').toString();
bootstrap=bootstrap.replace('jsme.__moduleBase=B()','jsme.__moduleBase=\'\'').replace('function C(a){','function C(a){if(window.__JSME_FILES[a])return window.__JSME_FILES[a];');
files['jsme.nocache.js']=Buffer.from(bootstrap).toString('base64');
const engine=`
(async()=>{
 try{
 const unzip=async b=>new Uint8Array(await new Response(new Blob([Uint8Array.from(atob(b),c=>c.charCodeAt(0))]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
 const decode=b=>new TextDecoder().decode(b);
 const script=s=>{const e=document.createElement('script');e.textContent=s;document.head.append(e);};
 const files=JSON.parse(decode(await unzip('${gzip(Buffer.from(JSON.stringify(files)))}')));
 window.__JSME_FILES={};
 for(const [name,b64] of Object.entries(files)){
 const mime=name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':name.endsWith('.png')?'image/png':'image/gif';
 window.__JSME_FILES[name]='data:'+mime+';base64,'+b64;
 }
 const jsmeReady=new Promise(resolve=>window.jsmeOnLoad=resolve);
 script(atob(files['jsme.nocache.js']));
 script(decode(await unzip('${gzip(fs.readFileSync(require.resolve('@rdkit/rdkit')))}')));
 const wasmBinary=await unzip('${gzip(fs.readFileSync(require.resolve('@rdkit/rdkit/RDKit_minimal.wasm')))}');
 // This RDKit.js build ignores the wasmBinary option and would fetch RDKit_minimal.wasm, which the sandbox blocks.
 const rdkit=await initRDKitModule({instantiateWasm:(imports,receive)=>{WebAssembly.instantiate(wasmBinary,imports).then(r=>receive(r.instance));return {};}});
 await jsmeReady;
 window.dispatchEvent(new CustomEvent('bindingdb-engines',{detail:{rdkit}}));
 }catch(e){document.getElementById('engineStatus').textContent='Chemistry engine failed';document.getElementById('notice').textContent='Could not initialize the chemistry engine: '+e.message;document.getElementById('notice').className='notice error';}
})();`;
let html=fs.readFileSync('ui/editor.html','utf8');
for(const [tag,value] of Object.entries({STYLE:fs.readFileSync('ui/style.css','utf8'),CORE:fs.readFileSync('ui/core.js','utf8'),BRIDGE:fs.readFileSync('.bridge/bridge.js','utf8'),ENGINE:engine,APP:fs.readFileSync('ui/app.js','utf8')})) html=html.replace('/*'+tag+'*/',()=>value.replace(/<\/script/gi,'<\\/script'));
const output=path.resolve('../../src/mcp_bindingdb/assets/structure-editor');
fs.mkdirSync(output,{recursive:true});
for(const name of fs.readdirSync(output)){if(name.endsWith('.gz.part'))fs.unlinkSync(path.join(output,name));}
const bundle=gzipSync(Buffer.from(html),{level:9});
const chunkSize=192*1024;
for(let offset=0;offset<bundle.length;offset+=chunkSize){fs.writeFileSync(path.join(output,String(offset/chunkSize).padStart(3,'0')+'.gz.part'),bundle.subarray(offset,offset+chunkSize));}
console.log('Built '+output+' ('+(Buffer.byteLength(html)/1024/1024).toFixed(2)+' MB)');

// Figure panel: shows draw_structure_grid's image in the chat (src/mcp_bindingdb/structure_editor.py, FIGURE_URI).
await build({configFile:false,build:{lib:{entry:path.resolve('ui/figure.js'),name:'BindingDBFigure',formats:['iife'],fileName:()=> 'figure.js'},outDir:'.bridge',emptyOutDir:false,minify:true}});
const figure=fs.readFileSync('ui/figure.html','utf8').replace('/*FIGURE*/',()=>fs.readFileSync('.bridge/figure.js','utf8').replace(/<\/script/gi,'<\\/script'));
fs.writeFileSync(path.resolve('../../src/mcp_bindingdb/assets/figure-viewer.html.gz'),gzipSync(Buffer.from(figure),{level:9}));
console.log('Built figure panel ('+(Buffer.byteLength(figure)/1024).toFixed(0)+' KB)');
