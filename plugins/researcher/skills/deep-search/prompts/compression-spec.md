# State Compression Specification

各ラウンド終了時、以下の JSON を出力し `$SESSION_DIR/state-rN.json` に保存する。
これが次ラウンドへの唯一の引き継ぎ手段。

## JSON フォーマット

```json
{
  "round": 1,
  "confidence": 0,
  "current_answer": "現時点での最有力の部分回答。まだなければ null",
  "answer_rationale": "なぜそれを最有力とするか 2–3 文",

  "evidence_base": [
    {
      "claim": "事実主張を 1 文で",
      "source_url": "出典 URL",
      "verification": "verified | unverified | conflicting",
      "notes": "矛盾があれば併記"
    }
  ],

  "source_inventory": [
    {
      "url": "https://...",
      "fetched_at": "round-1",
      "content_quality": "high | medium | low | useless",
      "summary": "1–2 文の要約"
    }
  ],

  "uncertainties": [
    {
      "question": "未解決の問い",
      "priority": "high | medium | low",
      "next_action": "次に何をすべきか具体的に",
      "previous_attempts": ["過去に試して失敗したクエリ"]
    }
  ],

  "discarded_directions": [
    { "direction": "捨てた探索方向", "reason": "理由" }
  ],

  "next_plan": "次ラウンドで実行すべきことの 3–5 文の計画",

  "audit": {
    "failed_attempts": ["失敗したアプローチ"],
    "uncompleted_proposals": ["立てたが実行しなかった計画"],
    "discarded_possibilities": ["検討したが採用しなかった仮説"]
  }
}
```

## 圧縮の原則

1. **冗長性を排除**: 同じ事実を複数の `evidence_base` エントリに書かない
2. **失敗を残す**: 失敗したクエリは `uncertainties[*].previous_attempts` に必ず記録する。
   記録しないと次ラウンドで同じ失敗を繰り返す
3. **質を評価**: `source_inventory[*].content_quality` は厳しめに付ける。`"useless"` と
   マークすることで再訪問を防ぐ（ベクタ store なしの再検索回避）
4. **優先順で並べる**: `uncertainties` は `priority:high` → `medium` → `low` の順
5. **`audit` を正直に**: 失敗・未実行・棄却した選択肢を明示することで次ラウンドの
   self-reflection の質が上がる（Re-TRAC 論文の Audit Part に準拠）
