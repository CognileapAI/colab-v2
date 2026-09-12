"""검색 질문이 요구한 조건 중 현재 검색이 검증하지 못하는 것을 설명한다."""
from __future__ import annotations

import re


_CONDITION_PATTERNS = (
    ("기간", re.compile(r"(?:\d{4}\s*년|기간|시계열|부터|까지)")),
    ("지역", re.compile(r"(?:전국|한반도|지역|서울|경기|강원|충청|전라|경상|제주)")),
    ("품질", re.compile(r"(?:품질|결측|누락|오차|정확도|완전성)")),
    ("직접 관측", re.compile(r"(?:직접\s*관측|원관측|관측\s*해상도)")),
    ("파일 역할", re.compile(
        r"(?:검증용|학습용|정답|예측\s*(?:파일|자료)|입력\s*(?:파일|자료)|"
        r"모델\s*(?:입력|출력)|파일\s*역할)")),
)


def explain_unverified_conditions(rationale: str, query: str) -> str:
    """기존 한 줄 근거를 보존하면서 질문에서만 드러난 미확인 조건을 밝힌다.

    데이터셋 요약이나 격자 간격은 이 함수의 입력이 아니다. 따라서 검색어가 맞았다는
    사실을 기간·품질·직접 관측·파일 역할이 충족됐다는 주장으로 바꾸지 않는다.
    """
    labels = [label for label, pattern in _CONDITION_PATTERNS if pattern.search(query)]
    if not labels:
        return rationale
    base = rationale.rstrip()
    return (
        f"{base} 요청한 {'·'.join(labels)} 조건은 현재 검색 근거만으로 "
        "충족 여부를 확인하지 못했어요."
    )
