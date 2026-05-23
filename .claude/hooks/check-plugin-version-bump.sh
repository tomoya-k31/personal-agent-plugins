#!/bin/bash
# Reminds when a plugins/<name>/ file is edited without bumping the
# corresponding plugin.json version (compared to git HEAD).
# Exit 2 + stderr feeds the message back to Claude.
set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

[[ -z "$file_path" ]] && exit 0

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
plugins_root="${project_dir}/plugins/"

case "$file_path" in
"${plugins_root}"*) ;;
*) exit 0 ;;
esac

rel="${file_path#"$plugins_root"}"
plugin_name="${rel%%/*}"
[[ -z "$plugin_name" ]] && exit 0

manifest_rel="plugins/${plugin_name}/.claude-plugin/plugin.json"
manifest_abs="${project_dir}/${manifest_rel}"

# Editing the manifest itself doesn't need a reminder.
[[ "$file_path" == "$manifest_abs" ]] && exit 0
[[ -f "$manifest_abs" ]] || exit 0

# If the manifest already differs from HEAD, assume version was bumped.
if ! git -C "$project_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  exit 0
fi
if ! git -C "$project_dir" diff --quiet HEAD -- "$manifest_rel" 2>/dev/null; then
  exit 0
fi

cat >&2 <<EOF
⚠️  ${plugin_name} のファイルを編集しましたが、${manifest_rel} の version は未変更です。
キャッシュ更新のため version を bump してください（例: 0.1.1 → 0.1.2）。
EOF
exit 2
