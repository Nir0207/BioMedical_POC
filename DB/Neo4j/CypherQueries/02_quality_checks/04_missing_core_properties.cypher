// Find entities missing critical fields used in downstream analysis.

MATCH (n:Entity)
WHERE n.node_id IS NULL
   OR n.name IS NULL
   OR n.label IS NULL
   OR n.source IS NULL
RETURN n
LIMIT 100;
