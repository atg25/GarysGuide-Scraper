SELECT
  (SELECT COUNT(*) FROM runs) AS runs_count,
  (SELECT COUNT(*) FROM products) AS products_count,
  (SELECT COUNT(*) FROM product_snapshots) AS snapshots_count;
