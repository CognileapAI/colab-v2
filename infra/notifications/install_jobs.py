from __future__ import annotations
import argparse,json
from pathlib import Path
def render(manifest:dict)->dict:
    if manifest.get("environment") not in {"dev","staging"} or manifest.get("usage") not in {"live","rehearsal"}:raise ValueError("invalid manifest")
    import shlex
    probes=manifest.get("probes")
    if not probes or any(not isinstance(p,dict) or not p.get("command") for p in probes):raise ValueError("explicit probe argv required")
    runtime_python=shlex.quote(manifest.get("runtime_python","python3"))
    base=runtime_python+" -m infra.notifications.cli"
    manifest_path=manifest.get("runtime_manifest_path","/etc/colab/operator-manifest.json")
    manifest_arg=" --manifest "+shlex.quote(manifest_path)+" --profile connected"
    commands=[base+" probe"+manifest_arg+" --target "+shlex.quote(p["target"])+" --state /var/lib/colab/operator/"+shlex.quote(p["target"])+".json --spool /var/lib/colab/operator-spool" for p in probes]
    return {"probe":{"minutes":5,"commands":commands,"command":commands[0]},
            "export":{"minutes":1,"command":runtime_python+" services/core-api/ops/operator_audit_export.py sync --manifest "+shlex.quote(manifest_path)},
            "spool":{"minutes":1,"command":base+" drain-spool --profile connected --spool /var/lib/colab/operator-spool"},
            "retry":{"minutes":1,"command":base+" publish-pending"+manifest_arg},
            "daily":{"expression":"cron(0 8 * * ? *)","timezone":"Asia/Seoul","catchup_minutes":5,"command":base+" daily "+manifest_arg.strip()}}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--manifest",required=True);mode=p.add_mutually_exclusive_group(required=True);mode.add_argument("--check",action="store_true");mode.add_argument("--render",action="store_true");mode.add_argument("--apply",action="store_true");args=p.parse_args(argv)
    try:value=render(json.loads(Path(args.manifest).read_text()))
    except (OSError,ValueError,KeyError,json.JSONDecodeError):return 78
    if args.apply:return 78
    if args.render:print(json.dumps(value,ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
