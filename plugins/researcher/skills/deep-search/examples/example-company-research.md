# Example: Company Research

**User prompt**: "網羅的にリサーチして、Anthropicの2026年時点での競合ポジションと主要な製品戦略を教えてください。"

**Search type detected**: `company` (phrase: 企業の戦略/ポジション)
**Depth**: deep (trigger word: "網羅的にリサーチ")

---

## What the skill does

1. Parses topic: "Anthropic 競合ポジション・製品戦略 2026"
2. Spawns `researcher:researcher` with Re-TRAC brief, `search type: company`
3. Researcher reads `references/recipes/company.md` before searching
4. Researcher runs Re-TRAC loop; final report relayed to user

---

## Brief sent to researcher (illustrative, after CLAUDE_PLUGIN_ROOT expansion)

```
Deep search task (Re-TRAC protocol):
- Topic: Anthropicの2026年時点での競合ポジションと主要な製品戦略
- Search type: company
- Script:   /path/to/plugins/researcher/scripts/search.py
- Contents: /path/to/plugins/researcher/scripts/contents.py
- Python:   /path/to/plugins/researcher/.venv/bin/python
- max_rounds: 4
- max_tools_per_round: 8
- confidence_threshold: 90
- max_sources: 30

First run the prerequisites block in your system prompt ...
Read and follow: retrac-protocol.md, compression-spec.md, final-verification.md
DO NOT follow references/deep-search-protocol.md.
Read: references/recipes/company.md before issuing searches.
```

---

## Round 2 state snapshot (example, after initial broad search)

```json
{
  "round": 2,
  "confidence": 62,
  "current_answer": "Anthropicは2026年時点でClaudeシリーズ（Opus/Sonnet/Haiku）を軸に企業向けAPIとClaude.aiを展開。OpenAI GPT-4oシリーズと直接競合し、安全性・長コンテキストを差別化軸とする。",
  "answer_rationale": "ラウンド1でAnthropic IR・TechCrunch・The Informationから基本情報を取得。ただし2026年の製品ロードマップと資金調達状況が未確認。",
  "evidence_base": [
    {
      "claim": "Anthropic Claude 3.5 Sonnet は MMLU で GPT-4o を上回ると公式ベンチマークで主張",
      "source_url": "https://anthropic.com/news/claude-3-5-sonnet",
      "verification": "verified",
      "notes": "自社ベンチマーク。独立検証は uncertainties に残す"
    },
    {
      "claim": "Anthropicの2025年の評価額は $60B 超（Series E）",
      "source_url": "https://techcrunch.com/2025/anthropic-series-e/",
      "verification": "verified",
      "notes": ""
    }
  ],
  "source_inventory": [
    {
      "url": "https://anthropic.com/news/claude-3-5-sonnet",
      "fetched_at": "round-1",
      "content_quality": "high",
      "summary": "公式発表。モデル能力・価格・API の詳細"
    },
    {
      "url": "https://en.wikipedia.org/wiki/Anthropic",
      "fetched_at": "round-1",
      "content_quality": "medium",
      "summary": "概要のみ。一次情報源へのリンクとして利用"
    }
  ],
  "uncertainties": [
    {
      "question": "2026年の製品ロードマップや新発表はあるか？",
      "priority": "high",
      "next_action": "Brave news で 'Anthropic 2026 product announcement' を検索",
      "previous_attempts": []
    },
    {
      "question": "独立機関によるベンチマーク比較は？",
      "priority": "medium",
      "next_action": "Exa で 'Claude vs GPT-4o independent benchmark 2025 2026 MMLU' を検索",
      "previous_attempts": ["'Claude benchmark 2025' → 公式ページのみ"]
    }
  ],
  "discarded_directions": [
    {
      "direction": "Anthropic の学術論文一覧",
      "reason": "ユーザの質問は製品戦略・競合ポジション。研究論文リストは範囲外"
    }
  ],
  "next_plan": "Round 3: Brave news で最新発表を確認。独立ベンチマーク検索。confidence が 75 以上なら検索を絞り込む。",
  "audit": {
    "failed_attempts": ["'Anthropic 2026 roadmap' — 未発表のため結果なし"],
    "uncompleted_proposals": [],
    "discarded_possibilities": ["競合としてMistral AI — ユーザは言及しておらず範囲外"]
  }
}
```

## Key patterns illustrated

- **Company search type → recipe が適用される**: `references/recipes/company.md` の
  パラメータチューニングが自動適用される（Exa の `category: company` など）
- **自社ベンチマークは `unverified` に近い扱い**: `notes` で「独立検証は uncertainties に」と
  トレーサビリティを確保
- **discarded_directions が論文一覧を排除**: ユーザの意図に沿ったスコープ維持
