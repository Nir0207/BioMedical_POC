import { Alert, Box, Button, Paper, Stack, Tab, Tabs, TextField, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthContext";

type AuthMode = "login" | "register";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register } = useAuth();
  const [mode, setMode] = useState<AuthMode>("login");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState({
    email: "",
    full_name: "",
    password: ""
  });

  const redirectPath = useMemo(() => {
    const state = location.state as { from?: string } | null;
    return state?.from ?? "/dashboard";
  }, [location.state]);

  return (
    <Box className="flex min-h-screen items-center justify-center bg-mesh-warm px-4 py-8">
      <Paper className="grid max-w-6xl overflow-hidden rounded-[36px] border border-white/70 bg-white/90 shadow-dashboard lg:grid-cols-[1.1fr_0.9fr]">
        <Stack className="justify-between bg-sea p-10 text-white">
          <Stack spacing={2}>
            <Typography variant="overline" className="tracking-[0.32em] text-white/70">
              Biomedical Knowledge Console
            </Typography>
            <Typography variant="h3">
              Investigate the graph, validate Cypher outputs, and keep auth under Postgres.
            </Typography>
            <Typography className="max-w-xl text-white/75">
              This UI sits on top of the FastAPI backend and Neo4j query library. Login, run curated
              graph queries, and inspect subgraphs interactively.
            </Typography>
          </Stack>
          <Stack direction="row" spacing={2} className="flex-wrap" useFlexGap>
            <Box className="rounded-full border border-white/20 px-4 py-2">React + TypeScript</Box>
            <Box className="rounded-full border border-white/20 px-4 py-2">Material UI + Tailwind</Box>
            <Box className="rounded-full border border-white/20 px-4 py-2">Neo4j Graph Explorer</Box>
          </Stack>
        </Stack>
        <Stack spacing={4} className="p-8 lg:p-10">
          <Stack spacing={1}>
            <Typography variant="h4">{mode === "login" ? "Sign in" : "Create account"}</Typography>
            <Typography color="text.secondary">Use the backend auth endpoints to enter the console.</Typography>
          </Stack>
          <Tabs value={mode} onChange={(_, value) => setMode(value)} sx={{ minHeight: 44 }}>
            <Tab label="Login" value="login" />
            <Tab label="Register" value="register" />
          </Tabs>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <Stack
            component="form"
            spacing={2.5}
            onSubmit={async (event) => {
              event.preventDefault();
              setIsSubmitting(true);
              setError(null);
              try {
                if (mode === "login") {
                  await login({ email: form.email, password: form.password });
                } else {
                  await register(form);
                }
                navigate(redirectPath, { replace: true });
              } catch (caughtError) {
                setError("Authentication failed. Check the form values and backend availability.");
              } finally {
                setIsSubmitting(false);
              }
            }}
          >
            <TextField
              label="Email"
              type="email"
              value={form.email}
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              required
              fullWidth
            />
            {mode === "register" ? (
              <TextField
                label="Full name"
                value={form.full_name}
                onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
                required
                fullWidth
              />
            ) : null}
            <TextField
              label="Password"
              type="password"
              value={form.password}
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
              required
              fullWidth
              helperText="Backend requires at least 8 characters."
            />
            <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
              {mode === "login" ? "Enter dashboard" : "Create account"}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
}
