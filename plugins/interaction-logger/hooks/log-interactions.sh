#!/usr/bin/env bash
# log-interactions.sh
#
# Dispatcher hook that logs Claude Code user/AI interactions as JSONL.
# Wire it up from settings.json on the following events:
#   - UserPromptSubmit
#   - PreToolUse  (matcher: AskUserQuestion)
#   - PostToolUse (matcher: AskUserQuestion|Bash|Edit|Write|MultiEdit|WebFetch|Monitor|NotebookEdit|PowerShell|ShareOnboardingGuide|Skill)
#   - PermissionRequest
#   - PermissionDenied
#   - Stop
#
# Log format: one JSON object per line at $HOME/.claude/logs/interactions.jsonl
#   event values:
#     user_prompt              - prompt the user submitted
#     ai_offered_options       - AskUserQuestion options the AI presented
#     user_selected_option     - which option(s) the user picked
#     permission_request       - permission dialog shown for a tool call
#     tool_executed            - tool ran (correlate with permission_request -> user said OK)
#     permission_denied        - tool call denied by classifier
#     ai_response_end          - AI finished a response (Stop) - captures last assistant text
#                                so terse user replies ("2", "yes") can be correlated to context
#
# OK/NG correlation:
#   PermissionRequest followed by a tool_executed for the same session+tool ~= user said OK.
#   PermissionRequest with no matching tool_executed ~= user said NG (or session ended).

# shellcheck disable=SC2016
# The single-quoted strings passed to `append` are jq filters. $ts inside them
# is a jq variable bound via --arg, not a shell variable, so single quotes are
# intentional. SC2016 warnings on these lines are false positives.

set -uo pipefail

LOG_DIR="${HOME}/.claude/logs"
# Daily rotation: one file per local date. Old files stay in place; prune with
# e.g. `find ~/.claude/logs -name 'interactions-*.jsonl' -mtime +30 -delete`.
LOG_FILE="${LOG_DIR}/interactions-$(date +%Y-%m-%d).jsonl"
mkdir -p "${LOG_DIR}"

INPUT=$(cat)

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

EVENT=$(printf '%s' "${INPUT}" | jq -r '.hook_event_name // "unknown"')
# GNU date supports %3N for milliseconds; BSD date (macOS) leaves it as literal
# "3N", so probe with gdate first, then fall back to seconds precision.
if command -v gdate >/dev/null 2>&1; then
  TS=$(gdate -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
else
  TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
fi

append() {
  printf '%s' "${INPUT}" | jq -c --arg ts "${TS}" "$1" >>"${LOG_FILE}" 2>/dev/null || true
}

case "${EVENT}" in
UserPromptSubmit)
  append '{
    ts: $ts,
    event: "user_prompt",
    session_id: .session_id,
    cwd: .cwd,
    prompt: .prompt
  }'
  ;;

PreToolUse)
  TOOL=$(printf '%s' "${INPUT}" | jq -r '.tool_name // ""')
  if [ "${TOOL}" = "AskUserQuestion" ]; then
    append '{
      ts: $ts,
      event: "ai_offered_options",
      session_id: .session_id,
      cwd: .cwd,
      questions: .tool_input.questions
    }'
  fi
  ;;

PostToolUse)
  TOOL=$(printf '%s' "${INPUT}" | jq -r '.tool_name // ""')
  case "${TOOL}" in
  AskUserQuestion)
    append '{
      ts: $ts,
      event: "user_selected_option",
      session_id: .session_id,
      cwd: .cwd,
      questions: .tool_input.questions,
      answers: (.tool_response.answers // .tool_response // {})
    }'
    ;;
  Bash | Edit | Write | MultiEdit | WebFetch | Monitor | NotebookEdit | PowerShell | ShareOnboardingGuide | Skill)
    append '{
      ts: $ts,
      event: "tool_executed",
      session_id: .session_id,
      cwd: .cwd,
      tool_name: .tool_name,
      tool_input_summary: (
        .tool_input
        | (.command // .file_path // .url // .pattern // .)
        | tostring
        | .[0:200]
      ),
      exit_code: (.tool_response.exit_code // .tool_response.exitCode // null),
      interrupted: (.tool_response.interrupted // false),
      stderr_tail: ((.tool_response.stderr // "") | tostring | .[-500:])
    }'
    ;;
  esac
  ;;

PermissionRequest)
  append '{
    ts: $ts,
    event: "permission_request",
    session_id: .session_id,
    cwd: .cwd,
    tool_name: .tool_name,
    tool_input: .tool_input
  }'
  ;;

PermissionDenied)
  append '{
    ts: $ts,
    event: "permission_denied",
    session_id: .session_id,
    cwd: .cwd,
    tool_name: .tool_name,
    tool_input: .tool_input,
    reason: (.reason // "auto_mode_classifier")
  }'
  ;;

Stop)
  # Extract the last assistant text message from the transcript so that terse
  # follow-up prompts ("2", "yes") can be correlated to what was just offered.
  # Truncate to 2000 chars to keep log size bounded.
  TRANSCRIPT=$(printf '%s' "${INPUT}" | jq -r '.transcript_path // ""')
  LAST_TEXT=""
  if [ -n "${TRANSCRIPT}" ] && [ -f "${TRANSCRIPT}" ]; then
    LAST_TEXT=$(jq -s -r '
      map(select(.type == "assistant"))
      | last
      | (.message.content // [])
      | map(select(.type == "text") | .text)
      | join("\n")
      | .[0:2000]
    ' "${TRANSCRIPT}" 2>/dev/null || printf '')
  fi
  printf '%s' "${INPUT}" |
    jq -c \
      --arg ts "${TS}" \
      --arg tp "${TRANSCRIPT}" \
      --arg last "${LAST_TEXT}" \
      '{
          ts: $ts,
          event: "ai_response_end",
          session_id: .session_id,
          cwd: .cwd,
          transcript_path: $tp,
          last_assistant_text: $last
        }' >>"${LOG_FILE}" 2>/dev/null || true
  ;;
esac

exit 0
