"use client";
import React, { useEffect, useState } from "react";
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle, LinearProgress,
  MenuItem, Select, Slider, Snackbar, Stack, Typography,
} from "@mui/material";
import { apiFetch } from "@/lib/api";
import { useRole } from "@/context/RoleContext";
import type { Assignment, Resource } from "@/lib/types";

const STATUS_COLORS: Record<string, "success" | "warning" | "error" | "default"> = {
  Assigned: "default",
  "In Progress": "success",
  Completed: "success",
  Removed: "error",
};

interface UpdateModalProps {
  assignment: Assignment | null;
  onClose: () => void;
  onSaved: () => void;
}

function UpdateProgressModal({ assignment, onClose, onSaved }: UpdateModalProps) {
  const { role } = useRole();
  const [status, setStatus] = useState(assignment?.status ?? "Assigned");
  const [progress, setProgress] = useState(assignment?.progress_percent ?? 0);
  const [saving, setSaving] = useState(false);
  const [snack, setSnack] = useState<string | null>(null);

  useEffect(() => {
    if (assignment) {
      setStatus(assignment.status);
      setProgress(assignment.progress_percent ?? 0);
    }
  }, [assignment]);

  async function save() {
    if (!assignment) return;
    setSaving(true);
    try {
      await apiFetch(`/assignments/${assignment.assignment_id}`, role, {
        method: "PUT",
        body: JSON.stringify({ status, progress_percent: progress }),
      });
      onSaved();
    } catch (e) {
      setSnack(String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Dialog open={!!assignment} onClose={onClose} fullWidth maxWidth="xs">
        <DialogTitle>Update Progress</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Box>
              <Typography variant="caption" color="text.secondary">Status</Typography>
              <Select fullWidth size="small" value={status} onChange={(e) => setStatus(e.target.value)}>
                {["Assigned", "In Progress", "Completed", "Removed"].map((s) => (
                  <MenuItem key={s} value={s}>{s}</MenuItem>
                ))}
              </Select>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Progress: {progress}%</Typography>
              <Slider
                value={progress}
                onChange={(_, v) => setProgress(v as number)}
                min={0} max={100} step={5}
                marks={[{ value: 0, label: "0%" }, { value: 50, label: "50%" }, { value: 100, label: "100%" }]}
              />
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="contained" onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)}>
        <Alert severity="error" onClose={() => setSnack(null)}>{snack}</Alert>
      </Snackbar>
    </>
  );
}

const SIM_USER_NAME_KEY = "sim_user_name";

export default function MyAssignments() {
  const { role } = useRole();
  const [resources, setResources] = useState<Resource[]>([]);
  const [selectedResourceId, setSelectedResourceId] = useState("");
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState<Assignment | null>(null);
  const [snack, setSnack] = useState<string | null>(null);

  useEffect(() => {
    const simName = localStorage.getItem(SIM_USER_NAME_KEY)?.toLowerCase() ?? "";
    apiFetch<Resource[]>("/resources", role)
      .then((rs) => {
        setResources(rs);
        if (rs.length === 0) return;
        // Try to auto-select the resource that matches the simulator user name
        const match = simName
          ? rs.find((r) => r.name.toLowerCase().startsWith(simName))
          : null;
        setSelectedResourceId(match ? match.resource_id : rs[0].resource_id);
      })
      .catch((e) => setSnack(String(e)));
  }, [role]);

  useEffect(() => {
    if (!selectedResourceId) return;
    setLoading(true);
    apiFetch<Assignment[]>(`/assignments?resource_id=${selectedResourceId}`, role)
      .then(setAssignments)
      .catch((e) => setSnack(String(e)))
      .finally(() => setLoading(false));
  }, [selectedResourceId, role]);

  function reload() {
    if (!selectedResourceId) return;
    setLoading(true);
    apiFetch<Assignment[]>(`/assignments?resource_id=${selectedResourceId}`, role)
      .then(setAssignments)
      .catch((e) => setSnack(String(e)))
      .finally(() => setLoading(false));
  }

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>My Assignments</Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="body2" color="text.secondary">Viewing as:</Typography>
          <Select
            size="small" displayEmpty value={selectedResourceId}
            onChange={(e) => setSelectedResourceId(e.target.value)}
            sx={{ minWidth: 160 }}
          >
            {resources.map((r) => (
              <MenuItem key={r.resource_id} value={r.resource_id}>{r.name}</MenuItem>
            ))}
          </Select>
        </Box>
      </Box>

      {loading ? (
        <CircularProgress />
      ) : assignments.length === 0 ? (
        <Typography color="text.secondary">No assignments found for this resource.</Typography>
      ) : (
        <Stack spacing={2}>
          {assignments.map((a) => (
            <Card key={a.assignment_id} variant="outlined">
              <CardContent>
                <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <Box>
                    <Typography sx={{ fontWeight: 700 }}>{a.project_name ?? "Unknown project"}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {a.role ?? "No role"} · {a.resource_name}
                    </Typography>
                  </Box>
                  <Chip
                    label={a.status}
                    size="small"
                    color={STATUS_COLORS[a.status] ?? "default"}
                  />
                </Box>

                <Box sx={{ mt: 1.5 }}>
                  <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">Progress</Typography>
                    <Typography variant="caption">{a.progress_percent ?? 0}%</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={a.progress_percent ?? 0}
                    sx={{ borderRadius: 1, height: 6 }}
                  />
                </Box>

                <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 1.5 }}>
                  <Button size="small" variant="outlined" onClick={() => setEditing(a)}>
                    Update Progress
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}

      <UpdateProgressModal
        assignment={editing}
        onClose={() => setEditing(null)}
        onSaved={() => { setEditing(null); reload(); }}
      />

      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)}>
        <Alert severity="error" onClose={() => setSnack(null)}>{snack}</Alert>
      </Snackbar>
    </Box>
  );
}
