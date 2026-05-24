# Brave Search API Guide

No official Python SDK exists. Use `requests` to call the REST API directly.

## Authentication

```
Header: X-Subscription-Token: <BRAVE_API_KEY>
Header: Accept: application/json
```

API key from: https://brave.com/search/api/

## Endpoints

### Web Search
```
GET https://api.search.brave.com/res/v1/web/search
```

### News Search
```
GET https://api.search.brave.com/res/v1/news/search
```

## Query Parameters

### Web Search

| Parameter | Type | Values | Notes |
|---|---|---|---|
| `q` | string | any | Required. Search query. |
| `count` | int | 1–20 | Results per page. **Max 20.** |
| `country` | string | lowercase 2-char | e.g. `us`, `jp`, `gb`. Affects result ranking. **Must be lowercase.** **CLI: `--country`** |
| `search_lang` | string | Brave country code | **Not ISO 639-1.** Use country code: `en`, `jp`, `de`, `fr`, `es`, `ko`. **CLI: `--search-lang`** |
| `safesearch` | string | `off` / `moderate` / `strict` | **Always `off` (hardcoded).** |
| `freshness` | string | see below | Filter by publication date. |
| `offset` | int | 0–9 | Page offset for pagination. |
| `extra_snippets` | bool | `true`/`false` | Up to 5 additional excerpt alternatives per result. |
| `result_filter` | string | comma-separated types | Restrict result types. See values below. |

### News Search

| Parameter | Type | Values | Notes |
|---|---|---|---|
| `q` | string | any | Required. Search query. |
| `count` | int | 1–**50** | Results per page. **Max 50** (larger than web). |
| `country` | string | lowercase 2-char | e.g. `us`, `jp`. **Must be lowercase.** **CLI: `--country`** |
| `search_lang` | string | Brave country code | **Not ISO 639-1.** Use country code: `en`, `jp`, `de`, `fr`, `es`, `ko`. **CLI: `--search-lang`** |
| `safesearch` | string | `off` / `moderate` / `strict` | **Always `off` (hardcoded).** |
| `freshness` | string | see below | Filter by publication date. |
| `offset` | int | 0–9 | Page offset for pagination. |
| `extra_snippets` | bool | `true`/`false` | Up to 5 additional excerpt alternatives per result. |

### Freshness Values
| Value | Meaning |
|---|---|
| `pd` | Past day |
| `pw` | Past week |
| `pm` | Past month |
| `py` | Past year |
| `YYYY-MM-DDtoYYYY-MM-DD` | Custom date range |
| *(omit)* | Any time |

### result_filter Values (Web only)
| Value | Meaning |
|---|---|
| `web` | Standard web pages |
| `news` | News articles |
| `discussions` | Forums, Reddit, community threads |
| `faq` | FAQ snippets |
| `infobox` | Knowledge panel / infobox |
| `videos` | Video results |
| `locations` | Local / map results |

Comma-separate to combine: `"web,discussions"`, `"news,web"`

## Response Structure

### Web Search Response
```json
{
  "type": "search",
  "web": {
    "type": "search",
    "results": [
      {
        "title": "...",
        "url": "...",
        "description": "...",
        "published": "2024-01-15T...",
        "profile": { "name": "Source Name", "url": "..." },
        "extra_snippets": ["..."]
      }
    ]
  }
}
```
Access results via: `data["web"]["results"]`

### News Search Response
```json
{
  "type": "news",
  "results": [
    {
      "title": "...",
      "url": "...",
      "description": "...",
      "age": "3 hours ago",
      "source": { "name": "Reuters", "url": "..." },
      "thumbnail": { "src": "..." }
    }
  ]
}
```
Access results via: `data["results"]` (top-level, not nested under `"web"`)

## Error Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 401 | Invalid or missing `X-Subscription-Token` |
| 422 | Invalid parameter value |
| 429 | Rate limit exceeded |

## Script CLI Equivalents

```bash
# Web search (standard)
.venv/bin/python scripts/search.py brave \
  --query "climate change policy 2025" \
  --type web \
  --count 10

# Web search with extra context snippets
.venv/bin/python scripts/search.py brave \
  --query "LLM inference optimization" \
  --type web \
  --count 10 \
  --extra-snippets

# Web search filtered to community discussions only
.venv/bin/python scripts/search.py brave \
  --query "best Python web framework 2025" \
  --type web \
  --count 10 \
  --result-filter "discussions"

# Web search filtered to web + discussions (broad)
.venv/bin/python scripts/search.py brave \
  --query "open source LLM frameworks" \
  --type web \
  --count 10 \
  --result-filter "web,discussions"

# Web search — page 2 (offset for deep search rounds)
.venv/bin/python scripts/search.py brave \
  --query "machine learning" \
  --type web \
  --count 10 \
  --offset 1

# Breaking news (past day) with snippets
.venv/bin/python scripts/search.py brave \
  --query "NVIDIA earnings" \
  --type news \
  --count 10 \
  --freshness pd \
  --extra-snippets

# News search — up to 25 results (News max is 50)
.venv/bin/python scripts/search.py brave \
  --query "AI regulation" \
  --type news \
  --count 25 \
  --freshness pw

# News search — page 2
.venv/bin/python scripts/search.py brave \
  --query "OpenAI GPT" \
  --type news \
  --count 20 \
  --offset 1
```

## Notes

- Brave web search is better than Exa for general recency (breaking news, trending topics)
- Exa news search tends to have better academic/technical coverage
- Combine both for maximum news coverage: `search.py brave --type news` + `search.py exa --category "news"`
- **Web max**: 20 results/page; **News max**: 50 results/page
- Use `--offset` (0–9) to paginate in deep search rounds and avoid duplicate results across rounds
- Use `--extra-snippets` when synthesis quality matters more than speed
- Use `--result-filter discussions` to find community opinions (Reddit, forums, Stack Overflow)
- **`safesearch` is always `off`** — hardcoded, not exposed as a CLI argument
- **`search_lang` uses Brave's own country-code convention**, not ISO 639-1: use `jp` not `ja`, `en` not `en-US`. Invalid values return HTTP 422.
- **`country` must be lowercase** (`jp` ✅, `JP` ❌)
