# Assignment Visibility & Resource Alignment Platform
## Phase 1 MVP

---

## Overview

A centralized operations dashboard that consolidates project and assignment information from **Slack** and **Excel** into a single view — giving managers complete visibility into who is working on what, what skills are required, and whether projects are properly staffed.

---

## Monorepo Structure

```
assignment-dashboard/
├── backend/          Python + FastAPI
├── frontend/         Next.js + TypeScript + MUI + AG Grid
├── docs/             Setup guides and data format docs
├── sample-data/      Sample Excel and Slack message files
├── docker-compose.yml
└── README.md
```

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose (for PostgreSQL)
- A Slack app with Events API enabled
- An OpenAI-compatible LLM provider

---

## Environment Variables

Copy the root `.env` and fill in the values:

```env
# ─── Database ────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/assignment_db

# ─── LLM — OpenAI-compatible provider (no vendor lock-in) ─
# BOB_API_KEY in .env is used as LLM_API_KEY
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=          # set to the value of BOB_API_KEY
LLM_MODEL=gpt-4o

# ─── Slack ───────────────────────────────────────────────
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
```

> **Note:** If your `.env` already has `BOB_API_KEY`, the backend also accepts that
> key name directly — see `backend/config.py` for the alias mapping.

---

## Local Development

### 1. Start PostgreSQL

```bash
docker compose up postgres -d
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local    # edit NEXT_PUBLIC_API_URL if needed
npm run dev
```

Dashboard available at: http://localhost:3000

---

## Running with Docker Compose (all services)

```bash
docker compose up --build
```

---

## Required Slack OAuth Scopes

| Scope | Purpose |
|---|---|
| `channels:history` | Read messages from public channels |
| `channels:read` | List channels |
| `groups:history` | Read messages from private channels |
| `users:read` | Look up user profiles |
| `chat:write` | Post messages (future use) |

See [`docs/slack-setup.md`](docs/slack-setup.md) for full Slack app setup instructions.

---

## Excel Format

See [`docs/excel-format.md`](docs/excel-format.md) for the expected column schema.
Sample file: [`sample-data/sample-projects.xlsx`](sample-data/sample-projects.xlsx)

---

## Demo Walkthrough

1. Start all services (`docker compose up`)
2. Upload `sample-data/sample-projects.xlsx` via `POST /excel/upload` or the dashboard UI
3. Post a message in your connected Slack channel, e.g.:
   ```
   Need Storage Scale deployment support for ABC Corp starting next month.
   ```
4. The backend captures the event, runs NLP extraction, and creates a project record
5. Open the dashboard at http://localhost:3000 — the new project appears in the AG Grid
6. Click the project row → Project Detail panel opens
7. Click **Assign Resource** → pick a resource and role → confirm
8. Switch Role Toggle to **User** → navigate to **My Assignments** → see the assignment
9. Update progress using the Update Progress button

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Phase Roadmap

| Phase | Scope |
|---|---|
| **Phase 1** (current) | Slack intake, Excel upload, Project Repository, Assignment Dashboard |
| Phase 2 | Skills Inventory, Resource Recommendations, Readiness Dashboard |
| Phase 3 | Salesforce Integration, Microsoft Graph, BP&E Dashboard |
| Phase 4 | AI Workflow Builder, Admin Slack Alerts, Advanced Analytics |
