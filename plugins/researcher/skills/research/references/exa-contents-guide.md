# Exa Contents API Guide

Wraps the Exa `get_contents()` endpoint via `scripts/contents.py`. Use this
**after** `search.py` returns URLs, to pull deep content for a curated subset.

This is the two-step pattern recommended by Exa:

1. **Triage** — `search.py exa --highlights` returns URLs + short excerpts (cheap).
2. **Deep fetch** — `contents.py --urls ... --text` retrieves full content for the
   handful of URLs you actually need (more expensive per URL).

## Three Content Modes

| Mode | What you get | When to use |
|---|---|---|
| **text** | Full page as clean markdown | Deep document analysis; needs full context |
| **highlights** | Extractive key excerpts (not LLM-generated) | Agentic workflows — **10× more token-efficient** than text |
| **summary** | LLM-generated abstract; optional JSON schema | Structured extraction; tailored question answering |

Modes can be combined in a single call.

## Core Parameters

| Flag | Type | Notes |
|---|---|---|
| `--urls` | CSV | Required. One or more URLs. |
| `--no-text` | bool | Skip text (use with `--highlights` / `--summary` only) |
| `--text-max-chars` | int | Cap text length per result |
| `--verbosity` | enum | `compact` / `standard` / `full` |
| `--highlights` | bool | Enable highlights mode |
| `--highlights-query` | str | Query that selects which excerpts to extract |
| `--summary` | bool | Enable summary mode |
| `--summary-query` | str | Question the summary should answer |
| `--subpages` | int | Auto-discover N linked pages (recommended 5–10, max 15) |
| `--subpage-target` | CSV | Keywords prioritizing relevant subpages (e.g. `docs,api`) |
| `--livecrawl` | enum | `auto` / `always` / `fallback` / `never` |
| `--livecrawl-timeout` | int (ms) | Default 10000; bump to 15000 for slow sites |
| `--extras-links` | int | Extract N links per page |
| `--extras-image-links` | int | Extract N image URLs per page |

## CLI Examples

### Full text (default)
```bash
.venv/bin/python scripts/contents.py --urls "https://example.com,https://example.org"
```

### Highlights (token-efficient agent workflow)
```bash
.venv/bin/python scripts/contents.py \
  --urls "https://example.com/article" \
  --highlights \
  --highlights-query "main argument and supporting evidence" \
  --no-text
```

### Summary with structured query
```bash
.venv/bin/python scripts/contents.py \
  --urls "https://anthropic.com/about" \
  --summary \
  --summary-query "Extract company HQ location, founding year, headcount, funding total" \
  --no-text
```

### Combined modes
```bash
.venv/bin/python scripts/contents.py \
  --urls "https://arxiv.org/abs/2401.12345" \
  --text-max-chars 8000 \
  --highlights --highlights-query "experimental results" \
  --summary --summary-query "what novel contribution does this paper make"
```

### Fresh crawl (real-time data)
```bash
.venv/bin/python scripts/contents.py \
  --urls "https://news.example.com/breaking" \
  --livecrawl always \
  --livecrawl-timeout 15000
```

### Crawl docs site with subpages
```bash
.venv/bin/python scripts/contents.py \
  --urls "https://docs.example.com" \
  --subpages 8 \
  --subpage-target "api,reference,guide"
```

## Best Practices

1. **Start with `--highlights`** for agent workflows. Pull full text only when
   highlights aren't enough.
2. **Always inspect `statuses`** in the response — the endpoint returns HTTP 200
   even when individual URLs fail (404, paywalled, etc.).
3. **Set `--text-max-chars`** to prevent runaway token consumption on long pages.
4. **Use `--livecrawl never`** for static reference pages — much faster.
5. **Use `--livecrawl always`** + `--livecrawl-timeout 15000` for news/realtime.
6. **Subpages are expensive** — start at 5, only increase if needed.
7. **Summary with schema** beats two separate calls (text + LLM extraction).

## Output Shape

```json
{
  "count": 2,
  "results": [
    {
      "url": "https://...",
      "title": "...",
      "text": "..." ,           // if requested
      "highlights": ["..."],     // if requested
      "summary": "...",          // if requested
      "subpages": [...],         // if requested
      "extras": {...}            // if requested
    }
  ],
  "statuses": [...]              // per-URL fetch status if available
}
```

## When NOT to use contents.py

- For initial discovery — that's `search.py`'s job.
- For very large URL lists (50+) — batch into groups of ~10 instead.
- When `search.py exa --highlights` already returned enough content.
