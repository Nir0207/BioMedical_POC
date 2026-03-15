import { render } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { Providers } from "../app/Providers";
import { appRoutes } from "../app/routes";

export function renderApp(initialEntry: string) {
  const router = createMemoryRouter(appRoutes, {
    initialEntries: [initialEntry]
  });

  return render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>
  );
}
