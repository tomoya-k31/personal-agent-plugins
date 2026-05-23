---
name: skill-creator-x
description: Manual-invocation-only meta-skill for creating Skills. Adds a pre-flight responsibility judgment (Skill vs MCP vs Subagent vs .claude/rules/), an explicit MCP/Subagent confirmation step, and an Exa-MCP research phase on top of the official skill-creator loop. Invoke explicitly via /skill-creator-x or by naming the skill — it does not auto-trigger.
disable-model-invocation: true
---

# Skill Creator X

An evolved meta-skill for creating Skills. It keeps the proven `draft → test → review → improve → repeat` loop of the official `skill-creator`, and adds three stages in front:

- **Stage 0 — Responsibility judgment**: decide whether Skill is the right abstraction at all. Halt with an alternative plan if not.
- **Stage 1.5 — MCP/Subagent confirmation**: explicitly agree with the user on the tooling shape of the new skill before drafting.
- **Stage 2 — Research**: when current knowledge is stale or absent, use the Exa MCP to fetch fresh evidence instead of guessing.

The rest of the loop (draft → test → grade → review → iterate → optimize → package) is the same as the official skill-creator and uses the bundled scripts under `scripts/`, the subagent prompts under `agents/`, and the viewer under `eval-viewer/`.

> Heads-up about your reader: skill-creator users span deep technical and non-technical backgrounds. "evaluation" / "benchmark" are borderline OK; explain "JSON" or "assertion" briefly when in doubt. Match the user's vocabulary.

---

## High-level flow

```
Stage 0   Responsibility judgment  ──┐  halt → alternative plan
                                     │
Stage 1   Capture intent             │
Stage 1.5 Confirm MCP/Subagent       │
Stage 2   Research (Exa, if needed)  │
Stage 3   Draft SKILL.md             │
Stage 4   Test cases & evals.json    │ ← same as official
Stage 5   Run with-skill + baseline  │   skill-creator from here
Stage 6   Grade, aggregate, review   │
Stage 7   Iterate                    │
Stage 8   Description optimization   │
Stage 9   Package                    ┘
```

Add these to your TodoList so they do not get skipped, especially **Stage 0** and **Stage 1.5**. In Cowork specifically, also add "Create evals JSON and run `eval-viewer/generate_review.py` so human can review test cases".

---

## Stage 0 — Responsibility judgment (NEW)

**Goal**: before drafting anything, decide whether the requested capability belongs in a Skill, or in MCP / Subagent / `.claude/rules/`, or in a combination.

Read `references/judgment-framework.md` (the 4-step flow) and walk through it. Then reach one of three verdicts:

1. **Skill alone is appropriate** → proceed to Stage 1.
2. **Skill + (MCP and/or Subagent and/or `.claude/rules/`) is appropriate** → proceed to Stage 1, but record which additional components will be created or assumed, and reflect them in Stage 1.5.
3. **Skill is NOT appropriate** → **halt**. Output an alternative plan using `references/halt-template.md` and stop. Do not write any skill files.

Communicate the verdict explicitly to the user before continuing — they may have context that flips the answer. If the verdict is (3), present the alternative plan and wait for the user's explicit direction before doing anything else.

**Worked judgment examples** are in `references/judgment-framework.md`. The decisive question for the most common confusion is: *"Does this need tool-permission scoping or independent context?"* If yes, it's at least partly a Subagent — not a Skill.

---

## Stage 1 — Capture intent

Same as the official skill-creator. Get clear answers (or confirm what is already in the conversation) on:

1. What should the skill enable Claude to do?
2. When should it trigger (what user phrases, contexts, file types)?
3. What is the expected output format?
4. Are objectively verifiable outputs available (so we can build assertions), or is this a subjective skill?

If the current conversation already contains a workflow the user wants to capture ("turn this into a skill"), extract as much as possible from history first — tools used, sequence, corrections, formats — then have the user fill the gaps.

Proactively ask about edge cases, input/output formats, example files, success criteria, and dependencies. Do not jump to test prompts until this is solid.

---

## Stage 1.5 — Confirm MCP / Subagent shape

Before drafting, **explicitly agree with the user** on the tooling shape of the new skill. Use `references/mcp-subagent-confirmation.md` for the question script; the short version:

1. **MCP servers the new skill should depend on**. List the MCPs currently visible in the user's environment (call them out by name — e.g., "I see `brave-search`, `context7`, `exa`, `playwright` configured here"). Ask which, if any, the new skill should rely on. Document this in the skill's `description` / `compatibility` so users without those MCPs are warned.
2. **Subagents the new skill should spawn**. Decide whether parts of the workflow run as subagents — typically for parallelism, scoped tool permissions, or independent context. If yes, identify which agent definitions are needed (new vs. existing), and what `tools` / `permissionMode` each one should have.
3. **`.claude/rules/` companion files** (only if the verdict in Stage 0 said so). Note their `globs:` so the user knows when they auto-load.
4. **`allowed-tools` frontmatter** for the skill itself: which tools should be auto-approved when this skill is active? Default to the minimum set.

Write the answers into a short summary block ("Tooling shape") and read it back to the user for confirmation before moving on.

---

## Stage 2 — Research

When the skill will touch a library, API, or domain whose current state you are not confident about, **do not guess**. Use the `exa` MCP to research, then summarize evidence in the skill. See `references/research-phase.md` for the full protocol; the essentials:

- Identify each "unknown": library version syntax, recent deprecations, current best practices, competing skills/tools in the same space.
- For each unknown, decide: do I already know this with high confidence, or do I need a search?
- For searches, spawn the **researcher** subagent (`agents/researcher.md`) — it uses `mcp__exa__web_search_exa` (and `mcp__exa__web_fetch_exa` to pull specific URLs) and returns a short evidence-grounded summary with URLs.
- If the researcher returns "no useful evidence", ask the user instead of inventing.

Skip Stage 2 when the skill is trivially within your training (e.g., "make a skill that always adds a smiley to the response").

---

## Stage 3 — Draft the skill

Same structure as the official skill-creator. Decide the directory layout:

```
<skill-name>/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
├── scripts/    (executable, decisive, deterministic)
├── references/ (loaded into context on demand)
└── assets/     (templates, icons, fonts used in output)
```

Frontmatter fields beyond `name`/`description` are often overlooked. See `references/frontmatter-cheatsheet.md` — pay attention to:

- `when_to_use`: adds to description (combined 1,536-char cap)
- `allowed-tools`: tools auto-approved while this skill is active
- `disable-model-invocation: true`: manual `/<name>` only — also blocks subagent preload
- `paths`: globs that trigger automatic load — overlaps with `.claude/rules/` behavior
- `model` / `effort` / `context: fork` / `agent`: advanced overrides

**Writing style** (from agent-skills + skill-creator):
- Use imperative form. Explain **why** behind each instruction. Big-caps ALWAYS/NEVER is a yellow flag — reframe and motivate.
- Make `description` "pushy": Claude undertriggers skills, so include both *what* the skill does AND *contexts where it must trigger*, even when the user does not name the skill explicitly.
- Apply **progressive disclosure**: SKILL.md under ~500 lines; push detail to `references/` and `scripts/`. The 3-level model is metadata → SKILL.md body → bundled resources.

---

## Stage 4 — Test cases

After the draft, propose 2-3 **realistic** test prompts — the kind of thing a real user would actually type, with concrete file paths, column names, casual phrasing where appropriate. Save them to `evals/evals.json`. Do **not** write assertions yet — just the prompts. See `references/schemas.md` for the schema.

```json
{
  "skill_name": "example-skill",
  "evals": [
    { "id": 1, "prompt": "...", "expected_output": "...", "files": [] }
  ]
}
```

Share the prompts with the user: "Here are a few test cases — do they look right, or do you want to add more?"

---

## Stage 5 — Run with-skill AND baseline in the same turn

Use the workspace pattern: `<skill-name>-workspace/iteration-N/eval-<ID>/{with_skill,without_skill,old_skill,new_skill}/outputs/`.

**Spawn all subagents in one turn**. Do not run with-skill first and baselines later — launch both for every eval together.

- **New skill**: baseline = no skill (`without_skill`).
- **Improving existing skill**: snapshot first (`cp -r <skill> <workspace>/skill-snapshot/`), baseline = snapshot (`old_skill`).

Write `eval_metadata.json` per eval (assertions can be empty initially; give a descriptive `eval_name`):

```json
{ "eval_id": 0, "eval_name": "renames-columns-on-xlsx", "prompt": "...", "assertions": [] }
```

**While runs execute**, draft the assertions. Good assertions are objectively verifiable with names that read cleanly in the viewer. Subjective skills (writing style, design) skip assertions — lean on human review.

**As each task completes**, immediately capture `total_tokens` and `duration_ms` from the completion notification into `timing.json` — this is the only chance to persist that data.

```json
{ "total_tokens": 84852, "duration_ms": 23332, "total_duration_seconds": 23.3 }
```

---

## Stage 6 — Grade, aggregate, review

1. **Grade** each run with a subagent reading `agents/grader.md`. Output `grading.json` per run. Field names must be exactly `text` / `passed` / `evidence` — the viewer depends on them. For programmatic checks, write a script rather than eyeballing.
2. **Aggregate**:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   Produces `benchmark.json` + `benchmark.md` (pass_rate / time / tokens, mean ± stddev, delta).
3. **Analyst pass** using `agents/analyzer.md` — surface non-discriminating assertions, flaky evals, time/token tradeoffs. Add notes to the benchmark.
4. **Launch the viewer**:
   ```bash
   nohup python <skill-creator-x>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "<name>" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2+, pass `--previous-workspace <workspace>/iteration-<N-1>`. For Cowork / headless, use `--static <output_path>` and proffer the link.
5. **Tell the user**: "Outputs tab is for clicking through each test case and leaving feedback; Benchmark tab is the quantitative comparison."

When the user is done, read `feedback.json`. Empty feedback means "fine" — focus improvements on entries with specific complaints. Kill the viewer with `kill $VIEWER_PID 2>/dev/null`.

---

## Stage 7 — Iterate

Iterate by:

1. **Generalize from the feedback** — do not overfit to specific examples. If a stubborn issue keeps appearing, try a different metaphor, working pattern, or section layout rather than piling on `MUST` clauses.
2. **Keep the prompt lean** — remove things that are not pulling their weight. Read the transcripts (not just outputs) for time wasted on unproductive tangents and trim the prompt accordingly.
3. **Explain the why** — replace rigid bans with motivated reasoning. Modern LLMs respond better to "here's the constraint and the consequence" than to "NEVER do X".
4. **Bundle repeated work** — if all 3 test cases independently wrote a `create_docx.py`, that script belongs in `scripts/` of the skill.

After improvements: rerun all evals into a new `iteration-N+1/`, re-launch the viewer with `--previous-workspace`, wait, re-read feedback. Stop when the user is happy, all feedback is empty, or progress has plateaued.

---

## Stage 8 — Description optimization (optional)

After the skill itself is solid, offer to optimize the description for triggering accuracy. See `references/schemas.md` for the eval set format. Workflow:

1. Generate 16-20 eval queries (8-10 should-trigger, 8-10 should-not-trigger). Make them **realistic**, **substantive** (Claude only consults skills when it cannot handle the task with built-in tools — trivial "read this PDF" queries do not test description quality), and concentrate negatives on **near-misses**, not unrelated tasks.
2. Review with the user via the HTML template:
   - Read `assets/eval_review.html`
   - Replace `__EVAL_DATA_PLACEHOLDER__` / `__SKILL_NAME_PLACEHOLDER__` / `__SKILL_DESCRIPTION_PLACEHOLDER__`
   - Write to `/tmp/eval_review_<skill>.html`, `open` it
   - User exports edited set as `~/Downloads/eval_set.json`
3. Run the loop in the background:
   ```bash
   python -m scripts.run_loop \
     --eval-set <path> --skill-path <path> \
     --model <current-session-model-id> \
     --max-iterations 5 --verbose
   ```
   The script splits 60/40 train/test (stratified by `should_trigger`), runs each query 3× per iteration, asks Claude for a new description, re-evaluates, picks the iteration with the best **test** score.
4. Write `best_description` back into `SKILL.md` frontmatter. Show before/after and report scores.

---

## Stage 9 — Package

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

Validates the frontmatter, excludes `evals/` at the skill root (development artefact), produces `<skill-name>.skill` (a ZIP). If `present_files` is available, present the file path to the user.

---

## Environment-specific notes

**Claude.ai (no subagents):**
- Stage 5 baselines are skipped; Claude runs each test prompt inline, in series.
- Stage 6 viewer: present results in conversation instead, file outputs go to disk for the user to download.
- Stage 8 (description optimization) and the blind-comparison flow require `claude -p` → skip.

**Cowork (subagents available, no display):**
- All stages work, but always pass `--static` to `generate_review.py` and offer the user a link.
- **Generate the viewer BEFORE reviewing outputs yourself** — humans should see runs first.
- Feedback download arrives as `feedback.json` (request access if needed), copy into the workspace.

**Updating an existing skill:**
- Preserve the original name and directory name.
- Copy to `/tmp/<skill-name>/` first — install location may be read-only — and edit there.
- If the verdict in Stage 0 changes (e.g., the original skill should really have been a Subagent), present the migration plan and let the user decide before continuing.

---

## Reference index

- `references/judgment-framework.md` — Stage 0 4-step decision tree with worked examples.
- `references/halt-template.md` — output template when Stage 0 halts.
- `references/mcp-subagent-confirmation.md` — Stage 1.5 question script.
- `references/research-phase.md` — Stage 2 Exa-MCP research protocol.
- `references/frontmatter-cheatsheet.md` — full frontmatter field list, condensed.
- `references/schemas.md` — JSON shapes for evals / grading / benchmark / comparison / analysis (inherited from the official skill-creator).
- `agents/researcher.md` — Exa-driven research subagent (NEW).
- `agents/grader.md` — assertion-based grading subagent.
- `agents/comparator.md` — blind A/B comparator subagent.
- `agents/analyzer.md` — post-hoc + benchmark observation analyzer.

---

Core loop one more time:

**Stage 0 judgment → Stage 1 intent → Stage 1.5 confirm tooling → Stage 2 research → Stage 3 draft → Stage 4 evals → Stage 5 run → Stage 6 grade/review → Stage 7 iterate → Stage 8 optimize → Stage 9 package.**

The first three stages are what skill-creator-x adds on top of the official loop. They are not optional — they exist because skipping them produces skills that should have been MCPs, agents that should have been rules, and descriptions that overfit to stale information.

Good luck.
