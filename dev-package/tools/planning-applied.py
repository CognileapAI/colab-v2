#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""기획 입력물 적용 상태 동기 — `10_적용전` 원본을 `30_적용완료/<라운드>/` 로 **복사**한다 (J-1).

무엇을 하지 않는가 (이것이 이 도구의 절반이다) —
  - **원본을 옮기지 않는다.** `40 COLAB-기획/10_적용전/` 은 읽기 전용이다
    (`.claude/rules/colab-rules.md §7` · 폴더 색인 `40 COLAB-기획/README.md`).
  - **원본을 고치지 않는다.** 파일명·내용 무수정이 규약이고, 여기서는 읽기만 한다.
  - **사본을 지우지 않는다.** 이 도구는 만들기만 한다.

무엇을 하는가 —
  매니페스트 `dev-package/prd/planning-applied.yaml`(적용 상태의 원본)에서 `status: merged`
  항목을 골라, 사본이 없거나 원본과 다르면 복사한다. 복사 뒤 그 항목의 `copied_at` 을 적는다.
  기본은 **dry-run** 이고 `--apply` 를 줘야 실제로 쓴다.

판정은 게이트가 한다 —
  `bash gates/run.sh planning-freshness` (검사기 `dev-package/tools/check-package-freshness.py`).
  이 도구는 그 게이트가 red 로 지목한 것을 해소하는 손이지, 판정처가 아니다.

사용:
    planning-applied.py --sync                 # 무엇을 복사할지만 출력
    planning-applied.py --sync --apply         # 실제 복사 + 매니페스트 `copied_at` 기록
    planning-applied.py --check                # 게이트와 같은 판정을 그대로 출력
  환경변수 `COLAB_PLANNING_HOME` · `COLAB_PLANNING_MANIFEST` 로 자리를 옮길 수 있다.
"""
import datetime
import importlib.util
import io
import os
import re
import shutil
import sys

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_gate():
    """검사기를 그대로 불러 쓴다 — 판정 규칙을 두 곳에 적지 않는다."""
    path = os.path.join(_TOOLS_DIR, "check-package-freshness.py")
    spec = importlib.util.spec_from_file_location("colab_pkg_freshness", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = _load_gate()


def _read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def plan(home, manifest_path):
    """(할 일 목록, 오류). 할 일 = (id, 원본 상대경로, 사본 상대경로, 사유)"""
    items, errors = G.load_manifest(manifest_path)
    if errors:
        return [], errors
    todo = []
    for item in items:
        if not isinstance(item, dict) or item.get("status") != "merged":
            continue
        iid, src = item.get("id"), item.get("source")
        rel = G.copy_rel(item)
        if not src or not rel:
            errors.append("%s: merged 인데 원본·사본 경로가 정해지지 않았다" % iid)
            continue
        src_abs, dst_abs = G._abs(home, src), G._abs(home, rel)
        if not os.path.isfile(src_abs):
            errors.append("%s: 원본이 없다 — %s" % (iid, src))
            continue
        if not os.path.isfile(dst_abs):
            todo.append((iid, src, rel, "사본 없음"))
        elif G._sha_file(src_abs) != G._sha_file(dst_abs):
            todo.append((iid, src, rel, "사본이 원본과 다름"))
    return todo, errors


_ID_RE = re.compile(r"^(\s*)-\s+id:\s*(\S.*?)\s*$")


def record_copied_at(manifest_path, iid, rel, date_str):
    """매니페스트에 `copy`·`copied_at` 을 기록한다.

    전체 재출력(`yaml.dump`)을 쓰지 않는다 — 주석·따옴표·항목 순서가 통째로 갈린다.
    해당 항목 블록의 줄만 바꾸고, 쓴 뒤 다시 파싱해 항목 수·id 가 그대로인지 확인한다.
    """
    original = _read(manifest_path)
    lines = original.split("\n")
    start = None
    indent = ""
    for i, line in enumerate(lines):
        m = _ID_RE.match(line)
        if m and m.group(2).strip('"\'') == str(iid):
            start, indent = i, m.group(1) + "  "
            break
    if start is None:
        return "항목 %s 을 매니페스트에서 찾지 못했다" % iid
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _ID_RE.match(lines[j]):
            end = j
            break

    def find(key):
        for j in range(start, end):
            if re.match(r"^\s*%s:" % re.escape(key), lines[j]):
                return j
        return None

    copy_line = '%scopy: "%s"' % (indent, rel)
    at_line = "%scopied_at: %s" % (indent, date_str)
    i_copy, i_at = find("copy"), find("copied_at")
    if i_copy is None:
        anchor = find("source")
        anchor = start if anchor is None else anchor
        lines.insert(anchor + 1, copy_line)
        end += 1
        i_at = find("copied_at")
    else:
        lines[i_copy] = copy_line
    if i_at is None:
        i_copy = find("copy")
        lines.insert(i_copy + 1, at_line)
    else:
        lines[i_at] = at_line

    patched = "\n".join(lines)
    # 되읽어 검증한다 — 파손된 매니페스트를 남기느니 쓰지 않는다.
    tmp = manifest_path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        f.write(patched)
    new_items, errs = G.load_manifest(tmp)
    old_items, _ = G.load_manifest(manifest_path)
    if errs or new_items is None or len(new_items) != len(old_items) \
            or [x.get("id") for x in new_items] != [x.get("id") for x in old_items]:
        os.remove(tmp)
        return "매니페스트 갱신이 항목 구성을 바꿨다 — 쓰지 않았다 (%s)" % (errs or "id 목록 불일치")
    got = [x for x in new_items if str(x.get("id")) == str(iid)][0]
    if str(got.get("copied_at")) != date_str or got.get("copy") != rel:
        os.remove(tmp)
        return "매니페스트 갱신이 반영되지 않았다 — 쓰지 않았다 (%s)" % iid
    os.replace(tmp, manifest_path)
    return None


def sync(home, manifest_path, apply):
    todo, errors = plan(home, manifest_path)
    print("── planning-applied --sync%s ──────────────" % (" --apply" if apply else " (dry-run)"))
    print("  기획 홈   %s" % home)
    print("  매니페스트 %s" % manifest_path)
    if errors:
        for e in errors:
            print("  ✗ %s" % e)
    if not todo:
        print("  복사할 것 0건 — 매니페스트의 merged 항목이 전부 사본과 일치한다.")
        return 1 if errors else 0
    print("  복사 대상 %d건:" % len(todo))
    for iid, src, rel, why in todo:
        print("    %s  %s\n        → %s  (%s)" % (iid, src, rel, why))
    if not apply:
        print("  dry-run 이라 아무것도 쓰지 않았다. 실제로 복사하려면 --apply 를 준다.")
        return 1 if errors else 0

    date_str = datetime.date.today().isoformat()
    done = 0
    for iid, src, rel, _why in todo:
        src_abs, dst_abs = G._abs(home, src), G._abs(home, rel)
        os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
        shutil.copy2(src_abs, dst_abs)          # 복사다. 원본은 그 자리에 그대로 있다.
        if G._sha_file(src_abs) != G._sha_file(dst_abs):
            print("  ✗ %s: 복사했는데 내용이 다르다 — %s" % (iid, rel))
            errors.append("%s 복사 검증 실패" % iid)
            continue
        err = record_copied_at(manifest_path, iid, rel, date_str)
        if err:
            print("  ✗ %s: %s" % (iid, err))
            errors.append(err)
            continue
        done += 1
        print("  ✓ %s → %s (copied_at %s)" % (src, rel, date_str))
    print("  복사 %d건 · 원본 이동 0건 · 원본 수정 0건" % done)
    return 1 if errors else 0


def check(home, manifest_path):
    rows, errors = G.check_applied(home, manifest_path)
    if rows:
        G.print_applied_table(rows)
    if errors:
        print("::error::적용 상태 red — %d건" % len(errors))
        for e in errors:
            print("  - %s" % e)
        return 1
    print("적용 상태 green — %d건 정합." % len(rows))
    return 0


def main(argv):
    home = os.environ.get(G.ENV_HOME_VAR) or G.DEFAULT_PLANNING_HOME
    manifest_path = os.environ.get(G.MANIFEST_ENV_VAR) or G.DEFAULT_MANIFEST
    for i, a in enumerate(argv):
        if a == "--home" and i + 1 < len(argv):
            home = argv[i + 1]
        if a == "--manifest" and i + 1 < len(argv):
            manifest_path = argv[i + 1]
    if "--check" in argv:
        return check(home, manifest_path)
    if "--sync" in argv:
        return sync(home, manifest_path, apply="--apply" in argv)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
