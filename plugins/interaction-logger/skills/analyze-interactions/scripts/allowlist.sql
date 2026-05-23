-- Mode A: permission-allowlist candidates.
-- Bash commands that triggered a permission dialog AND were subsequently
-- executed (= user approved) AND look read-only.
-- Output columns: argv0, command, cwd, approvals, sessions, last_seen.

CREATE OR REPLACE TEMP VIEW events AS
SELECT
  json_extract_string(json, '$.ts')                       AS ts,
  json_extract_string(json, '$.event')                    AS event,
  json_extract_string(json, '$.session_id')               AS session_id,
  json_extract_string(json, '$.cwd')                      AS cwd,
  json_extract_string(json, '$.tool_name')                AS tool_name,
  json_extract_string(json, '$.tool_input.command')       AS command,
  json_extract_string(json, '$.tool_input_summary')       AS tool_input_summary,
  TRY_CAST(json_extract(json, '$.exit_code')   AS INTEGER) AS exit_code,
  TRY_CAST(json_extract(json, '$.interrupted') AS BOOLEAN) AS interrupted
FROM read_ndjson_objects('__LOG_GLOB__')
WHERE json_extract_string(json, '$.ts') >= '__SINCE_TS__';

WITH approved AS (
  SELECT
    pr.session_id,
    pr.cwd,
    pr.tool_name,
    pr.command,
    pr.ts AS req_ts
  FROM events pr
  WHERE pr.event = 'permission_request'
    AND pr.tool_name = 'Bash'
    AND pr.command IS NOT NULL
    AND EXISTS (
      SELECT 1
      FROM events te
      WHERE te.event = 'tool_executed'
        AND te.session_id = pr.session_id
        AND te.tool_name = pr.tool_name
        AND te.ts >= pr.ts
        AND COALESCE(te.exit_code, 0) = 0
        AND COALESCE(te.interrupted, false) = false
    )
),
filtered AS (
  SELECT
    *,
    regexp_extract(command, '^\s*([^\s|;&]+)', 1) AS argv0
  FROM approved
  WHERE
    regexp_matches(
      command,
      '^\s*(ls|cat|head|tail|grep|rg|fd|find\s+\.|jq|yq|wc|file|stat|tree|du|df|ps|pwd|whoami|hostname|date|env|which|command\s+-v|command\s+-V|where|type|echo|printf|column|sort|uniq|cut|awk|true|false|test|gh\s+(pr|issue|run|api|search)\s+(view|list|status|get|search)|git\s+(status|diff|log|show|branch|blame|fetch|remote|config\s+--get|ls-files|rev-parse|describe)|docker\s+(ps|images|inspect|logs|version)|kubectl\s+(get|describe|logs|version|config\s+view)|brew\s+(list|info|outdated)|npm\s+(list|outdated|view|info|ls)|node\s+--version|python3?\s+--version|duckdb\s+--version|duckdb\b\s+-)'
    )
    AND NOT regexp_matches(
      command,
      '(\s>\s|\s>>\s|\brm\b|\bmv\b|\bcp\b|\bsudo\b|\bdd\b|\bchmod\b|\bchown\b|\bkill\b|\btee\b|\|\s*sh\b|\beval\b|\bcurl\b[^|]*-o\s|\bwget\b|\bgh\s+pr\s+(merge|close|edit|create|review|comment)|\bgh\s+issue\s+(close|edit|create|comment)|git\s+(push|reset|checkout|rebase|merge|commit|add|stash|tag|clean|restore|cherry-pick|revert)|brew\s+(install|uninstall|upgrade|reinstall)|npm\s+(install|uninstall|update|publish|run))'
    )
)
SELECT
  argv0,
  command,
  cwd,
  COUNT(*)                       AS approvals,
  COUNT(DISTINCT session_id)     AS sessions,
  MAX(req_ts)                    AS last_seen
FROM filtered
GROUP BY argv0, command, cwd
ORDER BY approvals DESC, argv0;
