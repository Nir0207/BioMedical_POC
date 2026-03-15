import { useQuery } from "@tanstack/react-query";
import { Alert, Box, Paper, Stack, Typography } from "@mui/material";
import { fetchCypherQueries, fetchNeo4jSummary, fetchPostgresSummary } from "../services/data";
import { useAuth } from "../features/auth/AuthContext";
import { MetricCard } from "../components/MetricCard";

export function DashboardPage() {
  const { user } = useAuth();
  const postgresSummaryQuery = useQuery({
    queryKey: ["postgres-summary"],
    queryFn: fetchPostgresSummary
  });
  const graphSummaryQuery = useQuery({
    queryKey: ["neo4j-summary"],
    queryFn: fetchNeo4jSummary
  });
  const queriesQuery = useQuery({
    queryKey: ["cypher-queries"],
    queryFn: fetchCypherQueries
  });

  const error = postgresSummaryQuery.error ?? graphSummaryQuery.error ?? queriesQuery.error;

  return (
    <Stack spacing={4}>
      <Stack spacing={1}>
        <Typography variant="overline" className="tracking-[0.28em] text-sea">
          Control Room
        </Typography>
        <Typography variant="h3">Welcome back, {user?.full_name?.split(" ")[0] ?? "Analyst"}.</Typography>
        <Typography color="text.secondary">
          Monitor backend auth usage, graph volume, and the current executable Cypher surface.
        </Typography>
      </Stack>
      {error ? (
        <Alert severity="error">Failed to load dashboard data. Check backend and authentication state.</Alert>
      ) : null}
      <Box className="grid gap-3 md:grid-cols-3">
        <Box>
          <MetricCard
            eyebrow="Postgres Users"
            value={String(postgresSummaryQuery.data?.user_count ?? "--")}
            detail="Authenticated application users stored in Postgres."
            testId="metric-postgres-users"
          />
        </Box>
        <Box>
          <MetricCard
            eyebrow="Graph Nodes"
            value={String(graphSummaryQuery.data?.nodes ?? "--")}
            detail="Current entity count available in Neo4j."
            testId="metric-graph-nodes"
          />
        </Box>
        <Box>
          <MetricCard
            eyebrow="Published Queries"
            value={String(queriesQuery.data?.length ?? "--")}
            detail="Non-maintenance Cypher routes exposed by FastAPI."
            testId="metric-published-queries"
          />
        </Box>
      </Box>
      <Box className="grid gap-3 lg:grid-cols-[1.4fr_1fr]">
        <Box>
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
            <Stack spacing={2}>
              <Typography variant="h5">Cypher coverage by category</Typography>
              {Object.entries(
                (queriesQuery.data ?? []).reduce<Record<string, number>>((accumulator, query) => {
                  accumulator[query.category] = (accumulator[query.category] ?? 0) + 1;
                  return accumulator;
                }, {})
              ).map(([category, count]) => (
                <Stack key={category} direction="row" justifyContent="space-between">
                  <Typography>{category}</Typography>
                  <Typography fontWeight={700}>{count}</Typography>
                </Stack>
              ))}
            </Stack>
          </Paper>
        </Box>
        <Box>
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
            <Stack spacing={2}>
              <Typography variant="h5">Featured routes</Typography>
              {(queriesQuery.data ?? []).slice(0, 4).map((query) => (
                <Stack key={query.query_id} spacing={0.5}>
                  <Typography fontWeight={700}>{query.name.replaceAll("_", " ")}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {query.description}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          </Paper>
        </Box>
      </Box>
    </Stack>
  );
}
