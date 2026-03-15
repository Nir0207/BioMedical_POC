import type { GraphDataSet, GraphLinkDatum, GraphNodeDatum } from "../types/graph";

const CATEGORY_COLORS: Record<string, string> = {
  Disease: "#b3523b",
  Gene: "#1d4d5b",
  Protein: "#2f6b5f",
  Compound: "#c98f42",
  Pathway: "#6c5b7b",
  default: "#41525d"
};

interface Neo4jNodeLike {
  id?: string | number;
  labels?: string[];
  properties?: Record<string, unknown>;
}

interface Neo4jRelationshipLike {
  id?: string | number;
  type?: string;
  start_node_id?: string | number;
  end_node_id?: string | number;
  properties?: Record<string, unknown>;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isNodeLike(value: unknown): value is Neo4jNodeLike {
  return isObject(value) && Array.isArray(value.labels) && isObject(value.properties);
}

function isRelationshipLike(value: unknown): value is Neo4jRelationshipLike {
  return (
    isObject(value) &&
    "start_node_id" in value &&
    "end_node_id" in value &&
    "properties" in value
  );
}

function extractNode(node: Neo4jNodeLike): GraphNodeDatum {
  const properties = node.properties ?? {};
  const categoryLabel =
    node.labels?.find((label) => label !== "Entity") ?? String(properties.label ?? node.labels?.[0] ?? "Entity");
  const category = String(categoryLabel);
  const id = String(properties.node_id ?? node.id ?? crypto.randomUUID());
  return {
    id,
    label: String(properties.name ?? properties.node_id ?? id),
    category,
    color: CATEGORY_COLORS[category] ?? CATEGORY_COLORS.default
  };
}

function extractLink(relationship: Neo4jRelationshipLike): GraphLinkDatum {
  const properties = relationship.properties ?? {};
  const start = String(properties.source_node_id ?? relationship.start_node_id ?? "");
  const end = String(properties.target_node_id ?? relationship.end_node_id ?? "");
  const relationshipType = String(properties.relationship_type ?? properties.relation_type ?? relationship.type ?? "RELATED_TO");
  return {
    id: String(properties.edge_id ?? relationship.id ?? `${start}-${end}-${relationshipType}`),
    source: start,
    target: end,
    label: relationshipType
  };
}

export function extractGraphData(records: Array<Record<string, unknown>>): GraphDataSet {
  const nodeMap = new Map<string, GraphNodeDatum>();
  const linkMap = new Map<string, GraphLinkDatum>();

  function walk(value: unknown): void {
    if (Array.isArray(value)) {
      value.forEach(walk);
      return;
    }

    if (isNodeLike(value)) {
      const node = extractNode(value);
      nodeMap.set(node.id, node);
      return;
    }

    if (isRelationshipLike(value)) {
      const link = extractLink(value);
      if (link.source && link.target) {
        linkMap.set(link.id, link);
      }
      return;
    }

    if (isObject(value) && Array.isArray((value as { nodes?: unknown[] }).nodes)) {
      walk((value as { nodes: unknown[] }).nodes);
    }

    if (isObject(value) && Array.isArray((value as { relationships?: unknown[] }).relationships)) {
      walk((value as { relationships: unknown[] }).relationships);
    }

    if (isObject(value)) {
      Object.values(value).forEach(walk);
    }
  }

  records.forEach(walk);

  return {
    nodes: Array.from(nodeMap.values()),
    links: Array.from(linkMap.values())
  };
}
