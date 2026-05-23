-- Mode B: prompt extract for in-session LLM judging.
-- Returns intent-shaped prompts (length >= 20 chars) ordered newest-first.
-- The skill (Claude in-session) scores each against the rubric in SKILL.md.

CREATE OR REPLACE TEMP VIEW events AS
SELECT
  json_extract_string(json, '$.ts')         AS ts,
  json_extract_string(json, '$.event')      AS event,
  json_extract_string(json, '$.session_id') AS session_id,
  json_extract_string(json, '$.cwd')        AS cwd,
  json_extract_string(json, '$.prompt')     AS prompt
FROM read_ndjson_objects('__LOG_GLOB__')
WHERE json_extract_string(json, '$.ts') >= '__SINCE_TS__';

SELECT
  ts,
  session_id,
  cwd,
  length(prompt) AS prompt_len,
  prompt
FROM events
WHERE event = 'user_prompt'
  AND prompt IS NOT NULL
  AND length(prompt) >= 20
ORDER BY ts DESC;
