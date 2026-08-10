# MVP Offline Validation

> This is a deterministic mock-provider validation of routing behavior, accounting, cache, and escalation. It is **not** a benchmark of real model quality.

## Aggregate

- Cases: 9
- Direct / Cascade / Fusion: 6 / 2 / 1
- Provider calls: 12
- Provider tokens: 1631
- Cache hits: 1
- Actual simulated cost: $0.00255615
- Like-for-like flagship counterfactual: $0.00305600
- Cost delta: 16.36%

A negative per-row saving is valid: bounded Fusion intentionally spends extra compute when the policy judges that multi-perspective quality may be worth it.

## Cases

| Case | Strategy | Final model | Calls | Tokens | Cache | Escalated | Cost | Baseline | Delta |
|---|---|---|---:|---:|---|---|---:|---:|---:|
| summary | direct | mock/fast | 1 | 60 | no | no | $0.00000445 | $0.00029400 | 98.49% |
| classification | direct | mock/fast | 1 | 55 | no | no | $0.00000405 | $0.00026600 | 98.48% |
| extraction-json | direct | mock/fast | 1 | 37 | no | no | $0.00000235 | $0.00013400 | 98.25% |
| translation | direct | mock/fast | 1 | 49 | no | no | $0.00000365 | $0.00024200 | 98.49% |
| coding-review | cascade | mock/balanced | 2 | 335 | no | no | $0.00006570 | $0.00053400 | 87.70% |
| high-risk-review | cascade | mock/balanced | 2 | 312 | no | no | $0.00005915 | $0.00047400 | 87.52% |
| deep-research-fusion | fusion | mock/smart | 3 | 745 | no | no | $0.00241400 | $0.00074400 | -224.46% |
| cache-first | direct | mock/fast | 1 | 38 | no | no | $0.00000280 | $0.00018400 | 98.48% |
| cache-hit | direct | mock/fast | 0 | 0 | yes | no | $0.00000000 | $0.00018400 | 100.00% |

## Assertions demonstrated

- Simple workloads take a one-call direct path.
- More complex or high-risk workloads use verification/cascade.
- Deep multi-perspective work uses a two-reference bounded Fusion path.
- Exact cache hits return with zero provider calls and zero provider tokens.
- Every row reports actual simulated cost, a like-for-like flagship counterfactual, and whether the budget was exceeded.
