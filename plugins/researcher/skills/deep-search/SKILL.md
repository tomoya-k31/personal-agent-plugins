---
name: deep-search
description: >
  Conducts exhaustive multi-round deep research using the Re-TRAC (Recursive
  Trajectory Compression) protocol (Microsoft InfoAgent, arXiv:2602.02486).
  Delegates all search execution to the researcher:researcher agent so search
  noise stays out of the main context. Use ONLY when the user explicitly requests
  deep / thorough / exhaustive research, or comparative analysis that requires
  cross-source synthesis over multiple rounds. For quick single-shot lookups,
  defer to /research instead. Triggers: "deep search", "deep research",
  "exhaustive research", "thorough investigation", "comprehensive analysis",
  "徹底的に調査", "網羅的に比較", "包括的にリサーチ".
allowed-tools: Agent Read
---

# Deep Search Skill (Re-TRAC ベース)

## 目的とスコープ

単一の Web 検索では答えられない複雑な調査依頼を、Re-TRAC (Recursive Trajectory
Compression) で多ラウンド実行する。実行は `researcher:researcher` サブエージェントに
委譲し、検索ノイズをメインコンテキストから隔離する。

**使うべきとき：**
- 複数ソースの突合せ・比較・評価が必要
- 「最新の動向」「2026 年の状況」など時間軸が明示されている
- `/research` で答えが見つからなかった、または問いが複雑で単発では不十分

**使うべきでないとき（→ /research を使う）：**
- 固定的な事実（定義・歴史的事実・基礎概念）
- 単発の検索で十分な場合
- context にある情報の整理だけで済む場合

## 手順

### 1. クエリ解析

ユーザの依頼から以下を抽出する：

- **Topic**: ユーザの言葉そのまま
- **Search type**: web / news / paper / finance / company / people / lead / code /
  personal-site（/research の Search Type Detection 表に準拠）
- **制約**: 対象期間・地域・比較対象の数など
- **パラメータ上書き**: ユーザが「5 ラウンドやって」「30 件ソースで」と指定した場合は
  下記設定パラメータの既定値を上書きする

### 2. researcher:researcher サブエージェントを spawn

Agent ツールで以下のパラメータを設定する：

- `subagent_type: "researcher:researcher"`
- `description: "Deep search (Re-TRAC): <short topic>"`
- `prompt:` 手順 3 の Re-TRAC ブリーフ

既定はフォアグラウンド（ユーザは結果を待つ）。ユーザが「裏で走らせて」など明示した
場合のみ `run_in_background: true`。ただしバックグラウンドはパーミッションプロンプトを
出せず auto-deny されるため、README の allow-list を `.claude/settings.json` に
登録済みであることが前提（未登録ならフォアグラウンドで実行する）。

### 3. Re-TRAC ブリーフを組み立てる

以下のテンプレートの `<...>` を埋めてブリーフとする。`[]` 内は既定値。

```
Deep search task (Re-TRAC protocol):
- Topic: <topic verbatim>
- Search type: <type>
- Script:   ${CLAUDE_PLUGIN_ROOT}/scripts/search.py
- Contents: ${CLAUDE_PLUGIN_ROOT}/scripts/contents.py
- Python:   ${CLAUDE_PLUGIN_ROOT}/.venv/bin/python
- Validate: ${CLAUDE_PLUGIN_ROOT}/skills/deep-search/scripts/validate_state.py
- max_rounds: [4]
- max_tools_per_round: [8]
- confidence_threshold: [90]
- max_sources: [30]

First run the prerequisites block in your system prompt (idempotent — no-op
if venv already exists). Then read and follow these three protocol files in order:

  ${CLAUDE_PLUGIN_ROOT}/skills/deep-search/prompts/retrac-protocol.md
  ${CLAUDE_PLUGIN_ROOT}/skills/deep-search/prompts/compression-spec.md
  ${CLAUDE_PLUGIN_ROOT}/skills/deep-search/prompts/final-verification.md

DO NOT follow references/deep-search-protocol.md for this task — the Re-TRAC
protocol above supersedes it.

Read the matching recipe in
  ${CLAUDE_PLUGIN_ROOT}/skills/research/references/recipes/<type>.md
before issuing searches (substitute <type> with the actual search type above).

Persist each round's state JSON under a fresh mktemp directory
(/tmp/deep-search-XXXXXX). After saving each round's state, validate it with the
Validate script above and fix any reported violations before proceeding. Return
ONLY the final structured Markdown report — no agentId / usage suffixes.
```

### 4. レポートを relay する

サブエージェントが返すレポートを**再要約せず**ユーザへ返す。
`agentId:` 以降（`<usage>` ブロック含む）はハーネスメタデータなので除去してから relay する。

## 設定パラメータ

| パラメータ | 既定 | 意味 |
|---|---|---|
| `max_rounds` | 4 | ラウンド数の安全弁（通常 3-4 で信頼度が閾値に届く） |
| `max_tools_per_round` | 8 | 1 ラウンドあたりのツールコール上限。並列発行と相性良 |
| `confidence_threshold` | 90 | この自己評価信頼度で収束とみなす |
| `max_sources` | 30 | 最終レポートの引用ソース上限 |

## 参照ファイル

サブエージェントが直接 Read する。メインコンテキストは読まなくてよい。

- `prompts/retrac-protocol.md` — ラウンド手順・停止条件
- `prompts/compression-spec.md` — state JSON スキーマと圧縮原則
- `prompts/final-verification.md` — 最終検証 rubric（13 項目）
- `state-schema.json` — state の JSON Schema（`scripts/validate_state.py` が参照）
- `scripts/validate_state.py` — state JSON をスキーマ検証（stdlib のみ、依存ゼロ）
- `examples/example-tech-comparison.md` — 技術比較系の調査例
- `examples/example-company-research.md` — 企業調査系の調査例
