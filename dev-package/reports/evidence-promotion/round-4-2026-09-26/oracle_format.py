"""오라클(`eval/k4-search/practitioner-conditions.json`)의 손 서식을 그대로 다시 쓴다.

최상위 객체와 `modes`·사례 객체는 키 한 줄씩, probe 목록은 probe 한 줄씩, 나머지 목록은 한 줄이다.
재채점 스크립트가 JSON 으로 고친 뒤 이 서식으로 써서 diff 를 바뀐 줄로 한정한다.
"""
from __future__ import annotations

import json

EXPANDED_OBJECT_LISTS = ("cases",)


def _one(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _object(obj: dict, level: int) -> list[str]:
    pad = "  " * (level + 1)
    items = list(obj.items())
    out = []
    for index, (key, value) in enumerate(items):
        tail = "," if index < len(items) - 1 else ""
        head = f"{pad}{_one(key)}: "
        if isinstance(value, dict) and level == 0:
            out.append(head + "{")
            out.extend(_object(value, level + 1))
            out.append(pad + "}" + tail)
        elif isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
            out.append(head + "[")
            inner = "  " * (level + 2)
            for i, item in enumerate(value):
                comma = "," if i < len(value) - 1 else ""
                if key in EXPANDED_OBJECT_LISTS:
                    out.append(inner + "{")
                    out.extend(_object(item, level + 2))
                    out.append(inner + "}" + comma)
                else:
                    out.append(inner + _one(item) + comma)
            out.append(pad + "]" + tail)
        else:
            out.append(head + _one(value) + tail)
    return out


def dumps(obj: dict) -> str:
    return "\n".join(["{", *_object(obj, 0), "}"]) + "\n"
