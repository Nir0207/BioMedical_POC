import { Button, ButtonGroup, Chip, Divider, Paper, Stack, Typography } from "@mui/material";
import ZoomInRoundedIcon from "@mui/icons-material/ZoomInRounded";
import ZoomOutRoundedIcon from "@mui/icons-material/ZoomOutRounded";
import RestartAltRoundedIcon from "@mui/icons-material/RestartAltRounded";
import OpenInFullRoundedIcon from "@mui/icons-material/OpenInFullRounded";
import CompressRoundedIcon from "@mui/icons-material/CompressRounded";
import DownloadRoundedIcon from "@mui/icons-material/DownloadRounded";
import NavigationRoundedIcon from "@mui/icons-material/NavigationRounded";
import TuneRoundedIcon from "@mui/icons-material/TuneRounded";
import IosShareRoundedIcon from "@mui/icons-material/IosShareRounded";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import ForceGraph3D from "react-force-graph-3d";
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import SpriteText from "three-spritetext";
import { useElementSize } from "../hooks/useElementSize";
import type { GraphDataSet } from "../types/graph";

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

type GraphCanvasVariant = "card" | "modal";

interface GraphCanvasProps {
  data: GraphDataSet;
  title: string;
  variant?: GraphCanvasVariant;
  onClose?: () => void;
}

type ForceGraphHandle = {
  camera?: () => { position: { x: number; y: number; z: number } };
  cameraPosition?: (
    position?: { x?: number; y?: number; z?: number },
    lookAt?: { x?: number; y?: number; z?: number },
    ms?: number
  ) => void;
  d3Force?: (forceName: string) => { distance?: (value: number) => void; strength?: (value: number) => void } | undefined;
  d3ReheatSimulation?: () => void;
  zoomToFit?: (durationMs?: number, paddingPx?: number) => void;
  renderer?: () => { domElement?: HTMLCanvasElement };
};

function GraphViewport({
  data,
  title,
  graphRef,
  spread,
  variant
}: {
  data: GraphDataSet;
  title: string;
  graphRef: React.MutableRefObject<ForceGraphHandle | null>;
  spread: number;
  variant: GraphCanvasVariant;
}) {
  const [containerElement, setContainerElement] = useState<HTMLDivElement | null>(null);
  const { width, height } = useElementSize(containerElement);
  const canvasWidth = Math.floor(width);
  const canvasHeight = Math.floor(height);
  const isReady = canvasWidth > 0 && canvasHeight > 0;
  const isTestMode = import.meta.env.MODE === "test";
  const fallbackWidth = variant === "modal" ? 1040 : 960;
  const fallbackHeight = variant === "modal" ? 760 : 640;
  const resolvedWidth = isReady ? canvasWidth : fallbackWidth;
  const resolvedHeight = isReady ? canvasHeight : fallbackHeight;

  useEffect(() => {
    if (!graphRef.current?.zoomToFit) {
      return;
    }
    const timeoutId = window.setTimeout(() => {
      graphRef.current?.zoomToFit?.(700, 90);
    }, 650);
    return () => window.clearTimeout(timeoutId);
  }, [data, graphRef, resolvedWidth, resolvedHeight]);

  useEffect(() => {
    const forceGraph = graphRef.current;
    if (!forceGraph) {
      return;
    }
    const linkForce = forceGraph.d3Force?.("link");
    if (linkForce?.distance) {
      linkForce.distance(90 * spread);
    }
    const chargeForce = forceGraph.d3Force?.("charge");
    if (chargeForce?.strength) {
      chargeForce.strength(-180 * spread);
    }
    forceGraph.d3ReheatSimulation?.();
  }, [data, graphRef, spread]);

  return (
    <div
      ref={setContainerElement}
      className={variant === "modal" ? "h-[78vh] w-full overflow-hidden rounded-[28px] bg-[#f7f0e5]" : "h-[640px] w-full overflow-hidden rounded-[26px] bg-[#f7f0e5]"}
    >
      {isReady || isTestMode ? (
        <ForceGraph3D
          key={`${variant}-${resolvedWidth}-${resolvedHeight}`}
          ref={graphRef as any}
          graphData={data}
          width={resolvedWidth}
          height={resolvedHeight}
          backgroundColor="#f7f0e5"
          rendererConfig={{ antialias: true, alpha: true, preserveDrawingBuffer: true }}
          showNavInfo={false}
          nodeOpacity={1}
          nodeResolution={8}
          linkOpacity={0.18}
          linkWidth={0.45}
          linkColor={() => "rgba(17, 33, 45, 0.24)"}
          cooldownTicks={120}
          nodeLabel={(node) => {
            const typedNode = node as { label?: string; category?: string };
            const label = typedNode.label ?? "Node";
            const category = typedNode.category ?? "Entity";
            return `${label} (${category})`;
          }}
          nodeThreeObject={(node: unknown) => {
            const typedNode = node as { color: string; label: string };
            const group = new THREE.Group();

            const sphere = new THREE.Mesh(
              new THREE.SphereGeometry(1.45, 12, 12),
              new THREE.MeshLambertMaterial({
                color: typedNode.color,
                transparent: true,
                opacity: 0.96
              })
            );
            group.add(sphere);

            const label = new SpriteText(typedNode.label) as any;
            label.color = "#11212d";
            label.textHeight = 2.1;
            label.fontFace = "IBM Plex Sans";
            label.backgroundColor = "rgba(255,248,238,0.82)";
            label.padding = 1.1;
            label.borderRadius = 2;
            label.position.set(0, 2.4, 0);
            group.add(label);

            return group;
          }}
        />
      ) : null}
    </div>
  );
}

function GraphControls({
  data,
  title,
  graphRef,
  spread,
  setSpread,
  onClose
}: {
  data: GraphDataSet;
  title: string;
  graphRef: React.MutableRefObject<ForceGraphHandle | null>;
  spread: number;
  setSpread: React.Dispatch<React.SetStateAction<number>>;
  onClose?: () => void;
}) {
  function handleZoom(direction: "in" | "out"): void {
    const camera = graphRef.current?.camera?.();
    const cameraPosition = graphRef.current?.cameraPosition;
    if (!camera || !cameraPosition) {
      return;
    }
    const multiplier = direction === "in" ? 0.8 : 1.25;
    cameraPosition(
      {
        x: camera.position.x * multiplier,
        y: camera.position.y * multiplier,
        z: Math.max(22, camera.position.z * multiplier)
      },
      undefined,
      300
    );
  }

  function handleDownloadHtml(): void {
    const canvas = graphRef.current?.renderer?.()?.domElement;
    const screenshot = canvas instanceof HTMLCanvasElement ? canvas.toDataURL("image/png") : "";
    const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${escapeHtml(title)} Snapshot</title>
    <style>
      body { font-family: IBM Plex Sans, Segoe UI, sans-serif; margin: 0; padding: 32px; background: #f6f1e8; color: #11212d; }
      .card { background: #fffaf2; border: 1px solid #e2d5be; border-radius: 24px; padding: 24px; margin-bottom: 24px; }
      img { width: 100%; max-width: 1200px; border-radius: 18px; border: 1px solid #dcc8a7; }
      pre { white-space: pre-wrap; word-break: break-word; font-size: 12px; background: #f0e7d8; border-radius: 16px; padding: 16px; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>${escapeHtml(title)}</h1>
      <p>${data.nodes.length} nodes / ${data.links.length} links</p>
      ${screenshot ? `<img src="${screenshot}" alt="Graph snapshot" />` : "<p>Canvas screenshot unavailable.</p>"}
    </div>
    <div class="card">
      <h2>Graph data</h2>
      <pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>
    </div>
  </body>
</html>`;

    const blob = new Blob([html], { type: "text/html" });
    const blobUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = blobUrl;
    anchor.download = `${title.replaceAll(/\s+/g, "-").toLowerCase()}-snapshot.html`;
    anchor.click();
    URL.revokeObjectURL(blobUrl);
  }

  return (
    <Stack spacing={2.5}>
      <Stack spacing={0.75}>
        <Typography variant="h6">Graph controls</Typography>
        <Typography color="text.secondary">
          Zoom, fit, spread nodes, and export the current canvas snapshot.
        </Typography>
      </Stack>
      <Paper variant="outlined" className="rounded-[24px] border-[#d9c7a8] bg-[#fff7ea] p-4">
        <Stack spacing={1.5}>
          <Stack direction="row" spacing={1} alignItems="center">
            <NavigationRoundedIcon fontSize="small" />
            <Typography variant="subtitle2">Navigation</Typography>
          </Stack>
          <ButtonGroup orientation="vertical" variant="outlined" size="small" aria-label="graph zoom controls" fullWidth>
            <Button startIcon={<ZoomInRoundedIcon />} onClick={() => handleZoom("in")}>
              Zoom in
            </Button>
            <Button startIcon={<ZoomOutRoundedIcon />} onClick={() => handleZoom("out")}>
              Zoom out
            </Button>
            <Button
              startIcon={<RestartAltRoundedIcon />}
              onClick={() => {
                graphRef.current?.zoomToFit?.(400, 80);
              }}
            >
              Reset
            </Button>
          </ButtonGroup>
        </Stack>
      </Paper>
      <Paper variant="outlined" className="rounded-[24px] border-[#d9c7a8] bg-[#fff7ea] p-4">
        <Stack spacing={1.5}>
          <Stack direction="row" spacing={1} alignItems="center">
            <TuneRoundedIcon fontSize="small" />
            <Typography variant="subtitle2">Layout</Typography>
          </Stack>
          <Typography variant="body2" color="text.secondary">
            Current spread: {spread.toFixed(2)}x
          </Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={<OpenInFullRoundedIcon />}
            onClick={() => setSpread((currentSpread) => Math.min(currentSpread + 0.35, 3))}
          >
            Expand
          </Button>
          <Button
            variant="outlined"
            size="small"
            startIcon={<CompressRoundedIcon />}
            onClick={() => setSpread((currentSpread) => Math.max(currentSpread - 0.35, 0.65))}
          >
            Compact
          </Button>
        </Stack>
      </Paper>
      <Paper variant="outlined" className="rounded-[24px] border-[#d9c7a8] bg-[#fff7ea] p-4">
        <Stack spacing={1.5}>
          <Stack direction="row" spacing={1} alignItems="center">
            <IosShareRoundedIcon fontSize="small" />
            <Typography variant="subtitle2">Export</Typography>
          </Stack>
          <Button variant="contained" size="small" startIcon={<DownloadRoundedIcon />} onClick={handleDownloadHtml}>
            Download HTML
          </Button>
          {onClose ? (
            <Button variant="text" size="small" startIcon={<CloseRoundedIcon />} onClick={onClose}>
              Close graph
            </Button>
          ) : null}
        </Stack>
      </Paper>
    </Stack>
  );
}

export function GraphCanvas({ data, title, variant = "card", onClose }: GraphCanvasProps) {
  const graphRef = useRef<ForceGraphHandle | null>(null);
  const [spread, setSpread] = useState(1);

  if (variant === "modal") {
    return (
      <div data-testid="graph-canvas-modal" className="fixed inset-0 z-[1500] bg-[#0f1a21d9] p-4">
        <div className="mx-auto grid h-full max-w-[1320px] gap-4 rounded-[36px] border border-white/10 bg-[#fef8ef] p-4 xl:grid-cols-[minmax(0,1fr)_280px]">
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-4 shadow-dashboard">
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Stack>
                <Typography variant="h5">{title}</Typography>
                <Typography color="text.secondary">
                  {data.nodes.length} nodes / {data.links.length} links
                </Typography>
              </Stack>
              <Chip label="Interactive Neo4j graph" color="secondary" variant="outlined" />
            </Stack>
            <Divider className="mb-3" />
            <GraphViewport data={data} title={title} graphRef={graphRef} spread={spread} variant="modal" />
          </Paper>
          <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-5 shadow-dashboard">
            <GraphControls data={data} title={title} graphRef={graphRef} spread={spread} setSpread={setSpread} onClose={onClose} />
          </Paper>
        </div>
      </div>
    );
  }

  return (
    <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-4 shadow-dashboard">
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Stack>
          <Typography variant="h6">Graph canvas</Typography>
          <Typography color="text.secondary">
            {data.nodes.length} nodes / {data.links.length} links
          </Typography>
        </Stack>
        <Chip label="Interactive Neo4j graph" color="secondary" variant="outlined" />
      </Stack>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
        <div>
          <Divider className="mb-3" />
          <GraphViewport data={data} title={title} graphRef={graphRef} spread={spread} variant="card" />
        </div>
        <Paper className="rounded-[32px] border border-white/70 bg-white/90 p-5 shadow-dashboard">
          <GraphControls data={data} title={title} graphRef={graphRef} spread={spread} setSpread={setSpread} />
        </Paper>
      </div>
    </Paper>
  );
}
