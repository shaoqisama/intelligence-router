from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ModelPricing(BaseModel):
    input_per_million: float = Field(ge=0)
    output_per_million: float = Field(ge=0)
    cached_input_per_million: float | None = Field(default=None, ge=0)


class ModelSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    provider: str
    adapter: Literal[
        "mock",
        "openai_responses",
        "anthropic_messages",
        "gemini_generate_content",
        "openai_compatible",
    ]
    provider_model: str
    enabled: bool = True
    api_key_env: str | None = None
    base_url: str | None = None
    base_url_env: str | None = None
    extra_headers: dict[str, str] = Field(default_factory=dict)

    pricing: ModelPricing
    context_window: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    expected_latency_ms: int = Field(default=2000, gt=0)
    quality: dict[str, float] = Field(default_factory=dict)
    capabilities: set[str] = Field(default_factory=lambda: {"text"})
    data_boundary: Literal["external", "regional", "local"] = "external"
    tags: set[str] = Field(default_factory=set)
    mock_profile: str | None = None

    def quality_for(self, task_type: str) -> float:
        return float(self.quality.get(task_type, self.quality.get("general", 0.5)))

    def effective_base_url(self) -> str | None:
        if self.base_url_env and os.getenv(self.base_url_env):
            return os.environ[self.base_url_env].rstrip("/")
        return self.base_url.rstrip("/") if self.base_url else None

    def api_key(self) -> str | None:
        if not self.api_key_env:
            return None
        value = os.getenv(self.api_key_env)
        return value.strip() if value else None

    def availability_reason(self) -> str | None:
        if not self.enabled:
            return "disabled"
        if self.adapter == "mock":
            return None
        if self.api_key_env and not self.api_key():
            return f"missing environment variable {self.api_key_env}"
        if self.adapter == "openai_compatible" and not self.effective_base_url():
            return "missing base_url"
        return None

    @property
    def available(self) -> bool:
        return self.availability_reason() is None


class ModelRegistry:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.version: str = "unknown"
        self._models: dict[str, ModelSpec] = {}
        self.fingerprint: str = ""
        self.reload()

    def reload(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Model registry not found: {self.path}")
        raw_text = self.path.read_text(encoding="utf-8")
        payload: dict[str, Any] = yaml.safe_load(raw_text) or {}
        self.version = str(payload.get("version", "unknown"))
        models = [ModelSpec.model_validate(item) for item in payload.get("models", [])]
        duplicates = {m.id for m in models if sum(x.id == m.id for x in models) > 1}
        if duplicates:
            raise ValueError(f"Duplicate model ids: {sorted(duplicates)}")
        self._models = {m.id: m for m in models}
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        self.fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    def get(self, model_id: str) -> ModelSpec:
        try:
            return self._models[model_id]
        except KeyError as exc:
            raise KeyError(f"Unknown model: {model_id}") from exc

    def all(self) -> list[ModelSpec]:
        return list(self._models.values())

    def available(self) -> list[ModelSpec]:
        return [m for m in self._models.values() if m.available]

    def unavailable(self) -> list[tuple[ModelSpec, str]]:
        result: list[tuple[ModelSpec, str]] = []
        for model in self._models.values():
            reason = model.availability_reason()
            if reason:
                result.append((model, reason))
        return result

    def public_model_list(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for model in self.all():
            items.append(
                {
                    "id": model.id,
                    "object": "model",
                    "owned_by": model.provider,
                    "available": model.available,
                    "unavailable_reason": model.availability_reason(),
                    "capabilities": sorted(model.capabilities),
                    "context_window": model.context_window,
                    "max_output_tokens": model.max_output_tokens,
                    "data_boundary": model.data_boundary,
                }
            )
        return items
