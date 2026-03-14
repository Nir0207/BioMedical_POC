// Relation facts without backing nodes should never exist.

MATCH ()-[r:HAS_RELATION_FACT]->()
WHERE r.relation_id IS NULL OR r.relation_type IS NULL
RETURN r
LIMIT 100;
