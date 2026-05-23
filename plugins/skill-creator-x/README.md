# skill-creator-x

Manual-invocation-only meta-skill for creating Claude Code Skills. It wraps the
official `skill-creator` loop (`draft → test → review → improve → repeat`) with
three additional up-front stages so you do not produce a Skill that should have
been an MCP server, a subagent, or a `.claude/rules/` file instead.

Skill を作成するためのメタスキル。公式 `skill-creator` の `draft → test → review → improve → repeat`
ループの前に、(1) Skill が本当に正しい抽象かを判定する **責務判断**、(2) MCP / Subagent
構成のユーザー確認、(3) 必要なら Exa-MCP で最新情報を取得する **リサーチ** の 3 段階を追加する。

`disable-model-invocation: true` のため Claude は自動起動しない。`/skill-creator-x`
と打つか、明示的に名指しした時だけ動く。

## High-level flow

```
Stage 0   Responsibility judgment  ──┐  halt → alternative plan
                                     │
Stage 1   Capture intent             │
Stage 1.5 Confirm MCP/Subagent       │
Stage 2   Research (Exa, if needed)  │
Stage 3   Draft SKILL.md             │
Stage 4   Test cases & evals.json    │ ← same as official
Stage 5   Run with-skill + baseline  │   skill-creator from here
Stage 6   Grade, aggregate, review   │
Stage 7   Iterate                    │
Stage 8   Description optimization   │
Stage 9   Package                    ┘
```

Detailed instructions are in `skills/skill-creator-x/SKILL.md`.

## What the plugin bundles

```
plugins/skill-creator-x/
├── .claude-plugin/plugin.json
├── README.md                                  ← you are here
└── skills/skill-creator-x/
    ├── SKILL.md                               Main skill entry point
    ├── agents/                                Subagent prompts (analyzer, comparator, grader, researcher)
    ├── assets/                                Static assets (eval_review.html template)
    ├── eval-viewer/                           Human-readable eval review viewer (generate_review.py)
    ├── references/                            Detailed reference docs (judgment-framework, schemas, etc.)
    └── scripts/                               Eval loop scripts (run_eval, run_loop, aggregate_benchmark, package_skill, …)
```

## Install

This plugin is published through the `personal-agent-plugins` marketplace.

### Everyday use (from GitHub)

```text
/plugin marketplace add tomoya-k31/personal-agent-plugins
/plugin install skill-creator-x@personal-agent-plugins
/reload-plugins
```

### Local development

If you are working on the plugin itself, register the marketplace by local path
in `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "personal-agent-plugins": {
      "source": {
        "source": "local",
        "path": "/path/to/personal-agent-plugins"
      }
    }
  },
  "enabledPlugins": {
    "skill-creator-x@personal-agent-plugins": true
  }
}
```

Then restart Claude Code.

## Requirements

- **Python 3** — runs the scripts under `skills/skill-creator-x/scripts/` and
  `skills/skill-creator-x/eval-viewer/`.
- **Exa MCP server** (optional, used in Stage 2) — only required when the new
  skill targets a fast-moving domain and current knowledge is stale. Register
  via your project's `.mcp.json` or globally.
- The Claude Code CLI itself, for the eval loop (`claude --print …` calls in
  `scripts/run_eval.py`).

## Usage

After install, invoke explicitly:

```text
/skill-creator-x
```

then describe the skill you want to create. The flow walks through Stage 0
first; if the responsibility judgment says "Skill is not appropriate" it halts
and outputs an alternative plan instead of writing skill files.

For full stage-by-stage behavior, command details, and rationale, read
[`skills/skill-creator-x/SKILL.md`](skills/skill-creator-x/SKILL.md).

## Notes

- Generated skills are written under the project's `.claude/skills/<name>/`
  by default. Override the destination by telling the skill where to put them
  during Stage 1.
- The bundled subagents (`agents/*.md`) are skill-internal — they are loaded
  by the scripts, not exposed as top-level Claude Code agents.
- `disable-model-invocation: true` is intentional. Skill creation has side
  effects (file writes, eval runs that cost tokens) and should never start
  automatically.
