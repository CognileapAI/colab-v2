"""3회차(지역 포함 관계) — 「한반도」 region probe 5건의 경로 2 자연어 판을 오라클과 해석 녹화에 싣는다.

intent `dev-package/intent/2026-09-26-region-containment-expansion.md` 결정 3: 5 probe 조건을 자연어로 옮겨
경로 2 에서도 잰다. **모델을 부르지 않는다** — 해석은 `interpret-fixture.json` 관례대로 규칙 기반
해석기(`LiteralInterpreter().interpret(query)`, 사전·그래프 확장 없음)의 출력이다. 실모델 녹화는
모델 호출 eval 이라 별도 승인 대기다.

  services/ai-service/.venv/bin/python dev-package/reports/evidence-promotion/round-3-2026-09-26/record_path_b_queries.py

멱등하다 — 이미 실린 id 는 다시 싣지 않고, 질의가 다르면 거절한다.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "services" / "ai-service" / "src"))
from colab_ai.app import interpret as interpret_module  # noqa: E402
from colab_ai.app.interpret import LiteralInterpreter  # noqa: E402

K4 = REPO / "eval" / "k4-search"
ORACLE = K4 / "practitioner-conditions.json"
FIXTURE = K4 / "interpret-fixture.json"

#: 사례 → (경로 2 id, 자연어). probe 조건(region · period/cadence/coverageYear/variable)을 경로 2 파서가 읽는 말로 옮긴다.
PATH_B = {
    "PC-1-3": ("PB-REGION-1", "2019년 7월 28일부터 2024년 7월 9일까지 한반도 레이더 강우 자료 찾아줘"),
    "PC-1-4": ("PB-REGION-2", "한반도 5분 주기 레이더 강우 자료 찾아줘"),
    "PC-2-3": ("PB-REGION-3", "2022년 한반도 강우 자료 찾아줘"),
    "PC-2-4": ("PB-REGION-4", "한반도 15분 주기 강수 자료 찾아줘"),
    "PC-2-7": ("PB-REGION-5", "2021년이 포함된 한반도 강수 자료 찾아줘"),
}
#: 상향 누수 대조 — 「남한」 질의가 한반도 자료(seq 6)를 파일 근거 후보로 올리지 않는가.
LEAK = [("PB-LEAK-1", "남한 식생 자료 찾아줘")]
RECORDED_FROM = "LiteralInterpreter().interpret(query) — 사전·그래프 확장 없음"
NOTE = "경로 2 자연어 판(결정 3). 해석은 interpret-fixture.json 의 규칙 기반 녹화 — 실모델 녹화는 별도 승인 대기"


def _dump(value, like: str) -> str:
    indent = 2 if '\n  "' in like[:200] else 1
    return json.dumps(value, ensure_ascii=False, indent=indent) + "\n"


def main() -> int:
    # 오라클은 probe 한 줄 = 객체 하나 모양이다. 파일 전체를 다시 쓰지 않고 그 줄만 고친다(서식 보존).
    lines = ORACLE.read_text(encoding="utf-8").split("\n")
    case_id, marked = None, 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('"id": "PC-'):
            case_id = stripped.split('"')[3]
        if case_id not in PATH_B or not stripped.startswith("{") or '"korean_peninsula"' not in stripped:
            continue
        comma = stripped.endswith(",")
        probe = json.loads(stripped.rstrip(","))
        if probe["conditions"].get("region") != "korean_peninsula":
            continue
        pid, query = PATH_B[case_id]
        existing = probe.get("pathB")
        if existing and (existing["id"], existing["query"]) != (pid, query):
            raise SystemExit(f"{case_id}: 다른 pathB 가 이미 있다 — {existing}")
        probe["pathB"] = {"id": pid, "query": query, "note": NOTE}
        lines[index] = line[:len(line) - len(line.lstrip())] + json.dumps(probe, ensure_ascii=False) + ("," if comma else "")
        marked += 1
    if marked != len(PATH_B):
        raise SystemExit(f"「한반도」 region probe 를 {marked}건 찾았다(기대 {len(PATH_B)})")
    ORACLE.write_text("\n".join(lines), encoding="utf-8")
    json.loads(ORACLE.read_text(encoding="utf-8"))  # 고친 뒤에도 JSON 이어야 한다

    ftext = FIXTURE.read_text(encoding="utf-8")
    fixture = json.loads(ftext)
    sha = hashlib.sha256(pathlib.Path(interpret_module.__file__).read_bytes()).hexdigest()
    fixture["provenance"]["practitionerPathB"] = {
        "what": ("LiteralInterpreter().interpret(query) — 사전·그래프 확장 없음. 실무자 「한반도」 region probe 5건의 "
                 "경로 2 자연어 판(PB-REGION-*)과 상향 누수 대조 질의(PB-LEAK-*). 실모델 녹화는 별도 승인 대기"
                 "(intent 2026-09-26-region-containment-expansion 결정 3)"),
        "interpreterSha256": sha,
    }
    by_id = {e["id"]: e for e in fixture["entries"]}
    for pid, query in [*PATH_B.values(), *LEAK]:
        got = LiteralInterpreter().interpret(query)
        entry = {"id": pid, "query": query, "isDataQuery": got.is_data_query, "terms": list(got.terms),
                 "topic": got.topic, "source": got.source, "recordedFrom": RECORDED_FROM}
        if pid in by_id:
            if by_id[pid] != entry:
                raise SystemExit(f"{pid}: 녹화가 이미 있고 다르다 — 해석기가 바뀌었는지 확인한다")
            continue
        fixture["entries"].append(entry)
    FIXTURE.write_text(_dump(fixture, ftext), encoding="utf-8")
    print(json.dumps({"pathB": marked, "entries": len(fixture["entries"]), "interpreterSha256": sha,
                      "modelCalls": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
