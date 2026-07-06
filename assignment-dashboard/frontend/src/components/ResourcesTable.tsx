"use client";
import React, { useEffect, useState } from "react";
import {
  Alert, Box, Chip, CircularProgress, Snackbar,
  Stack, Table, TableBody, TableCell, TableHead, TableRow,
  Typography,
} from "@mui/material";
import { apiFetch } from "@/lib/api";
import { useRole } from "@/context/RoleContext";
import type { Resource } from "@/lib/types";

const AVAIL_COLORS: Record<string, "success" | "warning" | "default"> = {
  Available: "success",
  Busy: "warning",
  "On Leave": "default",
};

export default function ResourcesTable() {
  const { role } = useRole();
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [snack, setSnack] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Resource[]>("/resources", role)
      .then(setResources)
      .catch((e) => setSnack(String(e)))
      .finally(() => setLoading(false));
  }, [role]);

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>Resources</Typography>
      {loading ? (
        <CircularProgress />
      ) : (
        <Table size="small" sx={{ bgcolor: "#fff", borderRadius: 1 }}>
          <TableHead>
            <TableRow sx={{ "& th": { fontWeight: 700 } }}>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Availability</TableCell>
              <TableCell>Utilization</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {resources.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography variant="body2" color="text.secondary">No resources yet.</Typography>
                </TableCell>
              </TableRow>
            ) : resources.map((r) => (
              <TableRow key={r.resource_id} hover>
                <TableCell>{r.name}</TableCell>
                <TableCell>{r.email ?? "—"}</TableCell>
                <TableCell>
                  <Chip label={r.availability} size="small" color={AVAIL_COLORS[r.availability] ?? "default"} />
                </TableCell>
                <TableCell>{r.utilization ?? 0}%</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)}>
        <Alert severity="error" onClose={() => setSnack(null)}>{snack}</Alert>
      </Snackbar>
    </Box>
  );
}
