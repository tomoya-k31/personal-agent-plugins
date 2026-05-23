# Halt template — when Stage 0 says "not a Skill"

Use this template verbatim (filling the bracketed parts) when the judgment in Stage 0 concludes that Skill is not the right primary abstraction. **Do not create any skill files.** Output the plan to the user and stop.

---

## Output structure

```
⛔ Skill creation halted

I walked through the Stage 0 judgment (see references/judgment-framework.md) and the conclusion is that **Skill is not the right primary abstraction** for what you're asking. Here's why, and what to do instead.

### What you asked for
[1-sentence restatement of the user's request, in their words]

### Why Skill alone does not fit
[2-4 bullets citing which step in the 4-step flow surfaced the mismatch, with reasoning. Reference judgment-framework.md examples where useful.]

### Recommended primary abstraction: [MCP | Subagent | .claude/rules/]

[1-paragraph statement of why this layer is the right fit. Cite the decisive question from the framework (e.g., "needs scoped tool permissions" → Subagent; "binds to a file glob" → .claude/rules/).]

### Components needed (alternative plan)

[Render the section(s) below that apply.]

#### If recommending MCP
- **Server kind**: [stdio | SSE | HTTP | WebSocket]
- **Likely candidates**: [name existing MCPs that already cover this; otherwise list the API/data source]
- **Tools to expose**: [list]
- **Configuration sketch** (`.mcp.json` or `claude mcp add`):
  ```json
  {
    "mcpServers": {
      "[name]": {
        "command": "[binary]",
        "args": ["..."],
        "env": { "...": "..." }
      }
    }
  }
  ```
- **Reading**: see the user-invocable `plugin-dev:mcp-integration` skill for the full set-up flow.

#### If recommending Subagent
- **Where it lives**: `.claude/agents/[name].md` (project-scoped — recommended) or `~/.claude/agents/[name].md`
- **Frontmatter sketch**:
  ```yaml
  ---
  name: [kebab-name]
  description: [when Claude should delegate to this agent]
  tools: [comma-separated whitelist — e.g., Read, Grep, Glob]
  disallowedTools: [optional — e.g., Write, Edit, Bash]
  model: [sonnet | haiku | opus | inherit]
  permissionMode: [default | acceptEdits | plan | bypassPermissions]
  ---
  ```
- **System prompt outline**: [3-5 bullets of what the agent should do, in its own context]
- **Permission scoping rationale**: [explain which tools are restricted and why — this is the main reason it must be a Subagent, not a Skill]

#### If recommending `.claude/rules/`
- **File path**: `.claude/rules/[descriptive-name].md`
- **Frontmatter (mandatory for lazy load)**:
  ```yaml
  ---
  description: [short purpose]
  paths: [**/*.tsx]    # unquoted CSV; multi-pattern: paths: **/*.tsx, **/*.ts
  alwaysApply: false   # required — without this, the rule loads eagerly
  ---
  ```
  Note: the official Claude Code field is `paths:`, not `globs:`. The `globs:` form circulating in community examples is documented as broken — it loads the rule at session start regardless of file scope (Claude Code issue #45587).
- **Behavior**: lazy-loaded when a matching file is touched (with both `paths:` and `alwaysApply: false`). Without `paths:` or with `alwaysApply: true`, it loads every session like CLAUDE.md — confirm with the user which behavior they want.
- **Body**: [outline the conventions / constraints that should be enforced]

#### If recommending a combination
List each component with its own block, then describe how they fit together in 2-3 sentences (e.g., "the subagent uses the MCP to fetch the PR, then reads the .claude/rules/ for language conventions").

### What I will NOT do without your direction
I am NOT creating a Skill for this. If you want me to:
- Build the alternative components above, say so and I'll proceed.
- Override the judgment and create a Skill anyway, say "create the skill anyway" and I'll do it, but I want to flag the risks: [list the specific risks — e.g., "Skill inherits parent tool permissions, so the safety boundary you wanted is unenforced"].
- Re-run the judgment with extra context you have, share it and I'll re-walk Stage 0.

What would you like to do?
```

---

## Notes for filling the template

- **Be specific about which Stage 0 step surfaced the mismatch.** "Step 2 said this needs scoped permissions" is more useful than "Skill doesn't fit".
- **Always offer the override path** ("create the skill anyway") — the user may have valid reasons to do so, and the framework is a guide, not a gate. But surface the risks explicitly.
- **Do not soft-pedal.** If a Subagent is needed for permission scoping, do not handwave with "the skill could include warnings". Skills cannot enforce permissions.
- **Cite concrete files**: link `references/judgment-framework.md` and any worked examples that match.
- **If the user has stated a deadline or a constraint that forces a single-layer choice** (e.g., "this needs to ship today and we can't add MCPs"), acknowledge it in the response and recommend the least-bad single-layer solution while flagging what is being given up.

---

## When NOT to use this template

- **If the conclusion is "Skill + other layers"** (combination): do not halt. State the verdict, list the additional layers needed, and proceed to Stage 1 once the user confirms.
- **If Stage 0 is ambiguous**: ask a clarifying question first (Step 4 file binding? permission scoping?) — do not halt prematurely.
