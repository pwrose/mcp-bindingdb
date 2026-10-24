const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
vm.runInThisContext(fs.readFileSync('ui/core.js','utf8'));
const init=require('@rdkit/rdkit');const promise=init();
test('canonical roundtrip, stereo and salt preservation',async()=>{const rd=await promise;for(const smi of ['CC(=O)Oc1ccccc1C(=O)O','N[C@@H](C)C(=O)O','CC(=O)[O-].[Na+]']){const s=BindingDBCore.parse(rd,smi,'smiles');const t=BindingDBCore.parse(rd,s.smiles,'smiles');assert.equal(s.smiles,t.smiles);assert.match(s.key,/^[A-Z]{14}-[A-Z]{10}-[A-Z]$/);s.mol.delete();t.mol.delete();}});
test('SMARTS stays exact query text and is blocked in molecular modes',async()=>{const rd=await promise;const s=BindingDBCore.parse(rd,'[NX3;H1,H2][CX3](=[OX1])','smarts');assert.equal(s.smiles,null);assert.equal(BindingDBCore.plan(s,'substructure').arguments.query,'[NX3;H1,H2][CX3](=[OX1])');assert.throws(()=>BindingDBCore.plan(s,'exact'));assert.throws(()=>BindingDBCore.plan(s,'similarity'));s.mol.delete();});
test('invalid, empty, and wildcard input',async()=>{const rd=await promise;for(const v of ['','C1CCC','C(C)(C)(C)(C)C','xyz'])assert.throws(()=>BindingDBCore.parse(rd,v,'smiles'));assert.throws(()=>BindingDBCore.parse(rd,'[C','smarts'));const s=BindingDBCore.parse(rd,'*CC','smiles');assert.throws(()=>BindingDBCore.plan(s,'exact'));assert.throws(()=>BindingDBCore.plan(s,'similarity'));s.mol.delete();});
test('query plans match BindingDB tool signatures',async()=>{const rd=await promise;const s=BindingDBCore.parse(rd,'CCO','smiles');assert.deepEqual(BindingDBCore.plan(s,'similarity',.85),{name:'similarity_search',arguments:{smiles:'CCO',threshold:.85,limit:50}});assert.equal(BindingDBCore.plan(s,'substructure',.7,true).arguments.use_chirality,true);assert.deepEqual(BindingDBCore.plan(s,'exact'),{name:'exact_structure_search',arguments:{smiles:'CCO',limit:50}});assert.equal(BindingDBCore.plan(s,'similarity').arguments.threshold,.85);assert.throws(()=>BindingDBCore.plan(s,'similarity',2));s.mol.delete();});

test('sketcher MOL input preserves header lines',async()=>{const rd=await promise;const mol=rd.get_mol('CCO');const s=BindingDBCore.parse(rd,mol.get_molblock(),'smiles');assert.equal(s.smiles,'CCO');s.mol.delete();mol.delete();});

test('affinity ranges are carried by the search tool for every mode',async()=>{
 const rd=await promise,s=BindingDBCore.parse(rd,'CCO','smiles');
 const tools={exact:'exact_structure_search',substructure:'substructure_search',similarity:'similarity_search'};
 for(const mode of ['exact','substructure','similarity'])for(const type of ['Any','Ki','Kd','IC50','EC50']){
  const p=BindingDBCore.plan(s,mode,.81,true,{type,min:0,max:1000});
  assert.equal(p.name,tools[mode]);
  assert.deepEqual(p.arguments.affinity_types,type==='Any'?undefined:[type]);assert.equal(p.arguments.min_value_nm,0);assert.equal(p.arguments.max_value_nm,1000);
  if(mode==='similarity')assert.equal(p.arguments.threshold,.81);
  if(mode==='substructure')assert.equal(p.arguments.use_chirality,true);
 }
 assert.equal(BindingDBCore.plan(s,'exact',.7,false,null).arguments.max_value_nm,undefined);
 for(const range of [{type:'Any',min:20,max:10},{type:'Ki',min:-1,max:1000},{type:'Any',min:0,max:NaN},{type:'Any',min:NaN,max:1000},{type:'Any',min:0,max:Infinity},{type:'kon',min:0,max:1000}])assert.throws(()=>BindingDBCore.plan(s,'exact',.7,false,range));
 assert.equal(BindingDBCore.plan(s,'exact',.7,false,{type:'Kd',min:.1,max:.1}).arguments.min_value_nm,.1);
 s.mol.delete();
 const q=BindingDBCore.parse(rd,'[NX3;H1,H2][CX3](=[OX1])','smarts');
 assert.equal(BindingDBCore.plan(q,'substructure',.7,false,{type:'Ki',min:0,max:50}).arguments.query,q.input);
 assert.throws(()=>BindingDBCore.plan(q,'exact',.7,false,{type:'Ki',min:0,max:50}));q.mol.delete();
});
