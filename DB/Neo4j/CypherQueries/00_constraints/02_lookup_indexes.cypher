// Optional lookup indexes for common analyst filters.

CREATE INDEX entity_label_lookup IF NOT EXISTS
FOR (n:Entity)
ON (n.label);

CREATE INDEX entity_source_lookup IF NOT EXISTS
FOR (n:Entity)
ON (n.source);

CREATE INDEX related_to_type_lookup IF NOT EXISTS
FOR ()-[r:RELATED_TO]-()
ON (r.relationship_type);

CREATE INDEX relation_fact_type_lookup IF NOT EXISTS
FOR ()-[r:HAS_RELATION_FACT]-()
ON (r.relation_type);
