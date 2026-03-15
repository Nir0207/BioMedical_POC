// Find graph paths between a gene entity and disease entities.
// :param gene_id => Gene entity node_id. Example: ENSG000001;
// :param max_hops => Maximum traversal depth for RELATED_TO hops. Example: 3;

MATCH (g:Entity:Gene {node_id: $gene_id})
CALL {
  WITH g
  MATCH path = (g)-[:HAS_RELATION_FACT]->(d:Entity:Disease)
  RETURN path

  UNION

  WITH g
  CALL apoc.path.expandConfig(
    g,
    {
      relationshipFilter: "RELATED_TO",
      minLevel: 1,
      maxLevel: toInteger($max_hops),
      bfs: true,
      uniqueness: "NODE_PATH"
    }
  ) YIELD path
  WITH path, last(nodes(path)) AS d
  WHERE d:Disease
  RETURN path
}
RETURN path
LIMIT 50;
