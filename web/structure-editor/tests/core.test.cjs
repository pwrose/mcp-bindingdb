const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
vm.runInThisContext(fs.readFileSync('ui/core.js','utf8'));
const init=require('@rdkit/rdkit');const promise=init();
test('canonical roundtrip, stereo and salt preservation',async()=>{const rd=await promise;for(const smi of ['CC(=O)Oc1ccccc1C(=O)O','N[C@@H](C)C(=O)O','CC(=O)[O-].[Na+]']){const s=BindingDBCore.parse(rd,smi,'smiles');const t=BindingDBCore.parse(rd,s.smiles,'smiles');assert.equal(s.smiles,t.smiles);assert.match(s.key,/^[A-Z]{14}-[A-Z]{10}-[A-Z]$/);s.mol.delete();t.mol.delete();}});
test('SMARTS stays exact query text and is blocked in molecular modes',async()=>{const rd=await promise;const s=BindingDBCore.parse(rd,'[NX3;H1,H2][CX3](=[OX1])','smarts');assert.equal(s.smiles,null);assert.equal(BindingDBCore.plan(s,'substructure').arguments.query,'[NX3;H1,H2][CX3](=[OX1])');assert.throws(()=>BindingDBCore.plan(s,'exact'));assert.throws(()=>BindingDBCore.plan(s,'similarity'));s.mol.delete();});
test('invalid, empty, and wildcard input',async()=>{const rd=await promise;for(const v of ['','C1CCC','C(C)(C)(C)(C)C','xyz'])assert.throws(()=>BindingDBCore.parse(rd,v,'smiles'));assert.throws(()=>BindingDBCore.parse(rd,'[C','smarts'));const s=BindingDBCore.parse(rd,'*CC','smiles');assert.throws(()=>BindingDBCore.plan(s,'exact'));assert.throws(()=>BindingDBCore.plan(s,'similarity'));s.mol.delete();});
test('query plans match BindingDB tool signatures',async()=>{const rd=await promise;const s=BindingDBCore.parse(rd,'CCO','smiles');assert.deepEqual(BindingDBCore.plan(s,'similarity',.85),{name:'similarity_search',arguments:{smiles:'CCO',threshold:.85,limit:50}});assert.equal(BindingDBCore.plan(s,'substructure',.7,true).arguments.use_chirality,true);assert.deepEqual(BindingDBCore.plan(s,'exact'),{name:'exact_structure_search',arguments:{smiles:'CCO',limit:50}});assert.equal(BindingDBCore.plan(s,'similarity').arguments.threshold,.7);assert.throws(()=>BindingDBCore.plan(s,'similarity',2));s.mol.delete();});

test('sketcher MOL input preserves header lines',async()=>{const rd=await promise;const mol=rd.get_mol('CCO');const s=BindingDBCore.parse(rd,mol.get_molblock(),'smiles');assert.equal(s.smiles,'CCO');s.mol.delete();mol.delete();});

test('affinity ranges are carried by the search tool for every mode',async()=>{
 const rd=await promise,s=BindingDBCore.parse(rd,'CCO','smiles');
 const tools={exact:'exact_structure_search',substructure:'substructure_search',similarity:'similarity_search'};
 for(const mode of ['exact','substructure','similarity'])for(const types of [['Ki','Kd','IC50','EC50'],['Ki'],['Kd','Ki'],['IC50','EC50','Kd']]){
  const p=BindingDBCore.plan(s,mode,.81,true,{types,min:0,max:1000});
  assert.equal(p.name,tools[mode]);
  // In the server's order; all four is the server's default, so none are sent.
  assert.deepEqual(p.arguments.affinity_types,{1:['Ki'],2:['Ki','Kd'],3:['Kd','IC50','EC50'],4:undefined}[types.length]);
  assert.equal(p.arguments.min_value_nm,0);assert.equal(p.arguments.max_value_nm,1000);
  if(mode==='similarity')assert.equal(p.arguments.threshold,.81);
  if(mode==='substructure')assert.equal(p.arguments.use_chirality,true);
 }
 assert.equal(BindingDBCore.plan(s,'exact',.7,false,null).arguments.max_value_nm,undefined);
 const all=['Ki','Kd','IC50','EC50'];
 for(const range of [{types:all,min:20,max:10},{types:['Ki'],min:-1,max:1000},{types:all,min:0,max:NaN},{types:all,min:NaN,max:1000},{types:all,min:0,max:Infinity},{types:['kon'],min:0,max:1000},{types:[],min:0,max:1000}])assert.throws(()=>BindingDBCore.plan(s,'exact',.7,false,range));
 assert.equal(BindingDBCore.plan(s,'exact',.7,false,{types:['Kd'],min:.1,max:.1}).arguments.min_value_nm,.1);
 assert.match(BindingDBCore.describe(BindingDBCore.plan(s,'exact',.7,false,{types:['Kd','Ki'],min:0,max:10})),/requiring at least one Ki or Kd measurement from 0 to 10 nM$/);
 s.mol.delete();
 const q=BindingDBCore.parse(rd,'[NX3;H1,H2][CX3](=[OX1])','smarts');
 assert.equal(BindingDBCore.plan(q,'substructure',.7,false,{types:['Ki'],min:0,max:50}).arguments.query,q.input);
 assert.throws(()=>BindingDBCore.plan(q,'exact',.7,false,{types:['Ki'],min:0,max:50}));q.mol.delete();
});
test('results table and the search description',async()=>{
 const rd=await promise,s=BindingDBCore.parse(rd,'OCC','smiles');
 const exact=BindingDBCore.plan(s,'exact');
 let h=BindingDBCore.hits(exact,{rows:[{monomerid:1,bdbm_id:'BDBM1',name:'ethanol',mol_weight:46.07,n_activities:1234,n_targets:3}],n_exact_matches:1,truncated:false});
 assert.deepEqual(h,{columns:['Compound','MW','Measurements','Targets'],rows:[['BDBM1 ethanol','46.07','1,234','3']],summary:'1 exact match.'});
 const filtered=BindingDBCore.plan(s,'similarity',.7,false,{types:['Ki','Kd','IC50','EC50'],min:0,max:1000});
 const data={rows:[{monomerid:2,compound_name:'x',similarity:0.75,affinity_type:'IC50',relation:'<',value:10,target_name:'Kinase'}],n_similar_compounds:21,truncated:true};
 h=BindingDBCore.hits(filtered,data);
 assert.deepEqual(h.columns,['Compound','Similarity','Best affinity','Target']);
 assert.deepEqual(h.rows,[['BDBM2 x','0.75','IC50 < 10 nM','Kinase']]);
 assert.equal(h.summary,'21 compounds at or above the threshold with a qualifying measurement (first 1 shown; more exist).');
 assert.equal(BindingDBCore.describe(filtered),'BindingDB similarity search with a minimum Tanimoto similarity of 0.70, requiring at least one Ki, Kd, IC50, or EC50 measurement from 0 to 1000 nM');
 assert.equal(BindingDBCore.hits(BindingDBCore.plan(s,'substructure'),{rows:[],truncated:false}).summary,'0 compounds.');
 s.mol.delete();
});
