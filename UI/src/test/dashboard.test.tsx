import { screen, waitFor } from "@testing-library/react";
import { renderApp } from "./renderApp";

test("dashboard loads summaries for authenticated users", async () => {
  window.localStorage.setItem("bio_token", "test-token");
  renderApp("/dashboard");

  expect(await screen.findByText(/welcome back, graph/i)).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByTestId("metric-postgres-users-value")).toHaveTextContent("14");
    expect(screen.getByTestId("metric-graph-nodes-value")).toHaveTextContent("175800");
    expect(screen.getByTestId("metric-published-queries-value")).toHaveTextContent("5");
  });
});
