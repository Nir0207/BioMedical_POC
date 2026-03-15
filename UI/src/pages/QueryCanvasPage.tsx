import { useMemo, useState, useDeferredValue, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography
} from "@mui/material";
import PlayArrowRoundedIcon from "@mui/icons-material/PlayArrowRounded";
import BoltRoundedIcon from "@mui/icons-material/BoltRounded";
import {
  fetchQueryCanvasCategories,
  fetchQueryCanvasNodes,
  runQueryCanvasRelation,
  validateQueryCanvasRelation
} from "../services/data";
import type {
  QueryCanvasNode,
  QueryCanvasRelationValidationResponse
} from "../types/api";
import { GraphCanvas } from "../components/GraphCanvas";
import { extractGraphData } from "../utils/graph";

interface CanvasNodeInstance extends QueryCanvasNode {
  canvas_id: string;
  x: number;
  y: number;
}

interface CanvasEdge {
  id: string;
  source_canvas_id: string;
  target_canvas_id: string;
  validation?: QueryCanvasRelationValidationResponse;
}

interface SuggestedCanvasCombo {
  id: string;
  label: string;
  description: string;
  source: QueryCanvasNode;
  target: QueryCanvasNode;
}

const PRESET_COMBINATIONS: SuggestedCanvasCombo[] = [
  {
    id: "tp53-breast-cancer",
    label: "TP53 to breast cancer",
    description: "Gene to disease relation with direct evidence in the current graph snapshot.",
    source: {
      node_id: "ENSG00000141510",
      name: "TP53",
      category: "Gene",
      labels: ["Entity", "Gene"]
    },
    target: {
      node_id: "MONDO_0007254",
      name: "breast cancer",
      category: "Disease",
      labels: ["Entity", "Disease"]
    }
  },
  {
    id: "tp53-protein",
    label: "TP53 to P04637",
    description: "Gene to protein encoding relation that renders a compact graph.",
    source: {
      node_id: "ENSG00000141510",
      name: "TP53",
      category: "Gene",
      labels: ["Entity", "Gene"]
    },
    target: {
      node_id: "UNIPROT:P04637",
      name: "P04637",
      category: "Protein",
      labels: ["Entity", "Protein"]
    }
  }
];

function truncateText(value: string, maxLength = 18) {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength - 1)}...`;
}

export function QueryCanvasPage() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const [canvasNodes, setCanvasNodes] = useState<CanvasNodeInstance[]>([]);
  const [canvasEdges, setCanvasEdges] = useState<CanvasEdge[]>([]);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [validationModal, setValidationModal] = useState<QueryCanvasRelationValidationResponse | null>(null);
  const [graphModalOpen, setGraphModalOpen] = useState(false);
  const [generatedCypher, setGeneratedCypher] = useState("");
  const [queryEditor, setQueryEditor] = useState("");
  const [queryParameters, setQueryParameters] = useState<Record<string, string | number>>({});

  const categoriesQuery = useQuery({
    queryKey: ["query-canvas-categories"],
    queryFn: fetchQueryCanvasCategories
  });

  const categories = categoriesQuery.data ?? [];
  const activeCategory = selectedCategory ?? categories[0]?.category ?? null;

  const nodesQuery = useQuery({
    queryKey: ["query-canvas-nodes", activeCategory, deferredSearch],
    queryFn: () => fetchQueryCanvasNodes({ category: activeCategory, search: deferredSearch, limit: 18 }),
    enabled: Boolean(activeCategory)
  });

  const validateMutation = useMutation({
    mutationFn: validateQueryCanvasRelation,
    onSuccess: (response) => {
      setCanvasEdges((currentEdges) =>
        currentEdges.map((edge) => (edge.id === selectedEdgeId ? { ...edge, validation: response } : edge))
      );
      setGeneratedCypher(response.generated_cypher);
      setQueryEditor(response.generated_cypher);
      setQueryParameters(response.parameters);
      setValidationModal(response);
    }
  });

  const runMutation = useMutation({
    mutationFn: runQueryCanvasRelation,
    onMutate: () => {
      setGraphModalOpen(true);
    },
    onSuccess: () => {
      setGraphModalOpen(true);
    }
  });

  const selectedEdge = useMemo(
    () => canvasEdges.find((edge) => edge.id === selectedEdgeId) ?? null,
    [canvasEdges, selectedEdgeId]
  );

  const selectedNodes = useMemo(() => {
    if (!selectedEdge) {
      return { source: null, target: null };
    }
    return {
      source: canvasNodes.find((node) => node.canvas_id === selectedEdge.source_canvas_id) ?? null,
      target: canvasNodes.find((node) => node.canvas_id === selectedEdge.target_canvas_id) ?? null
    };
  }, [canvasNodes, selectedEdge]);

  const paletteNodes = useMemo(() => nodesQuery.data ?? [], [nodesQuery.data]);

  const resultGraph = useMemo(
    () => extractGraphData(runMutation.data?.records ?? []),
    [runMutation.data?.records]
  );

  useEffect(() => {
    if (!selectedEdge?.validation) {
      return;
    }
    setGeneratedCypher(selectedEdge.validation.generated_cypher);
    setQueryEditor(selectedEdge.validation.generated_cypher);
    setQueryParameters(selectedEdge.validation.parameters);
  }, [selectedEdge?.id, selectedEdge?.validation]);

  function clearCanvas() {
    setCanvasNodes([]);
    setCanvasEdges([]);
    setSelectedEdgeId(null);
    setValidationModal(null);
    setGeneratedCypher("");
    setQueryEditor("");
    setQueryParameters({});
    setGraphModalOpen(false);
    validateMutation.reset();
    runMutation.reset();
  }

  function addNodeToCanvas(node: QueryCanvasNode, x?: number, y?: number, canvasId?: string) {
    setCanvasNodes((currentNodes) => {
      const nextNode = {
        ...node,
        canvas_id: canvasId ?? `${node.node_id}-${currentNodes.length + 1}`,
        x: x ?? 32 + (currentNodes.length % 3) * 190,
        y: y ?? 32 + Math.floor(currentNodes.length / 3) * 100
      };
      const lastNode = currentNodes[currentNodes.length - 1];
      if (lastNode && lastNode.node_id !== nextNode.node_id) {
        const nextEdgeId = `${lastNode.canvas_id}->${nextNode.canvas_id}`;
        setCanvasEdges((currentEdges) => {
          const exists = currentEdges.some(
            (edge) =>
              (edge.source_canvas_id === lastNode.canvas_id && edge.target_canvas_id === nextNode.canvas_id) ||
              (edge.source_canvas_id === nextNode.canvas_id && edge.target_canvas_id === lastNode.canvas_id)
          );
          if (exists) {
            return currentEdges;
          }
          setSelectedEdgeId(nextEdgeId);
          return [
            ...currentEdges,
            {
              id: nextEdgeId,
              source_canvas_id: lastNode.canvas_id,
              target_canvas_id: nextNode.canvas_id
            }
          ];
        });
      }
      return [...currentNodes, nextNode];
    });
  }

  function runValidation() {
    if (!selectedNodes.source || !selectedNodes.target) {
      return;
    }
    validateMutation.mutate({
      source_node_id: selectedNodes.source.node_id,
      target_node_id: selectedNodes.target.node_id
    });
  }

  function runSelectedQuery(sourceNodeId?: string, targetNodeId?: string) {
    const effectiveSourceNodeId = sourceNodeId ?? selectedNodes.source?.node_id;
    const effectiveTargetNodeId = targetNodeId ?? selectedNodes.target?.node_id;
    if (!effectiveSourceNodeId || !effectiveTargetNodeId) {
      return;
    }
    runMutation.mutate({
      source_node_id: effectiveSourceNodeId,
      target_node_id: effectiveTargetNodeId,
      neighbor_limit: 8,
      cypher: queryEditor.trim() || undefined,
      parameters: queryParameters
    });
  }

  function loadSuggestedCanvas(combo: SuggestedCanvasCombo) {
    const sourceCanvasId = `${combo.id}-source`;
    const targetCanvasId = `${combo.id}-target`;
    const edgeId = `${sourceCanvasId}->${targetCanvasId}`;
    setCanvasNodes([
      {
        ...combo.source,
        canvas_id: sourceCanvasId,
        x: 86,
        y: 154
      },
      {
        ...combo.target,
        canvas_id: targetCanvasId,
        x: 398,
        y: 194
      }
    ]);
    setCanvasEdges([
      {
        id: edgeId,
        source_canvas_id: sourceCanvasId,
        target_canvas_id: targetCanvasId
      }
    ]);
    setSelectedEdgeId(edgeId);
    setSelectedCategory(combo.source.category);
    setSearch("");
    setValidationModal(null);
    setGeneratedCypher("");
    setQueryEditor("");
    setQueryParameters({});
    setGraphModalOpen(false);
    validateMutation.reset();
    runMutation.reset();
  }

  return (
    <Stack spacing={4}>
      <Stack spacing={1}>
        <Typography variant="overline" className="tracking-[0.28em] text-sea">
          Query Canvas
        </Typography>
        <Typography variant="h3">Build relationship questions visually.</Typography>
        <Typography color="text.secondary">
          Add nodes from Neo4j, validate the selected relation, and open graph results only in a modal with controls on the right.
        </Typography>
      </Stack>
      <Box className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Stack spacing={3}>
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-5 shadow-dashboard">
            <Stack spacing={2}>
              <Typography variant="h6">Node palette</Typography>
              <TextField
                label="Search nodes"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search TP53, MONDO, UNIPROT..."
              />
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                {categories.map((category) => (
                  <Chip
                    key={category.category}
                    label={`${category.category} (${category.count})`}
                    color={activeCategory === category.category ? "primary" : "default"}
                    onClick={() => setSelectedCategory(category.category)}
                  />
                ))}
              </Stack>
              <Box className="overflow-x-auto pb-2">
                <Stack direction="row" spacing={1.5} className="min-w-max">
                  {nodesQuery.isLoading ? <CircularProgress size={24} className="mt-4" /> : null}
                  {paletteNodes.map((node) => (
                    <Tooltip
                      key={node.node_id}
                      title={
                        <Stack spacing={0.5}>
                          <Typography variant="body2" fontWeight={700}>
                            {node.name}
                          </Typography>
                          <Typography variant="caption">{node.node_id}</Typography>
                          <Typography variant="caption">{node.category}</Typography>
                        </Stack>
                      }
                      arrow
                    >
                      <Box
                        data-testid={`palette-node-${node.node_id}`}
                        draggable
                        onDragStart={(event) => {
                          event.dataTransfer.setData("application/query-canvas-node", JSON.stringify(node));
                        }}
                        className="w-[180px] shrink-0 rounded-[24px] border border-sand bg-[#fff7ea] p-4"
                      >
                        <Stack spacing={1.5}>
                          <Stack spacing={0.5}>
                            <Typography fontWeight={700} className="truncate">
                              {truncateText(node.name, 20)}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" className="truncate">
                              {truncateText(node.node_id, 18)}
                            </Typography>
                            <Chip label={node.category} size="small" className="w-fit" />
                          </Stack>
                          <Button size="small" variant="contained" onClick={() => addNodeToCanvas(node)}>
                            Add
                          </Button>
                        </Stack>
                      </Box>
                    </Tooltip>
                  ))}
                </Stack>
              </Box>
            </Stack>
          </Paper>
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-5 shadow-dashboard">
            <Stack spacing={2}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">Suggested combinations</Typography>
                <Button
                  startIcon={<PlayArrowRoundedIcon />}
                  variant="contained"
                  color="secondary"
                  onClick={() => loadSuggestedCanvas(PRESET_COMBINATIONS[0])}
                >
                  Run Default
                </Button>
              </Stack>
              <Typography color="text.secondary">
                These combinations already exist in the current database and are safe for validation checks.
              </Typography>
              <Stack spacing={1.5}>
                {PRESET_COMBINATIONS.map((combo) => (
                  <Paper
                    key={combo.id}
                    variant="outlined"
                    className="rounded-[24px] border-[#e7d7b9] bg-[#fffbf2] px-4 py-3"
                  >
                    <Stack direction="row" spacing={2} justifyContent="space-between" alignItems="center">
                      <Stack spacing={0.5}>
                        <Typography fontWeight={700}>{combo.label}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {combo.description}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {combo.source.node_id} {"->"} {combo.target.node_id}
                        </Typography>
                      </Stack>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => loadSuggestedCanvas(combo)}
                      >
                        Use combo
                      </Button>
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            </Stack>
          </Paper>
        </Stack>
        <Stack spacing={3} data-testid="query-canvas-inspector" className="xl:sticky xl:top-6 xl:self-start">
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-5 shadow-dashboard">
            <Stack spacing={2}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">Canvas controls</Typography>
                <Button variant="text" color="secondary" onClick={clearCanvas}>
                  Clear selection
                </Button>
              </Stack>
              <Typography color="text.secondary">
                No graph is rendered on this page. Every graph result opens only in a modal with the Neo4j controls on the right.
              </Typography>
              {runMutation.data ? (
                <Button className="w-fit" variant="contained" onClick={() => setGraphModalOpen(true)}>
                  Reopen graph modal
                </Button>
              ) : null}
              {runMutation.error ? <Alert severity="error">Failed to run the generated graph query.</Alert> : null}
            </Stack>
          </Paper>
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-5 shadow-dashboard">
            <Stack spacing={2.5}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">Selected relation</Typography>
                {selectedEdge ? <Chip size="small" color="secondary" label="Active" /> : null}
              </Stack>
              {selectedEdge && selectedNodes.source && selectedNodes.target ? (
                <>
                  <Paper variant="outlined" className="rounded-[24px] border-[#e7d7b9] bg-[#fffbf2] p-4">
                    <Stack spacing={1}>
                      <Typography fontWeight={700}>{selectedNodes.source.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedNodes.source.node_id}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        to
                      </Typography>
                      <Typography fontWeight={700}>{selectedNodes.target.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedNodes.target.node_id}
                      </Typography>
                    </Stack>
                  </Paper>
                  <Stack direction="row" spacing={1.5}>
                    <Button
                      variant="outlined"
                      startIcon={<BoltRoundedIcon />}
                      onClick={runValidation}
                      disabled={validateMutation.isPending}
                    >
                      Validate
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={<PlayArrowRoundedIcon />}
                      disabled={!selectedEdge.validation?.exists || runMutation.isPending}
                      onClick={() => runSelectedQuery()}
                    >
                      Run query
                    </Button>
                  </Stack>
                  {selectedEdge.validation ? (
                    <Alert severity={selectedEdge.validation.exists ? "success" : "warning"}>
                      {selectedEdge.validation.message}
                    </Alert>
                  ) : (
                    <Alert severity="info">
                      Validate this connection to confirm the relation exists before running the graph query.
                    </Alert>
                  )}
                  <Stack spacing={1.25}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="subtitle2">Generated Cypher</Typography>
                      {generatedCypher ? (
                        <Button size="small" onClick={() => setQueryEditor(generatedCypher)}>
                          Reset query
                        </Button>
                      ) : null}
                    </Stack>
                    <TextField
                      data-testid="query-canvas-query-editor"
                      multiline
                      minRows={10}
                      value={queryEditor}
                      onChange={(event) => setQueryEditor(event.target.value)}
                      placeholder="Click Validate to generate a Cypher query here."
                      helperText="Validate loads the generated Cypher here. You can edit it before running, but only read-only Cypher is allowed."
                    />
                    <Paper variant="outlined" className="rounded-[20px] border-[#e7d7b9] bg-[#fffbf2] p-3">
                      <Stack spacing={0.75}>
                        <Typography variant="subtitle2">Bound parameters</Typography>
                        {Object.keys(queryParameters).length ? (
                          Object.entries(queryParameters).map(([key, value]) => (
                            <Typography key={key} variant="body2" color="text.secondary">
                              {key}: {String(value)}
                            </Typography>
                          ))
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Parameters will appear here after validation.
                          </Typography>
                        )}
                      </Stack>
                    </Paper>
                  </Stack>
                </>
              ) : (
                <Typography color="text.secondary">
                  Add two nodes from the palette or load a suggested combination. The latest pair becomes the active relation here, and validation stays available from this right-side panel.
                </Typography>
              )}
            </Stack>
          </Paper>
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-5 shadow-dashboard">
            <Stack spacing={1.5}>
              <Typography variant="h6">Try this first</Typography>
              <Typography color="text.secondary">
                Recommended starting combination: <strong>TP53</strong> to <strong>breast cancer</strong>.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Node ids: ENSG00000141510 {"->"} MONDO_0007254
              </Typography>
              <Button
                variant="outlined"
                onClick={() => loadSuggestedCanvas(PRESET_COMBINATIONS[0])}
              >
                Load recommended combo
              </Button>
            </Stack>
          </Paper>
        </Stack>
      </Box>
      {validationModal ? (
        <div className="fixed inset-0 z-[1400] flex items-center justify-center bg-[#11212dcc] p-4">
          <div className="w-full max-w-xl rounded-[32px] border border-white/10 bg-[#fff8ee] p-6 shadow-2xl">
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sea">Relation Validation</p>
              <h3 className="text-3xl font-bold text-ink">
                {validationModal.exists ? "Relation exists" : "Relation not found"}
              </h3>
              <p className="text-sm text-slate-600">{validationModal.message}</p>
              <div className="rounded-[24px] bg-white/80 p-4">
                <p className="font-semibold text-ink">
                  {validationModal.source.name} to {validationModal.target.name}
                </p>
                <p className="mt-2 text-sm text-slate-600">
                  RELATED_TO: {validationModal.related_to_types.length ? validationModal.related_to_types.join(", ") : "None"}
                </p>
                <p className="text-sm text-slate-600">
                  HAS_RELATION_FACT:{" "}
                  {validationModal.relation_fact_types.length ? validationModal.relation_fact_types.join(", ") : "None"}
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  className="rounded-full border border-slate-300 px-5 py-2 font-semibold text-slate-700"
                  onClick={() => setValidationModal(null)}
                >
                  Close
                </button>
                {validationModal.exists && selectedEdge ? (
                  <button
                    type="button"
                    data-testid="query-canvas-modal-run"
                    className="rounded-full bg-ember px-5 py-2 font-semibold text-white"
                    onClick={() => {
                      runSelectedQuery(validationModal.source.node_id, validationModal.target.node_id);
                      setValidationModal(null);
                    }}
                  >
                    Run validated query
                  </button>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      ) : null}
      {graphModalOpen ? (
        runMutation.isPending ? (
          <div data-testid="graph-canvas-loading-modal" className="fixed inset-0 z-[1500] bg-[#0f1a21d9] p-4">
            <div className="mx-auto flex h-full max-w-[960px] items-center justify-center rounded-[36px] border border-white/10 bg-[#fef8ef] p-8">
              <Stack spacing={2} alignItems="center">
                <CircularProgress />
                <Typography variant="h5">Loading graph</Typography>
                <Typography color="text.secondary">
                  Running the Neo4j query and preparing the modal graph view.
                </Typography>
                <Button variant="text" onClick={() => setGraphModalOpen(false)}>
                  Close
                </Button>
              </Stack>
            </div>
          </div>
        ) : runMutation.error ? (
          <div data-testid="graph-canvas-error-modal" className="fixed inset-0 z-[1500] bg-[#0f1a21d9] p-4">
            <div className="mx-auto flex h-full max-w-[960px] items-center justify-center rounded-[36px] border border-white/10 bg-[#fef8ef] p-8">
              <Stack spacing={2} alignItems="center">
                <Alert severity="error">Failed to run the graph query. Check the generated Cypher and try again.</Alert>
                <Button variant="contained" onClick={() => setGraphModalOpen(false)}>
                  Close
                </Button>
              </Stack>
            </div>
          </div>
        ) : runMutation.data && resultGraph.nodes.length > 0 ? (
          <GraphCanvas data={resultGraph} title="Query Canvas Result" variant="modal" onClose={() => setGraphModalOpen(false)} />
        ) : runMutation.data ? (
          <div data-testid="graph-canvas-empty-modal" className="fixed inset-0 z-[1500] bg-[#0f1a21d9] p-4">
            <div className="mx-auto flex h-full max-w-[960px] items-center justify-center rounded-[36px] border border-white/10 bg-[#fef8ef] p-8">
              <Stack spacing={2} alignItems="center">
                <Alert severity="warning">
                  The query finished, but it did not return graph-shaped data that can be rendered in the modal.
                </Alert>
                <Button variant="contained" onClick={() => setGraphModalOpen(false)}>
                  Close
                </Button>
              </Stack>
            </div>
          </div>
        ) : null
      ) : null}
    </Stack>
  );
}
