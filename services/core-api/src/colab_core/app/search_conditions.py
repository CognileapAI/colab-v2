"""검색 질문의 품질 수치 조건을 검색어 OR 매칭에서 떼어 낸다.

⭑ 종전 `explain_unverified_conditions`(「요청한 X 조건은 … 확인하지 못했어요」)는 지웠다 —
카드 근거는 검색된 이유만 싣는다(intent `2026-09-25-search-rationale-separation.md` Q6 ·
Ted 2026-09-26).
"""
from __future__ import annotations

import re


_QUALITY_PERCENT = re.compile(
    r"(?<!\w)(?:결측률|결측율|누락률|정확도)\s*(?:이|가|은|는)?\s*"
    r"(?:[<>]=?|[≤≥])?\s*\d+(?:[.,]\d+)?\s*%"
    r"(?:\s*(?:이하|이상|미만|초과))?(?:으로|에서|까지|부터|인|의|로|가|를)?")


def candidate_terms(query: str, terms: list[str]) -> list[str]:
    """Keep quality thresholds out of OR matching, regardless of interpreter.

    Preserve the original query for condition explanations. A numeric token that
    also occurs outside the quality phrase remains a legitimate search term.
    Splitting here recognizes decimal fragments returned by literal interpreters;
    it never produces new search terms or removes numbers without that context.
    """
    spans = list(_QUALITY_PERCENT.finditer(query))
    if not spans:
        return terms

    def tokens(value: str) -> set[str]:
        parts = re.findall(r"[^\W\d_]+|\d+", value.lower())
        return {re.sub(r"^(결측률|결측율|누락률|정확도)(?:이|가|은|는)$", r"\1", part)
                for part in parts}

    removed = tokens(" ".join(match.group() for match in spans))
    remaining = tokens(_QUALITY_PERCENT.sub(" ", query))
    return [term for term in terms
            if not (tokens(term) and tokens(term) <= removed
                    and not tokens(term) & remaining)]
