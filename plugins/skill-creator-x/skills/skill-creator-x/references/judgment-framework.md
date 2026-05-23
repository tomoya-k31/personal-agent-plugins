# Stage 0 — Responsibility judgment framework

Before drafting any Skill, decide whether Skill is the right place for the capability. Skills, MCP servers, Subagents, and `.claude/rules/` are **not interchangeable**. Each one solves a different problem.

## Core principle (Anthropic official)

> **MCP for connectivity, Skills for procedural knowledge.**

MCP gets data into Claude. Skills teach Claude what to do with that data. Subagents isolate context and scope tool permissions. `.claude/rules/` enforces file-type or path-specific conventions in a deterministic, glob-driven way.

| Layer | Role | Analogy |
|-------|------|---------|
| **MCP** | Connectivity to external systems | Driver / API client |
| **Skill** | Packaged procedural knowledge (how) | Domain manual / training material |
| **Subagent** | Isolated context + permission scope | Specialized colleague |
| **`.claude/rules/`** | File/path-bound behavior rules | On-site work regulations |

## The 4-step decision flow

Walk through each step in order. **Stop at the first match** — that is the *primary* abstraction. Then come back through the remaining steps to see if anything needs to be *combined*.

### Step 1 — Does it require external data / API access?

- **Yes** → MCP is involved. If the capability is "talk to system X, fetch data Y", the primary abstraction is MCP, not Skill.
- **No** → continue.

### Step 2 — Does it require deep exploration, parallel multi-step work, or carry context-pollution risk?

- **Yes** → Subagent is involved. If the work is long-running, mechanical, or needs scoped tool permissions (e.g., `Read`/`Grep` only, no `Write`), the abstraction is at least partly a Subagent.
- **No** → continue.

### Step 3 — Is the capability reusable procedural knowledge, a domain handbook, or a document-processing workflow?

- **Yes** → Skill is appropriate.
- **No** → continue.

### Step 4 — Is the behavior bound to a file type or path pattern?

- **Yes** → `.claude/rules/*.md` with `paths:` frontmatter — lazy-loaded only when matching files are touched. For reliable lazy loading also set `alwaysApply: false`; the community-used `globs:` form is documented as broken (loads eagerly at session start, per Claude Code issue #45587).
- **No** → re-evaluate; the main agent may handle it directly without packaging.

## The Skill-vs-Subagent boundary (most common confusion)

This is where most "should it be a Skill or an agent?" debates happen. Test these:

### Skill is right if **all** are true:
- The work is short.
- It runs on the same model as the parent.
- It **needs the parent's context**.
- Value comes from injecting it into an ongoing conversation.

### Subagent is right if **any** are true:
- Work is long, mechanical, or repetitive.
- The work would **pollute the parent's context**.
- You can run it on a cheaper model (e.g., Haiku).
- You **must restrict sensitive permissions** (`git push`, MCP write, `Bash`).

The last point is the decisive one. **Skills inherit the parent's tool permissions; you cannot scope them down.** Subagents have `tools:` / `disallowedTools:` / `permissionMode:` in their frontmatter and can be locked down.

**Common combined pattern**: a Subagent that *uses* a Skill. E.g., a `python-developer` subagent that consults a `pandas-analysis` skill, or a `code-reviewer` subagent with `tools: Read, Grep` that consults language-specific best-practices skills. This is the right shape for most real systems.

## Skill-vs-`.claude/rules/` boundary

| Aspect | `.claude/rules/*.md` | Skill |
|--------|----------------------|-------|
| Trigger | File path (glob match) — deterministic | `description` match — heuristic |
| Scope | Project-local | Portable across projects, Claude.ai, API, Cowork |
| Typical use | Coding conventions, language-specific constraints | Documentation generation, domain procedures |
| Reliability | 100% when glob matches | Depends on `description` quality |

**Heuristic**:
- Conventions you want enforced *whenever a particular file type is touched* → `.claude/rules/`.
- Reusable procedures or domain knowledge you want available *across projects* → Skill.
- Foundational rules every team member must follow → `CLAUDE.md` (≤200 lines).
- One-off instructions → the prompt itself.

## Worked examples

### Example A — "Make a skill that runs OWASP Top 10 code review on PRs"

- Step 1: needs GitHub access → MCP involved.
- Step 2: review is long, should be isolated, needs `Read`/`Grep` only (no `Write`) → Subagent involved.
- Step 3: the OWASP checklist itself is reusable procedural knowledge → Skill involved.
- Step 4: not file-type-bound.

**Verdict**: **Skill + MCP + Subagent combination**.
- MCP: GitHub server (PR fetch).
- Skill: "OWASP Top 10 review procedure" — portable, called from the subagent.
- Subagent: `code-reviewer` with `tools: Read, Grep, mcp__github__*` and `disallowedTools: Write, Edit`.

→ **Proceed**, but inform the user the skill alone is not enough; record the additional components in Stage 1.5.

### Example B — "Make a skill that turns a CSV into a styled XLSX with our brand colors"

- Step 1: no external API. → no.
- Step 2: single-shot, fast, no permission concerns. → no.
- Step 3: reusable procedural knowledge (brand palette, openpyxl recipes) + bundled script. → Skill.
- Step 4: not path-bound.

**Verdict**: **Skill alone**.

→ Proceed straight to Stage 1.

### Example C — "Whenever someone edits a `*.tsx` file, force Constructor Injection"

- Step 1: no external API. → no.
- Step 2: not a multi-step task. → no.
- Step 3: it's a rule, not a procedure. → marginal.
- Step 4: file-type-bound (`*.tsx`). → **`.claude/rules/`**.

**Verdict**: **Not a Skill**. Halt. Provide an alternative plan using `halt-template.md` showing a `.claude/rules/tsx-conventions.md` with `paths: **/*.tsx` and `alwaysApply: false` frontmatter.

### Example D — "Make a skill that does a 2-hour deep market research and writes a report"

- Step 1: probably needs web search → MCP involved (Exa, Brave).
- Step 2: long-running, parallelizable across queries, context-polluting → **Subagent is the primary abstraction**, not Skill.
- Step 3: the "how to write the report" *is* procedural knowledge → Skill is a useful sub-component.

**Verdict**: **Primary is Subagent**, with a supporting Skill for report templating + MCP for search.

→ Halt. The user asked for "a skill", but what they actually need is a `market-researcher` subagent that *consults* a "report-template" skill. Provide the alternative plan.

## 3-axis confirmation (final sanity check)

Once the primary abstraction is chosen, walk these three:

1. **Portability axis** — needed across teams / projects / Claude products? → ensures Skill is present.
2. **Permission-scoping axis** — must restrict tools for safety? → ensures Subagent is present.
3. **Connectivity axis** — needs persistent external connection? → ensures MCP is present.

If any axis says yes and the corresponding layer is missing, the plan is incomplete. Skill cannot substitute for MCP; `.claude/rules/` cannot substitute for Subagent permission scoping. **Layers do not down-cast.**

## Output of Stage 0

State the verdict to the user in one of these forms:

- ✅ "Skill alone fits — proceeding."
- ✅ "Skill + [MCP|Subagent|.claude/rules/]: I'll create the skill, and I'll also need [X] alongside it. OK to proceed?"
- ⛔ "Skill is not the right primary abstraction for this. The fit is [MCP|Subagent|.claude/rules/]. Here is the alternative plan: [render halt-template.md]."

Wait for the user before continuing.
