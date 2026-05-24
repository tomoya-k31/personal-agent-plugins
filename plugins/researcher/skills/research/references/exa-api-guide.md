# Exa API Guide

SDK: `exa-py` (official) — minimum version: `>=2.13.0`

For type-specific tuning (company / paper / finance / people / lead / code /
personal site), read the matching file in `references/recipes/`. This guide
covers the **generic SDK surface** only.

For deep content retrieval (full text after URL discovery), see
`exa-contents-guide.md` and use `scripts/contents.py`.

## Client

```python
from exa_py import Exa
client = Exa(api_key)   # falls back to EXA_API_KEY env var
```

## Main Method: `search()`

`search_and_contents()` is **deprecated** in v2 — use `search()`. Text content
is returned by default (~10,000 chars per result) unless `contents=False`.

```python
response = client.search(
    query,                          # str — required
    num_results=10,                 # int
    type=None,                      # see Search Type table
    category=None,                  # see Category table
    include_domains=None,           # list[str]
    exclude_domains=None,           # list[str]
    start_published_date=None,      # "YYYY-MM-DD" ISO
    end_published_date=None,        # "YYYY-MM-DD" ISO
    start_crawl_date=None,          # "YYYY-MM-DD" ISO
    end_crawl_date=None,            # "YYYY-MM-DD" ISO
    include_text=None,              # list[str] — SINGLE ITEM ONLY
    exclude_text=None,              # list[str] — SINGLE ITEM ONLY; rejected by some categories
    user_location=None,             # ISO 2-letter country
    additional_queries=None,        # list[str] — max 10 variations (deep search)
    system_prompt=None,             # str — deep search synthesis hint
    output_schema=None,             # JSON Schema for structured output
    contents=None,                  # ContentsOptions | False
)
```

## Search Type Table (`type` parameter)

| Value | Behavior | Cost | Latency |
|---|---|---|---|
| `auto` | SDK chooses heuristic | — | varies |
| `instant` | Cached results, sub-second | low | very low |
| `fast` | Optimized for speed | low | low |
| `deep-lite` | Light reasoning, query expansion | medium | medium |
| `deep` | Deep search with query variations | high | high |
| `deep-reasoning` | Maximum-quality reasoning + variations | highest | highest |

Heuristic:
- Default to `auto` for general queries.
- Use `deep` / `deep-reasoning` for research-paper / company / lead-gen / finance.
- Use `fast` / `instant` when latency matters (UI typeahead, batch enrichment).

## Category Table

| Category | Use case |
|---|---|
| `"news"` | News articles |
| `"research paper"` | Academic papers, preprints, journals |
| `"financial report"` | 10-K, 10-Q, earnings, SEC filings |
| `"company"` | Company homepages, profiles |
| `"personal site"` | Personal blogs, portfolios |
| `"people"` | LinkedIn profiles, public bios |
| `"pdf"` | PDF documents |
| `None` | General web — no filter |

Note: `"github"` and `"tweet"` may exist but are not in current docs.

**Category constraints (causes 400 errors):**

| Category | Forbidden combinations |
|---|---|
| `company` | `include_domains`, `exclude_domains`, date filters |
| `people` | date filters, `exclude_domains`. `include_domains` LinkedIn-only |
| `financial report` | `exclude_text` |
| All | `include_text` / `exclude_text` with multi-item arrays |

## Contents Options

The `contents` parameter is either `False` (skip) or a dict:

```python
contents = {
    "text": True | {"maxCharacters": 10000, "verbosity": "compact"},
    "highlights": True | {"query": "..."},
    "summary": True | {"query": "...", "schema": {...}},
    "max_age_hours": int,     # 0=fresh, -1=cached only
    "subpages": int,          # 0-15
    "subpage_target": str | list[str],
}
```

**Text verbosity**: `compact` (default) / `standard` / `full`.

## Result Object Attributes

```python
r.url             # str — always present
r.title           # Optional[str]
r.score           # Optional[float] — relevance
r.published_date  # Optional[str]
r.author          # Optional[str]
r.text            # Optional[str] — present unless contents=False
r.highlights      # Optional[list[str]] — if requested
r.summary         # Optional[str] — if requested
r.id              # str — Exa internal ID
```

## Other SDK Methods

```python
# Find pages similar to a known URL
client.find_similar(url, num_results=10, exclude_source_domain=True)

# Get full content for known URLs — see exa-contents-guide.md
client.get_contents(urls, text=True, highlights={"query": "..."})

# One-shot Q&A with cited sources
client.answer(query, text=True)
for chunk in client.stream_answer(query):
    print(chunk, end="")
```

## Script CLI Cheatsheet

```bash
# Basic search
.venv/bin/python scripts/search.py exa --query "..." --num-results 10

# Deep search on research papers
.venv/bin/python scripts/search.py exa \
  --query "transformer attention" \
  --category "research paper" \
  --type deep \
  --include-domains "arxiv.org,openreview.net" \
  --start-published-date 2024-01-01

# Web search with highlights (token-efficient)
.venv/bin/python scripts/search.py exa \
  --query "AI safety regulation 2025" \
  --highlights --highlights-query "specific policies and timelines" \
  --no-text

# Faster, URLs only
.venv/bin/python scripts/search.py exa --query "..." --no-text --num-results 20

# Localized
.venv/bin/python scripts/search.py exa --query "..." --user-location jp

# Multi-variant deep search
.venv/bin/python scripts/search.py exa \
  --query "main intent" \
  --type deep \
  --additional-queries "variation 1,variation 2,variation 3"
```

## Decision Guide: Exa vs Brave

- **Exa** — academic papers, financial reports, company research, code, personal
  sites, structured deep research with `type=deep`.
- **Brave** — breaking news, general web with freshness filters, broad coverage,
  community discussions (`--result-filter discussions`).
- **Both (parallel)** — general web research where source diversity matters.

## Known Gotchas

1. **`include_text` / `exclude_text` accept ONE item only.** Multi-item arrays
   cause 400 errors across all categories.
2. **`category=company` rejects domain & date filters.** Drop them or drop the
   category.
3. **`category=people` rejects most filters.** Only `include_domains=["linkedin.com"]`
   works; for richer filtering, omit the category.
4. **`exclude_text` is rejected by `category=financial report`.** Use query
   negation instead.
5. **`category=research paper` is exclusive** — other categories can't be mixed
   in the same call. Run separate searches and merge.
6. **Text is included by default in v2.** Pass `contents=False` (or `--no-text`)
   when you only need URLs, to save tokens and latency.
