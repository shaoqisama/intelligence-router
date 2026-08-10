# Intelligence Router 路线图

## 产品北极星

```text
在明确的质量、风险、隐私、区域和延迟约束下，持续降低 cost per successful task。
```

不要以“平均 token 降幅”作为唯一目标。Router 省下的 token 若换来更多重试、人工返工或错误执行，就不是真正节省。

## Phase 0 — Runnable MVP（当前完成）

已具备：

- OpenAI 风格 API；
- model/service catalog；
- 任务画像与硬约束；
- 可解释候选打分；
- Direct / Cascade / Fusion；
- budget guard、cache、trace、metrics、feedback；
- acting-model tool trust boundary；
- OpenAI、Anthropic、Gemini、OpenRouter adapters；
- mock demo 与 23 个测试。

出口：代码可复现运行，路由决策可解释，关键安全语义有测试。

## Phase 1 — Provider Productionization

工作：

- 为选定的 3–5 个真实模型填充版本化 catalog；
- 自动同步价格、上下文、能力与下线状态；
- 文本、vision、structured output、function calling、native tools contract tests；
- 准确处理 cache tokens、native tool fees、batch/priority tiers；
- timeout、retry、backoff、circuit breaker、health score；
- secrets manager、tenant credentials 与 provider quotas；
- SSE streaming；
- OpenTelemetry trace 与 cost ledger；
- `no_store`、ZDR、region 与 retention policy 验证。

出口：所有启用 provider 的请求与账单可对齐；故障与政策行为可预测。

## Phase 2 — Evaluation & Calibrated Cascade

工作：

- 建立匿名化真实任务 replay set；
- task-specific deterministic graders；
- 人工 pairwise preference 与 downstream outcome；
- 校准 `P(success | task, model, service)`；
- 训练 escalation classifier；
- 按 task/tenant/language/risk 估计置信区间；
- 比较 always-premium、cheap-direct、cascade、fixed-fusion 与 auto；
- 建立 Pareto dashboard 和 canary rollout。

出口：在真实任务上以统计证据证明 cost per success 改善，且关键质量与风险门不退化。

## Phase 3 — Native Service Planner

工作：

- 把 search/file/code/computer/MCP 从 model 属性升级为独立 plan node；
- evidence store：来源、时间、hash、权限、引用与保留；
- service-specific caching 与复用；
- 工具权限、approval、sandbox、参数 schema 与 injection 防护；
- 选择“哪个模型 + 哪个服务 + 何时验证”，而非只选模型；
- 对 agent tool loop 实现有意义状态变化后的周期性 advisor refresh。

出口：Native service 的增量价值、费用与证据链可单独度量，advisor 文本和真实执行事件不会混淆。

## Phase 4 — Learning Router / Contextual Bandit

工作：

- 由任务、上下文形状、tenant、历史表现、实时健康预测成功率；
- 学习 Direct/Cascade/Fusion 与 panel size；
- 在硬约束内做低风险探索；
- inverse propensity / doubly robust 评估；
- 防止反馈偏差、幸存者偏差和 provider drift；
- 自动回滚、版本化 policy、离线 replay gate。

出口：学习型 policy 在 shadow/canary 中稳定优于手工规则，并保持可解释的约束证明。

## Phase 5 — Dynamic Agentic Scaffolds

工作：

- 由 orchestrator 生成有限、类型安全的执行 DAG；
- 动态选择 worker、角色、工具、验证器、共享记忆和停止条件；
- scaffold 模板 + constrained generation，而非任意自然语言流程；
- 用 end-to-end outcome、工具轨迹和环境反馈训练；
- 针对复杂 coding/research/planning 开启，低价值任务仍走 Direct；
- workflow cost envelope 与最大步数硬约束。

出口：在复杂任务上动态 scaffold 相比固定 Fusion 有可测量的质量/成本边际收益，并能在错误时安全降级。

## Phase 6 — Enterprise Intelligence Control Plane

工作：

- tenant policy、产品 tier、部门 budget、项目配额；
- region/data residency、合同与模型许可目录；
- 模型/服务 marketplace 与内部模型；
- prompt/tool/evidence governance；
- 审计、成本归因、chargeback、SLA；
- 用户可解释的“为什么使用此模型/工具/预算”；
- policy-as-code 与审批工作流。

出口：Router 从技术组件变成企业 AI 资源调度与治理平面。

## 最优先的真实数据闭环

下一步最有价值的输入不是更多启发式规则，而是：

- 3–5 个计划实际使用的模型与 Native AI Service；
- 当前合同价格、数据政策、区域和 rate limit；
- 200–1000 条代表性任务日志；
- 至少一个可验证 outcome 或人工 preference；
- 当前基线方案的真实 billed usage 与延迟。

这些数据可以直接用于 offline replay，校准 model card 的 task score、质量容差、Cascade gate 和 Fusion 触发阈值。
