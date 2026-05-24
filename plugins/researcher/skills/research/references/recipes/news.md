# Recipe: News Search

**Trigger phrases:** "latest news", "recent news", "news about", "what happened with",
"breaking news on", "セキュリティのニュース", "最新ニュース", "直近の…"

## Recommended Parameters (run BOTH providers in parallel)

### Brave news — primary recency source

```bash
.venv/bin/python scripts/search.py brave \
  --query "your topic" \
  --type news \
  --count 20 \
  --freshness pw \
  --extra-snippets
```

For Japanese topics — use `--country jp --search-lang jp` (NOT `ja`):
```bash
.venv/bin/python scripts/search.py brave \
  --query "セキュリティ インシデント" \
  --type news \
  --count 20 \
  --freshness pw \
  --country jp --search-lang jp \
  --extra-snippets
```

### Exa news — corroborating depth

```bash
.venv/bin/python scripts/search.py exa \
  --query "your topic" \
  --category news \
  --num-results 10 \
  --start-published-date $(date -v-7d +%Y-%m-%d) \
  --highlights --highlights-query "incident summary, affected systems, impact" \
  --no-text
```

## Freshness Defaults

| User says… | `--freshness` |
|---|---|
| "today", "今日" | `pd` |
| "this week", "今週", "直近" | `pw` (default) |
| "this month", "今月" | `pm` |
| "this year", explicit date range | `--start-published-date YYYY-MM-DD` |

## Primary Sources > Aggregators

When merging results, **prefer primary sources** over news aggregators:

- ✅ Prefer: 朝日新聞 / Reuters / NHK / Bloomberg / ITmedia / @IT / 企業 IR ページ
- ⚠️  Use sparingly: 個人 Substack / Medium ブログ / 週次サマリ系サイト
- ❌ Avoid as sole source: コンテンツ集約サイト全般

If an aggregator is the only source for a given finding, attribute it AND
note the lack of primary corroboration in the Confidence section.

## Parallel Execution Pattern

For news, the agent should run Brave + Exa **concurrently** via two Bash calls
in a single message (not sequentially). Then merge results, deduplicate by URL,
and sort by recency.

## Known Constraints

- Brave news `--count` max is 50 (not 20 like web).
- Brave `--freshness pd` may return very few results for niche topics — fall
  back to `pw` if < 3 results.
- Exa `category=news` accepts date filters (unlike `company` / `people`).
- HTML tags in Brave descriptions are stripped by `search.py` (no special
  handling needed by the agent).

## Output Shape (suggested)

Follow the global Synthesis Principles in `agents/researcher.md`:
- **Shallow: ≤ 15 sources**, Deep: ≤ 30. Drop low-signal items.
- **ISO 8601 dates only** (`2026-05-19`, range: `2026-05-17 〜 2026-05-24`).

```markdown
## News Report: <TOPIC> (<YYYY-MM-DD 〜 YYYY-MM-DD>)

### Summary
<2-3 sentence overview of the main themes>

### Key Findings

#### <Theme 1>
- **<Headline>** (<source>, <YYYY-MM-DD>) — <one-line takeaway> [link](URL)
- ...

#### <Theme 2>
- ...

### Sources
| Title | Source | Date (YYYY-MM-DD) | URL | Notes |
|---|---|---|---|---|

### Confidence
**[High / Medium / Low]** — <coverage, source quality (primary vs aggregator), recency>.
If you fetched > 15 items but cited ≤ 15, note: "N items fetched, top 15 cited;
others corroborated the same findings."
```
