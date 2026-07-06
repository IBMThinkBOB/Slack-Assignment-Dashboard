"""Integration tests covering the Phase 1 MVP API surface."""
import io
import json
from pathlib import Path

import openpyxl
import pytest


# ──────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ──────────────────────────────────────────────
# Slack Events — url_verification
# ──────────────────────────────────────────────

def test_slack_url_verification(client):
    payload = {"type": "url_verification", "challenge": "test-challenge-abc"}
    r = client.post("/slack/events", json=payload)
    assert r.status_code == 200
    assert r.json()["challenge"] == "test-challenge-abc"


# ──────────────────────────────────────────────
# Slack Events — message stored, processed=False
# ──────────────────────────────────────────────

def test_slack_message_stored(client):
    payload = {
        "type": "event_callback",
        "event": {
            "type": "message",
            "text": "Need Storage Scale support for ABC Corp starting July",
            "user": "U12345",
            "channel": "C99999",
            "ts": "1716400000.000001",
        },
    }
    r = client.post("/slack/events", json=payload)
    assert r.status_code == 200

    # Event should appear in the admin listing
    r2 = client.get("/slack/events", headers={"X-Role": "admin"})
    assert r2.status_code == 200
    events = r2.json()
    assert len(events) == 1
    assert events[0]["text"] == "Need Storage Scale support for ABC Corp starting July"
    assert events[0]["processed"] is False


def test_slack_events_requires_admin(client):
    r = client.get("/slack/events", headers={"X-Role": "user"})
    assert r.status_code == 403


# ──────────────────────────────────────────────
# Resources CRUD
# ──────────────────────────────────────────────

def test_create_and_list_resources(client):
    # Admin can create
    r = client.post("/resources", json={"name": "John Smith", "email": "john@example.com"}, headers={"X-Role": "admin"})
    assert r.status_code == 201
    resource = r.json()
    assert resource["name"] == "John Smith"
    assert resource["availability"] == "Available"

    # Anyone can list
    r2 = client.get("/resources")
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_create_resource_requires_admin(client):
    r = client.post("/resources", json={"name": "Jane"}, headers={"X-Role": "user"})
    assert r.status_code == 403


# ──────────────────────────────────────────────
# Projects CRUD
# ──────────────────────────────────────────────

def test_create_and_list_projects(client):
    r = client.post(
        "/projects",
        json={"name": "Test Project", "customer": "ACME"},
        headers={"X-Role": "admin"},
    )
    assert r.status_code == 201
    p = r.json()
    assert p["name"] == "Test Project"
    assert p["source"] == "manual"

    r2 = client.get("/projects")
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_get_project_with_assignments(client):
    rr = client.post("/resources", json={"name": "Alice"}, headers={"X-Role": "admin"})
    pr = client.post("/projects", json={"name": "Proj", "customer": "Corp"}, headers={"X-Role": "admin"})
    project_id = pr.json()["project_id"]
    resource_id = rr.json()["resource_id"]

    client.post(
        "/assignments",
        json={"project_id": project_id, "resource_id": resource_id, "role": "SME"},
        headers={"X-Role": "admin"},
    )

    r = client.get(f"/projects/{project_id}")
    assert r.status_code == 200
    data = r.json()
    assert len(data["assignments"]) == 1
    assert data["assignments"][0]["resource_name"] == "Alice"


def test_project_filter_by_status(client):
    client.post("/projects", json={"name": "A", "customer": "C", "status": "Active"}, headers={"X-Role": "admin"})
    client.post("/projects", json={"name": "B", "customer": "C", "status": "Completed"}, headers={"X-Role": "admin"})

    r = client.get("/projects?status=Active")
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "A"


# ──────────────────────────────────────────────
# Assignments CRUD + role guard
# ──────────────────────────────────────────────

def test_assign_resource_admin_only(client):
    rr = client.post("/resources", json={"name": "Bob"}, headers={"X-Role": "admin"})
    pr = client.post("/projects", json={"name": "P", "customer": "C"}, headers={"X-Role": "admin"})

    r = client.post(
        "/assignments",
        json={"project_id": pr.json()["project_id"], "resource_id": rr.json()["resource_id"]},
        headers={"X-Role": "user"},
    )
    assert r.status_code == 403


def test_assign_and_remove(client):
    rr = client.post("/resources", json={"name": "Carol"}, headers={"X-Role": "admin"})
    pr = client.post("/projects", json={"name": "Q", "customer": "D"}, headers={"X-Role": "admin"})

    ar = client.post(
        "/assignments",
        json={"project_id": pr.json()["project_id"], "resource_id": rr.json()["resource_id"], "role": "Architect"},
        headers={"X-Role": "admin"},
    )
    assert ar.status_code == 201
    assignment_id = ar.json()["assignment_id"]

    # User can update progress
    ur = client.put(
        f"/assignments/{assignment_id}",
        json={"status": "In Progress", "progress_percent": 50},
        headers={"X-Role": "user"},
    )
    assert ur.status_code == 200
    assert ur.json()["progress_percent"] == 50

    # User cannot change role
    br = client.put(
        f"/assignments/{assignment_id}",
        json={"role": "PM"},
        headers={"X-Role": "user"},
    )
    assert br.status_code == 403

    # Admin can delete
    dr = client.delete(f"/assignments/{assignment_id}", headers={"X-Role": "admin"})
    assert dr.status_code == 204


# ──────────────────────────────────────────────
# Excel Upload
# ──────────────────────────────────────────────

def _make_xlsx(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = ["Project Name", "Customer", "Description", "Start Date", "End Date",
               "Project Type", "Priority", "Progress", "Manager", "Practice", "Required Skills"]
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_excel_upload_inserts_projects(client):
    xlsx = _make_xlsx([
        ["Storage Deployment", "ABC Corp", "Deploy storage cluster", "2024-07-01", "2024-09-30",
         "Paid", "High", 10, "Mike", "Storage", "Storage Scale, Linux"],
        ["Cloud Migration", "Globex", "Migrate to AWS", "2024-06-01", "2024-08-31",
         "Presales", "Medium", 0, "Sarah", "Cloud", "AWS, Terraform"],
    ])

    r = client.post(
        "/excel/upload",
        files={"file": ("projects.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers={"X-Role": "admin"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["inserted"] == 2
    assert body["updated"] == 0
    assert body["total"] == 2

    projects = client.get("/projects").json()
    assert len(projects) == 2
    names = {p["name"] for p in projects}
    assert "Storage Deployment" in names
    assert "Cloud Migration" in names


def test_excel_upload_upserts_existing(client):
    xlsx1 = _make_xlsx([["Proj X", "Corp Y", "", None, None, "Paid", "High", 10, "", "", ""]])
    client.post("/excel/upload", files={"file": ("p.xlsx", xlsx1, "")}, headers={"X-Role": "admin"})

    xlsx2 = _make_xlsx([["Proj X", "Corp Y", "Updated desc", None, None, "Paid", "High", 50, "", "", ""]])
    r = client.post("/excel/upload", files={"file": ("p.xlsx", xlsx2, "")}, headers={"X-Role": "admin"})
    body = r.json()
    assert body["inserted"] == 0
    assert body["updated"] == 1

    projects = client.get("/projects").json()
    assert projects[0]["progress_percent"] == 50


def test_excel_upload_missing_required_column(client):
    # File with only "Project Name" — missing "Customer"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Project Name", "Description"])
    ws.append(["Test", "desc"])
    buf = io.BytesIO()
    wb.save(buf)

    r = client.post(
        "/excel/upload",
        files={"file": ("bad.xlsx", buf.getvalue(), "")},
        headers={"X-Role": "admin"},
    )
    assert r.status_code == 422
    assert "Customer" in r.json()["detail"]


def test_excel_upload_requires_admin(client):
    xlsx = _make_xlsx([["P", "C", "", None, None, None, None, 0, "", "", ""]])
    r = client.post("/excel/upload", files={"file": ("f.xlsx", xlsx, "")}, headers={"X-Role": "user"})
    assert r.status_code == 403
