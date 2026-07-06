# Phase 1 Plan — Assignment Visibility & Resource Alignment Platform

## Top-Level Overview

Build the Phase 1 MVP of the Assignment Visibility & Resource Alignment Platform.

**Goal:** Give managers a single dashboard where they can see all projects, their status, and who is assigned — sourced from Slack messages and Excel uploads.

**Scope:** Phase 1 only. No Salesforce, no Microsoft Graph, no Skills Inventory, no Recommendations, no Workflow Builder.

**Stack:**
- **Frontend:** Next.js (React, TypeScript), MUI, AG Grid, Recharts
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **NLP/Extraction:** OpenAI-compatible provider abstraction — configured via `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` env vars (no vendor lock-in)
- **Auth:** Header-based role check (`X-Role: admin` / `X-Role: user`) with a UI role toggle. No JWT or sessions. Microsoft Entra ID + RBAC comes in a later phase.

**Monorepo layout:**
```
assignment-dashboard/
├── backend/          (FastAPI)
├── frontend/         (Next.js)
├── docs/
├── sample-data/
├── docker-compose.yml
└── README.md
```

**Outcome:** A manager can post an assignment request in Slack, have it automatically captured and parsed, upload an Excel project sheet, view unified project records in a dashboard, and assign team members.

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffolding & Monorepo Setup

**Intent**
Establish the project layout so all subsequent sub-tasks have a consistent, runnable foundation. Both the frontend and backend must be independently startable and share environment configuration.

**Expected Outcomes**
- `backend/` directory with a runnable FastAPI app returning a health-check endpoint
- `frontend/` directory with a runnable Next.js app showing a placeholder page
- `.env` file at the root holds all secrets (already exists)
- `docker-compose.yml` (optional but recommended) spins up PostgreSQL locally
- `README.md` documents how to start each service

**Todo List**
1. Create the monorepo root: `assignment-dashboard/` with `docs/`, `sample-data/` directories
2. Create `backend/` — initialize Python project with `pyproject.toml` (or `requirements.txt`): FastAPI, Uvicorn, SQLAlchemy, Alembic, psycopg2-binary, python-dotenv, httpx, openai
3. Create `backend/main.py` with a `GET /health` endpoint
4. Create `frontend/` — initialize Next.js app with TypeScript, MUI, AG Grid, and Recharts dependencies
5. Create root `docker-compose.yml` with a `postgres` service (port 5432) and optionally a `backend` and `frontend` service
6. Create root `README.md` with local setup instructions for both services
7. Copy or symlink root `.env` so `backend/` reads from it via `python-dotenv`; document all required env vars (see Relevant Context below)
8. Add `.gitignore` entries for `__pycache__`, `.venv`, `node_modules`, `.env`, `.env.local`

**Relevant Context**
- Root `.env` already exists — backend reads it via `python-dotenv`
- Required env vars to document in README:
  ```
  # LLM (OpenAI-compatible)
  LLM_BASE_URL=https://api.openai.com/v1
  LLM_API_KEY=<your key>
  LLM_MODEL=gpt-4o

  # Slack
  SLACK_BOT_TOKEN=
  SLACK_SIGNING_SECRET=

  # Database
  DATABASE_URL=postgresql://user:pass@localhost:5432/assignment_db
  ```
- `BOB_API_KEY` in `.env` maps to `LLM_API_KEY` — note this in README

**Status:** [x] done

---

### Sub-Task 2 — Database Schema & Migrations

**Intent**
Define and migrate the core PostgreSQL schema that all other sub-tasks depend on. Based directly on the data model in `INSTRUCTIONS.md` §9 (Assignment Repository) and §8 (Data Model).

**Expected Outcomes**
- Alembic migration creates all tables cleanly from scratch
- All entity relationships are correctly expressed as foreign keys
- Tables are queryable via SQLAlchemy ORM models

**Todo List**
1. Configure Alembic in `backend/` pointing to `DATABASE_URL` from `.env`
2. Create SQLAlchemy models in `backend/models/`:
   - `projects` — `project_id`, `name`, `customer`, `status`, `type`, `priority`, `start_date`, `end_date`, `progress_percent`, `description`, `source` (`slack` | `excel` | `manual`), `required_skills` (JSON array), `manager`, `practice`
   - `resources` — `resource_id`, `name`, `email`, `availability`, `utilization`
   - `assignments` — `assignment_id`, `project_id` (FK→projects), `resource_id` (FK→resources), `role`, `status`
   - `slack_events` — `event_id`, `channel`, `slack_user_id`, `text`, `ts`, `processed` (bool, default false), `project_id` (FK→projects, nullable)
3. Write the initial Alembic migration (`alembic revision --autogenerate`)
4. Verify migration runs cleanly against a fresh Postgres instance via `alembic upgrade head`

**Relevant Context**
- Project entity from INSTRUCTIONS.md §9: `projectId`, `name`, `customer`, `status`, `type`
- Resource entity: `resourceId`, `name`, `availability`
- Assignment entity: `projectId`, `resourceId`, `role`, `status`
- `slack_events` is a new table needed for Phase 1 intake tracking

**Status:** [x] done

---

### Sub-Task 3 — Slack Integration (Events API + Connector)

**Intent**
Connect the platform to Slack so that messages posted in designated channels are automatically captured and stored as raw `slack_events` records. This is the primary data intake path described in INSTRUCTIONS.md §7 (Slack Connector) and §4 (System Flow Steps 1–2).

**Expected Outcomes**
- FastAPI exposes a `POST /slack/events` endpoint that Slack can POST events to
- Slack URL verification challenge is handled
- `message` events from subscribed channels are stored in the `slack_events` table
- A `GET /slack/events` endpoint lists stored raw events (for debugging)
- Slack app credentials (`SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`) are read from `.env`

**Todo List**
1. `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are already in `.env` — document their purpose in README
2. Create `backend/routers/slack.py` with:
   - `POST /slack/events` — verifies Slack signing secret (HMAC check against `SLACK_SIGNING_SECRET`), handles `url_verification` challenge, stores `message` events to `slack_events` table, fires background NLP extraction task
   - `GET /slack/events` — returns recent raw events (admin debug use)
3. Document Slack app setup steps in `docs/slack-setup.md`: create app, subscribe to `message.channels` event, set Request URL to `https://<host>/slack/events`
4. Add required Slack OAuth scopes to README: `channels:history`, `channels:read`, `chat:write`
5. Test: post a message in a Slack channel and confirm it appears in `slack_events` with `processed=false`

**Relevant Context**
- INSTRUCTIONS.md §6 Slack APIs: required scopes `channels:history`, `channels:read`, `users:read`, `chat:write`
- INSTRUCTIONS.md §6 Web API endpoints: `conversations.history`, `conversations.list`, `users.list`, `chat.postMessage`
- Slack signs requests with `X-Slack-Signature` — must verify before trusting payload

**Status:** [x] done

---

### Sub-Task 4 — NLP Extraction (Slack Message → Project Record)

**Intent**
Parse raw Slack messages into structured project fields using an OpenAI-compatible LLM provider. No vendor lock-in — the provider is fully swappable via env vars. This is INSTRUCTIONS.md §8 (Assignment Correlation Engine), NLP Extraction step.

**Expected Outcomes**
- A `POST /extract` endpoint accepts a Slack message string and returns a structured JSON object
- The extraction is triggered automatically when a new `slack_events` record arrives (via a background task)
- Extracted fields populate a new `projects` record (or update an existing one) and `slack_events.project_id` is linked
- Extraction returns a `ProjectExtraction` Pydantic model: `project_name`, `customer`, `skills` (list), `timeline_start`, `timeline_end`, `status`, `assignment_need`

**Todo List**
1. Create `backend/services/llm.py` — OpenAI-compatible client that reads `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` from env. Exposes a single `complete(prompt: str) -> str` function. `BOB_API_KEY` maps to `LLM_API_KEY`.
2. Create `backend/services/nlp.py` — defines the extraction system prompt (instructs model to return valid JSON only) and calls `llm.complete()`. Returns a `ProjectExtraction` Pydantic model.
3. Create `backend/services/correlation.py` — takes a `ProjectExtraction` and upserts a `projects` record (matched on `name` + `customer`), sets `slack_events.processed = true`, sets `slack_events.project_id`
4. Wire up `BackgroundTasks` inside `POST /slack/events` to run `nlp → correlation` after storing the raw event
5. Expose `POST /extract` for manual testing: accepts `{ "text": "..." }`, returns `ProjectExtraction` JSON
6. Handle LLM failures gracefully — log error, leave `slack_events.processed = false`, do not crash the event handler

**Relevant Context**
- `LLM_BASE_URL`, `LLM_API_KEY` (`BOB_API_KEY`), `LLM_MODEL` drive the client — switching providers requires only env var changes
- INSTRUCTIONS.md §8 NLP example: "Need Storage Scale deployment support for ABC Corp" → `{ "project": "Storage Scale Deployment", "customer": "ABC Corp", "skill": "Storage Scale" }`
- System prompt must enforce JSON-only output to allow reliable Pydantic parsing

**Status:** [x] done

---

### Sub-Task 5 — Excel Upload & Ingestion

**Intent**
Allow admins to upload an Excel file containing structured project data, which gets parsed and merged into the `projects` table. This is INSTRUCTIONS.md §7 (Excel Connector) and §5 (Excel data source).

**Expected Outcomes**
- `POST /excel/upload` endpoint accepts a `.xlsx` file and parses it
- Parsed rows are upserted into the `projects` table (matched on `name` + `customer`)
- Expected Excel columns: `Project Name`, `Customer`, `Description`, `Start Date`, `End Date`, `Project Type`, `Priority`, `Progress`, `Manager`, `Practice`, `Required Skills`
- A `GET /excel/preview` endpoint returns the last uploaded batch as JSON (for UI confirmation)

**Todo List**
1. Add `openpyxl` to backend dependencies (lighter than pandas for this use case)
2. Create `backend/routers/excel.py` with:
   - `POST /excel/upload` — accepts `multipart/form-data` file upload, validates expected columns, upserts rows into `projects`, returns count of inserted/updated rows
   - `GET /excel/preview` — returns latest `source='excel'` projects as JSON
3. Handle missing columns gracefully — return `422` with a list of which required columns are absent
4. Create `sample-data/sample-projects.xlsx` — 3–5 example rows matching the expected schema (for demo and testing)
5. Document expected column names in `docs/excel-format.md`

**Relevant Context**
- INSTRUCTIONS.md §5 Excel fields: `Project Name`, `Customer`, `Description`, `Start Date`, `End Date`, `Project Type`, `Priority`, `Progress`, `Current Team`, `Required Skills`, `Manager`, `Practice`
- Excel source sets `projects.source = 'excel'`

**Status:** [x] done

---

### Sub-Task 6 — Core REST API (Projects, Resources, Assignments)

**Intent**
Expose the CRUD API layer that the frontend dashboard will call. This is the programmatic interface to the Assignment Repository (INSTRUCTIONS.md §9).

**Expected Outcomes**
- Full CRUD for `projects`, `resources`, and `assignments`
- Admin can assign a resource to a project via `POST /assignments`
- Admin can reassign or remove an assignment
- All endpoints are documented via FastAPI's auto-generated `/docs`

**Todo List**
1. Create `backend/middleware/role_guard.py` — FastAPI dependency that reads the `X-Role` request header. Attaches `role="admin"` or `role="user"` to request state. Write endpoints (POST/PUT/DELETE) inject this dependency and return `403` for non-admin callers where required.
2. Create `backend/routers/projects.py`:
   - `GET /projects` — list all; query params: `status`, `type`, `customer`
   - `GET /projects/{id}` — single project with its assignments joined
   - `POST /projects` — create manually (admin only)
   - `PUT /projects/{id}` — update fields (admin only)
   - `DELETE /projects/{id}` — (admin only)
3. Create `backend/routers/resources.py`:
   - `GET /resources` — list all resources
   - `POST /resources` — create (admin only)
   - `PUT /resources/{id}` — update availability / utilization (admin only)
4. Create `backend/routers/assignments.py`:
   - `GET /assignments` — list, filterable by `project_id` or `resource_id`
   - `POST /assignments` — assign resource to project (admin only)
   - `PUT /assignments/{id}` — reassign / change role / update progress (admin, or the assigned resource updating their own progress)
   - `DELETE /assignments/{id}` — remove (admin only)

**Relevant Context**
- INSTRUCTIONS.md §12 Assignment Actions: Assign User, Reassign User, Remove Assignment
- INSTRUCTIONS.md §9 entities: Project, Resource, Assignment
- Phase 1 auth is `X-Role` header; Microsoft Entra + RBAC comes in a later phase

**Status:** [x] done

---

### Sub-Task 7 — Frontend: Assignment Dashboard (Admin View)

**Intent**
Build the core Next.js dashboard that gives admins full visibility into all projects, their assignments, and their status. This is INSTRUCTIONS.md Dashboard 1 (Assignment Overview) and §12 (Admin Dashboard Requirements).

**Expected Outcomes**
- `/dashboard` page renders an AG Grid table of all projects with columns: Project, Customer, Type, Status, Progress, Start Date, End Date
- Clicking a row opens a project detail panel showing: current assignments, required skills (from Excel), source (Slack/Excel/Manual)
- Admin can assign a resource to the project from the detail panel (calls `POST /assignments`)
- Admin can reassign or remove an assignment from the detail panel
- Status filter bar: filter projects by Status, Type, Customer
- Data is fetched from the FastAPI backend

**Todo List**
1. Set up Next.js app with MUI theme, global layout (sidebar nav), and a `RoleContext` that holds the current role (`admin` | `user`) and injects it as the `X-Role` header on every API call
2. Add a visible **Role Toggle** in the top nav bar (Admin / User chip switch) — Phase 1 demo only; replaced by Microsoft Entra login in a later phase
3. Create `frontend/lib/api.ts` — typed fetch wrapper that auto-injects `X-Role` from `RoleContext` and reads base URL from `NEXT_PUBLIC_API_URL`
4. Create `/dashboard` route — fetches `GET /projects`, renders AG Grid table with columns: Project, Customer, Type, Status, Progress %, Start Date, End Date, Source
5. Create `ProjectDetailPanel` (MUI Drawer) — fetches `GET /projects/{id}`, shows project metadata + assignment list
6. Create `AssignResourceModal` — lists resources from `GET /resources`, lets admin pick one and set a role, calls `POST /assignments`
7. Show/hide admin-only controls (Assign, Reassign, Remove) based on `RoleContext.role`
8. Add Status / Type / Customer filter bar above the AG Grid
9. Create `/resources` route — MUI table of all resources with availability badge
10. Add `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`

**Relevant Context**
- INSTRUCTIONS.md Dashboard 1 fields: Project, Customer, Status, Type, Progress, Timeline
- INSTRUCTIONS.md §12 Admin Dashboard: Assignment Oversight, Staffing Alignment
- INSTRUCTIONS.md §12 Assignment Actions: Assign User, Reassign User, Remove Assignment
- AG Grid is specified in the tech stack for tabular data
- MUI is specified for the component library

**Status:** [x] done

---

### Sub-Task 8 — Frontend: User Dashboard

**Intent**
Build the user-facing view where engineers and consultants can see their own assignments, project details, timelines, and update their progress. This is INSTRUCTIONS.md §13 (User Dashboard Requirements).

**Expected Outcomes**
- `/my-assignments` page shows only projects assigned to the logged-in resource
- Each assignment shows: Project name, role, timeline, required skills, progress, status
- User can update `status` and `progress_percent` on their assignment (calls `PUT /assignments/{id}`)
- User cannot access admin actions (Assign/Reassign/Remove buttons are hidden)

**Todo List**
1. Create `/my-assignments` route — fetches `GET /assignments?resource_id={id}`, renders assignment cards (for Phase 1 demo, `resource_id` is selected from a dropdown since there is no real auth session)
2. Create `AssignmentCard` — shows project name, customer, role, timeline, progress bar (MUI `LinearProgress`), status badge
3. Create `UpdateProgressModal` — lets user set `status` and `progress_percent` via dropdown + slider, calls `PUT /assignments/{id}`
4. Admin controls (Assign/Reassign/Remove) are automatically hidden via the shared `RoleContext` from Sub-Task 7 — no duplicate logic needed
5. The Role Toggle built in Sub-Task 7 covers this view too — switching to Admin reveals admin controls inline

**Relevant Context**
- INSTRUCTIONS.md §13 User Dashboard: My Assignments, My Projects, Required Skills, Timeline, Milestones, Progress, Status
- INSTRUCTIONS.md §13 Users Can: Update Status, Update Progress, View Deliverables
- INSTRUCTIONS.md §13 Cannot: Manage Projects, Assign Resources, Modify Readiness Models

**Status:** [x] done

---

### Sub-Task 9 — Integration Testing & MVP Validation

**Intent**
Verify that the full end-to-end flow works as described in INSTRUCTIONS.md §14 Prototype Success Criteria, steps 1–7 (Phase 1 relevant steps).

**Expected Outcomes**
- A manager can post a Slack message and see it auto-appear as a project in the dashboard
- A manager can upload an Excel file and see those projects in the dashboard
- A manager can assign a team member to a project from the UI
- A user can view their assignments and update progress
- All FastAPI endpoints return correct data and status codes

**Todo List**
1. Write `backend/tests/` using `pytest` + `httpx.AsyncClient` covering:
   - `POST /slack/events` — event stored, `processed=false`, background task queued
   - `POST /extract` — returns valid `ProjectExtraction` JSON for a sample message
   - `POST /excel/upload` — projects upserted from `sample-data/sample-projects.xlsx`
   - `GET /projects` — returns merged list
   - `POST /assignments` with `X-Role: admin` — assignment created
   - `POST /assignments` with `X-Role: user` — returns `403`
   - `PUT /assignments/{id}` — progress updated
   - `DELETE /assignments/{id}` with `X-Role: admin` — removed
2. Manually walk the full end-to-end demo flow using the sample data and a real Slack channel
3. Fix any integration issues discovered
4. Update `README.md` with a **Demo Walkthrough** section (step-by-step)
5. Add `sample-data/sample-slack-messages.txt` — example Slack messages that exercise the NLP extractor

**Relevant Context**
- INSTRUCTIONS.md §14 Prototype Success Criteria (Phase 1 relevant):
  1. Post or detect an assignment from Slack
  2. Automatically correlate it with Excel data
  3. View project details
  4. View required skills (from Excel `Required Skills` column)
  5. ~~View recommended resources~~ *(Phase 2)*
  6. Assign team members
  7. Monitor project progress

**Status:** [x] done

---

## Dependency Order

```
Sub-Task 1 (Scaffold)
    └── Sub-Task 2 (DB Schema)
            ├── Sub-Task 3 (Slack Connector)
            │       └── Sub-Task 4 (NLP Extraction)
            ├── Sub-Task 5 (Excel Upload)
            └── Sub-Task 6 (Core REST API)
                    ├── Sub-Task 7 (Admin Dashboard)
                    └── Sub-Task 8 (User Dashboard)
                            └── Sub-Task 9 (Integration Testing)
```
