import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "./renderApp";

test("query canvas keeps graph output out of the main page and opens it only in a modal", async () => {
  window.localStorage.setItem("bio_token", "test-token");
  renderApp("/query-canvas");
  const user = userEvent.setup();

  expect(await screen.findByText(/build relationship questions visually/i)).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByTestId("palette-node-ENSG00000141510")).toBeInTheDocument();
  }, { timeout: 4000 });

  expect(screen.queryByText(/^Canvas$/i)).not.toBeInTheDocument();
  expect(screen.queryByTestId("query-canvas-dropzone")).not.toBeInTheDocument();
  expect(screen.getByTestId("query-canvas-inspector")).toBeInTheDocument();
  expect(screen.getByText(/no graph is rendered on this page/i)).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: /run default/i }));

  const inspector = screen.getByTestId("query-canvas-inspector");
  expect(inspector).toHaveTextContent("TP53");
  expect(inspector).toHaveTextContent("MONDO_0007254");

  await user.click(screen.getByRole("button", { name: /^validate$/i }));

  expect(await screen.findByText(/relation exists/i)).toBeInTheDocument();
  expect(screen.getByText(/ASSOCIATED_WITH/)).toBeInTheDocument();

  const queryEditor = screen.getByTestId("query-canvas-query-editor").querySelector("textarea");
  expect(queryEditor?.value).toContain("MATCH (source:Entity");

  fireEvent.change(queryEditor!, {
    target: { value: "MATCH (source:Entity {node_id: $source_node_id}) RETURN source" }
  });
  expect(queryEditor?.value).toBe("MATCH (source:Entity {node_id: $source_node_id}) RETURN source");

  await user.click(screen.getByRole("button", { name: /run validated query/i }));

  await waitFor(() => {
    expect(screen.getByTestId("graph-canvas-modal")).toBeInTheDocument();
  });
  expect(screen.getByRole("button", { name: /zoom in/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /expand/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /download html/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /close graph/i })).toBeInTheDocument();
  expect(screen.getByTestId("mock-force-graph")).toHaveTextContent("graph 3 nodes 2 links");
}, 25000);

test("query canvas lets users load a recommended combo and reopen the graph modal without a page graph section", async () => {
  window.localStorage.setItem("bio_token", "test-token");
  renderApp("/query-canvas");
  const user = userEvent.setup();

  expect(await screen.findByText(/try this first/i)).toBeInTheDocument();
  expect(screen.queryByText(/^Canvas$/i)).not.toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: /load recommended combo/i }));
  await user.click(screen.getByRole("button", { name: /^validate$/i }));
  expect(await screen.findByText(/relation exists/i)).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: /run validated query/i }));
  await waitFor(() => {
    expect(screen.getByTestId("graph-canvas-modal")).toBeInTheDocument();
  });

  await user.click(screen.getByRole("button", { name: /close graph/i }));
  await waitFor(() => {
    expect(screen.queryByTestId("graph-canvas-modal")).not.toBeInTheDocument();
  });

  expect(screen.getByRole("button", { name: /reopen graph modal/i })).toBeInTheDocument();
  expect(screen.queryByText(/^Canvas$/i)).not.toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: /reopen graph modal/i }));
  await waitFor(() => {
    expect(screen.getByTestId("graph-canvas-modal")).toBeInTheDocument();
  });
});
