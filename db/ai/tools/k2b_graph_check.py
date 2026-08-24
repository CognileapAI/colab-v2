#!/usr/bin/env python3
"""K2b 그래프 판정기 — 기준(TSV)과 적재된 행(사실 TSV)을 대조한다.

이것이 **WU-K2b 의 완료 오라클**이다 (K1b-ONTOLOGY-CONTENT.md §E-4).

  기준 = db/ai/seed/k2b-graph-standard.tsv   (Ted 판정 2026-08-25 을 옮긴 것)
  사실 = DB 에서 뽑은 줄들 (stdin) — 다섯 종류
           node<TAB>concept_id<TAB>kind<TAB>label<TAB>source_grade<TAB>expandable
           edge<TAB>src<TAB>relation<TAB>dst<TAB>source_grade
           mterm<TAB>term            (d9_method_term — §E-3 정합 대조용)
           topic<TAB>topic           (d9_topic_synonym.topic — §E-4 4번)
검사 항목 (§E-4)
  1. 노드·엣지 집합이 기준과 **완전일치** (기준에 없는 행이 있어도 red, 없어도 red)
  2. source_grade=6 행이 **Ted 승인 목록(APPROVED_G6)과 정확히 일치** — 승인 안 난 ⑥ 이 몰래 들어오면 red
  3. kind='방법' 정본 인용 13개가 d9_method_term 과 문자열 일치
  4. kind='주제' 4개가 d9_topic_synonym.topic 4값과 일치
  5. '~의 한 가지다' 의 dst 중 expandable=false 인 것이 0 건 (§D-6 경계 4 — 부모 금지 목록)
  6. 팬아웃 상한 — 어떤 dst 도 자식이 6개를 넘지 않는다 (§D-6 경계 3)
  7. '안에 있다'·'~의 한 가지다' 의 양끝 kind 규약 (§E-2)

「대상이 없어서 통과」를 만들지 않는다 — 기준이 비었거나 사실이 비면 그 자체가 red 다
(CLAUDE.md §4: 검사를 못 한 것은 통과가 아니다).

표준 라이브러리만 쓴다. DB 접속은 껍데기(k2b-graph-check.sh)의 일이다.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

KINDS = ("방법", "주제", "지명", "원천표기")
RELATIONS = ("같은 말이다", "~의 한 가지다", "안에 있다")
FANOUT_MAX = 6

# 정본 인용 13개 — d9_method_term 과 **한 글자도 달라선 안 되는** label 들 (§E-3).
CANON_METHOD_LABELS = (
    "격자 보간", "품질검사", "유역 클리핑", "유역 평균", "유역 집계", "일 단위 평균",
    "유역 경계로 잘라냄", "임계값 초과일 집계", "재격자화", "편의 보정", "다운스케일",
    "전처리", "보간 방식(선형/최근접)",
)
CANON_TOPICS = ("강우·강수", "식생·NDVI", "지형·DEM", "토지피복·LULC")

# ── Ted 승인 목록 (2026-08-25, K1b-ONTOLOGY-CONTENT §F-A) ────────────────────
# 등급 ⑥(도메인 상식)에 기댄 엣지는 **이 목록에 있는 것만** 시드에 들어올 수 있다.
# 초안 11 줄 중 F-4d(Co-Kriging → 재격자화) · F-7(유역 평균 → 유역 집계) 은 ❌ 로 빠졌다 → 승인 9 줄.
APPROVED_G6 = {
    ("m-cokriging", "같은 말이다", "m-regkriging"): "F-1",
    ("m-basin-clip", "같은 말이다", "m-basin-cut"): "F-2",
    ("p-korea-en", "같은 말이다", "p-korea-peninsula"): "F-3",
    ("m-nearest", "~의 한 가지다", "m-regrid"): "F-4a",
    ("m-bilinear", "~의 한 가지다", "m-regrid"): "F-4b",
    ("m-idw", "~의 한 가지다", "m-regrid"): "F-4c",
    ("m-grid-interp", "~의 한 가지다", "m-regrid"): "F-5",
    ("m-downscale", "~의 한 가지다", "m-regrid"): "F-6",
    ("p-han-upper", "안에 있다", "p-han"): "F-8",
}
# F-8 은 **승인됐으나 시드에 없다.** F-10 ㈏ 가 「E2 는 충청권⊂한반도 1행만 · E2-2 는 넣지 않는다」로
# 그 뒤에 닫았기 때문이다. 승인(내용 판단)과 적재(모델링 판정)가 갈리는 유일한 줄이라 여기 적어 둔다.
# 그래서 검사는 둘로 나뉜다 — 적재된 ⑥ 은 (가) 기준 TSV 와 완전일치하고 (나) 전부 이 목록 안이어야 한다.
APPROVED_BUT_NOT_SEEDED = {("p-han-upper", "안에 있다", "p-han"): "F-8 (F-10 ㈏ 로 미적재)"}

FAILS: list[str] = []


def red(msg: str) -> None:
    """즉시 종결되는 red — 검사 자체가 성립하지 않는 경우에만 쓴다."""
    print(f"::error::k2b-graph red — {msg}")
    raise SystemExit(1)


def fail(msg: str) -> None:
    FAILS.append(msg)


def load_standard(path: Path):
    if not path.is_file():
        red(f"그래프 기준 정본이 없다: {path.name}")
    nodes: dict[str, tuple[str, str, int, bool]] = {}
    edges: dict[tuple[str, str, str], int] = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        p = line.split("\t")
        if p[0] == "node":
            if len(p) < 7 or not p[6].strip():
                red(f"기준 {n}행: node 는 7열(근거 포함)이어야 한다. 근거 없는 기준 항목은 기준이 아니다")
            cid, kind, label, grade, exp = p[1].strip(), p[2].strip(), p[3].strip(), p[4].strip(), p[5].strip()
            if kind not in KINDS:
                red(f"기준 {n}행: 알 수 없는 kind {kind!r}")
            if exp not in ("t", "f"):
                red(f"기준 {n}행: expandable 은 t/f 여야 한다 — {exp!r}")
            if cid in nodes:
                red(f"기준 {n}행: concept_id 중복 {cid!r}")
            nodes[cid] = (kind, label, int(grade), exp == "t")
        elif p[0] == "edge":
            if len(p) < 6 or not p[5].strip():
                red(f"기준 {n}행: edge 는 6열(근거 포함)이어야 한다")
            key = (p[1].strip(), p[2].strip(), p[3].strip())
            if key[1] not in RELATIONS:
                red(f"기준 {n}행: 알 수 없는 relation {key[1]!r}")
            if key in edges:
                red(f"기준 {n}행: 엣지 중복 {key}")
            edges[key] = int(p[4].strip())
        else:
            red(f"기준 {n}행: 첫 열은 node/edge 여야 한다 — {p[0]!r}")
    if not nodes or not edges:
        red("기준이 비었다. 0건을 green 으로 세지 않는다.")
    return nodes, edges


def read_facts():
    nodes: dict[str, tuple[str, str, int, bool]] = {}
    edges: dict[tuple[str, str, str], int] = {}
    mterms: set[str] = set()
    topics: set[str] = set()
    seen = 0
    for line in sys.stdin.read().splitlines():
        if not line.strip():
            continue
        p = line.split("\t")
        seen += 1
        if p[0] == "node":
            if len(p) < 6:
                red(f"사실 줄이 node 6열이 아니다: {line!r}")
            nodes[p[1].strip()] = (p[2].strip(), p[3].strip(), int(p[4].strip()), p[5].strip() in ("t", "true"))
        elif p[0] == "edge":
            if len(p) < 5:
                red(f"사실 줄이 edge 5열이 아니다: {line!r}")
            edges[(p[1].strip(), p[2].strip(), p[3].strip())] = int(p[4].strip())
        elif p[0] == "mterm":
            mterms.add(p[1].strip())
        elif p[0] == "topic":
            topics.add(p[1].strip())
        else:
            red(f"사실 줄의 종류가 알 수 없는 값이다: {p[0]!r}")
    if seen == 0:
        red("적재된 행이 0건이다. 빈 DB 를 '기준과 일치'로 세지 않는다.")
    if not nodes:
        red("d9_concept 이 0행이다. K2b 가 적재되지 않았다.")
    return nodes, edges, mterms, topics


def main() -> int:
    std_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parents[1] / "seed" / "k2b-graph-standard.tsv"
    )
    std_nodes, std_edges = load_standard(std_path)
    nodes, edges, mterms, topics = read_facts()

    # ── 1. 집합 완전일치 ─────────────────────────────────────────────────────
    for cid in sorted(set(std_nodes) - set(nodes)):
        fail(f"[1 노드 누락] {cid} — 기준에 있는데 DB 에 없다")
    for cid in sorted(set(nodes) - set(std_nodes)):
        fail(f"[1 노드 초과] {cid} — 기준에 없는 노드가 DB 에 있다 (발명 금지 · PLAN-SoT §9-㊴-②)")
    for cid in sorted(set(std_nodes) & set(nodes)):
        if std_nodes[cid] != nodes[cid]:
            fail(f"[1 노드 불일치] {cid} — 기준 {std_nodes[cid]} vs DB {nodes[cid]}")
    for e in sorted(set(std_edges) - set(edges)):
        fail(f"[1 엣지 누락] {e[0]} -{e[1]}-> {e[2]}")
    for e in sorted(set(edges) - set(std_edges)):
        fail(f"[1 엣지 초과] {e[0]} -{e[1]}-> {e[2]} — 기준에 없는 엣지가 DB 에 있다")
    for e in sorted(set(std_edges) & set(edges)):
        if std_edges[e] != edges[e]:
            fail(f"[1 등급 불일치] {e[0]} -{e[1]}-> {e[2]} — 기준 ⑥표기 {std_edges[e]} vs DB {edges[e]}")

    # ── 2. source_grade=6 ↔ Ted 승인 목록 ────────────────────────────────────
    db_g6 = {e for e, g in edges.items() if g == 6}
    std_g6 = {e for e, g in std_edges.items() if g == 6}
    for e in sorted(db_g6 - std_g6):
        fail(f"[2 미승인 ⑥] {e[0]} -{e[1]}-> {e[2]} — 기준에 없는 등급 ⑥ 행이 적재됐다. "
             "도메인 상식에 기댄 행은 Ted 승인 없이 들어올 수 없다 (§F)")
    for e in sorted(std_g6 - db_g6):
        fail(f"[2 승인 ⑥ 누락] {e[0]} -{e[1]}-> {e[2]} — 승인된 ⑥ 행이 적재되지 않았다")
    for e in sorted(db_g6):
        if e not in APPROVED_G6:
            fail(f"[2 승인 목록 밖] {e[0]} -{e[1]}-> {e[2]} — Ted 승인 목록(§F-A 9줄) 어디에도 없다")
    # ⑥ 노드는 애초에 0 건이어야 한다 (§A — 노드는 등급 ⑥ 이 없다).
    for cid, (_, _, g, _) in sorted(nodes.items()):
        if g == 6:
            fail(f"[2 ⑥ 노드] {cid} — 노드에는 등급 ⑥ 이 없어야 한다 (§A)")

    # ── 3. 방법 13 ↔ d9_method_term ─────────────────────────────────────────
    labels = {v[1] for v in nodes.values() if v[0] == "방법"}
    if mterms:
        for t in CANON_METHOD_LABELS:
            if t not in labels:
                fail(f"[3 정본 어휘 누락] d9_method_term '{t}' 에 대응하는 d9_concept 방법 노드가 없다")
            if t not in mterms:
                fail(f"[3 사전 누락] '{t}' 가 d9_method_term 에 없다 — K2 시드가 흔들렸다")
    else:
        fail("[3] d9_method_term 사실이 0건이다. §E-3 정합 대조를 못 했다 — 못 한 검사는 통과가 아니다")

    # ── 4. 주제 4 ↔ d9_topic_synonym.topic ──────────────────────────────────
    topic_labels = {v[1] for v in nodes.values() if v[0] == "주제"}
    if topic_labels != set(CANON_TOPICS):
        fail(f"[4 주제 불일치] d9_concept 주제 {sorted(topic_labels)} ≠ 정본 4값 {sorted(CANON_TOPICS)}")
    if topics and not topics <= set(CANON_TOPICS):
        fail(f"[4] d9_topic_synonym.topic 에 정본 4값 밖의 값이 있다: {sorted(topics - set(CANON_TOPICS))}")

    # ── 5. 부모 금지 목록 — expandable=false 가 '~의 한 가지다' 의 dst 가 될 수 없다 ──
    for (s, r, d) in sorted(edges):
        if r == "~의 한 가지다" and d in nodes and not nodes[d][3]:
            fail(f"[5 부모 금지] {d} 는 expandable=false 인데 '{r}' 의 dst 다 (§D-6 경계 4)")

    # ── 6. 팬아웃 상한 6 ────────────────────────────────────────────────────
    fanout = Counter(d for (_, r, d) in edges if r in ("~의 한 가지다", "안에 있다"))
    for d, c in sorted(fanout.items()):
        if c > FANOUT_MAX:
            fail(f"[6 팬아웃] {d} 의 자식이 {c}개다 (상한 {FANOUT_MAX} · §D-6 경계 3)")

    # ── 7. 양끝 kind 규약 ───────────────────────────────────────────────────
    need = {"안에 있다": "지명", "~의 한 가지다": "방법"}
    for (s, r, d) in sorted(edges):
        if r not in need:
            continue
        for end in (s, d):
            if end in nodes and nodes[end][0] != need[r]:
                fail(f"[7 kind] {s} -{r}-> {d} — '{end}' 의 kind 가 {nodes[end][0]} 다 (있어야 할 값 {need[r]}, §E-2)")
    for (s, r, d) in sorted(edges):
        if s == d:
            fail(f"[7 자기참조] {s} -{r}-> {d}")
        if r == "같은 말이다" and not s < d:
            fail(f"[7 정규화] '같은 말이다' 는 src < dst 여야 한다 — {s} / {d} (§E-2)")

    # ── 출력 ────────────────────────────────────────────────────────────────
    print("k2b-graph — Ted 판정(2026-08-25) 기준 대비 적재 대조")
    print(f"  노드  기준 {len(std_nodes)} · DB {len(nodes)}")
    print(f"  엣지  기준 {len(std_edges)} · DB {len(edges)}")
    print(f"  등급⑥ 기준 {len(std_g6)} · DB {len(db_g6)}  (Ted 승인 목록 {len(APPROVED_G6)}줄 중 "
          f"{len(APPROVED_BUT_NOT_SEEDED)}줄은 F-10 ㈏ 로 미적재)")
    for kind in KINDS:
        print(f"  kind={kind:<5} {sum(1 for v in nodes.values() if v[0] == kind)}")
    for rel in RELATIONS:
        print(f"  relation={rel:<12} {sum(1 for (_, r, _) in edges if r == rel)}")

    if FAILS:
        print(f"::error::k2b-graph red — 위반 {len(FAILS)}건. 완료 정의는 '기준과 완전일치 · 미승인 ⑥ 0건' 이다.")
        for f in FAILS:
            print(f"   - {f}")
        return 1
    print("k2b-graph green — 노드·엣지 집합 완전일치 · 미승인 등급 ⑥ 0건 · 경계 규칙 7항 전부 통과.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
