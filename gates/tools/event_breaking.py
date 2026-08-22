#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""event-breaking 게이트의 판정 엔진 (WU-D2b).

이벤트 계약(JSON Schema 2020-12)의 **$defs 단위 파괴적 변경**을 검출한다.
oasdiff 는 OpenAPI 전용이라 이 자리를 볼 수 없다 (sessions/D2-events.md §7).

규칙 정본 = dev-package/sessions/D2b.md §2. 코드와 문서가 갈라지지 않게
규칙 코드(E01…·W01…)를 양쪽에서 같은 기호로 쓴다.

판정 관점: **소비자(consumer)** 다. 이벤트는 생산자가 밀고 소비자가 읽는 단방향 계약이라,
"이미 배포된 소비자가 다음 메시지에서 깨지는가"가 파괴 여부의 기준이다.

사용: event_breaking.py <base_dir> <rev_dir>
      exit 0 = 파괴적 변경 없음 / 1 = 있음 / 2 = 사용법 오류
"""
import json
import os
import sys

ERR, WARN = "ERR", "WARN"

RULES = {
    "E01": (ERR,  "이벤트 스키마 파일 제거"),
    "E02": (ERR,  "$def 제거(또는 이름 변경)"),
    "E03": (ERR,  "속성 제거"),
    "E04": (ERR,  "required 에 속성 추가"),
    "E05": (ERR,  "required 에서 속성 제거"),
    "E06": (ERR,  "enum 값 제거"),
    "E07": (ERR,  "type 축소"),
    "E08": (ERR,  "additionalProperties 조임"),
    "E09": (ERR,  "const 값 변경"),
    "E10": (ERR,  "값 제약 조임"),
    "E11": (ERR,  "oneOf/anyOf/allOf 분기 제거"),
    "E12": (ERR,  "$ref 대상 변경"),
    "E13": (ERR,  "format 추가·변경"),
    "E14": (ERR,  "$id 변경"),
    "W01": (WARN, "enum 값 추가"),
    "W02": (WARN, "선택 속성 추가"),
    "W03": (WARN, "새 $def·새 파일 추가"),
}

# 값이 커지면 조여지는 키워드 / 작아지면 조여지는 키워드
TIGHTEN_UP = ("minimum", "exclusiveMinimum", "minLength", "minItems", "minProperties", "minContains")
TIGHTEN_DOWN = ("maximum", "exclusiveMaximum", "maxLength", "maxItems", "maxProperties", "maxContains")

SUBSCHEMA_KEYS = ("items", "contains", "not", "propertyNames", "if", "then", "else",
                  "additionalProperties", "unevaluatedProperties", "unevaluatedItems")
LIST_KEYS = ("oneOf", "anyOf", "allOf", "prefixItems")
MAP_KEYS = ("properties", "$defs", "definitions", "patternProperties", "dependentSchemas")

findings = []


def add(code, path, detail):
    findings.append((code, RULES[code][0], path, detail))


def as_type_set(node):
    t = node.get("type")
    if t is None:
        return None
    return set(t) if isinstance(t, list) else {t}


def cmp_node(path, b, r):
    if isinstance(b, bool) or isinstance(r, bool):
        if b is True and r is False:
            add("E08", path, "true → false")
        return
    if not isinstance(b, dict) or not isinstance(r, dict):
        return

    # $ref
    if b.get("$ref") != r.get("$ref") and ("$ref" in b or "$ref" in r):
        add("E12", path, f'{b.get("$ref")!r} → {r.get("$ref")!r}')

    # const
    if "const" in b and b.get("const") != r.get("const"):
        add("E09", path, f'{b["const"]!r} → {r.get("const")!r}')

    # type
    bt, rt = as_type_set(b), as_type_set(r)
    if rt is not None:
        if bt is None:
            add("E07", path, f'(제약 없음) → {sorted(rt)}')
        elif bt - rt:
            add("E07", path, f'{sorted(bt)} → {sorted(rt)}')

    # enum
    if "enum" in b or "enum" in r:
        be, re_ = b.get("enum"), r.get("enum")
        if be is not None and re_ is None:
            pass  # 제약 완화
        elif be is None and re_ is not None:
            add("E10", path, f'enum 신설 {re_}')
        else:
            gone = [v for v in be if v not in re_]
            new = [v for v in re_ if v not in be]
            if gone:
                add("E06", path, f'제거된 값 {gone}')
            if new:
                add("W01", path, f'추가된 값 {new}')

    # required
    breq, rreq = set(b.get("required", [])), set(r.get("required", []))
    if rreq - breq:
        add("E04", path, f'추가 {sorted(rreq - breq)}')
    if breq - rreq:
        add("E05", path, f'제거 {sorted(breq - rreq)}')

    # additionalProperties 조임
    bap, rap = b.get("additionalProperties", True), r.get("additionalProperties", True)
    if bap is not False and rap is False:
        add("E08", path, f'{bap!r} → false')

    # format
    if b.get("format") != r.get("format") and "format" in r:
        add("E13", path, f'{b.get("format")!r} → {r["format"]!r}')

    # 수치·문자열 제약
    for k in TIGHTEN_UP:
        bv, rv = b.get(k), r.get(k)
        if rv is not None and (bv is None or rv > bv):
            add("E10", path + "/" + k, f'{bv} → {rv}')
    for k in TIGHTEN_DOWN:
        bv, rv = b.get(k), r.get(k)
        if rv is not None and (bv is None or rv < bv):
            add("E10", path + "/" + k, f'{bv} → {rv}')
    for k in ("pattern", "multipleOf"):
        if r.get(k) is not None and b.get(k) != r.get(k):
            add("E10", path + "/" + k, f'{b.get(k)!r} → {r[k]!r}')
    if r.get("uniqueItems") is True and b.get("uniqueItems") is not True:
        add("E10", path + "/uniqueItems", "false → true")

    # 하위 스키마 — 맵
    for mk in MAP_KEYS:
        bm, rm = b.get(mk) or {}, r.get(mk) or {}
        if not isinstance(bm, dict) or not isinstance(rm, dict):
            continue
        for name, sub in bm.items():
            p = f"{path}/{mk}/{name}"
            if name not in rm:
                add("E02" if mk in ("$defs", "definitions") else "E03", p, "제거됨")
            else:
                cmp_node(p, sub, rm[name])
        for name in rm:
            if name not in bm:
                code = "W03" if mk in ("$defs", "definitions") else "W02"
                # required 로 들어온 새 속성은 위 E04 가 이미 ERR 로 잡는다.
                add(code, f"{path}/{mk}/{name}", "추가됨")

    # 하위 스키마 — 리스트
    for lk in LIST_KEYS:
        bl, rl = b.get(lk), r.get(lk)
        if not isinstance(bl, list):
            continue
        if not isinstance(rl, list):
            add("E11", f"{path}/{lk}", "블록 자체가 사라짐")
            continue
        if len(rl) < len(bl):
            add("E11", f"{path}/{lk}", f'분기 {len(bl)} → {len(rl)}')
        for i in range(min(len(bl), len(rl))):
            cmp_node(f"{path}/{lk}/{i}", bl[i], rl[i])

    # 하위 스키마 — 단일
    for sk in SUBSCHEMA_KEYS:
        bs, rs = b.get(sk), r.get(sk)
        if isinstance(bs, (dict, bool)) and isinstance(rs, (dict, bool)):
            cmp_node(f"{path}/{sk}", bs, rs)


def load_dir(d):
    out = {}
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(d, fn), encoding="utf-8") as fh:
            out[fn] = json.load(fh)
    return out


def main(argv):
    if len(argv) != 3:
        print("usage: event_breaking.py <base_dir> <rev_dir>", file=sys.stderr)
        return 2
    base, rev = load_dir(argv[1]), load_dir(argv[2])

    for fn, bdoc in base.items():
        if fn not in rev:
            add("E01", fn, "파일이 사라졌다")
            continue
        rdoc = rev[fn]
        if bdoc.get("$id") != rdoc.get("$id"):
            add("E14", f"{fn}#/$id", f'{bdoc.get("$id")!r} → {rdoc.get("$id")!r}')
        cmp_node(fn + "#", bdoc, rdoc)
    for fn in rev:
        if fn not in base:
            add("W03", fn, "새 파일")

    errs = [f for f in findings if f[1] == ERR]
    warns = [f for f in findings if f[1] == WARN]
    for code, sev, path, detail in errs + warns:
        print(f"  [{sev}] {code} {RULES[code][1]} — {path} : {detail}")
    print(f"# 판정 — ERR {len(errs)}건 · WARN {len(warns)}건 "
          f"(규칙표 = dev-package/sessions/D2b.md §2)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
