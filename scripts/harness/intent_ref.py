#!/usr/bin/env python3
"""Gate `intent-ref`: commits link to an intent, and approved intents are append-only.

⑴ When the range changes a subject path, at least one commit in it must carry an
   `Intent-Ref: dev-package/intent/<file>.md` trailer naming a file that exists at head.
   An empty commit carrying only the trailer counts (retroactive path for old branches).
   A range that touches no subject path is out of scope: printed with counts, green.
⑵ An intent that is approved at the base OR at the fork point (its meta line says 승인 and not
   미승인) may only gain lines in the range. Deleting, renaming or editing any existing line is red.
   Both points count: a PR that forked before develop approved an intent must not rewrite it.
   Additions-only = every existing line (raw bytes, from `git cat-file blob`) still appears in
   order in the new content (ordered subsequence). No diff text is parsed, so `---` lines, a
   missing final newline, `-diff`/textconv attributes, colour or binary detection cannot hide a
   removal. Paths keep their original bytes (surrogateescape) so non-UTF-8 names stay protected.

Base: COLAB_INTENT_REF_BASE (CI passes the PR base sha). Undeclared → merge-base(HEAD,
origin/develop), and the output says so. Head: COLAB_INTENT_REF_HEAD, default HEAD.
exit 0 green · 1 red(판정) · 78 red(준비: base unresolvable / not a repository).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

INTENT_ROOT = "dev-package/intent"
EXCLUDED = {"TEMPLATE.md", "README.md"}
SUBJECT_PREFIXES = ("services/", "frontend/src/", "contracts/", "db/", "scripts/", "gates/",
                    ".agents/", ".claude/", ".codex/")
META = re.compile(r"^메타.*$", re.M)
REF = re.compile(r"^dev-package/intent/[^/\s]+\.md$")


class Readiness(Exception):
    """The judgement target could not be read."""


def classify(text: str) -> str:
    """approved | unapproved | no-meta, from the first line starting with 메타."""
    match = META.search(text)
    if match is None:
        return "no-meta"
    line = match.group(0)
    if "미승인" in line:
        return "unapproved"
    return "approved" if "승인" in line else "unapproved"


def is_protected(name: str, text: str) -> bool:
    return name not in EXCLUDED and classify(text) == "approved"


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if check and result.returncode != 0:
        raise Readiness(f"git {' '.join(args[:2])} failed: "
                        + result.stderr.decode("utf-8", "replace").strip())
    return result


def resolve(root: Path, ref: str, label: str) -> str:
    result = git(root, "rev-parse", "--verify", "--quiet", ref + "^{commit}", check=False)
    if result.returncode != 0:
        raise Readiness(f"{label} `{ref}` does not resolve to a commit")
    return result.stdout.decode().strip()


def blob(root: Path, commit: str, path: str) -> bytes | None:
    """Raw blob bytes (no textconv, no attributes); None when the path is absent."""
    result = git(root, "cat-file", "blob", f"{commit}:{path}", check=False)
    return result.stdout if result.returncode == 0 else None


def show(root: Path, commit: str, path: str) -> str | None:
    data = blob(root, commit, path)
    return data.decode("utf-8", "replace") if data is not None else None


def printable(path: str) -> str:
    return path.encode("utf-8", "surrogateescape").decode("utf-8", "backslashreplace")


def first_missing_line(old: bytes, new: bytes) -> bytes | None:
    """The first old line not found, in order, among the new lines (None = only additions)."""
    lines = iter(new.splitlines())
    for line in old.splitlines():
        if not any(candidate == line for candidate in lines):
            return line
    return None


def judge(root: Path, base_ref: str | None, head_ref: str) -> tuple[list[str], list[str]]:
    """Return (info lines, red lines). Raises Readiness."""
    info: list[str] = []
    head = resolve(root, head_ref, "head")
    if base_ref:
        base = resolve(root, base_ref, "COLAB_INTENT_REF_BASE")
        info.append(f"기준 = COLAB_INTENT_REF_BASE `{base_ref}` ({base[:12]})")
    else:
        develop = resolve(root, "refs/remotes/origin/develop", "COLAB_INTENT_REF_BASE 미선언 · origin/develop")
        result = git(root, "merge-base", head, develop, check=False)
        if result.returncode != 0:
            raise Readiness("COLAB_INTENT_REF_BASE 미선언 · merge-base(HEAD, origin/develop) 없음")
        base = result.stdout.decode().strip()
        info.append(f"기준 = COLAB_INTENT_REF_BASE 미선언 → merge-base(HEAD, origin/develop) = {base[:12]}")
    result = git(root, "merge-base", base, head, check=False)
    if result.returncode != 0:
        raise Readiness(f"base {base[:12]} and head {head[:12]} share no history (shallow clone?)")
    fork = result.stdout.decode().strip()

    commits = [c for c in git(root, "rev-list", f"{fork}..{head}").stdout.decode().split() if c]
    changed = sorted({p for p in git(root, "diff", "--no-renames", "--name-only", "-z", fork, head)
                      .stdout.decode("utf-8", "surrogateescape").split("\0") if p})
    subject = [p for p in changed if p.startswith(SUBJECT_PREFIXES)]
    red: list[str] = []

    # ⑴ trailer
    valid, broken = [], []
    if commits:
        log = git(root, "log", "-z", "--format=%H%n%(trailers:key=Intent-Ref,valueonly,unfold)",
                  f"{fork}..{head}").stdout.decode("utf-8", "replace")
        for record in filter(None, log.split("\0")):
            sha, _, values = record.partition("\n")
            for value in (v.strip() for v in values.splitlines() if v.strip()):
                name = PurePosixPath(value).name
                if (REF.fullmatch(value) and name not in EXCLUDED
                        and git(root, "cat-file", "-e", f"{head}:{value}", check=False).returncode == 0):
                    valid.append((sha, value))
                else:
                    broken.append((sha, value))
    scope = f"범위 {fork[:12]}..{head[:12]} · 커밋 {len(commits)} · 변경 파일 {len(changed)}"
    if not subject:
        info.append(f"⑴ 대상 밖 — 대상 경로 변경 0건 ({scope}) · 트레일러 검사 생략")
    elif valid:
        info.append(f"⑴ Intent-Ref {len(valid)}건 유효 ({scope} · 대상 경로 {len(subject)}) — "
                    + ", ".join(sorted({v for _, v in valid})))
    else:
        red.append(f"⑴ 범위의 커밋 {len(commits)}개 중 유효한 `Intent-Ref: dev-package/intent/<파일>.md` "
                   f"트레일러가 0개다 ({scope} · 대상 경로 {len(subject)}건, 예: {printable(subject[0])}).")
        for sha, value in broken:
            red.append(f"   - {sha[:12]} `Intent-Ref: {printable(value)}` — 형식이 틀렸거나 head 에 그 파일이 없다")
        red.append("   고치는 법: 해당 intent 를 가리키는 트레일러를 커밋에 단다. 이미 올린 브랜치는 "
                   "`git commit --allow-empty -m \"…\" -m \"Intent-Ref: dev-package/intent/<파일>.md\"` 1개.")

    # ⑵ approved intents (at the base OR at the fork point) stay append-only in fork..head
    def intent_names(commit: str) -> set[str]:
        return {n for n in git(root, "ls-tree", "-z", "--name-only", commit, INTENT_ROOT + "/")
                .stdout.decode("utf-8", "surrogateescape").split("\0") if n.endswith(".md")}

    protected = 0
    for path in sorted(intent_names(base) | intent_names(fork)):
        name = PurePosixPath(path).name
        approved_at = [c for c in dict.fromkeys((base, fork))
                       if (text := show(root, c, path)) is not None and is_protected(name, text)]
        if not approved_at:
            continue
        protected += 1
        if path not in changed:
            continue
        after = blob(root, head, path)
        if after is None:
            red.append(f"⑵ 승인 intent 가 삭제·이동됐다: {printable(path)} — 재개봉 금지 · 새 intent 를 쓴다")
            continue
        before = blob(root, fork, path)
        if before is None:
            continue  # created in the range: nothing existing to protect
        missing = first_missing_line(before, after)
        if missing is not None:
            shown = missing.decode("utf-8", "replace")[:60]
            red.append(f"⑵ 승인 intent 의 기존 줄이 변경·삭제됐다: {printable(path)} `{shown}` "
                       "— 줄 추가만 허용한다 · 필요하면 새 intent")
    info.append(f"⑵ 기준·분기 시점 승인 intent {protected}건 대조")
    return info, red


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    base = os.environ.get("COLAB_INTENT_REF_BASE") or None
    head = os.environ.get("COLAB_INTENT_REF_HEAD") or "HEAD"
    try:
        info, red = judge(args.repo_root.resolve(), base, head)
    except (Readiness, OSError) as exc:
        print(f"::gate-readiness-failure::gate=intent-ref|detail={exc}", file=sys.stderr)
        print(f"intent-ref red(준비) — 판정하지 못했다: {exc}")
        return 78
    for line in info:
        print("  " + line)
    if red:
        print(f"intent-ref red(판정) — {sum(1 for r in red if not r.startswith('   '))}건")
        for line in red:
            print("  " + line)
        return 1
    print("intent-ref green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
