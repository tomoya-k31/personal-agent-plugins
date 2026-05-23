# Stage 2 — Research phase protocol

When the new skill will touch a library, API, or domain whose current state you are not confident about, do not guess. This stage exists so that the skill being drafted is grounded in current evidence, not stale training data.

## When to skip Stage 2

Skip if:
- The skill is purely structural / generic (e.g., "always reply in bullet points").
- Everything the skill references is in your high-confidence training (e.g., basic Python stdlib, well-known git operations).
- The user has already given you authoritative source material (linked docs, files in the repo).

If in doubt, run Stage 2 — research is cheap, drafting on a stale assumption is expensive.

## The unknowns inventory

Before searching, list explicitly what you do not know with high confidence. Common categories:

| Category | Examples |
|----------|----------|
| **Library syntax & API** | "Does pandas 2.x still expose `DataFrame.append`?" "Latest pptx-python API for table styling?" |
| **Recent deprecations** | "Are there changes in OpenAI's API since [knowledge cutoff]?" |
| **Best practices in domain** | "What does OWASP say about JWT storage as of [current date]?" |
| **Competing skills / tools** | "Is there an existing community skill that already does this?" |
| **Standards / specs updates** | "Latest version of the OpenAPI spec?" |
| **Tool / CLI changes** | "Has `gh` CLI added a flag for X?" |

For each unknown, mark whether it needs a **search** or a **library doc lookup** or **just asking the user**.

## The tools

**Primary**: `mcp__exa__web_search_exa` — high-signal web search for AI agents. Use this as the default.
**Page fetch**: `mcp__exa__web_fetch_exa` — pull a specific URL when you have a known good source.
**Built-in fallbacks** (when Exa is unavailable): `WebSearch`, `WebFetch`.

The user opted Exa-only for this skill creator. If the user has explicitly allowed Brave or other search MCPs in the future, expand here.

## How to search well

Search quality dominates result quality. Some rules:

1. **One specific question per query.** Not "skill creation best practices" — instead "Anthropic skill description writing best practices 2025".
2. **Include the date or version** when relevant: "pandas 2.2 DataFrame.concat replace append".
3. **Search for the source you want**: "site:docs.anthropic.com skill description" or "github anthropics/skills examples".
4. **Use 2-3 queries per unknown** — phrasing variations surface different sources.

## Delegating to the researcher subagent

For non-trivial research, spawn the researcher subagent — it isolates the search-and-summarize work from your main context.

```
Use the Agent tool with subagent_type="general-purpose" (or the bundled
agents/researcher.md as a system prompt) and prompt:

"You are researching for the creation of a Skill named '[skill-name]'.
The unknowns to resolve are:

1. [unknown 1]
2. [unknown 2]
...

For each unknown:
- Run 2-3 Exa searches.
- Read the most authoritative result(s) via web_fetch_exa.
- Summarize findings in 3-5 sentences citing source URLs.

If the evidence is thin or contradictory, say so explicitly.
Do NOT speculate beyond what the sources support.

Report back with one section per unknown."
```

The researcher should not write skill files — its job is to return evidence. You decide what makes it into the skill.

## Inline (no subagent) protocol

If subagents are not available (Claude.ai) or the research is small (1-2 quick lookups), do it inline:

```
mcp__exa__web_search_exa(query="...")
mcp__exa__web_fetch_exa(url="...")
```

Keep results in working notes during the conversation — do not write them to disk unless they become part of the skill.

## Turning evidence into skill content

Once research is done, choose **what goes into the skill** and **what stays in your head**:

- **Code patterns / API signatures** that the skill will reproduce → bake them into `references/` or `scripts/` so the model executing the skill does not have to re-search.
- **High-level domain knowledge** that informs the skill design but is too broad to bundle → use it to shape the SKILL.md instructions; cite the most important source URL in a comment so future maintainers can verify.
- **Conflicting evidence** → ask the user before committing. Do not pick a side silently.

## What NOT to do

- **Do not cite sources you did not actually fetch.** If you only saw the search-result snippet, say "based on Exa snippet, not full page".
- **Do not bundle outdated docs as `references/`.** If the doc updates frequently, link to it instead of inlining.
- **Do not pretend to know.** "I think pandas 2.x still has `.append`" with no search behind it is exactly the failure mode this stage exists to prevent.
- **Do not over-research.** If 2-3 queries return the same answer, stop. Burning tokens to confirm what you already know is not free.

## A note on time-sensitivity

The skill being drafted will be read by Claude weeks or months from now, on a session whose knowledge cutoff is different from yours. Anything time-sensitive in the skill body should either:
- Reference a stable URL to fetch at runtime, or
- Be marked as "as of [date], verify if working with [library] later than [version]".

Future-proof against your own staleness.
