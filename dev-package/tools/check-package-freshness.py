#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""전달 패키지 최신성 검사기 (WU-G1).

패키지 HTML 안에 박힌 문서 본문(`<script type="text/markdown" id="md-*">`)이
`documents/*.md` 원본과 같은 판인지 **내용 해시로만** 판정한다.

  - 파일명·mtime 은 판정 입력에서 배제한다 (R1·R2 — 정본 8개 패키지의 mtime 이 전부 같고,
    파일명 260817 이 내용 08-18 개정과 다르다).
  - 정본 폴더가 안 보이면 skip 이 아니라 red 다 (CLAUDE.md §4 — green-by-skip 금지).
  - 이 게이트는 **문서 임베드만** 본다. 화면·목업 최신성은 판정하지 않는다 (그쪽은 WU-G1b).

사용:
    check-package-freshness.py [정본_루트]
    COLAB_PLANNING_ROOT=... check-package-freshness.py
    check-package-freshness.py --selftest
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

# 정본 루트의 기본 위치 — 이 상수 하나에서만 파생된다.
# 절대경로를 박지 않는다 (CLAUDE.md §5) — 레포 위치에서 상대로 푸다.
#   <작업공간>/30 CoLAB-v2/dev-package/tools/  →  <작업공간>/40 COLAB-기획/<정본>
# 위치의 문서화 자리는 `planning/README.md §1` 이다.
# ⭑⟨이동 2026-09-05⟩ 40 COLAB-기획/ 재편으로 패키지가 00_기획원본/ 아래로 옮겨졌다
# (대응표: <작업공간>/40 COLAB-기획/README.md §「경로 대응표」).
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_PLANNING_ROOT = os.path.join(
    os.path.dirname(_REPO_ROOT), "40 COLAB-기획", "00_기획원본",
    "Co-Lab_ver2_1차마일스톤_목업패키지_260818_이태헌",
)
EPICS_DIRNAME = "에픽"          # 에픽
ENV_VAR = "COLAB_PLANNING_ROOT"

# 임베드 블록: 줄머리에서 시작하는 것만 인정한다.
# (템플릿·JS 주석 안의 `id="md-<docType>"`, `id="md-prd|md-policy|md-validation"` 은 미끼다)
BLOCK_RE = re.compile(
    r'^<script type="text/markdown" id="md-(prd|policy)">\n(.*?)\n?</script>',
    re.DOTALL | re.MULTILINE,
)
# 블록 id → 원본 md 파일명 접두사
PREFIXES = {"prd": ("PRD_", "DataModel_"), "policy": ("Policy_",)}
VERSION_RE = re.compile(r"^version:\s*(\S+)\s*$", re.MULTILINE)


def normalize(text):
    """말미 개행·BOM만 정규화한다. 그 외로 관대해지지 않는다."""
    if text.startswith("﻿"):
        text = text[1:]
    return text.replace("\r\n", "\n").rstrip("\n \t")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_root(argv_root):
    return argv_root or os.environ.get(ENV_VAR) or DEFAULT_PLANNING_ROOT


class Unreadable(Exception):
    """정본 파일이 *있는데* 읽히지 않는다 — 낡음과 구분해야 하는 실패다."""


def read(path):
    # 목록은 되고 읽기만 실패하는 상태가 실재했다(외부 드라이브 스트리밍 사본, OSError 5).
    # 그대로 두면 traceback 으로 죽어 "패키지가 낡았다"는 오탐으로 읽힌다. red 는 red 이되 이유를 말한다.
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        raise Unreadable("파일이 보이는데 읽히지 않는다 (%s): %s\n"
                         "   → 정본 폴더가 제자리인지 본다 (planning/README.md §1). "
                         "낡음이 아니라 **읽기 실패**다." % (e.__class__.__name__, path))
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise Unreadable("UTF-8 로 읽히지 않는다: %s (%s)" % (path, e))


def check(root):
    """(rows, errors) 반환. rows = (epic, block, source, verdict, version, sha8)"""
    try:
        return _check(root)
    except Unreadable as e:
        return [], ["정본 읽기 실패 — %s" % e]


def _check(root):
    rows, errors = [], []
    epics_dir = os.path.join(root, EPICS_DIRNAME)
    if not os.path.isdir(epics_dir):
        errors.append(
            "정본 폴더가 없다 (위치 확인 — planning/README.md §1): %s" % epics_dir)
        return rows, errors

    epics = sorted(d for d in os.listdir(epics_dir)
                   if d.startswith("E-") and os.path.isdir(os.path.join(epics_dir, d)))
    if not epics:
        errors.append("에픽 폴더가 0건이다: %s" % epics_dir)
        return rows, errors

    for epic in epics:
        ed = os.path.join(epics_dir, epic)
        pkg_dir, doc_dir = os.path.join(ed, "package"), os.path.join(ed, "documents")
        htmls = sorted(f for f in os.listdir(pkg_dir) if f.endswith(".html")) if os.path.isdir(pkg_dir) else []
        docs = sorted(f for f in os.listdir(doc_dir) if f.endswith(".md")) if os.path.isdir(doc_dir) else []
        if len(htmls) != 1:
            errors.append("%s: package/*.html 이 %d건 (1건이어야 한다)" % (epic, len(htmls)))
            continue
        if not docs:
            errors.append("%s: documents/*.md 가 0건" % epic)
            continue

        blocks = dict((m.group(1), m.group(2)) for m in BLOCK_RE.finditer(read(os.path.join(pkg_dir, htmls[0]))))
        if not blocks:
            errors.append("%s: 임베드 블록을 하나도 찾지 못했다 (%s)" % (epic, htmls[0]))
            continue

        matched_docs = set()
        for block in sorted(blocks):
            cands = [d for d in docs if d.startswith(PREFIXES.get(block, ()))]
            if len(cands) != 1:
                errors.append("%s: md-%s 에 짝지을 원본이 %d건" % (epic, block, len(cands)))
                rows.append((epic, "md-" + block, "?", "NO-SOURCE", "-", "-"))
                continue
            src = cands[0]
            matched_docs.add(src)
            emb, orig = normalize(blocks[block]), normalize(read(os.path.join(doc_dir, src)))
            ok = emb == orig
            ver = (VERSION_RE.search(orig[:400]) or [None, "-"])[1] if VERSION_RE.search(orig[:400]) else "-"
            rows.append((epic, "md-" + block, src, "MATCH" if ok else "DIFFER", ver, sha(orig)[:8]))
            if not ok:
                errors.append("%s / md-%s ≠ %s (임베드 %s vs 원본 %s)"
                              % (epic, block, src, sha(emb)[:8], sha(orig)[:8]))
        for d in docs:
            if d not in matched_docs:
                errors.append("%s: 원본 %s 이 어느 임베드 블록에도 담기지 않았다" % (epic, d))
                rows.append((epic, "-", d, "NOT-EMBEDDED", "-", "-"))
    return rows, errors


def print_table(rows):
    hdr = ("EPIC", "BLOCK", "SOURCE", "VERDICT", "VER", "SHA8")
    w = [max(len(str(r[i])) for r in (rows + [hdr])) for i in range(6)]
    fmt = "  ".join("{:<%d}" % x for x in w)
    print(fmt.format(*hdr))
    print("  ".join("-" * x for x in w))
    for r in rows:
        print(fmt.format(*r))


# ---------------------------------------------------------------- selftest

def selftest():
    """red fixture 로 fail-closed 를 증명한다. 정본에는 절대 쓰지 않는다."""
    root = resolve_root(None)
    tmp = tempfile.mkdtemp(prefix="pkgfresh-selftest-")
    failures = []
    try:
        # ① 정본 미마운트 → red 여야 한다
        _, errs = check(os.path.join(tmp, "no-such-planning-root"))
        print("[selftest 1] 정본 미마운트 → %s" % ("red OK" if errs else "GREEN (자격 없음)"))
        if not errs:
            failures.append("정본 부재인데 green 이 나왔다")

        # ② 임베드 한 글자를 바꾼 사본 → red 여야 한다
        epics_dir = os.path.join(root, EPICS_DIRNAME)
        if not os.path.isdir(epics_dir):
            print("[selftest 2] 정본을 읽을 수 없어 변조 fixture 를 만들지 못했다 — red")
            failures.append("정본 미마운트로 fixture 검증 불가")
        else:
            epic = sorted(d for d in os.listdir(epics_dir) if d.startswith("E-"))[0]
            fake_root = os.path.join(tmp, "fixture")
            dst = os.path.join(fake_root, EPICS_DIRNAME, epic)
            shutil.copytree(os.path.join(epics_dir, epic), dst)  # 사본에만 쓴다
            html = os.path.join(dst, "package",
                                sorted(f for f in os.listdir(os.path.join(dst, "package")) if f.endswith(".html"))[0])
            body = read(html)
            m = BLOCK_RE.search(body)
            assert m, "fixture: 임베드 블록을 찾지 못했다"
            i = m.start(2)
            tampered = body[:i] + "오염 " + body[i:]  # 한 글자 변조
            with open(html, "wb") as f:
                f.write(tampered.encode("utf-8"))
            _, errs2 = check(fake_root)
            print("[selftest 2] 변조 fixture (%s) → %s" % (epic, "red OK" if errs2 else "GREEN (자격 없음)"))
            for e in errs2:
                print("            %s" % e)
            if not errs2:
                failures.append("변조된 패키지에 green 이 나왔다")

            # ③ 파일이 있는데 읽히지 않음 → traceback 이 아니라 **진단된 red** 여야 한다.
            #    (목록은 되고 읽기만 실패하는 상태가 실재했다 — PLAN-SoT §9-㉕)
            os.chmod(html, 0)
            try:
                _, errs3 = check(fake_root)
            finally:
                os.chmod(html, 0o644)
            diagnosed = any("읽기 실패" in e for e in errs3)
            print("[selftest 3] 읽기 불가 fixture → %s" % (
                "red OK (진단됨)" if diagnosed else
                ("red 이지만 진단 문구 없음" if errs3 else "GREEN (자격 없음)")))
            if not errs3:
                failures.append("읽히지 않는 정본에 green 이 나왔다")
            elif not diagnosed:
                failures.append("읽기 실패를 낡음과 구분하지 못한다 (오탐 red)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("::error::selftest 실패 — 검사기가 fail-closed 가 아니다:")
        for f in failures:
            print("  - %s" % f)
        return 1
    print("selftest green — 검사기는 틀린 것을 틀렸다고 말한다 (fail-closed 증명).")
    return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    root = resolve_root(argv[0] if argv else None)
    rows, errors = check(root)
    if rows:
        print_table(rows)
        print("")
    print("# 이 게이트는 문서 임베드만 본다. 화면·목업 최신성은 판정하지 않는다 (WU-G1b).")
    if errors:
        print("::error::planning-freshness red — %d건" % len(errors))
        for e in errors:
            print("  - %s" % e)
        return 1
    print("planning-freshness green — %d개 임베드 블록 전부 원본과 일치." % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
