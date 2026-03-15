import type {
  CypherQueryDefinition,
  CypherQueryExecutionResponse,
  GraphSummary,
  PostgresSummary,
  QueryCanvasCategory,
  QueryCanvasNode,
  QueryCanvasRelationValidationResponse,
  QueryCanvasRunResponse,
  User
} from "../types/api";

export const mockUser: User = {
  id: 7,
  email: "graph@example.com",
  full_name: "Graph Analyst",
  is_active: true,
  created_at: "2026-03-14T08:00:00Z"
};

export const mockPostgresSummary: PostgresSummary = {
  user_count: 14
};

export const mockGraphSummary: GraphSummary = {
  nodes: 175800,
  relationships: 9780872
};

export const mockCypherQueries: CypherQueryDefinition[] = [
  {
    query_id: "00_constraints/01_core_constraints",
    category: "00_constraints",
    name: "01_core_constraints",
    description: "Core graph constraints.",
    parameters: [],
    parameter_help: {},
    endpoint_path: "/api/v1/data/neo4j/queries/00_constraints/01_core_constraints"
  },
  {
    query_id: "01_load_validation/01_count_nodes_by_label",
    category: "01_load_validation",
    name: "01_count_nodes_by_label",
    description: "Count nodes by domain label after a load.",
    parameters: [],
    parameter_help: {},
    endpoint_path: "/api/v1/data/neo4j/queries/01_load_validation/01_count_nodes_by_label"
  },
  {
    query_id: "03_exploration/04_disease_target_ranking",
    category: "03_exploration",
    name: "04_disease_target_ranking",
    description: "Rank targets for a disease by Open Targets score.",
    parameters: ["disease_node_id"],
    parameter_help: {
      disease_node_id: "Disease entity node_id. Example: EFO:0000311"
    },
    endpoint_path: "/api/v1/data/neo4j/queries/03_exploration/04_disease_target_ranking"
  },
  {
    query_id: "03_exploration/03_protein_pathway_membership",
    category: "03_exploration",
    name: "03_protein_pathway_membership",
    description: "Show pathways for a protein.",
    parameters: ["protein_node_id"],
    parameter_help: {
      protein_node_id: "Protein entity node_id. Example: UNIPROT:P04637"
    },
    endpoint_path: "/api/v1/data/neo4j/queries/03_exploration/03_protein_pathway_membership"
  },
  {
    query_id: "04_subgraphs/01_export_disease_neighborhood",
    category: "04_subgraphs",
    name: "01_export_disease_neighborhood",
    description: "Extract a disease-centered neighborhood for downstream inspection.",
    parameters: ["disease_node_id", "max_hops"],
    parameter_help: {
      disease_node_id: "Disease entity node_id. Example: EFO:0000311",
      max_hops: "Maximum traversal depth for RELATED_TO hops. Example: 2"
    },
    endpoint_path: "/api/v1/data/neo4j/queries/04_subgraphs/01_export_disease_neighborhood"
  }
];

export const mockQueryCanvasCategories: QueryCanvasCategory[] = [
  { category: "Gene", count: 98939 },
  { category: "Disease", count: 46960 },
  { category: "Protein", count: 21961 }
];

export const mockQueryCanvasNodes: QueryCanvasNode[] = [
  {
    node_id: "ENSG00000141510",
    name: "TP53",
    category: "Gene",
    labels: ["Entity", "Gene"]
  },
  {
    node_id: "MONDO_0007254",
    name: "breast cancer",
    category: "Disease",
    labels: ["Entity", "Disease"]
  },
  {
    node_id: "UNIPROT:P04637",
    name: "P04637",
    category: "Protein",
    labels: ["Entity", "Protein"]
  }
];

export const mockQueryCanvasValidation: QueryCanvasRelationValidationResponse = {
  source: mockQueryCanvasNodes[0],
  target: mockQueryCanvasNodes[1],
  exists: true,
  related_to_types: ["ASSOCIATED_WITH"],
  relation_fact_types: ["TARGET_DISEASE_ASSOCIATION"],
  message: "Direct relation found between the selected nodes.",
  generated_cypher: [
    "MATCH (source:Entity {node_id: $source_node_id})",
    "MATCH (target:Entity {node_id: $target_node_id})",
    "OPTIONAL MATCH direct_path = (source)-[:RELATED_TO]-(target)",
    "RETURN direct_path"
  ].join("\n"),
  parameters: {
    source_node_id: "ENSG00000141510",
    target_node_id: "MONDO_0007254",
    neighbor_limit: 8
  }
};

export const mockRankingResponse: CypherQueryExecutionResponse = {
  query_id: "03_exploration/04_disease_target_ranking",
  record_count: 1,
  records: [
    {
      "target.node_id": "ENSG00000141510",
      "target.name": "TP53",
      "r.score": 0.91,
      "r.evidence": "Open Targets"
    }
  ]
};

export const mockGraphResponse: CypherQueryExecutionResponse = {
  query_id: "04_subgraphs/01_export_disease_neighborhood",
  record_count: 1,
  records: [
    {
      path: {
        nodes: [
          {
            id: 1,
            labels: ["Entity", "Disease"],
            properties: {
              node_id: "MONDO_0007254",
              name: "breast cancer"
            }
          },
          {
            id: 2,
            labels: ["Entity", "Gene"],
            properties: {
              node_id: "ENSG00000141510",
              name: "TP53"
            }
          }
        ],
        relationships: [
          {
            id: 10,
            type: "RELATED_TO",
            start_node_id: 1,
            end_node_id: 2,
            properties: {
              edge_id: "edge-1",
              relationship_type: "ASSOCIATED_WITH",
              source_node_id: "MONDO_0007254",
              target_node_id: "ENSG00000141510"
            }
          }
        ]
      }
    }
  ]
};

export const mockQueryCanvasRunResponse: QueryCanvasRunResponse = {
  query_id: "query_canvas_relation",
  record_count: 3,
  executed_cypher: mockQueryCanvasValidation.generated_cypher,
  parameters: mockQueryCanvasValidation.parameters,
  records: [
    {
      source_node: {
        id: 1,
        labels: ["Entity", "Gene"],
        properties: {
          node_id: "ENSG00000141510",
          name: "TP53"
        }
      },
      target_node: {
        id: 2,
        labels: ["Entity", "Disease"],
        properties: {
          node_id: "MONDO_0007254",
          name: "breast cancer"
        }
      }
    },
    ...mockGraphResponse.records,
    {
      path: {
        nodes: [
          {
            id: 1,
            labels: ["Entity", "Gene"],
            properties: {
              node_id: "ENSG00000141510",
              name: "TP53"
            }
          },
          {
            id: 3,
            labels: ["Entity", "Protein"],
            properties: {
              node_id: "UNIPROT:P04637",
              name: "P04637"
            }
          }
        ],
        relationships: [
          {
            id: 11,
            type: "RELATED_TO",
            start_node_id: 1,
            end_node_id: 3,
            properties: {
              edge_id: "edge-2",
              relationship_type: "ENCODES",
              source_node_id: "ENSG00000141510",
              target_node_id: "UNIPROT:P04637"
            }
          }
        ]
      }
    }
  ]
};
