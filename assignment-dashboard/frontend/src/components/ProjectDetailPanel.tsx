"use client";
import React, { useCallback, useEffect, useState } from "react";
import {
  Alert, Box, Button, Chip, CircularProgress, Divider,
  Drawer, IconButton, Snackbar, Stack, Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import PersonAddIcon from "@mui/icons-material/PersonAdd";

import { apiFetch } from "@/lib/api";
import { useRole } from "@/context/RoleContext";
import type { Assignment, Project } from "@/lib/types";
import AssignResourceModal from "./AssignResourceModal";

interface Props {
  projectId: string | null;
  onClose: () => void;
  onRefresh: () => void;
}

export default function ProjectDetailPanel({ projectId, onClose, onRefresh }: Props) {
  const { role, isAdmin } = useRole();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [snack, setSnack] = useState<{ msg: string; sev: "success" | "error" } | null>(null);

  const load = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const p = await apiFetch<Project>(`/projects/${projectId}`, role);
      setProject(p);
    } catch (e) {
      setSnack({ msg: String(e), sev: "error" });
    } finally {
      setLoading(false);
    }
  }, [projectId, role]);

  useEffect(() => { load(); }, [load]);

  async function removeAssignment(assignmentId: string) {
    try {
      await apiFetch(`/assignments/${assignmentId}`, role, { method: "DELETE" });
      load();
      onRefresh();
    } catch (e) {
      setSnack({ msg: String(e), sev: "error" });
    }
  }

  return (
    <Drawer anchor="right" open={!!projectId} onClose={onClose} slotProps={{ paper: { sx: { width: 420, p: 3 } } }}>
      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", mt: 6 }}>
          <CircularProgress />
        </Box>
      ) : project ? (
        <Stack spacing={2}>
          {/* Title row */}
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>{project.name}</Typography>
              <Typography variant="body2" color="text.secondary">{project.customer}</Typography>
            </Box>
            <IconButton onClick={onClose} size="small"><CloseIcon /></IconButton>
          </Box>

          {/* Status chips */}
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
            <Chip label={project.status} size="small" color="primary" />
            {project.type && <Chip label={project.type} size="small" variant="outlined" />}
            {project.priority && <Chip label={project.priority} size="small" variant="outlined" />}
            <Chip label={`Source: ${project.source}`} size="small" variant="outlined" sx={{ textTransform: "capitalize" }} />
          </Box>

          <Box>
            <Typography variant="caption" color="text.secondary">TIMELINE</Typography>
            <Typography variant="body2">{project.start_date ?? "—"} → {project.end_date ?? "—"}</Typography>
          </Box>

          <Box>
            <Typography variant="caption" color="text.secondary">PROGRESS</Typography>
            <Typography variant="body2">{project.progress_percent ?? 0}%</Typography>
          </Box>

          {project.description && (
            <Box>
              <Typography variant="caption" color="text.secondary">DESCRIPTION</Typography>
              <Typography variant="body2">{project.description}</Typography>
            </Box>
          )}

          {project.required_skills?.length > 0 && (
            <Box>
              <Typography variant="caption" color="text.secondary">REQUIRED SKILLS</Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mt: 0.5 }}>
                {project.required_skills.map((s) => (
                  <Chip key={s} label={s} size="small" color="secondary" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}

          <Divider />

          {/* Assignments header */}
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Assignments</Typography>
            {isAdmin && (
              <Button size="small" startIcon={<PersonAddIcon />} onClick={() => setAssignOpen(true)}>
                Assign
              </Button>
            )}
          </Box>

          {(!project.assignments || project.assignments.length === 0) ? (
            <Typography variant="body2" color="text.secondary">No assignments yet.</Typography>
          ) : (
            project.assignments.map((a: Assignment) => (
              <Box
                key={a.assignment_id}
                sx={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  p: 1, border: "1px solid #e5e7eb", borderRadius: 1,
                }}
              >
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{a.resource_name}</Typography>
                  <Typography variant="caption" color="text.secondary">{a.role ?? "No role"} · {a.status}</Typography>
                </Box>
                {isAdmin && (
                  <Button size="small" color="error" onClick={() => removeAssignment(a.assignment_id)}>
                    Remove
                  </Button>
                )}
              </Box>
            ))
          )}
        </Stack>
      ) : null}

      <AssignResourceModal
        open={assignOpen}
        projectId={projectId}
        onClose={() => setAssignOpen(false)}
        onAssigned={() => { setAssignOpen(false); load(); onRefresh(); }}
      />

      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)}>
        <Alert severity={snack?.sev ?? "info"} onClose={() => setSnack(null)}>{snack?.msg}</Alert>
      </Snackbar>
    </Drawer>
  );
}
