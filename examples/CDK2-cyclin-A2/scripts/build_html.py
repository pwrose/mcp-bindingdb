import base64, json, pandas as pd, html
from pathlib import Path
S=json.load(open('stats.json'))
ct=pd.read_csv('chemotype_table.csv')
df=pd.read_csv('compounds_ct.csv')
rg=open('chemotype.py').read().split('RULES = [')[1].split(']\n')[0]
def b64(p): return base64.b64encode(Path(p).read_bytes()).decode()
PROMPT = Path('prompt.txt').read_text()
import gzip
IPT_CSS = Path('interactive.css').read_text()
IPT_JS  = Path('interactive.js').read_text()
IPT_DATA = base64.b64encode(gzip.compress(Path('points.json').read_bytes(),9)).decode()

def fig(path,num,title,cap,cls='',interactive=None):
    live=f'<div class="ipt-wrap" id="{interactive}"></div>' if interactive else ''
    img=(f'<div class="static-fallback"><img src="data:image/png;base64,{b64(path)}" '
         f'alt="{html.escape(title)}"></div>')
    return f"""<figure class="{cls}">
{live}{img}
<figcaption><b>Figure {num}.</b> {cap}</figcaption></figure>"""

rows="\n".join(
 f"<tr><td>{html.escape(r.chemotype)}</td><td class=n>{r.n}</td><td class=n>{r.med:.2f}</td>"
 f"<td class=n>{r.best:.2f}</td><td>{html.escape(str(r.best_cpd))}</td></tr>"
 for r in ct.itertuples())

data_rows="\n".join(
 f"<tr><td>{html.escape(str(r.compound_name))}</td><td>{html.escape(r.chemotype)}</td>"
 f"<td class=n>{'&gt;' if r.relation=='>' else ('&lt;' if r.relation=='<' else '')}{r.value:g}</td>"
 f"<td class=n>{r.pKi:.2f}</td><td class=n>{int(r.n_measurements)}</td>"
 f"<td class=s>{html.escape(r.smiles_std)}</td></tr>"
 for r in df.sort_values('pKi',ascending=False).itertuples())

refs="\n".join(f"<li><a href='https://doi.org/{d}'>{d}</a> ({y})</li>" for d,y in S['refs'])

HTML=f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CDK2/cyclin A2 Ki Chemotypes</title>
<style>
:root{{color-scheme:light;--surface:#fcfcfb;--plane:#f9f9f7;--ink:#0b0b0b;
--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--rule:#c3c2b7;--accent:#2a78d6;
--code:#f2f1ec;--border:rgba(11,11,11,.10)}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;
--surface:#1a1a19;--plane:#0d0d0d;--ink:#fff;--ink2:#c3c2b7;--muted:#898781;
--grid:#2c2c2a;--rule:#383835;--accent:#3987e5;--code:#232320;--border:rgba(255,255,255,.10)}}}}
:root[data-theme="dark"]{{color-scheme:dark;--surface:#1a1a19;--plane:#0d0d0d;--ink:#fff;
--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--rule:#383835;--accent:#3987e5;
--code:#232320;--border:rgba(255,255,255,.10)}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--plane);color:var(--ink);
font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1120px;margin:0 auto;padding:48px 16px 96px}}
h1{{font-size:1.9rem;line-height:1.2;margin:0 0 .3em;letter-spacing:-.02em}}
h2{{font-size:1.25rem;margin:2.6em 0 .6em;padding-bottom:.3em;
border-bottom:1px solid var(--rule)}}
h3{{font-size:1rem;margin:1.8em 0 .4em}}
.lede{{color:var(--ink2);font-size:1.05rem;margin:0 0 1.5em}}
.meta{{color:var(--muted);font-size:.82rem;margin-bottom:2.4em}}
figure{{margin:1.8em 0;background:var(--surface);border:1px solid var(--border);
border-radius:10px;padding:14px}}
figure img{{width:100%;height:auto;display:block;border-radius:4px}}
figcaption{{color:var(--ink2);font-size:.84rem;margin-top:.9em;line-height:1.5}}
figure.tall img{{max-height:none}}
table{{border-collapse:collapse;width:100%;font-size:.85rem;margin:1.2em 0;
background:var(--surface);border:1px solid var(--border);border-radius:8px}}
th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--grid)}}
th{{color:var(--ink2);font-weight:600;font-size:.78rem;text-transform:uppercase;
letter-spacing:.04em;position:sticky;top:0;background:var(--surface)}}
td.n{{text-align:right;font-variant-numeric:tabular-nums}}
td.s{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.72rem;
color:var(--muted);max-width:420px;overflow-wrap:anywhere}}
tr:last-child td{{border-bottom:none}}
pre,code{{background:var(--code);border-radius:6px}}
code{{padding:.12em .35em;font-size:.86em}}
pre{{padding:14px 16px;overflow-x:auto;font-size:.78rem;line-height:1.5;
border:1px solid var(--border)}}
pre code{{background:none;padding:0}}
blockquote{{margin:0;padding:14px 18px;background:var(--surface);
border-left:3px solid var(--accent);border-radius:0 8px 8px 0;
white-space:pre-wrap;font-size:.88rem;color:var(--ink2)}}
.scroll{{max-height:460px;overflow:auto;border:1px solid var(--border);
border-radius:8px}}
.scroll table{{border:none;margin:0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
gap:12px;margin:1.4em 0}}
.tile{{background:var(--surface);border:1px solid var(--border);border-radius:10px;
padding:14px 16px}}
.tile .v{{font-size:1.6rem;font-weight:650;letter-spacing:-.02em;display:block}}
.tile .k{{color:var(--muted);font-size:.76rem;text-transform:uppercase;
letter-spacing:.05em}}
.inline-core{{float:right;width:210px;margin:0 0 10px 18px}}
a{{color:var(--accent)}}
ul,ol{{padding-left:1.3em}} li{{margin:.3em 0}}
.note{{font-size:.86rem;color:var(--ink2);background:var(--surface);
border:1px solid var(--border);border-left:3px solid var(--rule);
border-radius:0 8px 8px 0;padding:12px 16px;margin:1.2em 0}}
@media (max-width:640px){{.inline-core{{float:none;width:60%;margin:0 auto 12px;display:block}}}}
{IPT_CSS}
</style></head><body><main>

<h1>Chemotype landscape of CDK2/cyclin A2 K<sub>i</sub> ligands</h1>
<p class="lede">{S['n_cpd']} compounds with K<sub>i</sub> measured against the intact
human CDK2–cyclin A2 complex, classified by rule-based chemotype and projected into
two chemical-space embeddings.</p>
<p class="meta">Source: BindingDB (local MCP mirror), complex 97 ·
{S['n_meas']} measurements from {S['n_art']} primary references,
{S['years'][0]}–{S['years'][1]} · Generated 3 October 2026</p>

<div class="grid">
<div class="tile"><span class="v">{S['n_cpd']}</span><span class="k">compounds</span></div>
<div class="tile"><span class="v">12</span><span class="k">chemotypes</span></div>
<div class="tile"><span class="v">{S['pki'][0]}–{S['pki'][2]}</span><span class="k">pK<sub>i</sub> range</span></div>
<div class="tile"><span class="v">{S['n_cens']}</span><span class="k">censored bounds</span></div>
</div>

<h2>1 · The request</h2>
<blockquote>{html.escape(PROMPT)}</blockquote>

<h2>2 · Target selection and data retrieval</h2>
<p>BindingDB holds three complexes whose name matches CDK2 with cyclin A2. Only one
is the intact pair of full-length human sequences:</p>
<table><thead><tr><th>Complex</th><th>Components</th><th>K<sub>i</sub> records</th>
<th>Used</th></tr></thead><tbody>
<tr><td>97</td><td>CDK2 P24941 (298 aa) + cyclin A2 P20248 (432 aa)</td>
<td class=n>164</td><td>yes</td></tr>
<tr><td>92</td><td>CDK2 P24941 + cyclin A2 <b>[171–432]</b> truncated</td>
<td class=n>2</td><td>no — truncated</td></tr>
<tr><td>304</td><td>CDK2 P24941 + cyclin A2 <b>[177–432]</b> truncated</td>
<td class=n>0</td><td>no — truncated</td></tr>
<tr><td>50014798</td><td>CDK2 P24941 + cyclin A2 P30274 (430 aa)</td>
<td class=n>0</td><td>no — no K<sub>i</sub></td></tr>
<tr><td>50000025</td><td>cyclin A1 + cyclin A2 + CDK2 (ternary)</td>
<td class=n>0</td><td>no — not the binary complex</td></tr>
</tbody></table>
<p>Both components of complex 97 carry full UniProt-length sequences
(no <code>[start-end]</code> construct suffix), so the set is exactly the intact
CDK2/cyclin A2 complex. Query:</p>
<pre><code>SELECT a.monomerid, a.relation, a.value, a.unit, a.p_affinity,
       a.compound_name, a.inchi_key, a.doi, a.year, c.smiles
FROM activity a LEFT JOIN compound c USING (monomerid)
WHERE a.complexid = 97 AND a.affinity_type = 'Ki'</code></pre>

<h3>Collapsing to one record per compound</h3>
<p>All 164 values are in nM. Records were sorted by K<sub>i</sub> ascending, with
exact (<code>=</code>) relations preferred over censored ones at equal value, and the
first row per <code>monomerid</code> kept — i.e. the <b>strongest reported
K<sub>i</sub></b>. One compound had two measurements; the other 162 had one each,
giving {S['n_cpd']} unique compounds. Salts were stripped to the largest organic
fragment and SMILES re-canonicalised. Affinity is reported as
pK<sub>i</sub> = 9 − log<sub>10</sub>(K<sub>i</sub>/nM); the {S['n_cens']} censored
records (12 &ldquo;&gt;&rdquo;, 1 &ldquo;&lt;&rdquo;) are kept but flagged, and are
treated as bounds rather than point estimates throughout.</p>

<h2>3 · Chemotype assignment</h2>
<p>Chemotypes are assigned by an <b>ordered list of SMARTS rules</b> matched against
the ring system — first match wins — so every class carries a chemically meaningful
name rather than a cluster index. Fused polycyclic cores are tested before
monocyclic ones, and the hinge-binding heterocycle that defines a published series
takes precedence over its peripheral rings. The rules classify all
{S['n_cpd']} compounds with no residual &ldquo;Other&rdquo;.</p>
<pre><code>RULES = [{html.escape(rg)}]</code></pre>
<div class="note">A SMARTS caveat worth recording: a branch written after a ring
closure attaches to the <em>last</em> atom of the ring, not the first. Writing the
thiazolylpyrimidine rule as <code>c1scnc1-c1ccnc(N)n1</code> therefore places the
pyrimidine on thiazole C4 and matches nothing; <code>s1cncc1-c1ccnc([#7])n1</code>
places it on C5 and matches the 85-member series.</div>
<table><thead><tr><th>Chemotype</th><th>n</th><th>Median pK<sub>i</sub></th>
<th>Best pK<sub>i</sub></th><th>Most potent member</th></tr></thead>
<tbody>{rows}</tbody></table>

<h2>4 · Chemical space: Morgan fingerprints and t-SNE</h2>
<p>Morgan fingerprints (radius 2, 2048 bits) were computed for each standardised
structure, a full 163×163 <b>Tanimoto distance</b> matrix (1 − similarity) was built
from them, and t-SNE was run directly on that matrix
(<code>metric='precomputed'</code>, perplexity 20, 2000 iterations, seed 42). Mean
pairwise Tanimoto distance is 0.75, so the set is chemically diverse. Both panels
share identical coordinates, so a point sits in the same place in each.</p>
{fig('fig1_tsne.png',1,'t-SNE of CDK2 ligands',
 'Morgan/Tanimoto t-SNE of the 163 compounds, rendered live from the embedded data. '
 '<b>(A)</b> Coloured by rule-assigned chemotype, with marker shape as a redundant '
 'channel so identity never rests on colour alone. <b>(B)</b> The same coordinates '
 'coloured by pK<sub>i</sub> on a single-hue sequential ramp; open rings mark censored '
 'measurements, whose colour reflects a bound rather than a point estimate. '
 'Chemotypes resolve into distinct islands, confirming that the SMARTS rules track the '
 'fingerprint neighbourhood structure. Potency is not uniform across the map: the '
 'pyrido[3,4-d]pyrimidine island (right) is systematically weaker than the '
 'thiazolylpyrimidine territory it faces. '
 '<b>Click any point</b> for its structure and full measurement record; click a legend '
 'entry to filter a chemotype in or out; the panels are keyboard-navigable with the '
 'arrow keys. A static version of this figure is in <code>figures/fig1_tsne.png</code>.',
 interactive='fig1-interactive')}

<h2>5 · Most potent members, aligned on the defining core</h2>
<p>For each chemotype the three strongest compounds are shown. The most potent member
of each class is depicted first and its 2D coordinates are used as the
<b>alignment template</b>: the remaining members are laid out with
<code>GenerateDepictionMatching2DStructure</code> against that template, matched on
the chemotype's own SMARTS, and the matched atoms and bonds are highlighted. Each row
therefore presents its core in one fixed orientation, and what differs between the
depictions is substitution rather than drawing. Exact measurements are ranked ahead of
censored ones, which are shown with their inequality.</p>
{fig('fig2_chemotype_grid.png',2,'Top 3 per chemotype',
 'Top three compounds per chemotype (rows), aligned and highlighted on the '
 'substructure that defines the class; each row is headed by its chemotype and the '
 'highlight carries that chemotype\'s colour and marker from the Figure 1 legend. Recognisable reference chemistry falls out in '
 'the expected places — staurosporine and UCN-01 as the indolocarbazoles, NU-6102 as '
 'the purine, AT-7519 as the pyrazole carboxamide, and palbociclib '
 '(K<sub>i</sub> &gt; 5 µM) correctly at the bottom of the set as a CDK4/6-selective '
 'drug.','tall')}

<h2>6 · IRIS projection with affinity as the radial coordinate</h2>
<p>IRIS performs the same kind of nonlinear embedding as t-SNE or UMAP, but takes a
scalar per point that it maps to the <b>radius</b>, leaving the manifold structure to
the angular coordinate. Passing pK<sub>i</sub> in place of a timestamp turns the
layout into an affinity-stratified map: potency increases outward, while angular
position still reflects fingerprint neighbourhood. The same 2048-bit Morgan
fingerprints were used as input, with <code>n_neighbors=15</code> and
<code>rho=0</code> so that radius is <em>linear</em> in pK<sub>i</sub> and the rings
are evenly spaced (the default adaptive rho spreads points over the annulus but makes
the radial axis hard to read).</p>
<div class="note"><b>Known bug worked around.</b>
<a href="https://github.com/BIDS-Xu-Lab/IRIS/issues/1">IRIS issue #1</a>: with fewer
than ~1000 points, a thread can be allocated fewer than 100 points,
<code>(hi-lo)/100</code> evaluates to zero, and the progress-counter modulo raises a
floating-point exception that kills the process. At n=163 this fires reliably. IRIS
was built from source with both occurrences of the pattern in
<code>LargeVis/LargeVis.cpp</code> guarded:
<code>(i-lo) % std::max&lt;long long&gt;(1, (hi-lo)/100)</code> at the ANN-query
progress line, and the same guard on <code>n_samples/10000000</code> in the
checkpoint block, which fails identically once the first is fixed. No other change
was made to the algorithm.</div>
{fig('fig3_iris.png',3,'IRIS projection',
 'IRIS projection of the same fingerprints with pK<sub>i</sub> as the radial '
 'coordinate, rendered live; rings are labelled in pK<sub>i</sub> units and potency '
 'increases outward. Angular sectors recover the chemotypes — the '
 'pyrido[3,4-d]pyrimidines occupy a contiguous wedge, as do the pyrrole-2-carboxamides '
 '— while the radial axis makes the potency ceiling of each series directly readable: '
 'the indolocarbazoles sit at the perimeter, the tetrahydroquinazolines stay near the '
 'centre. <b>Click any point</b> for its structure and measurement record; the legend '
 'filters chemotypes. A static version is in <code>figures/fig3_iris.png</code>.',
 interactive='fig3-interactive')}

<h2>7 · R-group decomposition of the pyrido[3,4-d]pyrimidines</h2>
<img class="inline-core" src="data:image/png;base64,{b64('fig4_core.png')}"
 alt="Pyrido[3,4-d]pyrimidine core with R1, R2, R3 labelled">
<p>The 24-member pyrido[3,4-d]pyrimidine series was decomposed against the fused
bicyclic core <code>c1cc2cncnc2cn1</code> using RDKit's
<code>RGroupDecomposition</code> with <code>onlyMatchAtRGroups=False</code> and the
greedy-chunks matching strategy. All 24 compounds matched with none left over,
resolving into three substitution points: <b>R1</b> at C8, <b>R2</b> at C2 and
<b>R3</b> at C6 (locants read off the returned core
<code>c1nc([*:2])nc2c([*:1])nc([*:3])cc12</code>).</p>
<p>Within each position the unique R-groups are ranked by <b>median pK<sub>i</sub></b>
of the compounds bearing them. Because the series is small and unevenly distributed —
one R1 group accounts for 12 of 24 compounds while most appear once — each bar also
carries its n and, where n &gt; 1, a min–max range line. Single-occurrence groups at
the top of a ranking are one measurement, not an established trend.</p>
{fig('fig4_rgroups.png',4,'R-group decomposition',
 'R-group decomposition of the pyrido[3,4-d]pyrimidine series, ranked within each '
 'position by median pK<sub>i</sub>. R2 carries the clearest signal: the '
 '4-methyl-1,2,4-triazol-3-yl / methoxyaniline combination reaches a median of 7.64 '
 'against 5.30 for the fused bicyclic triazole at the bottom of the same position, a '
 'spread of over two log units from the arylamine alone. R1 tolerates a wide range of '
 'branched and cyclic amines within roughly one log unit, with the neopentylamine that '
 'dominates the series (n=12) sitting mid-rank — a deliberate scaffold constant rather '
 'than an optimised choice. R3 barely moves the needle.','tall')}

<h2>8 · Methods summary</h2>
<ol>
<li><b>Retrieval</b> — BindingDB <code>activity</code> table, <code>complexid=97</code>,
<code>affinity_type='Ki'</code>; complex membership verified against
<code>complex_component</code> and <code>polymer</code> to exclude truncated
constructs and ternary complexes.</li>
<li><b>Curation</b> — largest-fragment standardisation
(<code>rdMolStandardize.LargestFragmentChooser</code>), canonical SMILES, one record
per compound at the strongest K<sub>i</sub>, censored relations flagged.</li>
<li><b>Descriptors</b> — Morgan fingerprints, radius 2, 2048 bits
(<code>rdFingerprintGenerator</code>).</li>
<li><b>Chemotypes</b> — ordered SMARTS rule list, first match wins, verified to leave
no unclassified compound.</li>
<li><b>t-SNE</b> — scikit-learn, precomputed Tanimoto distance matrix, perplexity 20,
2000 iterations, random init, seed 42.</li>
<li><b>Depictions</b> — CoordGen 2D coordinates; per-chemotype template alignment via
<code>AllChem.GenerateDepictionMatching2DStructure</code> with the chemotype SMARTS as
<code>refPatt</code>; core atoms and bonds highlighted.</li>
<li><b>IRIS</b> — built from source at
<a href="https://github.com/BIDS-Xu-Lab/IRIS">BIDS-Xu-Lab/IRIS</a> with the issue-#1
division-by-zero guard applied; binary fingerprint matrix as input, pK<sub>i</sub> as
the scalar coordinate, <code>n_neighbors=15</code>, <code>rho=0</code>,
<code>return_polar=True</code>.</li>
<li><b>R-groups</b> — <code>rdRGroupDecomposition</code>, greedy-chunks strategy,
<code>onlyMatchAtRGroups=False</code>, <code>removeHydrogensPostMatch=True</code>.</li>
<li><b>Figures</b> — matplotlib with a colourblind-validated categorical palette for
chemotypes and a single-hue sequential ramp for pK<sub>i</sub>; because 12 classes
exceed what colour alone can separate under an all-pairs scatter criterion, marker
shape and direct labelling carry identity alongside colour.</li>
</ol>

<h2>9 · Limitations</h2>
<ul>
<li>K<sub>i</sub> values are pooled across {S['n_art']} publications spanning
{S['years'][0]}–{S['years'][1]}, with different assay formats, ATP concentrations and
analysis methods. Cross-series comparisons carry inter-laboratory variance that the
within-series rankings do not.</li>
<li>Keeping the strongest reported K<sub>i</sub> per compound is a best-case summary;
it biases upward where replicates disagree. Only one compound here had replicates, so
the effect is negligible in this set.</li>
<li>Censored values are plotted at their bound. The 12 &ldquo;&gt;&rdquo; records are
weaker than shown, and ranking treats them as the value stated.</li>
<li>Chemotypes with n = 1–3 give medians and rankings that are descriptive only.</li>
<li>IRIS builds its neighbour graph with its own internal metric on the bit vectors,
not Tanimoto, so Figure 3's angular structure is not strictly comparable to Figure 1's
Tanimoto-based layout.</li>
<li>Only the intact CDK2/cyclin A2 complex is covered. Compounds measured solely
against CDK2 alone, truncated cyclin A2, or as IC<sub>50</sub>/K<sub>d</sub> are out of
scope by construction — the complex holds 3069 IC<sub>50</sub> and 116 K<sub>d</sub>
records that this K<sub>i</sub>-only analysis does not touch.</li>
</ul>

<h2>10 · Compound data</h2>
<div class="scroll"><table><thead><tr><th>Compound</th><th>Chemotype</th>
<th>K<sub>i</sub> (nM)</th><th>pK<sub>i</sub></th><th>#meas</th><th>SMILES</th>
</tr></thead><tbody>{data_rows}</tbody></table></div>

<h2>Primary references</h2>
<ol>{refs}</ol>
<p class="meta" style="margin-top:2.5em">Data from BindingDB. Analysis performed with
RDKit, scikit-learn and IRIS.</p>
</main>
<script type="application/octet-stream" id="ipt-data">{IPT_DATA}</script>
<script>{IPT_JS}</script>
</body></html>"""
Path('CDK2_cyclinA2_chemotypes.html').write_text(HTML)
print('bytes',len(HTML))
