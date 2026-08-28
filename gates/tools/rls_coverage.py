#!/usr/bin/env python3
"""rls-coverage 판정 코어 — DB 에서 뽑아낸 사실(facts)만 보고 판정한다.

DB 접속·컨테이너 기동은 rls-coverage.sh 가 한다. 판정을 여기로 떼어 놓은 이유:
**판정 로직 자체의 fail-closed 증명이 도커 사고에 걸려 넘어지면 안 되기 때문이다.**
selftest 는 합성 facts 로 이 파일을 직접 때린다.

강제하는 것
  CLAUDE.md §3-5      모든 조회에 연구실 경계가 자동 주입된다 (스코프 커널 + RLS + 음성 테스트)
  PLAN-SoT §9-㉖ · P-34  잠금 두 층 — ① 연구실 경계 = RLS ③ 파일 본체 = RLS(허용자 목록 + 만료일)

facts 형식 (TSV, 한 줄 = 한 테이블)
  <체인>\t<테이블>\t<rowsecurity t|f>\t<forced t|f>\t<정책 이름들, 쉼표 구분(없으면 빈칸)>

원칙 (CLAUDE.md §4): 어떤 체인의 테이블이 0건이면 red. "RLS 누락이 없다"와 "테이블이 없다"는 다른 사실이다.
"""
from __future__ import annotations

import os
import pathlib
import sys
import tomllib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG = pathlib.Path(
    os.environ.get("COLAB_RLS_ALLOWLIST") or (REPO_ROOT / "gates/config/rls-allowlist.toml")
)
CHAINS = ("platform", "ai")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: rls_coverage.py <facts.tsv>", file=sys.stderr)
        return 2
    facts_path = pathlib.Path(argv[1])
    if not CONFIG.is_file():
        print(f"::error::rls-coverage red — allow-list 설정이 없다: {CONFIG}")
        return 1
    cfg = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    naming = cfg["policy_naming"]
    lab_policy, body_policy = naming["lab_boundary"], naming["body_access"]

    if not facts_path.is_file():
        print(f"::error::rls-coverage red — facts 파일이 없다: {facts_path}")
        return 1

    facts: dict[str, dict[str, tuple[bool, bool, set[str]]]] = {c: {} for c in CHAINS}
    for lineno, line in enumerate(facts_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 5:
            print(f"::error::rls-coverage red — facts {lineno}행 형식 오류: {line!r}")
            return 1
        chain, table, rls, forced, policies = parts
        if chain not in facts:
            print(f"::error::rls-coverage red — 모르는 체인 '{chain}' (facts {lineno}행)")
            return 1
        facts[chain][table] = (
            rls == "t",
            forced == "t",
            {p for p in policies.split(",") if p},
        )

    errors: list[str] = []
    for chain in CHAINS:
        sec = cfg.get(chain, {})
        allow = set(sec.get("allow_no_rls", []))
        body = set(sec.get("body_tables", []))
        tables = facts[chain]

        if not tables:
            errors.append(
                f"db/{chain} — 테이블이 0건이다. 대상 0건은 통과가 아니다 — "
                f"'RLS 누락이 없다'와 '테이블이 없다'는 다른 사실이다 (CLAUDE.md §4). "
                f"v1 CI 가 DB 없이 돌아 RLS 테스트를 green-by-skip 한 실패가 정확히 이것이다."
            )
            continue

        # 낡은 면제 — 목록에만 있고 DB 엔 없는 테이블. 조용한 구멍이 되기 전에 잡는다.
        for t in sorted(allow - set(tables)):
            errors.append(
                f"db/{chain} — allow_no_rls 의 '{t}' 가 실제 스키마에 없다. "
                f"낡은 면제는 나중에 같은 이름의 테이블이 생기는 순간 구멍이 된다. 목록에서 지운다."
            )
        for t in sorted(body - set(tables)):
            errors.append(f"db/{chain} — body_tables 의 '{t}' 가 실제 스키마에 없다.")

        for table in sorted(tables):
            rls, forced, policies = tables[table]
            if table in allow:
                if table in body:
                    errors.append(
                        f"db/{chain}.{table} — 본체 테이블이 allow_no_rls 에도 있다. 면제와 필수를 동시에 적을 수 없다."
                    )
                print(f"# db/{chain}.{table}: RLS 면제(allow-list) — rls={'on' if rls else 'off'}")
                continue
            if not rls:
                errors.append(
                    f"db/{chain}.{table} — RLS 가 꺼져 있고 allow-list 에도 없다. "
                    f"연구실 경계가 이 테이블에는 주입되지 않는다 (CLAUDE.md §3-5)."
                )
                continue
            if not forced:
                errors.append(
                    f"db/{chain}.{table} — RLS 는 켰지만 FORCE 가 아니다. "
                    f"테이블 소유자로 접속하면 정책이 통째로 무시된다 — ENABLE 만으로는 경계가 아니다."
                )
            if lab_policy not in policies:
                errors.append(
                    f"db/{chain}.{table} — 연구실 경계 정책 '{lab_policy}' 이 없다"
                    f"{' (걸린 정책: ' + ', '.join(sorted(policies)) + ')' if policies else ' (정책 0건)'}."
                )
            if table in body and body_policy not in policies:
                errors.append(
                    f"db/{chain}.{table} — 파일 본체 테이블인데 본체 정책 '{body_policy}' 이 없다. "
                    f"허용자 목록 + 만료일은 DB 가 거부해야 한다 (PLAN-SoT §9-㉖ · P-34 ③)."
                )
            extra = policies - {lab_policy, body_policy}
            note = f" · 그 밖의 정책: {', '.join(sorted(extra))}" if extra else ""
            print(
                f"# db/{chain}.{table}: rls={'on' if rls else 'off'} force={'on' if forced else 'off'} "
                f"정책={len(policies)}{note}"
            )

    if errors:
        print("::error::rls-coverage red —")
        for e in errors:
            print(f"   - {e}")
        print(
            "   allow-list 정본은 gates/config/rls-allowlist.toml 하나뿐이다. 스크립트에 목록을 다시 적지 않는다.\n"
            "   게이트를 green 으로 만들려고 테이블을 allow-list 에 밀어 넣는 것은 검사 대상을 줄이는 짓이다 (CLAUDE.md §4)."
        )
        return 1
    print("rls-coverage green — allow-list 밖 테이블 전부 FORCE RLS + 연구실 경계 정책, 본체 테이블은 본체 정책까지.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
