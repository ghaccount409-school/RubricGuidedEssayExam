from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Together "Small & Fast" tier — used for every chat/completions call unless overridden (see together_use_env_model).
# https://docs.together.ai/docs/recommended-models
TOGETHER_CHAT_MODEL_DEFAULT = "openai/gpt-oss-20b"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    together_api_key: str = ""
    # Read from TOGETHER_MODEL in .env; only applied when together_use_env_model is True.
    together_model_from_env: str = Field(default=TOGETHER_CHAT_MODEL_DEFAULT, alias="TOGETHER_MODEL")
    # When False (default), all requests use TOGETHER_CHAT_MODEL_DEFAULT so old .env examples cannot force slow models.
    # Set TOGETHER_USE_ENV_MODEL=1 to honor TOGETHER_MODEL for custom / higher-quality models.
    together_use_env_model: bool = Field(default=False, alias="TOGETHER_USE_ENV_MODEL")
    # Official inference host (see https://docs.together.ai/docs/api-keys-authentication)
    together_base_url: str = "https://api.together.xyz/v1"
    mock_llm: bool = False

    def together_model_for_requests(self) -> str:
        """Model id for Together chat/completions — single source of truth for the app."""
        if self.together_use_env_model:
            m = (self.together_model_from_env or "").strip()
            return m if m else TOGETHER_CHAT_MODEL_DEFAULT
        return TOGETHER_CHAT_MODEL_DEFAULT

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
