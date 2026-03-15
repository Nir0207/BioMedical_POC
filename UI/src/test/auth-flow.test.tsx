import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "./renderApp";

test("login flow authenticates and redirects to dashboard", async () => {
  renderApp("/login");
  const user = userEvent.setup();

  await user.type(screen.getByLabelText(/email/i), "graph@example.com");
  await user.type(screen.getByLabelText(/^password/i), "strong-pass-123");
  await user.click(screen.getByRole("button", { name: /enter dashboard/i }));

  await waitFor(() => {
    expect(window.localStorage.getItem("bio_token")).toBe("test-token");
  });
  expect(await screen.findByTestId("metric-postgres-users-value", {}, { timeout: 25000 })).toBeInTheDocument();
}, 25000);
