# Output Format Templates

## Standard Research Report (all search types)

```markdown
## Research Report: [Topic]

### Summary
[2-3 sentences covering the most important findings. Write for someone who
will only read this section.]

### Key Findings
- [Specific finding or fact — linked source](URL)
- [Specific finding or fact — linked source](URL)
- [Specific finding or fact — linked source](URL)
[3-10 bullet points, most important first]

### Sources
| Title | URL | Date | Relevance |
|---|---|---|---|
| Full article title | https://... | YYYY-MM-DD | Why this source matters |
[List all sources used in synthesis, not just those in Key Findings]

### Confidence
**[High / Medium / Low]** — [1-2 sentence explanation: how many sources,
how current, how consistent across sources]
```

## Deep Search Report (adds Search Log)

```markdown
## Research Report: [Topic]

### Summary
[Same as standard]

### Key Findings
[Same as standard]

### Sources
[Same as standard]

### Confidence
[Same as standard]

### Search Log
| Round | Query | Provider | Results | New |
|---|---|---|---|---|
| 1 | "original query" | Exa + Brave | 18 | 18 |
| 2 | "follow-up query 1" | Exa | 8 | 6 |
| 2 | "follow-up query 2" | Brave | 7 | 5 |
| 3 | "targeted query" | Exa | 5 | 3 |

**Total**: 38 results examined, 32 unique URLs
```

## Domain-Specific Adjustments

### Research Paper Report

Add after Key Findings:
```markdown
### Papers Found
| Title | Authors | Year | Venue | URL |
|---|---|---|---|---|
| Full paper title | Author1, Author2 | 2024 | NeurIPS | https://arxiv.org/... |
```

### Financial Report

Add after Key Findings:
```markdown
### Financial Documents Found
| Company | Document Type | Period | Source | URL |
|---|---|---|---|---|
| Apple Inc | 10-K | FY2024 | SEC EDGAR | https://sec.gov/... |
```

### Company Research

Add after Summary:
```markdown
### Company Overview
- **Founded**: [year]
- **Headquarters**: [location]
- **Industry**: [sector]
- **Key products/services**: [brief list]
- **Recent news**: [1-2 sentences on latest developments]
```

### News Search

Prepend to the report:
```markdown
> **News search** — Results ordered by recency. Coverage period: [date range].
```

And sort Key Findings by publication date (most recent first).

## Confidence Rating Guidelines

| Rating | When to use |
|---|---|
| **High** | 5+ independent sources, consistent findings, published within relevant timeframe |
| **Medium** | 2-4 sources, minor inconsistencies, or sources older than 1 year for time-sensitive topics |
| **Low** | Fewer than 2 sources, contradictory findings, unable to verify key claims, topic outside API coverage |

## Error / No Results Response

When search returns no useful results:
```markdown
## Research: [Topic]

**No results found** for query: "[query]"

**What was tried:**
- Exa search: `[query]` (category: [category]) — 0 results
- Brave search: `[query]` (type: web) — 0 results

**Suggestions:**
- Broaden the search terms (e.g., "[broader query]")
- Check that API keys are valid: `.venv/bin/python scripts/search.py check-keys`
- Try a different search type (e.g., web instead of paper)
```
