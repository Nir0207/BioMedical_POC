import { useState } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  AppBar,
  Box,
  Button,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  Toolbar,
  Typography
} from "@mui/material";
import MenuRoundedIcon from "@mui/icons-material/MenuRounded";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import SchemaRoundedIcon from "@mui/icons-material/SchemaRounded";
import TravelExploreRoundedIcon from "@mui/icons-material/TravelExploreRounded";
import HubRoundedIcon from "@mui/icons-material/HubRounded";
import { useAuth } from "../features/auth/AuthContext";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: <DashboardRoundedIcon fontSize="small" /> },
  { to: "/queries", label: "Query Workbench", icon: <SchemaRoundedIcon fontSize="small" /> },
  { to: "/graph", label: "Graph Explorer", icon: <TravelExploreRoundedIcon fontSize="small" /> },
  { to: "/query-canvas", label: "Query Canvas", icon: <HubRoundedIcon fontSize="small" /> }
];

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const drawerContent = (
    <Stack className="h-full rounded-r-[32px] bg-white/80 p-4 backdrop-blur">
      <Box className="rounded-[28px] bg-sea p-5 text-white">
        <Typography variant="overline" className="tracking-[0.28em] text-white/70">
          Biomedical Console
        </Typography>
        <Typography variant="h5" mt={1}>
          Graph intelligence with query control.
        </Typography>
      </Box>
      <List className="mt-6 space-y-2">
        {navItems.map((item) => (
          <ListItemButton
            key={item.to}
            component={NavLink}
            to={item.to}
            selected={location.pathname.startsWith(item.to)}
            onClick={() => setMobileOpen(false)}
            className="rounded-3xl px-4 py-3"
          >
            <Stack direction="row" spacing={1.5} alignItems="center">
              {item.icon}
              <ListItemText primary={item.label} />
            </Stack>
          </ListItemButton>
        ))}
      </List>
      <Box className="mt-auto rounded-[28px] border border-sand bg-[#fff7ea] p-4">
        <Typography variant="subtitle2" fontWeight={700}>
          Signed in
        </Typography>
        <Typography>{user?.full_name}</Typography>
        <Typography variant="body2" color="text.secondary">
          {user?.email}
        </Typography>
      </Box>
    </Stack>
  );

  return (
    <Box className="min-h-screen bg-mesh-warm">
      <AppBar position="sticky" color="transparent" elevation={0}>
        <Toolbar className="border-b border-white/40 bg-[#f6f1e8cc] backdrop-blur">
          <IconButton edge="start" onClick={() => setMobileOpen(true)} className="mr-2 lg:hidden">
            <MenuRoundedIcon />
          </IconButton>
          <Typography variant="h6" fontWeight={700} flexGrow={1}>
            {navItems.find((item) => location.pathname.startsWith(item.to))?.label ?? "Biomedical Console"}
          </Typography>
          <Button
            color="secondary"
            variant="contained"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Sign out
          </Button>
        </Toolbar>
      </AppBar>
      <Box className="mx-auto flex max-w-[1600px] gap-6 px-4 py-6 lg:px-6">
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          className="lg:hidden"
          PaperProps={{ className: "w-80 bg-transparent shadow-none" }}
        >
          {drawerContent}
        </Drawer>
        <Drawer
          variant="permanent"
          open
          PaperProps={{
            className: "hidden h-[calc(100vh-96px)] w-[320px] rounded-[32px] border border-white/60 bg-transparent p-0 lg:block"
          }}
        >
          {drawerContent}
        </Drawer>
        <Box component="main" className="min-w-0 flex-1 lg:ml-[320px]">
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
