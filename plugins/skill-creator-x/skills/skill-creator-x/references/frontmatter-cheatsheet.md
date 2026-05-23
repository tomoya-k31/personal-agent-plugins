# Skill frontmatter cheatsheet

The YAML frontmatter at the top of `SKILL.md` controls every aspect of how a skill is discovered, loaded, and run. Only `name` (auto-derived from directory if absent) is strictly required; `description` is required in practice because it is the **triggering mechanism**.

## The full field list

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | yes-ish | Display identifier. Kebab-case, lowercase + digits + hyphens, max 64 chars. No leading/trailing or doubled hyphens. Defaults to directory name. |
| `description` | strongly recommended | Primary triggering signal. Tells Claude **what the skill does** and **when to use it**. Max 1,024 chars. **Must not contain `<` or `>`** (enforced by `quick_validate.py`). Be "pushy". |
| `when_to_use` | optional | Additional trigger context. Appended to `description`; combined cap 1,536 chars. |
| `argument-hint` | optional | Autocomplete display, e.g. `[issue-number]`. |
| `arguments` | optional | Named positional arguments (space-separated string or YAML list) for `$name` substitution. |
| `disable-model-invocation` | optional | `true` → no automatic invocation. Manual `/<name>` only. Also blocks subagent preload. |
| `user-invocable` | optional | `false` → hide from the `/` menu. Use for background knowledge. |
| `allowed-tools` | optional | Tools auto-approved while this skill is active. Space-separated or YAML list. |
| `model` | optional | Override the session model when this skill is active. |
| `effort` | optional | `low` / `medium` / `high` / `xhigh` / `max`. |
| `context` | optional | `fork` → run the skill in a forked subagent context. |
| `agent` | optional | The subagent type used when `context: fork`. |
| `hooks` | optional | Lifecycle hooks scoped to this skill. |
| `paths` | optional | Glob patterns. Skill auto-loads when matching files are touched (overlaps `.claude/rules/`). |
| `shell` | optional | `bash` (default) or `powershell` for inline `!`command`` substitution. |
| `license` | optional | SPDX or text. |
| `compatibility` | optional | Free-form requirements (e.g., "requires MCP exa configured"). Max 500 chars. |
| `metadata` | optional | Arbitrary nested metadata. |

`quick_validate.py` (bundled in `scripts/`) enforces the strict subset: `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`. Other fields are tolerated but not validated. Keep your frontmatter to fields you actually need.

### Caveat: `context: fork` + `agent:` in plugin-distributed skills

If the skill will be packaged into a plugin (rather than installed directly under `.claude/skills/`), `context: fork` paired with a bare `agent: <name>` is **silently ignored** on Claude Code ≤ 2.1.112 (issues #49559 and #35054). Workaround: use the namespaced form `agent: <plugin>:<agent-name>` so the fork resolves the agent from the same plugin. Test the fork behavior end-to-end before shipping.

## Substitution variables

Use these in the SKILL.md body to template at runtime.

| Variable | Resolves to |
|----------|-------------|
| `$ARGUMENTS` | All arguments concatenated |
| `$ARGUMENTS[N]` / `$N` | 0-based positional argument |
| `$name` | A named argument declared in `arguments:` |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_EFFORT}` | Current effort level |
| `${CLAUDE_SKILL_DIR}` | Directory containing this `SKILL.md` |

## Dynamic context injection (the `!` syntax)

Skills can run shell commands **before being sent to Claude**, substituting the output inline:

```markdown
The current git branch is !`git rev-parse --abbrev-ref HEAD`.

Recent commits:
```!
git log --oneline -5
```
```

The command runs in the user's shell with the `shell:` setting. Claude sees only the substituted output, not the command. Useful for "current state" context that should not be cached into the skill body.

Disabled in some enterprise environments via `disableSkillShellExecution: true`. If portability matters, prefer instructing Claude to run the command via `Bash` instead.

## Writing the `description`

This is the single most important field. Treat it as the skill's pitch to a busy Claude session.

### Structure that works

`"[Verb-phrase of what the skill does]. [Concrete trigger phrases: "Use this skill whenever the user mentions X, Y, or wants to Z"]. [Optional disambiguation against other skills]."`

### Anti-patterns

- **Too narrow**: "Generates pptx files." — misses related phrases like "make a slide deck".
- **Too vague**: "Helps with documents." — Claude cannot decide when to invoke it.
- **Self-deprecating**: "Maybe useful for…". Claude undertriggers; do not give it more reasons to.
- **Wall of text**: hard cap 1,024 chars. The `description` is in every session — burning context.

### "Pushy" works because Claude undertriggers

Default Claude behavior is to **not** invoke a skill unless the match is obvious. To counter, write descriptions that explicitly call out implicit contexts:

> "Build internal dashboards. **Use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard'.**"

### When to use `when_to_use` instead of stuffing `description`

If you need >1,024 chars of trigger context, split into `description` (the core pitch) + `when_to_use` (extended context, contexts to skip, disambiguation). They concatenate for triggering purposes (1,536 cap).

## `allowed-tools` — safety budget

Skills inherit the parent session's tool permission rules, but `allowed-tools` lets a skill **expand** auto-approval. Use cautiously.

### Safe to include freely
- `Read`, `Grep`, `Glob`, `LSP` — read-only inspection.
- `WebFetch` for specific known-safe URLs (note: `WebFetch` doesn't accept URL scoping in `allowed-tools`).

### Require justification
- `Bash` — broad blast radius. Prefer scoping with the `Bash(<command>:*)` syntax in `.claude/settings.json` instead.
- `Write`, `Edit`, `NotebookEdit` — silent file changes.
- `WebSearch` — generally fine, but accumulates cost.

### MCP tool names
Use the fully prefixed form: `mcp__exa__web_search_exa`, not `web_search_exa`.

## Skill `paths:` vs `.claude/rules/`

Both auto-load on file pattern matches. The differences:

| Aspect | `paths:` (skill frontmatter) | `.claude/rules/` |
|--------|------------------------------|------------------|
| Location | Inside a skill | `.claude/rules/*.md` |
| Field name | `paths:` | `paths:` (NOT `globs:` — see note) |
| Lazy-load requirement | `paths:` alone | `paths:` **plus** `alwaysApply: false` |
| Body content | Full skill body (potentially long) | Typically short rule files |
| Portability | Travels with the skill | Project-bound |
| Triggering | Skill's full body loads | Just the rule file loads |

**Important — `.claude/rules/` field name**: the official documented field is `paths:`, not `globs:`. The `globs:` form circulating in community examples is broken (per Claude Code issue #45587, it loads the rule at session start without scoping). Always use `paths:` and pair it with `alwaysApply: false` to get the intended lazy-load behavior.

If the behavior is a project convention, prefer `.claude/rules/`. If it's a reusable procedure (with the convention as a side effect), use a skill with `paths:`.

## `disable-model-invocation` and `user-invocable`

These look similar but combine differently:

- `disable-model-invocation: true` → Claude cannot trigger it automatically. User must type `/<name>`. **Also excludes it from subagent `skills:` preload.**
- `user-invocable: false` → does not appear in the `/` menu. Reserved for skills loaded by other mechanisms (e.g., explicit `skills:` preload in a subagent).
- Both `true` → effectively a hidden background-knowledge skill that only other agents can preload.

## Compatibility notes

If the skill depends on MCP servers, libraries, or environment features, declare them in `compatibility:`:

```yaml
compatibility: "Requires MCP server 'exa' (https://docs.exa.ai/) configured. Falls back to WebSearch if absent."
```

This is plain text (500 char cap). It is not machine-enforced — its job is to give a user looking at the skill a fast way to tell whether it will work.

## A complete minimal example

```yaml
---
name: extract-pdf-tables
description: Extract tables from PDF files into clean CSV. Use this skill whenever the user mentions PDFs, tables, scraping data from a PDF, or asks to convert PDF content into a spreadsheet — even without saying "extract" explicitly. Prefer this over generic PDF readers when the task is structured-data extraction rather than full-text reading.
allowed-tools: Read, Glob, Bash
compatibility: Requires Python 3.10+ and the `pdfplumber` library. Install with `pip install pdfplumber`.
---
```

That's all you usually need.
