# Example queries

Twelve transcripts of questions answered with the `mcp-bindingdb` tools against BindingDB release 202610.
Each file shows the question, every tool call with its exact arguments (and SQL), the results (a readable
table plus the raw JSON in a collapsible block), and an answer written from those results.

Example 13 is a different kind: a standalone HTML report that combines BindingDB data with RDKit,
scikit-learn and IRIS analysis, with its scripts and data alongside (see [Reports](#reports)).

| # | Question | Tools used | What it shows |
|---|---|---|---|
| [01](01-egfr-most-potent-ki.md) | Most potent Ki ligands for wild-type human EGFR | `search_targets`, `find_ligands_for_target` | Resolving a gene name to a target; wild type vs mutants |
| [02](02-imatinib-target-profile.md) | Targets imatinib binds below 100 nM | `search_compounds`, `find_targets_for_compound` | Selectivity profile; spotting single-measurement outliers |
| [03](03-egfr-mutant-selectivity.md) | Compounds selective for EGFR T790M/L858R over wild type | `search_targets`, `run_sql` | Custom SQL across two targets; implausible values |
| [04](04-identify-compound-by-inchikey.md) | What compound is InChIKey BNRNXUUZRGQAQC-UHFFFAOYSA-N? | `search_compounds`, `get_compound` | Structure lookup; PDE5 vs PDE6 off-target activity |
| [05](05-herg-liability.md) | Distribution of hERG potency; share of potent blockers | `search_targets`, `get_target`, `run_sql` | Aggregation over censored (`<`, `>`) values |
| [06](06-measurement-provenance.md) | Where the most potent BTK IC50 comes from | `find_ligands_for_target`, `get_activity` | Assay conditions and patent citation; tight-binding limit check |
| [07](07-binding-kinetics-residence-time.md) | Longest residence times (1/koff) | `describe_tables`, `run_sql` | Schema discovery; sparse kinetic data |
| [08](08-cdk2-cyclin-e-complex.md) | CDK2/cyclin E composition and best inhibitors | `search_targets`, `get_target`, `find_ligands_for_target` | Multi-protein complex targets |
| [09](09-sars-cov-2-inhibitors.md) | Most potent SARS-CoV-2 inhibitors | `search_targets`, `run_sql`, `find_ligands_for_target` | Recovering from an empty search; likely unit error |
| [10](10-kras-g12c-data-growth.md) | Growth of KRAS G12C data; papers vs patents | `search_targets`, `run_sql` | How curation choices shape an answer |
| [11](11-patent-dataset-summary.md) | Summarize the patent data | `run_sql` | Whole-database aggregation; patents vs other sources; censored values |
| [12](12-most-recently-added-targets.md) | The 5 most recently added targets | `run_sql`, `search_targets`, `get_target` | Defining "added" from deposition dates; new protein vs new construct; missing organism |
| [13](CDK2-cyclin-A2/CDK2_cyclinA2_chemotypes.html) | Chemotype landscape of CDK2/cyclin A2 Ki ligands ([supplementary files](CDK2-cyclin-A2/)) | BindingDB data + RDKit, scikit-learn, IRIS | Choosing the intact complex over truncated constructs; SMARTS chemotypes; t-SNE of Morgan fingerprints; IRIS map with pKi as radius; R-group decomposition |

The answers point out data-quality issues where the results show them (duplicate records, values at
detection limits, probable unit errors, wrong synonyms). Check these before relying on a single number.

## Reports

[CDK2_cyclinA2_chemotypes.html](CDK2-cyclin-A2/CDK2_cyclinA2_chemotypes.html) is a self-contained HTML
page (plots embedded) that includes the prompt that produced it. GitHub shows HTML as source, so download
it and open it in a browser. The prompt asked for every compound with a Ki against the intact
CDK2/cyclin A2 complex (target 97), chemotypes assigned by SMARTS rules, a t-SNE map of Morgan
fingerprints coloured by chemotype and by Ki, the top 3 compounds per chemotype aligned on their core,
an [IRIS](https://github.com/BIDS-Xu-Lab/IRIS) map with pKi as the radius, and an R-group decomposition
of the pyrido[3,4-d]pyrimidine series.

The [CDK2-cyclin-A2](CDK2-cyclin-A2/) folder also holds the supplementary files:

- `figures/`: the figures as PNG files
- `data/`: compound tables with chemotypes and t-SNE coordinates, the chemotype summary, and the R-group table
- `scripts/`: the Python scripts that built the analysis and the page, and the prompt (`prompt.txt`)
- `iris_issue1.patch`: the fix applied to IRIS for [issue #1](https://github.com/BIDS-Xu-Lab/IRIS/issues/1)
  (a division by zero on small datasets)

The report is not produced by `generate_examples.py` and is not updated when the data release changes.

## Regenerating

```bash
uv run python scripts/generate_examples.py              # all examples
uv run python scripts/generate_examples.py --only 05    # one example
```

The queries are defined in `EXAMPLES` in `scripts/generate_examples.py`. Each "## Answer" section is
written by hand. Regenerating keeps the answer and records a hash of the tool results. When a new data
release changes the results, the script prints `REVIEW <file>: results changed...` so you know which
answers to recheck. A new example gets a placeholder answer to fill in.
