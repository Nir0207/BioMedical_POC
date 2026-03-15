import { RouterProvider } from "react-router-dom";
import { Providers } from "./app/Providers";
import { createAppRouter } from "./app/routes";

const router = createAppRouter();

export default function App() {
  return (
    <Providers>
      <RouterProvider router={router} />
    </Providers>
  );
}
