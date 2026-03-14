// Count relation fact edges by relation type.

MATCH ()-[r:HAS_RELATION_FACT]->()
RETURN
  r.relation_type AS relation_type,
  count(*) AS fact_count
ORDER BY fact_count DESC;
