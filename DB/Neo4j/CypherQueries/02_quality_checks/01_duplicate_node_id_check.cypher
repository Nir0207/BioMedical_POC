// Should return zero rows if node uniqueness is intact.

MATCH (n:Entity)
WITH n.node_id AS node_id, count(*) AS cnt
WHERE cnt > 1
RETURN node_id, cnt
ORDER BY cnt DESC, node_id;
