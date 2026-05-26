# Example: Technology Comparison

**User prompt**: "Thoroughly research and compare PyTorch and JAX for large-scale model training in 2026. I need to understand ecosystem maturity, performance, and adoption trends."

**Search type detected**: `web` (general technical comparison)
**Depth**: deep (trigger word: "thoroughly research")

---

## What the skill does

1. Parses topic: "PyTorch vs JAX for large-scale model training 2026"
2. Spawns `researcher:researcher` with Re-TRAC brief
3. Researcher runs the loop, relays final report

---

## Round 1 state snapshot (example)

```json
{
  "round": 1,
  "confidence": 45,
  "current_answer": null,
  "answer_rationale": "Initial broad search retrieved good PyTorch coverage but JAX adoption data is sparse. Need targeted follow-up.",
  "evidence_base": [
    {
      "claim": "PyTorch holds ~70% of ML research paper implementations as of 2025-Q4",
      "source_url": "https://paperswithcode.com/trends",
      "verification": "verified",
      "notes": ""
    },
    {
      "claim": "Google internally migrated Gemini training infrastructure to JAX/XLA",
      "source_url": "https://blog.google/technology/ai/gemini-architecture-2025/",
      "verification": "unverified",
      "notes": "Blog post, not peer-reviewed. Need corroboration."
    }
  ],
  "source_inventory": [
    {
      "url": "https://paperswithcode.com/trends",
      "fetched_at": "round-1",
      "content_quality": "high",
      "summary": "Framework adoption stats from ML papers 2022-2025"
    },
    {
      "url": "https://medium.com/pytorch-vs-jax-2025",
      "fetched_at": "round-1",
      "content_quality": "low",
      "summary": "Opinionated blog post, no primary data"
    }
  ],
  "uncertainties": [
    {
      "question": "What is JAX's actual adoption outside Google (startups, academic labs)?",
      "priority": "high",
      "next_action": "Search 'JAX adoption 2025 non-Google companies academic' on Exa with category research paper",
      "previous_attempts": []
    },
    {
      "question": "How do training throughput benchmarks compare on H100/TPUv5?",
      "priority": "high",
      "next_action": "Search 'PyTorch JAX H100 benchmark throughput 2025 2026'",
      "previous_attempts": []
    },
    {
      "question": "Is the Google Gemini JAX claim accurate?",
      "priority": "medium",
      "next_action": "Find primary Google engineering source or conference talk",
      "previous_attempts": []
    }
  ],
  "discarded_directions": [
    {
      "direction": "TensorFlow comparison",
      "reason": "User asked specifically for PyTorch vs JAX; TF is declining in relevance"
    }
  ],
  "next_plan": "Round 2: Focus on JAX non-Google adoption (Exa paper search) and hardware benchmarks (Brave news + Exa). Verify Gemini JAX claim via Google engineering blog.",
  "audit": {
    "failed_attempts": ["'JAX startup adoption 2025' returned mostly marketing pages"],
    "uncompleted_proposals": [],
    "discarded_possibilities": []
  }
}
```

## Key patterns illustrated

- **Source Inventory prevents re-fetching**: the Medium blog is marked `low` — Round 2 won't waste a fetch on it
- **previous_attempts tracks failures**: "JAX startup adoption 2025" went wrong → Round 2 tries a different angle
- **discarded_directions focuses scope**: TensorFlow is off the table without spending more searches
- **confidence 45 → continue**: well below threshold (90), so loop proceeds
