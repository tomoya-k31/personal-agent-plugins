#!/usr/bin/env bash
# run.sh — render a mode's SQL with the user's log glob + since-date, then
# invoke duckdb. Output is CSV with header on stdout.
#
# Usage:
#   run.sh <allowlist|prompts|procedures> [--since YYYY-MM-DD] [--glob '<path>'] [-- <extra-duckdb-args>]
#
# Examples:
#   run.sh allowlist
#   run.sh prompts --since 2026-05-01
#   run.sh procedures --glob "$HOME/.claude/logs/interactions-2026-05-*.jsonl"
#
# Defaults:
#   --glob   : $HOME/.claude/logs/interactions-*.jsonl
#   --since  : 7 days ago (UTC, ISO date)
#
# The SQL files use two placeholders, replaced here:
#   __LOG_GLOB__   the glob string passed verbatim to read_json_auto()
#   __SINCE_TS__   ISO-8601 UTC cutoff; SQL filters `ts >= '__SINCE_TS__'`

set -euo pipefail

MODE="${1:?usage: run.sh <allowlist|prompts|procedures> [--since YYYY-MM-DD] [--glob '<path>']}"
shift

LOG_GLOB="${HOME}/.claude/logs/interactions-*.jsonl"
# 7-day default. macOS date -v vs GNU date -d.
if date -v-7d +%Y-%m-%d >/dev/null 2>&1; then
  SINCE="$(date -v-7d -u +%Y-%m-%dT00:00:00Z)"
else
  SINCE="$(date -u -d '7 days ago' +%Y-%m-%dT00:00:00Z)"
fi

DUCKDB_ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
  --since)
    SINCE="${2:?--since needs an ISO date}T00:00:00Z"
    shift 2
    ;;
  --glob)
    LOG_GLOB="${2:?--glob needs a path}"
    shift 2
    ;;
  --)
    shift
    DUCKDB_ARGS+=("$@")
    break
    ;;
  *)
    DUCKDB_ARGS+=("$1")
    shift
    ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="${SCRIPT_DIR}/${MODE}.sql"
if [ ! -f "${SQL_FILE}" ]; then
  echo "run.sh: no SQL file for mode '${MODE}' (expected ${SQL_FILE})" >&2
  exit 2
fi

if ! command -v duckdb >/dev/null 2>&1; then
  echo "run.sh: duckdb not found on PATH" >&2
  exit 3
fi

# Substitute placeholders. The glob may contain spaces or quotes — escape for sed.
glob_esc=$(printf '%s\n' "${LOG_GLOB}" | sed -e 's/[\/&|]/\\&/g')
since_esc=$(printf '%s\n' "${SINCE}" | sed -e 's/[\/&|]/\\&/g')

sed -e "s|__LOG_GLOB__|${glob_esc}|g" \
  -e "s|__SINCE_TS__|${since_esc}|g" \
  "${SQL_FILE}" |
  duckdb -csv -header "${DUCKDB_ARGS[@]+"${DUCKDB_ARGS[@]}"}"
