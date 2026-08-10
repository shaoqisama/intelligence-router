# Intelligence Router MVP 0.2.0 — Release Notes

**Release date:** 2026-08-10

## What changed in 0.2.0

- Added a responsive customer-facing landing page at `GET /` and `GET /playground`.
- Added a live router playground connected to the real `/v1/route/preview` and `/v1/chat/completions` endpoints.
- Added task presets and controls for strategy, cost tier, request budget, quality target, tenant ID, and optional bearer token.
- Added explainable result rendering for task type, complexity, risk, selected strategy, primary model, planned path, candidates, reasons, routed cost, flagship counterfactual, and completion token usage.
- Added a service-health indicator, a developer quick-start example, governance comparison, execution-mode diagrams, responsive layouts, keyboard focus states, and reduced-motion support.
- Bundled all landing-page assets inside the Python package; no CDN, external font, or frontend framework is required at runtime.
- Added API tests for the homepage, playground alias, CSS, and JavaScript assets.
- Validated the interactive preview and completion states in a headless Chromium smoke test, including mobile layout with no horizontal overflow.
- The full automated Python suite now reports `17 passed`.
- Updated the application and Python package version to `0.2.0`.

## Core router capabilities retained

- OpenAI-compatible FastAPI gateway.
- Direct, confidence-gated Cascade, and budget-bounded Fusion execution.
- Native adapters for OpenAI Responses, Anthropic Messages, and Gemini `generateContent`.
- OpenAI-compatible adapter for DeepSeek, OpenRouter fixed-model routes, LiteLLM, vLLM, and similar endpoints.
- Capability/context/privacy/provider policy filtering, cost-quality tiers, fallback, cooldown, and session stickiness.
- Exact cache, SQLite traces and accounting, route preview, feedback ingestion, and online quality adjustment.
- Deterministic offline mock providers, Docker configuration, OpenAPI schema, examples, tests, and benchmark script.

## Validation boundaries

- The built-in benchmark uses deterministic mock models; it validates routing behavior, accounting, cache, fallback, and escalation—not real-model answer quality.
- The live landing-page demo reflects whichever models are available in the running registry. With no cloud keys, it uses the bundled deterministic mock pool.
- No cloud-provider calls are required to run or test the website.
- Published prices and model lifecycle data remain a 2026-08-09 snapshot and must be revalidated or automatically synchronized before production use.
