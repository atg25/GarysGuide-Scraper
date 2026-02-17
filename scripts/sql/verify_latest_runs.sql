SELECT id, source, fetched_at, search_term, record_limit, status, fetched_count, attempts, error
FROM runs
ORDER BY id DESC
LIMIT 10;
