#!/usr/bin/env python3
"""**dev 한정** 환경 전면 초기화 — 계수 · 두 체인 스키마 재생성 · S3 접두사 2개 비우기.

⛔ **제품 기능이 아니다.** dev 에 쌓인 검증용 데이터를 한 지점으로 되돌리는 일회성 운영 도구이고,
제품 패키지 밖(`ops/`)이라 배포 이미지에 실리지 않는다. 실행 사유·승인자는 `PLAN-SoT §9` 행에 남고
**승인은 1회 소진이다**. 데이터셋 **행 단위** 삭제의 유일한 자리는 그대로 `ops/purge_datasets.py` 이고
이 도구가 그 자리를 대신하지 않는다(`.claude/rules/deploy.md` 「깨뜨리면 안 되는 것」 11번).

## dev 식별자 — 셋을 **모두** 만족해야 실행된다

  ⓐ `--target dev` ＋ `--yes-reset-dev`
  ⓑ `COLAB_CORE_S3_BUCKET` 이 `colab-platform-data-dev` 와 **정확히** 일치
  ⓒ 두 DB URL 의 **호스트**에 `-dev` 포함 (`deploy_doctor` ⑫ `env_pair_findings` 규약)

⚠ **DB 이름 단독은 판별력이 0 이다** — `colab_platform` 은 staging 과 같은 값이다. 그래서 호스트를 본다.
⚠ 접속 문자열은 **파일 경로로만** 받는다(`--platform-url-file`·`--ai-url-file`). 값을 받는 argv 인자는
   **아예 없고**, 출력·예외 어디에도 URL 을 싣지 않는다.

## 단계 — 이 도구는 ⑴⑵⑸ 만 한다

  ⑴ `--phase count`     계수. 표별 행수(연구실 경계를 건 상태) · 접두사별 객체 수 · 진행 중 멀티파트 수.
  ⑵ `--phase schema`    두 체인 스키마 삭제·재생성. 끝나면 **다음 명령을 찍고 0 으로 끝난다.**
  ⑸ `--phase s3-plan`   `uploads/`·`previews/` 의 **exact key** 목록 ＋ 진행 중 멀티파트를 계획 파일로.
     `--phase s3-apply` 그 계획의 키만 삭제 ＋ 멀티파트 중단. `--plan-sha256` 대조가 있어야 돈다.

⭑ **⑵′ 확장 · ⑶ 마이그레이션 · ⑷ 앱 권한은 이 도구에 없다.** 앱 이미지에 alembic 이 없고
  (`infra/dev/migrator/Dockerfile` 의 별도 이미지가 소유자 롤로 돈다) 부트스트랩은 셸 스크립트다.
  그래서 `--phase schema` 는 끝에 **그 다음에 사람이 내야 할 명령을 축자로 찍는다**:

    bash infra/dev/db-bootstrap.sh extensions            # ⑵′ pg_trgm 재생성(멱등)
    bash infra/dev/up.sh  의 ① 마이그레이션 단계          # ⑶ migrate-platform · migrate-ai
    bash infra/dev/db-bootstrap.sh app-grants            # ⑷ 앱 롤 GRANT — 재실행이 **필수**다
    bash infra/dev/db-bootstrap.sh account-admin         #    기본 권한은 스키마와 함께 사라진다

  ⚠ 각 명령이 비영 종료하면 그 자리에서 멈춘다 — 다음 명령을 내지 않는다.

## 왜 `account_admin` 을 같이 지우는가

`db/platform/versions/0025_stage3_accounts.py` 가 `CREATE SCHEMA account_admin` 을 `IF NOT EXISTS`
없이 낸다 ⟹ 남겨 두면 재-upgrade 가 0025 에서 죽는다. `alembic downgrade base` 는 대안이 아니다 —
같은 파일의 downgrade 가 자격 행이 있으면 `RAISE EXCEPTION` 한다.

## 무접촉

`_ops/`(백업 접두사). 계획 파일에 그 접두사 키가 **1건이라도** 있으면 전체를 거부한다 —
지우면 `deploy_doctor` ⑭(백업 24h)가 red 다. 접두사 삭제·`--recursive` API 를 쓰지 않고
**exact key 목록**으로만 지운다(선례 `PLAN-SoT §9 〈354〉`).

## 쓰는 법 (dev EC2 위 · `docs/DEPLOY.md §6-1` 의 격리 실행과 같은 모양)

    docker run --rm --network host --user 0 \\
      -v $COLAB_DEV_SECRETS_DIR/platform-owner-db.url:/s/platform.url:ro \\
      -v $COLAB_DEV_SECRETS_DIR/ai-owner-db.url:/s/ai.url:ro \\
      -v <이 파일>:/tmp/reset.py:ro -v /tmp/out:/out \\
      -e COLAB_CORE_S3_BUCKET -e COLAB_CORE_S3_REGION \\
      colab-v2/core-api:dev python /tmp/reset.py \\
        --target dev --yes-reset-dev --phase count \\
        --platform-url-file /s/platform.url --ai-url-file /s/ai.url --report /out/count.json

`--dry-run` 은 모든 검사·목록을 그대로 하고 보고서·계획을 쓰되 **파괴적인 일을 하나도 하지 않는다**.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import pathlib
import stat
import sys
import urllib.parse

#: ⓑ dev 데이터 버킷. 이름 하나로 환경이 갈린다.
EXPECTED_BUCKET = "colab-platform-data-dev"

#: ⓒ `deploy_doctor` ⑫ 와 같은 규약 — 호스트에 이 조각이 있어야 dev 다.
ENV_HOST_MARK = "-dev"

#: 지우는 접두사. **이 둘 뿐이다.**
ALLOWED_PREFIXES = ("uploads/", "previews/")

#: ⛔ 무접촉 접두사. 계획에 1건이라도 들어오면 전체를 거부한다.
NEVER_TOUCH_PREFIXES = ("_ops/",)

#: 스키마 집합의 기대값. 어긋나면 아무것도 지우지 않고 멈춘다.
EXPECTED_SCHEMAS: dict[str, frozenset[str]] = {
    "platform": frozenset({"public", "account_admin"}),
    "ai": frozenset({"public"}),
}

#: 재생성 DDL. 소유자 롤이 슈퍼유저 없이 낸다(부트스트랩 `roles` 가 스키마 소유를 옮겨 둔다).
RECREATE_DDL: dict[str, tuple[str, ...]] = {
    "platform": (
        "DROP SCHEMA public, account_admin CASCADE",
        "CREATE SCHEMA public AUTHORIZATION colab_owner",
        "REVOKE CREATE ON SCHEMA public FROM PUBLIC",
    ),
    "ai": (
        "DROP SCHEMA public CASCADE",
        "CREATE SCHEMA public AUTHORIZATION colab_owner",
        "REVOKE CREATE ON SCHEMA public FROM PUBLIC",
    ),
}

#: 계수 대상. 전부 **FORCE RLS** 아래라 경계를 먼저 걸지 않으면 조용히 0 이 나온다.
COUNT_TABLES = ("d3_dataset", "d3_file", "d6_project", "d4_lineage_edge")

PLAN_SCHEMA = "colab-dev-reset-plan/1"
REPORT_SCHEMA = "colab-dev-reset-report/1"
PLAN_FIELDS = {"schema", "bucket", "keys", "multipartUploads", "sha256"}

#: 스키마 재생성 뒤 **사람이 내야 하는** 명령. 이 도구는 여기를 대신하지 않는다.
NEXT_COMMANDS = (
    "bash infra/dev/db-bootstrap.sh extensions",
    "bash infra/dev/up.sh 의 ① 마이그레이션 단계 (migrate-platform · migrate-ai)",
    "bash infra/dev/db-bootstrap.sh app-grants",
    "bash infra/dev/db-bootstrap.sh account-admin",
)

PHASES = ("count", "schema", "s3-plan", "s3-apply")

_REFUSE = 2        # 인자·환경·계획 파일 가드
_PRECONDITION = 3  # DB 실물이 기대와 다르다
_PARTIAL = 4       # 실행 중 부분 실패


# ── 가드 (시험이 직접 부른다) ───────────────────────────────────────────────

def bucket_refusal(name: str | None) -> str | None:
    """버킷 이름이 dev 것이 아니면 사유 한 줄. staging·prod 는 여기서 걸린다."""
    if not name:
        return f"COLAB_CORE_S3_BUCKET 이 비어 있다 — {EXPECTED_BUCKET} 여야 한다."
    if name != EXPECTED_BUCKET:
        return (f"버킷이 {name} 다 — {EXPECTED_BUCKET} 여야 한다. "
                "다른 환경의 벌이므로 아무것도 하지 않는다.")
    return None


def host_refusal(chain: str, host: str | None) -> str | None:
    """DB URL 의 **호스트**에 `-dev` 가 없으면 사유 한 줄. DB 이름은 보지 않는다."""
    if not host:
        return f"{chain} DB URL 에서 호스트를 읽지 못했다."
    if ENV_HOST_MARK not in host:
        return (f"{chain} DB 호스트 {host} 에 {ENV_HOST_MARK} 가 없다 — 다른 환경의 DB 다. "
                "DB 이름은 staging 과 같은 값이라 판별에 쓰지 않는다.")
    return None


def schema_set_refusal(chain: str, actual: set[str]) -> str | None:
    """비시스템 스키마 집합이 기대와 **정확히** 같지 않으면 사유 한 줄."""
    expected = EXPECTED_SCHEMAS[chain]
    if set(actual) == set(expected):
        return None
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    parts = [f"{chain} 의 비시스템 스키마 집합이 기대와 다르다 "
             f"(기대 {sorted(expected)} · 실측 {sorted(actual)})"]
    if missing:
        parts.append(f"없는 것 {missing}")
    if extra:
        parts.append(f"여분 {extra}")
    return " · ".join(parts) + " — 재생성하지 않는다."


def plan_key_refusal(keys) -> str | None:                    # noqa: ANN001
    """허용 접두사 밖 키가 1건이라도 있으면 사유 한 줄. **전체를 거부한다.**"""
    bad_ops = [k for k in keys if any(k.startswith(p) for p in NEVER_TOUCH_PREFIXES)]
    if bad_ops:
        return (f"계획에 무접촉 접두사 {NEVER_TOUCH_PREFIXES} 의 키가 {len(bad_ops)} 건 있다 "
                f"(예: {bad_ops[0]}) — `_ops/` 를 지우면 deploy_doctor ⑭ 가 red 다. 전체를 거부한다.")
    bad = [k for k in keys if not any(k.startswith(p) for p in ALLOWED_PREFIXES)]
    if bad:
        return (f"계획에 허용 접두사 {ALLOWED_PREFIXES} 밖의 키가 {len(bad)} 건 있다 "
                f"(예: {bad[0]!r}) — 전체를 거부한다.")
    return None


def plan_digest(payload: dict) -> str:
    """계획의 정규 직렬화 sha256. 키 순서가 달라도 같은 계획은 같은 값이다."""
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


# ── 파일 다루기 ────────────────────────────────────────────────────────────

def _private_file(path: str, what: str) -> str:
    """실행자 소유 mode 0600 일반 파일만 읽는다 (`app/storage_maintenance_cli._private_plan`)."""
    p = pathlib.Path(path)
    info = p.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"{what} 은 일반 파일이어야 한다")
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
        raise RuntimeError(f"{what} 은 실행자 소유 mode 0600 이어야 한다")
    return p.read_text(encoding="utf-8")


def _write_private_json(path: str, body: dict) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(body, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                 encoding="utf-8")
    p.chmod(0o600)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_url_file(path: str, chain: str) -> tuple[str, str | None]:
    """접속 URL 을 **파일에서만** 읽는다. 값은 돌려주되 절대 출력하지 않는다."""
    if "://" in path:
        raise RuntimeError(f"--{chain}-url-file 에는 접속 문자열이 아니라 **파일 경로**를 준다")
    url = pathlib.Path(path).read_text(encoding="utf-8").strip()
    if not url:
        raise RuntimeError(f"{chain} 접속 URL 파일이 비어 있다")
    host = urllib.parse.urlsplit(url).hostname
    # SQLAlchemy 표기도 받는다 — core 의 `*_DATABASE_URL_FILE` 을 그대로 줄 수 있게.
    return url.replace("postgresql+psycopg://", "postgresql://"), host


def _default_connect(url: str):                              # noqa: ANN201
    import psycopg  # 컨테이너 안에만 있다 — 모듈 상단에 두면 시험이 못 읽는다.
    return psycopg.connect(url, connect_timeout=15, autocommit=False)


def _default_s3(**kwargs):                                   # noqa: ANN003, ANN201
    from colab_core.kernel.s3 import S3Client
    return S3Client(**kwargs)


# ── DB 조회 ────────────────────────────────────────────────────────────────

_NAMESPACE_SQL = ("select nspname from pg_namespace "
                  "where nspname !~ '^pg_' and nspname <> 'information_schema' order by 1")


def _namespaces(cur) -> set[str]:                            # noqa: ANN001
    cur.execute(_NAMESPACE_SQL)
    return {row[0] for row in cur.fetchall()}


def _row_counts(cur) -> tuple[list[str], dict[str, int]]:    # noqa: ANN001
    """⭑ 경계를 **먼저** 건다. FORCE RLS 아래에서 경계 없는 `count(*)` 는 조용히 0 이다."""
    cur.execute("select id from d1_lab order by id")
    labs = [row[0] for row in cur.fetchall()]
    totals = {table: 0 for table in COUNT_TABLES}
    for lab in labs:
        cur.execute("select set_config('app.current_lab', %s, true)", (lab,))
        for table in COUNT_TABLES:
            cur.execute(f"select count(*) from {table}")
            row = cur.fetchone()
            totals[table] += int(row[0]) if row else 0
    return labs, totals


# ── S3 조회 ────────────────────────────────────────────────────────────────

def _s3_snapshot(s3) -> tuple[dict[str, list[str]], list[list[str]]]:   # noqa: ANN001
    objects = {prefix: sorted(key for key, _size in s3.list_objects(prefix))
               for prefix in ALLOWED_PREFIXES}
    uploads = sorted([key, upload_id]
                     for key, upload_id in s3.list_multipart_uploads(ALLOWED_PREFIXES[0]))
    return objects, uploads


# ── 단계 ───────────────────────────────────────────────────────────────────

def _phase_count(a, urls, bucket, region, connect, s3_factory) -> int:   # noqa: ANN001
    db: dict[str, dict] = {}
    for chain in ("platform", "ai"):
        with connect(urls[chain]) as conn:
            with conn.cursor() as cur:
                entry: dict = {"schemas": sorted(_namespaces(cur))}
                if chain == "platform":
                    labs, totals = _row_counts(cur)
                    entry["labs"] = len(labs)
                    entry["rows"] = totals
                db[chain] = entry
            conn.rollback()
    objects, uploads = _s3_snapshot(s3_factory(bucket=bucket, region=region))
    report = {
        "schema": REPORT_SCHEMA, "phase": "count", "at": _now(), "dryRun": bool(a.dry_run),
        "bucket": bucket, "db": db,
        "s3": {"objects": {p: len(objects[p]) for p in ALLOWED_PREFIXES},
               "multipartUploads": len(uploads)},
    }
    _write_private_json(a.report, report)
    print("── 계수 (연구실 경계를 건 상태에서 센 값)")
    for chain, entry in db.items():
        print(f"   {chain:<9} 스키마 {entry['schemas']}"
              + (f" · 연구실 {entry['labs']} · {entry['rows']}" if "rows" in entry else ""))
    for prefix in ALLOWED_PREFIXES:
        print(f"   S3 {prefix:<10} 객체 {len(objects[prefix])}")
    print(f"   S3 진행 중 멀티파트 {len(uploads)}")
    print(f"── 보고서: {a.report}")
    return 0


def _phase_schema(a, urls, bucket, connect) -> int:          # noqa: ANN001
    # ⭑ 두 체인을 **먼저 다 본 뒤에** 손을 댄다. 한쪽만 지우고 멈추면 부분 실행이다.
    observed: dict[str, set[str]] = {}
    refusals: list[str] = []
    for chain in ("platform", "ai"):
        with connect(urls[chain]) as conn:
            with conn.cursor() as cur:
                observed[chain] = _namespaces(cur)
            conn.rollback()
        refusal = schema_set_refusal(chain, observed[chain])
        if refusal:
            refusals.append(refusal)
    if refusals:
        for line in refusals:
            print(f"⛔ {line}", file=sys.stderr)
        return _PRECONDITION

    report = {"schema": REPORT_SCHEMA, "phase": "schema", "at": _now(),
              "dryRun": bool(a.dry_run), "bucket": bucket,
              "before": {c: sorted(s) for c, s in observed.items()},
              "statements": {c: list(RECREATE_DDL[c]) for c in ("platform", "ai")}}

    if a.dry_run:
        print("── dry-run 이다. 아래를 내지 않았다.")
        for chain in ("platform", "ai"):
            for sql in RECREATE_DDL[chain]:
                print(f"   {chain:<9} {sql}")
    else:
        for chain in ("platform", "ai"):
            with connect(urls[chain]) as conn:
                with conn.cursor() as cur:
                    for sql in RECREATE_DDL[chain]:
                        cur.execute(sql)
                        print(f"   {chain:<9} {sql}")
                conn.commit()
        print("── 두 체인 스키마 재생성 COMMIT.")

    _write_private_json(a.report, report)
    print("\n── 다음은 이 도구가 하지 않는다. 사람이 이 순서로 낸다"
          " (앱 이미지에 alembic 이 없다).")
    for i, cmd in enumerate(NEXT_COMMANDS, start=1):
        print(f"   {i}. {cmd}")
    print("   ⚠ 각 명령이 비영 종료하면 그 자리에서 멈춘다 — 다음 명령을 내지 않는다.")
    print(f"── 보고서: {a.report}")
    return 0


def _phase_s3_plan(a, bucket, region, s3_factory) -> int:    # noqa: ANN001
    if not a.plan_out:
        print("--phase s3-plan 에는 --plan-out 이 필요하다.", file=sys.stderr)
        return _REFUSE
    objects, uploads = _s3_snapshot(s3_factory(bucket=bucket, region=region))
    keys = sorted(k for prefix in ALLOWED_PREFIXES for k in objects[prefix])
    # 목록을 만든 쪽도 자기 산출을 검사한다 — 접두사 조회가 무엇을 돌려주든 계획은 좁다.
    refusal = plan_key_refusal(keys) or plan_key_refusal([k for k, _u in uploads])
    if refusal:
        print(f"⛔ {refusal}", file=sys.stderr)
        return _REFUSE
    payload = {"schema": PLAN_SCHEMA, "bucket": bucket,
               "keys": keys, "multipartUploads": [list(u) for u in uploads]}
    digest = plan_digest(payload)
    _write_private_json(a.plan_out, dict(payload, sha256=digest))
    _write_private_json(a.report, {
        "schema": REPORT_SCHEMA, "phase": "s3-plan", "at": _now(),
        "dryRun": bool(a.dry_run), "bucket": bucket, "plan": a.plan_out, "planSha256": digest,
        "before": {"objects": {p: len(objects[p]) for p in ALLOWED_PREFIXES},
                   "multipartUploads": len(uploads)}})
    print(f"── 계획 {a.plan_out} — 키 {len(keys)} 건 · 진행 중 멀티파트 {len(uploads)} 건")
    print(f"   sha256 {digest}")
    print("   적용은 `--phase s3-apply --apply-plan <위 파일> --plan-sha256 <위 값>` 이다.")
    return 0


def _parse_plan(raw: str, bucket: str, expected_sha: str) -> tuple[dict, str | None]:
    try:
        plan = json.loads(raw)
    except json.JSONDecodeError:
        return {}, "계획 파일 JSON 이 올바르지 않다."
    if not isinstance(plan, dict) or set(plan) != PLAN_FIELDS:
        return {}, f"계획 최상위 필드가 정확하지 않다 — {sorted(PLAN_FIELDS)} 여야 한다."
    if plan["schema"] != PLAN_SCHEMA:
        return {}, f"계획 schema 가 {PLAN_SCHEMA} 가 아니다."
    if plan["bucket"] != bucket:
        return {}, f"계획의 버킷이 실행 대상 버킷과 다르다 (계획 {plan['bucket']} · 실행 {bucket})."
    keys, uploads = plan["keys"], plan["multipartUploads"]
    if not isinstance(keys, list) or any(not isinstance(k, str) for k in keys):
        return {}, "계획 keys 는 문자열 목록이어야 한다."
    if (not isinstance(uploads, list)
            or any(not isinstance(u, list) or len(u) != 2
                   or any(not isinstance(x, str) for x in u) for u in uploads)):
        return {}, "계획 multipartUploads 는 [키, uploadId] 쌍 목록이어야 한다."
    if len(set(keys)) != len(keys):
        return {}, "계획 keys 에 중복이 있다."
    refusal = plan_key_refusal(keys) or plan_key_refusal([u[0] for u in uploads])
    if refusal:
        return {}, refusal
    payload = {k: v for k, v in plan.items() if k != "sha256"}
    real = plan_digest(payload)
    if real != plan["sha256"] or real != expected_sha:
        return {}, ("계획 sha256 이 어긋난다 — 파일 기재 "
                    f"{plan['sha256'][:12]}… · 인자 {expected_sha[:12]}… · 실측 {real[:12]}…")
    return plan, None


def _phase_s3_apply(a, bucket, region, s3_factory) -> int:   # noqa: ANN001
    if not a.apply_plan or not a.plan_sha256:
        print("--phase s3-apply 에는 --apply-plan 과 --plan-sha256 이 둘 다 필요하다.",
              file=sys.stderr)
        return _REFUSE
    try:
        raw = _private_file(a.apply_plan, "승인 계획")
    except (OSError, RuntimeError) as exc:
        print(f"⛔ {exc}", file=sys.stderr)
        return _REFUSE
    plan, refusal = _parse_plan(raw, bucket, a.plan_sha256)
    if refusal:
        print(f"⛔ {refusal}", file=sys.stderr)
        return _REFUSE

    s3 = s3_factory(bucket=bucket, region=region)
    keys = list(plan["keys"])
    uploads = [tuple(u) for u in plan["multipartUploads"]]
    print(f"── s3-apply — 키 {len(keys)} 건 · 멀티파트 {len(uploads)} 건"
          + (" · dry-run" if a.dry_run else ""))
    failures: list[str] = []
    if not a.dry_run:
        # 멀티파트를 먼저 중단한다 — 중단 전에 객체를 지우면 조각이 원장 없이 남는다.
        for key, upload_id in uploads:
            try:
                s3.abort_multipart_upload(key, upload_id)
            except Exception as exc:                          # noqa: BLE001
                failures.append(f"멀티파트 중단 실패 {key}: {type(exc).__name__}")
        if keys:
            try:
                s3.delete_objects(keys)
            except Exception as exc:                          # noqa: BLE001
                failures.append(f"객체 삭제 실패: {type(exc).__name__}")

    objects_after, uploads_after = _s3_snapshot(s3)
    _write_private_json(a.report, {
        "schema": REPORT_SCHEMA, "phase": "s3-apply", "at": _now(),
        "dryRun": bool(a.dry_run), "bucket": bucket, "planSha256": a.plan_sha256,
        "planned": {"keys": len(keys), "multipartUploads": len(uploads)},
        "after": {"objects": {p: len(objects_after[p]) for p in ALLOWED_PREFIXES},
                  "multipartUploads": len(uploads_after)},
        "failures": failures})
    for prefix in ALLOWED_PREFIXES:
        print(f"   실행 후 {prefix:<10} 객체 {len(objects_after[prefix])}")
    print(f"   실행 후 진행 중 멀티파트 {len(uploads_after)}")
    print(f"── 보고서: {a.report}")
    if failures:
        for line in failures:
            print(f"⛔ {line}", file=sys.stderr)
        return _PARTIAL
    return 0


# ── 진입점 ─────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None, *, connect=None, s3_factory=None) -> int:  # noqa: ANN001
    # ⚠ `allow_abbrev=False` 가 규율의 일부다 — 기본값(축약 허용)에서는 `--platform-url <URL>` 이
    #    `--platform-url-file` 의 축약으로 **받아들여진다.** 접속 문자열을 argv 로 받는 모양이
    #    오타 하나로 생기는 자리라 축약을 끈다(가드는 그대로 두 겹으로 남는다).
    ap = argparse.ArgumentParser(
        allow_abbrev=False,
        description="dev 전용 환경 전면 초기화 (계수 · 스키마 재생성 · S3 접두사 2개)")
    ap.add_argument("--target", required=True,
                    help="dev 하나만 받는다. staging·prod 는 거부한다.")
    ap.add_argument("--phase", required=True, choices=PHASES)
    ap.add_argument("--platform-url-file", required=True,
                    help="platform 소유자 롤 접속 URL 파일(0600). ⛔ 값을 argv 로 받지 않는다.")
    ap.add_argument("--ai-url-file", required=True,
                    help="ai 소유자 롤 접속 URL 파일(0600). ⛔ 값을 argv 로 받지 않는다.")
    ap.add_argument("--report", required=True, help="계수·실행 보고 JSON 을 쓸 자리(0600).")
    ap.add_argument("--yes-reset-dev", action="store_true",
                    help="이것이 없으면 아무 단계도 돌지 않는다.")
    ap.add_argument("--dry-run", action="store_true",
                    help="검사·목록·보고서는 하고 파괴적인 일은 하나도 하지 않는다.")
    ap.add_argument("--plan-out", help="--phase s3-plan 이 쓸 계획 파일 자리.")
    ap.add_argument("--apply-plan", help="--phase s3-apply 가 읽을 계획 파일(실행자 소유 0600).")
    ap.add_argument("--plan-sha256", help="--apply-plan 의 기대 sha256. 어긋나면 거부한다.")
    a = ap.parse_args(argv)

    def refuse(message: str) -> int:
        print(f"⛔ {message} 아무것도 하지 않았다.", file=sys.stderr)
        return _REFUSE

    # ⓐ 플래그 — 기본이 파괴이면 사고가 조용해진다.
    if a.target != "dev":
        return refuse(f"--target 은 dev 하나다 (받은 값 {a.target!r}).")
    if not a.yes_reset_dev:
        return refuse("--yes-reset-dev 가 없다.")

    # ⓑ 버킷.
    bucket = os.environ.get("COLAB_CORE_S3_BUCKET")
    refusal = bucket_refusal(bucket)
    if refusal:
        return refuse(refusal)
    region = os.environ.get("COLAB_CORE_S3_REGION")
    if not region:
        return refuse("COLAB_CORE_S3_REGION 이 비어 있다.")

    # ⓒ DB 호스트 — 값은 파일에서만 읽고 출력하지 않는다.
    urls: dict[str, str] = {}
    for chain, path in (("platform", a.platform_url_file), ("ai", a.ai_url_file)):
        try:
            url, host = _read_url_file(path, chain)
        except (OSError, RuntimeError) as exc:
            return refuse(str(exc) + ".")
        refusal = host_refusal(chain, host)
        if refusal:
            return refuse(refusal)
        urls[chain] = url

    connect = connect or _default_connect
    s3_factory = s3_factory or _default_s3

    if a.phase == "count":
        return _phase_count(a, urls, bucket, region, connect, s3_factory)
    if a.phase == "schema":
        return _phase_schema(a, urls, bucket, connect)
    if a.phase == "s3-plan":
        return _phase_s3_plan(a, bucket, region, s3_factory)
    return _phase_s3_apply(a, bucket, region, s3_factory)


if __name__ == "__main__":
    raise SystemExit(main())
