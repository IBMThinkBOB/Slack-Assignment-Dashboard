"use client";
import React, { useEffect, useState } from "react";
import {
  Alert, Box, Button, CircularProgress, Dialog, DialogActions,
  DialogContent, DialogTitle, MenuItem, Select, Snackbar,
  Stack, TextField, Typography,
} from "@mui/material";
import { apiFetch } from "@/lib/api";
import { useRole } from "@/context/RoleContext";
import type { Resource } from "@/lib/types";

interface Props {
  open: boolean;
  projectId: string | null;
  onClose: () => void;
  onAssigned: () => void;
}

export default function AssignResourceModal({ open, projectId, onClose, onAssigned }: Props) {
  const { role } = useRole();
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(false);
  const [resourceId, setResourceId] = useState("");
  const [assignRole, setAssignRole] = useState("");
  const [saving, setSaving] = useState(false);
  const [snack, setSnack] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    apiFetch<Resource[]>("/resources", role)
      .then(setResources)
      .catch((e) => setSnack(String(e)))
      .finally(() => setLoading(false));
  }, [open, role]);

  async function handleAssign() {
    if (!resourceId || !projectId) return;
    setSaving(true);
    try {
      await apiFetch("/assignments", role, {
        method: "POST",
        body: JSON.stringify({ project_id: projectId, resource_id: resourceId, role: assignRole || null }),
      });
      onAssigned();
    } catch (e) {
      setSnack(String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
        <DialogTitle>Assign Resource</DialogTitle>
        <DialogContent>
          {loading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}><CircularProgress /></Box>
          ) : (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">Resource</Typography>
                <Select
                  fullWidth size="small" displayEmpty
                  value={resourceId}
                  onChange={(e) => setResourceId(e.target.value)}
                >
                  <MenuItem value="" disabled>Select a resource</MenuItem>
                  {resources.map((r) => (
                    <MenuItem key={r.resource_id} value={r.resource_id}>
                      {r.name} ({r.availability})
                    </MenuItem>
                  ))}
                </Select>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Role (optional)</Typography>
                <TextField
                  fullWidth size="small" placeholder="e.g. Storage SME"
                  value={assignRole}
                  onChange={(e) => setAssignRole(e.target.value)}
                />
              </Box>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="contained" onClick={handleAssign} disabled={!resourceId || saving}>
            {saving ? "Assigning…" : "Assign"}
          </Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)}>
        <Alert severity="error" onClose={() => setSnack(null)}>{snack}</Alert>
      </Snackbar>
    </>
  );
}
