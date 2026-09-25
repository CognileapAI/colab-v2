#!/usr/bin/env python3
"""report 단계 — 단계 조각을 모아 result.json 과 회차 기록 뼈대를 만든다.

- 입력 = `<실행 자리>/stages/*.json` · `preflight.json` · `counts.json` · `blocked.jsonl`
  · `preview-judgment.tsv` · `doctor-summary.txt` · `approval-record.json`.
- 판정 = `result-schema.json` 의 required·enum·타입을 직접 대조한다(외부 의존 없음).
- 비밀 값은 입력에 없다. 그래도 마지막에 한 번 더 훑어 의심 문자열이 있으면 비영 종료한다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys

STAGES = ["preflight", "rehearse", "deploy", "reset", "bootstrap", "up", "s3",
          "prelude", "seed", "verify", "report"]

# 결과 JSON 에 절대 실리면 안 되는 것 — 접속 문자열의 비밀번호 필드와 비밀번호 환경변수 이름.
SECRET_PATTERNS = [
    re.compile(r"://[^:/@\s]+:[^@\s]+@"),
    re.compile(r"(COLAB_OWNER_PASSWORD|COLAB_APP_PASSWORD|COLAB_AI_APP_PASSWORD"
               r"|COLAB_ACCOUNT_ADMIN_PASSWORD|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN)\s*="),
]


def _load(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _preview_rows(path: pathlib.Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        f = (line.split("\t") + [""] * 8)[:8]
        rows.append({
            "seq": f[0], "name": f[1], "processingLevel": f[2],
            # 모르는 값을 「미성립」으로 접지 않는다 — **재지 못한 것**과 **재서 어긋난 것**은 다르다.
            "verdict": f[3] if f[3] in ("성립", "미성립", "판정불가") else "판정불가",
            "elapsedMs": _count_or_none(f[4]) or 0,
            # 계수 칸이 `?`·빈 값(id 미확보 · 로그인 화면 · 값 못 받음)이면 **null** 로 둔다 — 0 으로 접으면
            # 「0 을 받았다」와 「못 받았다」가 같은 모양이 되고, int() 로 읽으면 report 가 죽는다
            # (4회차 `20260914T041707Z` 실측 · seq 13 의 `?` 행에서 `ValueError`).
            "unsetLevel": _count_or_none(f[5]), "usageCards": _count_or_none(f[6]),
            "note": f[7],
        })
    return rows


def _count_or_none(raw: str):
    s = (raw or "").strip()
    return int(s) if s.isdigit() else None


def validate(doc: dict, schema: dict) -> list[str]:
    """스키마의 required·enum·const·type 만 대조한다 — 이 문서가 쓰는 것이 그 셋이다."""
    errs: list[str] = []

    def check(node, spec, path):
        if "const" in spec and node != spec["const"]:
            errs.append(f"{path}: const {spec['const']} 아님 ({node!r})")
            return
        if "enum" in spec and node not in spec["enum"]:
            errs.append(f"{path}: enum 밖 값 {node!r}")
            return
        t = spec.get("type")
        types = t if isinstance(t, list) else ([t] if t else [])
        if types:
            ok = any(
                (ty == "object" and isinstance(node, dict))
                or (ty == "array" and isinstance(node, list))
                or (ty == "string" and isinstance(node, str))
                or (ty == "integer" and isinstance(node, int) and not isinstance(node, bool))
                or (ty == "boolean" and isinstance(node, bool))
                or (ty == "null" and node is None)
                for ty in types)
            if not ok:
                errs.append(f"{path}: 타입 {t} 아님 ({type(node).__name__})")
                return
        if isinstance(node, dict):
            for req in spec.get("required", []):
                if req not in node:
                    errs.append(f"{path}: 필수 필드 {req} 없음")
            props = spec.get("properties", {})
            if spec.get("additionalProperties") is False:
                for k in node:
                    if k not in props:
                        errs.append(f"{path}: 선언 밖 필드 {k}")
            for k, v in node.items():
                if k in props:
                    check(v, props[k], f"{path}.{k}")
        if isinstance(node, list) and "items" in spec:
            for i, v in enumerate(node):
                check(v, spec["items"], f"{path}[{i}]")

    check(doc, schema, "$")
    return errs


SESSION_TEMPLATE = """# DR-4 — dev 무인 재생성 실행 기록 ({date})

- 성격 = `dev-package/tools/dev-reseed/reseed.sh` 1회 실행의 **생성물**. 값의 원본은 `result.json` 이다.
- 승인 = dev 한정 상시 승인(`.claude/rules/deploy.md` 11번 증보 문단). 회차별 GO 불요 · 승인 기록 = `{approval}`.
- 실행 자리 = {run_dir} · 실행 식별자 `{run_id}` · 배포 대상 sha `{sha}`.
- 단계 로그와 승인 기록의 상대경로 기준은 실행 폴더다. `result.json`의 `runDir`는 JSON 파일 위치 기준이다.
- 결과 = **{outcome}**{failed_note} · 총 소요 {duration}초.

## 1. 단계별 소요

| 단계 | 상태 | 종료코드 | 소요(초) | 로그 |
|---|---|---|---|---|
{stage_rows}

## 2. 계수

{counts_block}

- `deploy_doctor` 요약줄 축자 = `{doctor}`
- 알려진 결함 면제 {known_defects}
- verify 재개 = {verify_from}

## 3. 미리보기 판정 표 ({preview_n} 행 · 성립 {preview_ok} · 판정불가 {preview_undecided})

| 순번 | 데이터셋 | 가공 단계 | 판정 | ms |
|---|---|---|---|---|
{preview_rows}

## 4. 차단 ({blocked_n} 건)

{blocked_block}

## 4-1. 자동 복구 ({recovery_n} 건)

{recovery_block}

## 5. 사람이 채울 자리

- 원장 등재문 · 대장 `DR-4` 상태 · `03-HANDOFF §1` 갱신은 오케스트레이터가 한다(레인·도구가 하지 않는다).
- 판정이 필요한 미성립 항목의 원인 분류(도구 결함 / 미리보기 뒷단 `PV-2`)를 여기에 적는다.
- **「판정불가」가 1건이라도 있으면 그 회차는 미리보기를 잰 것이 아니다** — 원인(브라우저 무응답 · 선택자 변경)을 먼저 적는다.
"""


def check_accounts(work,profile,target):
    import importlib.util
    spec=importlib.util.spec_from_file_location("reseed_accounts",pathlib.Path(__file__).with_name("accounts.py"))
    accounts=importlib.util.module_from_spec(spec);spec.loader.exec_module(accounts)
    try:
        work=pathlib.Path(work)
        entries=json.loads(accounts.private(profile).read_text())
        expected=json.loads(accounts.private(accounts.DEFAULT_PROFILE).read_text());accounts.validate(entries,expected)
        entries=sorted(entries,key=lambda e:[v['email'] for v in expected].index(e['email']))
        binding=accounts.proof(entries,work,None,target)
        final=json.loads(accounts.private(work/'finalization.json').read_text())
        checked=json.loads(accounts.private(work/'verification.json').read_text())
        identity={'profile':accounts.fingerprint(entries),'binding':binding}
        if final.get('state')!='complete' or any(final.get(k)!=v or checked.get(k)!=v for k,v in identity.items()):raise ValueError()
        required={'accounts':5,'operators':4,'professors':1,'must_change_password':True,'password_changed_by_check':False}
        if any(checked.get(k)!=v for k,v in required.items()):raise ValueError()
        # 소유자 관리 운영자 수는 승인 프로필과 같아야 한다(0 이면 표시가 없던 종전 증거도 받는다).
        owners=sum(map(accounts.owner_managed,entries))
        if checked.get('owner_managed',0)!=owners or checked.get('initial_logins',5)!=5-owners:raise ValueError()
    except Exception as exc:
        raise ValueError('required account verification evidence missing or changed') from exc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--target-sha", default="")
    ap.add_argument("--stages", default="")
    ap.add_argument("--dry-run", default="0")
    ap.add_argument("--schema", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--session-out", required=True)
    ap.add_argument("--accounts-work")
    ap.add_argument("--accounts-profile",default=os.environ.get("COLAB_RESEED_ACCOUNTS_PROFILE",str(pathlib.Path.home()/".config/colab-platform/dev-reseed-accounts-approved.json")))
    args = ap.parse_args()

    run = pathlib.Path(args.run_dir)
    # 실제 입력 경로는 그대로 읽고, 공개 기록에 직렬화하는 경로만 바꾼다.
    root = pathlib.Path(__file__).resolve().parents[3]
    try:
        session_run = f"`{run.resolve().relative_to(root)}` (레포 뿌리 기준)"
    except ValueError:
        session_run = "`<RUN_DIR>` (`--run-dir` 입력으로 지정한 실행 폴더; `result.json` 포함)"
    ran = [s for s in args.stages.split(",") if s]
    dry = args.dry_run == "1"

    stages, failed_stage = [], None
    for name in STAGES:
        piece = _load(run / "stages" / f"{name}.json", None)
        if piece is None:
            stages.append({"stage": name, "status": "skipped"})
            continue
        status = "ok" if piece.get("exitCode") == 0 else "failed"
        if status == "failed" and failed_stage is None:
            failed_stage = name
        piece["status"] = status
        stages.append(piece)

    blocked = []
    bl = run / "blocked.jsonl"
    if bl.exists():
        for line in bl.read_text(encoding="utf-8").splitlines():
            if line.strip():
                blocked.append(json.loads(line))

    if not dry and not failed_stage and not blocked and (not ran or any(s not in ('preflight','rehearse','report') for s in ran)):
        try:
            check_accounts(args.accounts_work,args.accounts_profile,args.target_sha)
        except ValueError:
            failed_stage='verify'
            blocked.append({'name':'accounts','stage':'verify','reason':'필수 5계정 최종화·로그인 검증 증거 없음 또는 변경'})

    # 정지 뒤 자동 재기동 기록. 없으면 되살릴 일이 없었다는 뜻이다.
    recovery = []
    rc = run / "recovery.jsonl"
    if rc.exists():
        for line in rc.read_text(encoding="utf-8").splitlines():
            if line.strip():
                recovery.append(json.loads(line))

    started = min((s["startedAt"] for s in stages if s.get("startedAt")), default="")
    ended = max((s["endedAt"] for s in stages if s.get("endedAt")), default="")
    duration = sum(int(s.get("durationSec") or 0) for s in stages)
    doctor = ""
    if (run / "doctor-summary.txt").exists():
        doctor = (run / "doctor-summary.txt").read_text(encoding="utf-8").strip()

    doc = {
        "schema": "colab-reseed-result/1",
        "runId": args.run_id,
        "startedAt": started or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "endedAt": ended or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "durationSec": duration,
        "dryRun": dry,
        "targetSha": args.target_sha,
        "runDir": os.path.relpath(run.resolve(), pathlib.Path(args.out).resolve().parent),
        "stages": stages,
        "counts": _load(run / "counts.json", {}),
        "blocked": blocked,
        "recovery": recovery,
        "approvalRecord": "approval-record.json" if (run / "approval-record.json").exists() else None,
        "outcome": "dry-run" if dry else ("failed" if failed_stage or blocked else "ok"),
        "failedStage": failed_stage,
    }
    pf = _load(run / "preflight.json", None)
    if pf is not None:
        doc["preflight"] = pf
    rows = _preview_rows(run / "preview-judgment.tsv")
    if rows:
        doc["previewJudgment"] = rows
    if doctor:
        doc["doctorSummary"] = doctor
    # `--verify-from` 재개 출처 — 앞 실행 자리 이름·runId·대상 sha·옮긴 파일 hash(절대경로 없음).
    vf = _load(run / "verify-from.json", None)
    if isinstance(vf, dict):
        doc["verifyFrom"] = {k: vf.get(k) for k in ("priorRunDirName", "priorRunId", "priorTargetSha",
                                                    "priorApprovalTargetSha", "targetShaMatches", "priorOutcome",
                                                    "priorFailedStage", "files")}

    schema = json.loads(pathlib.Path(args.schema).read_text(encoding="utf-8"))
    errs = validate(doc, schema)
    if errs:
        print("result.json 이 스키마와 어긋난다:", file=sys.stderr)
        for e in errs:
            print("  " + e, file=sys.stderr)
        return 1

    text = json.dumps(doc, ensure_ascii=False, indent=2)
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            print("result.json 에 비밀로 보이는 값이 있다 — 기록하지 않는다", file=sys.stderr)
            return 1
    pathlib.Path(args.out).write_text(text + "\n", encoding="utf-8")

    stage_rows = "\n".join(
        "| {stage} | {status} | {code} | {dur} | `{log}` |".format(
            stage=s["stage"], status=s["status"], code=s.get("exitCode", "—"),
            dur=s.get("durationSec", "—"), log=s.get("log", "—"))
        for s in stages)
    counts = doc["counts"]
    counts_block = ("```json\n" + json.dumps(counts, ensure_ascii=False, indent=2) + "\n```"
                    if counts else "- 계수 없음 — verify 단계를 돌지 않았다.")
    preview_rows = "\n".join(
        "| {seq} | {name} | {lv} | {v} | {ms} |".format(
            seq=r["seq"], name=r["name"], lv=r["processingLevel"], v=r["verdict"], ms=r["elapsedMs"])
        for r in rows) or "| — | — | — | — | — |"
    blocked_block = "\n".join(
        "- `{stage}` · **{name}** — {reason}".format(**b) for b in blocked) or "- 0 건."
    # 앱을 되살린 자리. 0 건 = 정지 뒤 실패가 없었다(사람이 손댈 일도 없었다).
    recovery_block = "\n".join(
        "- `{stage}` · **앱 재기동** — {reason} (종료코드 {exitCode})".format(**r)
        for r in recovery) or "- 0 건 — 정지 뒤 실패가 없었다."

    kd = counts.get("knownDefects") if isinstance(counts, dict) else None
    known_defects = ("{n}건{rows}".format(n=kd.get("exemptedCount", 0), rows="".join(
        " · seq {seq} {name} {issue}".format(**e) for e in kd.get("exempted", [])))
        + ("".join(" · 면제 불필요 seq {seq} {name} {issue}(known-defects.json 에서 뺄 것)".format(**e)
                   for e in kd.get("unneeded", [])))) if isinstance(kd, dict) else "— 대조 미실행"
    vfd = doc.get("verifyFrom")
    verify_from = ("앞 실행 `{priorRunDirName}` · runId `{priorRunId}` · 대상 sha `{priorTargetSha}` · "
                   "상세 화면 순회 생략(판정표·계수 옮김)").format(**vfd) + (
                   "" if vfd.get("targetShaMatches") else " · ⚠ 이번 대상 sha 와 다르다 — 두 배포 사이 미리보기 경로 변경 확인"
                   ) if vfd else "없음(상세 화면 순회)"
    pathlib.Path(args.session_out).write_text(SESSION_TEMPLATE.format(
        date=dt.date.today().isoformat(),
        approval=doc["approvalRecord"] or "없음(reset 단계 미실행)",
        run_dir=session_run, run_id=args.run_id, sha=args.target_sha or "—",
        outcome=doc["outcome"],
        failed_note=f"(멈춘 단계 `{failed_stage}`)" if failed_stage else "",
        duration=duration, stage_rows=stage_rows, counts_block=counts_block,
        doctor=doctor or "—", known_defects=known_defects, verify_from=verify_from, preview_n=len(rows),
        preview_ok=sum(1 for r in rows if r["verdict"] == "성립"),
        preview_undecided=sum(1 for r in rows if r["verdict"] == "판정불가"),
        preview_rows=preview_rows, blocked_n=len(blocked), blocked_block=blocked_block,
        recovery_n=len(recovery), recovery_block=recovery_block,
    ), encoding="utf-8")
    print("result.json · 회차 기록 뼈대 기록 · 단계 %d · 차단 %d" % (len(ran), len(blocked)))
    return 1 if failed_stage == "verify" and any("5계정" in b.get("reason", "") for b in blocked) else 0


if __name__ == "__main__":
    raise SystemExit(main())
