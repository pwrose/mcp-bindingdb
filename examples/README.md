# Example queries

Forty questions answered with the `mcp-bindingdb` tools against BindingDB release 202610, in eight levels from single lookups to multi-step workflows. Each is an HTML transcript written by `create_transcript`: the prompt, the answer, its figures, and structure drawings for the compounds it names (example 8.2 also lists every tool call). Some folders hold the plotting script and data behind a figure.

**[Browse the examples](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/index.html)**. GitHub shows HTML files as source, so the links below open a rendered view.

## Level 1 — Simple lookups

One question, one or two tools: find a compound or a target and read its record.

| # | Example |
|---|---|
| 1.1 | [Look up a compound by name (imatinib)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/01-simple-lookups/1.1-compound-by-name/1.1-compound-by-name.html) |
| 1.2 | [Look up a compound by identifier](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/01-simple-lookups/1.2-compound-by-identifier/1.2-compound-by-identifier.html) |
| 1.3 | [Look up a target by gene name (EGFR)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/01-simple-lookups/1.3-target-by-gene-name/1.3-target-by-gene-name.html) |
| 1.4 | [Turn a chemical name into a structure](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/01-simple-lookups/1.4-name-to-structure/1.4-name-to-structure.html) |

## Level 2 — Structure search

Search by chemical structure: exact match, similarity, substructure, SMARTS, and scaffold-to-target summaries.

| # | Example |
|---|---|
| 2.1 | [Exact structure search (the two enantiomers of crizotinib)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/02-structure-search/2.1-exact-structure/2.1-exact-structure.html) |
| 2.2 | [Similarity search: close analogues of imatinib](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/02-structure-search/2.2-similarity-search/2.2-similarity-search.html) |
| 2.3 | [Substructure search: how many quinazolines, and which are most potent?](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/02-structure-search/2.3-substructure-count-and-potency/2.3-substructure-count-and-potency.html) |
| 2.4 | [SMILES vs SMARTS queries (4-chloroaniline)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/02-structure-search/2.4-smiles-vs-smarts/2.4-smiles-vs-smarts.html) |
| 2.5 | [Scaffold → target landscape (imatinib core)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/02-structure-search/2.5-scaffold-target-landscape/2.5-scaffold-target-landscape.html) |
| 2.6 | [Draw a structure and search with the structure editor](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/02-structure-search/2.6-structure-editor/2.6-structure-editor.html) |

## Level 3 — Compound ↔ target

Which compounds hit a target, which targets a compound hits, and what lies behind a single measurement.

| # | Example |
|---|---|
| 3.1 | [Most potent ligands for a target (EGFR)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/03-compound-target/3.1-ligands-for-target/3.1-ligands-for-target.html) |
| 3.2 | [Selectivity profile of a drug (imatinib)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/03-compound-target/3.2-compound-selectivity-profile/3.2-compound-selectivity-profile.html) |
| 3.3 | [Mutant vs wild type (EGFR T790M)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/03-compound-target/3.3-mutant-vs-wild-type/3.3-mutant-vs-wild-type.html) |
| 3.4 | [Drill into one measurement (gefitinib on EGFR)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/03-compound-target/3.4-measurement-details/3.4-measurement-details.html) |
| 3.5 | [Protein complexes: GABA-A receptor subtypes](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/03-compound-target/3.5-protein-complexes/3.5-protein-complexes.html) |

## Level 4 — Series SAR

R-group tables, matched molecular pairs and activity cliffs: what one substituent does to potency, and when the data says something else.

| # | Example |
|---|---|
| 4.1 | [R-group table: the position that picks the COX isoform](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/04-series-sar/4.1-r-group-table/4.1-r-group-table.html) |
| 4.2 | [Matched molecular pairs: swapping a group, not an atom](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/04-series-sar/4.2-matched-pairs/4.2-matched-pairs.html) |
| 4.3 | [Activity cliffs: only the ones measured in the same patent](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/04-series-sar/4.3-activity-cliffs/4.3-activity-cliffs.html) |
| 4.4 | [Transformations across seven target classes, one document at a time](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/04-series-sar/4.4-transformations-by-target/4.4-transformations-by-target.html) |

## Level 5 — Multi-step workflows

Realistic analyses that chain several tools: repurposing, selectivity panels, hit expansion, safety, species, patents, target networks.

| # | Example |
|---|---|
| 5.1 | [From a drug to its analogues to their targets (sildenafil)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/05-workflows/5.1-repurposing-from-analogues/5.1-repurposing-from-analogues.html) |
| 5.2 | [Kinase selectivity panel of four BCR-ABL inhibitors](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/05-workflows/5.2-kinase-selectivity-panel/5.2-kinase-selectivity-panel.html) |
| 5.3 | [Hit expansion: from one screening hit to an SAR series](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/05-workflows/5.3-hit-expansion/5.3-hit-expansion.html) |
| 5.4 | [hERG liability: which known drugs block the channel?](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/05-workflows/5.4-herg-liability/5.4-herg-liability.html) |
| 5.5 | [Compare a target across species (human vs rat D2 receptor)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/05-workflows/5.5-species-comparison/5.5-species-comparison.html) |
| 5.6 | [Trace potent compounds to their patents (BTK inhibitors)](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/05-workflows/5.6-patent-provenance/5.6-patent-provenance.html) |
| 5.7 | [Imatinib's targets and the network they form](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/05-workflows/5.7-imatinib-target-network/5.7-imatinib-target-network.html) |
| 5.8 | [Clustered selectivity heat map and R-groups of the imatinib core](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/05-workflows/5.8-scaffold-selectivity-clustering/5.8-scaffold-selectivity-clustering.html) |

## Level 6 — Properties, efficiency and alerts

Computed compound properties: drug-likeness, ligand efficiency, Bemis-Murcko scaffolds and structural alerts, as filters and as answers.

| # | Example |
|---|---|
| 6.1 | [Drug-likeness radar: the DPP-4 inhibitors](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/06-properties/6.1-drug-likeness-radar/6.1-drug-likeness-radar.html) |
| 6.2 | [Ligand efficiency over time: BACE1 inhibitors](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/06-properties/6.2-ligand-efficiency/6.2-ligand-efficiency.html) |
| 6.3 | [Scaffold landscape and chemical space: PDE2A inhibitors](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/06-properties/6.3-scaffold-landscape/6.3-scaffold-landscape.html) |
| 6.4 | [PAINS triage: 5-lipoxygenase inhibitors](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/06-properties/6.4-pains-triage/6.4-pains-triage.html) |
| 6.5 | [Property-filtered analogue search: ibrutinib and BTK](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/06-properties/6.5-property-filtered-analogues/6.5-property-filtered-analogues.html) |

## Level 7 — SQL analytics

Direct SQL over the BindingDB tables, for questions the curated tools do not cover.

| # | Example |
|---|---|
| 7.1 | [Schema discovery: what tables are in BindingDB?](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/07-sql-analytics/7.1-schema-discovery/7.1-schema-discovery.html) |
| 7.2 | [Aggregate counts: the most-studied human targets](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/07-sql-analytics/7.2-aggregate-counts/7.2-aggregate-counts.html) |
| 7.3 | [Patent landscape in BindingDB](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/07-sql-analytics/7.3-patent-landscape/7.3-patent-landscape.html) |
| 7.4 | [Data quality: censored values](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/07-sql-analytics/7.4-data-quality-censored-values/7.4-data-quality-censored-values.html) |
| 7.5 | [ITC thermodynamics: ΔG, ΔH and −TΔS](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/07-sql-analytics/7.5-itc-thermodynamics/7.5-itc-thermodynamics.html) |
| 7.6 | [PDB cross-links: HIV-1 protease ligands with crystal structures](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/07-sql-analytics/7.6-pdb-cross-links/7.6-pdb-cross-links.html) |

## Level 8 — Deliverables

Saving the work: a Markdown transcript, and a reproducible record with every tool call.

| # | Example |
|---|---|
| 8.1 | [Save a conversation as a Markdown transcript](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/08-deliverables/8.1-markdown-transcript/8.1-markdown-transcript.html) |
| 8.2 | [A reproducible record with every tool call](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/08-deliverables/8.2-reproducible-record/8.2-reproducible-record.html) |

The answers point out data-quality issues where the results show them (duplicate records, values at detection limits, probable unit errors, re-reported values). Check these before relying on a single number.