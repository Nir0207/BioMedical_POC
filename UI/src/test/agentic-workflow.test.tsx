import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "./renderApp";

test("agentic workflow tab executes and renders grounded response", async () => {
  window.localStorage.setItem("bio_token", "test-token");
  renderApp("/agentic");
  const user = userEvent.setup();

  expect(await screen.findByText(/graph-grounded disease target research assistant/i)).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: /run agentic workflow/i }));

  expect(await screen.findByText(/candidate genes: 2/i)).toBeInTheDocument();
  expect(screen.getByText(/EV-001/i)).toBeInTheDocument();
  expect(screen.getByText(/Nodes: 2 \| Edges: 1/i)).toBeInTheDocument();
});
