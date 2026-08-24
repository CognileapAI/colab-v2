"""D9 Ontology & Knowledge Graph. 수문학 도메인 소유.

**여기 있는 것은 사전 3종을 읽는 순수 규칙뿐이다** (`ONTOLOGY-SCOPE §④-4` — 「D9 는 세 개의
작은 사전이다. 그래프가 아니다」). 그래프 탐색·임베딩은 여기 없다 — 전자는 `K4-b`,
후자는 stage 1 밖이다 (`〈81〉`·`〈82〉`).

**넓히는 규칙이 결정적이어야 한다.** `〈72〉-㉮` 가 매칭·순위를 tsvector + 사전 3종에 맡긴
이유가 재현성이고, 넓히는 단계가 흔들리면 그 재현성이 첫 걸음에서 깨진다. 그래서
  · 순서는 **질의에 나온 순서**를 따른다 (집합이 아니라 튜플이다)
  · 같은 말은 **한 번만** 남는다
  · 사전에 없으면 **아무것도 만들지 않는다** (`㊴-②` — 지어내지 않는다)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dictionaries:
    """적재된 사전 3종의 스냅숏. K2 시드 실측 = 13 · 5 · 4 = 22행."""
    method_terms: tuple[str, ...]
    topic_synonyms: tuple[tuple[str, str], ...]      # (질의어, 주제 4값)
    place_aliases: tuple[tuple[str, str], ...]       # (별칭, 정본 표기)


@dataclass(frozen=True)
class Expansion:
    """넓힌 결과. `terms` 가 실행기로 내려가고 나머지는 근거 한 줄의 재료다.

    `graph_hops` 는 `K4-b` 가 더한 칸이다 — **그래프가 데려온 말과 그 엣지**이고,
    사전만 돌았으면 빈 튜플이다. 기본값을 둔 것은 순수 함수 `expand` 가 그래프를
    모르기 때문이지 그래프가 선택 사항이어서가 아니다.
    """
    terms: tuple[str, ...]
    topic: str | None
    places: tuple[str, ...]
    methods: tuple[str, ...]
    graph_hops: tuple["GraphHop", ...] = ()


def _dedup(values) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for v in values:
        v = (v or "").strip()
        if v:
            seen.setdefault(v, None)
    return tuple(seen)


def expand(terms: tuple[str, ...], *, query: str, dictionaries: Dictionaries) -> Expansion:
    """검색어를 사전 3종으로 넓힌다.

    **낱말과 질의 원문을 함께 본다.** 「낙동강 유역」은 두 낱말이라 낱말 단위로만 보면
    영원히 안 만나기 때문이다 (`ts_config='simple'` 은 공백에서 자른다 — `〈81〉-㉲`).
    원문 훑기는 **긴 표제어부터** 본다: 짧은 것이 먼저 먹으면 긴 별칭이 못 잡힌다.
    """
    q = query or ""
    out: list[str] = list(terms)
    topic: str | None = None
    places: list[str] = []
    methods: list[str] = []

    def _hit(key: str) -> bool:
        return key in terms or (key in q)

    # 주제는 **질의에서 가장 먼저 나온 동의어**가 정한다. 한 질의에 둘이 걸리는 규칙은
    # 정본에 없으므로(`d9_topic_synonym` 주석 — 다의어 규칙 [정본 무근거]) 사전 파일의
    # 줄 순서 같은 우연이 답을 정하지 않게 **위치로** 못 박는다.
    candidates: list[tuple[int, str]] = []
    for synonym, mapped in sorted(dictionaries.topic_synonyms, key=lambda r: (-len(r[0]), r[0])):
        if not _hit(synonym):
            continue
        out.append(synonym)
        out.append(mapped)
        pos = terms.index(synonym) if synonym in terms else len(terms) + q.find(synonym)
        candidates.append((pos, mapped))
    if candidates:
        topic = min(candidates, key=lambda c: c[0])[1]

    for alias, place in sorted(dictionaries.place_aliases, key=lambda r: (-len(r[0]), r[0])):
        if _hit(alias):
            out.append(alias)
            if place not in places:
                places.append(place)
            out.append(place)

    for term in sorted(dictionaries.method_terms, key=lambda t: (-len(t), t)):
        if _hit(term):
            out.append(term)
            if term not in methods:
                methods.append(term)

    return Expansion(terms=_dedup(out), topic=topic,
                     places=tuple(places), methods=tuple(methods))


# ════════════════════════════════════════════════════════════════════════════
# K4-b — 개념 그래프 증강 (`PLAN-SoT §9-〈90〉` · `sessions/K1b-ONTOLOGY-CONTENT §D-6`)
#
# **그래프는 검색어 집합만 넓힌다. 순위에 손대지 않는다** (`〈72〉-㉮`) — 매기는 것은
# core-api 의 `ts_rank_cd` 이고, 여기서 나가는 것은 말 몇 개와 그 말이 어느 엣지로
# 왔는지뿐이다. 순위가 이 층으로 올라오면 같은 질의가 때마다 다른 답을 낸다.
#
# **확장은 그대로 두면 검색을 나쁘게 만든다.** §D-6 이 그 자리를 둘 보였다 —
# 「전처리」에 자식을 달고 깊이 제한 없이 타면 관련도 막대가 전부 같은 길이가 되고,
# 상향으로 타면 `Bilinear` 하나를 물었는데 형제 셋이 따라와 4건 중 3건이 오답이 된다.
# 그래서 경계 넷이 **선택이 아니라 구조**로 들어온다 (Ted `F-11` 승인).
#
#   ① 하향 전용   질의어가 **상위**일 때만 하위로 편다. `같은 말이다` 만 양방향이다
#   ② 깊이 1      한 홉이다. 전이 폐포를 만들지 않는다
#   ③ 팬아웃 상한 직계 하위가 `MAX_FANOUT` 을 넘으면 **그 질의어는 확장하지 않는다**
#   ④ 부모 금지   `expandable=false` 인 노드는 `~의 한 가지다` 의 도착이 될 수 없다
#
# 그리고 다섯째 — **넓힌 말마다 `GraphHop` 이 붙는다.** 「적을 수 없으면 확장하지
# 않는다」는 §D-6 의 마지막 안전장치이고, 근거 한 줄이 「‘재격자화’의 한 가지인
# ‘Nearest’」로 **엣지를 이름으로** 말하는 재료다.
# ════════════════════════════════════════════════════════════════════════════

#: `d9_concept_edge.relation` CHECK 3값. **여기서 새로 정하는 것이 아니라** 정본
#: (`db/ai/schema.sql`)이 적어 둔 것을 코드 쪽에 한 번 더 옮긴 것이다.
SAME_AS = "같은 말이다"
KIND_OF = "~의 한 가지다"
INSIDE = "안에 있다"

#: 방향이 있는 관계 둘. **`src` 가 하위이고 `dst` 가 상위다** — 확장은 `dst → src` 로만 간다.
HIERARCHY = (KIND_OF, INSIDE)

#: 경계 ③. 권고값 6 (`§D-6`). **넓은 말일수록 확장이 무가치하다**는 성질을 규칙으로 만든 것이다.
#: 늘리려면 평가셋에 회귀 케이스를 먼저 넣는다.
MAX_FANOUT = 6


@dataclass(frozen=True)
class ConceptNode:
    """`d9_concept` 한 행 중 확장이 쓰는 세 값. `expandable` 이 경계 ④ 의 실물이다."""
    concept_id: str
    label: str
    expandable: bool


@dataclass(frozen=True)
class ConceptEdge:
    """`d9_concept_edge` 한 행. `src` = 하위/부분, `dst` = 상위/전체."""
    src: str
    relation: str
    dst: str


@dataclass(frozen=True)
class ConceptGraph:
    """적재된 그래프의 스냅숏. K2b 시드 실측 = 노드 49 · 엣지 19."""
    nodes: tuple[ConceptNode, ...]
    edges: tuple[ConceptEdge, ...]


@dataclass(frozen=True)
class GraphHop:
    """넓힌 말 하나와 **그 말을 데려온 엣지**. 근거 한 줄이 이것을 읽는다."""
    term: str
    relation: str
    parent: str


@dataclass(frozen=True)
class GraphExpansion:
    """`terms` 는 **새로 붙은 말만**이다 — 이미 있던 말은 여기 없다.

    `hops` 는 `terms` 와 **한 칸씩 짝**이다. 길이가 다르면 근거를 못 적는 말이 생긴 것이고,
    그것이 §D-6 의 다섯째 안전장치가 금지한 상태다.
    """
    terms: tuple[str, ...]
    hops: tuple[GraphHop, ...]


def _scan_order(nodes):
    """**긴 표제어부터** 본다 — 짧은 것이 먼저 먹으면 긴 이름이 못 잡힌다.

    사전 확장(`expand`)과 같은 규칙이고, 같은 이유로 **시드 파일의 줄 순서가 결과를
    정하지 않는다.** 길이가 같으면 표제어 사전순, 그래도 같으면 식별자 사전순이다.
    """
    return sorted(nodes, key=lambda n: (-len(n.label), n.label, n.concept_id))


def expand_by_graph(terms: tuple[str, ...], *, query: str,
                    graph: ConceptGraph) -> GraphExpansion:
    """질의에 나타난 **상위 개념**을 그 하위로 한 홉 편다. 경계 넷을 그대로 지킨다."""
    q = query or ""
    known = set(terms)
    by_id = {n.concept_id: n for n in graph.nodes}

    # 하향 관계: 상위(dst) → 하위(src) 목록. **정렬해 둔다** — 팬아웃 판정과 출력 순서가
    # 둘 다 이 목록을 읽으므로 결정성이 여기서 끝나야 한다.
    children: dict[str, list[tuple[str, str]]] = {}
    synonyms: dict[str, list[str]] = {}
    for e in graph.edges:
        if e.src not in by_id or e.dst not in by_id:
            continue                                  # 반쪽 엣지는 없는 것으로 본다
        if e.relation in HIERARCHY:
            children.setdefault(e.dst, []).append((e.src, e.relation))
        elif e.relation == SAME_AS:
            synonyms.setdefault(e.src, []).append(e.dst)   # 대칭 — 양쪽 다 단다
            synonyms.setdefault(e.dst, []).append(e.src)
    for bucket in children.values():
        bucket.sort()
    for syn_bucket in synonyms.values():
        syn_bucket.sort()

    out: list[str] = []
    hops: list[GraphHop] = []

    def _add(label: str, relation: str, parent: str) -> None:
        label = (label or "").strip()
        if not label or label in known:
            return
        known.add(label)
        out.append(label)
        hops.append(GraphHop(term=label, relation=relation, parent=parent))

    for node in _scan_order(graph.nodes):
        # 사전 확장과 같은 판정 — 낱말로도 보고 질의 원문으로도 본다. 「낙동강 유역」처럼
        # 두 낱말인 표제어가 토큰 단위로는 영원히 안 만나기 때문이다 (`〈81〉-㉲`).
        if node.label not in terms and node.label not in q:
            continue

        # ── 경계 ①④③ — 하향 확장 ────────────────────────────────────────────
        kids = children.get(node.concept_id, ())
        if node.expandable and kids and len(kids) <= MAX_FANOUT:
            for kid_id, relation in kids:
                kid = by_id[kid_id]
                # ── 경계 ② — 여기서 멈춘다. 자식의 자식을 부르지 않는다 ──────
                _add(kid.label, relation, node.label)
                # 자식의 **표기 변형**은 새 홉이 아니라 같은 자식의 다른 이름이다.
                # 그래서 근거도 자식의 것을 그대로 물려받는다 (§D-2 의 예문이 그 모양이다).
                for syn_id in synonyms.get(kid_id, ()):
                    _add(by_id[syn_id].label, relation, node.label)

        # ── 경계 ① 의 예외 — `같은 말이다` 만 양방향이다 ─────────────────────
        # 금지 목록도 여기서는 막지 않는다. 금지된 것은 `~의 한 가지다` 의 **도착**이지
        # 표기 변형이 아니다 (§D-6 경계 4 의 글자 그대로).
        for syn_id in synonyms.get(node.concept_id, ()):
            _add(by_id[syn_id].label, SAME_AS, node.label)

    return GraphExpansion(terms=tuple(out), hops=tuple(hops))
