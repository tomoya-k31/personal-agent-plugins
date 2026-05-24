# Recipe: Research Paper Search

**Trigger phrases:** "find papers on X", "academic research on X", "studies about X",
"literature review on X", "what does research say about X"

## Recommended Parameters

```bash
.venv/bin/python scripts/search.py exa \
  --query "transformer attention scalability limitations" \
  --category "research paper" \
  --type "deep" \
  --num-results 15 \
  --include-domains "arxiv.org,openreview.net,semanticscholar.org,acl.org,neurips.cc" \
  --start-published-date 2023-01-01 \
  --highlights --highlights-query "key findings, methods, datasets"
```

## Known Constraints

- `category="research paper"` is exclusive — other categories can't be combined in
  the same call. Run separate searches and merge.
- `include_text` / `exclude_text` accept **single-item arrays only**.

## Heuristics

- **Default domains** (curated, high-signal):
  `arxiv.org`, `openreview.net`, `semanticscholar.org`, `aclanthology.org`,
  `proceedings.neurips.cc`, `proceedings.mlr.press`.
- **Add `nature.com`, `science.org`, `pubmed.ncbi.nlm.nih.gov`** for life-science /
  natural-science topics.
- Use `--type deep` for high-quality reasoning; `--type fast` only when scanning.
- Cap recency with `--start-published-date` for "recent" / "latest" / "2024-2025".

## Two-step Pattern (best for long papers)

1. Search with `--highlights` only (cheap triage).
2. For top 3–5 URLs, use `contents.py --summary --summary-query "..."` to extract
   contributions / methods / limitations as structured text.

```bash
# Step 2 example
.venv/bin/python scripts/contents.py \
  --urls "https://arxiv.org/abs/...,https://arxiv.org/abs/..." \
  --summary \
  --summary-query "novel contribution, method, key result, limitations" \
  --no-text
```

## Output Shape (suggested)

```markdown
## Research Findings: <TOPIC>

### Overview
<2-3 sentence synthesis>

### Key Papers
- **<Title>** (<authors>, <year>) — <one-line contribution> [link](URL)
- ...

### Methodological Trends
- ...

### Open Questions / Limitations
- ...

### Sources
| Paper | Venue | Year | URL |
|---|---|---|---|
```
