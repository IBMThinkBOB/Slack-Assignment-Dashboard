"""Pytest configuration — shared fixtures for all backend tests."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use an in-memory SQLite DB for tests — no Postgres required
TEST_DB_URL = "sqlite:///./test.db"

os.environ.setdefault("DATABASE_URL", TEST_DB_URL)
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_MODEL", "gpt-4o")
os.environ.setdefault("SLACK_SIGNING_SECRET", "")
os.environ.setdefault("SLACK_BOT_TOKEN", "")

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate all tables before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
