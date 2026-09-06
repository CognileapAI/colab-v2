"""주제 어휘 드리프트 시험 — ai-service 사본 ↔ **선언 정본**(`db/platform/schema.sql`).

⭑ **왜 필요한가** — 어휘가 사는 자리가 넷이고(DB CHECK · core-api `_TOPICS` · 프론트 `TOPICS` ·
여기 `ports.TOPICS`) 한 곳만 넓히면 조용히 갈린다. 이쪽이 갈리면 **LLM 이 옳게 말한 주제를
`interpret.py` 가 버린다**(`interpret.py` 축자 「`topic in TOPICS` 가 아니면 None」) — 에러 없이
**덜 찾는다**. `〈357〉` 가 같은 무늬였다.

같은 대조 = 프론트 `frontend/test/topics-drift.test.ts` · core-api `test_input_error_paths.py`.
근거 = `PLAN-SoT §9 〈55〉` · `〈359〉`(4값 → 6값 · 회차 20차).

⚠ **`db/ai` 의 `d9_topic_synonym` CHECK 는 이 시험의 대상이 아니다** — 그것은 **동의어 사전 항목**을
지키지 발화 주제를 지키지 않는다. 그쪽이 아직 4값인 것은 `〈360〉` 로 등록돼 있다.
"""
from __future__ import annotations

import pathlib
import re

from colab_ai.ports import TOPICS

_REPO = pathlib.Path(__file__).resolve().parents[3]
_SCHEMA = _REPO / "db" / "platform" / "schema.sql"


def _declared_topics() -> tuple[str, ...]:
    line = next(
        line for line in _SCHEMA.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("topic") and "CHECK" in line
    )
    return tuple(re.findall(r"'([^']+)'", line))


def test_ports_TOPICS_가_선언_정본과_순서까지_같다() -> None:
    """⛔ 기대값을 여기 다시 적지 않는다 — 세 곳에 적으면 갈라진다."""
    assert TOPICS == _declared_topics()


def test_354_가_넓힌_두_값이_들어_있다() -> None:
    """회귀 표식 — 이 둘이 빠지면 LLM 이 옳게 말해도 버려진다."""
    assert "가뭄" in TOPICS
    assert "파일 포맷 예제" in TOPICS


def test_프롬프트가_개수를_문장에_박지_않는다() -> None:
    """`〈359〉` 전에는 「다음 **넷** 중 하나」였다 — 어휘가 넓어지면 프롬프트만 낡는다."""
    from colab_ai.app import interpret

    prompt = getattr(interpret, "SYSTEM_PROMPT", None) or "".join(
        v for v in vars(interpret).values() if isinstance(v, str)
    )
    assert "넷 중 하나" not in prompt
