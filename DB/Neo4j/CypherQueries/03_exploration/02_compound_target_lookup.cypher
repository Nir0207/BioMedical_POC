// Return compounds targeting a given protein accession.
// :param protein_node_id => 'UNIPROT:P35354';

MATCH (c:Entity {label: 'Compound'})-[r:RELATED_TO]->(p:Entity {node_id: $protein_node_id})
WHERE r.relationship_type = 'TARGETS'
RETURN c.node_id, c.name, r.evidence, r.properties_json
ORDER BY c.name;
