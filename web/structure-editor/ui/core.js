(function(root){
  function parse(rdkit, input, type) {
    const q=input.trim();
    if (!q) throw new Error('Enter a structure first.');
    if (q.length>20000) throw new Error('This editor accepts queries up to 20,000 characters.');
    let mol;
    try {
      mol=type==='smarts'?rdkit.get_qmol(q):rdkit.get_mol(input.includes('M  END')?input:q);
      if(!mol || !mol.is_valid()) throw new Error('invalid');
      const atoms=JSON.parse(mol.get_json()).molecules?.[0]?.atoms || [];
      if(!atoms.length) throw new Error('empty');
      const smiles=type==='smarts'?null:mol.get_smiles();
      const wildcard=type!=='smarts' && atoms.some(a=>a.z===0);
      let key=null, descriptors={};
      if(type!=='smarts' && !wildcard){
        try { key=rdkit.get_inchikey_for_inchi(mol.get_inchi()); } catch{}
        try { descriptors=JSON.parse(mol.get_descriptors()); } catch{}
      }
      return {mol, input:q, type, smiles, smarts:type==='smarts'?q:mol.get_smarts(), key, descriptors, wildcard, atomCount:atoms.filter(a=>a.z!==1).length, fragments:type==='smarts'?null:smiles.split('.').length};
    } catch(e) {
      if(mol) mol.delete();
      throw new Error(type==='smarts'?'Invalid SMARTS. Check atom expressions, bonds, and ring closures.':'Invalid molecular SMILES or drawing. Check valence, bonds, and ring closures.');
    }
  }
  const TYPES=['Ki','Kd','IC50','EC50'];  // the server's default affinity_types
  function plan(s, mode, threshold=0.7, chirality=false, affinity=null){
    if(!s) throw new Error('Load a valid structure to prepare a query.');
    if((s.type==='smarts'||s.wildcard) && mode!=='substructure') throw new Error('SMARTS and wildcard queries require Substructure mode. Exact and similarity searches require a concrete molecule.');
    if(mode==='similarity'&&(!Number.isFinite(threshold)||threshold<0||threshold>1)) throw new Error('Similarity must be between 0 and 1.');
    let filters={};
    if(affinity){
      const {types,min,max}=affinity;
      if(!Array.isArray(types)||!types.length||types.some(t=>!TYPES.includes(t))) throw new Error('Select at least one affinity measurement type.');
      if(!Number.isFinite(min)||!Number.isFinite(max)||min<0||max<0) throw new Error('Affinity limits must be non-negative numbers in nM.');
      if(min>max) throw new Error('Minimum affinity must not exceed maximum affinity.');
      const chosen=TYPES.filter(t=>types.includes(t));
      filters={...(chosen.length===TYPES.length?{}:{affinity_types:chosen}),min_value_nm:min,max_value_nm:max};
    }
    if(mode==='similarity') return {name:'similarity_search',arguments:{smiles:s.smiles,threshold,...filters,limit:50}};
    if(mode==='substructure') return {name:'substructure_search',arguments:{query:s.type==='smarts'?s.input:s.smiles,query_type:s.type==='smarts'?'smarts':'smiles',use_chirality:chirality,...filters,limit:50}};
    return {name:'exact_structure_search',arguments:{smiles:s.smiles,...filters,limit:50}};
  }
  const either=list=>list.length<3?list.join(' or '):list.slice(0,-1).join(', ')+', or '+list.at(-1);
  function describe(p){
    const a=p.arguments;
    const label={exact_structure_search:'exact structure',substructure_search:'substructure',similarity_search:'similarity'}[p.name];
    const threshold=p.name==='similarity_search'?' with a minimum Tanimoto similarity of '+a.threshold.toFixed(2):'';
    const affinity=a.max_value_nm===undefined?'':', requiring at least one '+either(a.affinity_types||TYPES)+' measurement from '+a.min_value_nm+' to '+a.max_value_nm+' nM';
    return 'BindingDB '+label+' search'+threshold+affinity;
  }
  // Rows are compounds, or with an affinity filter each compound's most potent qualifying measurement.
  function hits(p,data){
    const rows=data.rows||[],filtered=p.arguments.max_value_nm!==undefined,similarity=p.name==='similarity_search';
    const columns=['Compound',...(similarity?['Similarity']:[]),...(filtered?['Best affinity','Target']:['MW','Measurements','Targets'])];
    const n=v=>v===null||v===undefined?'':Number(v).toLocaleString('en-US');
    const cells=rows.map(r=>[(r.bdbm_id||'BDBM'+r.monomerid)+(r.name||r.compound_name?' '+(r.name||r.compound_name):''),...(similarity?[Number(r.similarity).toFixed(2)]:[]),
      ...(filtered?[r.affinity_type+' '+(r.relation==='='?'':r.relation+' ')+r.value+' nM',r.target_name||'']:[n(r.mol_weight),n(r.n_activities),n(r.n_targets)])]);
    const count=(k,noun)=>k+' '+noun+(k===1?'':noun.endsWith('h')?'es':'s'),qualifying=filtered?' with a qualifying measurement':'';
    const summary=p.name==='exact_structure_search'?count(data.n_exact_matches,'exact match')+(filtered?'; '+rows.length+qualifying:''):
      similarity?count(data.n_similar_compounds,'compound')+' at or above the threshold'+qualifying:count(rows.length,'compound')+qualifying;
    return {columns,rows:cells,summary:summary+(data.truncated?' (first '+rows.length+' shown; more exist)':'')+'.'};
  }
  root.BindingDBCore={parse,plan,describe,hits};
})(globalThis);
