// Extract a disease-centered neighborhood for downstream inspection.
// :param disease_node_id => 'EFO:0000311';
// :param max_hops => 2;

MATCH (d:Entity {node_id: $disease_node_id})
MATCH path = (d)-[:RELATED_TO*1..$max_hops]-(neighbor:Entity)
RETURN path
LIMIT 200;
