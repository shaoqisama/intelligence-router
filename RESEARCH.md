# Intelligence Router 深度研究与产品结论

**研究日期：2026-08-09**

## 一句话结论

最值得做的不是“OpenRouter + MoA 的又一个聚合网关”，而是一个 **以单模型为默认、以条件升级为核心、以多模型融合为稀缺预算动作、以用户反馈闭环为护城河** 的企业 Intelligence Router。

它的价值函数应是：

\[
\max_{route} \; \mathbb{E}[Quality] - \lambda_c Cost - \lambda_l Latency - \lambda_r Risk
\]

约束包括：模型能力、上下文窗口、数据驻留、工具支持、租户预算、可用性和 SLA。关键不是“找到全局最强模型”，而是“对当前任务找到满足质量门槛的最小充分计算量”。

## 1. 三个参照物分别教会我们什么

### Sakana Fugu：把编排隐藏在单模型接口之后

Fugu 把多代理系统暴露成单一模型接口，并按请求动态决定 worker、角色、组合、验证与最终综合。其低延迟版本倾向每次选择一个 worker；Fugu-Ultra 才为困难任务构造更深的多代理工作流。其轻量 selection head 直接在隐藏状态上做决策，避免路由器自己长篇 autoregressive 生成。

**可继承：**

- 对客户保持一个稳定模型/API 抽象。
- 编排必须 query-adaptive，而非固定 DAG。
- 日常流量以单 worker 为主，Ultra 模式只面向困难任务。
- 模型池、供应商、隐私与合规约束必须是配置，而不是重新训练的前提。

**MVP 的现实化取舍：** 暂不训练隐藏状态路由头，先用零 token 启发式分类 + 可解释评分；积累私有任务反馈后再训练 learned router。

### Hermes Mixture of Agents：参考模型是私有上下文，aggregator 才是执行者

Hermes 把 MoA 做成 virtual provider。参考模型先运行并向 aggregator 提供分析；aggregator 是真正写 assistant response、发出 tool calls 并继续 agent loop 的 acting model。

**可继承：**

- reference worker 不持有工具权限，降低成本和攻击面。
- reference 输出不直接暴露给用户，而作为不可信私有上下文。
- 最终 aggregator 保留完整的工具调用、会话和格式责任。

**MVP 的强化：** reference worker 不接收调用方 system/developer prompt，既减少 token，也降低敏感 system prompt 泄露给多个供应商的风险。

### OpenRouter Auto + Fusion：统一接入、约束路由、成本/质量旋钮、按需多视角

Auto Router 根据任务类型、复杂度与模型能力路由，并支持 allow/exclude 与成本—质量控制。Fusion 让模型在单模型不足时调用并行 panel，由 analyst 比较共识、矛盾、缺口，再让最终模型写答案；官方也明确指出短小战术问题不应使用 Fusion。

**可继承：**

- OpenAI-compatible 单入口和 provider fallback。
- 模型 allow/exclude、会话粘性和成本档位。
- Fusion 只用于 research、expert critique、多视角和高错误成本任务。

**MVP 的节流改造：** 将 analyst 与 final writer 合并成一个 aggregator，少一次付费模型调用；panel 默认上限为 2。

## 2. 学术研究给出的反直觉提醒

### 级联通常比“全员开会”更符合成本目标

FrugalGPT 将 prompt adaptation、近似和 LLM cascade 作为核心节流方法，其实验在特定设置下报告了在匹配最佳单模型性能时最高 98% 的成本下降。AutoMix 采用小模型作答、自验证、置信度驱动升级，在其五模型/五数据集实验中以可比性能降低超过 50% 的计算成本。

产品含义：先让低成本模型尝试，只有“失败概率 × 失败损失”超过升级成本时才升级。

### 异构模型越多，不一定越好

Self-MoA 研究发现，只对顶级模型做多次独立采样并聚合，在许多场景优于混入多个不同模型；核心原因是聚合对输入草稿质量敏感，弱模型会拉低平均质量。

产品含义：多样性是手段，不是 KPI。Fusion panel 应先设质量带，再追求供应商/思路多样性；模型池不足时宁可强模型 self-consistency，也不要为了“凑齐三家”引入明显弱模型。

### 复杂 router 未必稳定赢过简单 baseline

LLMRouterBench 在 40 万以上样本、21 个数据集、33 个模型和 10 种路由 baseline 上统一评估，发现许多方法表现接近，一些复杂或商业 router 未能稳定超过简单 baseline；更大的 ensemble 收益递减，仔细选择模型池更重要。

产品含义：MVP 首先要有可解释 baseline、严格 eval 和可靠数据，而不是先堆复杂神经路由器。真正护城河来自企业私有任务分布、反馈、工具结果与端到端成功率。

## 3. “节省 token”必须拆成四件不同的事

1. **减少供应商调用次数**：Direct、条件 Cascade、禁止默认 MoA。
2. **减少每次输入 token**：system prompt 去重、reference worker 不携带工具/schema、上下文压缩、RAG trimming。
3. **减少输出/推理 token**：阶段化 `max_output_tokens`、低 effort verifier、短 panel draft。
4. **减少付费 token**：exact/semantic cache、供应商 prefix cache、session stickiness。

只把任务从旗舰模型切到便宜模型，token 数可能完全相同，只是单价下降。因此产品面板应同时报告：

- provider input/output/cached/reasoning tokens
- 美元成本
- 调用数和升级率
- cache hit rate
- 反事实旗舰成本
- 质量/任务成功率

## 4. 建议的 Progressive Intelligence 状态机

```text
CACHE_HIT
  └── return

POLICY_GATE
  ├── blocked / local-only / no eligible model
  └── classify task, complexity, risk, capabilities

DIRECT
  ├── success + basic checks pass → return
  └── provider failure → cross-provider fallback

CASCADE
  ├── cheap answer
  ├── heuristic or small judge
  ├── pass → return
  └── fail → strong fallback → return

FUSION
  ├── 1–2 near-top-quality private workers in parallel
  ├── one aggregator compares + writes + may call tools
  └── aggregator failure → strongest surviving draft or direct recovery
```

默认策略阈值应该由真实数据校准，而不是长期写死。MVP 的启发式仅是启动策略。

## 5. 候选模型评分

MVP 使用：

\[
Utility(m,q) = w_q Q(m,t) + w_r R(m,t) + w_c C(m,q) + w_l L(m)
\]

- `Q`：任务类型质量先验与线上反馈的加权值。
- `R`：带 Beta prior 的调用可靠性。
- `C`：候选池内对数归一化成本分数，避免预算很大时所有模型都看起来“同样便宜”。
- `L`：相对租户 latency SLO 的时延分数。

先执行硬约束过滤，再打分：

- API Key / endpoint 可用
- context window
- tools / vision / JSON / reasoning / native tools
- data boundary
- allow/exclude/provider policy
- 近期故障 cooldown
- 最小输出 token 的预算可支付性

## 6. 为什么 MVP 不直接训练 learned router

训练路由器需要每个请求在多个模型上的**可比较 reward**。公开 benchmark 与真实企业任务差异很大；离线 leaderboard 也无法衡量工具执行、格式合规、客户采纳、响应时间和安全性。

合理路径：

1. 透明启发式上线 shadow mode。
2. 对小比例请求做随机探索或离线 replay。
3. 收集任务类型、候选模型、成本、延迟、自动 verifier、工具结果与人工反馈。
4. 训练轻量 classifier/ranker，输出候选效用或 pairwise preference。
5. 用 inverse propensity / doubly robust 等方法做 off-policy 评估。
6. 通过 canary 逐步接管启发式。

## 7. 当前模型与价格快照

`config/models.yaml` 使用 2026-08-09 官方公开信息：

- OpenAI GPT-5.6 Luna / Terra / Sol：分别面向成本、高性价比和旗舰复杂任务；通过 Responses API 保留 functions、web/file search 与 computer use。
- Anthropic Claude Haiku 4.5 / Sonnet 5 / Opus 5 / Fable 5：使用标准价格；Sonnet 5 的限时优惠未作为长期配置价格。
- Gemini 3.5 Flash-Lite / 3.6 Flash：1M 上下文、64K 最大输出。
- DeepSeek V4 Flash / Pro：配置 cache-hit 与 cache-miss 费率；官方提示近期可能提价，因此生产版必须自动同步。

这些价格不是代码常量，而是 registry 数据；生产环境应加定时同步、审批与版本回滚。

## 8. MVP 成功指标

**质量护栏：**

- 任务成功率相对“全量旗舰”下降不超过业务容忍值
- JSON/tool-call/schema 合规率
- 高风险任务漏升级率
- 客诉、人工接管与回退率

**效率指标：**

- 每成功任务成本，而非每请求成本
- P50/P95 首 token 与完成时延
- Direct 占比、Cascade 升级率、Fusion 占比
- cache hit、provider cached token 比例
- 每任务类型的 Pareto frontier

**可靠性指标：**

- provider 错误与 fallback 成功率
- 预算超限率
- 路由漂移与模型生命周期故障
- 数据边界违规为零

## 9. 商业定位

与通用 API 聚合商相比，企业 Intelligence Router 的差异化不应是“支持更多模型”，而应是：

- 企业私有任务与 reward 数据
- 原生工具/agent 能力不降级
- 可审计的预算、隐私、地区和模型策略
- 端到端任务成功率优化，而非仅文本 benchmark
- 可部署在客户 VPC/本地，云端模型与本地模型混合调度
- 可解释 trace 与反事实成本

## 10. 主要风险

- **Goodhart：** 只优化用户评分会偏向冗长、讨好式答案；必须混合客观 verifier。
- **Judge bias：** judge 与候选模型同源可能偏袒；关键任务要用执行结果或异构验证。
- **Hidden cost：** timeout、工具附加费、batch/缓存折扣会让估算偏差。
- **Data leakage：** 多模型意味着更多供应商看到数据；reference worker 必须受数据边界和最小上下文原则约束。
- **Router collapse：** 在线反馈不足时容易把流量集中到一个模型；需探索、置信区间和流量上限。
- **Model churn：** 模型名、价格、上下文和弃用快速变化；registry 必须版本化并自动验证。

## 参考资料

- Sakana AI, *Sakana Fugu Technical Report*: https://arxiv.org/html/2606.21228v1
- Nous Research, *Hermes Agent — Mixture of Agents*: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/mixture-of-agents.md
- OpenRouter, *Fusion*: https://openrouter.ai/docs/guides/features/plugins/fusion
- OpenRouter, *Auto Router*: https://openrouter.ai/docs/guides/routing/routers/auto-router
- Chen et al., *FrugalGPT*: https://arxiv.org/abs/2305.05176
- Aggarwal et al., *AutoMix*: https://arxiv.org/abs/2310.12963
- Li et al., *Rethinking Mixture-of-Agents / Self-MoA*: https://arxiv.org/abs/2502.00674
- Li et al., *LLMRouterBench*: https://arxiv.org/abs/2601.07206
- OpenAI model catalog: https://developers.openai.com/api/docs/models
- Anthropic model overview: https://platform.claude.com/docs/en/about-claude/models/overview
- Gemini latest models: https://ai.google.dev/gemini-api/docs/latest-model
- DeepSeek pricing: https://api-docs.deepseek.com/quick_start/pricing/
