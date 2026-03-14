// Should return zero rows if edge uniqueness is intact.

MATCH ()-[r:RELATED_TO]->()
WITH r.edge_id AS edge_id, count(*) AS cnt
WHERE cnt > 1
RETURN edge_id, cnt
ORDER BY cnt DESC, edge_id;
