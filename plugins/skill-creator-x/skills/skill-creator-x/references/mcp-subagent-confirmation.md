# Stage 1.5 — MCP / Subagent confirmation script

Use this before drafting SKILL.md. The goal is to lock down the tooling shape of the new skill so the draft does not assume capabilities the user does not have, and does not under-leverage capabilities they do.

## Pre-step: enumerate the environment

Before asking the user, **survey what is actually available** in the current environment. Otherwise you risk recommending an MCP that is not configured.

Run, or recall from the current session:

```bash
# MCPs configured for this project / user
cat .mcp.json 2>/dev/null
cat ~/.claude.json 2>/dev/null | grep -A1 -i mcpServers || true
# Active subagents available
ls -la .claude/agents/ 2>/dev/null
ls -la ~/.claude/agents/ 2>/dev/null
```

You can also look at the **MCP server instructions** and **available skills** lists in the current session's system messages — those reflect what is loaded.

Note the names. You will refer to them concretely in the questions below.

## The 4 questions

Ask these in order. Use `AskUserQuestion` for the multi-choice ones if available; otherwise just ask in plain prose.

### Q1 — MCP servers the new skill should depend on

Tell the user what MCPs are available in their environment by name, then ask:

> "I see the following MCPs configured in your environment: **[list — e.g., `brave-search`, `context7`, `exa`, `playwright`]**. Should the new skill depend on any of them? (You can pick multiple, or none.)"

Possible answers:
- **None** → the skill uses only built-in tools. Record this; do not add `compatibility:` fields for MCPs.
- **One or more** → record each one. In the skill's `description` (or a separate `compatibility:` paragraph in SKILL.md), state the dependency so users without those MCPs get a useful failure message.

If the skill **conditionally** uses an MCP (e.g., "use Exa if available; otherwise ask the user"), say so in the body of SKILL.md with a clear fallback path. Do not silently fail.

### Q2 — Subagents the new skill should spawn

> "Should this skill spawn subagents for any part of its workflow? Cases where this is worth doing:
> - **Parallelism** — running independent work concurrently (e.g., grade 5 outputs at once).
> - **Permission scoping** — locking down tools (e.g., a read-only reviewer).
> - **Context isolation** — keeping a noisy step out of the main conversation.
> - **Cheaper model** — running a mechanical step on Haiku."

For each subagent identified, capture:
- **Name** (kebab-case): `[name]`
- **Reuse or new**: existing definition in `.claude/agents/` or `~/.claude/agents/`, or new file to create?
- **`tools:` whitelist**: minimum set needed.
- **`disallowedTools:`** (optional): defense-in-depth for anything the agent must not do.
- **`model:`**: usually `inherit`; downgrade to `haiku` for cheap mechanical tasks; `sonnet` for balanced; `opus` for hard reasoning.
- **`permissionMode:`**: default unless there's a reason.

If new subagents are needed, **decide whether to bundle them inside the skill's `agents/` directory** or to expect them in `.claude/agents/`. Skill-bundled agents are portable; project-scoped agents are sharable across multiple skills.

### Q3 — `.claude/rules/` companion files

Only ask this if Stage 0 surfaced a path-bound concern.

> "Are there file-type-specific conventions that should ALWAYS apply when matching files are touched? Those belong in `.claude/rules/`, not in the skill itself. (Example: 'when `*.tsx` is touched, force Constructor Injection'.)"

If yes, list each rule file: `path` + `globs:` + 1-sentence content summary. These are companion files to the skill — note them but they live outside the skill directory.

### Q4 — `allowed-tools` for the skill itself

> "When this skill is active, which tools should be auto-approved without prompting the user each time? Default is none — every tool prompt still asks. Skills that orchestrate many tool calls benefit from a curated whitelist."

Possible answers:
- **None / default** → leave `allowed-tools` unset.
- **Specific list** → record as space-separated string or YAML list. Be conservative: include `Read`, `Grep`, `Glob` freely; require explicit justification for `Bash`, `Write`, `Edit`, `WebFetch`.

For MCP tools, use the full prefixed name (e.g., `mcp__exa__web_search_exa`).

## Output: the "Tooling shape" summary

Before drafting SKILL.md, read this summary back to the user and get explicit confirmation:

```
Tooling shape for [skill-name]
──────────────────────────────
MCP deps        : [list, or "none"]
Subagents       : [name (new/reuse), name (new/reuse), or "none"]
.claude/rules/  : [path → globs, or "none"]
allowed-tools   : [list, or "default"]

Does this look right?
```

If the user changes anything, update the summary before proceeding. Carry this forward into Stage 3 (drafting) — these decisions shape the frontmatter and the SKILL.md body.

## Anti-patterns to avoid

- **Recommending an MCP that the user does not have configured.** Always survey first.
- **Defaulting to spawning a subagent for short tasks.** Skills inherit the parent's context cheaply; subagents add coordination cost. Default to no subagent unless one of the four reasons above applies.
- **Auto-approving `Bash` or `Write` in `allowed-tools` without explicit confirmation.** The user should know exactly what becomes prompt-less.
- **Mixing concerns**: file-type conventions belong in `.claude/rules/`, not in the skill body. Procedural knowledge belongs in the skill, not in `.claude/rules/`. Resist the temptation to put everything in the skill because "it works".
