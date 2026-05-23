---
name: analyze-interactions
description: Analyze the JSONL logs produced by the interaction-logger plugin to (A) propose new `permissions.allow` entries for safe commands that still trigger permission dialogs, (B) audit recent user prompts for missing prompt-engineering context, and (C) surface auto-executed exploratory or failed commands worth adding to a procedure doc. Use when the user asks to "analyze interaction logs", "audit my prompts", "find allowlist candidates", "review tool-search/discovery commands", or otherwise references the `interaction-logger` log files in `~/.claude/logs/`. DuckDB-based.
---

# analyze-interactions

A three-mode analyzer over `~/.claude/logs/interactions-*.jsonl`. Each mode is one SQL file under `scripts/`, runnable via `scripts/run.sh <mode>`. The skill picks the mode (or runs all three), reads results, and proposes concrete config/doc edits which the user approves per finding.

## Prerequisites

- `duckdb` (≥ 1.5) on `PATH`
- `jq` (already required by `interaction-logger`)
- Logs exist at `~/.claude/logs/interactions-*.jsonl`. If absent, tell the user the plugin isn't wired up or hasn't accumulated data yet.

## Language

- Conversational replies to the user: **Japanese**.
- Content written into files (settings.json comments, CLAUDE.md sections, commit messages, etc.): match the language already used by the target file or surrounding repo docs. If the target is mixed or empty, fall back to the repo's primary doc language. Do not translate existing entries you're appending to.

## Workflow

1. **Ask which mode** (unless the user already named one).
   Use `AskUserQuestion` — never enumerate in plain markdown.
   - `A allowlist` — safe-but-prompted commands
   - `B prompts` — prompt-quality audit
   - `C procedures` — auto exploratory / failed commands
   - `all` — run A → B → C in sequence

2. **Run the SQL** for the chosen mode:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/skills/analyze-interactions/scripts/run.sh" allowlist
   ```
   (replace `allowlist` with `prompts` or `procedures`). Pass `--since 2026-05-01` (or any ISO date) to filter; default is **last 7 days** to keep results actionable.

3. **Interpret + propose** per-mode (see sections below).

4. **For each proposed change**, call `AskUserQuestion` with the exact diff in the option preview. On approval, write the file. On rejection, skip and continue. **Never batch-apply multiple changes in one approval**.

5. **Save a project memory** if the user confirms a non-obvious rule (e.g. "always treat `gh pr view` as global" or "never auto-allow anything in `~/work/secret-client/`").

---

## Mode A — Permission allowlist candidates

**What `allowlist.sql` returns**: `(argv0, command_pattern, cwd, n, last_seen)` rows for commands that
- triggered a `permission_request` (so they aren't currently allowed), and
- were followed by a `tool_executed` in the same session+tool (so the user approved), and
- match a conservative read-only regex (no `>`, `>>`, `rm`, `mv`, `sudo`, `dd`, `chmod`, `chown`, `kill`, `tee`, `| sh`, `eval`, `curl -o`, `wget`).

**How to act on results**:

- Group rows by `argv0` (first token). A pattern like `git status` appearing in many distinct `cwd`s ⇒ propose adding to **`~/.claude/settings.json`** under `permissions.allow`.
- A pattern that only appears in one `cwd` ⇒ propose adding to **`<cwd>/.claude/settings.json`**.
- Use the most general matcher that's still safe. Examples:
  - `Bash(git status:*)` for any `git status` invocation
  - `Bash(jq:*)`           for any jq command (jq is read-only on stdin)
  - `Bash(gh pr view:*)`   for that specific subcommand only — **don't** broaden to `Bash(gh:*)` (e.g. `gh pr merge` is destructive).
- Anything ambiguous (touches the network, writes files, mutates state) ⇒ **don't propose**. Surface it as "review by hand" instead.

**Proposal shape** (`AskUserQuestion` preview):
```
File: ~/.claude/settings.json
Add to permissions.allow:
  "Bash(git status:*)"
  "Bash(jq:*)"
Approved 8 times in 3 sessions, last seen 2026-05-22.
```

---

## Mode B — Prompt-quality audit

**What `prompts.sql` returns**: recent `user_prompt` rows as `(ts, session_id, cwd, prompt)`. Defaults to the last 7 days and to prompts ≥ 20 chars (shorter prompts are usually follow-ups, not "intent" prompts).

**How to act on results**:

For each prompt, score it against this rubric in-session (no API call needed):

| Dimension          | Look for                                                                 |
|--------------------|--------------------------------------------------------------------------|
| **Goal**           | What outcome the user wants. ("make X work", "find Y", "explain Z").     |
| **Success criteria** | How to know it's done. Tests pass? File compiles? Specific output?     |
| **Constraints**    | What not to touch, perf budget, deps to avoid, style rules.              |
| **Context**        | Relevant file paths, prior decisions, links to issues, environment.      |
| **Scope**          | What's *out* of scope. Prevents over-engineering.                        |

Only flag a prompt if **two or more dimensions** are missing AND the prompt looked like an intent prompt (not a one-word reply). Tight, targeted prompts ("yes", "fix that") are fine — don't lecture the user on terseness when context already exists.

**Proposal shape**: instead of editing files, summarize the patterns in a single message to the user:

> Across N prompts in the last 7 days, the recurring gaps are: (1) missing success criteria in 12/N, (2) no scope boundary in 8/N. Sample prompts: ..."

If the user wants this codified, propose adding a "Prompt template" section to `<cwd>/CLAUDE.md` or `~/.claude/CLAUDE.md`. Use `AskUserQuestion` to pick the target. **Never auto-edit CLAUDE.md without approval** — it's high-trust shared context.

---

## Mode C — Auto-executed exploratory / failed commands

**What `procedures.sql` returns**: `tool_executed` Bash rows that look like discovery (`which`, `command -v`, `where`, `type`, `find / `, `ls $(which ...)`, `command -V`) OR rows with non-zero `exit_code` / `interrupted = true`, plus a frequency rank.

**How to act on results**:

- Repeated `which X` / `command -v X` for the same `X` ⇒ surface as: "Claude is checking for `X` every session — add a note to CLAUDE.md confirming whether `X` is installed/available." Propose the addition.
- Commands with non-zero exit code that look like missing binaries (`stderr_tail` contains `command not found`, `No such file`, `not installed`) ⇒ propose CLAUDE.md note: "Don't try `X` here — it's not installed; use `Y` instead" (ask user for `Y`).
- Commands that succeeded but appear in nearly every session (e.g. `git rev-parse --show-toplevel`) ⇒ candidate for the procedure section in CLAUDE.md so future sessions can skip the lookup.

**Apply target**:
- One `cwd` ⇒ `<cwd>/CLAUDE.md`.
- Many `cwd`s ⇒ `~/.claude/CLAUDE.md`.

---

## When applying changes

- **Always** show the exact diff in an `AskUserQuestion` preview before writing.
- For `settings.json`, **read the existing `permissions.allow` array first**, append (don't replace), preserve key order, keep 2-space indent.
- For CLAUDE.md edits, append under an existing relevant section if one exists; create a new top-level section only if no fit. Keep the **Why:** / **How to apply:** structure that matches the file's existing style.
- After each successful edit, mention briefly what changed. Don't summarize at the end of the whole session — the per-edit confirmations already cover it.

## Limitations

- Mode C's "failed command" detection depends on the extended hook fields (`exit_code`, `stderr_tail`). Old log lines from before the hook upgrade won't have these — they're silently skipped.
- `permission_request → tool_executed` correlation infers approval. A `permission_request` with no matching `tool_executed` could mean denial OR session ended before answering. Mode A only uses *approved* requests, so this asymmetry is safe.
- The conservative regex in Mode A errs toward false negatives (won't propose risky commands) over false positives. Expect to add edge cases by hand.
