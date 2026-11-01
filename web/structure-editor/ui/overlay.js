import { App } from '@modelcontextprotocol/ext-apps';
// Shows overlay_binding_site's superposed PDB complexes (src/mcp_bindingdb/structures.py) with 3Dmol.js: each
// entry's protein chains (lines), ligand (sticks), hydrogen bonds and binding-site surface toggled separately,
// with an affinity bar, and optional labels on the residues the shown ligands bind. In a chat it
// fetches the structures with the app-only overlay_data tool; the standalone page has them inlined.
const $ = id => document.getElementById(id);
const ELEMENTS = {N: '#3050F8', O: '#FF0D0D', S: '#E6C200', P: '#FF8000', F: '#5BBF3A', Cl: '#1FB01F', Br: '#A62929', I: '#940094', B: '#FFB5B5'};
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const short = (s, n = 28) => s.length > n ? s.slice(0, n - 1) + '…' : s;
let app = null;

function status(text) { $('status').textContent = text; $('status').hidden = false; }

// Bar colours by affinity type, as in draw_structure_grid (src/mcp_bindingdb/figures.py, TYPE_COLOURS).
const TYPE_COLOURS = {Ki: '#2f6f8f', Kd: '#3f8a5c', IC50: '#7a5aa6', EC50: '#a8662d'};
const SITE = 5; // Å, residues whose surface is drawn as the binding site
const fmt = nm => nm >= 100 ? Math.round(nm).toLocaleString('en-US') : String(+nm.toPrecision(3));

// The bar scale in nM: whole decades around all values, as figures._scale; null without values.
function barScale(entries) {
  const values = entries.map(e => e.value_nm).filter(v => v > 0);
  if (!values.length) return null;
  const lo = 10 ** Math.floor(Math.log10(Math.min(...values))), hi = 10 ** Math.ceil(Math.log10(Math.max(...values)));
  return [hi === lo ? hi * 10 : hi, lo];
}
// The bar's length is the median on the log scale. With several values, a strip under it shows their spread
// on the same scale: whiskers from the weakest to the most potent value, a box over the middle half (from 3
// values) and a tick at the median.
function barHtml(e, scale) {
  if (!scale || !(e.value_nm > 0) || !TYPE_COLOURS[e.affinity_type]) return '';
  const [empty, full] = scale;
  const at = nm => 100 * Math.min(1, Math.max(0, (Math.log10(empty) - Math.log10(nm)) / (Math.log10(empty) - Math.log10(full))));
  const f = Math.max(3, at(e.value_nm));
  const n = e.n_measurements || 1, sp = e.spread, colour = TYPE_COLOURS[e.affinity_type];
  const text = `${e.affinity_type} ${fmt(e.value_nm)} nM${n > 1 ? ` (n=${n})` : ''}`;
  let strip = '', title = (e.affinity || text) + (n > 1 ? '' : ', one measurement');
  if (n > 1 && sp?.min > 0 && sp?.max > 0) {
    const lo = at(sp.max), hi = at(sp.min);  // the weakest value nearest the empty end
    const line = (x1, y1, x2, y2) => `<line x1="${x1.toFixed(2)}" y1="${y1}" x2="${x2.toFixed(2)}" y2="${y2}"/>`;
    let marks = line(lo, 4, hi, 4) + line(lo, 1.5, lo, 6.5) + line(hi, 1.5, hi, 6.5);
    title += `; range ${fmt(sp.min)}–${fmt(sp.max)} nM`;
    if (n >= 3 && sp.q1 > 0 && sp.q3 > 0) {
      const b1 = at(sp.q3), b2 = at(sp.q1);
      marks += `<rect x="${b1.toFixed(2)}" y="1" width="${Math.max(b2 - b1, 0.5).toFixed(2)}" height="6" fill="${colour}" fill-opacity=".45"/>`
        + line(at(e.value_nm), 0, at(e.value_nm), 8);
      title += `, middle half ${fmt(sp.q1)}–${fmt(sp.q3)} nM`;
    }
    strip = `<svg class="spread" viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true">${marks}</svg>`;
  }
  return `<div class="barwrap" title="${esc(title)}"><div class="bar${n < 3 ? ' faint' : ''}"><i style="width:${f.toFixed(1)}%;background:${colour}"></i><span>${esc(text)}</span></div>${strip}</div>`;
}

// Cα atoms joined in chain order (no bond across a gap), for a line trace.
function caTrace(protein) {
  const ca = protein.selectedAtoms({atom: 'CA'});
  const atoms = ca.map((a, i) => ({elem: 'C', atom: 'CA', resn: a.resn, resi: a.resi, chain: a.chain, x: a.x, y: a.y, z: a.z,
    hetflag: false, index: i, serial: i, bonds: [], bondOrder: []}));
  for (let i = 1; i < atoms.length; i++) {
    const a = atoms[i - 1], b = atoms[i];
    if (a.chain === b.chain && Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z) < 4.3) {
      a.bonds.push(i); a.bondOrder.push(1); b.bonds.push(i - 1); b.bondOrder.push(1);
    }
  }
  return atoms;
}

// Residues of `protein` with an atom within `distance` Å of a `ligand` atom, as 'chain|resi' keys.
function pocketKeys(protein, ligand, distance = SITE) {
  const lig = ligand.selectedAtoms({}), d2 = distance * distance, keys = new Set();
  for (const a of protein.selectedAtoms({})) {
    const key = a.chain + '|' + a.resi;
    if (!keys.has(key) && lig.some(l => (a.x - l.x) ** 2 + (a.y - l.y) ** 2 + (a.z - l.z) ** 2 <= d2)) keys.add(key);
  }
  return keys;
}

// Residue names from overlay_binding_site ('T315:A', named by the reference entry) -> {chain, resi}; null for a
// residue with no reference counterpart ('X12:B (6E9A)').
function parseResidue(name) {
  const m = /^[A-Z](-?\d+)[A-Z]?:(\S+)$/.exec(name);
  return m ? {resi: +m[1], chain: m[2]} : null;
}

function render(data) {
  $('status').hidden = true; $('app').hidden = false;
  $('title').textContent = data.title;
  const n = data.entries.length;
  $('subtitle').textContent = `${n} ${n === 1 ? 'entry' : 'entries'} superposed on ${data.reference} by the binding-site Cα atoms. Hover over atoms for names; click a ligand to zoom to it.`;
  const viewer = $3Dmol.createViewer($('stage'), {backgroundColor: 'white', antialias: true});
  // Surfaces are made without web workers: the chat's sandbox may not allow a worker from a blob: URL.
  $3Dmol.SurfaceWorker = undefined;
  // The binding-site surface is on for the first entry (the reference) only.
  const state = data.entries.map((e, i) => ({protein: true, ligand: true, hbonds: false, surface: i === 0}));
  const surfaces = new Map(); // entry index -> 3Dmol surface id
  const models = data.entries.map(e => {
    const protein = viewer.addModel(e.protein_pdb, 'pdb'), ligand = viewer.addModel(e.ligand_pdb, 'pdb');
    const trace = viewer.addModel();
    trace.addAtoms(caTrace(protein));
    return {protein, ligand, trace, pocket: pocketKeys(protein, ligand)};
  });
  let labels = [], shapes = [];

  const ligandStyle = e => ({stick: {radius: 0.2, colorscheme: {prop: 'elem', map: {...ELEMENTS, C: e.colour, H: '#ffffff'}}}});
  function draw() {
    const kind = $('proteinStyle').value;
    data.entries.forEach((e, i) => {
      const m = models[i], show = state[i].protein;
      m.protein.setStyle({}, !show || kind === 'trace' ? {} : kind === 'cartoon' ? {cartoon: {color: e.colour, opacity: 0.55}}
        : {line: {color: e.colour, opacity: 0.85}});
      m.trace.setStyle({}, show && kind === 'trace' ? {line: {color: e.colour}} : {});
      m.ligand.setStyle({}, state[i].ligand ? ligandStyle(e) : {});
    });
    for (const s of shapes) viewer.removeShape(s);
    for (const l of labels) viewer.removeLabel(l);
    shapes = []; labels = [];
    data.entries.forEach((e, i) => {
      if (!state[i].hbonds || !state[i].ligand) return;
      for (const h of e.hbonds) {
        const [a, b] = [h.a, h.b].map(([x, y, z]) => ({x, y, z}));
        shapes.push(viewer.addCylinder({start: a, end: b, radius: 0.06, dashed: true, dashLength: 0.25, gapLength: 0.18, color: e.colour, fromCap: 1, toCap: 1}));
        labels.push(viewer.addLabel(h.distance.toFixed(1), {position: {x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, z: (a.z + b.z) / 2}, fontSize: 10, fontColor: '#1c2321', backgroundColor: 'white', backgroundOpacity: 0.75, borderColor: e.colour, borderThickness: 1, inFront: true, showBackground: true}));
      }
    });
    // Residue labels at the reference's Cα atoms: the H-bond partners or contact residues of the ligands shown.
    const which = $('labels').value;
    if (which !== 'none') {
      const names = new Set(data.entries.flatMap((e, i) => state[i].ligand ? (which === 'hbonds' ? e.hbond_partners : e.contacts) : []));
      const parsed = [...names].map(n => [n, parseResidue(n)]).filter(([, r]) => r);
      const oneChain = new Set(parsed.map(([, r]) => r.chain)).size <= 1;
      for (const [name, r] of parsed) {
        const ca = models[0].protein.selectedAtoms({chain: r.chain, resi: r.resi, atom: 'CA'})[0];
        if (!ca) continue;
        labels.push(viewer.addLabel(oneChain ? name.split(':')[0] : name, {position: {x: ca.x, y: ca.y, z: ca.z}, fontSize: 11,
          fontColor: '#1c2321', backgroundColor: 'white', backgroundOpacity: 0.8, borderThickness: 0, inFront: true,
          showBackground: true, alignment: 'center'}));
      }
    }
    data.entries.forEach((e, i) => {
      const m = models[i], on = state[i].surface && m.pocket.size > 0;
      if (on && !surfaces.has(i)) {
        const made = viewer.addSurface($3Dmol.SurfaceType.MS, {color: e.colour, opacity: +$('opacity').value},
          {model: m.protein, predicate: a => m.pocket.has(a.chain + '|' + a.resi)}, {model: m.protein});
        surfaces.set(i, made.surfid);
        made.then(() => viewer.render());
      } else if (!on && surfaces.has(i)) {
        viewer.removeSurface(surfaces.get(i));
        surfaces.delete(i);
      }
    });
    viewer.render();
    syncAll();
  }
  function zoomLigands(ms = 0) {
    const visible = models.filter((m, i) => state[i].ligand).map(m => m.ligand);
    viewer.zoomTo(visible.length ? {model: visible} : {}, ms);
    viewer.zoom(0.85, ms);
  }

  const tip = $('tip');
  data.entries.forEach((e, i) => {
    const m = models[i];
    const residue = atom => { tip.textContent = `${e.pdb_id} · ${atom.resn} ${atom.resi}:${atom.chain} · ${atom.atom}`; tip.hidden = false; };
    m.protein.setHoverable({}, true, residue, () => { tip.hidden = true; });
    m.trace.setHoverable({}, true, residue, () => { tip.hidden = true; });
    m.ligand.setHoverable({}, true, atom => { tip.textContent = `${e.pdb_id} · ${e.het}${e.name ? ' · ' + e.name : ''}${e.affinity ? ' · ' + e.affinity : ''} · ${atom.atom}`; tip.hidden = false; }, () => { tip.hidden = true; });
    m.ligand.setClickable({}, true, () => viewer.zoomTo({model: m.ligand}, 500));
  });

  // The bars show each entry's default potency (Ki/Kd first, as the tool picked it) or one affinity type for all.
  const TYPES = ['Ki', 'Kd', 'IC50', 'EC50'];
  function viewed(e, type) {
    if (type === 'default') return {...e, spread: e.potencies?.[e.affinity_type]};
    const p = e.potencies?.[type];
    if (!p) return {...e, affinity_type: type, value_nm: null, n_measurements: 0, affinity: null};
    const notes = [p.n > 1 ? `median of ${p.n}` : '', e.measured_on || ''].filter(Boolean);
    return {...e, affinity_type: type, value_nm: p.median, n_measurements: p.n, spread: p,
      affinity: `${type} ${fmt(p.median)} nM${notes.length ? ` (${notes.join(', ')})` : ''}`};
  }
  const present = TYPES.filter(t => data.entries.some(e => e.potencies?.[t]));
  const defaults = TYPES.filter(t => data.entries.some(e => e.value_nm > 0 && e.affinity_type === t));
  if (present.length > 1) {
    $('atype').innerHTML = `<option value="default">default (${defaults.join('/') || 'none'})</option>`
      + present.map(t => `<option value="${t}">${t} (${data.entries.filter(e => e.potencies?.[t]).length} of ${n})</option>`).join('');
    $('atypeBox').hidden = false;
  }
  function paintBars() {
    const type = $('atype').value || 'default', entries = data.entries.map(e => viewed(e, type));
    const scale = barScale(entries);
    entries.forEach((e, i) => {
      const html = barHtml(e, scale) || (e.affinity ? `<small>${esc(e.affinity)}</small>` : (type !== 'default' ? `<small>no ${esc(type)} data</small>` : ''));
      const cell = document.querySelector(`td.aff[data-i="${i}"]`);
      cell.innerHTML = html;
      cell.parentElement.hidden = !html;
    });
    const types = [...new Set(entries.filter(e => e.value_nm > 0).map(e => e.affinity_type))].filter(t => TYPE_COLOURS[t]);
    $('legend').innerHTML = types.length ? types.map(t => `<span><span class="sw" style="background:${TYPE_COLOURS[t]}"></span>${t}</span>`).join('')
      + '<span>log scale, longer = more potent (median); faint = fewer than 3 measurements; the strip below a bar: '
      + 'range (whiskers) and middle half (box) of the values</span>' : '';
  }
  // Resolution and RMSD for the entry's first line; '*' marks pocket residues that moved, listed on hover.
  function meta(e) {
    const res = e.resolution ? e.resolution.toFixed(2) + ' Å' : esc((e.method || '').toLowerCase());
    if (e.pdb_id === data.reference) return `${res} · ref`;
    const rmsd = `RMSD ${(e.pocket_rmsd ?? e.global_rmsd).toFixed(2)}`;
    return `${res} · ` + (e.moved?.length
      ? `<abbr title="Pocket residues more than 2 Å from their place in ${esc(data.reference)}: ${esc(e.moved.join(', '))}">${rmsd}*</abbr>` : rmsd);
  }
  const box = (i, col, label, on, disabled = false) => `<td class="c"><input type="checkbox" data-i="${i}" data-col="${col}"${on ? ' checked' : ''}${disabled ? ' disabled' : ''} aria-label="${label}"></td>`;
  // Three rows per entry: the id line and the affinity bar span the table (also above and below the
  // checkboxes), and only the name shares a row with the checkboxes, to keep the panel narrow.
  $('rows').innerHTML = data.entries.map((e, i) => {
    return `<tr class="head">
    <td class="who" colspan="5" data-i="${i}"><span class="line"><span class="sw" style="background:${esc(e.colour)}"></span><b>${esc(e.pdb_id)}</b> · ${esc(e.het)}<small class="meta">${meta(e)}</small></span></td></tr>
    <tr><td class="who" data-i="${i}"><small title="${esc(e.name || '')}">${esc(short(e.name || '', 20))}</small></td>
    ${box(i, 'protein', `Protein chains of ${esc(e.pdb_id)}`, true)}
    ${box(i, 'ligand', `Ligand of ${esc(e.pdb_id)}`, true)}
    ${box(i, 'hbonds', `${e.hbonds.length} hydrogen bonds of ${esc(e.pdb_id)}`, false, !e.hbonds.length)}
    ${box(i, 'surface', `Binding-site surface of ${esc(e.pdb_id)}`, i === 0)}</tr>
    <tr><td class="who aff" colspan="5" data-i="${i}"></td></tr>`;
  }).join('');
  for (const [i, e] of data.entries.entries()) {
    const cell = document.querySelector(`input[data-i="${i}"][data-col="hbonds"]`).parentElement;
    cell.title = `${e.hbonds.length} hydrogen bond${e.hbonds.length === 1 ? '' : 's'}${e.hbond_partners?.length ? ': ' + e.hbond_partners.join(', ') : ''}`;
  }
  paintBars();
  $('atype').addEventListener('change', paintBars);
  $('rows').addEventListener('change', ev => { const t = ev.target; if (t.dataset.col) { state[+t.dataset.i][t.dataset.col] = t.checked; draw(); } });
  $('rows').addEventListener('click', ev => { const who = ev.target.closest('.who'); if (who) viewer.zoomTo({model: models[+who.dataset.i].ligand}, 500); });
  const usable = col => data.entries.map((e, i) => i).filter(i => col !== 'hbonds' || data.entries[i].hbonds.length);
  function syncAll() {
    for (const b of document.querySelectorAll('button.all')) b.setAttribute('aria-pressed', String(usable(b.dataset.col).every(i => state[i][b.dataset.col])));
  }
  for (const b of document.querySelectorAll('button.all')) b.addEventListener('click', () => {
    const col = b.dataset.col, on = !usable(col).every(i => state[i][col]);
    for (const i of usable(col)) {
      state[i][col] = on;
      document.querySelector(`input[data-i="${i}"][data-col="${col}"]`).checked = on;
    }
    draw();
  });
  $('proteinStyle').addEventListener('change', draw);
  $('labels').addEventListener('change', draw);
  $('opacity').addEventListener('input', () => {
    const opacity = +$('opacity').value;
    $('opacityValue').textContent = Math.round(100 * opacity) + '%';
    for (const [i, id] of surfaces) viewer.setSurfaceMaterialStyle(id, {color: data.entries[i].colour, opacity});
    viewer.render();
  });
  $('reset').addEventListener('click', () => zoomLigands(400));

  $('rmsdNote').textContent = `The first entry, ${data.reference}, is the reference. RMSD: binding-pocket Cα atoms `
    + `(${data.reference} residues within ${data.pocket_cutoff ?? 8} Å of a ligand), outliers left out. `
    + '*: pocket residues moved > 2 Å from the reference (hover).';
  if (data.skipped?.length) { $('skippedBox').hidden = false; $('skipped').innerHTML = data.skipped.map(s => `<li>${esc(s.reason)}</li>`).join(''); }
  $('notes').innerHTML = (data.notes || []).map(n => `<li>${esc(n)}</li>`).join('');
  const residues = data.residues || [];
  $('cm').innerHTML = `<table><thead><tr><th></th>${residues.map(r => `<th><span>${esc(r)}</span></th>`).join('')}</tr></thead><tbody>${data.entries.map(e => {
    const hb = new Set(e.hbond_partners), ct = new Set(e.contacts);
    return `<tr><th><span class="sw" style="background:${esc(e.colour)}"></span>${esc(e.pdb_id)} · ${esc(short(e.name || e.het, 28))}</th>${residues.map(r => `<td class="${hb.has(r) ? 'h' : ct.has(r) ? 'c' : ''}" title="${esc(r)}${hb.has(r) ? ': hydrogen bond' : ct.has(r) ? ': contact' : ''}"></td>`).join('')}</tr>`;
  }).join('')}</tbody></table><p class="sub" style="margin-top:6px"><span class="sw" style="background:#9ecae1"></span>contact (≤ 4 Å) <span class="sw" style="background:#08519c;margin-left:12px"></span>hydrogen bond (N/O–N/O ≤ 3.5 Å), residues named as in ${esc(data.reference)}</p>`;

  draw();
  zoomLigands();
  if (app) app.sendSizeChanged({width: Math.ceil(window.innerWidth), height: Math.ceil(document.documentElement.getBoundingClientRect().height)});
  $('contacts').addEventListener('toggle', () => app?.sendSizeChanged({width: Math.ceil(window.innerWidth), height: Math.ceil(document.documentElement.getBoundingClientRect().height)}));
}

if (window.__OVERLAY_DATA__) {
  render(window.__OVERLAY_DATA__);
} else {
  app = new App({name: 'BindingDB Overlay', version: '1.0.0'}, {}, {autoResize: true});
  const text = r => r.content?.find(c => c.type === 'text')?.text;
  app.ontoolresult = async result => {
    if (result.isError) return status(text(result) || 'The overlay could not be made.');
    const id = result.structuredContent?.overlay_id;
    if (!id) return status('This result has no overlay.');
    try {
      const saved = await app.callServerTool({name: 'overlay_data', arguments: {overlay_id: id}});
      if (saved.isError) throw new Error(text(saved));
      render(saved.structuredContent);
    } catch (e) { status('Could not load the structures: ' + (e.message || e)); }
  };
  app.connect().catch(() => status('Open this overlay in an MCP Apps chat client, or open overlay.html from the overlay folder.'));
}
