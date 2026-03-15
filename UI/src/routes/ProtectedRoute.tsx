import { Navigate, Outlet, useLocation } from "react-router-dom";
import { CircularProgress, Stack } from "@mui/material";
import { useAuth } from "../features/auth/AuthContext";

export function ProtectedRoute() {
  const { token, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <Stack alignItems="center" justifyContent="center" minHeight="100vh">
        <CircularProgress />
      </Stack>
    );
  }

  if (!token) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return <Outlet />;
}
