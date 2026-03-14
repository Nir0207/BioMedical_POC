// Show coverage of loaded nodes by source system.

MATCH (n:Entity)
RETURN
  n.source AS source,
  count(*) AS node_count
ORDER BY node_count DESC;
