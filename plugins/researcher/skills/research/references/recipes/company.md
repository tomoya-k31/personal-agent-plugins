# Recipe: Company Research

**Trigger phrases:** "company background on X", "about [company]", "research [company]",
"who is [company]", "tell me about [company]"

## Recommended Parameters

```bash
.venv/bin/python scripts/search.py exa \
  --query "Anthropic company AI safety" \
  --category "company" \
  --type "deep" \
  --num-results 15 \
  --highlights --highlights-query "funding, headcount, products, leadership"
```

## Known 400-error Constraints

`category=company` is incompatible with:
- `--include-domains` / `--exclude-domains`
- `--start-published-date` / `--end-published-date`
- `--start-crawl-date` / `--end-crawl-date`

If you need any of these, **omit `--category`** and use a richer query string instead
(e.g. add `"site:linkedin.com"` to the query).

## Multi-call Strategy

Issue 2–3 calls in parallel and dedupe:

| # | Category | Query template | Purpose |
|---|---|---|---|
| 1 | `company` | `"<NAME> company"` | Homepage + metadata (HQ, funding, headcount) |
| 2 | `news` | `"<NAME> announcement OR funding"` + recent date | Press coverage |
| 3 | `people` | `"<TITLE> at <NAME>"` | Leadership / key personnel |

## Result Count Tuning

- "a few" / "quickly" → `--num-results 10–20`
- "comprehensive" / "exhaustive" → `--num-results 50–100`
- User-specified number → match exactly
- Ambiguous → ask

## Post-Processing

- Deduplicate by URL.
- Group by source type (official site / press / social / analyst).
- Surface uncertainty notes when fields are missing or stale.

## Output Shape (suggested)

```markdown
## Company: <NAME>

### Snapshot
- Founded: ...
- HQ: ...
- Headcount: ... (as of <date>)
- Funding: $... (last round: ...)
- Products: ...

### Recent News (last 90 days)
- [Headline](URL) — <date>

### Leadership
- CEO: <name> ([LinkedIn](url))
- ...

### Sources
| Title | URL | Date |
|---|---|---|
```
