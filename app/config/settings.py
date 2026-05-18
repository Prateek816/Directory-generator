"""
app/config/settings.py
Application-wide configuration loaded from environment variables.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central settings object — loaded once and cached."""

    # Groq / LLM
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    model_name: str = Field("llama-3.3-70b-versatile", alias="MODEL_NAME")
    max_tokens: int = Field(2048, alias="MAX_TOKENS")
    temperature: float = Field(0.3, alias="TEMPERATURE")
    request_timeout: int = Field(30, alias="REQUEST_TIMEOUT")
    max_retries: int = Field(3, alias="MAX_RETRIES")

    # Feature flags
    enable_caching: bool = Field(True, alias="ENABLE_CACHING")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    @field_validator("temperature")
    @classmethod
    def clamp_temperature(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    model_config = {"env_file": ".env", "populate_by_name": True}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance."""
    return Settings()  # type: ignore[call-arg]