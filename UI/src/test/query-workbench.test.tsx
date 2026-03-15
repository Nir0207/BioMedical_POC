import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "./renderApp";

test("query workbench executes selected cypher endpoint and renders results", async () => {
  window.localStorage.setItem("bio_token", "test-token");
  renderApp("/queries");
  const user = userEvent.setup();

  await waitFor(() => {
    expect(screen.getByTestId("query-item-03_exploration-04_disease_target_ranking")).toBeInTheDocument();
  }, { timeout: 5000 });
  await user.click(screen.getByTestId("query-item-03_exploration-04_disease_target_ranking"));
  await user.clear(screen.getByLabelText(/disease_node_id/i));
  await user.type(screen.getByLabelText(/disease_node_id/i), "EFO:0000311");
  await user.click(screen.getByRole("button", { name: /run query/i }));

  expect(await screen.findByText(/TP53/i)).toBeInTheDocument();
  expect(screen.getByText(/Disease entity node_id/i)).toBeInTheDocument();
});
