from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    together_api_key: str = ""
    together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    # Official inference host (see https://docs.together.ai/docs/api-keys-authentication)
    together_base_url: str = "https://api.together.xyz/v1"
    mock_llm: bool = False

    @field_validator("together_api_key", mode="before")
    @classmethod
    def _normalize_api_key(cls, v):
        if v is None:
            return ""
        s = str(v).strip().strip('"').strip("'")
        return s

    @field_validator("mock_llm", mode="before")
    @classmethod
    def _coerce_mock(cls, v):
        if isinstance(v, str):
            return v.strip().lower() in ("1", "true", "yes", "on")
        return bool(v)
    database_url: str = "sqlite:///./exam_system.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
