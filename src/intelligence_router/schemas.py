from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TaskType = Literal[
    "general",
    "classification",
    "extraction",
    "summarization",
    "translation",
    "coding",
    "math",
    "reasoning",
    "research",
    "creative",
    "customer_support",
    "agentic",
]

Strategy = Literal["auto", "direct", "cascade", "fusion"]
CostTier = Literal["low", "medium", "high", "max"]
VerificationMode = Literal["auto", "none", "heuristic", "judge"]
DataBoundary = Literal["any", "regional_or_local", "local_only"]
ReasoningEffort = Literal["none", "low", "medium", "high", "xhigh", "max"]


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: Literal["system", "developer", "user", "assistant", "tool"]
    content: Any
    name: str | None = None
    tool_call_id: str | None = None

    def text(self) -> str:
        if isinstance(self.content, str):
            return self.content
        if isinstance(self.content, list):
            chunks: list[str] = []
            for item in self.content:
                if isinstance(item, str):
                    chunks.append(item)
                elif isinstance(item, dict):
                    if isinstance(item.get("text"), str):
                        chunks.append(item["text"])
                    elif item.get("type") in {"image", "image_url", "input_image"}:
                        chunks.append("[image]")
                    else:
                        chunks.append(json.dumps(item, ensure_ascii=False, sort_keys=True))
            return "\n".join(chunks)
        if self.content is None:
            return ""
        return json.dumps(self.content, ensure_ascii=False, sort_keys=True, default=str)


class RouterOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: Strategy = "auto"
    cost_tier: CostTier = "medium"
    max_cost_usd: float | None = Field(default=None, gt=0)
    quality_target: float = Field(default=0.80, ge=0, le=1)
    latency_slo_ms: int = Field(default=15_000, ge=100)
    risk: Literal["auto", "low", "medium", "high"] = "auto"

    allowed_models: list[str] = Field(default_factory=list)
    excluded_models: list[str] = Field(default_factory=list)
    allowed_providers: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    data_boundary: DataBoundary = "any"

    cache: bool = True
    session_id: str | None = Field(default=None, max_length=256)
    session_stickiness: bool = True
    explain: bool = True

    verification: VerificationMode = "auto"
    max_panel_models: int = Field(default=2, ge=1, le=2)
    reasoning_effort: ReasoningEffort | None = None
    native_tools: list[str] = Field(default_factory=list)


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = "intelligence-router/auto"
    messages: list[ChatMessage] = Field(min_length=1)
    max_tokens: int | None = Field(default=None, ge=1)
    max_completion_tokens: int | None = Field(default=None, ge=1)
    temperature: float | None = Field(default=None, ge=0, le=2)
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    tool_choice: Any | None = None
    response_format: dict[str, Any] | None = None
    router: RouterOptions = Field(default_factory=RouterOptions)

    @model_validator(mode="after")
    def validate_output_token_fields(self) -> "ChatCompletionRequest":
        if self.max_tokens is not None and self.max_completion_tokens is not None:
            raise ValueError("Use either max_tokens or max_completion_tokens, not both")
        return self

    def requested_output_tokens(self, default: int) -> int:
        return self.max_completion_tokens or self.max_tokens or default

    def prompt_text(self) -> str:
        return "\n".join(m.text() for m in self.messages if m.role in {"user", "tool"})


class TaskProfile(BaseModel):
    task_type: TaskType
    complexity: float = Field(ge=0, le=1)
    risk: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    required_capabilities: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)


class CandidateScore(BaseModel):
    model_id: str
    provider: str
    quality: float
    reliability: float
    estimated_cost_usd: float
    estimated_latency_ms: float
    utility: float
    affordable_output_tokens: int
    reasons: list[str] = Field(default_factory=list)


class RoutePlan(BaseModel):
    strategy: Literal["direct", "cascade", "fusion"]
    task: TaskProfile
    primary_model: str
    fallback_models: list[str] = Field(default_factory=list)
    panel_models: list[str] = Field(default_factory=list)
    aggregator_model: str | None = None
    judge_model: str | None = None
    output_caps: dict[str, int] = Field(default_factory=dict)
    estimated_cost_usd: float
    baseline_cost_usd: float
    budget_usd: float
    candidates: list[CandidateScore] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    session_pinned: bool = False


class RoutePreviewResponse(BaseModel):
    object: Literal["intelligence_router.route_plan"] = "intelligence_router.route_plan"
    plan: RoutePlan


@dataclass(slots=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, other: "TokenUsage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cached_input_tokens += other.cached_input_tokens
        self.reasoning_tokens += other.reasoning_tokens

    def as_openai(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.input_tokens,
            "completion_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(slots=True)
class ProviderResponse:
    text: str
    provider: str
    model_id: str
    raw_model: str
    usage: TokenUsage
    latency_ms: float
    finish_reason: str = "stop"
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


class ProviderCallTrace(BaseModel):
    stage: str
    model_id: str
    provider: str
    success: bool
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    cost_usd: float = 0
    error: str | None = None


class RouterTrace(BaseModel):
    trace_id: str
    strategy: str
    task_type: str
    complexity: float
    risk: float
    selected_model: str
    calls: list[ProviderCallTrace] = Field(default_factory=list)
    cache_hit: bool = False
    session_pinned: bool = False
    escalated: bool = False
    escalation_reason: str | None = None
    estimated_cost_usd: float = 0
    actual_cost_usd: float = 0
    baseline_cost_usd: float = 0
    estimated_savings_usd: float = 0
    estimated_savings_pct: float = 0
    budget_usd: float = 0
    budget_overrun: bool = False
    reasons: list[str] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    trace_id: str
    score: float = Field(ge=0, le=1)
    note: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    accepted: bool
    trace_id: str
    model_id: str
    task_type: str
    normalized_score: float


class ErrorResponse(BaseModel):
    error: dict[str, Any]
