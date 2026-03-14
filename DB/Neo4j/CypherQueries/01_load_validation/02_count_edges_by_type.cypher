// Count normalized KG edges by semantic type.

MATCH ()-[r:RELATED_TO]->()
RETURN
  r.relationship_type AS relationship_type,
  count(*) AS edge_count
ORDER BY edge_count DESC;
