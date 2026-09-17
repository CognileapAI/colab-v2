"""실무자 사례 14건의 **어휘 관문** 오라클 — `eval/k4-search/practitioner-lexical.json`.

`dev-package/intent/2026-09-18-practitioner-cases-ontology.md` §(v) 가 이 회차의 **첫 작업
단위**로 못 박은 자리다. 시드를 늘리기 **전에** red 를 내는 오라클을 세워, 적재 뒤의 green 이
「원래 되던 것」이 아니라 **전이**임을 파일 변경으로 증명한다.

**DB·모델·HTTP 를 부르지 않는다.** 대상은 `d9_ontology.expand()` 와 `expand_by_graph()` —
둘 다 순수 함수다. 사전과 그래프는 `db/ai/seed/*.sql` 의 `INSERT` 를 그대로 읽어 만든다.
시험이 제 사전을 손으로 적으면 **시드 변경을 영원히 못 잰다** — `k2-coverage-standard.tsv` 를
적재물에서 만들지 않는 것과 같은 규율이다(`k2_ontology_seed.sql` 축자 「기준을 적재물에서
만들면 커버리지 체크가 영원히 green 이 된다」). 여기서는 반대 방향이다: **오라클의 기대값**은
손으로 적은 JSON 이고, **사실**만 적재물에서 읽는다.

판정 둘을 함께 본다.
  ① `mode` 가 요구하는 상태 — `topic`·`place` 는 `hit`, `blocked` 는 `none`
  ② 픽스처의 `now` 가 **실측과 같은가** — 다르면 red 다. 그래서 상태가 바뀌면 픽스처를
     고쳐야 하고, red→green 이 커밋 diff 에 남는다
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from colab_ai.domains.d9_ontology import (
    ConceptEdge,
    ConceptGraph,
    ConceptNode,
    Dictionaries,
    expand,
    expand_by_graph,
)

ROOT = Path(__file__).resolve().parents[3]
SEED_DIR = ROOT / "db" / "ai" / "seed"
FIXTURE = ROOT / "eval" / "k4-search" / "practitioner-lexical.json"

#: `mode` 별로 **요구되는** 상태. blocked 는 「아무것도 넓히지 않는 것」이 정답이다.
REQUIRED = {"topic": "hit", "place": "hit", "blocked": "none"}


# ════════════════════════════════════════════════════════════════════════════
# 적재물 읽기 — 시드 SQL 의 INSERT 만 본다 (DDL·주석·ON CONFLICT 는 버린다)
# ════════════════════════════════════════════════════════════════════════════
def _strip_comments(text: str) -> str:
    """`--` 주석을 지운다. **문자열 안의 `--` 는 건드리지 않는다.**"""
    out: list[str] = []
    i, n, in_str = 0, len(text), False
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if ch == "'":
                if i + 1 < n and text[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                in_str = False
            i += 1
            continue
        if ch == "'":
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == "-" and i + 1 < n and text[i + 1] == "-":
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _statements(text: str) -> list[str]:
    stmts: list[str] = []
    buf: list[str] = []
    in_str = False
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if in_str:
            buf.append(ch)
            if ch == "'":
                if i + 1 < n and text[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                in_str = False
            i += 1
            continue
        if ch == "'":
            in_str = True
            buf.append(ch)
            i += 1
            continue
        if ch == ";":
            stmts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    if "".join(buf).strip():
        stmts.append("".join(buf))
    return stmts


def _literal(raw: str):
    raw = raw.strip()
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'")
    low = raw.lower()
    if low in ("true", "false"):
        return low == "true"
    if low == "null":
        return None
    try:
        return int(raw)
    except ValueError:
        return raw


def _tuples(rest: str) -> list[list]:
    """`VALUES` 뒤의 괄호 묶음들을 읽는다. `ON CONFLICT` 이후는 보지 않는다."""
    rows: list[list] = []
    i, n = 0, len(rest)
    while i < n:
        ch = rest[i]
        if ch == "(":
            fields: list[str] = []
            cur: list[str] = []
            depth, in_str = 1, False
            i += 1
            while i < n:
                c = rest[i]
                if in_str:
                    cur.append(c)
                    if c == "'":
                        if i + 1 < n and rest[i + 1] == "'":
                            cur.append("'")
                            i += 2
                            continue
                        in_str = False
                    i += 1
                    continue
                if c == "'":
                    in_str = True
                    cur.append(c)
                elif c == "(":
                    depth += 1
                    cur.append(c)
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        fields.append("".join(cur))
                        i += 1
                        break
                    cur.append(c)
                elif c == "," and depth == 1:
                    fields.append("".join(cur))
                    cur = []
                else:
                    cur.append(c)
                i += 1
            rows.append([_literal(f) for f in fields])
            continue
        if rest[i:].lstrip().upper().startswith("ON CONFLICT"):
            break
        i += 1
    return rows


def _seed_rows() -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = {}
    for path in sorted(SEED_DIR.glob("*.sql")):
        text = _strip_comments(path.read_text(encoding="utf-8"))
        for stmt in _statements(text):
            head = stmt.strip()
            if not head.upper().startswith("INSERT INTO"):
                continue
            after = head[len("INSERT INTO"):].lstrip()
            table, _, tail = after.partition("(")
            cols_raw, _, rest = tail.partition(")")
            cols = [c.strip() for c in cols_raw.split(",")]
            values_at = rest.upper().find("VALUES")
            if values_at < 0:
                continue
            for tup in _tuples(rest[values_at + len("VALUES"):]):
                rows.setdefault(table.strip(), []).append(dict(zip(cols, tup)))
    return rows


SEED = _seed_rows()


def _dictionaries() -> Dictionaries:
    return Dictionaries(
        method_terms=tuple(r["term"] for r in SEED.get("d9_method_term", ())),
        topic_synonyms=tuple((r["synonym"], r["topic"]) for r in SEED.get("d9_topic_synonym", ())),
        place_aliases=tuple((r["alias"], r["place_name"]) for r in SEED.get("d9_place_alias", ())),
    )


def _graph() -> ConceptGraph:
    return ConceptGraph(
        nodes=tuple(
            ConceptNode(concept_id=r["concept_id"], label=r["label"], expandable=bool(r["expandable"]))
            for r in SEED.get("d9_concept", ())
        ),
        edges=tuple(
            ConceptEdge(src=r["src"], relation=r["relation"], dst=r["dst"])
            for r in SEED.get("d9_concept_edge", ())
        ),
    )


DICTS = _dictionaries()
GRAPH = _graph()
FIXTURE_DATA = json.loads(FIXTURE.read_text(encoding="utf-8"))
CASES = FIXTURE_DATA["cases"]


def _measure(case: dict) -> str:
    term = case["term"]
    out = expand((term,), query=term, dictionaries=DICTS)
    graph_out = expand_by_graph((term,), query=term, graph=GRAPH)
    mode = case["mode"]
    if mode == "topic":
        return "hit" if out.topic == case["expectTopic"] else "miss"
    if mode == "place":
        return "hit" if case["expectPlace"] in out.places else "miss"
    if mode == "blocked":
        quiet = (out.terms == (term,) and out.topic is None
                 and out.places == () and out.methods == () and graph_out.terms == ())
        return "none" if quiet else "leak"
    raise AssertionError(f"알 수 없는 mode: {mode!r}")


# ════════════════════════════════════════════════════════════════════════════
# 판정
# ════════════════════════════════════════════════════════════════════════════
@pytest.mark.search_golden
def test_적재물을_실제로_읽었다() -> None:
    """파서가 조용히 빈 사전을 만들면 blocked 행이 **전부 공짜로 통과**한다 — fail-closed."""
    assert len(SEED.get("d9_method_term", ())) >= 13
    assert len(SEED.get("d9_topic_synonym", ())) >= 18
    assert len(SEED.get("d9_place_alias", ())) >= 4
    assert len(SEED.get("d9_concept", ())) >= 49
    assert len(SEED.get("d9_concept_edge", ())) >= 19


@pytest.mark.search_golden
def test_픽스처가_형식을_지킨다() -> None:
    ids = [c["id"] for c in CASES]
    assert ids, "픽스처가 비었다. 0건을 green 으로 세지 않는다."
    assert len(set(ids)) == len(ids), "사례 ID 가 중복됐다"
    for case in CASES:
        assert case["mode"] in REQUIRED, case
        assert case["term"].strip(), case
        if case["mode"] == "blocked":
            assert case.get("reason", "").strip(), f"{case['id']} 에 blocked 사유가 없다"


@pytest.mark.search_golden
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_어휘_관문(case: dict) -> None:
    status = _measure(case)
    assert status == REQUIRED[case["mode"]], (
        f"{case['id']} {case['term']!r} — 요구 {REQUIRED[case['mode']]} · 실측 {status}. "
        "시드 적재 전에는 이 줄이 red 인 것이 정상이다."
    )
    assert status == case["now"], (
        f"{case['id']} 의 픽스처 now={case['now']!r} 가 실측 {status!r} 과 다르다. "
        "상태가 바뀌었으면 practitioner-lexical.json 을 고친다 — 전이는 파일에 남아야 한다."
    )
