# JAK1 selectivity across the JAK family

A reproducible record of an AI-assisted BindingDB analysis with 3 tool calls, made by mcp-bindingdb v0.1.7.

- **Date:** 2026-11-22
- **Model:** claude-opus-5
- **Data:** BindingDB release **202610** (`BDB-mySQL_All_202610_dmp.zip`, SHA-256 `923415e9d990867d9f4f43dc6e674c173eb29ea18f496dea02a011e3d2f45690`)
- **Database build:** 2026-10-02T22:41:22+00:00, DuckDB 1.5.6
- **Derived data:** standard InChIKeys computed from SMILES by RDKit 2026.03.6; compound_property computed from SMILES (largest fragment) by RDKit 2026.03.6
- **Server:** mcp-bindingdb v0.1.7, commit [`4fad6d8e47a1`](https://github.com/pwrose/mcp-bindingdb/commit/4fad6d8e47a12cf81a3d235a82a744752ac14376)
- **Software:** python 3.12.7, duckdb 1.5.6, rdkit 2026.03.6, mcp 2.3.0, gemmi 0.7.5
- **Notebook generated:** 2026-11-23T05:37:38Z

## How to run

Keep the notebook in its folder, which holds everything it needs: `requirements.txt` (mcp-bindingdb at its commit and the versions of the packages it needs), the recorded results in `data/` and the figures in `figures/`. With [uv](https://docs.astral.sh/uv/), from that folder (replace the path with yours):

```bash
cd /path/to/3.6-family-selectivity-matrix-notebook
uv run --no-project --with-requirements requirements.txt --with jupyterlab jupyter lab 3.6-family-selectivity-matrix-notebook.ipynb
```

then choose Run → Run All Cells. The first start installs the packages, which takes a minute or two; the cells show the recorded results, so no database is needed. Without uv: `pip install -r requirements.txt jupyterlab`, then `jupyter lab 3.6-family-selectivity-matrix-notebook.ipynb` in the folder.

## How to rerun the calls

To rerun every BindingDB call on your own copy of release 202610 and check each result against the recorded one, set `RERUN = True` in the setup cell and run all cells, or rerun the notebook without opening Jupyter, writing a copy with the new results:

```bash
cd /path/to/3.6-family-selectivity-matrix-notebook
BINDINGDB_RERUN=1 uv run --no-project --with-requirements requirements.txt --with nbconvert jupyter nbconvert --to notebook --execute --output 3.6-family-selectivity-matrix-notebook-rerun.ipynb 3.6-family-selectivity-matrix-notebook.ipynb
```

A rerun needs the database: the one `BINDINGDB_DUCKDB=/path/to/bindingdb_202610.duckdb` names (put it before `uv run`), else the newest one mcp-bindingdb built on this computer, for example for Claude Desktop. With neither, the first rerun builds one, which takes about half an hour and 2.4 GB. To build exactly release 202610, with a clone of mcp-bindingdb:

```bash
git clone https://github.com/pwrose/mcp-bindingdb.git
cd mcp-bindingdb
git checkout 4fad6d8e47a12cf81a3d235a82a744752ac14376
scripts/build_duckdb.sh --release 202610
```

The setup cell checks the database's release and source checksum against the recorded ones.

## Contents

- `3.6-family-selectivity-matrix-notebook.ipynb`: the notebook: each prompt, a cell per BindingDB tool call with its recorded result, the answer and its figures, with the provenance and how to cite it
- `3.6-family-selectivity-matrix-notebook.html`: the notebook as a web page, with the results as recorded (when it was written)
- `requirements.txt`: the Python packages it runs with, at pinned versions
- `data/`: the result each call returned during the session (`call-NN.json`, for Call NN)
- `figures/figure-1.png`

## Caveats

- The recorded results are what this BindingDB release returned during the session. A rerun on another release, or of a call that reads PubChem, RCSB or PDBe, can differ; the notebook marks each such result ⚠️.
- Figures drawn by mcp-bindingdb are drawn again on a rerun; other images are kept as recorded.
