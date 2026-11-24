"""Copy the example transcripts from the working folder into examples/ and rebuild its index.

    python3 scripts/sync_examples.py                          # from ~/mcp-bindingdb-examples
    python3 scripts/sync_examples.py --source /path/to/folder
    python3 scripts/sync_examples.py --dry-run                # list what would change
    python3 scripts/sync_examples.py --index-only ~/mcp-bindingdb-examples

The examples are written in Claude sessions into a working folder (default ~/mcp-bindingdb-examples, or the
environment variable MCP_BINDINGDB_EXAMPLES) with one folder per level ('01-simple-lookups', ...) and one
folder per example inside it. Syncing replaces examples/<level>/ with the working copy (examples removed
there are removed here too), leaves out .DS_Store files, then writes examples/index.html. Files other
than the level folders and index.html are left alone.

The index links each example page relatively; GitHub Pages serves them from the main branch at
https://sbl-sdsc.github.io/mcp-bindingdb/examples/ (.nojekyll at the repository root: files as they are).
Links to other files (CSV, PNG, scripts, notebooks) point at GitHub, which shows them rendered.
--index-only writes the index of a working folder in place, with relative links throughout.

Pages are checked for absolute home-directory paths, which should not be published; any found are listed.
Nothing is committed.
"""

import argparse
import filecmp
import html
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
REPO_FILES_URL = "https://github.com/sbl-sdsc/mcp-bindingdb/blob/main/examples/"
SKIP = (".DS_Store", ".ipynb_checkpoints")  # neither copied into the repository nor compared
IGNORE = shutil.ignore_patterns(*SKIP)
LEVEL_FOLDER = re.compile(r"^\d\d-")
LOCAL_PATH = re.compile(rb"/Users/[A-Za-z]|/home/[A-Za-z]|/private/tmp/|[A-Z]:\\Users\\")

LEVELS = [
    ("01-simple-lookups", "Level 1 — Simple lookups",
     "One question, one or two tools: find a compound or a target and read its record."),
    ("02-structure-search", "Level 2 — Structure search",
     "Search by chemical structure: exact match, similarity, substructure, SMARTS, and scaffold-to-target summaries."),
    ("03-compound-target", "Level 3 — Compound ↔ target",
     "Which compounds hit a target, which targets a compound hits, and what lies behind a single measurement."),
    ("04-series-sar", "Level 4 — Series SAR",
     ("R-group tables, matched molecular pairs and activity cliffs: what one substituent does to potency, "
      "and when the data says something else.")),
    ("05-workflows", "Level 5 — Multi-step workflows",
     ("Realistic analyses that chain several tools: repurposing, selectivity panels, hit expansion, safety, species, "
      "patents, target networks, scaffold selectivity clustering.")),
    ("06-binding-sites", "Level 6 — Binding sites in 3D",
     ("PDB complexes of a target's ligands superposed on the binding site: poses, shared contacts and hydrogen "
      "bonds next to the measured potency. Each example has the transcript and the interactive 3D viewer.")),
    ("07-properties", "Level 7 — Properties, efficiency and alerts",
     ("Computed compound properties: drug-likeness, ligand efficiency, Bemis-Murcko scaffolds and structural "
      "alerts, as filters and as answers.")),
    ("08-sql-analytics", "Level 8 — SQL analytics",
     "Direct SQL over the BindingDB tables, for questions the curated tools do not cover."),
    ("09-deliverables", "Level 9 — Deliverables",
     "Saving the work: a Markdown transcript, and a reproducible record with every tool call."),
]

PAGE_STYLE = """
:root { --fg:#1f2328; --muted:#59636e; --bg:#ffffff; --card:#f6f8fa; --line:#d1d9e0; --accent:#0969da; --tag:#ddf4ff; --tagfg:#0550ae; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --fg:#e6edf3; --muted:#9198a1; --bg:#0d1117; --card:#151b23; --line:#3d444d; --accent:#4493f8; --tag:#0c2d6b; --tagfg:#9ecbff; } }
:root[data-theme="dark"] { --fg:#e6edf3; --muted:#9198a1; --bg:#0d1117; --card:#151b23; --line:#3d444d; --accent:#4493f8; --tag:#0c2d6b; --tagfg:#9ecbff; }
body { margin:0 auto; max-width:960px; padding:32px 16px 64px; font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; color:var(--fg); background:var(--bg); }
h1 { font-size:2em; margin:0 0 .3em; }
.lede { color:var(--muted); max-width:46em; }
h2 { font-size:1.35em; margin:2.2em 0 .2em; padding-bottom:.3em; border-bottom:1px solid var(--line); }
.intro { color:var(--muted); margin:.3em 0 1em; }
ol.cards { list-style:none; padding:0; margin:0; display:grid; gap:10px; }
.card { display:flex; gap:14px; background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px 14px; }
.num { font:600 14px ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--muted); min-width:2.2em; padding-top:2px; }
.body { min-width:0; flex:1; }
a { color:var(--accent); text-decoration:none; overflow-wrap:anywhere; }
a:hover { text-decoration:underline; }
a.title { font-weight:600; font-size:1.05em; }
blockquote { margin:.35em 0 .5em; padding:0 0 0 .8em; border-left:3px solid var(--line); color:var(--fg); font-style:italic; }
.tag { display:inline-block; font-size:12px; background:var(--tag); color:var(--tagfg); border-radius:999px; padding:1px 9px; margin:0 6px 4px 0; }
.files { font-size:12.5px; color:var(--muted); margin-top:2px; }
.viewer { font-size:13px; margin-top:4px; font-weight:600; }
.howto { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px 16px; margin-top:1.4em; }
.howto p { margin:.4em 0; }
footer { margin-top:3em; color:var(--muted); font-size:12.5px; }
"""


def text(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def natural_key(s: str) -> list:
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s)]


def parse_transcript(path: Path) -> tuple[str, str, list[str], str, str]:
    """Title, first prompt, tags, BindingDB release and mcp-bindingdb version of one HTML transcript. The
    release and version are "" for a transcript that records neither (an overlay's viewer page)."""
    src = path.read_text(encoding="utf-8")
    release = (re.search(r"BindingDB release:</strong>\s*([0-9]{6})", src) or [None, ""])[1]
    version = (re.search(r"Generated by:</strong>\s*mcp-bindingdb v([0-9][0-9.]*)", src) or [None, ""])[1]
    title = text(re.search(r"<title>(.*?)</title>", src, re.DOTALL).group(1))
    m = re.search(r"<strong>User</strong></p>\s*(.*?)<hr", src, re.DOTALL)
    prompt = text(m.group(1)) if m else ""
    tags = []
    if ">BindingDB tool calls<" in src:
        tags.append("tool calls")
    if re.search(r'<figure class="sg"', src):
        tags.append("structure grid")
    n_fig = len(re.findall(r'<img class="figure"', src))
    if n_fig:
        tags.append(f"{n_fig} plot" + ("s" if n_fig > 1 else ""))
    if re.search(r'<img class="structure"', src):
        tags.append("structures")
    n_user = src.count("<strong>User</strong>")
    if n_user > 1:
        tags.append(f"{n_user} turns")
    return title, prompt, tags, release, version


def collect(root: Path) -> list[tuple[str, str, str, list[dict]]]:
    """The examples of each level: (folder, heading, intro, [example])."""
    levels = []
    for folder, heading, intro in LEVELS:
        level = root / folder
        if not level.is_dir():
            continue
        examples = []
        for ex in sorted((p for p in level.iterdir() if p.is_dir()), key=lambda p: natural_key(p.name)):
            pages = sorted(p.name for p in ex.glob("*.html"))
            if not pages:
                continue
            main = f"{ex.name}.html" if f"{ex.name}.html" in pages else pages[0]
            title, prompt, tags, release, version = parse_transcript(ex / main)
            # A notebook from create_jupyter_notebook sits in a folder of its own with the files it needs.
            notebook = next((nb for sub in sorted(ex.iterdir()) if sub.is_dir()
                             for nb in sorted(sub.glob("*.ipynb"))), None)
            if notebook is not None:
                tags.append("notebook")
            examples.append({
                "num": ex.name.split("-")[0],
                "title": re.sub(r"^Example\s+[\d.]+\s+—\s+", "", title),
                "prompt": prompt, "tags": tags, "release": release, "version": version,
                "href": f"{folder}/{ex.name}/{main}",
                "extras": [f"{folder}/{ex.name}/{f.name}" for f in sorted(ex.iterdir())
                           if f.is_file() and f.name != main and not f.name.startswith(".") and f.suffix != ".html"],
                # other HTML pages (an overlay's 3D viewer): linked like the transcript, so they open rendered
                "pages": [f"{folder}/{ex.name}/{name}" for name in pages if name != main],
                "notebook": None if notebook is None else {
                    "ipynb": f"{folder}/{ex.name}/{notebook.parent.name}/{notebook.name}",
                    "page": (f"{folder}/{ex.name}/{notebook.parent.name}/{notebook.stem}.html"
                             if notebook.with_suffix(".html").is_file() else None)},
            })
        if examples:
            levels.append((folder, heading, intro, examples))
    unknown = sorted(p.name for p in root.iterdir() if p.is_dir() and LEVEL_FOLDER.match(p.name)
                     and p.name not in {f for f, _, _ in LEVELS})
    if unknown:
        print(f"warning: level folders not in LEVELS, left out of the index: {', '.join(unknown)}", file=sys.stderr)
    return levels


def page_label(path: str) -> str:
    """How the index names an example's second HTML page."""
    return "Interactive 3D viewer" if path.endswith("overlay-viewer.html") else "Interactive page"


def span(values: set[str], one: str, many: str, sep: str = " ") -> str:
    """"release 202610" for a single value, "releases 202610-202611" for several: the examples are rerun a few
    at a time, so the set they were generated against drifts apart and no single value describes them. Sorted
    with natural_key, so v0.1.10 ends up above v0.1.9 rather than below it."""
    seen = sorted((v for v in values if v), key=natural_key)
    if not seen:
        return ""
    return f"{one}{sep}{seen[0]}" if len(seen) == 1 else f"{many}{sep}{seen[0]}–{seen[-1]}"


def build_index(root: Path, files_base_url: str = "") -> int:
    """Write root/index.html; returns the number of examples."""
    levels = collect(root)
    total = sum(len(examples) for *_, examples in levels)
    every = [e for *_, examples in levels for e in examples]
    releases = span({e["release"] for e in every}, "release", "releases")
    versions = span({e["version"] for e in every}, "v", "v", sep="")
    sections = []
    for _, heading, intro, examples in levels:
        cards = []
        for e in examples:
            tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in e["tags"])
            files = "".join(f'<div class="viewer">{page_label(page)}: <a href="{html.escape(page)}">'
                            f'{html.escape(page.rsplit("/", 1)[1])}</a></div>' for page in e["pages"])
            if e["extras"]:
                links = ", ".join(f'<a href="{html.escape(files_base_url + f)}">{html.escape(f.rsplit("/", 1)[1])}</a>'
                                  for f in e["extras"])
                files += f'<div class="files">Also in this folder: {links}</div>'
            if nb := e["notebook"]:  # the .ipynb itself only renders on GitHub, not on Pages
                rendered = f'<a href="{html.escape(nb["page"])}">rendered</a> &middot; ' if nb["page"] else ""
                files += (f'<div class="viewer">Jupyter notebook: {rendered}'
                          f'<a href="{html.escape(files_base_url + nb["ipynb"])}">'
                          f'{html.escape(nb["ipynb"].rsplit("/", 1)[1])}</a></div>')
            cards.append(f'''<li class="card">
  <div class="num">{html.escape(e["num"])}</div>
  <div class="body">
    <a class="title" href="{html.escape(e["href"])}">{html.escape(e["title"])}</a>
    <blockquote>{html.escape(e["prompt"])}</blockquote>
    <div class="tags">{tags}</div>
    {files}
  </div>
</li>''')
        sections.append(f'<section><h2>{html.escape(heading)}</h2><p class="intro">{html.escape(intro)}</p>'
                        f'<ol class="cards">{"".join(cards)}</ol></section>')
    with_calls = [e["num"] for *_, examples in levels for e in examples if "tool calls" in e["tags"]]
    calls_note = (f" (Example {', '.join(with_calls)})" if with_calls else "")
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mcp-bindingdb Examples</title>
<style>{PAGE_STYLE}</style>
</head>
<body>
<h1>mcp-bindingdb Examples</h1>
<p class="lede">Worked examples for new users of the BindingDB MCP server. They start with one-line lookups and build up to multi-step analyses. Each example is a real conversation: the prompt, the answer, a short lesson about the data, the tools that were used, and what to try next. They were run against BindingDB {releases}; a newer release can give somewhat different numbers.</p>
<div class="howto">
<p><strong>How to use these.</strong> Read the transcript, then paste the quoted prompt into your own chat with mcp-bindingdb connected and compare. Transcripts show the tool calls only where the prompt asks for them{calls_note}. Tables that carry SMILES are drawn as structures.</p>
<p><strong>Check the data.</strong> The answers point out data-quality issues where the results show them (duplicate records, values at detection limits, probable unit errors, re-reported values). Check these before relying on a single number.</p>
</div>
{"".join(sections)}
<footer>Generated from the transcripts in this folder · BindingDB {releases} · mcp-bindingdb {versions}</footer>
</body>
</html>
'''
    (root / "index.html").write_text(page, encoding="utf-8")
    return total


def differences(src: Path, dst: Path) -> tuple[list[str], list[str], list[str]]:
    """Files added, changed and removed going from dst to src (relative paths, SKIP ignored)."""
    def files(d: Path) -> set[str]:
        if not d.exists():
            return set()
        paths = (p.relative_to(d) for p in d.rglob("*") if p.is_file())
        return {str(rel) for rel in paths if not any(part in SKIP for part in rel.parts)}
    a, b = files(src), files(dst)
    changed = [f for f in sorted(a & b) if not filecmp.cmp(src / f, dst / f, shallow=False)]
    return sorted(a - b), changed, sorted(b - a)


def local_paths(root: Path) -> list[str]:
    """Text files under root that contain an absolute home-directory or temp path."""
    hits = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".html", ".md", ".py", ".csv", ".json", ".txt"}:
            data = p.read_bytes()
            # base64 images in the pages can contain anything; look only outside data: URIs
            data = re.sub(rb"data:[a-z/+.-]+;base64,[A-Za-z0-9+/=]+", b"", data)
            if LOCAL_PATH.search(data):
                hits.append(str(p.relative_to(root)))
    return sorted(hits)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path,
                        default=Path(os.environ.get("MCP_BINDINGDB_EXAMPLES", "~/mcp-bindingdb-examples")),
                        help="Working folder with the level folders (default ~/mcp-bindingdb-examples)")
    parser.add_argument("--dry-run", action="store_true", help="Only list what would change")
    parser.add_argument("--index-only", type=Path, metavar="FOLDER",
                        help="Only write FOLDER/index.html, with relative links (for the working folder)")
    args = parser.parse_args()

    if args.index_only:
        folder = args.index_only.expanduser()
        print(f"{folder / 'index.html'}: {build_index(folder)} examples")
        return

    source = args.source.expanduser()
    levels = sorted(p.name for p in source.iterdir() if p.is_dir() and LEVEL_FOLDER.match(p.name)) \
        if source.is_dir() else []
    if not levels:
        sys.exit(f"{source}: no level folders (01-..., 02-...) found")
    stale = sorted(p.name for p in EXAMPLES.iterdir() if p.is_dir() and LEVEL_FOLDER.match(p.name)
                   and p.name not in levels) if EXAMPLES.exists() else []

    added, changed, removed = [], [], []
    for level in levels:
        a, c, r = differences(source / level, EXAMPLES / level)
        added += [f"{level}/{f}" for f in a]
        changed += [f"{level}/{f}" for f in c]
        removed += [f"{level}/{f}" for f in r]
    for level in stale:
        removed += [f"{level}/{f}" for f in differences(source / level, EXAMPLES / level)[2]]
    for label, files in (("added", added), ("changed", changed), ("removed", removed)):
        for f in files:
            print(f"{label:8} {f}")
    print(f"{len(added)} added, {len(changed)} changed, {len(removed)} removed")

    hits = local_paths(source)
    hits = [h for h in hits if LEVEL_FOLDER.match(h)]
    if hits:
        print("warning: these files contain absolute local paths; check them before committing:", file=sys.stderr)
        for h in hits:
            print(f"  {h}", file=sys.stderr)
    if args.dry_run:
        return

    EXAMPLES.mkdir(exist_ok=True)
    for level in stale:
        shutil.rmtree(EXAMPLES / level)
    for level in levels:
        if (EXAMPLES / level).exists():
            shutil.rmtree(EXAMPLES / level)
        shutil.copytree(source / level, EXAMPLES / level, ignore=IGNORE)
    total = build_index(EXAMPLES, files_base_url=REPO_FILES_URL)
    print(f"wrote examples/index.html ({total} examples); nothing committed")


if __name__ == "__main__":
    main()
