#!/usr/bin/env python3
"""Claude/Codex lifecycle bridge. Guards never execute the command being inspected."""
from __future__ import annotations

import argparse
import collections
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude/hooks"))
from lifecycle_contract import validate_report, load_task, verify_task_report


def tool_environment() -> dict[str, str]:
    """Expose existing user-installed tools to non-login WSL child processes."""
    env = dict(os.environ)
    bins = (Path.home()/'.local/bin', Path.home()/'.npm-global/bin')
    env['PATH'] = os.pathsep.join([*(str(p) for p in bins), env.get('PATH', '')])
    return env


def run_tool(tool: str, args: list[str]) -> int:
    """Resolve the existing WSL npm prefix for this child process only."""
    if os.name == "nt":
        print("red(준비): use scripts/dev.ps1 to run Linux tools in WSL", file=sys.stderr)
        return 78
    env = tool_environment()
    if args[:1] == ["--"]:
        args = args[1:]
    if tool == "browser":
        binary = shutil.which("agent-browser", path=env["PATH"])
        if not binary:
            print("red(준비): agent-browser not found in WSL PATH or ~/.npm-global/bin", file=sys.stderr)
            return 78
        command = [binary, *args]
    elif tool == "gate":
        binary = shutil.which("bash", path=env["PATH"])
        if not binary:
            return 78
        command = [binary, str(ROOT / "gates/run.sh"), *args]
    else:
        command = [sys.executable, str(Path(__file__).resolve()), *(args or ["doctor"])]
    return subprocess.run(command, cwd=ROOT, env=env).returncode


def git(*args: str, root: Path = ROOT) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def registered_hooks(tool: str, event: str = "PreToolUse") -> list[Path]:
    settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
    paths = []
    for entry in settings["hooks"].get(event, []):
        if not re.fullmatch(entry["matcher"], tool):
            continue
        for hook in entry["hooks"]:
            # Parse only the existing command convention; never eval settings as shell code.
            match = re.fullmatch(r'bash "\$\{CLAUDE_PROJECT_DIR\}/(\.claude/hooks/[\w-]+\.sh)"', hook["command"])
            if hook.get("type") != "command" or not match:
                raise ValueError(f"unsupported {event} registration; review bridge mapping")
            path = ROOT / match[1]
            if not path.is_file():
                raise ValueError(f"missing hook: {match[1]}")
            paths.append(path)
    if not paths and event == "PreToolUse":
        raise ValueError(f"no registered hooks for {tool}")
    return paths


def check() -> None:
    for role in ("advisor", "lane-worker", "researcher", "gate-runner"):
        config = tomllib.loads((ROOT / f".codex/agents/{role}.toml").read_text(encoding="utf-8"))
        for field in ("name", "description", "developer_instructions"):
            if not isinstance(config.get(field), str) or not config[field]:
                raise ValueError(f"{role}: missing {field}")
        source = f".claude/agents/{role}.md"
        if config["name"] != role or source not in config["developer_instructions"] or not (ROOT / source).is_file():
            raise ValueError(f"{role}: invalid source mapping")
        if role == "advisor" and config.get("sandbox_mode") != "read-only":
            raise ValueError("advisor must be read-only")
    skills = sorted(p.parent.name for p in (ROOT / ".claude/skills").glob("*/SKILL.md"))
    if not skills:
        raise ValueError("no source skills")
    for skill in skills:
        body = (ROOT / f".agents/skills/{skill}/SKILL.md").read_text(encoding="utf-8")
        if not body.startswith("---\n") or f"name: {skill}\n" not in body or "description:" not in body:
            raise ValueError(f"invalid skill metadata: {skill}")
        for source in re.findall(r"`([^`]+/SKILL\.md)`", body):
            if not (ROOT / source).is_file():
                raise ValueError(f"missing skill source: {source}")
    for tool in ("Bash", "Edit"):
        registered_hooks(tool)
    settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
    codex = json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
    if set(settings["hooks"]) != {name for name in codex["hooks"] if name != "Stop"}:
        raise ValueError("hook event coverage differs")
    stop = codex["hooks"].get("Stop")
    if not isinstance(stop, list) or len(stop) != 1 or "matcher" in stop[0]:
        raise ValueError("Stop hook must be one matcher-free command definition")
    stop_hooks = stop[0].get("hooks")
    if not isinstance(stop_hooks, list) or len(stop_hooks) != 1 or stop_hooks[0].get("type") != "command" \
       or not all(stop_hooks[0].get(key) for key in ("command", "commandWindows")):
        raise ValueError("invalid Stop command hook")
    count = 0
    for event, entries in settings["hooks"].items():
        expected = ["apply_patch" if e["matcher"] == "Edit|Write" else e["matcher"] for e in entries]
        actual = [e.get("matcher") for e in codex["hooks"][event]]
        if expected != actual:
            raise ValueError(f"{event}: hook matcher coverage differs")
        for entry in entries:
            probe = entry["matcher"].split("|")[0]
            count += len(registered_hooks(probe, event))
    print(f"green: 4 role mappings, {len(skills)} skill adapters, {count} hook mappings / {len(codex['hooks'])} events")


def run_registered(payload: dict) -> int:
    if os.name == "nt" or not shutil.which("bash") or not shutil.which("python3"):
        print("red(준비): run guards inside the existing WSL/Linux environment", file=sys.stderr)
        return 78
    if os.environ.get("COLAB_HOOKS") == "0":
        raise ValueError("COLAB_HOOKS=0: cannot claim an active guard")
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(ROOT), COLAB_HOOKS="1")
    for hook in registered_hooks(payload["tool_name"]):
        result = subprocess.run(["bash", str(hook)], input=json.dumps(payload), text=True,
                                cwd=ROOT, env=env, timeout=30)
        if result.returncode:
            print(f"guard rejected: {hook.name} (exit {result.returncode})", file=sys.stderr)
            return 2 if result.returncode == 2 else 78
    return 0


def guard(args: argparse.Namespace) -> int:
    tool = "Bash" if args.action == "guard-command" else "Edit"
    if tool == "Bash":
        if not args.command.strip():
            raise ValueError("empty command")
        ti = {"command": args.command}
    else:
        target = (ROOT / args.path).resolve()
        if not target.is_relative_to(ROOT):
            raise ValueError("edit path outside this checkout")
        ti = {"file_path": str(target)}
        if args.new_string is not None:
            ti["new_string"] = args.new_string
    payload = {"cwd": str(ROOT), "tool_name": tool, "tool_input": ti,
               "hook_event_name": "PreToolUse"}
    if args.worker:
        payload["agent_id"] = "codex-worker"
    rc = run_registered(payload)
    if rc:
        return rc
    print("green: registered guards accepted; requested command/edit was NOT executed")
    return 0


def patch_paths(patch: str) -> list[str]:
    lines = patch.strip().splitlines()
    if len(lines) < 3 or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise ValueError("invalid patch envelope")
    paths = []
    action = None
    moved = False
    for line in lines[1:-1]:
        match = re.match(r"^\*\*\* (Add File|Update File|Delete File|Move to): (.*)$", line)
        if not match:
            continue
        kind, path = match.groups()
        if not path.strip() or "\x00" in path:
            raise ValueError("empty or invalid patch path")
        if kind == "Move to":
            if action != "Update File" or moved:
                raise ValueError("move without update or duplicate move")
            moved = True
        else:
            action, moved = kind, False
        paths.append(path)
    if not paths:
        raise ValueError("patch contains no target paths")
    return list(dict.fromkeys(paths))


def patch_new_text(patch: str) -> dict[str, str]:
    """Preserve per-file inserted/context text for the shared decision-number judge."""
    result, targets, lines = {}, [], []
    def finish():
        for target in targets:
            result[target] = result.get(target, '') + '\n'.join(lines)
    for line in patch.strip().splitlines()[1:-1]:
        match = re.match(r"^\*\*\* (Add File|Update File|Delete File|Move to): (.*)$", line)
        if match:
            kind, name = match.groups()
            if kind == 'Move to':
                targets.append(name)
            else:
                finish()
                targets, lines = [name], []
        elif line.startswith(('+', ' ')):
            lines.append(line[1:])
    finish()
    return result


def event_path(value: str, cwd: Path) -> Path:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError("invalid event path")
    if os.name != "nt" and re.match(r"^[A-Za-z]:[\\/]", value):
        win = PureWindowsPath(value)
        value = str(Path("/mnt") / win.drive[0].lower() / Path(*win.parts[1:]))
    path = (cwd / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("event path outside this checkout")
    return path


def codex_payloads(data: dict) -> list[dict]:
    if not isinstance(data, dict) or data.get("hook_event_name") not in ("PreToolUse", "PostToolUse"):
        raise ValueError("expected tool event")
    cwd = event_path(data.get("cwd"), ROOT)
    tool = data.get("tool_name")
    ti = data.get("tool_input")
    if tool not in ("Bash", "apply_patch") or not isinstance(ti, dict):
        raise ValueError("unsupported tool payload")
    command = ti.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("missing tool_input.command")
    base = {"cwd": str(cwd), "hook_event_name": data["hook_event_name"]}
    if data.get("agent_id"):
        base["agent_id"] = data["agent_id"]
    if tool == "Bash":
        return [dict(base, tool_name="Bash", tool_input={"command": command})]
    # Resolve every path before invoking any guard, including a move's destination.
    texts = patch_new_text(command)
    paths = [(path, event_path(path, cwd)) for path in patch_paths(command)]
    return [dict(base, tool_name="Edit", tool_input={"file_path": str(path), "new_string": texts.get(raw, '')})
            for raw, path in paths]


def codex_event() -> int:
    """stdin adapter for reviewed lifecycle hooks; pre-tool checks never run the proposed operation."""
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
        if os.name == "nt":
            # Native hook -> existing WSL guards. No shell interpolation and no trust bypass.
            controls = {key: os.environ.get(key) for key in (
                "COLAB_HOOKS", "COLAB_FIX_LANE", "COLAB_ALLOW_TEST_EDIT", "COLAB_GATE_REPORT_DIR",
                "COLAB_TASK_ID", "COLAB_ROUND")}
            bootstrap = ("import json,os,runpy,sys; controls=json.loads(sys.argv[1]); "
                         "[(os.environ.pop(k,None) if v is None else os.environ.__setitem__(k,v)) "
                         "for k,v in controls.items()]; "
                         "sys.argv=['scripts/agent-bridge.py','codex-event']; "
                         "runpy.run_path(sys.argv[0],run_name='__main__')")
            result = subprocess.run(["wsl.exe", "--cd", str(ROOT), "-e", "python3", "-c",
                                     bootstrap, json.dumps(controls)],
                                    input=raw, text=True, encoding="utf-8", timeout=570)
            return 0 if result.returncode == 0 else 2
        output = dispatch_event(data)
        if output or data.get("hook_event_name") == "Stop":
            print(json.dumps(output, ensure_ascii=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError) as exc:
        # A hook error with exit 1 would fail open in Codex. Explicitly deny this operation.
        print(f"Codex guard cannot validate this operation: {exc}", file=sys.stderr)
        return 2


def dispatch_event(data: dict) -> dict:
    """Translate every registered lifecycle event; keep the existing shell judges."""
    if not isinstance(data, dict):
        raise ValueError("event must be an object")
    if os.environ.get("COLAB_HOOKS") == "0":
        raise ValueError("COLAB_HOOKS=0: hooks are disabled")
    event = data.get("hook_event_name")
    cwd = event_path(data.get("cwd"), ROOT)
    if event in ("PreToolUse", "PostToolUse"):
        payloads = codex_payloads(data)
        pairs = [(p, registered_hooks(p["tool_name"], event)) for p in payloads]
    elif event == "Stop":
        result = subprocess.run([sys.executable, str(ROOT / "scripts/slack_completion.py"), "hook"],
                                input=json.dumps(dict(data, cwd=str(cwd))), text=True,
                                capture_output=True, cwd=cwd, timeout=20)
        if result.returncode:
            raise ValueError("Slack completion hook failed")
        return json.loads(result.stdout or "{}")
    elif event in ("SessionStart", "SubagentStart", "SubagentStop"):
        selector = data.get("source") if event == "SessionStart" else data.get("agent_type")
        if not isinstance(selector, str) or not selector:
            raise ValueError("missing lifecycle selector")
        pairs = [(dict(data, cwd=str(cwd)), registered_hooks(selector, event))]
    else:
        raise ValueError(f"unsupported event: {event}")
    messages = []
    for payload, hooks in pairs:
        for hook in hooks:
            result = subprocess.run(["bash", str(hook)], input=json.dumps(payload),
                                    text=True, capture_output=True, cwd=cwd,
                                    env=dict(tool_environment(), CLAUDE_PROJECT_DIR=str(ROOT), COLAB_HOOKS="1"),
                                    timeout=540 if event == "SubagentStart" else 30)
            if result.returncode:
                raise ValueError(f"{hook.name}: {result.stderr.strip() or 'hook failed'} (exit {result.returncode})")
            if result.stdout.strip():
                messages.append(result.stdout.strip())
            if result.stderr.strip():
                messages.append(result.stderr.strip())
    if event == "SessionStart":
        messages.append("Codex: read AGENTS.md and docs/development/dual-agent.md. The user's selected round takes precedence over the mtime suggestion above; otherwise verify Git history and work-items.yaml. Claude tools and hooks are not assumed available.")
    if event == "SubagentStart":
        messages.append("Confirm the assigned checkout, branch and HEAD before writing. This hook prepares dependencies; it does not create an isolated checkout.")
    if not messages:
        return {}
    text = "\n".join(messages)
    if event in ("SessionStart", "SubagentStart", "PostToolUse"):
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}
    return {"systemMessage": text}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("check")
    sub.add_parser("doctor")
    sub.add_parser("codex-event")
    lifecycle = sub.add_parser("lifecycle")
    lifecycle.add_argument("args", nargs=argparse.REMAINDER)
    runner = sub.add_parser("run-tool")
    runner.add_argument("tool", choices=("browser", "gate", "bridge"))
    runner.add_argument("args", nargs=argparse.REMAINDER)
    cmd = sub.add_parser("guard-command")
    cmd.add_argument("--command", required=True)
    cmd.add_argument("--worker", action="store_true")
    edit = sub.add_parser("guard-edit")
    edit.add_argument("--path", required=True)
    edit.add_argument("--worker", action="store_true")
    edit.add_argument("--new-string", help="proposed content, required for decision-ledger checks")
    report = sub.add_parser("verify-report")
    report.add_argument("--report", required=True)
    report.add_argument("--task")
    report.add_argument("--gate", action="append", required=True)
    args = parser.parse_args()
    try:
        if args.action == "codex-event":
            return codex_event()
        if args.action == "lifecycle":
            return subprocess.run([sys.executable, str(ROOT / ".claude/hooks/lifecycle_contract.py"), *args.args], cwd=ROOT).returncode
        if args.action == "run-tool":
            return run_tool(args.tool, args.args)
        if args.action == "check":
            check()
        elif args.action == "doctor":
            check()
            print(f"platform: {sys.platform}; python: {sys.version.split()[0]}")
            for binary in ("git", "bash", "python3", "codex", "claude", "agent-browser"):
                print(f"{binary}: {'found' if shutil.which(binary) else 'missing'}")
            print("Informational only: no authentication, server, or E2E readiness claim.")
        elif args.action.startswith("guard-"):
            return guard(args)
        else:
            if args.task:
                task = load_task(ROOT, args.task)
                if set(args.gate) != set(task["gates"]):
                    raise ValueError("required gates differ from task declaration")
                verify_task_report(ROOT, task, args.report)
                print("green: task identity, explicit report/gates and current working files verified")
            else:
                if git("status", "--porcelain", "--untracked-files=all"):
                    raise ValueError("dirty checkout: use task-bound working-file evidence (--task)")
                data = json.loads((ROOT / args.report).read_text(encoding="utf-8"))
                validate_report(data, args.gate, git("rev-parse", "HEAD^{tree}"))
                print("green: explicit required gates, counts, clean checkout and HEAD tree verified")
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as exc:
        print(f"red: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
