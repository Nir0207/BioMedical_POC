// Show pathways for a protein.
// :param protein_node_id => 'UNIPROT:P04637';

MATCH (p:Entity {node_id: $protein_node_id})-[r:RELATED_TO]->(pathway:Entity)
WHERE r.relationship_type = 'PARTICIPATES_IN'
RETURN pathway.node_id, pathway.name, r.evidence
ORDER BY pathway.name;
