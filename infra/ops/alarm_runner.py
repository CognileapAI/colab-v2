#!/usr/bin/env python3
"""상태형 운영 probe — 연속 실패/회복 전이에만 알림을 보낸다."""
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_SCHEMA = "colab.ops.alarm-state.v1"
EVENT_SCHEMA = "colab.ops.v1"
READINESS_EXIT = 78


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _emit(event: str, *, target: str, failure_count: int, level: str) -> dict[str, Any]:
    value = {
        "schema": EVENT_SCHEMA,
        "timestamp": _now(),
        "level": level,
        "event": event,
        "service": "ops-alarm",
        "target": target,
        "failure_count": failure_count,
    }
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
          flush=True)
    return value


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": STATE_SCHEMA, "targets": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("알람 state를 읽을 수 없다") from exc
    if (not isinstance(value, dict) or value.get("schema") != STATE_SCHEMA
            or not isinstance(value.get("targets"), dict)):
        raise ValueError("알람 state 스키마가 맞지 않는다")
    return value


def _save(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(raw)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(state, stream, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            stream.write("\n")
        os.chmod(tmp, 0o600)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def _webhook(path: Path) -> str:
    try:
        info = path.stat()
    except OSError as exc:
        raise FileNotFoundError("알림 webhook 파일이 없다") from exc
    if stat.S_IMODE(info.st_mode) != 0o600:
        raise PermissionError("알림 webhook 파일은 0600이어야 한다")
    value = path.read_text(encoding="utf-8").strip()
    if not value.startswith("https://") or "\n" in value:
        raise ValueError("알림 webhook 파일은 https URL 한 줄이어야 한다")
    return value


def _notify(url: str, event: dict[str, Any]) -> None:
    # event는 target/계수/시각뿐이다. probe stdout/stderr나 요청 값은 절대 보내지 않는다.
    request = urllib.request.Request(
        url, data=json.dumps(event, separators=(",", ":")).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "colab-ops-alarm/1"})
    with urllib.request.urlopen(request, timeout=10) as response:
        if not 200 <= response.status < 300:
            raise RuntimeError(f"webhook가 {response.status}로 답했다")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path)
    parser.add_argument("--target")
    parser.add_argument("--threshold", type=int)
    parser.add_argument("--webhook-file", type=Path)
    parser.add_argument("--check-webhook", type=Path)
    parser.add_argument("--observe-only", action="store_true")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.check_webhook is not None:
        try:
            _webhook(args.check_webhook)
        except (OSError, ValueError):
            print("::gate-readiness-failure::gate=ops-alarm|missing=valid-https-webhook-file", file=sys.stderr)
            return READINESS_EXIT
        return 0
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if args.state is None or args.target is None or args.threshold is None or not command or not 1 <= args.threshold <= 100 or args.timeout <= 0:
        print("alarm-runner red — command, threshold(1~100), timeout(>0)을 확인한다", file=sys.stderr)
        return 1
    webhook = None
    if not args.observe_only:
        if args.webhook_file is None:
            print("::gate-readiness-failure::gate=ops-alarm|missing=COLAB_OPS_ALERT_WEBHOOK_FILE",
                  file=sys.stderr)
            return READINESS_EXIT
        try:
            webhook = _webhook(args.webhook_file)
        except (OSError, ValueError) as exc:
            print(f"::gate-readiness-failure::gate=ops-alarm|detail={exc}", file=sys.stderr)
            return READINESS_EXIT
    try:
        state = _load(args.state)
    except ValueError as exc:
        print(f"alarm-runner red — {exc}", file=sys.stderr)
        return 1

    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=args.timeout, check=False)
        passed = result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        passed = False

    targets = state["targets"]
    before = targets.get(args.target, {"failure_count": 0, "active": False})
    if not isinstance(before, dict):
        print("alarm-runner red — 대상 state가 객체가 아니다", file=sys.stderr)
        return 1
    failures = 0 if passed else int(before.get("failure_count", 0)) + 1
    active = bool(before.get("active", False))
    transition = None
    if not passed and failures >= args.threshold and not active:
        transition, active = "alarm.raised", True
    elif passed and active:
        transition, active = "alarm.cleared", False
    targets[args.target] = {"failure_count": failures, "active": active, "observed_at": _now()}

    _emit("probe.observed", target=args.target, failure_count=failures,
          level="INFO" if passed else "ERROR")
    if transition is not None:
        event = _emit(transition, target=args.target, failure_count=failures,
                      level="ERROR" if transition == "alarm.raised" else "INFO")
        if webhook is not None:
            try:
                _notify(webhook, event)
            except Exception as exc:  # 네트워크/HTTP 오류를 성공으로 접지 않는다.
                print(f"alarm-runner red — webhook 전송 실패: {type(exc).__name__}", file=sys.stderr)
                return 1
    _save(args.state, state)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
