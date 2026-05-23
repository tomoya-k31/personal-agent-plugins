# personal-agent-plugins

tomoya-k31's personal Claude Code plugin marketplace.

This repository hosts a collection of [Claude Code](https://claude.com/claude-code) plugins maintained by [@tomoya-k31](https://github.com/tomoya-k31). It is structured as a Claude Code **plugin marketplace** — a directory tree with `.claude-plugin/marketplace.json` at the root that Claude Code can ingest to discover and install the plugins under `plugins/`.

tomoya-k31 個人の Claude Code プラグインを束ねたマーケットプレイス。`.claude-plugin/marketplace.json` を入口として、`plugins/` 配下の各プラグインを Claude Code から導入・有効化できる。

---

## Repository layout

```
.
├── .claude-plugin/
│   └── marketplace.json          # Marketplace manifest (lists the plugins below)
├── .claude/
│   └── settings.json             # Project-local Claude Code settings (used when working *on* this repo)
├── .mcp.json                     # MCP servers used while developing the plugins
└── plugins/
    └── interaction-logger/       # See plugin's own README for details
        ├── .claude-plugin/
        │   └── plugin.json
        ├── hooks/
        │   ├── hooks.json
        │   └── log-interactions.sh
        └── README.md
```

The shape that matters to Claude Code is:

- **Marketplace root** = `.claude-plugin/marketplace.json` at the repo root.
- **Each plugin** lives under `plugins/<name>/` and contains its own `.claude-plugin/plugin.json` plus any `commands/`, `agents/`, `skills/`, `hooks/`, etc.

## Included plugins

| Plugin | Category | Description |
| --- | --- | --- |
| [`interaction-logger`](plugins/interaction-logger/README.md) | observability | Logs every user prompt, every `AskUserQuestion` option presented and answered, and every permission OK/NG to a daily-rotated JSONL file under `~/.claude/logs/`. |

Add new plugins by creating `plugins/<your-plugin>/` and appending an entry to `.claude-plugin/marketplace.json`.

---

## Installing plugins from this marketplace

> Quick mental model: Claude Code never streams plugin code from GitHub at runtime. `/plugin marketplace add <owner>/<repo>` clones the marketplace into `~/.claude/plugins/marketplaces/` **once**, then copies a snapshot into `~/.claude/plugins/cache/` and reads from there. Third-party marketplaces have `autoUpdate` **disabled by default** (only `claude-plugins-official` defaults to `true`), so installed plugin code is frozen until you explicitly run `/plugin marketplace update` or set `"autoUpdate": true`.

For everyday use, install from GitHub. For developing/debugging plugins in this repo, use one of the local methods in the next section instead.

### Option A — From GitHub (everyday use)

Inside Claude Code, register the marketplace and install a plugin:

```text
/plugin marketplace add tomoya-k31/personal-agent-plugins
/plugin install interaction-logger@personal-agent-plugins
/reload-plugins
```

`/plugin marketplace add <owner>/<repo>` clones this repo under `~/.claude/plugins/marketplaces/personal-agent-plugins/` and reads `.claude-plugin/marketplace.json`. The marketplace name (`personal-agent-plugins`) comes from the `name` field of that manifest.

### Option B — Pinned in project settings

To share the marketplace + plugin set with everyone who checks out a repo, add this to that repo's **`.claude/settings.json`** (project scope — not `~/.claude/settings.json`):

```json
{
  "extraKnownMarketplaces": {
    "personal-agent-plugins": {
      "source": {
        "source": "github",
        "repo": "tomoya-k31/personal-agent-plugins"
      },
      "autoUpdate": false
    }
  },
  "enabledPlugins": {
    "interaction-logger@personal-agent-plugins": true
  }
}
```

When a teammate trusts the folder, Claude Code prompts them to install the marketplace and plugin. `"autoUpdate": false` is the default for third-party marketplaces — written explicitly here so it's obvious.

> Note: `extraKnownMarketplaces` with `source: "directory"` only auto-discovers from **project-scope** `.claude/settings.json`, not from user-scope `~/.claude/settings.json` (see "Known gotchas" below).

### Verifying the install

```text
/plugin                                 # UI lists enabled plugins + their on-disk path
/plugin marketplace list                # Lists personal-agent-plugins
```

Or from the shell:

```bash
ls ~/.claude/plugins/marketplaces/personal-agent-plugins/
ls ~/.claude/plugins/cache/personal-agent-plugins/
jq '.enabledPlugins' ~/.claude/settings.json
```

Each plugin may have its own runtime requirements — check the plugin's own README. For example, `interaction-logger` needs `jq` (and optionally `coreutils` for `gdate` on macOS).

### Updating and removing

```text
/plugin marketplace update personal-agent-plugins   # Re-pull from GitHub
/plugin uninstall interaction-logger@personal-agent-plugins
/plugin marketplace remove personal-agent-plugins
```

`/plugin marketplace remove` also uninstalls every plugin that came from that marketplace.

### Security

Plugins execute arbitrary code with your user privileges. Only add marketplaces you trust. Org admins can hard-lock the allowlist via the managed-settings `strictKnownMarketplaces` field; a corresponding `blockedMarketplaces` denylist is also enforced on every add/install/update/refresh.

---

## Debugging plugins (local-first workflow)

> The big realization: **Claude Code reads installed plugins from `~/.claude/plugins/cache/`, not from your working copy.** Editing files in this repo while a plugin is installed from GitHub will not change runtime behavior. For debugging you want a workflow where Claude Code reads from the source tree you're editing.

### Method 1 — `--plugin-dir` (recommended for active development)

The official, ephemeral way to load a plugin without installing it:

```bash
claude --plugin-dir ./plugins/interaction-logger
```

This loads exactly that plugin (manifest + commands + agents + skills + hooks + MCP) for **this session only**. No marketplace registration, no cache copy, nothing persisted to `~/.claude/settings.json`. If a plugin with the same name is already installed from a marketplace, `--plugin-dir` takes precedence for this session.

Repeat the flag to load multiple plugins:

```bash
claude --plugin-dir ./plugins/interaction-logger --plugin-dir ./plugins/some-other-plugin
```

Edited a file? Run `/reload-plugins` inside the session — no restart needed. This reloads skills, agents, hooks, MCP servers, and LSP servers.

### Method 2 — Local marketplace via `/plugin marketplace add`

Use this when you want the full marketplace install flow (multiple plugins, enable/disable UI) but pointing at your working copy instead of GitHub:

```text
/plugin marketplace add /absolute/path/to/personal-agent-plugins
/plugin install interaction-logger@personal-agent-plugins
/reload-plugins
```

Important: pass an **absolute path**. Local-path marketplaces have `autoUpdate` disabled by default, so the cache won't refresh on its own — re-run `/plugin marketplace update personal-agent-plugins` after editing, or use Method 3.

### Method 3 — Cache symlink trick (longest iteration loop)

If you must install through the normal marketplace flow but still want edit-in-place behaviour, replace the cache directory with a symlink to your working copy:

```bash
PLUGIN=interaction-logger
MKT=personal-agent-plugins
VERSION=$(jq -r '.version' plugins/$PLUGIN/.claude-plugin/plugin.json)

CACHE=~/.claude/plugins/cache/$MKT/$PLUGIN/$VERSION
mv "$CACHE" "${CACHE}.bak"
ln -s "$PWD/plugins/$PLUGIN" "$CACHE"
```

From now on `/reload-plugins` reads straight from your repo. When you're done, `rm "$CACHE" && mv "${CACHE}.bak" "$CACHE"` restores the original.

This is **un**documented officially — use it only as a fallback when `--plugin-dir` doesn't fit (e.g. you need to debug something that breaks under the symlink-vs-fresh-checkout difference).

---

### Investigation cheatsheet

Work from the cheapest check to the most invasive.

#### 1. Run Claude Code in debug mode

```bash
claude --debug --plugin-dir ./plugins/interaction-logger
```

`--debug` prints hook invocations, command discovery, MCP server startup, and permission decisions to stderr. Fastest way to see *why* a hook didn't fire or a command didn't appear.

#### 2. Confirm what Claude Code actually loaded

```text
/plugin
```

The UI shows each enabled plugin, which marketplace it came from, and **the absolute path on disk Claude Code is reading it from**. If that path is under `~/.claude/plugins/cache/…` and you're editing the source repo, you have a cache-mismatch bug — switch to Method 1 or 3.

#### 3. Validate manifests

```bash
jq . .claude-plugin/marketplace.json
jq . plugins/<name>/.claude-plugin/plugin.json
jq . plugins/<name>/hooks/hooks.json
```

Invalid JSON silently breaks loading. Also:

```bash
claude plugin validate .          # Validates the marketplace at the current dir
```

The official `plugin-dev` plugin (enabled in this repo's `.claude/settings.json`) also exposes a `/plugin-validator` agent for structural checks.

#### 4. Exercise hooks directly

Hook scripts read event JSON from stdin and exit `0`. Replay an event without going through Claude Code at all:

```bash
echo '{
  "hook_event_name": "UserPromptSubmit",
  "session_id": "test-session",
  "cwd": "'"$PWD"'",
  "prompt": "hello"
}' | bash plugins/interaction-logger/hooks/log-interactions.sh

tail -n1 ~/.claude/logs/interactions-$(date +%Y-%m-%d).jsonl | jq .
```

If the script writes the expected JSON line, the bug is in how Claude Code is matching/dispatching events (check `hooks.json` matchers), not the script itself.

#### 5. Read the live transcript

```bash
ls -lt ~/.claude/projects/<project-slug>/   # one transcript JSONL per session
```

Hook payloads, tool calls, and permission events are all there — grep for the event name to see what Claude Code actually delivered.

#### 6. Reload, don't restart

After any source edit:

```text
/reload-plugins
```

This picks up changes to commands, agents, skills, hooks, plugin MCP servers, and plugin LSP servers without exiting the session. Restart is only necessary if `/reload-plugins` itself reports an error you can't explain.

### Common failure modes

| Symptom | Likely cause |
| --- | --- |
| Plugin not in `/plugin` list | Marketplace not added, or `enabledPlugins` not set, or typo in `name@marketplace`. |
| Hook never fires | Matcher in `hooks.json` doesn't match the tool name, or the event name itself is wrong. Verify with `claude --debug`. |
| Script runs but produces no log | The script swallows errors (intentional in `interaction-logger`). Re-run with `bash -x` to see what failed. |
| Edits to repo files don't take effect | Claude Code is reading from `~/.claude/plugins/cache/…`, not your working copy. Use `claude --plugin-dir <path>` or the symlink trick above. |
| `${CLAUDE_PLUGIN_ROOT}` resolves wrong | Only valid inside hooks/commands defined by the plugin manifest — don't rely on it in unrelated scripts. |
| Local `directory` marketplace silently missing | See "Known gotchas" below. |

### Known gotchas with `source: "directory"`

The `directory` marketplace source is officially marked "for development only" and has several rough edges worth knowing before you adopt it for daily use:

- **User-scope settings don't auto-discover it.** `extraKnownMarketplaces` with `source: "directory"` only triggers the install prompt from **project-scope** `.claude/settings.json`. Listing it in `~/.claude/settings.json` won't add the marketplace on startup (anthropics/claude-code #26861).
- **Absolute paths can silently fail.** On some Linux setups, an absolute `path` is not discovered until you change it to a relative path (also #26861). Workaround: relative path from project root, or a symlink.
- **Relative paths resolve from the main repo root, not the worktree root.** If you use git worktrees, `path: "./marketplace"` will look in your main checkout regardless of which worktree you launched Claude Code from (anthropics/claude-code #49669).
- **Relative paths stored literally.** A `path: "./"` in `extraKnownMarketplaces` is written verbatim to `known_marketplaces.json` instead of being resolved (anthropics/claude-code #23978).

For active debugging, prefer `claude --plugin-dir` over `directory` marketplaces — `--plugin-dir` doesn't depend on any of the above resolving correctly.

---

## Developing a new plugin in this repo

1. Create `plugins/<your-plugin>/.claude-plugin/plugin.json` with `name`, `version`, `description`, and optional `author`.
2. Add components at the **plugin root** (NOT inside `.claude-plugin/`):
   - `commands/*.md` — slash commands
   - `agents/*.md` — sub-agents
   - `skills/<name>/SKILL.md` — skills
   - `hooks/hooks.json` (+ scripts) — event hooks
   - `.mcp.json` — MCP servers
3. Iterate with `claude --plugin-dir ./plugins/<your-plugin>` (see Debugging Method 1). Use `/reload-plugins` to pick up edits without restarting.
4. Once stable, add an entry for the plugin to `.claude-plugin/marketplace.json` and commit.
5. Use `${CLAUDE_PLUGIN_ROOT}` whenever a hook or command needs an absolute path inside the plugin — it makes the plugin location-independent.

The official `plugin-dev`, `skill-creator`, and `claude-md-management` plugins are enabled in this repo's `.claude/settings.json`, so the matching slash commands (`/create-plugin`, `/skill-creator`, etc.) are available when developing here.

## MCP servers

`.mcp.json` defines three MCP servers used while developing in this repo: `brave-search`, `exa`, and `context7`. They require the following env vars to be set in your shell before launching Claude Code:

- `BRAVE_API_KEY`
- `EXA_API_KEY`
- `CONTEXT7_API_KEY`

These are scoped to **developing on this repository** — they are not bundled with any of the plugins shipped from here.

## License

No license file is currently published. Treat the code as "all rights reserved" until one is added.
