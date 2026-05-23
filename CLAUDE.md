# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is a **Claude Code plugin marketplace** (`personal-agent-plugins`), not application code. It hosts plugins under `plugins/<name>/` and registers them in `.claude-plugin/marketplace.json`. Currently shipped:

- `interaction-logger` — Hooks that log prompts / AskUserQuestion options / permission events to `~/.claude/logs/interactions-YYYY-MM-DD.jsonl`. Includes the `analyze-interactions` skill (DuckDB-backed analyzer).
- `skill-creator-x` — Meta-skill for guided Skill authoring with Exa research, eval loop, and packaging scripts.

## Plugin editing workflow

**Always bump `version` in `plugins/<name>/.claude-plugin/plugin.json` after touching anything inside that plugin directory.** Installed plugins are cached at `~/.claude/plugins/cache/<marketplace>/<name>/<version>/` keyed by version string, so leaving the version unchanged causes `auto-update` to skip — clients keep running the stale cached copy even after `git pull`. Bumping the version is what forces refresh. (Past incident: the initial `interaction-logger@0.1.0` install was stuck without the `skills/` directory because subsequent commits never bumped the version.)

### Version resolution order

Claude Code resolves a plugin's cache-key version from the first of these that is set ([plugins-reference docs](https://code.claude.com/docs/en/plugins-reference#version-management)):

1. `plugins/<name>/.claude-plugin/plugin.json` → `version` (highest priority — *plugin.json wins*)
2. `.claude-plugin/marketplace.json` → `plugins[].version` for that plugin entry (fallback)
3. Git commit SHA of the plugin source (used only when both above are omitted and the source is git-hosted)
4. `unknown` (npm sources or local directories not inside a git repo — no auto-update)

Practical rules for this repo:

- We rely on (1) — every plugin sets `version` in its own `plugin.json`, so that's the field to bump.
- The `marketplace.json` entries in this repo intentionally **do not** declare `version` (see `.claude-plugin/marketplace.json`). If you ever add one, remember it must be bumped too whenever `plugin.json`'s version is bumped — keeping two in sync is error-prone, so prefer leaving the marketplace entry's `version` unset.
- If you want commit-SHA-driven auto-refresh (no manual bumping), you'd need to **remove `version` from both `plugin.json` and the marketplace entry** for that plugin. We don't do this today, but it's an option for fast-iteration plugins.
- `marketplace.json` also has a top-level `version` (and `metadata.version` for backward compat) — that is the **marketplace manifest** version, *not* a per-plugin cache key. Bumping it does **not** trigger per-plugin refresh; ignore it for the iteration loop below.

Iteration loop:
1. Edit files under `plugins/<name>/`.
2. Bump `plugins/<name>/.claude-plugin/plugin.json` `version` (SemVer; patch bump is fine for most changes).
3. Test live: `claude --plugin-dir ./plugins/<name>` reads from the source tree, bypassing the marketplace cache.
4. In an open session, `/reload-plugins` picks up edits without restarting.
5. Commit directly to `main` (個人リポなので PR 不要、main 直 commit OK).

When adding a **new plugin**: create `plugins/<new-name>/.claude-plugin/plugin.json`, then add an entry to `.claude-plugin/marketplace.json` `plugins[]` with `source: "./plugins/<new-name>"`.

## Hook conventions (this repo)

- File: `plugins/<name>/hooks/hooks.json`. Shape: top-level `description` + `hooks` keyed by event name (`UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PermissionRequest`, `PermissionDenied`, `Stop`).
- Each hook command uses `${CLAUDE_PLUGIN_ROOT}` (expands to the plugin dir at runtime) — never hard-code paths.
- `matcher` is a **regex** against the tool name, not a glob. Empty string = match all.
- Default `timeout: 5` seconds. Hooks must exit 0; failures are silent.
- `interaction-logger` uses a single dispatcher script (`log-interactions.sh`) that branches on `.hook_event_name` from stdin JSON. Follow this pattern for multi-event plugins.

## Skill conventions (this repo)

- Layout: `plugins/<plugin>/skills/<skill-name>/SKILL.md` + optional `scripts/`, `references/`, `assets/`, `agents/`.
- SKILL.md frontmatter requires `name` and `description`. Add `disable-model-invocation: true` to make the skill user-trigger-only.
- **`skill-creator-x` is manual-only** (`disable-model-invocation: true`). Never auto-invoke it; only run when the user explicitly types `/skill-creator-x` or asks to create a skill via it.
- Keep SKILL.md ≤500 lines; push detail to `references/` and behavior to `scripts/`.

## Runtime dependencies

The plugins shell out — these must be on PATH for the corresponding feature to work:

- `jq` — required by `interaction-logger` hook dispatcher.
- `duckdb` (≥1.5) — required by `analyze-interactions` skill (`scripts/run.sh`). Skill fails silently without it.
- Python 3 — used by `skill-creator-x` scripts (`run_eval`, `aggregate_benchmark`, `package_skill`, `run_loop`, etc.). Invoke as `python -m scripts.<name>` from the skill directory.
- `gdate` (GNU coreutils) — optional for ms-precision timestamps; falls back to BSD `date` (seconds) on macOS.

All of the above are installed on this dev machine (via Homebrew / mise). No need to `which`-check them per session.

## Interaction logs

`interaction-logger` writes one JSONL file per day at `~/.claude/logs/interactions-YYYY-MM-DD.jsonl`. Daily rotation, no size cap, no automatic pruning — the user manages cleanup manually. The directory is gitignored via `.gitignore` (`.claude/logs/`). Schema: one event per line with `event` ∈ {`user_prompt`, `ai_offered_options`, `user_selected_option`, `permission_request`, `tool_executed`, `permission_denied`, `ai_response_end`}, plus `ts` (ISO-8601 UTC), `session_id`, `cwd`. See `plugins/interaction-logger/README.md` for full field reference.

## MCP servers (development only)

`.mcp.json` declares `brave-search`, `exa`, and `context7` for **development on this repo**, not for the published plugins. They require the following env vars: `BRAVE_API_KEY`, `EXA_API_KEY`, `CONTEXT7_API_KEY`. If missing, the server fails to start — verify env before assuming an MCP tool is broken. Servers are pulled fresh via `npx -y` each run, no version pinning.

## Verifying changes

This repo has no test runner, linter, or build step. Verify edits by:
- Running the live hook: `echo '{...stdin event JSON...}' | bash plugins/interaction-logger/hooks/log-interactions.sh` (use a real event payload from an existing log line).
- Loading the plugin in isolation: `claude --plugin-dir ./plugins/<name>`.
- For `skill-creator-x` scripts: `cd plugins/skill-creator-x/skills/skill-creator-x && python -m scripts.quick_validate <skill-path>`.
