#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""전달 패키지 최신성 검사기 (WU-G1).

패키지 HTML 안에 박힌 문서 본문(`<script type="text/markdown" id="md-*">`)이
`documents/*.md` 원본과 같은 판인지 **내용 해시로만** 판정한다.

  - 파일명·mtime 은 판정 입력에서 배제한다 (R1·R2 — 정본 8개 패키지의 mtime 이 전부 같고,
    파일명 260817 이 내용 08-18 개정과 다르다).
  - 정본 폴더가 안 보이면 skip 이 아니라 red 다 (CLAUDE.md §4 — green-by-skip 금지).
  - 이 게이트는 **문서 임베드만** 본다. 화면·목업 최신성은 판정하지 않는다 (그쪽은 WU-G1b).

두 번째 판정(2026-09-06 · J-1) — **적용 상태 환류**. `dev-package/prd/planning-applied.yaml`
(적용 상태의 원본)과 `40 COLAB-기획/30_적용완료/`(사본 보관소)를 대조한다. 병합된 라운드의
기획 문서가 사본으로 남지 않으면 red 다. 원본 `10_적용전/` 은 읽기만 한다(rules §7).

사용:
    check-package-freshness.py [정본_루트]
    COLAB_PLANNING_ROOT=... check-package-freshness.py     # 정본 패키지 자리
    COLAB_PLANNING_HOME=... check-package-freshness.py     # `40 COLAB-기획` 자리
    COLAB_PLANNING_MANIFEST=... check-package-freshness.py # 적용 상태 매니페스트 자리
    check-package-freshness.py --selftest
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import tempfile

# 정본 루트의 기본 위치 — 이 상수 하나에서만 파생된다.
# 절대경로를 박지 않는다 (CLAUDE.md §5) — 레포 위치에서 상대로 푸다.
#   <작업공간>/30 CoLAB-v2/dev-package/tools/  →  <작업공간>/40 COLAB-기획/<정본>
# 위치의 문서화 자리는 `planning/README.md §1` 이다.
# ⭑⟨이동 2026-09-05⟩ 40 COLAB-기획/ 재편으로 패키지가 00_기획원본/ 아래로 옮겨졌다
# (대응표: <작업공간>/40 COLAB-기획/README.md §「경로 대응표」).
# ⭑⟨정정 2026-09-06 · P-C⟩ 워크트리에서 경로가 어긋나던 것을 고쳤다.
#   종전 = 이 파일에서 세 단계 위를 레포 루트로 봤다. 워크트리에서는 그 자리가
#   `<레포>/.claude/worktrees/<이름>` 이라 정본을 `<레포>/.claude/worktrees/40 COLAB-기획`
#   에서 찾고 「정본 폴더가 없다」로 red 를 냈다(실측 로그 = reports/harness/2026-09-06/pe-sweep-3.12.log).
#   지금 = `git rev-parse --git-common-dir` 이 **워크트리에서도 본 체크아웃의 `.git`** 을 가리키므로
#   그 부모가 레포 루트이고, 다시 그 부모가 작업공간이다. git 이 없으면 옛 방식으로 물러선다.
# 두 「루트」를 가른다 —
#   _CHECKOUT_ROOT = 지금 검사받는 트리(워크트리일 수 있다). **레포 안 파일**은 여기서 찾는다.
#   _MAIN_REPO_ROOT = 본 체크아웃. 레포 **밖**(작업공간의 기획 폴더)을 짚을 때만 쓴다.
#   둘을 섞으면 워크트리가 본 체크아웃의 매니페스트를 검사하게 되고 브랜치의 변경분이 안 보인다.
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_CHECKOUT_ROOT = os.path.dirname(os.path.dirname(_TOOLS_DIR))


def _repo_root():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=_TOOLS_DIR, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
    except OSError:
        return _CHECKOUT_ROOT
    common = out.stdout.decode("utf-8", "replace").strip()
    if out.returncode != 0 or not common:
        return _CHECKOUT_ROOT
    if not os.path.isabs(common):
        common = os.path.join(_TOOLS_DIR, common)
    return os.path.dirname(os.path.abspath(common))


_MAIN_REPO_ROOT = _repo_root()
WORKSPACE_ROOT = os.path.dirname(_MAIN_REPO_ROOT)
PLANNING_HOME_DIRNAME = "40 COLAB-기획"
DEFAULT_PLANNING_HOME = os.path.join(WORKSPACE_ROOT, PLANNING_HOME_DIRNAME)
DEFAULT_PLANNING_ROOT = os.path.join(
    DEFAULT_PLANNING_HOME, "00_기획원본",
    "Co-Lab_ver2_1차마일스톤_목업패키지_260818_이태헌",
)
EPICS_DIRNAME = "에픽"          # 에픽
ENV_VAR = "COLAB_PLANNING_ROOT"
ENV_HOME_VAR = "COLAB_PLANNING_HOME"
MANIFEST_ENV_VAR = "COLAB_PLANNING_MANIFEST"

# ── 적용 상태 매니페스트 (J-1 · `30_적용완료` 환류) ────────────────────────
# 적용 상태의 원본은 레포 쪽 이 파일이다. `10_적용전/` 은 읽기 전용이라 그 폴더에
# 표식을 남길 수 없다(rules §7). `30_적용완료/` 는 사본 보관소이고, 이 게이트가 둘을 대조한다.
MANIFEST_REL = os.path.join("dev-package", "prd", "planning-applied.yaml")
DEFAULT_MANIFEST = os.path.join(_CHECKOUT_ROOT, MANIFEST_REL)
APPLIED_DIRNAME = "30_적용완료"

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


def resolve_home(argv_root=None):
    """`40 COLAB-기획` 자체의 자리. 정본 패키지 경로(`resolve_root`)보다 두 단계 위다."""
    home = os.environ.get(ENV_HOME_VAR)
    if home:
        return home
    override = argv_root or os.environ.get(ENV_VAR)
    if override:
        # 패키지 경로만 주어졌으면 `<홈>/00_기획원본/<패키지>` 규약으로 되짚는다.
        return os.path.dirname(os.path.dirname(os.path.abspath(override)))
    return DEFAULT_PLANNING_HOME


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


# ------------------------------------------------- 적용 상태 환류 (J-1 · `30_적용완료`)

def _nfc(s):
    return unicodedata.normalize("NFC", s)


def load_manifest(path):
    """(items, errors). 파서 부재·파일 부재·형식 파손은 전부 red 다 — skip 이 아니다."""
    try:
        import yaml
    except ImportError:
        return None, ["PyYAML 이 없어 적용 상태를 판정할 수 없다 — 이것은 skip 이 아니라 red 다 "
                      "(CLAUDE.md §4 green-by-skip 금지): %s" % path]
    if not os.path.isfile(path):
        return None, ["적용 상태 매니페스트가 없다: %s" % path]
    try:
        with open(path, "rb") as f:
            doc = yaml.safe_load(f.read().decode("utf-8"))
    except Exception as e:  # 파손 YAML·인코딩 오류
        return None, ["매니페스트를 읽지 못했다 (%s): %s" % (e.__class__.__name__, path)]
    if not isinstance(doc, dict) or not isinstance(doc.get("items"), list):
        return None, ["매니페스트 형식이 아니다 (`items:` 목록이 필요하다): %s" % path]
    return doc["items"], []


def copy_rel(item):
    """사본 경로 — 명시 `copy` 우선, 없으면 `30_적용완료/<applied_round>/<원파일명>` 으로 파생."""
    explicit = item.get("copy")
    if explicit:
        return explicit
    rnd, src = item.get("applied_round"), item.get("source") or ""
    if not rnd or not src:
        return None
    return "%s/%s/%s" % (APPLIED_DIRNAME, rnd, os.path.basename(src))


def _abs(home, rel):
    return os.path.join(home, *rel.split("/"))


def _sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def check_applied(home, manifest_path):
    """(rows, errors) 반환. rows = (id, status, round, verdict, copy).

    판정 둘 —
      ㈎ status: merged 인 항목은 `30_적용완료/` 에 **원본과 바이트 동일한 사본**이 있어야 한다.
         (병합된 라운드인데 사본이 없으면 그것이 기획 드리프트가 숨는 자리다 — 스펙 F 15행)
      ㈏ `30_적용완료/` 아래 모든 파일은 매니페스트에 등재돼 있어야 한다.
         (등재 없는 사본은 어느 라운드가 무엇을 반영했는지 아무도 모르는 상태다)
    원본(`10_적용전/`)은 읽지만 쓰지 않는다 — 읽기 전용 규약(rules §7).
    """
    rows, errors = [], []
    items, errs = load_manifest(manifest_path)
    if errs:
        return rows, errs

    expected = {}          # NFC 정규화한 사본 상대경로 → 항목 id
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append("항목 %d 이 매핑이 아니다" % i)
            continue
        iid = item.get("id") or "(id 없음 · 항목 %d)" % i
        src = item.get("source")
        status = item.get("status")
        rnd = item.get("applied_round") or "-"
        if not src:
            errors.append("%s: `source` 가 없다" % iid)
            rows.append((iid, str(status), rnd, "NO-SOURCE", "-"))
            continue
        if status not in ("merged", "in_progress", "pending"):
            errors.append("%s: `status` 가 merged|in_progress|pending 이 아니다 (%r)" % (iid, status))
        src_abs = _abs(home, src)
        if not os.path.isfile(src_abs):
            errors.append("%s: 원본이 없다 — %s (10_적용전 은 옮기지 않는다, rules §7)" % (iid, src))
            rows.append((iid, str(status), rnd, "SRC-MISSING", "-"))
            continue

        rel = copy_rel(item)
        if status == "merged":
            if not item.get("applied_date"):
                errors.append("%s: merged 인데 `applied_date` 가 없다" % iid)
            if not rel:
                errors.append("%s: merged 인데 사본 경로를 정할 수 없다 "
                              "(`copy` 또는 `applied_round` 가 필요하다)" % iid)
                rows.append((iid, status, rnd, "NO-COPY-PATH", "-"))
                continue
            expected[_nfc(rel)] = iid
            dst_abs = _abs(home, rel)
            if not os.path.isfile(dst_abs):
                errors.append("%s: 병합된 라운드(%s)인데 사본이 없다 — %s\n"
                              "   → `dev-package/tools/planning-applied.py --sync --apply` 로 복사한다 "
                              "(원본은 그대로 둔다)" % (iid, rnd, rel))
                rows.append((iid, status, rnd, "NOT-COPIED", rel))
                continue
            try:
                same = _sha_file(src_abs) == _sha_file(dst_abs)
            except OSError as e:
                errors.append("%s: 사본을 읽지 못했다 (%s): %s" % (iid, e.__class__.__name__, rel))
                rows.append((iid, status, rnd, "UNREADABLE", rel))
                continue
            if not same:
                errors.append("%s: 사본이 원본과 다르다 — %s (사본은 무수정 보관이다)" % (iid, rel))
                rows.append((iid, status, rnd, "COPY-DIFFERS", rel))
                continue
            rows.append((iid, status, rnd, "COPIED", rel))
        else:
            if rel and os.path.isfile(_abs(home, rel)):
                expected[_nfc(rel)] = iid
                errors.append("%s: status 가 %s 인데 사본이 이미 있다 — %s "
                              "(사본은 라운드 병합 뒤에만 만든다)" % (iid, status, rel))
                rows.append((iid, str(status), rnd, "EARLY-COPY", rel))
            else:
                rows.append((iid, str(status), rnd, "PENDING", "-"))

    # ㈏ 등재 없는 사본 — 어느 라운드가 무엇을 반영했는지 모르는 파일이 남지 않게 한다.
    applied_dir = os.path.join(home, APPLIED_DIRNAME)
    if os.path.isdir(applied_dir):
        for dirpath, dirnames, filenames in os.walk(applied_dir):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fn in filenames:
                if fn.startswith(".") or fn == ".gitkeep":
                    continue
                rel = os.path.relpath(os.path.join(dirpath, fn), home).replace(os.sep, "/")
                if _nfc(rel) not in expected:
                    errors.append("등재 없는 사본이다 — %s "
                                  "(`dev-package/prd/planning-applied.yaml` 에 항목을 적는다)" % rel)
                    rows.append(("(미등재)", "-", "-", "UNLISTED", rel))
    elif expected:
        errors.append("사본 폴더가 없다: %s" % applied_dir)
    return rows, errors


def print_applied_table(rows):
    hdr = ("ID", "STATUS", "ROUND", "VERDICT", "COPY")
    w = [max(len(str(r[i])) for r in (rows + [hdr])) for i in range(5)]
    fmt = "  ".join("{:<%d}" % x for x in w)
    print(fmt.format(*hdr))
    print("  ".join("-" * x for x in w))
    for r in rows:
        print(fmt.format(*[str(x) for x in r]))


def print_table(rows):
    hdr = ("EPIC", "BLOCK", "SOURCE", "VERDICT", "VER", "SHA8")
    w = [max(len(str(r[i])) for r in (rows + [hdr])) for i in range(6)]
    fmt = "  ".join("{:<%d}" % x for x in w)
    print(fmt.format(*hdr))
    print("  ".join("-" * x for x in w))
    for r in rows:
        print(fmt.format(*r))


def _selftest_applied(tmp):
    """적용 상태 환류의 red fixture 4종. 반환 = 실패 사유 목록(빈 목록이면 통과)."""
    import textwrap
    failures = []
    home = os.path.join(tmp, "applied-home")
    src_rel = "10_적용전/샘플_기획_260906.txt"
    os.makedirs(os.path.join(home, "10_적용전"))
    os.makedirs(os.path.join(home, APPLIED_DIRNAME, "R-Z"))
    with open(_abs(home, src_rel), "wb") as f:
        f.write("원본 본문\n".encode("utf-8"))
    copy_rel_path = "%s/R-Z/샘플_기획_260906.txt" % APPLIED_DIRNAME

    def manifest(status, extra=""):
        path = os.path.join(tmp, "manifest-%s.yaml" % status)
        with open(path, "wb") as f:
            f.write(textwrap.dedent("""\
                version: 1
                items:
                  - id: fixture
                    source: "%s"
                    rounds: ["R-Z"]
                    applied_round: "R-Z"
                    status: %s
                    applied_date: 2026-09-06
                %s""" % (src_rel, status, extra)).encode("utf-8"))
        return path

    def expect(label, cond_red, errs):
        red = bool(errs)
        if cond_red:
            verdict = "red OK" if red else "GREEN (자격 없음)"
        else:
            verdict = "green OK" if not red else "RED (오탐 — 정합한데 막았다)"
        print("[selftest 4-%s] %s → %s" % (label[0], label[2:], verdict))
        if cond_red and not red:
            failures.append("적용 상태 %s 인데 green 이 나왔다" % label[2:])
        if not cond_red and red:
            failures.append("정합한 적용 상태에 red 가 나왔다: %s" % errs)

    # ㈎ 병합됐는데 사본 없음 → red
    _, e1 = check_applied(home, manifest("merged"))
    expect("a 병합된 라운드인데 사본 없음", True, e1)

    # ㈏ 사본이 원본과 다름 → red
    with open(_abs(home, copy_rel_path), "wb") as f:
        f.write("원본 본문 오염\n".encode("utf-8"))
    _, e2 = check_applied(home, manifest("merged"))
    expect("b 사본이 원본과 다름", True, e2)

    # ㈐ 사본이 원본과 같음 → green (검사기가 통과도 낼 수 있어야 자격이 있다)
    shutil.copy2(_abs(home, src_rel), _abs(home, copy_rel_path))
    _, e3 = check_applied(home, manifest("merged"))
    expect("c 사본이 원본과 동일", False, e3)

    # ㈑ 등재 없는 사본이 섞임 → red
    with open(os.path.join(home, APPLIED_DIRNAME, "R-Z", "미등재.txt"), "wb") as f:
        f.write(b"x")
    _, e4 = check_applied(home, manifest("merged"))
    expect("d 등재 없는 사본", True, e4)
    os.remove(os.path.join(home, APPLIED_DIRNAME, "R-Z", "미등재.txt"))

    # ㈒ 매니페스트 자체가 없음 → skip 이 아니라 red
    _, e5 = check_applied(home, os.path.join(tmp, "no-such-manifest.yaml"))
    expect("e 매니페스트 부재", True, e5)
    return failures


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
        # ④ 적용 상태 환류 (J-1) — 네 갈래 fixture 로 fail-closed 를 증명한다.
        #    정본 마운트와 무관하게 돈다(자체 fixture 만 쓴다).
        failures.extend(_selftest_applied(tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("::error::selftest 실패 — 검사기가 fail-closed 가 아니다:")
        for f in failures:
            print("  - %s" % f)
        return 1
    print("selftest green — 검사기는 틀린 것을 틀렸다고 말한다 (fail-closed 증명).")
    return 0


def resolve_manifest():
    return os.environ.get(MANIFEST_ENV_VAR) or DEFAULT_MANIFEST


def main(argv):
    if "--selftest" in argv:
        return selftest()
    argv_root = argv[0] if argv else None
    root = resolve_root(argv_root)
    rows, errors = check(root)
    if rows:
        print_table(rows)
        print("")

    home, manifest = resolve_home(argv_root), resolve_manifest()
    arows, aerrors = check_applied(home, manifest)
    print("── 적용 상태 환류 (J-1) — 매니페스트 %s ─────────" % os.path.relpath(manifest, _CHECKOUT_ROOT))
    if arows:
        print_applied_table(arows)
    else:
        print("  등재 0건")
    print("")

    print("# 이 게이트는 ① 문서 임베드 일치 ② 적용 상태 환류만 본다. 화면·목업 최신성은 판정하지 않는다 (WU-G1b).")
    errors = errors + aerrors
    if errors:
        print("::error::planning-freshness red — %d건" % len(errors))
        for e in errors:
            print("  - %s" % e)
        return 1
    print("planning-freshness green — 임베드 블록 %d개 전부 원본과 일치 · 적용 상태 %d건 정합."
          % (len(rows), len(arows)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
