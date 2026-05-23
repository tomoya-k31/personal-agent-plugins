# interaction-logger

Claude Code hooks that log every user prompt, every multiple-choice question the
AI asks (via `AskUserQuestion`), the option the user picks, and every
permission-dialog approval/denial — into a daily-rotated JSONL file.

ユーザのプロンプト、AIが `AskUserQuestion` で提示した選択肢、ユーザが選んだ回答、
そして許可ダイアログでのOK/NG応答を日次ローテーションするJSONLに記録するフック集。

## What gets logged

| `event`                | When                                                  | Notes                                            |
|------------------------|-------------------------------------------------------|--------------------------------------------------|
| `user_prompt`          | The user submits a prompt                             | `UserPromptSubmit`                               |
| `ai_offered_options`   | The AI calls `AskUserQuestion`                        | `PreToolUse` — captures the questions presented  |
| `user_selected_option` | The user answers an `AskUserQuestion`                 | `PostToolUse` — captures the answers             |
| `permission_request`   | A permission dialog is shown for a tool call          | `PermissionRequest`                              |
| `tool_executed`        | A permission-required tool actually ran               | Used to infer user said **OK** (see below). Includes `exit_code`, `interrupted`, and `stderr_tail` (last 500 chars) for Bash. |
| `permission_denied`    | A tool call is denied by the auto-mode classifier     | `PermissionDenied`                               |
| `ai_response_end`      | The AI finished a response                            | `Stop` — captures last assistant text (≤2000 chars) so terse follow-ups ("2", "yes") can be correlated to the offered choices |

Log location: `~/.claude/logs/interactions-YYYY-MM-DD.jsonl` (one line per event).

### OK / NG correlation

The Claude Code hook API does not emit a dedicated event for the user's choice
in a permission dialog. We infer it:

- `permission_request` followed by a `tool_executed` with the same
  `session_id` and `tool_name` ⇒ user said **OK**.
- `permission_request` with **no** matching `tool_executed` in the session ⇒
  user said **NG** (or the session ended before they answered).

## Install

This plugin lives in a local marketplace at
`/Users/tomoya-k31/Workspace/github/tomoya-k31/personal-agent-plugins`.

Add the marketplace and enable the plugin in `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "personal-agent-plugins": {
      "source": {
        "source": "local",
        "path": "/Users/tomoya-k31/Workspace/github/tomoya-k31/personal-agent-plugins"
      }
    }
  },
  "enabledPlugins": {
    "interaction-logger@personal-agent-plugins": true
  }
}
```

Restart Claude Code so the hooks load.

### Requirements

- `jq` — required for JSON parsing. Install: `brew install jq`.
- `gdate` (optional) — for millisecond-precision timestamps on macOS. Install: `brew install coreutils`. Without it the script falls back to seconds.

## Log rotation

Files are split by **local date** (`interactions-YYYY-MM-DD.jsonl`). No size cap.
Prune old files yourself, e.g. keep the last 30 days:

```bash
find ~/.claude/logs -name 'interactions-*.jsonl' -mtime +30 -delete
```

## Querying the log

```bash
# Tail today's events
tail -f ~/.claude/logs/interactions-$(date +%Y-%m-%d).jsonl | jq .

# Every prompt you submitted this week
jq -r 'select(.event == "user_prompt") | "\(.ts)  \(.prompt)"' \
  ~/.claude/logs/interactions-*.jsonl

# Event count grouped by project (cwd)
jq -r '.cwd' ~/.claude/logs/interactions-*.jsonl | sort | uniq -c | sort -rn

# Only events from one project
jq -c 'select(.cwd | startswith("/Users/tomoya-k31/Workspace/github/tomoya-k31/hakoniwa-infra"))' \
  ~/.claude/logs/interactions-*.jsonl

# Permission requests that were NOT followed by execution
# (rough NG detector: requested tools with no matching tool_executed in same session)
jq -s '
  group_by(.session_id)
  | map({
      session: .[0].session_id,
      requested: [.[] | select(.event == "permission_request") | "\(.tool_name)"],
      executed:  [.[] | select(.event == "tool_executed")     | "\(.tool_name)"]
    })
  | map({session, ng: (.requested - .executed)})
  | map(select(.ng | length > 0))
' ~/.claude/logs/interactions-*.jsonl
```

## Implementation notes

- One bash dispatcher (`hooks/log-interactions.sh`) handles all five hook
  events. It reads the event JSON from stdin, dispatches on
  `.hook_event_name`, and appends a single JSON line to today's log file.
- Matchers in `hooks/hooks.json` keep the script from firing on noisy tools
  (e.g. `Read`, `Glob`, `Grep`) — only the events listed in the table above
  trigger it.
- The script never blocks: `jq` failures or missing fields silently produce no
  log entry. It always exits `0`.
- All paths use `${CLAUDE_PLUGIN_ROOT}` so the plugin is portable across
  installations.

## Analyzing the logs

The plugin ships a companion skill, `analyze-interactions`, at
`skills/analyze-interactions/`. It runs DuckDB queries over the JSONL logs to:

- **A** — find safe Bash commands that still trigger permission dialogs and
  propose `permissions.allow` additions (project- or user-scoped, decided from
  the `cwd` distribution in the logs).
- **B** — extract recent user prompts and audit them against a
  goal/criteria/constraints/context/scope rubric.
- **C** — surface auto-executed discovery commands (`which`, `command -v`,
  `find /`, …) and failed commands as candidates for a procedure doc.

Each proposed change is shown as a diff and requires per-finding approval via
`AskUserQuestion`. See `skills/analyze-interactions/SKILL.md` for the workflow
and `scripts/{allowlist,prompts,procedures}.sql` for the queries. Run a single
mode by hand with:

```bash
bash plugins/interaction-logger/skills/analyze-interactions/scripts/run.sh allowlist --since 2026-05-01
```

## Hook events used

`UserPromptSubmit`, `PreToolUse` (AskUserQuestion), `PostToolUse`
(AskUserQuestion + permission-required tools), `PermissionRequest`,
`PermissionDenied`, `Stop`.

See `hooks/hooks.json` for the exact matcher strings.
