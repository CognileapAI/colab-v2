#!/usr/bin/env python3
"""work-item-consistency — 개발 항목 상태의 대장과 산문이 어긋나는지 본다.

왜 있나
  이 레포는 「관례를 두지 않는다, 기계가 강제한다」로 서 있는데 **상태 관리만 그 밖에 있었다.**
  상태가 산문 세 곳(`03-HANDOFF §1` · `WORK-UNITS §10~§11` · `PLAN-SoT §9`)에 흩어져
  사람 기억으로 동기화됐고, 한 회차에서만 아래가 동시에 관측됐다 —

    · 완주 체크리스트가 여러 항목을 완료로 적었는데 진실원은 미완이었다
    · 단계 정의에는 열 항목인데 순서표에는 넷뿐이었다
    · 「하지 않기로 한 것」(⏸)이 착수 후보 표에 재등장했다
    · 같은 항목이 한 파일에서는 미착수, 다른 파일에서는 완료였다
    · 완료 정의 없이 항목 둘이 편성됐다
    · 기한 조건이 발동했는데 아무도 열지 않았다

  판정(2026-08-28 Ted) = **기계가 읽는 대장 파일을 상태의 유일한 원본으로 두고,
  검사기가 산문 문서와의 불일치를 차단한다.**

정의처
  `dev-package/work-items.yaml` 하나뿐. 이 스크립트에 항목표를 다시 적지 않는다.
  산문 문서는 그 대장의 **반영본**이며, 여기서 대조 대상이다.

검사 여섯
  ㈎ 대장 스키마 — 필수 필드 · status/stage 값 · depends_on 이 실재하지 않는 id 를 가리킴
  ㈏ 완주 체크리스트 대조 — `WORK-UNITS §11` 코드블록의 상태 토큰과 대장의 상태 일치
  ㈐ 진실원 대조 — `03-HANDOFF §1` 각 트랙 표와 대장의 상태 일치
  ㈑ 보류 항목 혼입 — `status: deferred`(⏸ 계열)가 착수 후보 표에 이름으로 등장하는가
  ㈒ 기한 경과 — `deadline.fired: true` 인데 status 가 open/deferred 로 남아 있는가
  ㈓ conflict 잔존 — 대장에 `status: conflict` 가 하나라도 있으면 red

  ⚠ ㈏·㈐ 는 **conflict 항목을 비교 대상에서 뺀다.** 산문끼리 갈린 것은 대장이 `conflict` 로
  기록하고 ㈓ 가 잡는다. 같은 사실을 두 검사가 각자 red 로 세면 건수가 부풀고, 그러면
  「몇 건이 어긋나 있는가」라는 이 기구의 첫 산출이 못 읽히게 된다.

보는 것 (정직하게)
  · 표 구조(`| ... | ... |` 행)와 코드 블록(``` 안)만 파싱한다.
  · `03-HANDOFF §1` 은 **헤더명(`WU`·`상태`)으로 열을 찾는다.** 트랙마다 열 수가 다르다 —
    아홉은 `| WU | 상태 | 비고 |` 이고 T-P 하나만 `| WU | 단계 | 상태 | 진입조건 |` 다.
    열 위치를 상수로 박으면 T-P 를 오독한다.
  · **비고 열은 산문이므로 건드리지 않는다.** 산문 안의 서술 문장을 정규식으로 판정하지 않는다 —
    오탐이 잦은 검사기는 곧 무시당하고, 무시당하는 검사기는 없는 것과 같다.

fail-closed (CLAUDE.md §4)
  대장 부재·파싱 실패·항목 0건 · 산문 문서 부재 · 대조 표 0건 · 코드블록 부재 → 전부 red.

green-by-skip 방지
  파싱할 수 없어 **검사하지 못한 자리**는 건수와 함께 출력에 명시한다. 무엇을 안 봤는지를
  숨기는 통과는 이 레포가 막으려는 바로 그 모양이다(`gates/README.md`).
"""
from __future__ import annotations

import os
import pathlib
import re
import sys

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - 환경 문제는 red 다
    print("::error::work-item-consistency — pyyaml 이 없다 (검사 불가는 통과가 아니다)")
    sys.exit(1)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

LEDGER = pathlib.Path(
    os.environ.get("COLAB_WORK_ITEMS_LEDGER") or (REPO_ROOT / "dev-package/work-items.yaml")
)
HANDOFF = pathlib.Path(
    os.environ.get("COLAB_WORK_ITEMS_HANDOFF") or (REPO_ROOT / "dev-package/03-HANDOFF.md")
)
WORKUNITS = pathlib.Path(
    os.environ.get("COLAB_WORK_ITEMS_WORKUNITS") or (REPO_ROOT / "dev-package/WORK-UNITS.md")
)

# 진행 표기 규칙 = WORK-UNITS §12
GLYPH_TO_STATUS = {
    "✅": "done",
    "🟦": "in_progress",
    "⬜": "open",
    "🟧": "partial",
    "⛔": "blocked",
    "⏸": "deferred",
}
GLYPHS = "".join(GLYPH_TO_STATUS)

STATUSES = set(GLYPH_TO_STATUS.values()) | {"conflict"}
STAGES = {"stage1", "stage2", "after_stage2", "out_of_scope", "unknown"}

REQUIRED_FIELDS = ("id", "name", "status", "stage", "owner", "completion_def", "evidence")

# 식별자 — P2 · D2b · G1b · IS4 · R-1 · X-5 · PA-G · T-1 …
ID_RE = re.compile(r"[A-Z]{1,3}(?:-[A-Z0-9]+|\d+[a-z]?)")
ID_AT_START = re.compile(r"^(" + ID_RE.pattern + r")\b")

problems: list[str] = []       # 위반 — red 사유
unchecked: list[str] = []      # 검사하지 못한 자리 — 숨기지 않는다


def die(msg: str) -> None:
    print(f"::error::work-item-consistency — {msg}")
    sys.exit(1)


def strip_md(cell: str) -> str:
    """표 셀에서 마크다운 장식만 걷는다. 내용은 바꾸지 않는다."""
    out = cell.strip()
    out = out.replace("~~", "").replace("**", "").replace("`", "")
    return out.strip()


# ────────────────────────────────────────────────────────────────────────────
# 대장 읽기
# ────────────────────────────────────────────────────────────────────────────
def load_ledger() -> list[dict]:
    if not LEDGER.exists():
        die(f"대장이 없다: {LEDGER.relative_to(REPO_ROOT) if LEDGER.is_relative_to(REPO_ROOT) else LEDGER}")
    try:
        doc = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        die(f"대장 파싱 실패: {exc}")
    if not isinstance(doc, dict) or "items" not in doc:
        die("대장의 최상위가 `items:` 를 가진 매핑이 아니다")
    items = doc["items"]
    if not isinstance(items, list) or not items:
        die("대장의 항목이 0건이다 — 조용히 아무것도 못 찾은 게이트가 v1 의 실패다")
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            die(f"대장 {i}번째 항목이 매핑이 아니다")
    return items


# ────────────────────────────────────────────────────────────────────────────
# ㈎ 대장 스키마
# ────────────────────────────────────────────────────────────────────────────
def check_schema(items: list[dict]) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    for it in items:
        iid = it.get("id")
        if not iid or not isinstance(iid, str):
            problems.append(f"㈎ id 가 없거나 문자열이 아닌 항목이 있다: {it.get('name', it)!r}")
            continue
        if iid in by_id:
            problems.append(f"㈎ id 중복: `{iid}`")
        by_id[iid] = it

    for iid, it in by_id.items():
        for field in REQUIRED_FIELDS:
            if field not in it:
                problems.append(f"㈎ `{iid}`: 필수 필드 `{field}` 가 없다")
        for field in ("entry_conditions", "depends_on"):
            if field not in it:
                problems.append(f"㈎ `{iid}`: 필수 필드 `{field}` 가 없다 (없으면 빈 목록으로 적는다)")
            elif not isinstance(it[field], list):
                problems.append(f"㈎ `{iid}`: `{field}` 는 목록이어야 한다")

        status = it.get("status")
        if status not in STATUSES:
            problems.append(f"㈎ `{iid}`: status `{status}` 는 허용값이 아니다 ({sorted(STATUSES)})")
        stage = it.get("stage")
        if stage not in STAGES:
            problems.append(f"㈎ `{iid}`: stage `{stage}` 는 허용값이 아니다 ({sorted(STAGES)})")

        for dep in it.get("depends_on") or []:
            if dep not in by_id:
                problems.append(f"㈎ `{iid}`: depends_on 이 실재하지 않는 id `{dep}` 를 가리킨다")

        # done · partial 은 근거가 있어야 한다. conflict 는 근거가 아니라 어긋남의 기록이므로 뺀다.
        if status in ("done", "partial"):
            ev = it.get("evidence")
            if not ev or (isinstance(ev, str) and ev.strip() in ("", "[근거 미기재]", "null", "None")):
                problems.append(
                    f"㈎ `{iid}`: status `{status}` 인데 evidence 가 비었다 — "
                    f"결정 기록 인용이나 실측을 넣는다"
                )

        dl = it.get("deadline")
        if dl is not None:
            if not isinstance(dl, dict) or "condition" not in dl or "fired" not in dl:
                problems.append(f"㈎ `{iid}`: deadline 은 `condition`·`fired` 를 가진 매핑이어야 한다")

    return by_id


# ────────────────────────────────────────────────────────────────────────────
# 산문 파싱 — 표와 코드블록만
# ────────────────────────────────────────────────────────────────────────────
def section_lines(text: str, heading_re: str) -> list[str]:
    """지정한 제목부터 같은 수준 이상의 다음 제목 직전까지."""
    lines = text.splitlines()
    start = None
    level = 0
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m and re.search(heading_re, m.group(2)):
            start = i + 1
            level = len(m.group(1))
            break
    if start is None:
        return []
    out = []
    for ln in lines[start:]:
        m = re.match(r"^(#{1,6})\s+", ln)
        if m and len(m.group(1)) <= level:
            break
        out.append(ln)
    return out


def parse_tables(lines: list[str]) -> list[tuple[list[str], list[list[str]]]]:
    """마크다운 표를 (헤더셀, 데이터행들) 로 뽑는다. 코드블록 안은 표가 아니다."""
    tables = []
    in_fence = False
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if not in_fence and ln.lstrip().startswith("|") and i + 1 < len(lines):
            sep = lines[i + 1].strip()
            if re.fullmatch(r"\|(?::?-+:?\|)+", sep):
                header = [c.strip() for c in ln.strip().strip("|").split("|")]
                rows = []
                j = i + 2
                while j < len(lines) and lines[j].lstrip().startswith("|"):
                    rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                    j += 1
                tables.append((header, rows))
                i = j
                continue
        i += 1
    return tables


def code_blocks(lines: list[str]) -> list[list[str]]:
    blocks, cur, in_fence = [], [], False
    for ln in lines:
        if ln.strip().startswith("```"):
            if in_fence:
                blocks.append(cur)
                cur = []
            in_fence = not in_fence
            continue
        if in_fence:
            cur.append(ln)
    return blocks


def leading_ids(cell: str) -> list[str]:
    """셀 맨 앞의 식별자들. `C3 · C4` 처럼 둘일 수 있다."""
    s = strip_md(cell)
    ids = []
    while True:
        m = ID_AT_START.match(s)
        if not m:
            break
        ids.append(m.group(1))
        s = s[m.end():].lstrip()
        m2 = re.match(r"^[·,]\s*", s)
        if not m2:
            break
        s = s[m2.end():]
    return ids


# ────────────────────────────────────────────────────────────────────────────
# ㈐ 진실원 대조 — 03-HANDOFF §1
# ────────────────────────────────────────────────────────────────────────────
def check_handoff(by_id: dict[str, dict]) -> int:
    if not HANDOFF.exists():
        die(f"진실원 문서가 없다: {HANDOFF.name}")
    lines = section_lines(HANDOFF.read_text(encoding="utf-8"), r"^1\.\s*진행도")
    if not lines:
        die("`03-HANDOFF.md` 에서 `## 1. 진행도` 절을 찾지 못했다")
    tables = parse_tables(lines)
    if not tables:
        die("`03-HANDOFF §1` 에서 대조할 표를 하나도 찾지 못했다")

    compared = 0
    for header, rows in tables:
        # 헤더명으로 열을 찾는다 — 위치로 박지 않는다 (T-P 는 상태가 3열째다)
        try:
            id_col = next(i for i, h in enumerate(header) if strip_md(h) in ("WU", "레인", "항목"))
            st_col = next(i for i, h in enumerate(header) if strip_md(h) == "상태")
        except StopIteration:
            unchecked.append(f"㈐ 헤더에 `WU`/`상태` 열이 없는 표 1건 — 대조 대상 밖: `| {' | '.join(header)} |`")
            continue
        for row in rows:
            if len(row) <= max(id_col, st_col):
                unchecked.append(f"㈐ 열 수가 헤더와 다른 행 1건 — 대조 대상 밖: {row[:1]}")
                continue
            ids = leading_ids(row[id_col])
            if not ids:
                unchecked.append(f"㈐ 식별자로 시작하지 않는 행 — 대조 대상 밖: `{strip_md(row[id_col])[:30]}`")
                continue
            if len(ids) > 1:
                unchecked.append(f"㈐ 한 행에 식별자 둘 이상({', '.join(ids)}) — 대조 대상 밖")
                continue
            iid = ids[0]
            found = [g for g in row[st_col] if g in GLYPHS]
            if not found:
                unchecked.append(f"㈐ `{iid}`: 상태 열에 표기가 없다 — 대조 대상 밖")
                continue
            if len(set(found)) > 1:
                problems.append(
                    f"㈐ `{iid}`: `03-HANDOFF §1` 상태 열에 표기가 둘 이상이다 ({''.join(found)}) — "
                    f"어느 것이 현재인지 기계가 못 가른다"
                )
                continue
            doc_status = GLYPH_TO_STATUS[found[0]]
            it = by_id.get(iid)
            if it is None:
                problems.append(f"㈐ `{iid}`: `03-HANDOFF §1` 에 있는데 대장에 없다")
                continue
            if it.get("status") == "conflict":
                continue  # ㈓ 관할
            compared += 1
            if it.get("status") != doc_status:
                problems.append(
                    f"㈐ `{iid}`: 대장 `{it.get('status')}` ↔ `03-HANDOFF §1` `{found[0]}`({doc_status})"
                )
    if compared == 0:
        die("㈐ 대조한 행이 0건이다 — 검사 대상 0 은 통과가 아니다")
    return compared


# ────────────────────────────────────────────────────────────────────────────
# ㈏ 완주 체크리스트 대조 — WORK-UNITS §11
# ────────────────────────────────────────────────────────────────────────────
def check_checklist(by_id: dict[str, dict]) -> int:
    if not WORKUNITS.exists():
        die(f"작업 단위 문서가 없다: {WORKUNITS.name}")
    lines = section_lines(WORKUNITS.read_text(encoding="utf-8"), r"^11\.\s*완주 체크리스트")
    if not lines:
        die("`WORK-UNITS.md` 에서 `## 11. 완주 체크리스트` 절을 찾지 못했다")
    blocks = code_blocks(lines)
    if not blocks:
        die("`WORK-UNITS §11` 에서 코드 블록을 찾지 못했다 — 체크리스트가 파싱 대상 밖으로 옮겨졌다")

    pair_re = re.compile(r"(" + ID_RE.pattern + r")\s+([" + GLYPHS + r"])")
    compared = 0
    for block in blocks:
        for raw in block:
            if not raw.strip():
                continue
            body = raw.split("←")[0]  # ← 뒤는 주석이지 상태가 아니다
            pairs = pair_re.findall(body)
            rest = pair_re.sub("", body)
            if not pairs:
                unchecked.append(f"㈏ 식별자·상태 쌍이 없는 줄 — 대조 대상 밖: `{raw.strip()[:40]}`")
                continue
            if any(g in rest for g in GLYPHS):
                unchecked.append(f"㈏ 쌍으로 묶이지 않은 표기가 남은 줄 — 그 부분은 대조 대상 밖: `{raw.strip()[:40]}`")
            for iid, glyph in pairs:
                doc_status = GLYPH_TO_STATUS[glyph]
                it = by_id.get(iid)
                if it is None:
                    problems.append(f"㈏ `{iid}`: `WORK-UNITS §11` 에 있는데 대장에 없다")
                    continue
                if it.get("status") == "conflict":
                    continue  # ㈓ 관할
                compared += 1
                if it.get("status") != doc_status:
                    problems.append(
                        f"㈏ `{iid}`: 대장 `{it.get('status')}` ↔ `WORK-UNITS §11` `{glyph}`({doc_status})"
                    )
    if compared == 0:
        die("㈏ 대조한 항목이 0건이다 — 검사 대상 0 은 통과가 아니다")
    return compared


# ────────────────────────────────────────────────────────────────────────────
# ㈑ 보류 항목 혼입 — 착수 후보 표
# ────────────────────────────────────────────────────────────────────────────
def check_deferred_in_candidates(by_id: dict[str, dict]) -> int:
    lines = section_lines(WORKUNITS.read_text(encoding="utf-8"), r"^10\.\s*지금 착수 가능한 WU")
    if not lines:
        die("`WORK-UNITS.md` 에서 `## 10. 지금 착수 가능한 WU` 절을 찾지 못했다")
    tables = parse_tables(lines)
    if not tables:
        die("㈑ 착수 후보 표를 찾지 못했다")
    scanned = 0
    for header, rows in tables:
        for row in rows:
            if not row:
                continue
            ids = leading_ids(row[0])
            if not ids:
                unchecked.append(f"㈑ 식별자로 시작하지 않는 착수 후보 행 — 대조 대상 밖: `{strip_md(row[0])[:30]}`")
                continue
            for iid in ids:
                scanned += 1
                it = by_id.get(iid)
                if it is None:
                    problems.append(f"㈑ `{iid}`: 착수 후보 표에 있는데 대장에 없다")
                    continue
                if it.get("status") == "deferred":
                    problems.append(
                        f"㈑ `{iid}`: 대장이 `deferred`(하지 않기로 한 것)인데 "
                        f"`WORK-UNITS §10` 착수 후보 표에 이름으로 올라 있다 — "
                        f"⏸ 와 ⬜ 가 같은 자리에 있으면 끝난 일을 다시 착수한다"
                    )
    if scanned == 0:
        die("㈑ 훑은 착수 후보 행이 0건이다 — 검사 대상 0 은 통과가 아니다")
    return scanned


# ────────────────────────────────────────────────────────────────────────────
# ㈒ 기한 경과 · ㈓ conflict 잔존
# ────────────────────────────────────────────────────────────────────────────
def check_deadlines(by_id: dict[str, dict]) -> int:
    n = 0
    for iid, it in by_id.items():
        dl = it.get("deadline")
        if not isinstance(dl, dict):
            continue
        n += 1
        fired = dl.get("fired")
        if fired is True and it.get("status") in ("open", "deferred"):
            problems.append(
                f"㈒ `{iid}`: 기한 조건이 발동(`fired: true`)했는데 status 가 `{it.get('status')}` 다 — "
                f"조건 = {dl.get('condition')!r}"
            )
        if fired not in (True, False, "unknown", None):
            problems.append(f"㈒ `{iid}`: deadline.fired 값 `{fired}` 를 판정할 수 없다")
        if fired in ("unknown", None):
            unchecked.append(f"㈒ `{iid}`: 기한 발동 여부가 `unknown` — 사람이 판정해야 한다")
    return n


def check_conflicts(by_id: dict[str, dict]) -> int:
    n = 0
    for iid, it in by_id.items():
        if it.get("status") == "conflict":
            n += 1
            problems.append(
                f"㈓ `{iid}`: 산문 문서끼리 갈린 채 남아 있다 — {it.get('note') or '(note 미기재)'}"
            )
    return n


def main() -> int:
    items = load_ledger()
    by_id = check_schema(items)

    n_handoff = check_handoff(by_id)
    n_checklist = check_checklist(by_id)
    n_candidates = check_deferred_in_candidates(by_id)
    n_deadlines = check_deadlines(by_id)
    n_conflicts = check_conflicts(by_id)

    print(
        f"work-item-consistency: 대장 {len(by_id)}건 · "
        f"㈐ 진실원 대조 {n_handoff}행 · ㈏ 체크리스트 대조 {n_checklist}건 · "
        f"㈑ 착수 후보 {n_candidates}행 · ㈒ 기한 {n_deadlines}건 · ㈓ conflict {n_conflicts}건"
    )

    if unchecked:
        print(f"  ── 검사 대상 밖 {len(unchecked)}건 (파싱하지 못해 **안 본** 자리다 — 통과의 근거가 아니다)")
        for u in unchecked:
            print(f"     · {u}")

    if problems:
        print(f"::error::work-item-consistency — 불일치 {len(problems)}건")
        for p in problems:
            print(f"  · {p}")
        return 1

    print("work-item-consistency: green — 대장과 산문의 불일치 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
