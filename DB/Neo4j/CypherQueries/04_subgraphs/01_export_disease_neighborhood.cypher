// Extract a disease-centered neighborhood for downstream inspection.
// :param disease_node_id => Disease entity node_id. Example: EFO:0000311;
// :param max_hops => Maximum traversal depth for RELATED_TO hops. Example: 2;

MATCH (d:Entity {node_id: $disease_node_id})
MATCH path = (d)-[:RELATED_TO*1..$max_hops]-(neighbor:Entity)
RETURN path
LIMIT 200;
