// Parameters:
// :param gene_id => 'ENSG000001';
// :param max_hops => 3;

MATCH (g:Entity {node_id: $gene_id})
MATCH path = (g)-[:RELATED_TO*1..$max_hops]-(d:Entity)
WHERE d.label = 'Disease'
RETURN path
LIMIT 50;
