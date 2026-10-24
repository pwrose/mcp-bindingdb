(function(){
'use strict';
const $=id=>document.getElementById(id);
const core=window.BindingDBCore;
let fitQueued=false,lastEditorSize='',submitting=false;
let rdkit=null,editor=null,current=null,mode='exact',inputType='smiles',suppress=false,ready=false,requestSerial=0,currentPlan=null,provenance='Pasted SMILES',pendingInitial=null,lastEditorSmiles='';
const empty='<div class="empty-depiction">⌬<span>Your rendered structure will appear here</span></div>';
function queueFit(){if(fitQueued)return;fitQueued=true;requestAnimationFrame(()=>{fitQueued=false;fitEditor();});}
function fitEditor(){const main=$('workbench'),area=$('editorArea'),container=$('jsme_container');if(!main||!area)return;const fixed=main.getBoundingClientRect().height-area.getBoundingClientRect().height;const budget=Math.min(window.innerHeight||540,540);const minimum=$('inspectDetails').open?100:145;const height=Math.max(minimum,Math.min(270,Math.floor(budget-fixed-2)));if(Math.abs(area.clientHeight-height)>1)area.style.height=height+'px';const width=Math.floor(area.clientWidth);const scale=Math.min(1,height/300);container.style.width=width+'px';container.style.height=height+'px';container.style.transform='none';const size=width+'x'+height;if(editor&&width>0&&size!==lastEditorSize){lastEditorSize=size;editor.setMenuScale(scale);editor.setMolecularAreaScale(scale);editor.setSize(width,height);}}

function notice(message,kind=''){ $('notice').textContent=message;$('notice').className='notice '+kind; }
function release(){if(current?.mol)current.mol.delete();current=null;}
function invalidate(message){$('queryOverlay').hidden=true;$('provenance').textContent='Input → validation → canonical representation';$('editorState').textContent='JSME molecular sketcher';release();currentPlan=null;$('depiction').innerHTML=empty;$('smilesOutput').value='';$('inchiKey').textContent='—';['atomCount','molWeight','fragments'].forEach(id=>$(id).textContent='—');$('validBadge').textContent='Awaiting validation';$('validBadge').className='badge';$('copySmiles').disabled=true;updatePlan();if(message)notice(message);}
function setType(type){inputType=type;document.querySelectorAll('[data-type]').forEach(b=>{const yes=b.dataset.type===type;b.classList.toggle('active',yes);b.setAttribute('aria-selected',String(yes));});$('sourceWrap').hidden=type!=='name';$('privacyNote').hidden=type!=='name';$('inputHint').textContent=type==='smarts'?'SMARTS stays a query; it is never turned into molecular SMILES.':'Or draw directly in the editor below.';$('loadBtn').textContent=type==='name'?'Resolve':'Load';$('loadBtn').setAttribute('aria-label',type==='name'?'Resolve chemical name':'Load structure');$('structureInput').placeholder=type==='name'?'Enter a chemical name, e.g. aspirin or 5-ethyl-3,5-dimethyloctanal':type==='smarts'?'Paste a SMARTS query, e.g. [NX3][CX3](=[OX1])':'Paste a SMILES string, e.g. CC(=O)Oc1ccccc1C(=O)O';}
function setMode(value){mode=value;document.querySelectorAll('[data-mode]').forEach(b=>{const yes=b.dataset.mode===mode;b.classList.toggle('active',yes);b.setAttribute('aria-checked',String(yes));});$('similarityOptions').hidden=mode!=='similarity';$('similarityCard').classList.toggle('active',mode==='similarity');$('chiralityWrap').hidden=mode!=='substructure';$('searchNote').textContent=mode==='exact'?'Includes stereo and salts; keeps tautomers distinct.':mode==='substructure'?'Matches compounds containing this fragment.':'Compares the largest fragment; ignores stereo.';updatePlan();}
function affinityFilter(){if(!$('affinityEnabled').checked)return null;return {type:$('affinityType').value,min:$('affinityMin').valueAsNumber,max:$('affinityMax').valueAsNumber};}
function updatePlan(){currentPlan=null;try{if(mode==='similarity'&&(!$('thresholdNumber').validity.valid||!Number.isFinite($('thresholdNumber').valueAsNumber)))throw new Error('Enter 0–1 in steps of 0.01.');currentPlan=core.plan(current,mode,$('thresholdNumber').valueAsNumber,$('chirality').checked,affinityFilter());const label={exact:'exact structure',substructure:'substructure',similarity:'similarity'}[mode];$('queryStatus').textContent=label.charAt(0).toUpperCase()+label.slice(1)+' search ready.';}catch(e){$('queryStatus').textContent=current?e.message:'Draw or load a structure.';}$('queryStatus').hidden=!!currentPlan;$('runBtn').disabled=!currentPlan||submitting;}
function draw(s){return s.mol.get_svg_with_highlights(JSON.stringify({width:440,height:190,bondLineWidth:1.7,addStereoAnnotation:true,backgroundColour:[1,1,1,1]}));}
function accept(text,type,source,loadEditor=true){
 let s;try{s=core.parse(rdkit,text,type);}catch(e){invalidate(e.message);notice(e.message,'error');return false;}
 release();current=s;provenance=source;
 $('depiction').innerHTML=draw(s);$('queryOverlay').hidden=type!=='smarts';
 if(type==='smarts'){$('patternSvg').innerHTML=draw(s);if(mode!=='substructure')setMode('substructure');}
 else if(loadEditor && editor){suppress=true;try{editor.readMolFile(s.mol.get_molblock());lastEditorSmiles=editor.smiles();}finally{suppress=false;}}
 $('validBadge').textContent=type==='smarts'?'Valid query':'Valid molecule';$('validBadge').className='badge valid';
 $('atomCount').textContent=String(s.atomCount);$('molWeight').textContent=type==='smarts'||s.wildcard?'—':Number(s.descriptors.amw||0).toFixed(2);$('fragments').textContent=s.fragments===null?'—':String(s.fragments);
 $('smilesOutput').value=type==='smarts'?'Not defined for a SMARTS query pattern.':s.smiles;$('copySmiles').disabled=!s.smiles;
 $('inchiKey').textContent=s.key||'Not applicable';$('provenance').textContent=source+(type==='smarts'?' → original SMARTS preserved':' → RDKit canonical isomeric SMILES');$('editorState').textContent=type==='smarts'?'Query text controls this pattern':'JSME molecular sketcher';
 updatePlan();notice(type==='smarts'?'SMARTS ready for a substructure search.':'Structure ready.','success');
 if(s.fragments>1)notice('Multiple fragments detected. Exact retains all fragments; similarity uses the largest fragment.','success');
 return true;
}
function editChanged(){if(suppress||!ready)return;const drawn=editor.smiles();if(drawn===lastEditorSmiles)return;lastEditorSmiles=drawn;requestSerial++;$('candidates').hidden=true;setType('smiles');$('queryOverlay').hidden=true;let molfile;try{molfile=editor.molFile();}catch{invalidate('Could not read the drawing.');return;}if(!editor.smiles()){invalidate('The drawing is empty. Add an atom, bond, or ring to begin.');$('structureInput').value='';return;}if(accept(molfile,'smiles','Edited in sketcher',false))$('structureInput').value=current.smiles;}
function dataFromResult(result){if(result.isError)throw new Error(result.content?.[0]?.text||'Tool failed');if(result.structuredContent)return result.structuredContent;const text=result.content?.find(c=>c.type==='text')?.text;try{return JSON.parse(text||'{}');}catch{throw new Error('The name resolver returned an unexpected response.');}}
async function resolve(name,source){
 if(window.BindingDBHost){
  const sources=source==='auto'?['bindingdb','pubchem','opsin']:[source];
  const data=dataFromResult(await window.BindingDBHost.callServerTool({name:'chemical_name_to_smiles',arguments:{name,sources}}));
  if(Array.isArray(data.candidates)&&!data.resolved)return data;
  if(!data.resolved)return {candidates:[],tried:data.sources_tried||[]};
  let candidates=(data.candidates?.length?data.candidates:[{smiles:data.smiles,name:data.pubchem_name||name,inchi_key:data.inchi_key,monomerid:data.monomerid}]).map(c=>({smiles:c.smiles,title:c.name||data.pubchem_name||name,source:data.source,cid:data.pubchem_cid,inchi_key:c.inchi_key,monomerid:c.monomerid,warning:data.warning}));
  // PubChem may map a synonym to more than one CID. Fetch each through the app helper.
  if(data.other_pubchem_cids?.length){const more=dataFromResult(await window.BindingDBHost.callServerTool({name:'editor_pubchem_candidates',arguments:{cids:data.other_pubchem_cids.slice(0,19)}}));candidates.push(...(more.candidates||[]));}
  return {candidates,tried:data.sources_tried||[],ambiguous:data.ambiguous};
 }
 throw new Error('Open the editor in an MCP Apps chat client to resolve chemical names.');
}
function renderCandidates(data,name){const box=$('candidates');box.replaceChildren();box.hidden=false;const heading=document.createElement('div');heading.className='candidate-heading';heading.textContent=`${data.candidates.length} candidate${data.candidates.length===1?'':'s'} found. Review identity, stereo, and salts; select the intended structure.`;box.append(heading);
 for(const c of data.candidates){const row=document.createElement('div');row.className='candidate';let s;try{s=core.parse(rdkit,c.smiles,'smiles');const image=document.createElement('div');image.innerHTML=draw(s);row.append(image);}catch{continue;}finally{s?.mol.delete();}const info=document.createElement('div');info.className='candidate-info';const title=document.createElement('strong');title.textContent=c.title||name;info.append(title);for(const value of [c.source+(c.cid?' · CID '+c.cid:'')+(c.monomerid?' · BDBM'+c.monomerid:''),c.inchi_key||'',c.warning||'',c.smiles]){if(!value)continue;const p=document.createElement('p');p.textContent=value;info.append(p);}const btn=document.createElement('button');btn.className='secondary';btn.textContent='Use this structure';btn.onclick=()=>{if(accept(c.smiles,'smiles',c.source+(c.cid?' CID '+c.cid:'')+' · '+(c.title||name))){box.hidden=true;notice('Selected '+(c.title||name)+'. Review the rendered structure and query.','success');}};row.append(info,btn);box.append(row);}
 const trail=document.createElement('p');trail.className='muted';trail.textContent='Resolution: '+(data.tried||[]).map(t=>t.source+': '+t.status).join(' → ');box.append(trail);
}
async function load(){if(!ready)return;const input=$('structureInput').value.trim();requestSerial++;const serial=requestSerial;$('candidates').hidden=true;invalidate();if(!input){notice('Enter a chemical name, SMILES, or SMARTS.','error');return;}if(inputType!=='name'){accept(input,inputType,inputType==='smarts'?'Pasted SMARTS':'Pasted SMILES');return;}
 $('loadBtn').disabled=true;notice('Resolving name…');try{const data=await resolve(input,$('source').value);if(serial!==requestSerial)return;if(!data.candidates?.length){notice('No structure resolved. Try a more specific name or paste a verified SMILES. '+(data.tried||[]).map(t=>t.source+': '+t.status).join('; '),'error');return;}renderCandidates(data,input);notice('Review the candidate structures below and select one.');}catch(e){if(serial===requestSerial)notice('Name resolution failed: '+e.message,'error');}finally{$('loadBtn').disabled=!ready;}}
async function copy(value,label){try{await navigator.clipboard.writeText(value);notice(label+' copied.','success');}catch{notice('Clipboard is unavailable here. Select and copy the text directly.');}}
function startNew(){requestSerial++;$('structureInput').value='';$('candidates').hidden=true;setType('smiles');$('queryOverlay').hidden=true;lastEditorSmiles='';suppress=true;editor?.reset();suppress=false;invalidate('Start a new drawing, or paste a molecular SMILES.');}
function applyInitial(data){if(!ready){pendingInitial=data;return;}setType(data.input_type||'smiles');$('structureInput').value=data.initial_query;if(data.mode)setMode(data.mode);if(!data.initial_query)return;if(inputType!=='name')load();else notice('Name supplied by chat. Resolve it and review the candidates.');}
window.addEventListener('bindingdb-initial',event=>applyInitial(event.detail));
function hostConnected(){$('hostStatus').textContent='MCP App · connected to chat';$('runBtn').hidden=false;document.querySelector('.draft-label').hidden=true;}
window.addEventListener('bindingdb-connected',hostConnected);
if(window.BindingDBHost)hostConnected();
if(window.BindingDBInitialData)applyInitial(window.BindingDBInitialData);
window.addEventListener('bindingdb-engines',event=>{rdkit=event.detail.rdkit;window.jsmeOnLoad=()=>{};fitEditor();editor=new JSApplet.JSME('jsme_container','100%',$('jsme_container').clientHeight+'px',{options:'newlook,star,polarnitro',gui:{background:'#ffffff'}});editor.setCallBack('AfterStructureModified',()=>{if(!suppress)setTimeout(editChanged,0);});ready=true;$('loadBtn').disabled=false;$('engineStatus').textContent='Ready';document.querySelector('.engine').classList.add('ready');notice('Draw below, or load a structure above.');if(pendingInitial)applyInitial(pendingInitial);queueFit();});
document.querySelectorAll('[data-type]').forEach(b=>b.onclick=()=>{requestSerial++;setType(b.dataset.type);$('candidates').hidden=true;invalidate('Input format changed. Load to validate the new representation.');});
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));
$('structureInput').oninput=()=>{requestSerial++;$('candidates').hidden=true;invalidate('Input changed. Load it to update the structure and query.');};$('structureInput').onkeydown=e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter')load();};
$('source').onchange=()=>{requestSerial++;$('candidates').hidden=true;invalidate('Resolution source changed. Resolve the name again.');};
$('loadBtn').onclick=load;
function example(type,value){$('exampleMenu').open=false;setType(type);$('structureInput').value=value;load();}
$('aspirinBtn').onclick=()=>example('smiles','CC(=O)Oc1ccccc1C(=O)O');$('amideBtn').onclick=()=>example('smarts','[NX3][CX3](=[OX1])');$('iupacBtn').onclick=()=>example('name','5-ethyl-3,5-dimethyloctanal');
$('clearBtn').onclick=startNew;$('newMoleculeBtn').onclick=startNew;
$('cleanBtn').onclick=()=>{if(!current||current.type==='smarts')return;current.mol.set_new_coords();suppress=true;try{editor.readMolFile(current.mol.get_molblock());lastEditorSmiles=editor.smiles();}finally{suppress=false;}};
$('threshold').oninput=()=>{$('thresholdNumber').value=$('threshold').value;$('thresholdNumber').setAttribute('aria-invalid','false');updatePlan();};
$('thresholdNumber').oninput=()=>{const field=$('thresholdNumber');const valid=field.validity.valid&&Number.isFinite(field.valueAsNumber);field.setAttribute('aria-invalid',String(!valid));if(valid)$('threshold').value=field.value;updatePlan();};$('chirality').onchange=updatePlan;
function affinityChanged(){
 const enabled=$('affinityEnabled').checked,min=$('affinityMin'),max=$('affinityMax');
 for(const field of [min,max,$('affinityType')])field.disabled=!enabled;
 const ordered=Number.isFinite(min.valueAsNumber)&&Number.isFinite(max.valueAsNumber)&&min.valueAsNumber<=max.valueAsNumber;
 for(const field of [min,max])field.setAttribute('aria-invalid',String(enabled&&(!field.validity.valid||!Number.isFinite(field.valueAsNumber)||!ordered)));
 updatePlan();
}
$('affinityEnabled').onchange=affinityChanged;$('affinityType').onchange=affinityChanged;
$('affinityMin').oninput=$('affinityMax').oninput=affinityChanged;
$('copySmiles').onclick=()=>current?.smiles&&copy(current.smiles,'SMILES');
$('runBtn').onclick=async()=>{
 if(!currentPlan||!window.BindingDBHost||submitting)return;
 const plan=structuredClone(currentPlan),selectedMode=mode;
 const label={exact:'exact structure',substructure:'substructure',similarity:'similarity'}[selectedMode];
 const threshold=selectedMode==='similarity'?' with a minimum Tanimoto similarity of '+plan.arguments.threshold.toFixed(2):'';
 const affinity=plan.name==='filtered_structure_search'?', requiring at least one '+(plan.arguments.affinity_type==='Any'?'Ki, Kd, IC50, or EC50':plan.arguments.affinity_type)+' measurement from '+plan.arguments.min_value_nm+' to '+plan.arguments.max_value_nm+' nM':'';
 submitting=true;$('runBtn').disabled=true;notice('Submitting query to chat…');
 try{
  await window.BindingDBHost.updateModelContext({content:[{type:'text',text:'User-reviewed BindingDB query (not yet executed):\n'+JSON.stringify(plan)+'\nUse the connected BindingDB search tool with these arguments. If a compatible search tool is unavailable, explain that the BindingDB search service needs to be connected. Do not claim that a search ran without a tool result. If filtered_structure_search is requested, preserve the affinity range and measurement type; never silently run an unfiltered query or filter a truncated list of hits.'}]});
  const result=await window.BindingDBHost.sendMessage({role:'user',content:[{type:'text',text:'Run the reviewed BindingDB '+label+' search'+threshold+affinity+' and show the results.'}]});
  if(result?.isError)throw new Error('The chat host did not accept the query request.');
  notice('Query submitted. Results will appear in chat.','success');
 }catch(e){notice('Could not submit query: '+e.message,'error');}
 finally{submitting=false;updatePlan();}
};
$('guideBtn').onclick=$('aboutBtn').onclick=()=>$('guide').showModal();$('closeGuide').onclick=()=>$('guide').close();$('guide').onclick=e=>{if(e.target===$('guide'))$('guide').close();};
window.addEventListener('resize',queueFit);$('inspectDetails').addEventListener('toggle',queueFit);new ResizeObserver(queueFit).observe($('workbench'));queueFit();
window.BindingDBEditor={getState:()=>({ready,inputType,mode,smiles:current?.smiles,plan:currentPlan}),load,accept,startNew};
})();
