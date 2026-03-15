export interface GraphNodeDatum {
  id: string;
  label: string;
  category: string;
  color: string;
}

export interface GraphLinkDatum {
  id: string;
  source: string;
  target: string;
  label: string;
}

export interface GraphDataSet {
  nodes: GraphNodeDatum[];
  links: GraphLinkDatum[];
}
