import json, subprocess
ROOT = "<repo>"
HOOK = ROOT + "/scripts/harness/hooks/git-guard.sh"
G = "gi" + "t"
Q = '"' + ROOT + '"'
cases = [
    ("spaced -C, subagent push develop", G + " -C " + Q + " push origin develop", "agent-x"),
    ("no -C, subagent push develop", G + " push origin develop", "agent-x"),
    ("spaced -C, force push develop", G + " -C " + Q + " push --force origin develop", ""),
    ("no -C, force push develop", G + " push --force origin develop", ""),
    ("spaced -C, branch -D develop", G + " -C " + Q + " branch -D develop", ""),
    ("no -C, branch -D develop", G + " branch -D develop", ""),
    ("spaced -C, subagent push main", G + " -C " + Q + " push origin main", "agent-x"),
    ("no -C, subagent push main", G + " push origin main", "agent-x"),
    ("unspaced -C /tmp, force push develop", G + " -C /tmp push --force origin develop", ""),
]
for name, cmd, aid in cases:
    p = {"session_id": "probe", "transcript_path": "/dev/null", "cwd": ROOT,
         "hook_event_name": "PreToolUse", "tool_name": "Bash",
         "tool_input": {"command": cmd}, "tool_use_id": "t1"}
    if aid:
        p["agent_id"] = aid; p["agent_type"] = "lane-worker"
    r = subprocess.run(["bash", HOOK], input=json.dumps(p), capture_output=True, text=True)
    print(f"rc={r.returncode}  {name}  | {r.stderr.strip()[:90]}")
