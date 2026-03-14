// Find graph paths between a gene entity and disease entities.
// :param gene_id => Gene entity node_id. Example: ENSG000001;
// :param max_hops => Maximum traversal depth for RELATED_TO hops. Example: 3;

MATCH (g:Entity {node_id: $gene_id})
MATCH path = (g)-[:RELATED_TO*1..$max_hops]-(d:Entity)
WHERE d.label = 'Disease'
RETURN path
LIMIT 50;
