import { createBrowserRouter, Navigate, type RouteObject } from "react-router-dom";
import { AppShell } from "../layouts/AppShell";
import { ProtectedRoute } from "../routes/ProtectedRoute";
import { DashboardPage } from "../pages/DashboardPage";
import { GraphExplorerPage } from "../pages/GraphExplorerPage";
import { LoginPage } from "../pages/LoginPage";
import { AgenticWorkflowPage } from "../pages/AgenticWorkflowPage";
import { QueryCanvasPage } from "../pages/QueryCanvasPage";
import { QueryWorkbenchPage } from "../pages/QueryWorkbenchPage";

export const appRoutes: RouteObject[] = [
  {
    path: "/login",
    element: <LoginPage />
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          {
            path: "/dashboard",
            element: <DashboardPage />
          },
          {
            path: "/queries",
            element: <QueryWorkbenchPage />
          },
          {
            path: "/graph",
            element: <GraphExplorerPage />
          },
          {
            path: "/query-canvas",
            element: <QueryCanvasPage />
          },
          {
            path: "/agentic",
            element: <AgenticWorkflowPage />
          },
          {
            path: "*",
            element: <Navigate to="/dashboard" replace />
          }
        ]
      }
    ]
  }
];

export function createAppRouter() {
  return createBrowserRouter(appRoutes);
}
