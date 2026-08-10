from __future__ import annotations

import re
from collections import defaultdict

from .schemas import ChatCompletionRequest, TaskProfile


class HeuristicTaskClassifier:
    """Zero-token classifier used before any model call.

    It is intentionally transparent and cheap. Production deployments can replace it with a
    learned classifier while keeping the same ``TaskProfile`` contract.
    """

    _patterns: dict[str, tuple[str, ...]] = {
        "classification": (
            "classify",
            "classification",
            "label",
            "categorize",
            "intent",
            "分类",
            "打标签",
            "意图识别",
        ),
        "extraction": (
            "extract",
            "parse",
            "fields",
            "structured data",
            "json schema",
            "提取",
            "抽取",
            "结构化",
            "字段",
        ),
        "summarization": (
            "summarize",
            "summary",
            "tl;dr",
            "condense",
            "recap",
            "总结",
            "摘要",
            "概括",
        ),
        "translation": (
            "translate",
            "translation",
            "into english",
            "into chinese",
            "翻译",
            "译成",
            "中译英",
            "英译中",
        ),
        "coding": (
            "debug",
            "implement",
            "refactor",
            "repository",
            "pull request",
            "stack trace",
            "unit test",
            "typescript",
            "python",
            "javascript",
            "sql",
            "代码",
            "编程",
            "调试",
            "实现",
            "重构",
            "报错",
            "测试",
        ),
        "math": (
            "calculate",
            "equation",
            "theorem",
            "proof",
            "derivative",
            "integral",
            "probability",
            "solve for",
            "数学",
            "方程",
            "证明",
            "微分",
            "积分",
            "概率",
            "计算",
        ),
        "reasoning": (
            "reason step",
            "logic puzzle",
            "root cause",
            "trade-off",
            "tradeoff",
            "analyze why",
            "推理",
            "逻辑",
            "根因",
            "权衡",
            "论证",
        ),
        "research": (
            "deep research",
            "literature review",
            "cite sources",
            "with citations",
            "state of the art",
            "market research",
            "compare evidence",
            "最新",
            "深度研究",
            "文献综述",
            "引用来源",
            "调研",
            "竞品分析",
        ),
        "creative": (
            "brainstorm",
            "story",
            "poem",
            "tagline",
            "creative",
            "write a script",
            "头脑风暴",
            "故事",
            "诗",
            "创意",
            "文案",
        ),
        "customer_support": (
            "customer support",
            "support reply",
            "refund",
            "ticket",
            "customer complaint",
            "客服",
            "工单",
            "退款",
            "客户投诉",
        ),
        "agentic": (
            "plan and execute",
            "use tools",
            "multi-step",
            "autonomously",
            "agent",
            "run commands",
            "create files",
            "执行任务",
            "使用工具",
            "多步骤",
            "自主完成",
            "智能体",
        ),
    }

    _high_stakes = (
        "medical",
        "diagnosis",
        "treatment",
        "legal advice",
        "lawsuit",
        "contract clause",
        "investment advice",
        "tax advice",
        "financial advice",
        "patient",
        "dosage",
        "医学",
        "诊断",
        "治疗",
        "法律意见",
        "诉讼",
        "合同条款",
        "投资建议",
        "税务建议",
        "患者",
        "剂量",
    )

    _security = (
        "vulnerability",
        "incident response",
        "malware",
        "exploit",
        "security audit",
        "漏洞",
        "安全审计",
        "恶意软件",
        "应急响应",
    )

    _freshness = (
        "latest",
        "current",
        "today",
        "this week",
        "recent",
        "最新",
        "当前",
        "今天",
        "本周",
        "近期",
    )

    _strict_json = (
        "valid json",
        "json only",
        "strict json",
        "return json",
        "只返回json",
        "严格json",
        "json格式",
    )

    def classify(self, request: ChatCompletionRequest, input_tokens: int) -> TaskProfile:
        text = request.prompt_text().lower()
        scores: dict[str, float] = defaultdict(float)
        signals: list[str] = []

        for task, patterns in self._patterns.items():
            matches = sum(1 for pattern in patterns if pattern in text)
            if matches:
                scores[task] += min(1.2, 0.48 + 0.22 * matches)
                signals.append(f"keyword:{task}:{matches}")

        if "```" in text or re.search(r"\b(def|class|function|import|const|SELECT|CREATE TABLE)\b", text):
            scores["coding"] += 0.8
            signals.append("code-structure")

        if re.search(r"\b\d+(?:\.\d+)?\s*[+\-*/=<>]\s*\d+", text) or re.search(
            r"[∫∑√≈≠≤≥]", text
        ):
            scores["math"] += 0.75
            signals.append("math-symbols")

        if request.tools:
            scores["agentic"] += 0.7
            signals.append("tool-schema")

        if not scores:
            task_type = "general"
            confidence = 0.55
        else:
            ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
            task_type = ranked[0][0]
            margin = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0.0)
            confidence = min(0.96, 0.58 + 0.22 * margin)

        complexity = 0.12
        if input_tokens > 250:
            complexity += 0.08
        if input_tokens > 1000:
            complexity += 0.16
        if input_tokens > 4000:
            complexity += 0.20
        if input_tokens > 16_000:
            complexity += 0.18

        complexity += min(0.16, text.count("?") * 0.025)
        complexity += min(0.12, len(re.findall(r"(?:^|\n)\s*(?:[-*]|\d+[.)])\s+", text)) * 0.018)

        if task_type in {"coding", "math", "reasoning", "research", "agentic"}:
            complexity += 0.18
        if task_type in {"research", "agentic"}:
            complexity += 0.12
        if any(term in text for term in ("deep", "comprehensive", "ultra", "production-ready", "深度", "全面", "生产级")):
            complexity += 0.14
            signals.append("depth-requested")
        if any(term in text for term in ("compare", "critique", "pros and cons", "对比", "批判", "优缺点")):
            complexity += 0.08
            signals.append("multi-perspective")
        complexity = max(0.0, min(1.0, complexity))

        risk = 0.10
        if any(term in text for term in self._high_stakes):
            risk = max(risk, 0.82)
            signals.append("high-stakes-domain")
        if any(term in text for term in self._security):
            risk = max(risk, 0.68)
            signals.append("security-domain")
        if any(term in text for term in self._freshness):
            risk = max(risk, 0.42)
            signals.append("freshness-sensitive")
        if task_type == "research":
            risk = max(risk, 0.48)
        if task_type == "agentic" or request.tools:
            risk = max(risk, 0.50)
        if any(term in text for term in ("confidential", "secret", "personal data", "机密", "隐私", "个人信息")):
            risk = max(risk, 0.70)
            signals.append("sensitive-data")

        override = request.router.risk
        if override == "low":
            risk = min(risk, 0.25)
            signals.append("risk-override:low")
        elif override == "medium":
            risk = max(0.40, min(risk, 0.65))
            signals.append("risk-override:medium")
        elif override == "high":
            risk = max(risk, 0.85)
            signals.append("risk-override:high")

        required = {"text", *request.router.required_capabilities, *request.router.native_tools}
        if request.tools:
            required.add("tools")
        if request.response_format or any(term in text for term in self._strict_json):
            required.add("json")
        if input_tokens > 64_000:
            required.add("long_context")
        if self._contains_image(request):
            required.add("vision")
        if task_type in {"math", "reasoning"} and complexity >= 0.55:
            required.add("reasoning")

        return TaskProfile(
            task_type=task_type,  # type: ignore[arg-type]
            complexity=round(complexity, 4),
            risk=round(risk, 4),
            confidence=round(confidence, 4),
            required_capabilities=sorted(required),
            signals=signals,
        )

    @staticmethod
    def _contains_image(request: ChatCompletionRequest) -> bool:
        for message in request.messages:
            if not isinstance(message.content, list):
                continue
            for item in message.content:
                if isinstance(item, dict) and item.get("type") in {
                    "image",
                    "image_url",
                    "input_image",
                }:
                    return True
        return False
