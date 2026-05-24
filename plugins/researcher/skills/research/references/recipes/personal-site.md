# Recipe: Personal Site Search

**Trigger phrases:** "find blogs about X", "personal sites on X",
"practitioner perspectives on X", "indie writing on X"

## Recommended Parameters

```bash
.venv/bin/python scripts/search.py exa \
  --query "small team SaaS bootstrapping retrospective" \
  --category "personal site" \
  --num-results 15 \
  --exclude-domains "medium.com,substack.com,dev.to,linkedin.com" \
  --start-published-date 2023-01-01 \
  --highlights --highlights-query "lessons learned, what worked, what didn't"
```

## Heuristics

- **Exclude aggregators.** Medium, Substack, Dev.to, LinkedIn pull rank away
  from genuine personal sites. Always pass `--exclude-domains` for these unless
  the user wants Medium/Substack specifically.
- **Date-bound for recency.** `--start-published-date` is supported on this
  category (unlike `people` / `company`).
- **Use `--type deep`** for opinion-driven topics where multiple perspectives
  add value.

## Multi-call Strategy (optional)

For broad expertise discovery, pair with:

| # | Category | Purpose |
|---|---|---|
| 1 | `personal site` | Practitioner essays |
| 2 | `research paper` | Academic backing |
| 3 | (none, web) | Industry blogs / Substacks |

## Output Shape (suggested)

```markdown
## Practitioner Perspectives: <TOPIC>

### Recurring Themes
- ...

### Notable Posts
- **<Title>** by <author> — <one-line take-away> [link](URL)
  - Published: <date>
- ...

### Outliers / Contrarian Views
- ...
```

## Constraints

- `include_text` / `exclude_text` accept single item only.
- Otherwise this category is permissive (date / domain filters work).
