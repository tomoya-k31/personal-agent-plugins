# researcher

Research plugin for Claude Code. Provides web, news, academic paper, financial report, and company research via Exa and Brave Search APIs.

## Usage

```
/research <topic>
/research deep search: <topic>
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

## Deep Search

Add "deep search:" prefix or "thoroughly"/"exhaustively" to trigger iterative multi-round research:
- Round 1: Initial broad search
- Gap analysis: What questions remain unanswered?
- Round 2: Targeted follow-up queries
- Round 3 (if needed): Fill remaining gaps
- Final synthesis

## Architecture

- `scripts/search.py` — unified search CLI (Exa SDK + requests for Brave REST)
- `scripts/contents.py` — Exa Get Contents CLI for the two-step pattern
- `agents/researcher.md` — coordinator agent (model: sonnet, spawned by skill)
- `skills/research/SKILL.md` — entry point skill
- `skills/research/references/` — API guides + deep search protocol
- `skills/research/references/recipes/` — per-type parameter tuning (7 files)

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
(git-ignored). The agent creates it on first use:

```bash
VENV="${CLAUDE_PLUGIN_ROOT}/.venv"
REQS="${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt"
if [ ! -x "$VENV/bin/python" ]; then
  uv venv "$VENV"
  uv pip install --python "$VENV/bin/python" -r "$REQS"
fi
```

All scripts are invoked as:
```bash
"${CLAUDE_PLUGIN_ROOT}/.venv/bin/python" "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" ...
```

To rebuild the venv (e.g. after `requirements.txt` changes), delete `.venv/`
and let the agent recreate it.

## Version Tracking

API/SDK updates are tracked via Renovate (`scripts/requirements.txt`).
