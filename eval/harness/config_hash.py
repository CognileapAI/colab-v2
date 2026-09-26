#!/usr/bin/env python3
"""설정 해시 — eval 결과를 「어느 설정에서 잰 것인가」에 결합한다 (spec S-HARNESS-E0-EVAL-GATE-20260926 §4.1 · §4.3).

정본 파일 집합 = `eval/harness/config-paths.txt`(--root 기준). 러너 `eval/harness/run.sh` 가 회차마다
`compute` 로 `results/<run>/config-hash.json` 을 쓰고, 게이트 `gates/tools/harness-eval.sh` 면제 분기가
`verify` 로 「현재 해시와 일치하는 전수 결과」를 찾는다.

compute  파일 집합 = `git ls-files --cached --others --exclude-standard -- <pathspec>` (추적 + 비무시 미추적).
         파일마다 sha = git blob sha1(= `git hash-object --stdin < path`) · symlink 는 링크 텍스트의 blob sha
         (대상이 집합 밖 파일이면 대상 본문 sha 를 덧붙인다 · 집합 안이면 대상 항목으로 1회만 센다) ·
         깨진 링크·사라진 추적 파일 = `missing` 표기. hash = 정렬된 `path\\0sha\\n` 의 sha256.
         내용 기준이라 실행 시 dirty 였던 편집을 그대로 커밋하면 같은 해시다.
verify   후보 = `results/<YYYYMMDD-HHMMSS>/config-hash.json` 중 hash == 현재 ∧ selected == all ∧
         summary.md 요약줄 `준비 0` ∧ 표의 과제 행 수 == --tasks. 없으면 78.
         후보 중 id 최대 = R*. 직전 = R* 보다 id 가 작고 summary.md 가 있으며 표의 과제 행 수 == --tasks 인
         최신 전수 결과(해시 없는 옛 결과 포함 · 선택 실행 제외 · 행이 모자란 중단 회차 제외 — 중단 회차로
         「회귀 0」을 만들지 않는다). green(직전) − green(R*) − rate(R*) ≠ ∅ → 1(회귀). 그 밖 0.
         rate(R*) = 판정 칸 `rate [0-2]/2` 행(비율 측정 과제 · 15라운드 판정 H18-rate) — `rate` 로 시작하는
         그 밖의 칸 = 78 · rate 행 집합 ≠ `eval/harness/H??-*/mode`(본문 `rate`) 집합 = 78(해시 일치 결과 아님).
         입력을 못 읽음(json 손상 · 요약줄/표 파싱 실패 · git 실패) = 78 — 「못 읽음 = 78 · 읽었는데 위반 = 1」.

exit — 0 · 1(verify 회귀) · 78(준비). verify stdout = `<현재 해시>\\t<설명>` 한 줄.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

PATHS_REL = "eval/harness/config-paths.txt"
EXCLUDE = ":(exclude)"
SCHEMA = "colab-eval-config-hash/1"
RUN_ID_RE = re.compile(r"^\d{8}-\d{6}$")
SUMMARY_RE = re.compile(
    r"^- 요약 — 과제 (\d+) · 실행 (\d+) · green (\d+) · 불안정 (\d+) · 준비 (\d+) · ", re.MULTILINE)
# Verdict cell may contain a space (`rate 1/2`); the old tokens (green · 불안정 · 실패 · 준비) have none.
ROW_RE = re.compile(r"^\| (H\d\d-[^ |]+) \| ([^|]+?) \|", re.MULTILINE)
RATE_RE = re.compile(r"^rate [0-2]/2$")
MODE_RATE = "rate"


class ConfigHashError(Exception):
    """The configuration or its inputs could not be read (readiness · 78)."""


def read_patterns(path: Path) -> list[str]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigHashError(f"정본 파일을 읽지 못했다: {path} ({exc})") from exc
    patterns = [line.strip() for line in text.splitlines()]
    patterns = [p for p in patterns if p and not p.startswith("#")]
    if not [p for p in patterns if not p.startswith(":(")]:
        raise ConfigHashError(f"정본 파일에 포함 패턴이 0건이다: {path}")
    return patterns


def include_patterns(path: Path) -> list[str]:
    """Patterns a path filter must cover (exclusions only narrow the hash, not the trigger)."""
    return [p for p in read_patterns(path) if not p.startswith(":(")]


def pathspecs(patterns: list[str]) -> list[str]:
    return [(":(exclude,glob)" + p[len(EXCLUDE):]) if p.startswith(EXCLUDE) else (":(glob)" + p)
            for p in patterns]


def _git(root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    except OSError as exc:
        raise ConfigHashError(f"git 을 실행하지 못했다: {exc}") from exc
    if result.returncode != 0:
        raise ConfigHashError("git %s 실패(rc=%d): %s" % (
            args[0], result.returncode, result.stderr.decode("utf-8", "replace").strip()))
    return result.stdout


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _entry_sha(root: Path, rel: str, in_set: set[str]) -> str:
    path = root / rel
    if path.is_symlink():
        sha = "link:" + blob_sha(os.fsencode(os.readlink(path)))
        if not path.exists():
            return "missing:" + sha
        real = Path(os.path.realpath(path))
        if real.is_file():
            try:
                target = real.relative_to(root.resolve()).as_posix()
            except ValueError:
                target = None
            if target not in in_set:
                sha += "+" + blob_sha(real.read_bytes())
        return sha
    if not path.exists():
        return "missing"
    if path.is_dir():  # untracked nested repository listed as `dir/`
        return "dir"
    return blob_sha(path.read_bytes())


def entries(root: Path, patterns: list[str] | None = None) -> list[tuple[str, str]]:
    root = Path(root)
    if patterns is None:
        patterns = read_patterns(root / PATHS_REL)
    raw = _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--",
               *pathspecs(patterns))
    paths = sorted({p for p in raw.decode("utf-8", "surrogateescape").split("\0") if p})
    in_set = set(paths)
    return [(rel, _entry_sha(root, rel, in_set)) for rel in paths]


def _dirty(root: Path, patterns: list[str]) -> list[str]:
    raw = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--",
               *pathspecs(patterns))
    tokens = raw.decode("utf-8", "surrogateescape").split("\0")
    out, i = [], 0
    while i < len(tokens):
        token = tokens[i]
        i += 1
        if len(token) < 4:
            continue
        out.append(token[3:])
        if token[0] in "RC":  # rename/copy carries the original path as the next token
            i += 1
    return sorted(set(out))


def compute(root: Path, selected: str = "all", claude_version: str = "") -> dict:
    root = Path(root)
    paths_file = root / PATHS_REL
    patterns = read_patterns(paths_file)
    listed = entries(root, patterns)
    digest = hashlib.sha256()
    for rel, sha in listed:
        digest.update(rel.encode("utf-8", "surrogateescape") + b"\0" + sha.encode("ascii") + b"\n")
    try:
        head = _git(root, "rev-parse", "--verify", "-q", "HEAD").decode().strip() or None
    except ConfigHashError:
        head = None  # repository without commits
    return {
        "schema": SCHEMA,
        "hash": digest.hexdigest(),
        "files": len(listed),
        "head": head,
        "dirty": _dirty(root, patterns),
        "selected": selected,
        "patterns_sha256": hashlib.sha256(paths_file.read_bytes()).hexdigest(),
        "claude_version": claude_version,
        "computed_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _summary(run: Path) -> tuple[int, list[tuple[str, str]]]:
    """(준비 count, [(task, verdict)]) from results/<run>/summary.md."""
    try:
        text = (run / "summary.md").read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigHashError(f"{run.name}/summary.md 를 읽지 못했다: {exc}") from exc
    match = SUMMARY_RE.search(text)
    rows = ROW_RE.findall(text)
    if match is None or not rows:
        raise ConfigHashError(f"{run.name}/summary.md 의 요약줄·과제 표를 읽지 못했다")
    return int(match.group(5)), rows


def mode_rate_tasks(root: Path) -> set[str]:
    """Task dirs `eval/harness/H??-*/` whose `mode` file says exactly `rate` (15라운드 판정 H18-rate).

    The marker is inside the hash set, so a hash-matched result must carry exactly these rate rows."""
    found = set()
    for mode in sorted((Path(root) / "eval/harness").glob("H[0-9][0-9]-*/mode")):
        try:
            text = mode.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConfigHashError(f"{mode.parent.name}/mode 를 읽지 못했다: {exc}") from exc
        if text.rstrip("\n") == MODE_RATE:
            found.add(mode.parent.name)
    return found


def verify(root: Path, results: Path, tasks: int) -> tuple[int, str, str]:
    """Return (exit code, current hash, detail)."""
    try:
        current = compute(root)["hash"]
    except ConfigHashError as exc:
        return 78, "unknown", f"현재 설정 해시를 계산하지 못했다 — {exc}"
    results = Path(results)
    if not results.is_dir():
        return 78, current, f"결과 뿌리가 없다: {results}"
    runs = sorted(d for d in results.iterdir() if d.is_dir() and RUN_ID_RE.match(d.name))
    meta: dict[str, dict] = {}
    for run in runs:
        path = run / "config-hash.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("hash"), str):
                raise ValueError("hash 필드 없음")
        except (OSError, ValueError) as exc:
            return 78, current, f"{run.name}/config-hash.json 을 읽지 못했다(손상) — {exc}"
        meta[run.name] = data

    try:
        candidates, rejected = [], []
        for run in runs:
            data = meta.get(run.name)
            if data is None or data["hash"] != current:
                continue
            if data.get("selected") != "all":
                rejected.append(f"{run.name}: 선택 실행 {data.get('selected')}")
                continue
            ready, rows = _summary(run)
            if ready != 0:
                rejected.append(f"{run.name}: 준비 {ready}")
            elif len(rows) != tasks:
                rejected.append(f"{run.name}: 과제 {len(rows)} ≠ {tasks}")
            else:
                candidates.append((run, rows))
        if not candidates:
            why = " · ".join(rejected) if rejected else "해시 일치 회차 0건"
            return 78, current, (f"현재 설정 해시와 일치하는 전수 결과(선택 실행 아님 · 준비 0 · 과제 {tasks})가 "
                                 f"{results} 에 없다 ({why})")
        best, best_rows = candidates[-1]
        previous, prev_rows = None, []
        # Newest first: the first full result (row count == tasks) is the baseline. Unreadable
        # summaries on the way are still 78, as before, rather than being skipped silently.
        for run in reversed(runs):
            if run.name >= best.name or not (run / "summary.md").is_file():
                continue
            if run.name in meta and meta[run.name].get("selected") != "all":
                continue
            _, rows = _summary(run)
            if len(rows) == tasks:
                previous, prev_rows = run, rows
                break
        green = {name for name, verdict in best_rows if verdict == "green"}
        # Rate tasks are reported as a rate and left out of the regression set. `results/**` is outside
        # the hash set, so the rate rows must equal the `mode` markers of the hashed tree (검증 #1 · #7).
        rate = {name for name, verdict in best_rows if verdict.startswith("rate")}
        malformed = sorted(f"{n} {v!r}" for n, v in best_rows if n in rate and not RATE_RE.match(v))
        if malformed:
            raise ConfigHashError(f"{best.name}/summary.md 의 rate 판정 칸을 읽지 못했다(rate [0-2]/2 아님): "
                                  + ", ".join(malformed))
        expected_rate = mode_rate_tasks(root)
        if rate != expected_rate:
            return 78, current, (f"해시 일치 결과 아님 — {best.name} 의 rate 행 {sorted(rate) or '없음'} ≠ "
                                 f"eval/harness/H??-*/mode=rate 표지 {sorted(expected_rate) or '없음'}")
        rate_detail = (" · rate %d(%s)" % (len(rate), ", ".join(f"{n} {v[5:]}" for n, v in best_rows if n in rate))
                       if rate else " · rate 0")
        if previous is not None:
            regressed = sorted({name for name, verdict in prev_rows if verdict == "green"} - green - rate)
            if regressed:
                return 1, current, (f"회귀 — 직전 {previous.name} 에서 green 이던 과제 {len(regressed)}건이 "
                                    f"일치 결과 {best.name} 에서 green 이 아니다: {', '.join(regressed)}")
    except ConfigHashError as exc:
        return 78, current, str(exc)
    return 0, current, (f"hash(head)={current} hash(회차)={meta[best.name]['hash']} 일치 결과 {best.name} · "
                        f"green {len(green)}/{tasks} · 판정 red {tasks - len(green) - len(rate)}{rate_detail} · "
                        f"직전 {previous.name if previous else '없음'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("compute")
    c.add_argument("--root", type=Path, required=True)
    c.add_argument("--selected", default="all")
    c.add_argument("--claude-version", default="")
    v = sub.add_parser("verify")
    v.add_argument("--root", type=Path, required=True)
    v.add_argument("--results", type=Path, required=True)
    v.add_argument("--tasks", type=int, required=True)
    args = parser.parse_args(argv)
    if args.command == "compute":
        try:
            data = compute(args.root, args.selected, args.claude_version)
        except ConfigHashError as exc:
            print(f"::error::config-hash red(준비) — {exc}", file=sys.stderr)
            return 78
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    try:
        code, current, detail = verify(args.root, args.results, args.tasks)
    except Exception as exc:  # an unexpected crash must read as 78, never as regression (1)
        code, current, detail = 78, "unknown", f"검증기 오류: {exc!r}"
    print(f"{current}\t{detail}")
    return code


if __name__ == "__main__":
    sys.exit(main())
