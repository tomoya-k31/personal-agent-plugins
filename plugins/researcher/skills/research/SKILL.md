---
name: research
description: >
  Web, news, academic paper, financial report, company, people, lead-generation,
  code, and personal-site research via Exa and Brave Search APIs. Use this skill
  whenever the user asks to "research", "search for", "find information about",
  "look up", "find papers on", "find recent news on", "find news about",
  "company background on", "financial reports for", "10-K for", "find code for",
  "find people who", "who is", "leads for", "ICP search", "companies that",
  "blogs about", or any phrase implying information retrieval from the web.
  Deep search is triggered by "deep search", "deep research", "thorough research",
  "exhaustive search", or "research thoroughly / exhaustively".
  This skill spawns a researcher agent so all search API calls happen in a
  separate context, keeping the main conversation clean.
---

# Research Skill

## What This Skill Does

Delegates research tasks to the dedicated `researcher:researcher` agent. The
agent (model: sonnet) handles venv setup, API key validation, recipe routing,
search execution, and synthesis — all in its own context window so the main
conversation stays clean.

## How to Use

1. Parse the user's request to extract:
   - **Topic**: what to research
   - **Search type**: web, news, paper, finance, company, people, lead, code,
     personal-site (infer from phrasing — see detection table below)
   - **Depth**: shallow (default) or deep (if user says "deep", "thorough",
     "exhaustive")

2. Spawn the agent using the Agent tool with **exactly these parameters**:
   - `subagent_type: "researcher:researcher"`
   - `description: "Research: <short topic>"`
   - `prompt:` the brief in step 3

3. The brief to pass as `prompt` (fill in the bracketed values):

   ```
   Research task:
   - Topic: <user's topic, verbatim>
   - Search type: <web | news | paper | finance | company | people | lead | code | personal-site>
   - Depth: <shallow | deep>
   - Script:   ${CLAUDE_PLUGIN_ROOT}/scripts/search.py
   - Contents: ${CLAUDE_PLUGIN_ROOT}/scripts/contents.py
   - Python:   ${CLAUDE_PLUGIN_ROOT}/.venv/bin/python

   First run the prerequisites block in your system prompt (idempotent — it
   will no-op if the venv already exists). Then read the matching recipe in
   references/recipes/<type>.md before issuing searches. Run the research and
   return ONLY the structured Markdown report — no agentId/usage suffixes.
   ```

   `${CLAUDE_PLUGIN_ROOT}` should be substituted to its absolute path before
   passing to the agent (the skill loader does this automatically when the
   block is shown to you).

4. Return the agent's report directly to the user **without re-summarizing**.

   **Always strip harness metadata before relaying.** The Agent tool appends
   these to every subagent response — they are NOT part of the report:
   - Trailing line starting with `agentId:` (e.g. `agentId: a8b5cbe084d3e6560
     (use SendMessage with to: '...' to continue this agent)`)
   - Trailing `<usage>...</usage>` block with `total_tokens`, `tool_uses`,
     `duration_ms`

   Cut everything from the first `agentId:` onward before showing the report.

## Search Type Detection

| User says… | Search type |
|---|---|
| "find papers on", "academic research", "studies on", "literature on" | paper |
| "latest news", "recent news", "news about", "what happened with", "セキュリティのニュース" | news |
| "financial report", "10-K", "10-Q", "earnings", "annual report", "SEC filing" | finance |
| "company background", "about company", "tell me about [company]" | company |
| "find people who", "who is", "VP/Director/Head of X at", "engineers working on" | people |
| "leads for", "ICP search", "companies that", "competitors of", "companies using X" | lead |
| "find code", "library for", "GitHub repos", "how do I X in &lt;language&gt;" | code |
| "blogs about", "personal sites on", "practitioner views on", "indie writing on" | personal-site |
| Anything else | web |

## Reference Files

The agent loads these on-demand. You don't need to read them yourself.

- `references/exa-api-guide.md` — Exa SDK parameters & known gotchas
- `references/exa-contents-guide.md` — Get Contents API + two-step pattern
- `references/brave-api-guide.md` — Brave REST API
- `references/deep-search-protocol.md` — iterative deep-search rules
- `references/output-formats.md` — synthesis templates
- `references/recipes/<type>.md` — per-type parameter tuning (8 files: company,
  research-paper, financial-report, people, lead-generation, code,
  personal-site, news)
