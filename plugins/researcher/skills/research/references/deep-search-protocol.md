# Deep Search Protocol

Deep search combines **parallel breadth** (querying multiple providers at once)
with **iterative depth** (analyzing gaps and running follow-up queries).

## When to Activate

Activate deep search when the task includes any of:
- "deep search", "deep research"
- "thorough research", "thoroughly"
- "exhaustive search", "exhaustively"
- "comprehensive research"

For all other requests, use shallow search (single round).

## Round Structure

```
Round 1: Initial broad search
  ↓
  Gap Analysis: What remains unanswered?
  ↓
Round 2: Targeted follow-up queries (max 3 queries)
  ↓
  Coverage Assessment → STOP if conditions met
  ↓
Round 3 (if needed): Fill final gaps
  ↓
Synthesis
```

**Maximum rounds: 3.** Do not exceed this.

## Stop Conditions (check after each round)

Stop searching and move to synthesis if ANY of these is true:
1. Self-assessed coverage ≥ 80% of the original question's scope
2. Round N returned fewer than 2 URLs not seen in previous rounds
3. Round counter equals 3

If round 1 already meets stop conditions, skip rounds 2 and 3.

## Gap Analysis (after Round 1)

After round 1, ask yourself:
- What specific aspects of the question do the results NOT address?
- Are there time periods, regions, or perspectives missing?
- What claims in the results need corroboration from other sources?
- Are there related topics that would strengthen the answer?

Generate up to 3 targeted follow-up queries that address specific gaps.
Each follow-up query should be substantially different from the round 1 query.

**Bad follow-up** (too similar): "machine learning transformers" → "ML transformer models"
**Good follow-up** (fills gap): "machine learning transformers" → "transformer limitations scalability 2024"

Alternatively, use `--offset` to retrieve a different result page for the **same** query when the
topic is broad and you suspect the first page doesn't cover it fully:
```bash
# Round 1: offset 0 (default)
<PY> "<SCRIPT_PATH>" brave --query "..." --type web --count 10
# Round 2: offset 1 — next page, no query change needed
<PY> "<SCRIPT_PATH>" brave --query "..." --type web --count 10 --offset 1
```

## Parallel Search for Deep Web Topics

For general web topics with deep search, spawn two Agent subagents simultaneously:

```
Spawn two parallel agents:
- Agent A: Run Exa searches (rounds 1-3 iteratively, return all results as JSON)
- Agent B: Run Brave searches (rounds 1-3 iteratively, return all results as JSON)
Merge results from both agents, deduplicate by URL, then synthesize.
```

For domain-specific topics (papers, finance, company), parallelism is less useful
since they use a single provider. Run iterative rounds sequentially.

## Result Deduplication

When merging results across rounds or providers:
- Deduplicate by `url` (exact match)
- Keep the result with more text content if URL appears in both providers
- Track which round each result came from for the Search Log

## Coverage Self-Assessment

Rate coverage on a 0-100% scale based on:
- **Breadth**: Does the synthesis address all aspects of the original question?
- **Depth**: Are key claims supported by multiple independent sources?
- **Recency**: Is the information current enough for the query's timeframe?
- **Authority**: Are sources credible and relevant?

Stop when this self-assessed score is ≥ 80%.

## Example: Deep Web Search

Original query: "What are the main challenges in LLM alignment research?"

**Round 1**: `parallel --query "LLM alignment research challenges 2024" --num-results 10`
→ 18 results from Exa + Brave

Gap analysis: Results focus on RLHF and Constitutional AI but miss:
- Scalability of oversight methods
- International perspectives on alignment governance
- Recent empirical failure cases

**Round 2**:
- `exa --query "scalable oversight LLM alignment limitations" --category "research paper" --num-results 8`
- `brave --query "AI alignment governance international 2024" --type web --count 8`
- `exa --query "LLM alignment failure cases empirical 2024" --num-results 6`

Round 2 returns 15 new URLs. Coverage now ~75%.

**Round 3**:
- `exa --query "constitutional AI RLAIF limitations critique 2024" --category "research paper" --num-results 5`

Round 3 returns 4 new URLs. Coverage now ~85%. → STOP, synthesize.

## Synthesis Note for Deep Search

In the final synthesis, always include:
- A **Search Log** section showing queries run per round and result counts
- The **Confidence** rating informed by total source count and diversity
- Any explicitly identified gaps that remain unresolved after 3 rounds
