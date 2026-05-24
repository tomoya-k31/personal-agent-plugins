# Recipe: Code / Library Search

**Trigger phrases:** "how do I X in <language>", "find code for X",
"library for X", "GitHub repos for X", "example of X in <framework>"

## Recommended Parameters

```bash
# General code discovery — DO NOT set --category
.venv/bin/python scripts/search.py exa \
  --query "Rust async iterator stream combinators" \
  --num-results 10 \
  --highlights --highlights-query "code example, usage, idiomatic pattern"
```

## Key Insight: NO Category

The Exa Code Search reference skill **does not use `--category`**. The default
neural ranking already handles code well. Setting `--category github` narrows
too aggressively and misses blog posts / docs that often have the best examples.

## Query Construction Rules

Per the Exa reference skill, these rules dramatically improve precision:

1. **Always include the programming language by name.**
   Bad:  `"generics"`  →  Good: `"Go generics"` or `"TypeScript generics"`
2. **Add the framework + version when applicable.**
   `"Next.js 14 server actions"` / `"Python 3.12 typing.Self"`
3. **Include exact identifiers when known.**
   Function names, class names, config keys, error messages — these are gold.

## Token Sizing

The reference skill uses `tokensNum` to control content size. With this CLI,
use `--text-max-chars` as the analog:

| Use case | `--text-max-chars` |
|---|---|
| Focused snippet lookup | 3000–6000 (1000–3000 tokens) |
| Standard task | ~15000 (~5000 tokens) |
| Complex integration | 30000–60000 (10000–20000 tokens) |

## Two-step Pattern (recommended)

```bash
# 1. Discover URLs with highlights
.venv/bin/python scripts/search.py exa \
  --query "Rust tokio select! cancellation pattern" \
  --highlights --highlights-query "code example with error handling" \
  --no-text \
  --num-results 10

# 2. Pull full text for the top 2-3 URLs
.venv/bin/python scripts/contents.py \
  --urls "https://...,https://..." \
  --text-max-chars 15000
```

## Output Shape (suggested)

```markdown
## Code Reference: <TOPIC>

### Idiomatic Pattern
```<lang>
<code snippet>
```

### Notes
- ...

### Sources
- [Docs / blog / SO answer](URL)
- ...
```

## When to Add `category=github`

Only when the user explicitly wants repositories (not tutorials / docs):
- "find a library that does X"
- "GitHub repos implementing Y"

For those: `--category github` is fine. Otherwise omit it.
