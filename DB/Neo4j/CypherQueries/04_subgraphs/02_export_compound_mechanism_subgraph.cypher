// Extract a compound-target mechanism subgraph.
// :param compound_node_id => 'CHEMBL:CHEMBL25';

MATCH path = (c:Entity {node_id: $compound_node_id})-[r:RELATED_TO]->(target:Entity)
WHERE r.relationship_type = 'TARGETS'
OPTIONAL MATCH fact_path = (c)-[f:HAS_RELATION_FACT]->(target)
RETURN path, fact_path
LIMIT 100;
