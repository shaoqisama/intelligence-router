from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables prefixed with ``IR_``."""

    model_config = SettingsConfigDict(
        env_prefix="IR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "Intelligence Router"
    api_key: str | None = None
    config_path: Path = Path("config/models.yaml")
    db_path: Path = Path(".data/router.db")

    default_max_cost_usd: float = Field(default=0.05, gt=0)
    default_max_output_tokens: int = Field(default=800, ge=32, le=128_000)
    cache_ttl_sec: int = Field(default=900, ge=0)
    session_ttl_sec: int = Field(default=3600, ge=0)
    request_timeout_sec: float = Field(default=60.0, gt=0)
    max_retries: int = Field(default=0, ge=0, le=3)
    cache_enabled: bool = True
    log_raw_prompts: bool = False

    # Router behavior.
    minimum_completion_tokens: int = Field(default=64, ge=16, le=2048)
    panel_output_tokens: int = Field(default=320, ge=64, le=4096)
    judge_output_tokens: int = Field(default=96, ge=32, le=512)
    max_fallbacks: int = Field(default=2, ge=0, le=5)
    model_failure_cooldown_sec: int = Field(default=60, ge=0)

    def ensure_runtime_dirs(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def resolved_config_path(self) -> Path:
        """Use the source-tree registry, or the packaged fallback after wheel install."""

        if self.config_path.exists():
            return self.config_path
        if self.config_path == Path("config/models.yaml"):
            packaged = Path(__file__).with_name("default_models.yaml")
            if packaged.exists():
                return packaged
        return self.config_path
