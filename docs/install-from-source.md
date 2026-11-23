# Install from source

Most users should install the [Claude Desktop bundle](../README.md#quick-install-claude-desktop-bundle) instead.
Install from source to use the server from Claude Code, run a different BindingDB release, or work on the code.

1. **Install** [uv](https://docs.astral.sh/uv/), then clone the repository:

   ```bash
   git clone https://github.com/sbl-sdsc/mcp-bindingdb.git
   cd mcp-bindingdb
   ```

2. **Build the database** (downloads BindingDB's dump; about half an hour; about 3 GB of disk space while it builds and 1.8 GB afterwards):

   ```bash
   scripts/build_duckdb.sh
   ```

   You can also skip this step: without a database, the server builds the same one on first use, in
   `~/Library/Application Support/mcp-bindingdb` on macOS, `%LOCALAPPDATA%\mcp-bindingdb` on Windows and
   `~/.local/share/mcp-bindingdb` on Linux. See [Building the database](building-the-database.md) for releases and options.

3. **Add the server to Claude.**

   **Claude Desktop:** let Claude do it. Paste this prompt into a new Claude Desktop chat, and allow
   Claude to change the file when it asks:

   ```text
   Add the mcp-bindingdb MCP server to my Claude Desktop configuration.

   1. Find the mcp-bindingdb folder I cloned from GitHub: it contains a pyproject.toml with
      name = "mcp-bindingdb". If you find none, or more than one, ask me which folder to use.
   2. Find the full path of the uv program (`which uv` on macOS, `where uv` on Windows). Claude
      Desktop may not find "uv" by name, so use the full path.
   3. Open Claude Desktop's config file: ~/Library/Application Support/Claude/claude_desktop_config.json
      on macOS, %APPDATA%\Claude\claude_desktop_config.json on Windows. If it exists, save a backup copy
      next to it first; if it does not exist, create it.
   4. Inside "mcpServers" (create it if missing), add or replace only this entry, keeping every other
      server and setting exactly as it is:
        "mcp-bindingdb": {
          "command": "<full path of uv>",
          "args": ["--directory", "<the mcp-bindingdb folder>", "run", "--extra", "substructure",
                   "--extra", "opsin", "--extra", "structures", "mcp-bindingdb"]
        }
   5. Check that the file is still valid JSON, then show me the mcp-bindingdb entry and where the
      backup is. Do not restart Claude yourself.
   ```

   Then:

   1. **Restart Claude Desktop:** quit it completely (⌘Q on macOS; on Windows, quit it from the system
      tray) and open it again. Closing the window is not enough.
   2. **Allow the mcp-bindingdb tools:** select **Plugins** in the left sidebar. Click **mcp-bindingdb**, then
      **Settings**. Select **Always allow** for all tools (there are several sections), so Claude can look
      things up without asking you before every search.
   3. **Enable mcp-bindingdb in a chat:** in a new chat, click the **+** button and enable **mcp-bindingdb**.
   4. **Check it works:** in that chat, ask "Look up imatinib in BindingDB."

   **Claude Code:** the repository's `.mcp.json` registers the server when you run `claude` in this
   folder. To use it from any folder:

   ```bash
   claude mcp add --scope user mcp-bindingdb -- uv --directory /path/to/mcp-bindingdb run --extra substructure --extra opsin --extra structures mcp-bindingdb
   ```

If some tools are missing in a chat, check that they are switched on: in Claude Desktop, under **Plugins** in
the left sidebar → **mcp-bindingdb**, or in the chat's tools menu.

## Run a notebook

A notebook from [create_jupyter_notebook](tools.md#create_jupyter_notebook) comes in a folder with its own
`requirements.txt`, so it runs in an environment uv builds for it, not in this checkout's:

```bash
cd ~/results/imatinib-analogues
uv run --no-project --with-requirements requirements.txt --with jupyterlab jupyter lab imatinib-analogues.ipynb
```

To rerun every call on your database without opening Jupyter, writing a copy with the new results:

```bash
cd ~/results/imatinib-analogues
BINDINGDB_RERUN=1 BINDINGDB_DUCKDB=/path/to/mcp-bindingdb/data/bindingdb_<release>.duckdb \
  uv run --no-project --with-requirements requirements.txt --with nbconvert jupyter nbconvert --to notebook \
  --execute --output imatinib-analogues-rerun.ipynb imatinib-analogues.ipynb
```

The environment installs mcp-bindingdb from GitHub at the notebook's commit, so it does not see this
checkout's `data/`: name the database with `BINDINGDB_DUCKDB` (Claude's reply does). A notebook made while
the checkout has uncommitted changes, or a commit that is not pushed, gets a copy of the package instead.
