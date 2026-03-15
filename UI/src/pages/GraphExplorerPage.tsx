import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Box, Paper, Stack, Typography } from "@mui/material";
import { fetchCypherQueries, executeCypherQuery } from "../services/data";
import { GraphCanvas } from "../components/GraphCanvas";
import { QueryCatalogList } from "../components/QueryCatalogList";
import { QueryParameterForm } from "../components/QueryParameterForm";
import type { CypherQueryDefinition } from "../types/api";
import { extractGraphData } from "../utils/graph";

const GRAPH_QUERY_IDS = new Set([
  "03_exploration/01_gene_to_disease_paths",
  "03_exploration/03_protein_pathway_membership",
  "04_subgraphs/01_export_disease_neighborhood",
  "04_subgraphs/02_export_compound_mechanism_subgraph"
]);

export function GraphExplorerPage() {
  const [selectedQuery, setSelectedQuery] = useState<CypherQueryDefinition | null>(null);
  const queriesQuery = useQuery({
    queryKey: ["cypher-queries"],
    queryFn: fetchCypherQueries
  });

  const graphQueries = useMemo(
    () => (queriesQuery.data ?? []).filter((query) => GRAPH_QUERY_IDS.has(query.query_id)),
    [queriesQuery.data]
  );
  const activeQuery = selectedQuery ?? graphQueries[0] ?? null;

  const executionMutation = useMutation({
    mutationFn: (parameters: Record<string, string | number>) =>
      executeCypherQuery(activeQuery!.endpoint_path, parameters)
  });

  const graphData = useMemo(
    () => extractGraphData(executionMutation.data?.records ?? []),
    [executionMutation.data?.records]
  );

  return (
    <Stack spacing={4}>
      <Stack spacing={1}>
        <Typography variant="overline" className="tracking-[0.28em] text-sea">
          Graph Explorer
        </Typography>
        <Typography variant="h3">Inspect paths and subgraphs interactively.</Typography>
        <Typography color="text.secondary">
          Use graph-oriented Cypher endpoints and render the returned Neo4j structures as an interactive canvas.
        </Typography>
      </Stack>
      <Box className="grid gap-3 lg:grid-cols-[0.95fr_1.45fr]">
        <Box>
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-4 shadow-dashboard">
            <Stack spacing={2}>
              <Typography variant="h6">Graph-capable endpoints</Typography>
              <QueryCatalogList
                queries={graphQueries}
                selectedQueryId={activeQuery?.query_id ?? null}
                onSelect={setSelectedQuery}
              />
            </Stack>
          </Paper>
        </Box>
        <Box>
          {activeQuery ? (
            <Stack spacing={3}>
              <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
                <Stack spacing={1}>
                  <Typography variant="h5">{activeQuery.name.replaceAll("_", " ")}</Typography>
                  <Typography color="text.secondary">{activeQuery.description}</Typography>
                </Stack>
              </Paper>
              <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
                <QueryParameterForm
                  query={activeQuery}
                  isSubmitting={executionMutation.isPending}
                  onSubmit={(parameters) => executionMutation.mutate(parameters)}
                />
              </Paper>
              {executionMutation.error ? (
                <Alert severity="error">Failed to load graph data. Check parameter values.</Alert>
              ) : null}
              {executionMutation.data ? (
                graphData.nodes.length > 0 ? (
                  <GraphCanvas data={graphData} title={activeQuery.name.replaceAll("_", " ")} />
                ) : (
                  <Alert severity="warning">
                    The query returned records, but they did not contain graph paths or graph-structured nodes and links.
                  </Alert>
                )
              ) : (
                <Alert severity="info">Run a graph query to populate the canvas.</Alert>
              )}
            </Stack>
          ) : (
            <Alert severity="info">No graph-capable query endpoints were published by the backend.</Alert>
          )}
        </Box>
      </Box>
    </Stack>
  );
}
