// Core uniqueness constraints for the biomedical KG.

CREATE CONSTRAINT graph_node_id IF NOT EXISTS
FOR (n:Entity)
REQUIRE n.node_id IS UNIQUE;

CREATE CONSTRAINT graph_edge_id IF NOT EXISTS
FOR ()-[r:RELATED_TO]-()
REQUIRE r.edge_id IS UNIQUE;

CREATE CONSTRAINT graph_relation_id IF NOT EXISTS
FOR ()-[r:HAS_RELATION_FACT]-()
REQUIRE r.relation_id IS UNIQUE;
