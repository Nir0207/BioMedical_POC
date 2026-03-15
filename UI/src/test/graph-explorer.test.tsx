import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "./renderApp";

test("graph explorer renders interactive graph data from graph query response", async () => {
  window.localStorage.setItem("bio_token", "test-token");
  renderApp("/graph");
  const user = userEvent.setup();

  await screen.findByText(/graph-capable endpoints/i);
  await user.click(await screen.findByTestId("query-item-04_subgraphs-01_export_disease_neighborhood"));
  await user.clear(screen.getByLabelText(/disease_node_id/i));
  await user.type(screen.getByLabelText(/disease_node_id/i), "EFO:0000311");
  await user.clear(screen.getByLabelText(/max_hops/i));
  await user.type(screen.getByLabelText(/max_hops/i), "2");
  await user.click(screen.getByRole("button", { name: /run query/i }));

  expect(screen.getByRole("button", { name: /zoom in/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /expand/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /download html/i })).toBeInTheDocument();
  expect(await screen.findByTestId("mock-force-graph", {}, { timeout: 25000 })).toHaveTextContent("graph 2 nodes 1 links");
}, 25000);
