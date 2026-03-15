import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  Paper,
  Slider,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography
} from "@mui/material";
import PlayArrowRoundedIcon from "@mui/icons-material/PlayArrowRounded";
import TaskAltRoundedIcon from "@mui/icons-material/TaskAltRounded";
import PendingRoundedIcon from "@mui/icons-material/PendingRounded";
import ErrorRoundedIcon from "@mui/icons-material/ErrorRounded";
import ChevronRightRoundedIcon from "@mui/icons-material/ChevronRightRounded";
import SchemaRoundedIcon from "@mui/icons-material/SchemaRounded";
import BiotechRoundedIcon from "@mui/icons-material/BiotechRounded";
import DataObjectRoundedIcon from "@mui/icons-material/DataObjectRounded";
import LibraryBooksRoundedIcon from "@mui/icons-material/LibraryBooksRounded";
import HubRoundedIcon from "@mui/icons-material/HubRounded";
import { runAgenticResearchQuery } from "../services/agentic";
import type { AgenticResearchQueryResponse } from "../types/api";

type StageState = "idle" | "running" | "done" | "warning" | "failed" | "skipped";

const suggestedQueries = [
  "Find key targets for breast cancer and summarize evidence",
  "Prioritize targets for rheumatoid arthritis with pathway context",
  "Show protein interaction-backed targets for glioblastoma",
  "Which compounds are linked to Parkinson disease targets?"
];

const workflowStages = [
  { key: "query_intake", title: "Query Intake", detail: "Normalizes user question and parameters." },
  { key: "intent_module_router", title: "Intent Router", detail: "Routes to disease target discovery module." },
  { key: "entity_resolution", title: "Entity Resolution", detail: "Resolves disease entities from query text." },
  { key: "graph_query_planning", title: "Graph Planning", detail: "Builds bounded tool plan and graph strategy." },
  { key: "graph_retrieval", title: "Graph Retrieval", detail: "Collects disease → gene → protein graph context." },
  { key: "evidence_retrieval", title: "Evidence Retrieval", detail: "Performs hybrid evidence retrieval (graph + vector)." },
  { key: "optional_ranking", title: "Target Ranking", detail: "Ranks targets when ranking is needed." },
  { key: "answer_synthesis", title: "Answer Synthesis", detail: "Synthesizes answer from retrieved context only." },
  { key: "response_formatting", title: "Response Format", detail: "Returns structured answer, citations, graph payload." }
] as const;

function getString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function getNumber(value: unknown): number {
  if (typeof value === "number") {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

function stageColor(state: StageState): "default" | "success" | "warning" | "error" | "primary" {
  if (state === "done") return "success";
  if (state === "warning") return "warning";
  if (state === "failed") return "error";
  if (state === "running") return "primary";
  return "default";
}

function stageLabel(state: StageState): string {
  if (state === "done") return "Done";
  if (state === "running") return "Running";
  if (state === "warning") return "Partial";
  if (state === "failed") return "Failed";
  if (state === "skipped") return "Skipped";
  return "Idle";
}

function stageIcon(state: StageState) {
  if (state === "done") return <TaskAltRoundedIcon fontSize="small" color="success" />;
  if (state === "running") return <PendingRoundedIcon fontSize="small" color="primary" />;
  if (state === "warning") return <ErrorRoundedIcon fontSize="small" color="warning" />;
  if (state === "failed") return <ErrorRoundedIcon fontSize="small" color="error" />;
  if (state === "skipped") return <PendingRoundedIcon fontSize="small" color="disabled" />;
  return <PendingRoundedIcon fontSize="small" color="disabled" />;
}

function resolveStageState(
  stageKey: (typeof workflowStages)[number]["key"],
  payload: AgenticResearchQueryResponse | undefined,
  isPending: boolean,
  hasError: boolean
): StageState {
  if (hasError) {
    return "failed";
  }

  if (!payload) {
    if (isPending && ["query_intake", "intent_module_router", "entity_resolution"].includes(stageKey)) {
      return "running";
    }
    return "idle";
  }

  const hasResolved = payload.resolved_entities.length > 0;
  const hasGraph = (payload.graph_payload.nodes?.length ?? 0) > 0;
  const hasEvidence = payload.citations.length > 0;
  const hasRanking = payload.ranking_results.length > 0;
  const hasErrors = payload.errors.length > 0;

  if (stageKey === "query_intake") return "done";
  if (stageKey === "intent_module_router") return payload.intent ? "done" : "warning";
  if (stageKey === "entity_resolution") return hasResolved ? "done" : "failed";
  if (stageKey === "graph_query_planning") return hasResolved ? "done" : "skipped";
  if (stageKey === "graph_retrieval") return hasGraph ? "done" : hasResolved ? "warning" : "skipped";
  if (stageKey === "evidence_retrieval") {
    if (hasEvidence) return "done";
    if (hasErrors) return "warning";
    return hasResolved ? "warning" : "skipped";
  }
  if (stageKey === "optional_ranking") return hasRanking ? "done" : hasResolved ? "skipped" : "skipped";
  if (stageKey === "answer_synthesis") return payload.final_answer ? (hasErrors ? "warning" : "done") : "failed";
  if (stageKey === "response_formatting") return payload.final_answer ? "done" : "failed";
  return "idle";
}

export function AgenticWorkflowPage() {
  const [query, setQuery] = useState("Find key targets for breast cancer and summarize evidence");
  const [topK, setTopK] = useState(8);

  const mutation = useMutation({
    mutationFn: () =>
      runAgenticResearchQuery({
        user_query: query,
        top_k: topK
      })
  });

  const payload = mutation.data;

  const rankingRows = useMemo(
    () =>
      (payload?.ranking_results ?? []).map((row, index) => ({
        key: `${getString(row["gene_id"]) || "gene"}-${index}`,
        geneId: getString(row["gene_id"]),
        geneSymbol: getString(row["gene_symbol"]) || "n/a",
        score: getNumber(row["score"]),
        evidenceHits: getNumber((row["components"] as Record<string, unknown> | undefined)?.["evidence_hits"])
      })),
    [payload]
  );

  const graphSummary = useMemo(() => {
    const nodes = payload?.graph_payload.nodes ?? [];
    const edges = payload?.graph_payload.edges ?? [];
    const nodeTypeCount = nodes.reduce<Record<string, number>>((accumulator, node) => {
      const type = getString((node as Record<string, unknown>).type) || "Entity";
      accumulator[type] = (accumulator[type] ?? 0) + 1;
      return accumulator;
    }, {});

    return {
      nodes: nodes.length,
      edges: edges.length,
      nodeTypeCount
    };
  }, [payload]);

  const completedStageCount = workflowStages.filter(
    (stage) => resolveStageState(stage.key, payload, mutation.isPending, Boolean(mutation.error)) === "done"
  ).length;

  return (
    <Stack spacing={4}>
      <Paper className="rounded-[32px] border border-white/70 bg-gradient-to-br from-[#fef8ee] via-[#fff6ec] to-[#eef6f7] p-6 shadow-dashboard">
        <Stack spacing={2.5}>
          <Stack spacing={1}>
            <Typography variant="overline" className="tracking-[0.28em] text-sea">
              Agentic Workflow
            </Typography>
            <Typography variant="h3">Graph-grounded disease target research assistant.</Typography>
            <Typography color="text.secondary">
              Production workflow using bounded tool calls, hybrid retrieval, and evidence-first synthesis.
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip icon={<SchemaRoundedIcon />} label="LangGraph Bounded Pipeline" />
            <Chip icon={<HubRoundedIcon />} label="Neo4j Graph Retrieval" />
            <Chip icon={<LibraryBooksRoundedIcon />} label="Chroma Evidence Retrieval" />
            <Chip icon={<BiotechRoundedIcon />} label="Ollama Synthesis (qwen2.5:7b)" />
          </Stack>
        </Stack>
      </Paper>

      <Box className="grid gap-3 lg:grid-cols-[1.25fr_0.75fr]">
        <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
          <Stack spacing={2.5}>
            <Stack spacing={1}>
              <Typography variant="h5">Research Query Composer</Typography>
              <Typography color="text.secondary">
                Ask naturally. The workflow resolves disease entities from your sentence.
              </Typography>
            </Stack>
            <TextField
              label="Research Query"
              multiline
              minRows={3}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              fullWidth
            />
            <Stack spacing={1.25}>
              <Typography variant="subtitle2">Evidence Depth: {topK}</Typography>
              <Slider
                value={topK}
                onChange={(_, value) => setTopK(Array.isArray(value) ? value[0] : value)}
                min={3}
                max={25}
                step={1}
                valueLabelDisplay="auto"
              />
            </Stack>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {suggestedQueries.map((suggestion) => (
                <Chip key={suggestion} label={suggestion} onClick={() => setQuery(suggestion)} variant="outlined" />
              ))}
            </Stack>
            <Box>
              <Button
                variant="contained"
                startIcon={<PlayArrowRoundedIcon />}
                onClick={() => mutation.mutate()}
                disabled={mutation.isPending || query.trim().length < 3}
              >
                {mutation.isPending ? "Running workflow..." : "Run Agentic Workflow"}
              </Button>
            </Box>
          </Stack>
        </Paper>

        <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
          <Stack spacing={2}>
            <Typography variant="h6">Execution Snapshot</Typography>
            <Box className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
              <Paper className="rounded-3xl border border-[#d8ebe0] bg-[#effaf3] p-4 shadow-none">
                <Typography variant="overline" className="tracking-[0.18em] text-sea">
                  Stages Completed
                </Typography>
                <Typography variant="h4">{payload ? `${completedStageCount}/${workflowStages.length}` : "--"}</Typography>
              </Paper>
              <Paper className="rounded-3xl border border-[#e9decc] bg-[#fff8ea] p-4 shadow-none">
                <Typography variant="overline" className="tracking-[0.18em] text-sea">
                  Evidence Chunks
                </Typography>
                <Typography variant="h4">{payload ? payload.citations.length : "--"}</Typography>
              </Paper>
              <Paper className="rounded-3xl border border-[#dce6ec] bg-[#f2f7fb] p-4 shadow-none sm:col-span-2 lg:col-span-1">
                <Typography variant="overline" className="tracking-[0.18em] text-sea">
                  Graph Footprint
                </Typography>
                <Typography variant="h4">{payload ? `${graphSummary.nodes}N / ${graphSummary.edges}E` : "--"}</Typography>
              </Paper>
            </Box>
          </Stack>
        </Paper>
      </Box>

      {mutation.error ? <Alert severity="error">Failed to run agentic workflow.</Alert> : null}

      {payload ? (
        <Box className="grid gap-3 lg:grid-cols-2">
          <Paper className="rounded-[32px] border border-white/70 bg-white/95 p-6 shadow-dashboard">
            <Stack spacing={1.25}>
              <Stack direction="row" spacing={1} alignItems="center">
                <DataObjectRoundedIcon color="primary" />
                <Typography variant="h5">Answer</Typography>
              </Stack>
              <Typography>{payload.final_answer}</Typography>
            </Stack>
          </Paper>

          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
            <Stack spacing={1.5}>
              <Typography variant="h6">Top Ranked Targets</Typography>
              {rankingRows.length === 0 ? (
                <Typography color="text.secondary">Ranking skipped or unavailable.</Typography>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Gene</TableCell>
                        <TableCell>Score</TableCell>
                        <TableCell align="right">Evidence Hits</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {rankingRows.slice(0, 6).map((row) => (
                        <TableRow key={row.key}>
                          <TableCell>{row.geneSymbol !== "n/a" ? row.geneSymbol : row.geneId || "n/a"}</TableCell>
                          <TableCell>{row.score.toFixed(2)}</TableCell>
                          <TableCell align="right">{row.evidenceHits}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Stack>
          </Paper>
        </Box>
      ) : (
        <Alert severity="info">Submit a query to run the workflow.</Alert>
      )}

      <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
        <Stack spacing={1.5}>
          <Typography variant="h6">Workflow Stage Monitor</Typography>
          <Stack direction="row" spacing={0.75} alignItems="center" flexWrap="wrap" useFlexGap>
            {workflowStages.map((stage, index) => {
              const state = resolveStageState(stage.key, payload, mutation.isPending, Boolean(mutation.error));
              return (
                <Stack key={stage.key} direction="row" spacing={0.75} alignItems="center">
                  <Chip
                    size="small"
                    color={stageColor(state)}
                    icon={stageIcon(state)}
                    label={`${stage.title}: ${stageLabel(state)}`}
                    title={stage.detail}
                  />
                  {index < workflowStages.length - 1 ? <ChevronRightRoundedIcon color="disabled" fontSize="small" /> : null}
                </Stack>
              );
            })}
          </Stack>
        </Stack>
      </Paper>

      <Box className="grid gap-3 lg:grid-cols-2">
        <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
          <Stack spacing={1.5}>
            <Typography variant="h6">Resolved Entities</Typography>
            {payload ? (
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {payload.resolved_entities.length === 0 ? (
                  <Typography color="text.secondary">No entities resolved.</Typography>
                ) : (
                  payload.resolved_entities.map((entity) => (
                    <Chip
                      key={`${entity.type}-${entity.id}`}
                      color="primary"
                      variant="outlined"
                      label={`${entity.type}: ${entity.name ?? entity.id}`}
                    />
                  ))
                )}
              </Stack>
            ) : (
              <Typography color="text.secondary">Run the workflow to view resolved entities.</Typography>
            )}
          </Stack>
        </Paper>

        <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
          <Stack spacing={1.5}>
            <Typography variant="h6">Evidence Citations</Typography>
            {payload ? (
              payload.citations.length === 0 ? (
                <Typography color="text.secondary">No citations returned.</Typography>
              ) : (
                payload.citations.slice(0, 8).map((citation) => (
                  <Stack key={citation.id} spacing={0.5}>
                    <Typography fontWeight={700}>{citation.id}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {citation.source ?? "unknown source"}
                    </Typography>
                    <Divider />
                  </Stack>
                ))
              )
            ) : (
              <Typography color="text.secondary">Run the workflow to view evidence citations.</Typography>
            )}
          </Stack>
        </Paper>
      </Box>

      <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-dashboard">
        <Stack spacing={1.5}>
          <Typography variant="h6">Graph Payload</Typography>
          {payload ? (
            <>
              <Typography>
                Nodes: {graphSummary.nodes} | Edges: {graphSummary.edges}
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {Object.entries(graphSummary.nodeTypeCount).length === 0 ? (
                  <Typography color="text.secondary">No node type distribution available.</Typography>
                ) : (
                  Object.entries(graphSummary.nodeTypeCount).map(([type, count]) => (
                    <Chip key={type} label={`${type}: ${count}`} size="small" />
                  ))
                )}
              </Stack>
            </>
          ) : (
            <Typography color="text.secondary">Run the workflow to view graph payload summary.</Typography>
          )}
        </Stack>
      </Paper>

      {payload?.errors.length ? <Alert severity="warning">{payload.errors.join("; ")}</Alert> : null}
    </Stack>
  );
}
