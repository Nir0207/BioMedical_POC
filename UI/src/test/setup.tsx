import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { setupServer } from "msw/node";
import { handlers } from "./server";

vi.mock("react-force-graph-3d", () => ({
  default: ({ graphData }: { graphData: { nodes: unknown[]; links: unknown[] } }) => (
    <div data-testid="mock-force-graph">
      graph {graphData.nodes.length} nodes {graphData.links.length} links
    </div>
  )
}));

class ResizeObserverMock {
  observe() {}
  disconnect() {}
  unobserve() {}
}

Object.defineProperty(window, "ResizeObserver", {
  writable: true,
  value: ResizeObserverMock
});

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
  window.localStorage.clear();
});
afterAll(() => server.close());
