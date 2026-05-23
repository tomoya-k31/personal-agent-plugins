-- Mode C: auto-executed exploratory / failed Bash commands.
-- Three buckets:
--   discovery  - which/command -v/where/type X       (tool lookups)
--   fs_search  - find / ...                          (filesystem scans)
--   failed     - non-zero exit, interrupted, or stderr hints "command not found" / "No such file"
-- Output columns: category, argv0, command, cwd, n, sessions, last_seen, sample_stderr.

CREATE OR REPLACE TEMP VIEW events AS
SELECT
  json_extract_string(json, '$.ts')                       AS ts,
  json_extract_string(json, '$.event')                    AS event,
  json_extract_string(json, '$.session_id')               AS session_id,
  json_extract_string(json, '$.cwd')                      AS cwd,
  json_extract_string(json, '$.tool_name')                AS tool_name,
  json_extract_string(json, '$.tool_input_summary')       AS command,
  json_extract_string(json, '$.stderr_tail')              AS stderr_tail,
  TRY_CAST(json_extract(json, '$.exit_code')   AS INTEGER) AS exit_code,
  TRY_CAST(json_extract(json, '$.interrupted') AS BOOLEAN) AS interrupted
FROM read_ndjson_objects('__LOG_GLOB__')
WHERE json_extract_string(json, '$.ts') >= '__SINCE_TS__';

WITH bash_runs AS (
  SELECT
    ts,
    session_id,
    cwd,
    command,
    COALESCE(exit_code, 0)         AS exit_code,
    COALESCE(interrupted, false)   AS interrupted,
    COALESCE(stderr_tail, '')      AS stderr_tail
  FROM events
  WHERE event = 'tool_executed'
    AND tool_name = 'Bash'
    AND command IS NOT NULL
),
classified AS (
  SELECT
    *,
    CASE
      WHEN regexp_matches(command, '^\s*(which|command\s+-v|command\s+-V|where\s+\w|type\s+\w)') THEN 'discovery'
      WHEN regexp_matches(command, '^\s*find\s+/')                                                 THEN 'fs_search'
      WHEN exit_code <> 0 OR interrupted                                                           THEN 'failed'
      WHEN stderr_tail ILIKE '%command not found%'
        OR stderr_tail ILIKE '%: not found%'
        OR stderr_tail ILIKE '%not installed%'
        OR stderr_tail ILIKE '%No such file or directory%'                                         THEN 'failed'
      ELSE 'other'
    END                                                  AS category,
    regexp_extract(command, '^\s*([^\s|;&]+)', 1)        AS argv0
  FROM bash_runs
)
SELECT
  category,
  argv0,
  command,
  cwd,
  COUNT(*)                       AS n,
  COUNT(DISTINCT session_id)     AS sessions,
  MAX(ts)                        AS last_seen,
  MAX(NULLIF(stderr_tail, ''))   AS sample_stderr
FROM classified
WHERE category <> 'other'
GROUP BY category, argv0, command, cwd
ORDER BY category, n DESC, last_seen DESC;
