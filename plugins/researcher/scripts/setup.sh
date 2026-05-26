#!/usr/bin/env bash
# Idempotent prerequisites for the researcher plugin: ensure the venv exists,
# install deps, and verify API keys. Safe to run on every invocation — it
# no-ops once the venv is present. Packaging the whole prereq as one script
# means a single allow-list rule (Bash(*scripts/setup.sh*)) covers it, so
# background subagents can run it without per-command permission prompts.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$PLUGIN_ROOT/.venv"
REQS="$PLUGIN_ROOT/scripts/requirements.txt"

command -v uv >/dev/null 2>&1 || {
  echo "ERROR: uv not installed — curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
}

if [ ! -x "$VENV/bin/python" ]; then
  uv venv "$VENV"
  uv pip install --python "$VENV/bin/python" -r "$REQS"
fi

# Prints {"exa": "ok", "brave": "ok"} on success; non-zero exit if a key is missing.
"$VENV/bin/python" "$PLUGIN_ROOT/scripts/search.py" check-keys
