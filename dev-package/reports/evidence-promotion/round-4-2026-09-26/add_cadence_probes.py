"""4회차(「1시간 이하」 주기 범위) — PC-1-4·PC-2-4 에 범위 술어 probe 를 싣고 경로 2 자연어 판을 녹화한다.

intent `dev-package/intent/2026-09-26-cadence-range-predicate.md`. 정의(Ted 2026-09-26 원문
「측정 간격같은데 1시간이하는 산출간격(주기)」) — 「1시간 이하」 = 산출 간격(cadence) ≤ 3600 초.
**모델을 부르지 않는다** — 경로 2 해석은 3회차와 같은 규칙 기반 해석기(`LiteralInterpreter`) 녹화다.

  services/ai-service/.venv/bin/python dev-package/reports/evidence-promotion/round-4-2026-09-26/add_cadence_probes.py

멱등하다 — 같은 이름의 probe·같은 id 녹화는 다시 싣지 않고, 내용이 다르면 거절한다.
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
HOUR = 3600
NOTE = "경로 2 자연어 판. 해석은 interpret-fixture.json 의 규칙 기반 녹화 — 실모델 녹화는 별도 승인 대기"
RECORDED_FROM = "LiteralInterpreter().interpret(query) — 사전·그래프 확장 없음"

#: 사례 → 추가 probe. 기대 seq 는 정본이 cadence 를 reviewed 로 고정한 자료다(생성물 payload `facts.cadence`):
#: 5min seq 1 · 10min seq 17 · 15min seq 2·4 · hourly seq 16 — 1시간 이하. daily 6·12 · weekly 13·14 ·
#: monthly 7·8 · yearly 11 — 1시간 초과. cadence 가 없는 seq 3·5 는 모른다(unknown) — 범위를 맞추지 않는다.
PROBES = {
    "PC-1-4": [
        {"name": "1시간 이하 주기 — 범위 술어(전 자료)", "conditions": {"maxCadenceSeconds": HOUR},
         "expectSeq": [1, 2, 4, 16, 17], "forbidSeq": [3, 5, 6, 7, 8, 11, 12, 13, 14]},
        {"name": "강수 변수 + 1시간 이하", "conditions": {"variable": "precipitation", "maxCadenceSeconds": HOUR},
         "expectSeq": [2, 4], "forbidSeq": [5, 6, 12],
         "pathB": {"id": "PB-CADENCE-1", "query": "시간해상도 1시간 이하 강수 자료 찾아줘", "note": NOTE}},
        {"name": "1시간 이하 + 5 km 이하", "conditions": {"maxCadenceSeconds": HOUR, "maxResolutionM": 5000},
         "expectSeq": [1], "forbidSeq": [2, 3, 4, 6, 7, 16, 17]},
    ],
    "PC-2-4": [
        {"name": "한반도 + 1시간 이하", "conditions": {"region": "korean_peninsula", "maxCadenceSeconds": HOUR},
         "expectSeq": [1, 2], "forbidSeq": [6, 16, 17],
         "pathB": {"id": "PB-CADENCE-2", "query": "시간해상도 1시간 이하 한반도 강수 자료 찾아줘", "note": NOTE}},
        {"name": "한반도 + 1시간 이하 + 5 km 이하",
         "conditions": {"region": "korean_peninsula", "maxCadenceSeconds": HOUR, "maxResolutionM": 5000},
         "expectSeq": [1], "forbidSeq": [2, 6, 16, 17]},
    ],
}
#: 경로 2 가 「15분」을 주기로 읽는지 보는 대조 질의 — 녹화만 한다(probe 가 아니다).
EXTRA = [("PB-CADENCE-3", "30분 이내 강우 자료 찾아줘")]


def main() -> int:
    lines = ORACLE.read_text(encoding="utf-8").split("\n")
    added = 0
    for case_id, probes in PROBES.items():
        start = next(i for i, line in enumerate(lines) if line.strip() == f'"id": "{case_id}",')
        head = next(i for i in range(start, len(lines)) if lines[i].strip() == '"probes": [')
        end = next(i for i in range(head, len(lines)) if lines[i].strip() in ("],", "]"))
        indent = lines[head + 1][:len(lines[head + 1]) - len(lines[head + 1].lstrip())]
        existing = {json.loads(lines[i].strip().rstrip(","))["name"]: json.loads(lines[i].strip().rstrip(","))
                    for i in range(head + 1, end)}
        new = []
        for probe in probes:
            if probe["name"] in existing:
                if existing[probe["name"]] != probe:
                    raise SystemExit(f"{case_id}: 같은 이름의 다른 probe 가 있다 — {probe['name']}")
                continue
            new.append(indent + json.dumps(probe, ensure_ascii=False))
        if not new:
            continue
        if not lines[end - 1].rstrip().endswith(","):
            lines[end - 1] = lines[end - 1] + ","
        lines[end:end] = [line + "," for line in new[:-1]] + [new[-1]]
        added += len(new)
    ORACLE.write_text("\n".join(lines), encoding="utf-8")
    json.loads(ORACLE.read_text(encoding="utf-8"))  # 고친 뒤에도 JSON 이어야 한다

    ftext = FIXTURE.read_text(encoding="utf-8")
    fixture = json.loads(ftext)
    sha = hashlib.sha256(pathlib.Path(interpret_module.__file__).read_bytes()).hexdigest()
    fixture["provenance"]["practitionerCadence"] = {
        "what": ("LiteralInterpreter().interpret(query) — 사전·그래프 확장 없음. 실무자 「1시간 이하」 주기 범위 probe 의 "
                 "경로 2 자연어 판(PB-CADENCE-*). 실모델 녹화는 별도 승인 대기"
                 "(intent 2026-09-26-cadence-range-predicate)"),
        "interpreterSha256": sha,
    }
    by_id = {e["id"]: e for e in fixture["entries"]}
    queries = [(p["pathB"]["id"], p["pathB"]["query"]) for probes in PROBES.values() for p in probes if "pathB" in p]
    recorded = 0
    for pid, query in [*queries, *EXTRA]:
        got = LiteralInterpreter().interpret(query)
        entry = {"id": pid, "query": query, "isDataQuery": got.is_data_query, "terms": list(got.terms),
                 "topic": got.topic, "source": got.source, "recordedFrom": RECORDED_FROM}
        if pid in by_id:
            if by_id[pid] != entry:
                raise SystemExit(f"{pid}: 녹화가 이미 있고 다르다 — 해석기가 바뀌었는지 확인한다")
            continue
        fixture["entries"].append(entry)
        recorded += 1
    indent = 2 if '\n  "' in ftext[:200] else 1
    FIXTURE.write_text(json.dumps(fixture, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")
    print(json.dumps({"probesAdded": added, "recorded": recorded, "entries": len(fixture["entries"]),
                      "interpreterSha256": sha, "modelCalls": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
