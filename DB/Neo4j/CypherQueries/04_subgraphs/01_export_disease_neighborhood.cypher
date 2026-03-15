// Extract a disease-centered neighborhood for downstream inspection.
// :param disease_node_id => Disease entity node_id. Example: MONDO_0007254;
// :param max_hops => Maximum traversal depth for RELATED_TO hops. Example: 2;

MATCH (d:Entity:Disease {node_id: $disease_node_id})
CALL {
  WITH d
  MATCH path = (target:Entity)-[:HAS_RELATION_FACT]->(d)
  RETURN path
  LIMIT 100

  UNION

  WITH d
  WITH d, toInteger($max_hops) AS max_hops
  WHERE max_hops > 1
  MATCH (target:Entity)-[:HAS_RELATION_FACT]->(d)
  WITH DISTINCT target
  LIMIT 25
  MATCH path = (target)-[:RELATED_TO]-(neighbor:Entity)
  RETURN path
  LIMIT 100
}
RETURN path
LIMIT 200;
