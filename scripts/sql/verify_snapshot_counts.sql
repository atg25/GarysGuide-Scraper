SELECT
  (SELECT COUNT(*) FROM runs) AS runs_count,
  (SELECT COUNT(*) FROM "all events") AS all_events_count,
  (SELECT COUNT(*) FROM weekly_events) AS weekly_events_count;
