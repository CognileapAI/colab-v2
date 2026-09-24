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

  ⑴ `--phase count`     계수. 두 체인 모두 BYPASSRLS 롤(`--count-url-file` · `--count-ai-url-file` ·
                        `row_security=off`)로 센다 — 스키마의 **모든** 기본 표(pg_catalog 열거)의 행수와
                        행 내용 지문 · 정지 판정 표 일곱의 행수 · DB 가 가리키는 저장 키 · 접두사별 객체 수와
                        키 목록 sha256 · 진행 중 멀티파트. 보고서에 시각을 싣지 않는다 — 그 sha256 이 ack 대조값이다.
  ⑵ `--phase schema`    두 체인 스키마 삭제·재생성. **DROP 직전 같은 프로세스에서 다시 세어** `--count-report`
                        에 쓰고, 비어 있지 않은데(`nonempty_reasons`) `--ack-sha256` 이 그 재계수의 sha256 과
                        다르면 한 건도 지우지 않고 exit 3 이다. 끝나면 **다음 명령을 찍고 0 으로 끝난다.**
  ⑸ `--phase s3-plan`   `uploads/`·`previews/` 의 **exact key** 목록 ＋ 진행 중 멀티파트를 계획 파일로.
                        필수 = `--referenced-keys <⑵ 의 재계수>` ＋ `--referenced-sha256 <그 sha256>`(이번 reset 에
                        묶는다) ＋ `--count-url-file`(**지금** DB 가 가리키는 키 — 1건이라도 있으면 exit 3).
                        계획이 재계수의 참조 키와 겹치면 그 파일 sha256 을 `--ack-sha256` 로 받아야 쓴다.
                        `--dry-run` 이면 거부 사유를 찍고 `dryRun` 표지가 붙은 계획(적용 불가)을 쓴다.
     `--phase s3-apply` 그 계획의 키만 삭제 ＋ 멀티파트 중단. `--plan-sha256` 대조가 있어야 돈다.

⛔ **ack 는 사용자가 표별 계수를 보고 준 명시 GO 의 기록이다**(`.agents/rules/deploy.md` 11번 증보). 에이전트는
  계수 파일의 sha256 을 스스로 계산해 넘기지 않는다 — 비어 있지 않은 dev 는 상시 승인 밖이다.

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

재시드는 `dev-package/tools/dev-reseed/reseed.sh` 가 이 도구를 부른다(정지 게이트 · 1회용 ack). 손으로 부르면
아래 한 벌이다 — 계수 URL 두 파일은 백업 cron 이 쓰는 BYPASSRLS 읽기 롤(`colab_backup`)의 것이다.

    docker run --rm --network host --user 0 \\
      -v $COLAB_DEV_SECRETS_DIR/platform-owner-db.url:/s/platform.url:ro \\
      -v $COLAB_DEV_SECRETS_DIR/ai-owner-db.url:/s/ai.url:ro \\
      -v $COLAB_DEV_SECRETS_DIR/backup-platform-db.url:/s/count.url:ro \\
      -v $COLAB_DEV_SECRETS_DIR/backup-ai-db.url:/s/count-ai.url:ro \\
      -v <이 파일>:/tmp/reset.py:ro -v /tmp/out:/out \\
      -e COLAB_CORE_S3_BUCKET -e COLAB_CORE_S3_REGION \\
      colab-v2/core-api:dev python /tmp/reset.py \\
        --target dev --yes-reset-dev --phase count \\
        --platform-url-file /s/platform.url --ai-url-file /s/ai.url \\
        --count-url-file /s/count.url --count-ai-url-file /s/count-ai.url --report /out/count.json

    # 비어 있으면 ack 없이, 비어 있지 않으면 사용자 GO 를 받은 뒤에만 그 계수의 sha256 을 준다.
    … --phase schema --count-report /out/count-at-drop.json --report /out/schema.json [--ack-sha256 <sha256>]

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
#
# ⭑ 마지막 줄(`COMMENT ON SCHEMA`)이 없으면 `schema-diff` 가 red 다 — 실측(로컬 증명).
#   `initdb` 가 만든 `public` 은 주석 `standard public schema` 를 달고 있고, DROP·CREATE 하면
#   그 주석이 NULL 이 된다. `pg_dump` 는 그 차이를 `COMMENT ON SCHEMA public IS '';` 한 줄로
#   뽑고, 게이트는 선언 스키마와의 드리프트로 읽는다. 되돌려 놓는 것이 맞다 —
#   초기화 뒤 상태는 「마이그레이션을 처음 올린 DB」와 같아야 한다.
_PUBLIC_COMMENT = "COMMENT ON SCHEMA public IS 'standard public schema'"

RECREATE_DDL: dict[str, tuple[str, ...]] = {
    "platform": (
        "DROP SCHEMA public, account_admin CASCADE",
        "CREATE SCHEMA public AUTHORIZATION colab_owner",
        "REVOKE CREATE ON SCHEMA public FROM PUBLIC",
        _PUBLIC_COMMENT,
    ),
    "ai": (
        "DROP SCHEMA public CASCADE",
        "CREATE SCHEMA public AUTHORIZATION colab_owner",
        "REVOKE CREATE ON SCHEMA public FROM PUBLIC",
        _PUBLIC_COMMENT,
    ),
}

#: 계수 대상 — 사람이 만든 자료가 사는 표. **행 전수**를 센다(연구실 · 연구실 없는 행 · account_admin).
#
# ⭑ 2026-09-24 사고 — 종전 계수는 소유자 롤로 연구실마다 `app.current_lab` 을 걸고 표 넷만 셌다.
#   그 경로는 ⑴ `d1_lab` 에 없는 경계의 행을 못 보고 ⑵ `d3_file` 의 RESTRICTIVE `body_access`
#   (`db/platform/schema.sql` 「7. RLS」 ② · `CREATE POLICY body_access ON d3_file AS RESTRICTIVE`)에
#   잠긴 파일을 못 보며 ⑶ `account_admin` 을 세지 않았다. 그래서 계수는 소유자 경로가 아니라
#   **BYPASSRLS 읽기 전용 롤**(`colab_backup` · `infra/dev/db-bootstrap.sh backup-role`)로 한다.
COUNT_TABLES = ("d1_account", "account_admin.login_credential", "d3_dataset", "d3_file",
                "d5_upload", "d6_project", "d4_lineage_edge")

#: DB 행이 가리키는 저장 키의 출처. 스키마를 지우기 **전에** 모은다 — s3-plan 은 DROP 뒤에 돈다.
#  `d3_representative_image_cleanup` 은 지울 키의 대기열이라 넣지 않는다. `previews/` 는 파일 id 에서
#  파생되는 생성물이라 키 열이 없다(재생성 가능).
REFERENCED_KEY_SOURCES = ("d3_file", "d5_upload_file", "d5_upload_transfer_file",
                          "d3_dataset_representative_image")

#: 계수 보고서에 싣는 경로 표지 — 재시드 정지 게이트가 이 값이 아닌 계수를 판정 불가로 읽는다.
COUNT_PATH = "bypassrls:row_security=off"

#: 내용 지문 대상 — 체인별 스키마의 **모든** 기본 표를 pg_catalog 에서 열거한다(고정 목록이 아니다).
#
# ⭑ 2026-09-25 검토 — 고정 표 일곱의 행수만 해시하면 설명·변수 메타·접근 승인·AI 원장처럼 계수하지 않는
#   표의 편집, 계수 표의 UPDATE, 같은 개수의 S3 객체 교체가 토큰을 바꾸지 않는다. 그러면 운영자가 편집 전
#   상태를 보고 준 토큰이 편집 뒤에도 통과한다. 그래서 표마다 행수 ＋ 행 내용 지문(md5 의 정렬 결합)을 싣고
#   S3 는 접두사별 키 목록(키·크기)의 sha256 을 싣는다.
FINGERPRINT_SCHEMAS: dict[str, tuple[str, ...]] = {
    "platform": ("public", "account_admin"),
    "ai": ("public",),
}

# 파티션 부모(p)는 자식 행을 함께 세므로 자식(relispartition)은 뺀다. alembic 버전 표는 자료가 아니다.
_TABLES_SQL = ("select n.nspname, c.relname from pg_class c "
               "join pg_namespace n on n.oid = c.relnamespace "
               "where c.relkind in ('r', 'p') and not c.relispartition "
               "and n.nspname = any(%s) and c.relname not like 'alembic%%' "
               "order by 1, 2")

_SHA256_HEX = frozenset("0123456789abcdef")

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

#: 계수 URL(BYPASSRLS 읽기 롤)이 필요한 단계와 체인. `schema` 는 DROP 직전에 다시 세고,
#  `s3-plan` 은 **지금** DB 가 가리키는 키를 읽는다.
COUNT_URL_PHASES: dict[str, tuple[str, ...]] = {
    "count": ("platform", "ai"),
    "schema": ("platform", "ai"),
    "s3-plan": ("platform",),
}

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


def ack_token_refusal(token: str | None) -> str | None:
    """ack 토큰은 sha256 16진 64자다. 꼴이 틀리면 대조하기 전에 거부한다."""
    if token is None:
        return None
    if len(token) != 64 or not set(token) <= _SHA256_HEX:
        return "ack 토큰은 계수 파일의 sha256(소문자 16진 64자)이어야 한다."
    return None


def nonempty_reasons(report: dict) -> dict[str, int]:
    """정지 판정 — 0 이 아닌 항목. 빈 dict 이면 「비어 있다」.

    ⭑ DB 행 0 · 참조 키 0 이어도 `uploads/` 객체나 진행 중 멀티파트가 남아 있으면 비어 있지 않다.
      DB 는 `_ops/backups` 의 pg_dump 로 되살릴 수 있지만 업로드 원본은 백업 경로가 없다 — 그 객체가
      복원을 쓸모 있게 하는 마지막 사본이다(2026-09-25 검토 지적). `previews/` 는 파일 id 에서 다시
      만드는 생성물이라 보지 않는다.
    """
    rows = report["db"]["platform"]["rows"]
    out = {table: int(rows[table]) for table in COUNT_TABLES if rows.get(table)}
    refs = int(report["referencedKeys"]["count"])
    if refs:
        out["referencedKeys"] = refs
    uploads = int(report["s3"]["objects"].get(ALLOWED_PREFIXES[0], 0))
    if uploads:
        out["s3:uploads/"] = uploads
    multipart = int(report["s3"]["multipartUploads"])
    if multipart:
        out["s3:multipartUploads"] = multipart
    return out


def referenced_refusal(raw: bytes, bucket: str, planned: set[str],
                       ack: str | None) -> tuple[dict | None, str | None]:
    """계획 키 ∩ DB 가 가리키던 키. 겹치면 **그 계수 파일의 sha256** 을 ack 로 받아야 진행한다.

    겹침을 빼고 진행하지 않는다 — 겹친다는 것은 사람이 만든 자료를 지운다는 뜻이고,
    그 판단은 계수를 본 운영자의 토큰으로만 넘어간다(재시드 reset 정지 게이트와 같은 토큰).
    """
    refusal = ack_token_refusal(ack)
    if refusal:
        return None, refusal
    try:
        body = json.loads(raw)
    except ValueError as exc:
        return None, f"DB 참조 키를 읽지 못했다 ({type(exc).__name__}: {exc})."
    ref = body.get("referencedKeys") if isinstance(body, dict) else None
    if (not isinstance(body, dict) or body.get("schema") != REPORT_SCHEMA
            or body.get("phase") != "count" or not isinstance(ref, dict)
            or not isinstance(ref.get("keys"), list)
            or any(not isinstance(k, str) for k in ref["keys"])):
        return None, "DB 참조 키 파일이 초기화 도구의 계수 보고서(phase count · referencedKeys)가 아니다."
    if body.get("bucket") != bucket:
        return None, f"계수 보고서의 버킷이 실행 대상과 다르다 (계수 {body.get('bucket')} · 실행 {bucket})."
    token = hashlib.sha256(raw).hexdigest()
    hit = len(planned & set(ref["keys"]))
    if hit and ack != token:
        why = "ack 토큰이 없다" if ack is None else "ack 토큰이 이 계수 파일과 다르다(지난 회차 값)"
        return None, (f"계획 키 {len(planned)} 건 중 {hit} 건이 스키마 삭제 전 DB 행이 가리키던 키다 — "
                      f"{why}. 지우려면 이 계수 파일의 sha256 {token} 을 ack 로 준다.")
    return {"intersection": hit, "countReportSha256": token, "ackSha256": ack if hit else None}, None


def plan_digest(payload: dict) -> str:
    """계획의 정규 직렬화 sha256. 키 순서가 달라도 같은 계획은 같은 값이다."""
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


# ── 파일 다루기 ────────────────────────────────────────────────────────────

def _private_bytes(path: str, what: str) -> bytes:
    """실행자 소유 mode 0600 일반 파일만 읽는다 (`app/storage_maintenance_cli._private_plan`)."""
    p = pathlib.Path(path)
    info = p.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"{what} 은 일반 파일이어야 한다")
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
        raise RuntimeError(f"{what} 은 실행자 소유 mode 0600 이어야 한다")
    return p.read_bytes()


def _private_file(path: str, what: str) -> str:
    return _private_bytes(path, what).decode("utf-8")


def _json_bytes(body: dict) -> bytes:
    """보고서 직렬화 한 벌 — 계수 파일의 sha256(ack 토큰)은 이 바이트에서 나온다."""
    return (json.dumps(body, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _write_private_bytes(path: str, raw: bytes) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(raw)
    p.chmod(0o600)


def _write_private_json(path: str, body: dict) -> None:
    _write_private_bytes(path, _json_bytes(body))


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


class CountRefusal(RuntimeError):
    """전수를 못 센다 — 센 값이 0 이어도 「비어 있다」로 읽을 수 없다."""


def _count_one(cur, sql: str) -> int:                         # noqa: ANN001
    cur.execute(sql)
    row = cur.fetchone()
    if not row or row[0] is None:
        raise CountRefusal(f"계수 응답이 없다 — {sql}")
    return int(row[0])


def _bypass_on(cur, chain: str) -> None:                    # noqa: ANN001
    """⑴ 접속 롤이 BYPASSRLS 인지 먼저 본다. 아니면 거부한다(FORCE RLS 가 소유자에게도 걸린다).
    ⑵ `row_security = off` 를 건다. 우회 못 하는 롤이면 PostgreSQL 이 정책에 걸리는 질의를
       **걸러 내지 않고 오류로 끝낸다** — 거짓 0 이 나올 자리가 없다(`pg_dump` 가 쓰는 같은 장치).
    """
    cur.execute("select rolbypassrls from pg_roles where rolname = current_user")
    row = cur.fetchone()
    if not row or row[0] is not True:
        raise CountRefusal(f"{chain} 계수 접속 롤이 BYPASSRLS 가 아니다 — FORCE RLS 아래에서 센 0 은 "
                           "「비어 있다」가 아니다(deploy.md 10번). BYPASSRLS 읽기 롤 URL 을 준다.")
    cur.execute("set local row_security = off")


def _require_tables(cur, wanted) -> None:                     # noqa: ANN001
    """표가 없으면 0 으로 읽지 않고 거부한다."""
    cur.execute("select t from unnest(%s::text[]) as t where to_regclass(t) is null", (sorted(wanted),))
    missing = sorted(r[0] for r in cur.fetchall())
    if missing:
        raise CountRefusal(f"계수 대상 표가 없다 {missing} — 0 으로 읽지 않는다.")


def _referenced_keys(cur) -> list[str]:                       # noqa: ANN001
    cur.execute(" union ".join(f"select storage_key from {t}" for t in REFERENCED_KEY_SOURCES))
    return sorted({r[0] for r in cur.fetchall() if r and r[0]})


def _full_counts(cur) -> tuple[int, dict[str, int], list[str]]:  # noqa: ANN001
    """⭑ **전수**를 센다 — 연구실 경계를 걸지 않는다(`_bypass_on` 을 먼저 부른다)."""
    _require_tables(cur, set(COUNT_TABLES) | set(REFERENCED_KEY_SOURCES) | {"d1_lab"})
    labs = _count_one(cur, "select count(*) from d1_lab")
    totals = {table: _count_one(cur, f"select count(*) from {table}") for table in COUNT_TABLES}
    return labs, totals, _referenced_keys(cur)


def _ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _fingerprints(cur, schemas: tuple[str, ...]) -> dict[str, dict]:  # noqa: ANN001
    """스키마의 **모든** 기본 표 — 표마다 행수와 행 내용 지문(행 md5 의 정렬 결합의 md5).

    표 목록은 pg_catalog 에서 읽는다. 새 표가 생겨도 여기를 고치지 않고 토큰 안으로 들어온다.
    """
    cur.execute(_TABLES_SQL, (list(schemas),))
    found = [(r[0], r[1]) for r in cur.fetchall()]
    out: dict[str, dict] = {}
    for nsp, rel in found:
        qualified = f"{_ident(nsp)}.{_ident(rel)}"
        cur.execute(f"select count(*), md5(coalesce(string_agg(md5(t::text), '' "
                    f"order by md5(t::text)), '')) from {qualified} as t")
        row = cur.fetchone()
        if not row or row[0] is None or row[1] is None:
            raise CountRefusal(f"내용 지문 응답이 없다 — {nsp}.{rel}")
        out[f"{nsp}.{rel}"] = {"rows": int(row[0]), "md5": str(row[1])}
    return out


# ── S3 조회 ────────────────────────────────────────────────────────────────

def _s3_listing(s3) -> tuple[dict[str, list[tuple[str, int]]], list[list[str]]]:  # noqa: ANN001
    objects = {prefix: sorted((key, int(size)) for key, size in s3.list_objects(prefix))
               for prefix in ALLOWED_PREFIXES}
    uploads = sorted([key, upload_id]
                     for key, upload_id in s3.list_multipart_uploads(ALLOWED_PREFIXES[0]))
    return objects, uploads


def _s3_snapshot(s3) -> tuple[dict[str, list[str]], list[list[str]]]:   # noqa: ANN001
    listing, uploads = _s3_listing(s3)
    return {p: [k for k, _s in listing[p]] for p in ALLOWED_PREFIXES}, uploads


def _lines_sha256(lines) -> str:                              # noqa: ANN001
    return hashlib.sha256("".join(f"{line}\n" for line in lines).encode("utf-8")).hexdigest()


# ── 단계 ───────────────────────────────────────────────────────────────────

def _count_report(urls, bucket, region, connect, s3_factory) -> dict:  # noqa: ANN001
    """계수 보고서 본문 — `--phase count` 와 `--phase schema` 의 DROP 직전 재계수가 **같은 한 벌**을 쓴다.

    두 체인 모두 BYPASSRLS 계수 URL 로 센다. 실패는 `CountRefusal` 로 올라온다(보고서를 쓰지 않는다).
    ⚠ 시각을 싣지 않는다 — 이 바이트의 sha256 이 ack 토큰이다. 같은 상태를 다시 세면 같은 바이트다.
    """
    db: dict[str, dict] = {}
    referenced: list[str] = []
    for chain in ("platform", "ai"):
        with connect(urls["count-" + chain]) as conn:
            try:
                with conn.cursor() as cur:
                    entry: dict = {"schemas": sorted(_namespaces(cur))}
                    _bypass_on(cur, chain)
                    if chain == "platform":
                        labs, totals, referenced = _full_counts(cur)
                        entry.update(labs=labs, rows=totals)
                    entry.update(countPath=COUNT_PATH,
                                 tables=_fingerprints(cur, FINGERPRINT_SCHEMAS[chain]))
                    db[chain] = entry
            finally:
                conn.rollback()
    listing, uploads = _s3_listing(s3_factory(bucket=bucket, region=region))
    return {
        "schema": REPORT_SCHEMA, "phase": "count", "bucket": bucket, "db": db,
        "referencedKeys": {"count": len(referenced), "keys": referenced},
        "s3": {"objects": {p: len(listing[p]) for p in ALLOWED_PREFIXES},
               "objectsSha256": {p: _lines_sha256(f"{k}\t{n}" for k, n in listing[p])
                                 for p in ALLOWED_PREFIXES},
               "multipartUploads": len(uploads),
               "multipartSha256": _lines_sha256(f"{k}\t{u}" for k, u in uploads)},
    }


def _print_counts(report: dict) -> None:
    for chain, entry in report["db"].items():
        print(f"   {chain:<9} 스키마 {entry['schemas']} · 표 {len(entry['tables'])}"
              + (f" · 연구실 {entry['labs']} · {entry['rows']}" if "rows" in entry else ""))
    print(f"   DB 가 가리키는 저장 키 {report['referencedKeys']['count']}")
    for prefix in ALLOWED_PREFIXES:
        print(f"   S3 {prefix:<10} 객체 {report['s3']['objects'][prefix]}")
    print(f"   S3 진행 중 멀티파트 {report['s3']['multipartUploads']}")


def _phase_count(a, urls, bucket, region, connect, s3_factory) -> int:   # noqa: ANN001
    try:
        report = _count_report(urls, bucket, region, connect, s3_factory)
    except CountRefusal as exc:
        print(f"⛔ {exc} 보고서를 쓰지 않았다.", file=sys.stderr)
        return _PRECONDITION
    _write_private_json(a.report, report)
    print("── 계수 (BYPASSRLS 롤 · row_security=off · 두 체인 모든 기본 표의 행수·내용 지문)")
    _print_counts(report)
    print(f"── 보고서: {a.report}")
    return 0


def _phase_schema(a, urls, bucket, region, connect, s3_factory) -> int:  # noqa: ANN001
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

    # ⭑ DROP 직전 같은 프로세스에서 **다시 센다** — 래퍼의 정지 게이트를 거치지 않은 직접 호출도 여기서 막힌다.
    #   비어 있지 않은데 ack 가 이 재계수 바이트의 sha256 과 다르면 한 건도 지우지 않는다.
    try:
        recount = _count_report(urls, bucket, region, connect, s3_factory)
    except CountRefusal as exc:
        print(f"⛔ DROP 직전 재계수를 못 했다 — {exc} 아무것도 지우지 않았다.", file=sys.stderr)
        return _PRECONDITION
    raw = _json_bytes(recount)
    token = hashlib.sha256(raw).hexdigest()
    _write_private_bytes(a.count_report, raw)
    nonempty = nonempty_reasons(recount)
    if nonempty and a.ack_sha256 != token:
        why = ("ack 가 없다" if a.ack_sha256 is None else
               "ack 가 이 재계수와 다르다(지난 회차 값이거나 그 사이 자료가 바뀌었다)")
        counts = " · ".join(f"{k} {v}" for k, v in nonempty.items())
        print(f"⛔ DROP 직전 재계수가 비어 있지 않다 — {counts}", file=sys.stderr)
        print(f"   {why}. 아무것도 지우지 않았다. 재계수 {a.count_report} · sha256 {token}", file=sys.stderr)
        print("   비어 있지 않은 dev 는 사용자가 이 계수를 보고 준 명시 GO 로만 지운다"
              "(.agents/rules/deploy.md 11번 증보).", file=sys.stderr)
        return _PRECONDITION

    report = {"schema": REPORT_SCHEMA, "phase": "schema", "at": _now(),
              "dryRun": bool(a.dry_run), "bucket": bucket,
              "before": {c: sorted(s) for c, s in observed.items()},
              "countAtDrop": {"file": a.count_report, "sha256": token, "nonEmpty": nonempty,
                              "ackSha256": a.ack_sha256 if nonempty else None},
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
    print(f"── DROP 직전 재계수 {a.count_report} · sha256 {token}"
          + (" · 비어 있음" if not nonempty else " · ack 일치"))
    print("\n── 다음은 이 도구가 하지 않는다. 사람이 이 순서로 낸다"
          " (앱 이미지에 alembic 이 없다).")
    for i, cmd in enumerate(NEXT_COMMANDS, start=1):
        print(f"   {i}. {cmd}")
    print("   ⚠ 각 명령이 비영 종료하면 그 자리에서 멈춘다 — 다음 명령을 내지 않는다.")
    print(f"── 보고서: {a.report}")
    return 0


def _live_referenced(urls, connect) -> list[str]:            # noqa: ANN001
    """**지금** DB 가 가리키는 저장 키 — BYPASSRLS 로 전수. 표가 없으면(마이그레이션 전) 판정 불가다."""
    with connect(urls["count-platform"]) as conn:
        try:
            with conn.cursor() as cur:
                _bypass_on(cur, "platform")
                _require_tables(cur, REFERENCED_KEY_SOURCES)
                return _referenced_keys(cur)
        finally:
            conn.rollback()


def _phase_s3_plan(a, urls, bucket, region, connect, s3_factory) -> int:  # noqa: ANN001
    missing = [flag for flag, value in (("--plan-out", a.plan_out),
                                        ("--referenced-keys", a.referenced_keys),
                                        ("--referenced-sha256", a.referenced_sha256)) if not value]
    if missing:
        print(f"⛔ --phase s3-plan 에는 {' · '.join(missing)} 이 필요하다 — 이번 reset 의 DROP 직전 계수와 "
              "그 sha256 없이 계획을 쓰지 않는다.", file=sys.stderr)
        return _REFUSE
    refusal = ack_token_refusal(a.referenced_sha256)
    if refusal:
        print(f"⛔ --referenced-sha256 — {refusal}", file=sys.stderr)
        return _REFUSE
    try:
        raw = _private_bytes(a.referenced_keys, "참조 키 계수 파일")
    except (OSError, RuntimeError) as exc:
        print(f"⛔ DB 참조 키를 읽지 못했다 ({type(exc).__name__}: {exc}).", file=sys.stderr)
        return _REFUSE
    referenced_sha = hashlib.sha256(raw).hexdigest()

    # ⚠ 아래 셋(묶임 · 지금 DB · 겹침)은 dry-run 이면 사유만 찍고 적용할 수 없는 계획을 쓴다.
    problems: list[tuple[int, str]] = []
    if referenced_sha != a.referenced_sha256:
        problems.append((_REFUSE, f"참조 키 파일 sha256 {referenced_sha} 이 이번 reset 의 값 "
                                  f"{a.referenced_sha256} 과 다르다 — 지난 회차가 남긴 파일이다."))
    try:
        live = _live_referenced(urls, connect)
    except CountRefusal as exc:
        print(f"⛔ 지금 DB 가 가리키는 키를 못 셌다 — {exc} 계획을 쓰지 않았다.", file=sys.stderr)
        return _PRECONDITION
    if live:
        problems.append((_PRECONDITION, f"지금 DB 가 가리키는 저장 키 {len(live)} 건 — 스키마 삭제·재생성 뒤의 "
                                        "DB 가 아니다(그 뒤 올라온 자료다). 그 키를 지우는 계획을 쓰지 않는다."))

    objects, uploads = _s3_snapshot(s3_factory(bucket=bucket, region=region))
    keys = sorted(k for prefix in ALLOWED_PREFIXES for k in objects[prefix])
    # 목록을 만든 쪽도 자기 산출을 검사한다 — 접두사 조회가 무엇을 돌려주든 계획은 좁다.
    refusal = plan_key_refusal(keys) or plan_key_refusal([k for k, _u in uploads])
    if refusal:
        print(f"⛔ {refusal}", file=sys.stderr)
        return _REFUSE
    referenced, refusal = referenced_refusal(
        raw, bucket, set(keys) | {k for k, _u in uploads}, a.ack_sha256)
    if refusal:
        problems.append((_REFUSE, refusal))
    if problems and not a.dry_run:
        for _code, line in problems:
            print(f"⛔ {line} 계획을 쓰지 않았다.", file=sys.stderr)
        return max(code for code, _line in problems)
    for _code, line in problems:
        print(f"⚠ dry-run — 실행이면 거부: {line}", file=sys.stderr)

    payload = {"schema": PLAN_SCHEMA, "bucket": bucket,
               "keys": keys, "multipartUploads": [list(u) for u in uploads]}
    if a.dry_run:
        # s3-apply 는 이 필드가 있는 계획을 받지 않는다(PLAN_FIELDS) — 리허설 계획은 적용될 수 없다.
        payload["dryRun"] = True
    digest = plan_digest(payload)
    _write_private_json(a.plan_out, dict(payload, sha256=digest))
    _write_private_json(a.report, {
        "schema": REPORT_SCHEMA, "phase": "s3-plan", "at": _now(),
        "dryRun": bool(a.dry_run), "bucket": bucket, "plan": a.plan_out, "planSha256": digest,
        "referencedSha256": referenced_sha, "referenced": referenced,
        "live": {"referencedKeys": len(live)},
        "wouldRefuse": [line for _code, line in problems],
        "before": {"objects": {p: len(objects[p]) for p in ALLOWED_PREFIXES},
                   "multipartUploads": len(uploads)}})
    if referenced is not None:
        print(f"   DB 가 가리키던 키와 겹침 {referenced['intersection']} 건"
              + (" · ack 토큰 일치" if referenced["ackSha256"] else ""))
    print(f"   지금 DB 가 가리키는 키 {len(live)} 건")
    print(f"── 계획 {a.plan_out} — 키 {len(keys)} 건 · 진행 중 멀티파트 {len(uploads)} 건")
    print(f"   sha256 {digest}")
    if a.dry_run:
        print("   dry-run 계획이다 — s3-apply 가 받지 않는다.")
    else:
        print("   적용은 `--phase s3-apply --apply-plan <위 파일> --plan-sha256 <위 값>` 이다.")
    return 0


def _parse_plan(raw: str, bucket: str, expected_sha: str) -> tuple[dict, str | None]:
    try:
        plan = json.loads(raw)
    except json.JSONDecodeError:
        return {}, "계획 파일 JSON 이 올바르지 않다."
    if isinstance(plan, dict) and plan.get("dryRun") is not None:
        return {}, "dry-run 계획이다 — 리허설 계획은 적용하지 않는다. 실행 모드로 계획을 다시 세운다."
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
    ap.add_argument("--count-url-file",
                    help="count·schema·s3-plan 필수. platform DB 의 BYPASSRLS 읽기 롤(colab_backup) 접속 URL "
                         "파일. 호스트·DB 가 --platform-url-file 과 같아야 한다.")
    ap.add_argument("--count-ai-url-file",
                    help="count·schema 필수. ai DB 의 BYPASSRLS 읽기 롤 접속 URL 파일. "
                         "호스트·DB 가 --ai-url-file 과 같아야 한다.")
    ap.add_argument("--count-report",
                    help="--phase schema 필수. DROP 직전 재계수를 쓸 자리(0600). 그 sha256 이 ack 대조값이다.")
    ap.add_argument("--referenced-keys",
                    help="--phase s3-plan 필수. 이번 reset 의 DROP 직전 계수 파일(0600 · count-at-drop.json).")
    ap.add_argument("--referenced-sha256",
                    help="--phase s3-plan 필수. --referenced-keys 파일의 기대 sha256 — 이번 reset 에 묶는다.")
    ap.add_argument("--ack-sha256",
                    help="schema: 비어 있지 않은 재계수의 sha256. s3-plan: 계획이 참조 키와 겹칠 때 그 파일의 "
                         "sha256. 사용자가 계수를 보고 준 명시 GO 의 기록이다.")
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

    # ⓓ 계수 URL — 전수를 읽는 롤이어야 하고, 지울 바로 그 DB 여야 한다.
    for chain in COUNT_URL_PHASES.get(a.phase, ()):
        flag = "--count-url-file" if chain == "platform" else "--count-ai-url-file"
        path = a.count_url_file if chain == "platform" else a.count_ai_url_file
        if not path:
            return refuse(f"--phase {a.phase} 에는 {flag}({chain} BYPASSRLS 읽기 롤 URL 파일)이 필요하다 — "
                          "소유자·앱 롤로 센 0 은 FORCE RLS 아래 거짓 0 이다.")
        try:
            url, host = _read_url_file(path, flag[2:-9])
        except (OSError, RuntimeError) as exc:
            return refuse(str(exc) + ".")
        refusal = host_refusal(f"{chain} count", host)
        if refusal:
            return refuse(refusal)
        target = urllib.parse.urlsplit(urls[chain])
        counted = urllib.parse.urlsplit(url)
        if (counted.hostname, counted.port, counted.path) != (target.hostname, target.port, target.path):
            return refuse(f"{chain} 계수 URL 의 호스트·포트·DB 가 {chain} URL 과 다르다 — "
                          "센 DB 와 지울 DB 가 같아야 한다.")
        urls["count-" + chain] = url
    if a.phase == "schema" and not a.count_report:
        return refuse("--phase schema 에는 --count-report(DROP 직전 재계수 자리)가 필요하다.")
    refusal = ack_token_refusal(a.ack_sha256)
    if refusal:
        return refuse(refusal)

    connect = connect or _default_connect
    s3_factory = s3_factory or _default_s3

    if a.phase == "count":
        return _phase_count(a, urls, bucket, region, connect, s3_factory)
    if a.phase == "schema":
        return _phase_schema(a, urls, bucket, region, connect, s3_factory)
    if a.phase == "s3-plan":
        return _phase_s3_plan(a, urls, bucket, region, connect, s3_factory)
    return _phase_s3_apply(a, bucket, region, s3_factory)


if __name__ == "__main__":
    raise SystemExit(main())
