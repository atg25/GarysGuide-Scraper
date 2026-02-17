SELECT name, type
FROM sqlite_master
WHERE type IN ('table', 'index')
  AND name IN ('runs', 'products', 'product_snapshots');
