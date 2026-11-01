from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "CIT Scheduler API"
    database_url: str = "sqlite:///./cit_scheduler.db"
    secret_key: str = "change-me"
    frontend_origin: str = "http://localhost:5173"
    llm_provider: str = "openai"  # "anthropic" or "openai" (OpenAI-compatible: Gemini, Groq, OpenAI)
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def dataset_path(self) -> Path:
        return BACKEND_DIR / "data" / "cit_public.json"


settings = Settings()
