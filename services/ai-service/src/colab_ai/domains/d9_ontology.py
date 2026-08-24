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
    """넓힌 결과. `terms` 가 실행기로 내려가고 나머지는 근거 한 줄의 재료다."""
    terms: tuple[str, ...]
    topic: str | None
    places: tuple[str, ...]
    methods: tuple[str, ...]


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
