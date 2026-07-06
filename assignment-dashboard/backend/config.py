import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve env file relative to this file's location so it works regardless
# of the working directory the server is launched from.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ENV_FILE = os.path.join(_HERE, "..", "..", ".env")  # workspace-root .env


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5433/assignment_db"

    # LLM (OpenAI-compatible provider abstraction)
    # Defaults to local Ollama. Override via LLM_BASE_URL / LLM_API_KEY / LLM_MODEL env vars.
    # BOB_API_KEY in the root .env maps to llm_api_key via the Field alias (cloud fallback).
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = Field(default="ollama", alias="BOB_API_KEY")
    llm_model: str = "qwen:latest"

    # Slack
    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
