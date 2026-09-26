"""2회차 측정 입력 payload — 새 생성물에 1회차 승격(dev 반영 완료) 3규칙을 겹친 사본을 만든다.

결정 7 「dev 적재와 같은 payload로 일회용 DB」 — dev 에는 1회차 승격 payload(`41f488a4…`)가 실려 있다
(platform-from-instrument · direct-observation-from-level · native-resolution-carried 가 reviewed).
2회차가 dev 에 실릴 모양 = **새 생성물 + 같은 세 규칙 승격**이다. 그래서 측정 기준선을 dev 와 맞추려면
새 생성물(`dev-package/tools/generated/dataset-evidence-payloads.json`)에 같은 세 규칙을 같은 함수
(`measure_draft_contribution.promote_payload`)로 겹친다. 생성물 자체는 손대지 않는다.

  services/core-api/.venv/bin/python dev-package/reports/evidence-promotion/round-2-2026-09-26/prepare_input_payload.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOURCE = REPO / "dev-package" / "tools" / "generated" / "dataset-evidence-payloads.json"
TARGET = HERE / "input-payload.json"
ROUND1_RULES = ("platform-from-instrument", "direct-observation-from-level", "native-resolution-carried")
NOTE = ("dev-package/intent/2026-09-21-evidence-promotion.md 판정 결과 — 1회차(2026-09-26) · "
        "dev 반영 완료 2026-09-25T23:52Z · 2회차 측정 기준선(dev 와 같은 승격 상태)")


def main() -> int:
    spec = importlib.util.spec_from_file_location(
        "k4_measure_draft", REPO / "eval" / "k4-search" / "measure_draft_contribution.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    promoted = module.promote_payload(payload, ROUND1_RULES, NOTE)
    TARGET.write_text(json.dumps(promoted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
    print(json.dumps({"source": {"path": str(SOURCE.relative_to(REPO)), "sha256": digest(SOURCE)},
                      "target": {"path": str(TARGET.relative_to(REPO)), "sha256": digest(TARGET)},
                      "movedFacts": promoted["promotion"]["movedFacts"],
                      "draftFactsLeft": sum(len(r["draftFacts"]) for r in promoted["datasets"])},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
