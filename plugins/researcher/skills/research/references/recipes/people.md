# Recipe: People Search

**Trigger phrases:** "find people who X", "who is X", "VP Engineering at Y",
"engineers working on Z", "experts in X"

## Recommended Parameters

```bash
.venv/bin/python scripts/search.py exa \
  --query "VP Engineering AI infrastructure startup" \
  --category "people" \
  --type "deep" \
  --num-results 20 \
  --additional-queries "Head of Platform LLM infrastructure,Director of ML infra startup" \
  --include-domains "linkedin.com"
```

## Known 400-error Constraints

`category=people` rejects most filters. Only these are safe:
- `--include-domains "linkedin.com"` (LinkedIn-only allow-list works)
- `--num-results`, `--type`, `--additional-queries`

Forbidden with `category=people`:
- Date filters (`--start-*-date`, `--end-*-date`)
- `--exclude-domains`

If you need richer filtering, **drop `--category`** and access full filter
options (at the cost of mixing in non-people results).

## Heuristics

- **Run 2–3 query variations in parallel** via `--additional-queries` (deep search).
  People are described in many ways — "VP Eng" vs "Head of Platform" vs "Director".
- For broader discovery, also issue a `category=personal site` call (blogs / portfolios)
  and a `category=news` call (press mentions).
- Result count: "a few" → 10–20; "comprehensive" → 50–100.

## Multi-call Strategy

| # | Category | Purpose |
|---|---|---|
| 1 | `people` | Primary LinkedIn signal |
| 2 | `personal site` | Personal blogs / portfolios |
| 3 | `news` | Press mentions / conference talks |

Deduplicate by name + (LinkedIn URL ∪ personal-site URL).

## Output Shape (suggested)

```markdown
## People Search: <CRITERIA>

### Top Candidates
- **<Name>** — <Current title @ Company> ([LinkedIn](url))
  - <One-line relevance>
- ...

### Notable Mentions
- ...
```
