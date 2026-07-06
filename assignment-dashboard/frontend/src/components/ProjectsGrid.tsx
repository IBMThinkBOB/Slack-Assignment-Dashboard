"use client";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { AgGridReact } from "ag-grid-react";
import { AllCommunityModule, ModuleRegistry, type ColDef } from "ag-grid-community";
import {
  Alert, Box, Button, Chip, MenuItem, Select,
  Snackbar, TextField, Typography,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";

// Register all AG Grid Community modules once (required from v32+)
ModuleRegistry.registerModules([AllCommunityModule]);

import { apiFetch, apiUpload } from "@/lib/api";
import { useRole } from "@/context/RoleContext";
import type { Project } from "@/lib/types";
import ProjectDetailPanel from "./ProjectDetailPanel";

const STATUS_COLORS: Record<string, "success" | "warning" | "error" | "default"> = {
  Active: "success",
  "In Progress": "success",
  "On Hold": "warning",
  Completed: "default",
  Cancelled: "error",
};

export default function ProjectsGrid() {
  const { role } = useRole();
  const [rows, setRows] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Project | null>(null);
  const [filterStatus, setFilterStatus] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterCustomer, setFilterCustomer] = useState("");
  const [snack, setSnack] = useState<{ msg: string; sev: "success" | "error" } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterStatus) params.set("status", filterStatus);
      if (filterType) params.set("type", filterType);
      if (filterCustomer) params.set("customer", filterCustomer);
      const data = await apiFetch<Project[]>(`/projects?${params}`, role);
      setRows(data);
    } catch (e: unknown) {
      setSnack({ msg: String(e), sev: "error" });
    } finally {
      setLoading(false);
    }
  }, [role, filterStatus, filterType, filterCustomer]);

  useEffect(() => { load(); }, [load]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await apiUpload<{ inserted: number; updated: number; total: number }>(
        "/excel/upload", role, fd
      );
      setSnack({ msg: `Imported ${res.total} projects (${res.inserted} new, ${res.updated} updated)`, sev: "success" });
      load();
    } catch (e: unknown) {
      setSnack({ msg: String(e), sev: "error" });
    }
    if (fileRef.current) fileRef.current.value = "";
  }

  const colDefs: ColDef<Project>[] = [
    { field: "name", headerName: "Project", flex: 2, minWidth: 160 },
    { field: "customer", headerName: "Customer", flex: 1, minWidth: 120 },
    {
      field: "assigned_to", headerName: "Assigned To", flex: 1, minWidth: 130,
      cellRenderer: ({ value }: { value: string }) => (
        <Typography
          variant="body2"
          sx={{ fontSize: 12, color: value === "Unassigned" ? "#57606a" : "#1f2328", fontStyle: value === "Unassigned" ? "italic" : "normal" }}
        >
          {value ?? "Unassigned"}
        </Typography>
      ),
    },
    { field: "type", headerName: "Type", width: 110 },
    {
      field: "status", headerName: "Status", width: 120,
      cellRenderer: ({ value }: { value: string }) => (
        <Chip label={value} size="small" color={STATUS_COLORS[value] ?? "default"} sx={{ fontSize: 11 }} />
      ),
    },
    {
      field: "progress_percent", headerName: "Progress", width: 100,
      cellRenderer: ({ value }: { value: number }) => `${value ?? 0}%`,
    },
    { field: "start_date", headerName: "Start", width: 110 },
    { field: "end_date", headerName: "End", width: 110 },
    {
      field: "source", headerName: "Source", width: 90,
      cellRenderer: ({ value }: { value: string }) => (
        <Chip label={value} size="small" variant="outlined" sx={{ fontSize: 11, textTransform: "capitalize" }} />
      ),
    },
  ];

  return (
    <Box>
      {/* ── Header ── */}
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Assignment Overview</Typography>
        {role === "admin" && (
          <>
            <input ref={fileRef} type="file" accept=".xlsx" hidden onChange={handleUpload} />
            <Button
              variant="outlined"
              size="small"
              startIcon={<UploadFileIcon />}
              onClick={() => fileRef.current?.click()}
            >
              Import Excel
            </Button>
          </>
        )}
      </Box>

      {/* ── Filters ── */}
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}>
        <Select size="small" displayEmpty value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} sx={{ minWidth: 130 }}>
          <MenuItem value="">All Statuses</MenuItem>
          {["Active", "In Progress", "On Hold", "Completed", "Cancelled"].map((s) => (
            <MenuItem key={s} value={s}>{s}</MenuItem>
          ))}
        </Select>
        <Select size="small" displayEmpty value={filterType} onChange={(e) => setFilterType(e.target.value)} sx={{ minWidth: 130 }}>
          <MenuItem value="">All Types</MenuItem>
          {["Paid", "Presales", "Internal", "Support"].map((t) => (
            <MenuItem key={t} value={t}>{t}</MenuItem>
          ))}
        </Select>
        <TextField
          size="small" placeholder="Filter by customer" value={filterCustomer}
          onChange={(e) => setFilterCustomer(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          sx={{ minWidth: 180 }}
        />
        <Button size="small" variant="contained" onClick={load}>Apply</Button>
        <Button size="small" onClick={() => { setFilterStatus(""); setFilterType(""); setFilterCustomer(""); }}>Clear</Button>
      </Box>

      {/* ── AG Grid ── */}
      <Box className="ag-theme-alpine" sx={{ height: 520, width: "100%", borderRadius: 1, overflow: "hidden" }}>
        <AgGridReact
          rowData={rows}
          columnDefs={colDefs}
          loading={loading}
          rowSelection="single"
          onRowClicked={(e) => setSelected(e.data as Project)}
          animateRows
          suppressCellFocus
          defaultColDef={{ sortable: true, resizable: true, filter: true }}
        />
      </Box>

      {/* ── Detail panel ── */}
      <ProjectDetailPanel
        projectId={selected?.project_id ?? null}
        onClose={() => setSelected(null)}
        onRefresh={load}
      />

      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)}>
        <Alert severity={snack?.sev ?? "info"} onClose={() => setSnack(null)}>{snack?.msg}</Alert>
      </Snackbar>
    </Box>
  );
}
