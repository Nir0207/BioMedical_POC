// Rank targets for a disease by Open Targets score.
// :param disease_node_id => Disease entity node_id. Example: MONDO_0007254;

MATCH (target:Entity)-[r:HAS_RELATION_FACT]->(disease:Entity {node_id: $disease_node_id})
WHERE r.relation_type = 'TARGET_DISEASE_ASSOCIATION'
RETURN target.node_id, target.name, r.score, r.evidence
ORDER BY r.score DESC NULLS LAST
LIMIT 100;
