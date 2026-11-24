# Example 6.1 — HIV-1 Protease Inhibitors with PDB Structures: Overlay of the Four Most Potent

A reproducible record of an AI-assisted BindingDB analysis with 5 tool calls, made by mcp-bindingdb v0.1.17.

- **Date:** 2026-11-23
- **Model:** claude-opus-5-5
- **Data:** BindingDB release **202611** (`BDB-mySQL_All_202611_dmp.zip`, SHA-256 `daea9260d404919a183ce02d91bf4b9c49b410bea7eaaeba105c8e0280510381`)
- **Database build:** 2026-11-21T01:08:15+00:00, DuckDB 1.5.6
- **Derived data:** standard InChIKeys computed from SMILES by RDKit 2026.03.6; compound_property computed from SMILES (largest fragment) by RDKit 2026.03.6
- **Server:** mcp-bindingdb v0.1.17, commit [`79dae5d22c0f`](https://github.com/sbl-sdsc/mcp-bindingdb/commit/79dae5d22c0f15b8ded9b49adc8b105f0463703a)
- **Software:** python 3.12.7, duckdb 1.5.6, rdkit 2026.03.6, mcp 2.3.0, gemmi 0.7.5
- **Notebook generated:** 2026-11-24T04:55:57Z

## How to run

Keep the notebook in its folder, which holds everything it needs: `requirements.txt` (mcp-bindingdb at its commit and the versions of the packages it needs), the recorded results in `data/`, the figures in `figures/` and the 3D viewers of the binding-site overlays in `overlays/`. With [uv](https://docs.astral.sh/uv/), from that folder (replace the path with yours):

```bash
cd /path/to/6.1-hiv1-protease-inhibitor-overlay-notebook
uv run --no-project --with-requirements requirements.txt --with jupyterlab jupyter lab 6.1-hiv1-protease-inhibitor-overlay-notebook.ipynb
```

then choose Run → Run All Cells. The first start installs the packages, which takes a minute or two; the cells show the recorded results, so no database is needed. Without uv: `pip install -r requirements.txt jupyterlab`, then `jupyter lab 6.1-hiv1-protease-inhibitor-overlay-notebook.ipynb` in the folder.

## How to rerun the calls

To rerun every BindingDB call on your own copy of release 202611 and check each result against the recorded one, set `RERUN = True` in the setup cell and run all cells, or rerun the notebook without opening Jupyter, writing a copy with the new results:

```bash
cd /path/to/6.1-hiv1-protease-inhibitor-overlay-notebook
BINDINGDB_RERUN=1 uv run --no-project --with-requirements requirements.txt --with nbconvert jupyter nbconvert --to notebook --execute --output 6.1-hiv1-protease-inhibitor-overlay-notebook-rerun.ipynb 6.1-hiv1-protease-inhibitor-overlay-notebook.ipynb
```

A rerun needs the database: the one `BINDINGDB_DUCKDB=/path/to/bindingdb_202611.duckdb` names (put it before `uv run`), else the newest one mcp-bindingdb built on this computer, for example for Claude Desktop. With neither, the first rerun builds one, which takes about half an hour and 2.4 GB. To build exactly release 202611, with a clone of mcp-bindingdb:

```bash
git clone https://github.com/sbl-sdsc/mcp-bindingdb.git
cd mcp-bindingdb
git checkout 79dae5d22c0f15b8ded9b49adc8b105f0463703a
scripts/build_duckdb.sh --release 202611
```

The setup cell checks the database's release and source checksum against the recorded ones.

## Contents

- `6.1-hiv1-protease-inhibitor-overlay-notebook.ipynb`: the notebook: each prompt, a cell per BindingDB tool call with its recorded result, the answer and its figures, with the provenance and how to cite it
- `6.1-hiv1-protease-inhibitor-overlay-notebook.html`: the notebook as a web page, with the results as recorded (when it was written)
- `requirements.txt`: the Python packages it runs with, at pinned versions
- `data/`: the result each call returned during the session (`call-NN.json`, for Call NN)
- `figures/figure-1.png`
- `overlays/call-05.html`: the 3D viewer of Call 5's binding-site overlay, which opens in any browser

## Caveats

- The recorded results are what this BindingDB release returned during the session. A rerun on another release, or of a call that reads PubChem, RCSB or PDBe, can differ; the notebook marks each such result ⚠️.
- Figures drawn by mcp-bindingdb are drawn again on a rerun; other images are kept as recorded.
