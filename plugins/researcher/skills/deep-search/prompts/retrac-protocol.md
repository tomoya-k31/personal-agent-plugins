# Re-TRAC Round Protocol

このファイルを読んでいるあなたは `researcher:researcher` サブエージェントです。
このタスクは Re-TRAC (Recursive Trajectory Compression) deep search です。
`references/deep-search-protocol.md` ではなく、このファイルの手順に従ってください。

## プレースホルダ対応表

以下の手順に出てくる `<...>` は、すべてブリーフ（タスク冒頭）で渡された値に置換する：

| プレースホルダ | ブリーフのラベル | 例 |
|---|---|---|
| `<PY>` | `Python:` | `.../researcher/<ver>/.venv/bin/python` |
| `<SCRIPT>` | `Script:` | `.../researcher/<ver>/scripts/search.py` |
| `<CONTENTS>` | `Contents:` | `.../researcher/<ver>/scripts/contents.py` |
| `<VALIDATE>` | `Validate:` | `.../skills/deep-search/scripts/validate_state.py` |
| `<PLUGIN_ROOT>` | `Script:` の 2 階層上 | `dirname(<SCRIPT>)/..` |
| `<type>` | `Search type:` | `web` / `company` / `paper` など |

## セッションディレクトリの作成（ラウンド 1 開始前に一度だけ）

```bash
SESSION_DIR=$(mktemp -d /tmp/deep-search-XXXXXX)
echo "Session dir: $SESSION_DIR"
```

以降は `$SESSION_DIR` の値（実際のパス）を使う。変数名ではなく値を埋め込むこと。

## ラウンド 1（初回）

1. 検索タイプに対応する recipe を読む：
   - `web`（汎用）の場合は recipe が無いので `<PLUGIN_ROOT>/skills/research/references/exa-api-guide.md` を読む
   - それ以外（paper/company/finance/people/lead/code/personal-site/news）は
     `<PLUGIN_ROOT>/skills/research/references/recipes/<type>.md` を読む
2. 初回の検索計画を立て、search.py で広めに検索する
   - web タイプ：`search.py parallel`（Exa + Brave 同時）
   - ドメイン特化：`search.py exa --category ...`（recipe の指定に従う）
   - 1 メッセージ内で複数クエリを並列発行してよい（max_tools_per_round 以内で）
3. ツールコールは最大 `max_tools_per_round` 回
4. ラウンド終了時に `compression-spec.md` の形式で state JSON を出力する
5. state を `$SESSION_DIR/state-r1.json` に Write ツールで保存し、検証する（下記「state の検証」）

## ラウンド 2 以降

1. 前ラウンドの state JSON を Read ツールで読み直す（`$SESSION_DIR/state-rN.json`）
2. `state.uncertainties` の `priority:high` を最優先で解消する
3. `state.source_inventory` にある URL は再 fetch しない（再訪問は無駄）
4. `state.evidence_base` で `verification:unverified` のものを検証する
5. `state.discarded_directions` の方向には戻らない
6. `state.next_plan` に沿って行動。新たな発見があれば計画を更新してよい
7. ツールコールは最大 `max_tools_per_round` 回
8. 更新した state を `$SESSION_DIR/state-r<N>.json` に保存し、検証する（下記「state の検証」）

## state の検証（保存のたびに実行）

state JSON を保存したら、必ずスキーマ検証を通す：

```bash
<PY> <VALIDATE> $SESSION_DIR/state-r<N>.json
```

`<PY>` / `<VALIDATE>` はブリーフで指定されたパス。exit 0（`VALID: ...`）なら次へ進む。
`INVALID`（exit 1）が出たら、報告された違反箇所（型・enum・必須欠落など）を直して
再保存し、再度検証する。**検証を通らない state を次ラウンドへ渡さないこと** —
壊れた state（confidence が範囲外、verification の値が不正など）は探索を狂わせる。

## ツールの使い分け

| 目的 | コマンド |
|---|---|
| 一般 web 検索（デフォルト） | `<PY> <SCRIPT> parallel --query "..." --num-results 10 --count 10 --extra-snippets` |
| ドメイン特化（paper/company 等） | `<PY> <SCRIPT> exa --query "..." --category "..." --type deep --num-results 10` |
| 速報ニュース | `<PY> <SCRIPT> brave --query "..." --type news --freshness pw --count 20` |
| 日本語コンテンツ | 上記に `--country jp --search-lang jp` を追加 |
| 本文取得（highlights 不十分時） | `<PY> <CONTENTS> --urls "URL1,URL2,URL3" --summary --summary-query "..."` |
| ページ 2（同クエリで追加） | `<PY> <SCRIPT> brave --query "..." --offset 1` |

## 過剰検索の抑制

- 各ラウンド開始時に confidence を 0–100 で自己評価する
- `confidence ≥ 75` なら、追加検索が本当に必要か自問してから進む
- `state.uncertainties[*].previous_attempts` にあるクエリを言い換えただけの
  再検索は行わない（same intent = same failure）

## 停止条件（各ラウンド終了後にチェック）

以下のいずれかを満たしたら LOOP を終了し、最終検証フェーズへ：

1. **完全達成**: `state.uncertainties` が空 AND `state.confidence ≥ confidence_threshold`
2. **収束**: 直近 2 ラウンドで `state.evidence_base` の件数が増えていない
3. **打ち切り**: ラウンド数が `max_rounds` に到達

最終検証は `final-verification.md` の rubric に従う。
