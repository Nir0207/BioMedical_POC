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

Object.defineProperty(window, "AbortController", {
  writable: true,
  value: globalThis.AbortController
});

Object.defineProperty(window, "AbortSignal", {
  writable: true,
  value: globalThis.AbortSignal
});

const NativeRequest = globalThis.Request;
class RequestWithoutForeignSignal extends NativeRequest {
  constructor(input: RequestInfo | URL, init?: RequestInit) {
    if (init?.signal) {
      super(input, { ...init, signal: undefined });
      return;
    }
    super(input, init);
  }
}

Object.defineProperty(globalThis, "Request", {
  writable: true,
  value: RequestWithoutForeignSignal
});

Object.defineProperty(window, "Request", {
  writable: true,
  value: RequestWithoutForeignSignal
});

if (
  typeof window.localStorage === "undefined" ||
  typeof window.localStorage.getItem !== "function" ||
  typeof window.localStorage.setItem !== "function"
) {
  const store = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    writable: true,
    value: {
      getItem: (key: string) => (store.has(key) ? store.get(key)! : null),
      setItem: (key: string, value: string) => store.set(key, value),
      removeItem: (key: string) => store.delete(key),
      clear: () => store.clear()
    }
  });
}

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
  window.localStorage.clear();
});
afterAll(() => server.close());
