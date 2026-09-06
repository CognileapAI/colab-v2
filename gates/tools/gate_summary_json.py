#!/usr/bin/env python3
# 게이트 요약 JSON 배출기 — 스키마 `colab-gate-summary/1` (스펙 D절).
#
# 무엇을 하나: `gates/run.sh` 의 요약 블록이 **이미 쥐고 있는 값**을 TSV 로 받아 JSON 한 개로 적는다.
#
# ⛔ **여기서 계수를 다시 세지 않는다.** 세는 자리는 실행기의 요약 블록 하나이고,
#    여기서 로그를 다시 읽거나 상태를 다시 판정하면 두 값이 언젠가 갈린다
#    (스펙 D 축자 「`counts` 는 run.sh 가 이미 세는 `n_green` / `n_red_judge` / `n_red_ready` /
#    `n_undeclared_input` 을 그대로 쓴다」). 이 파일이 하는 판단은 **직렬화뿐**이다.
#
# ⚠ 상태는 셋뿐이다 — `green` / `red_판정` / `red_준비`. `SKIP` 은 만들지 않는다
#   (스펙 D · `CLAUDE.md §4` — 대상 0건을 통과로 세는 통로를 다시 열지 않는다).
#
# stdin (TSV · 줄 단위):
#   meta<TAB>요청대상<TAB>tree<TAB>commit<TAB>started<TAB>finished<TAB>병렬도
#   counts<TAB>green<TAB>red_판정<TAB>red_준비<TAB>red_준비_입력미선언
#   gate<TAB>이름<TAB>상태<TAB>종료코드<TAB>준비표식(없으면 빈 칸)
#   target<TAB>이름            (실행기가 고른 대상 목록 — 새 계수 개념이 아니라 이름 나열이다)
# argv: 배출 경로 1개 이상. 같은 내용을 각 자리에 적는다(원자적 교체).
import json
import os
import sys

SCHEMA = "colab-gate-summary/1"
STATES = ("green", "red_판정", "red_준비")


def main() -> int:
    outs = sys.argv[1:]
    if not outs:
        sys.stderr.write("gate_summary_json: 배출 경로가 없다\n")
        return 2

    meta = {}
    counts = {}
    gates = []
    targets = []

    for raw in sys.stdin.read().splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        kind = parts[0]
        if kind == "meta":
            f = (parts + [""] * 7)[1:7]
            meta = {
                "requested": f[0],
                "tree": f[1] or None,
                "commit": f[2] or None,
                "started": f[3] or None,
                "finished": f[4] or None,
                "parallelism": int(f[5]) if f[5].strip().isdigit() else None,
            }
        elif kind == "counts":
            f = (parts + [""] * 5)[1:5]
            counts = {
                "green": int(f[0] or 0),
                "red_판정": int(f[1] or 0),
                "red_준비": int(f[2] or 0),
                "red_준비_입력미선언": int(f[3] or 0),
            }
        elif kind == "gate":
            f = (parts + [""] * 5)[1:5]
            state = f[1] if f[1] in STATES else "red_판정"
            try:
                code = int(f[2])
            except ValueError:
                code = None
            gates.append(
                {
                    "name": f[0],
                    # `status` = P-J 지시문의 이름 · `state` = 스펙 D 예시의 이름.
                    # 값은 항상 같다. 소비자가 어느 쪽을 읽든 같은 사실을 본다.
                    "status": state,
                    "state": state,
                    "exit": code,
                    "readiness": f[3] or None,
                }
            )
        elif kind == "target":
            targets.append(parts[1] if len(parts) > 1 else "")

    # 대조 — 요약 계수와 게이트별 상태가 갈리면 **경고만** 한다. 정본은 요약 계수다.
    # (여기서 계수를 고쳐 쓰면 이 파일이 두 번째 판정처가 된다.)
    if counts:
        seen = {s: sum(1 for g in gates if g["status"] == s) for s in STATES}
        if seen["green"] != counts.get("green") or \
           seen["red_판정"] != counts.get("red_판정") or \
           seen["red_준비"] != counts.get("red_준비"):
            sys.stderr.write(
                "gate_summary_json: ⚠ 요약 계수와 게이트별 상태가 갈렸다 "
                f"(요약 {counts} · 게이트별 {seen}) — 요약 계수를 그대로 적었다\n"
            )

    doc = {
        "schema": SCHEMA,
        "tree": meta.get("tree"),
        "commit": meta.get("commit"),
        "started": meta.get("started"),
        "finished": meta.get("finished"),
        "parallelism": meta.get("parallelism"),
        "counts": counts,
        "gates": gates,
        "targets": {"requested": meta.get("requested"), "selected": targets},
    }

    body = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    written = []
    for path in outs:
        d = os.path.dirname(os.path.abspath(path))
        os.makedirs(d, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(body)
        os.replace(tmp, path)
        written.append(path)
    for path in written:
        print(f"  요약 JSON  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
