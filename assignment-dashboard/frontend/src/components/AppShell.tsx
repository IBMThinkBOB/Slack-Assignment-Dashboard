"use client";
import {
  AppBar, Box, Chip, Drawer, List, ListItemButton,
  ListItemText, Toolbar, Typography, Switch, FormControlLabel,
} from "@mui/material";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRole } from "@/context/RoleContext";

const DRAWER_WIDTH = 200;

const NAV = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Resources", href: "/resources" },
  { label: "My Assignments", href: "/my-assignments" },
  { label: "Slack Simulator", href: "/slack-simulator" },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { role, setRole, isAdmin } = useRole();

  return (
    <Box sx={{ display: "flex" }}>
      {/* ── Top bar ── */}
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1, bgcolor: "#1f2328" }}>
        <Toolbar sx={{ gap: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1, fontSize: 15, fontWeight: 600 }}>
            Assignment Dashboard
          </Typography>
          {/* Role toggle — Phase 1 demo only */}
          <FormControlLabel
            control={
              <Switch
                checked={isAdmin}
                onChange={(e) => setRole(e.target.checked ? "admin" : "user")}
                size="small"
                sx={{ "& .MuiSwitch-thumb": { bgcolor: isAdmin ? "#3b82d4" : "#aaa" } }}
              />
            }
            label={
              <Chip
                label={isAdmin ? "Admin" : "User"}
                size="small"
                color={isAdmin ? "primary" : "default"}
                sx={{ fontSize: 11 }}
              />
            }
            labelPlacement="start"
          />
        </Toolbar>
      </AppBar>

      {/* ── Sidebar ── */}
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box", top: 64 },
        }}
      >
        <List dense>
          {NAV.map(({ label, href }) => (
            <ListItemButton
              key={href}
              component={Link}
              href={href}
              selected={pathname === href}
              sx={{ "&.Mui-selected": { bgcolor: "primary.light", color: "primary.contrastText" } }}
            >
              <ListItemText primary={label} slotProps={{ primary: { sx: { fontSize: 13 } } }} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>

      {/* ── Main content ── */}
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8, ml: `${DRAWER_WIDTH}px` }}>
        {children}
      </Box>
    </Box>
  );
}
