#!/usr/bin/env python3
"""CI paths-filter `harness` 대조 — `dorny/paths-filter` 를 로컬에서 돌릴 수 없는 자리를 메운다.

무엇을 해소하나:
  `.github/workflows/ci.yml` 의 필터는 **GitHub 위에서만** 평가된다. 그래서 「필터를 적었다」와
  「그 필터가 의도한 경로를 잡는다」가 갈릴 수 있고, 실제로 이 레포에는 선언만 되고 소비처가
  0개인 출력(`outputs.frontend`)이 있어 `frontend/` 만 바꾼 PR 이 게이트 잡 0개로 병합된
  선례가 있다(`ci.yml` 「프런트 게이트」 주석 · 2026-09-03 코드리뷰 #6).

무엇을 재나 (일곱):
  ㈎ `changes` 잡의 필터 블록에 `harness` 가 있다
  ㈏ `harness` 패턴 집합이 정본과 축자 일치 — CLAUDE.md · .claude/skills/** · hooks/** · agents/**
  ㈐ 잡히는 것 — `CLAUDE.md` · `.claude/skills/x/SKILL.md` · `.claude/hooks/h.sh` · `.claude/agents/a.md`
  ㈑ 안 잡히는 것 — `frontend/src/a.tsx` · `services/core-api/x.py` (제품 경로가 하네스를 깨우지 않는다)
  ㈒ `changes` 잡 `outputs` 에 `harness` 항목이 있다(필터만 있고 출력이 없으면 소비처가 못 읽는다)
  ㈓ 잡 `harness-eval` 이 `needs.changes.outputs.harness == 'true'` 로 걸린다
  ㈔ 그 잡에 `continue-on-error` 가 없고 시크릿은 **참조만** 있다(값 기입 0)

⚠ **이 대조는 근사다.** 여기서 재는 것은 glob 문법의 뜻이고, `dorny/paths-filter` 가 실제 PR 의
  변경 목록에 그것을 어떻게 적용하는지는 **`[미상]`** 이다(로컬 실행 불가 · `act` 부재).
  근사라는 사실을 출력에 그대로 적는다 — 안 보이는 근사는 거짓말이 된다.

exit — 0 green · 1 red(판정) · 78 red(준비 · 파일·PyYAML 부재).
"""
from __future__ import annotations

import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CI_PATH = os.environ.get("COLAB_CI_WORKFLOW") or os.path.join(
    REPO_ROOT, ".github", "workflows", "ci.yml"
)

# 정본 = intent Q2 축자(트리거 4경로). 여기서 늘리거나 줄이지 않는다.
WANT_PATTERNS = {
    "CLAUDE.md",
    ".claude/skills/**",
    ".claude/hooks/**",
    ".claude/agents/**",
}
MUST_MATCH = [
    "CLAUDE.md",
    ".claude/skills/colab-v2-work/SKILL.md",
    ".claude/hooks/bootstrap-diet.sh",
    ".claude/agents/lane-worker.md",
]
MUST_NOT_MATCH = [
    "frontend/src/a.tsx",
    "services/core-api/src/colab_core/app.py",
    "dev-package/03-HANDOFF.md",
]
JOB = "harness-eval"


def ready_red(missing: str, detail: str) -> None:
    print(
        "::gate-readiness-failure::gate=ci-filter-check|cause=입력미선언|"
        "missing=%s|detail=%s" % (missing, detail)
    )
    print("::error::ci-filter-check red(준비) — 판정하지 못했다. 판정 red 가 아니다.")
    print("   선언되지 않은/없는 것: %s" % missing)
    print("   %s" % detail)
    sys.exit(78)


def glob_to_re(pat: str) -> "re.Pattern[str]":
    """picomatch 근사 — `**` 는 경로 구분자를 넘고, `*`·`?` 는 넘지 않는다."""
    out, i = [], 0
    while i < len(pat):
        c = pat[i]
        if pat.startswith("**", i):
            out.append(".*")
            i += 2
            if pat.startswith("/", i):  # `a/**/b` 의 가운데 슬래시를 선택적으로 먹는다
                out.append("/?")
                i += 1
            continue
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def main() -> int:
    try:
        import yaml  # noqa: WPS433
    except Exception as exc:  # pragma: no cover
        ready_red("PyYAML", "ci.yml 을 파싱할 수 없다 (%s). pip install pyyaml" % exc)
    if not os.path.exists(CI_PATH):
        ready_red(CI_PATH, "워크플로 파일이 이 체크아웃에 없다.")

    doc = yaml.safe_load(open(CI_PATH, encoding="utf-8"))
    jobs = (doc or {}).get("jobs") or {}
    changes = jobs.get("changes") or {}

    filters_raw = None
    for step in changes.get("steps") or []:
        with_block = step.get("with") or {}
        if "filters" in with_block:
            filters_raw = with_block["filters"]
            break
    if filters_raw is None:
        print("::error::ci-filter-check red(판정) — `changes` 잡에서 paths-filter 의 `filters` 블록을 찾지 못했다.")
        return 1
    filters = yaml.safe_load(filters_raw) or {}

    fails: list[str] = []

    # ㈎·㈏ 필터 존재와 패턴 집합
    if "harness" not in filters:
        fails.append("㈎ 필터 `harness` 가 없다 — 지침 4경로의 변경이 아무 잡도 깨우지 않는다.")
        got = set()
    else:
        got = set(filters["harness"] or [])
        if got != WANT_PATTERNS:
            fails.append(
                "㈏ `harness` 패턴이 정본과 다르다 · 남음 %s · 모자람 %s"
                % (sorted(got - WANT_PATTERNS), sorted(WANT_PATTERNS - got))
            )

    regexes = [glob_to_re(p) for p in sorted(got)]

    def matched(path: str) -> bool:
        return any(r.match(path) for r in regexes)

    for path in MUST_MATCH:
        if not matched(path):
            fails.append("㈐ `%s` 가 `harness` 에 안 잡힌다 — 지침이 바뀌어도 잡이 안 깨어난다." % path)
    for path in MUST_NOT_MATCH:
        if matched(path):
            fails.append("㈑ `%s` 가 `harness` 에 잡힌다 — 제품 변경이 모델 호출 잡을 깨운다." % path)

    # ㈒ outputs
    outputs = changes.get("outputs") or {}
    if "harness" not in outputs:
        fails.append("㈒ `changes` 잡 `outputs` 에 `harness` 가 없다 — 필터가 있어도 소비처가 못 읽는다.")

    # ㈓·㈔ 잡
    job = jobs.get(JOB)
    if job is None:
        fails.append("㈓ 잡 `%s` 가 없다." % JOB)
    else:
        cond = str(job.get("if") or "")
        if "needs.changes.outputs.harness" not in cond:
            fails.append("㈓ 잡 `%s` 의 `if` 가 `needs.changes.outputs.harness` 를 안 본다: %r" % (JOB, cond))
        if "continue-on-error" in job:
            fails.append("㈔ 잡 `%s` 에 `continue-on-error` 가 있다 — red 를 통과로 접는 자리다." % JOB)
        blob = yaml.safe_dump(job, allow_unicode=True)
        if "secrets.ANTHROPIC_API_KEY" not in blob:
            fails.append("㈔ 잡 `%s` 가 `secrets.ANTHROPIC_API_KEY` 를 참조하지 않는다." % JOB)
        for step in job.get("steps") or []:
            if str(step.get("continue-on-error", "")).lower() == "true":
                fails.append("㈔ 잡 `%s` 의 스텝에 `continue-on-error: true` 가 있다." % JOB)
        if re.search(r"sk-[A-Za-z0-9_-]{8,}", blob):
            fails.append("㈔ 잡 `%s` 에 시크릿 **값**으로 보이는 문자열이 있다 — 참조만 둔다." % JOB)

    if fails:
        print("::error::ci-filter-check red(판정) — CI 필터·잡 대조 %d건이 기대와 다르다." % len(fails))
        for f in fails:
            print("     - " + f)
        return 1

    print(
        "ci-filter-check green — 필터 `harness` 패턴 %d개 · 잡히는 경로 %d건 · 안 잡히는 경로 %d건 · "
        "outputs.harness 있음 · 잡 `%s` 조건·시크릿 참조 확인 · continue-on-error 0."
        % (len(got), len(MUST_MATCH), len(MUST_NOT_MATCH), JOB)
    )
    print(
        "   ⚠ 근사다 — 여기서 잰 것은 glob 문법의 뜻이고, `dorny/paths-filter` 가 실제 PR 에서 "
        "이 필터를 어떻게 평가하는지는 **[미상]** 이다(로컬 실행 불가 · `act` 부재)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
