# Landing Page Validation

The customer-facing website is bundled with Intelligence Router `0.2.0` and served by the same FastAPI process as the routing API.

## Delivered routes

| Route | Purpose |
|---|---|
| `GET /` | Responsive product landing page |
| `GET /playground` | Landing-page alias with the same live playground |
| `GET /assets/styles.css` | Bundled responsive design system |
| `GET /assets/app.js` | Playground, health, trace, and interaction logic |
| `GET /assets/favicon.svg` | Product favicon |
| `GET /robots.txt` | Basic crawler policy |

## Live behavior

- The service-status indicator reads the running instance's `/healthz` endpoint.
- Runtime request and cache counters read `/v1/stats` when that endpoint is accessible.
- `Preview route` calls `/v1/route/preview`; it uses the real classifier and policy planner without invoking an LLM.
- `Run request` calls `/v1/chat/completions` and renders the selected model, answer, actual cost, baseline delta, token usage, cache state, and provider-call trace.
- The playground accepts strategy, cost tier, budget, quality target, data boundary, tenant ID, and an optional bearer token.
- The bearer token remains in the current browser tab and is sent only to the same-origin deployment.
- All HTML, CSS, JavaScript, and favicon assets are bundled locally; the page has no CDN, web-font, or frontend-framework runtime dependency.

## Validation performed

| Check | Result |
|---|---:|
| Python test suite | `17 passed` |
| JavaScript syntax (`node --check`) | Passed |
| Python bytecode compilation | Passed |
| Homepage, playground alias, CSS, JavaScript, favicon, and robots routes | Passed |
| Browser route-preview render against the real FastAPI endpoint | Passed |
| Browser completion and provider trace against the bundled mock provider | Passed |
| Browser console errors / uncaught page errors | `0 / 0` |
| Desktop horizontal overflow at 1440 px | None |
| Mobile horizontal overflow at 390 px | None |
| Mobile navigation toggle | Passed |
| Native budget-field validity and step behavior | Passed |
| Wheel contains all HTML/CSS/JS/favicon assets | Passed |
| Wheel installed outside the source tree and served the landing page | Passed |

The browser smoke test uses the deterministic bundled mock pool, so it exercises the real API and UI without cloud-provider credentials or model spend. It covered `/healthz`, `/v1/stats`, `/v1/route/preview`, `/v1/chat/completions`, and the packaged favicon.

## Browser captures

Browser-validation screenshots are generated locally and excluded from source control. They are optional release artifacts; the landing page and playground themselves are fully bundled under `src/intelligence_router/web/`.
