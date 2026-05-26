# researcher

Research plugin for Claude Code. Provides web, news, academic paper, financial report, and company research via Exa and Brave Search APIs.

## Usage

```
/research <topic>          # single-round search
/deep-search <topic>       # exhaustive multi-round Re-TRAC research
```

## Setup

Set API keys in your environment:

```bash
export EXA_API_KEY=your_key      # https://exa.ai/
export BRAVE_API_KEY=your_key    # https://brave.com/search/api/
```

At least one key is required. Both keys enable full functionality (web search uses both providers in parallel).

Add to `~/.claude/settings.json`:
```json
{
  "env": {
    "EXA_API_KEY": "your_key",
    "BRAVE_API_KEY": "your_key"
  }
}
```

## Search Types

| Type | Trigger phrase | Provider | Recipe file |
|---|---|---|---|
| Web (general) | "research X", "find info about X" | Exa + Brave (parallel) | — |
| News | "recent news on X", "latest news about X" | Brave news + Exa news | — |
| Research paper | "find papers on X", "academic research on X" | Exa only | `recipes/research-paper.md` |
| Financial report | "financial reports for X", "10-K for X" | Exa only | `recipes/financial-report.md` |
| Company | "company background on X", "about company X" | Exa only | `recipes/company.md` |
| People | "find people who X", "who is X" | Exa only | `recipes/people.md` |
| Lead generation | "leads for X", "companies that X", "ICP search" | Exa only | `recipes/lead-generation.md` |
| Code/GitHub | "find code for X", "GitHub repos for X" | Exa only | `recipes/code.md` |
| Personal site | "blogs about X", "practitioner views on X" | Exa only | `recipes/personal-site.md` |

Recipes encode type-specific parameter tuning and known 400-error pitfalls.
The agent reads only the relevant recipe per query.

## Two-Step Search Pattern

For token-efficient deep research, the agent uses:

1. **Triage** — `search.py` with `--highlights` returns URLs + extractive excerpts
   (≈10× cheaper than full text).
2. **Deep fetch** — `contents.py --urls "..."` pulls full text / summary for the
   selected 3–5 URLs only.

See `skills/research/references/exa-contents-guide.md`.

## Deep Search (`/deep-search`)

Exhaustive multi-round research lives in the **`deep-search` skill**, which uses
the Re-TRAC (Recursive Trajectory Compression) protocol — each round emits a
structured `state` JSON (evidence, source inventory, uncertainties, discarded
directions) that conditions the next round, so the search converges instead of
repeating itself. The `/research` skill stays single-round; deep/thorough/
exhaustive requests route to `/deep-search`.

The deep-search skill spawns this `researcher` agent with a Re-TRAC brief, so the
multi-round search runs in the agent's context and only the final report returns
to the main conversation. Per-round `state-rN.json` files are validated against
`skills/deep-search/state-schema.json` by `skills/deep-search/scripts/validate_state.py`.

### Background execution

Background subagents cannot show permission prompts — they auto-deny any tool
call that would prompt. To run `/deep-search` (or `/research`) unattended in the
background, pre-approve its commands in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(*scripts/setup.sh*)",
      "Bash(*scripts/search.py *)",
      "Bash(*scripts/contents.py *)",
      "Bash(*deep-search/scripts/validate_state.py *)",
      "Bash(mktemp -d *)",
      "Write(/tmp/deep-search-*/**)"
    ]
  }
}
```

Without these, run it in the **foreground** (the default), where you approve the
prompts interactively. These rules are scoped to the research scripts; they do
not broaden Bash access generally.

## Architecture

- `scripts/setup.sh` — idempotent venv + dep install + key check (one approvable command)
- `scripts/search.py` — unified search CLI (Exa SDK + requests for Brave REST)
- `scripts/contents.py` — Exa Get Contents CLI for the two-step pattern
- `agents/researcher.md` — coordinator agent (model: sonnet, tools: Bash/Read/Write/Agent)
- `skills/research/SKILL.md` — single-round research entry point
- `skills/deep-search/` — Re-TRAC multi-round skill (SKILL.md, prompts/, state-schema.json, scripts/validate_state.py)
- `skills/research/references/` — API guides + (legacy) deep search protocol
- `skills/research/references/recipes/` — per-type parameter tuning (8 files)

## APIs Used

| API | Provider | Endpoint | Auth | Docs |
|---|---|---|---|---|
| Exa Search | Exa | `https://api.exa.ai` | `EXA_API_KEY` (header) | https://docs.exa.ai |
| Brave Web Search | Brave | `https://api.search.brave.com/res/v1/web/search` | `X-Subscription-Token` (header) | https://api-dashboard.search.brave.com/documentation/services/web-search |
| Brave News Search | Brave | `https://api.search.brave.com/res/v1/news/search` | `X-Subscription-Token` (header) | https://api-dashboard.search.brave.com/documentation/services/news-search |

### Python Libraries

| Library | Version | Purpose | Source |
|---|---|---|---|
| `exa-py` | `>=2.13.0` | Official Exa Python SDK | https://pypi.org/project/exa-py/ |
| `requests` | `>=2.32.0` | HTTP client for Brave REST API | https://pypi.org/project/requests/ |

> Brave has no official Python SDK. `requests` is used to call the Brave REST API directly.

## Dependencies

Requires `uv` on PATH for venv and dependency management:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Project venv

Scripts run inside a project-local venv at `plugins/researcher/.venv/`
(git-ignored). The agent creates it on first use via `scripts/setup.sh`:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh"
```

It runs `uv venv` + `uv pip install` only when the venv is missing, then verifies
API keys. All scripts are invoked as:
```bash
"${CLAUDE_PLUGIN_ROOT}/.venv/bin/python" "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" ...
```

To rebuild the venv (e.g. after `requirements.txt` changes), delete `.venv/`
and let the agent recreate it.

## Version Tracking

API/SDK updates are tracked via Renovate (`scripts/requirements.txt`).
