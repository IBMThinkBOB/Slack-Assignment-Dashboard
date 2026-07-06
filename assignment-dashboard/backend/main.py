import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import slack, excel, projects, resources, assignments, extract, simulate

app = FastAPI(
    title="Assignment Visibility & Resource Alignment Platform",
    version="1.0.0",
    description="Phase 1 MVP — Slack + Excel → Unified Project Dashboard",
)

# ALLOWED_ORIGINS can be a comma-separated list of origins set via env var.
# Falls back to localhost for local development.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract.router, tags=["NLP"])
app.include_router(simulate.router, prefix="/slack", tags=["Slack"])
app.include_router(slack.router, prefix="/slack", tags=["Slack"])
app.include_router(excel.router, prefix="/excel", tags=["Excel"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(resources.router, prefix="/resources", tags=["Resources"])
app.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "1.0.0"}
