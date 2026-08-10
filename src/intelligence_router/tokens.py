from __future__ import annotations

import math
import re
from typing import Iterable

from .schemas import ChatMessage


_CJK_RE = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]"
)


class TokenEstimator:
    """Provider-neutral planning estimator.

    Actual accounting always uses provider-reported usage. The estimator is deliberately
    conservative for Chinese/Japanese/Korean text and adds per-message framing overhead.
    """

    @staticmethod
    def text_tokens(text: str) -> int:
        if not text:
            return 0
        cjk = len(_CJK_RE.findall(text))
        non_cjk = max(0, len(text) - cjk)
        whitespace = len(re.findall(r"\s+", text))
        estimated = cjk / 1.45 + non_cjk / 3.8 + whitespace * 0.05
        return max(1, math.ceil(estimated))

    def messages_tokens(self, messages: Iterable[ChatMessage]) -> int:
        total = 3
        for message in messages:
            total += 5 + self.text_tokens(message.text())
            if message.name:
                total += self.text_tokens(message.name)
        return total

    def tools_tokens(self, tools: list[dict] | None) -> int:
        if not tools:
            return 0
        return sum(self.text_tokens(str(tool)) + 8 for tool in tools)
