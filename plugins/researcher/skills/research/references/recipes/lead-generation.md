# Recipe: Lead Generation

**Trigger phrases:** "find companies that X", "leads for X", "ICP search for X",
"competitors of X", "companies using <technology>"

## Recommended Parameters (the "sweet spot")

```bash
.venv/bin/python scripts/search.py exa \
  --query "AI infrastructure startup using Anthropic API for code review" \
  --category "company" \
  --type "deep" \
  --num-results 50 \
  --highlights --highlights-query "use case, customers, headcount, funding stage"
```

Per Exa's reference skill: `numResults=50` + `type=deep` yields ~42–49 unique
companies per call (the sweet spot). Going higher hits diminishing returns.

## Query Expansion Strategies

The reference skill uses several strategies; pick the one matching the user's intent:

| Strategy | Template |
|---|---|
| **Competitor mining** | `"companies similar to <KNOWN_CUSTOMER>"` |
| **Geographic** | `"<VERTICAL> companies US-based"` / `"...European"` |
| **Stage-based** | `"seed-stage <VERTICAL>"` / `"growth-stage..."` |
| **Tech-stack matching** | `"companies using <TECH> for <USE_CASE>"` |
| **Use-case decomposition** | Break the vertical into 4–8 micro-verticals |

For comprehensive coverage, run multiple strategies in **parallel** (subagents),
batched in groups of ~5 micro-verticals, then deduplicate.

## Output Schema (structured JSON via `--output-schema`)

The reference skill enforces a strict shape (max 10 properties total, flat arrays):

```json
{
  "type": "object",
  "properties": {
    "company_name":       {"type": "string", "description": "12 words or less"},
    "website":            {"type": "string"},
    "product_description":{"type": "string", "description": "20 words or less"},
    "icp_fit_score":      {"type": "number", "description": "0-10"},
    "icp_fit_reasoning":  {"type": "string", "description": "20 words or less"}
  },
  "required": ["company_name", "website"]
}
```

> **Note:** the current `search.py` doesn't expose `--output-schema` yet. When
> structured output is needed, parse highlights manually or extend the script.

## Deduplication

- Case-insensitive fuzzy match on `company_name`.
- Normalize suffixes (`Inc`, `Ltd`, `LLC`, `Corp`, `GmbH`, `K.K.`).
- When duplicates exist, retain the entry with the higher `icp_fit_score`.

## Output Shape (suggested)

```markdown
## Lead List: <ICP DESCRIPTION>

| # | Company | Website | Score | Why it fits |
|---|---|---|---|---|
| 1 | ... | ... | 9 | ... |
```
