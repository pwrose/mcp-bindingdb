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
  function plan(s, mode, threshold=0.85, chirality=false, affinity=null){
    if(!s) throw new Error('Load a valid structure to prepare a query.');
    if((s.type==='smarts'||s.wildcard) && mode!=='substructure') throw new Error('SMARTS and wildcard queries require Substructure mode. Exact and similarity searches require a concrete molecule.');
    if(mode==='similarity'&&(!Number.isFinite(threshold)||threshold<0||threshold>1)) throw new Error('Similarity must be between 0 and 1.');
    let filters={};
    if(affinity){
      const {type,min,max}=affinity;
      if(!['Any','Ki','Kd','IC50','EC50'].includes(type)) throw new Error('Select an affinity measurement type.');
      if(!Number.isFinite(min)||!Number.isFinite(max)||min<0||max<0) throw new Error('Affinity limits must be non-negative numbers in nM.');
      if(min>max) throw new Error('Minimum affinity must not exceed maximum affinity.');
      filters={...(type==='Any'?{}:{affinity_types:[type]}),min_value_nm:min,max_value_nm:max};
    }
    if(mode==='similarity') return {name:'similarity_search',arguments:{smiles:s.smiles,threshold,...filters,limit:50}};
    if(mode==='substructure') return {name:'substructure_search',arguments:{query:s.type==='smarts'?s.input:s.smiles,query_type:s.type==='smarts'?'smarts':'smiles',use_chirality:chirality,...filters,limit:50}};
    return {name:'exact_structure_search',arguments:{smiles:s.smiles,...filters,limit:50}};
  }
  root.BindingDBCore={parse,plan};
})(globalThis);
