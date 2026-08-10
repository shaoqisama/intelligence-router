# Intelligence Router MVP 0.2.0 — 评测与验证说明

## 1. 如何解读结果

本仓库包含三类验证，作用不同：

1. **自动化测试**：验证分类、候选过滤、Direct / Cascade / Fusion 规划、API、provider payload、缓存、成本核算与 Landing Page 静态资源。
2. **离线 deterministic mock benchmark**：验证策略分布、模型调用次数、token 账本、成本、升级与 exact cache 行为。
3. **Landing Page 浏览器验证**：验证实时路由预览、completion/trace 渲染、移动端布局、导航和前端错误。

这些验证都不代表真实 LLM 的答案质量，也不是生产节省承诺。真实质量、延迟、工具成功率和成本收益必须在客户任务集上，用实际 provider、实时价格和业务 reward 重新评测。

## 2. 自动化测试

执行：

```bash
pytest -q
node --check src/intelligence_router/web/app.js
python -m compileall -q src tests
```

本次结果：

```text
17 passed
JavaScript syntax: passed
Python bytecode compilation: passed
```

主要覆盖：

- 中英文任务分类、复杂度、风险和能力推断；
- capability、context、privacy、provider、budget 等硬约束；
- 简单任务 Direct、低置信度任务 Cascade、高复杂度任务 bounded Fusion；
- OpenAI Responses、Anthropic Messages、Gemini `generateContent` 与 OpenAI-compatible payload 转换；
- exact cache、成本与 token 核算、反馈和 API 行为；
- 首页、Playground alias、CSS、JavaScript、favicon 与 robots 路由。

## 3. 离线 mock benchmark

执行：

```bash
python scripts/demo_benchmark.py
```

脚本使用临时 SQLite 和三个 deterministic mock 模型，不需要云端 Key。完整逐条结果位于 `MVP_VALIDATION.md` 和 `benchmark_results.json`。

### 3.1 汇总

| 指标 | 结果 |
|---|---:|
| Cases | 9 |
| Direct / Cascade / Fusion | 6 / 2 / 1 |
| Provider calls | 12 |
| Provider tokens | 1,631 |
| Exact-cache hits | 1 |
| 模拟实际成本 | $0.00255615 |
| Like-for-like 旗舰反事实 | $0.00305600 |
| 模拟成本差 | 下降 16.36% |

### 3.2 已验证的机制

- 简单摘要、分类、抽取和翻译只运行一个低成本模型；
- 更复杂或高风险任务进入验证型 Cascade；
- 深度、多视角任务进入最多两个 reference workers 加一个 aggregator 的 bounded Fusion；
- exact cache hit 返回 0 provider calls 和 0 provider tokens；
- 隐藏的 judge/reference 调用均进入 token 与成本总账；
- Fusion 可以产生负节省，系统不会把额外质量计算伪装成成本优化。

### 3.3 正确解读 16.36%

该数值来自 deterministic mock 输出和模拟价格，仅说明当前实现的核算与策略路径可复现。它不测真实回答质量，也不预测客户生产环境的节省比例。生产评测需要至少比较：

- Router 与固定旗舰模型的任务成功率；
- Router 与固定经济模型的质量差；
- 端到端 P50 / P95 延迟；
- 工具调用、JSON Schema、代码执行等可验证成功率；
- 每个成功任务的成本，而不是单纯每次请求成本。

## 4. Landing Page 验证

客户页面由同一 FastAPI 服务提供：

```text
GET /            产品 Landing Page
GET /playground  同页面 Playground alias
GET /assets/*    打包后的 CSS / JS / favicon
```

本次浏览器检查包括：

| 检查 | 结果 |
|---|---:|
| Route preview 按真实 API schema 渲染 | Passed |
| Completion、成本、token 与 trace 渲染 | Passed |
| Console errors / uncaught page errors | 0 / 0 |
| 390 px 移动端 document width | 390 px |
| 390 px 移动端横向溢出 | None |
| 移动导航开合 | Passed |
| Wheel 外部安装后加载首页和资产 | Passed |

浏览器交互使用与实际接口一致的 API-shaped fixtures，避免调用云端模型；FastAPI 与 deterministic mock provider 的端到端行为由自动化测试和单独 API smoke test 覆盖。更多细节见 `LANDING_PAGE_VALIDATION.md`。

## 5. 生产评测建议

生产化前应建立代表性客户任务集和明确 reward：任务完成、事实正确、格式合规、工具成功、人工采纳、成本和延迟。先进行 shadow routing，再做 canary / A/B；按任务类型校准质量门槛，并持续记录模型版本、价格快照、策略版本和数据边界。只有在质量不降或业务 reward 提升的前提下，成本下降才算有效节省。
