import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Box, Paper, Stack, Typography } from "@mui/material";
import { fetchCypherQueries, executeCypherQuery } from "../services/data";
import { QueryCatalogList } from "../components/QueryCatalogList";
import { QueryParameterForm } from "../components/QueryParameterForm";
import { ResultsTable } from "../components/ResultsTable";
import type { CypherQueryDefinition } from "../types/api";

export function QueryWorkbenchPage() {
  const [selectedQuery, setSelectedQuery] = useState<CypherQueryDefinition | null>(null);

  const queriesQuery = useQuery({
    queryKey: ["cypher-queries"],
    queryFn: fetchCypherQueries
  });

  const orderedQueries = useMemo(() => queriesQuery.data ?? [], [queriesQuery.data]);
  const activeQuery = selectedQuery ?? orderedQueries[0] ?? null;

  const executionMutation = useMutation({
    mutationFn: (parameters: Record<string, string | number>) =>
      executeCypherQuery(activeQuery!.endpoint_path, parameters)
  });

  return (
    <Stack spacing={4}>
      <Stack spacing={1}>
        <Typography variant="overline" className="tracking-[0.28em] text-sea">
          Query Workbench
        </Typography>
        <Typography variant="h3">Run backend-managed Cypher endpoints.</Typography>
        <Typography color="text.secondary">
          Every route here is backed by a `.cypher` file. Query docs and parameter help come from the file metadata.
        </Typography>
      </Stack>
      {queriesQuery.error ? <Alert severity="error">Failed to load query catalog.</Alert> : null}
      <Box className="grid gap-3 lg:grid-cols-[0.95fr_1.45fr]">
        <Box>
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-4 shadow-dashboard">
            <Stack spacing={2}>
              <Typography variant="h6">Available endpoints</Typography>
              <QueryCatalogList
                queries={orderedQueries}
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
                <Stack spacing={1.5}>
                  <Typography variant="h5">{activeQuery.name.replaceAll("_", " ")}</Typography>
                  <Typography color="text.secondary">{activeQuery.description}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Route: {activeQuery.endpoint_path}
                  </Typography>
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
                <Alert severity="error">Query execution failed. Validate the parameter values.</Alert>
              ) : null}
              <Stack spacing={2}>
                <Typography variant="h6">
                  Results {executionMutation.data ? `(${executionMutation.data.record_count})` : ""}
                </Typography>
                <ResultsTable records={executionMutation.data?.records ?? []} />
              </Stack>
            </Stack>
          ) : (
            <Alert severity="info">No query endpoints are currently available.</Alert>
          )}
        </Box>
      </Box>
    </Stack>
  );
}
