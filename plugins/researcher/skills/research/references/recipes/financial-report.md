# Recipe: Financial Report Search

**Trigger phrases:** "10-K for X", "10-Q for X", "financial report for X",
"earnings for X", "SEC filing for X", "annual report for X"

## Recommended Parameters

```bash
.venv/bin/python scripts/search.py exa \
  --query "Apple Inc 10-K annual report fiscal 2024" \
  --category "financial report" \
  --type "deep" \
  --num-results 10 \
  --include-domains "sec.gov,ir.apple.com" \
  --start-published-date 2024-01-01 \
  --highlights --highlights-query "revenue, operating income, segment breakdown, risks"
```

## Known 400-error Constraints

- `--exclude-text` is **rejected** by `category=financial report`. Use query
  negation (e.g. add `"-press release"` to the query string) instead.
- `--include-text` accepts a single item only.

## Heuristics

- **Always include filing type in the query string**: `10-K`, `10-Q`, `8-K`, `S-1`,
  `20-F`, `proxy statement DEF 14A`.
- **Combine `sec.gov` + `ir.<company>.com` domains.** Investor-relations pages
  often have nicer summaries; SEC has primary text.
- For multi-quarter trends, run separate calls per filing type and merge.
- `--start-published-date` is "very useful" — always set it for recency.

## Two-step Pattern (long filings)

10-Ks are 100+ pages. Highlights triage first, then targeted summary extraction:

```bash
# Step 2: pull specific sections from a known filing URL
.venv/bin/python scripts/contents.py \
  --urls "https://www.sec.gov/.../aapl-20240928.htm" \
  --summary \
  --summary-query "Item 1A Risk Factors — summarize top 5 risks with one-line rationale" \
  --no-text
```

## Output Shape (suggested)

```markdown
## Financial Report: <COMPANY> <FILING-TYPE> <PERIOD>

### Headline Numbers
- Revenue: $...B (YoY: +/-X%)
- Operating Income: $...B
- Net Income: $...B
- ...

### Segment Breakdown
| Segment | Revenue | YoY |
|---|---|---|

### Notable Risks (from Item 1A)
- ...

### Filing
- [Primary filing on SEC.gov](URL)
- [Press release](URL)
```
