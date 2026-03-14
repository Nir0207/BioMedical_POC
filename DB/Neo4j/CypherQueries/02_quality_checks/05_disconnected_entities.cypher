// Entities with no graph relationships can indicate transform issues.

MATCH (n:Entity)
WHERE NOT (n)-[:RELATED_TO]-()
RETURN n.label AS label, n.node_id AS node_id, n.name AS name, n.source AS source
LIMIT 200;
