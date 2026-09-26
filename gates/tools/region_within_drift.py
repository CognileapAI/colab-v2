#!/usr/bin/env python3
"""region-within-drift — 검색 계약의 지역 포함 표(`regionWithin`)가 D9 그래프와 같은가.

정본 관계: 표의 원본은 D9 그래프다. `contracts/search/semantics.json` `regionWithin` 은 그 한 홉을
계약에 한 번 더 적은 것이고(intent `dev-package/intent/2026-09-26-region-containment-expansion.md`
결정 1 ㈎), 이 게이트가 둘이 갈라지는 것을 막는 **유일한 방어선**이다(intent 위험 절).

대조 입력(모두 커밋된 파일 · DB 무접속)
  · 표        COLAB_REGION_SEMANTICS  (기본 contracts/search/semantics.json)
  · 그래프    COLAB_REGION_GRAPH_TSV  (기본 db/ai/seed/k2b-graph-standard.tsv — 노드·엣지 기준 정본)
  · 지명 별칭 COLAB_REGION_ALIAS_DIR  (기본 db/ai/seed — `*.sql` 의 `INSERT INTO d9_place_alias` 행)

판정(red 1) — 표 항목마다
  ① 부모 식별자가 `regions` 에 있고 `place` 가 그 식별자의 질의 표기(키·별칭) 중 하나다.
  ② `place` 가 지명 노드로 있고 expandable=t 다(`d9_ontology.expand_by_graph` 의 경계와 같다).
  ③ 하위 = 그래프에서 `<하위> 안에 있다 <place>` 인 지명 노드 전부. 빠진 하위·남는 하위 모두 red.
     남는 하위가 거꾸로 `<place> 안에 있다 <하위>` 이면 **상향 엣지**로 이름 붙여 red.
  ④ 그래프 팬아웃이 6(`MAX_FANOUT`)을 넘는 부모는 표에 싣지 않는다 — 일부만 싣지 않고 전체를 뺀다.
  ⑤ 하위 별칭 = `d9_place_alias` 에서 place_name=하위 인 행(자기 자신 제외). `placeAliases` 도 같다.
  ⑥ 누락 부모 — `regions` 식별자가 가리키는 지명 노드가 확장 가능한 하위(1~6)를 가지면 표에 있어야 한다.
  대상 0건(표가 비었다)도 red 다.
준비 실패(78) — 입력 파일 부재·파싱 불가 · `regionWithin` 미선언 · 별칭 행 0건.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
INSIDE = "안에 있다"
PLACE = "지명"
#: `services/ai-service/src/colab_ai/domains/d9_ontology.py` `MAX_FANOUT` 과 같은 값.
MAX_FANOUT = 6
GATE = "region-within-drift"


class NotReady(Exception):
    pass


def compact(value) -> str:
    return re.sub(r"[\s_\-]+", "", str(value)).casefold()


def _path(env: str, default: str) -> pathlib.Path:
    raw = os.environ.get(env) or default
    path = pathlib.Path(raw)
    return path if path.is_absolute() else REPO / path


def load_graph(tsv: pathlib.Path) -> tuple[dict, list]:
    if not tsv.is_file():
        raise NotReady(f"그래프 기준 파일이 없다: {tsv}")
    nodes, edges = {}, []
    for number, line in enumerate(tsv.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if cols[0] == "node":
            if len(cols) < 6:
                raise NotReady(f"{tsv.name}:{number} node 열이 모자란다")
            nodes[cols[1]] = {"kind": cols[2], "label": cols[3], "expandable": cols[5] == "t"}
        elif cols[0] == "edge":
            if len(cols) < 4:
                raise NotReady(f"{tsv.name}:{number} edge 열이 모자란다")
            edges.append((cols[1], cols[2], cols[3]))
    if not nodes or not edges:
        raise NotReady(f"{tsv.name} 에서 노드·엣지를 읽지 못했다")
    return nodes, edges


def _tuples(text: str, start: int):
    """VALUES 뒤의 `( '..', '..', ... )` 들 — SQL 문자열 리터럴('' 이스케이프)을 따라 읽는다."""
    i, row, rows, depth = start, [], [], 0
    while i < len(text):
        ch = text[i]
        if text.startswith("--", i):
            nl = text.find("\n", i)
            i = len(text) if nl < 0 else nl + 1
            continue
        if ch == "'":
            j, buf = i + 1, []
            while True:
                if j >= len(text):
                    raise NotReady("닫히지 않은 SQL 문자열")
                if text[j] == "'":
                    if j + 1 < len(text) and text[j + 1] == "'":
                        buf.append("'"); j += 2; continue
                    break
                buf.append(text[j]); j += 1
            if depth == 1:
                row.append("".join(buf))
            i = j + 1
            continue
        if ch == "(":
            depth += 1
            if depth == 1:
                row = []
        elif ch == ")":
            if depth == 1:
                rows.append(row)
            depth -= 1
        elif ch == ";" and depth == 0:
            break
        elif depth == 0 and text.startswith("ON CONFLICT", i):
            break
        i += 1
    return rows


def load_aliases(directory: pathlib.Path) -> dict[str, str]:
    """alias → place_name. 같은 별칭이 서로 다른 지명으로 두 번 실리면 그것도 드리프트라 준비가 아니라 red 로 낸다."""
    if not directory.is_dir():
        raise NotReady(f"지명 별칭 시드 디렉터리가 없다: {directory}")
    out: dict[str, str] = {}
    conflicts = []
    head = re.compile(r"INSERT\s+INTO\s+d9_place_alias\s*\(([^)]*)\)\s*VALUES", re.I)
    for sql in sorted(directory.glob("*.sql")):
        text = sql.read_text(encoding="utf-8")
        for match in head.finditer(text):
            cols = [c.strip() for c in match.group(1).split(",")]
            if cols[:2] != ["alias", "place_name"]:
                raise NotReady(f"{sql.name}: d9_place_alias 열 순서가 (alias, place_name, …) 가 아니다")
            for row in _tuples(text, match.end()):
                alias, place = row[0], row[1]
                if alias in out and out[alias] != place:
                    conflicts.append(f"{alias!r} → {out[alias]!r} / {place!r} ({sql.name})")
                out[alias] = place
    if not out:
        raise NotReady(f"{directory} 의 *.sql 에서 d9_place_alias 행을 하나도 읽지 못했다")
    if conflicts:
        out["\0conflicts"] = " · ".join(conflicts)
    return out


def check(semantics: dict, nodes: dict, edges: list, aliases: dict) -> list[str]:
    errors: list[str] = []
    if "\0conflicts" in aliases:
        errors.append("d9_place_alias 한 별칭이 서로 다른 지명으로 실린다: " + aliases.pop("\0conflicts"))
    table = semantics["regionWithin"]
    regions = semantics.get("regions") or {}
    if not isinstance(table, dict) or not table:
        return errors + ["regionWithin 이 비었다 — 대상 0건은 통과가 아니다"]
    by_label: dict[str, list[str]] = {}
    for cid, node in nodes.items():
        if node["kind"] == PLACE:
            by_label.setdefault(node["label"], []).append(cid)

    def children_of(cid: str) -> set[str]:
        return {nodes[s]["label"] for s, rel, d in edges
                if rel == INSIDE and d == cid and s in nodes and nodes[s]["kind"] == PLACE}

    def parents_of(cid: str) -> set[str]:
        return {nodes[d]["label"] for s, rel, d in edges
                if rel == INSIDE and s == cid and d in nodes and nodes[d]["kind"] == PLACE}

    def own_aliases(label: str) -> set[str]:
        return {a for a, p in aliases.items() if p == label and a != label}

    for parent, entry in table.items():
        where = f"regionWithin.{parent}"
        if parent not in regions:
            errors.append(f"{where}: 부모가 regions 의 의미 식별자가 아니다")
            continue
        if not isinstance(entry, dict) or set(entry) - {"place", "placeAliases", "within"} \
                or not isinstance(entry.get("place"), str) or not isinstance(entry.get("within"), dict):
            errors.append(f"{where}: 모양이 {{place, placeAliases?, within}} 가 아니다")
            continue
        place = entry["place"]
        if compact(place) not in {compact(parent), *(compact(a) for a in regions[parent])}:
            errors.append(f"{where}: place {place!r} 가 이 식별자의 질의 표기(키·regions 별칭)가 아니다")
        ids = by_label.get(place, [])
        if len(ids) != 1:
            errors.append(f"{where}: 지명 노드 {place!r} 가 그래프에 {len(ids)}개다(정확히 1개여야 한다)")
            continue
        cid = ids[0]
        if not nodes[cid]["expandable"]:
            errors.append(f"{where}: {place!r}({cid}) 는 expandable=f — 표에 싣지 않는다")
        graph_kids = children_of(cid)
        table_kids = set(entry["within"])
        if len(graph_kids) > MAX_FANOUT:
            errors.append(f"{where}: 그래프 팬아웃 {len(graph_kids)} > {MAX_FANOUT} — 일부만 싣지 않고 부모 전체를 표에서 뺀다")
        if len(table_kids) > MAX_FANOUT:
            errors.append(f"{where}: 표의 하위 {len(table_kids)}개 > {MAX_FANOUT}")
        for kid in sorted(graph_kids - table_kids):
            errors.append(f"{where}: 빠진 하위 {kid!r} — 그래프에 `{kid} {INSIDE} {place}` 가 있다")
        uppers = parents_of(cid)
        for kid in sorted(table_kids - graph_kids):
            if kid in uppers:
                errors.append(f"{where}: 상향 엣지 {kid!r} — 그래프는 `{place} {INSIDE} {kid}`(상위)다. 표는 하향만 싣는다")
            else:
                errors.append(f"{where}: 남는 하위 {kid!r} — 그래프에 `{kid} {INSIDE} {place}` 엣지가 없다(깊이 1 · 직계만)")
        forbidden = {compact(place), *(compact(a) for a in regions[parent])}
        for kid, kid_aliases in entry["within"].items():
            if not isinstance(kid_aliases, list):
                errors.append(f"{where}.within.{kid}: 별칭이 목록이 아니다")
                continue
            want, got = own_aliases(kid), set(kid_aliases)
            for a in sorted(want - got):
                errors.append(f"{where}.within.{kid}: 빠진 별칭 {a!r}(d9_place_alias → {kid})")
            for a in sorted(got - want):
                errors.append(f"{where}.within.{kid}: 남는 별칭 {a!r} — d9_place_alias 에 {a} → {kid} 가 없다")
            if {compact(kid), *(compact(a) for a in kid_aliases)} & forbidden:
                errors.append(f"{where}.within.{kid}: 하위 표기가 부모 표기와 겹친다(상향 누수)")
        want, got = own_aliases(place), set(entry.get("placeAliases", []))
        for a in sorted(want - got):
            errors.append(f"{where}.placeAliases: 빠진 별칭 {a!r}(d9_place_alias → {place})")
        for a in sorted(got - want):
            errors.append(f"{where}.placeAliases: 남는 별칭 {a!r} — d9_place_alias 에 {a} → {place} 가 없다")

    # ⑥ 누락 부모 — 질의 표기가 지명 노드를 가리키고 그 노드가 펼 수 있는데 표에 없다.
    for rid, labels in regions.items():
        if rid in table:
            continue
        for label in {rid, *labels}:
            for cid in by_label.get(label, []):
                kids = children_of(cid)
                if nodes[cid]["expandable"] and 0 < len(kids) <= MAX_FANOUT:
                    errors.append(f"regions.{rid}: {label!r} 가 하위 {sorted(kids)} 를 갖는데 regionWithin 에 없다")
    return errors


def main() -> int:
    try:
        sem_path = _path("COLAB_REGION_SEMANTICS", "contracts/search/semantics.json")
        if not sem_path.is_file():
            raise NotReady(f"검색 계약이 없다: {sem_path}")
        try:
            semantics = json.loads(sem_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise NotReady(f"{sem_path.name} 를 JSON 으로 읽지 못했다: {exc}") from None
        if "regionWithin" not in semantics:
            print(f"::gate-readiness-failure::gate={GATE}|cause=입력미선언|detail={sem_path.name} 에 regionWithin 이 없다")
            return 78
        nodes, edges = load_graph(_path("COLAB_REGION_GRAPH_TSV", "db/ai/seed/k2b-graph-standard.tsv"))
        aliases = load_aliases(_path("COLAB_REGION_ALIAS_DIR", "db/ai/seed"))
    except NotReady as exc:
        print(f"::gate-readiness-failure::gate={GATE}|detail={exc}")
        return 78
    errors = check(semantics, nodes, edges, aliases)
    if errors:
        for error in errors:
            print(f"::gate-failure:: {GATE}: {error}")
        print(f"{GATE} red(판정) — {len(errors)}건. 그래프(k2b-graph-standard.tsv · d9_place_alias)와 "
              "contracts/search/semantics.json regionWithin 을 같은 커밋에서 맞춘다.")
        return 1
    table = semantics["regionWithin"]
    kids = sum(len(e["within"]) for e in table.values())
    print(f"{GATE} green — 부모 {len(table)} · 직계 하위 {kids} · 별칭 행 {len(aliases)} 대조 "
          f"(하향 · 깊이 1 · 팬아웃 ≤ {MAX_FANOUT} · 별칭 일치)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
