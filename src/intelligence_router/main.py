from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

from .engine import IntelligenceRouterEngine
from .planner import RoutingError
from .providers import ProviderError
from .schemas import (
    ChatCompletionRequest,
    FeedbackRequest,
    FeedbackResponse,
    RoutePreviewResponse,
)
from .settings import Settings


_bearer = HTTPBearer(auto_error=False)


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
        engine = IntelligenceRouterEngine(runtime_settings)
        app.state.engine = engine
        yield
        await engine.close()

    app = FastAPI(
        title="Intelligence Router",
        version="0.2.0",
        description=(
            "OpenAI-compatible, budget-aware routing across native LLM services with direct, "
            "cascade, and bounded fusion execution."
        ),
        lifespan=lifespan,
    )
    app.state.settings = runtime_settings

    web_dir = Path(__file__).with_name("web")
    app.mount("/assets", StaticFiles(directory=web_dir), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/playground", include_in_schema=False)
    async def landing_page() -> FileResponse:
        return FileResponse(web_dir / "index.html", media_type="text/html")

    @app.get("/robots.txt", include_in_schema=False)
    async def robots() -> PlainTextResponse:
        return PlainTextResponse("User-agent: *\nDisallow:\n")

    async def authorize(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    ) -> None:
        expected = runtime_settings.api_key
        if expected and (credentials is None or credentials.credentials != expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing bearer token",
            )

    def engine_from(request: Request) -> IntelligenceRouterEngine:
        return request.app.state.engine

    @app.exception_handler(RoutingError)
    async def routing_error_handler(_: Request, exc: RoutingError):  # type: ignore[no-untyped-def]
        return _error_response(400, exc.code, str(exc))

    @app.exception_handler(ProviderError)
    async def provider_error_handler(_: Request, exc: ProviderError):  # type: ignore[no-untyped-def]
        return _error_response(
            502,
            "provider_error",
            str(exc),
            provider=exc.provider,
            model=exc.model_id,
            retryable=exc.retryable,
        )

    @app.get("/healthz")
    async def health(request: Request) -> dict[str, Any]:
        engine = engine_from(request)
        return {
            "status": "ok",
            "registry_version": engine.registry.version,
            "registry_fingerprint": engine.registry.fingerprint,
            "models_available": len(engine.registry.available()),
            "models_total": len(engine.registry.all()),
        }

    @app.get("/v1/models", dependencies=[Depends(authorize)])
    async def models(request: Request) -> dict[str, Any]:
        engine = engine_from(request)
        aliases = [
            {
                "id": alias,
                "object": "model",
                "owned_by": "intelligence-router",
                "available": True,
            }
            for alias in (
                "intelligence-router/auto",
                "intelligence-router/fast",
                "intelligence-router/quality",
                "intelligence-router/fusion",
            )
        ]
        return {"object": "list", "data": [*aliases, *engine.registry.public_model_list()]}

    @app.post(
        "/v1/route/preview",
        response_model=RoutePreviewResponse,
        dependencies=[Depends(authorize)],
    )
    async def preview(
        payload: ChatCompletionRequest,
        request: Request,
        x_tenant_id: Annotated[str, Header(max_length=200)] = "default",
    ) -> RoutePreviewResponse:
        plan = engine_from(request).preview(payload, tenant_id=x_tenant_id)
        return RoutePreviewResponse(plan=plan)

    @app.post("/v1/chat/completions", dependencies=[Depends(authorize)])
    async def chat_completions(
        payload: ChatCompletionRequest,
        request: Request,
        x_tenant_id: Annotated[str, Header(max_length=200)] = "default",
    ) -> dict[str, Any]:
        if payload.stream:
            raise HTTPException(
                status_code=400,
                detail="Streaming is not implemented in this MVP; send stream=false",
            )
        return await engine_from(request).complete(payload, tenant_id=x_tenant_id)

    @app.post(
        "/v1/feedback",
        response_model=FeedbackResponse,
        dependencies=[Depends(authorize)],
    )
    async def feedback(payload: FeedbackRequest, request: Request) -> FeedbackResponse:
        try:
            result = engine_from(request).store.record_feedback(
                payload.trace_id, payload.score, payload.note
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return FeedbackResponse(
            accepted=True,
            trace_id=result["trace_id"],
            model_id=result["model_id"],
            task_type=result["task_type"],
            normalized_score=result["score"],
        )

    @app.get("/v1/stats", dependencies=[Depends(authorize)])
    async def stats(request: Request) -> dict[str, Any]:
        return engine_from(request).store.stats_summary()

    return app


def _error_response(status_code: int, code: str, message: str, **details: Any):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": code,
                "code": code,
                **details,
            }
        },
    )


app = create_app()


def run() -> None:
    uvicorn.run(
        "intelligence_router.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    run()
