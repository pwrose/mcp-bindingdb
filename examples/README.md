# Example queries

Twelve transcripts of questions answered with the `mcp-bindingdb` tools against BindingDB release 202610.
Each file shows the question, every tool call with its exact arguments (and SQL), the results (a readable
table plus the raw JSON in a collapsible block), and an answer written from those results.

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

The answers point out data-quality issues where the results show them (duplicate records, values at
detection limits, probable unit errors, wrong synonyms). Check these before relying on a single number.

## Regenerating

```bash
uv run python scripts/generate_examples.py              # all examples
uv run python scripts/generate_examples.py --only 05    # one example
```

The queries are defined in `EXAMPLES` in `scripts/generate_examples.py`. Each "## Answer" section is
written by hand. Regenerating keeps the answer and records a hash of the tool results. When a new data
release changes the results, the script prints `REVIEW <file>: results changed...` so you know which
answers to recheck. A new example gets a placeholder answer to fill in.
