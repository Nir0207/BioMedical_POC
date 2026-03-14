// Count nodes by domain label after a load.

MATCH (n:Entity)
RETURN
  n.label AS label,
  count(*) AS node_count
ORDER BY node_count DESC;
