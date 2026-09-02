"""`deploy_doctor` — 배포 상태 검사기 (dev-package/S3.md §2 · PLAN-SoT §9 〈281〉-㉲).

`s3_doctor` 가 「버킷 설정이 맞는가」 하나를 본다면, 이 스크립트는 **배포 한 벌이 서 있는가**를
14 항목으로 본다 — 운영자 자격증명 · 버킷 둘 · DB 둘 · 스키마 head 둘 · RLS 전수 · 앱 롤 ·
5 단위 헬스 · 앱 자격증명 출처 · 환경 짝 · 진입 라우팅 · 백업. 읽기만 한다 — 쓰지도 지우지도 않는다.

    (services/core-api 에서)
    .venv/bin/python ops/deploy_doctor.py --env dev \\
        --endpoint https://<cloudfront> --app-base http://127.0.0.1:18000 \\
        --db-url-file <0600 파일> --ai-db-url-file <0600 파일> \\
        --bucket <데이터 버킷> --web-bucket <웹 버킷> [--worker-base …] [--viz-base …] [--ai-base …]

설계 규칙
- **입력은 파일 경로·URL·이름뿐이다. 비밀 값은 argv 에 싣지 않는다** (`docker inspect`·쉘 이력에 남는다 —
  `〈121〉-㉯` 와 같은 이유). 접속 문자열은 0600 파일로, AWS 자격증명은 표준 사슬(env→ECS→IMDS)로 온다.
- 환경변수를 읽지 않는다 — 무엇을 검사했는지가 명령줄 하나에 다 보여야 한다.
- 각 항목은 ✓ / ✗ / ─. **입력이 없는 항목은 `─ (미지정 — 무엇을 주면 검사한다)`** 로 적고 요약줄에
  ─ 건수를 드러낸다 (`infra/staging/backup/lib.sh` 의 SKIP 규약 — 건너뛴 것을 통과로 세지 않는다).
- 판정: ✗ 가 하나라도 있으면 exit 1 · **검사한 항목이 0 이면 exit 1**(대상 0건은 통과가 아니다) ·
  ─ 가 남으면 **exit 1** — 콘솔 단계 사이의 부분 실행은 `--allow-skip` 으로 면제를 **명시**해야 exit 0 이고
  요약줄이 「부분 통과 · 면제 명시 · ─ n건」이라고 말한다. 「전 항목 통과」는 ─ 0 일 때만.
- 값·키·URL 전체를 출력하지 않는다 — 호스트·버킷 이름·롤 이름 정도만. `Report.line` 이 마지막 방어선으로
  `scheme://user:pw@` 와 `X-Amz-*` 서명 조각을 가린다.
- 앞 항목이 실패하면 그에 기대는 뒤 항목은 ─ 로 건너뛴다 (에러 열 개가 쏟아지면 원인이 묻힌다 — s3_doctor 규칙).

재사용: `s3_doctor`(Report · _s3_call · check_credentials · check_bucket) · `kernel/s3.S3Client` ·
`gates/tools/rls_coverage.py::main`(판정기 — facts 는 여기서 살아 있는 DB 로 만든다) ·
`infra/staging/db-bootstrap.sh verify` 의 롤·소유자 질의 · `migration_single_head.py` 의 head 규칙(파일이 print 형이라
같은 규칙을 최소로 다시 적었다 — `gates/` 는 이 스크립트가 고치지 않는다).
"""
from __future__ import annotations

import argparse
import ast
import configparser
import contextlib
import io
import json
import pathlib
import re
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]          # ops → core-api → services → 레포
if str(HERE) not in sys.path:        # 시험이 파일 경로로 import 할 때도 s3_doctor 를 찾게
    sys.path.insert(0, str(HERE))

import s3_doctor  # noqa: E402
from s3_doctor import BAD, OK, SKIP  # noqa: E402

from colab_core.kernel.s3 import S3Client, S3Error  # noqa: E402
from colab_core.kernel.sigv4 import Credentials  # noqa: E402

MARKS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭"
CHAINS = ("platform", "ai")
#: 앱 롤·소유자 롤 이름 — `infra/staging/db-bootstrap.sh` · `ops/app-role.sql` 이 만드는 이름 그대로.
APP_ROLE, OWNER_ROLE = "colab_app", "colab_owner"
LOCAL_ORIGIN = "http://localhost:5173"
BACKUP_PREFIX = "_ops/backups/{env}/"
BACKUP_MAX_AGE = timedelta(hours=24)
HTTP_TIMEOUT = 10.0

_CRED_IN_URL = re.compile(r"(://)[^/@\s]+@")
_AMZ_SIGNED = re.compile(r"(X-Amz-(?:Signature|Credential|Security-Token)=)[^&\s]+")


def redact(text: str) -> str:
    """마지막 방어선 — 어떤 경로로 들어온 문자열이든 자격 조각을 가린다."""
    return _AMZ_SIGNED.sub(r"\1…", _CRED_IN_URL.sub(r"\1…@", text))


# ── 보고 ────────────────────────────────────────────────────────────────────

class DeployReport(s3_doctor.Report):
    """`s3_doctor.Report` 와 같은 줄 모양 + 항목 단위 상태 + ─ 계수."""

    def __init__(self) -> None:
        super().__init__()
        self.skipped = 0
        self.items: list[tuple[str, str, str]] = []   # (기호, 제목, 상태)
        self._marks: list[str] = []

    def line(self, status: str, label: str, detail: str = "") -> None:
        self._marks.append(status)
        if status == OK:
            self.passed += 1
        elif status == BAD:
            self.failed += 1
        else:
            self.skipped += 1
        # s3_doctor 와 같은 줄 모양 — 라벨 칸만 `pipeline-worker` 가 들어가게 넓혔다.
        print(f"    {status} {label:<16}{redact(detail)}")

    @contextlib.contextmanager
    def item(self, no: int, title: str):
        mark = MARKS[no - 1]
        self.section(f"{mark} {title}")
        self._marks = []
        try:
            yield
        except Exception as e:  # noqa: BLE001 — 항목 하나의 예외가 나머지 13 을 묻지 않는다
            first = redact((str(e).splitlines() or [""])[0])[:160]
            self.line(BAD, "예외", f"{type(e).__name__}: {first}")
        status = BAD if BAD in self._marks else (OK if OK in self._marks else SKIP)
        self.items.append((mark, title, status))


def verdict(statuses: list[str], *, allow_skip: bool = False) -> tuple[int, str]:
    """(exit code, 요약 두 줄). ─ 는 통과가 아니고, 검사 0건도 통과가 아니다.

    세 상태 — 검사했으면 판정한다 · `--allow-skip` 으로 **명시 면제**하면 ─ 건수를 드러낸 채 넘어간다 ·
    아무 말 없이 ─ 가 남으면 **실패**다. 콘솔 단계 사이의 부분 실행은 면제를 적어야 통과다.
    """
    passed = statuses.count(OK)
    failed = statuses.count(BAD)
    skipped = statuses.count(SKIP)
    head = f"항목 {len(statuses)} — ✓ {passed} · ✗ {failed} · ─ {skipped}"
    if failed:
        tail = f" · ─ {skipped}건 미검사" if skipped else ""
        return 1, f"{head}\n  RED (실패 {failed}건{tail}) · 고치는 법: dev-package/S3.md §1 · infra/dev/README.md"
    if passed == 0:
        return 1, (f"{head}\n  RED (검사한 항목 0건 — 대상 0건은 통과가 아니다. 위 ─ 줄이 말하는 인자를 주면 검사한다)")
    if skipped and not allow_skip:
        return 1, (f"{head}\n  RED (미지정 {skipped}건 — 부분 실행은 `--allow-skip` 으로 면제를 적어야 통과다. "
                   "무엇을 안 봤는지는 위 ─ 줄)")
    if skipped:
        return 0, f"{head}\n  부분 통과 · 면제 명시 (✓ {passed} · ─ {skipped}건 — 전 항목 판정이 아니다)"
    return 0, f"{head}\n  전 항목 통과 (─ 0 — {len(statuses)} 항목이 실제로 돌았다)"


# ── 문맥 ────────────────────────────────────────────────────────────────────

@dataclass
class Ctx:
    env: str | None
    endpoint: str | None
    db_url_files: dict[str, str | None]
    app_base: str | None
    worker_base: str | None
    viz_base: str | None
    ai_base: str | None
    bucket: str | None
    web_bucket: str | None
    region: str
    allow_skip: bool = False
    creds: Credentials | None = None
    conns: dict[str, object] = field(default_factory=dict)
    db_hosts: dict[str, str | None] = field(default_factory=dict)
    web_index: str | None = None          # ③ 의 index.html 판정 — ⑩ 의 frontend 줄이 쓴다
    app_bucket: str | None = None         # ⑪ 이 본 앱의 버킷 — ⑫ 가 쓴다


def unspecified(flag: str) -> str:
    return f"(미지정 — {flag} 를 주면 검사한다)"


# ── HTTP ────────────────────────────────────────────────────────────────────

class Unreachable(RuntimeError):
    pass


def http_get(url: str, timeout: float = HTTP_TIMEOUT) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, method="GET",
                                 headers={"User-Agent": "colab-deploy-doctor", "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — 운영자가 준 URL
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read(65536)
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise Unreachable(type(e).__name__) from None


def is_html(headers: dict[str, str], body: bytes) -> bool:
    if headers.get("content-type", "").lower().startswith("text/html"):
        return True
    head = body[:64].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def as_json(headers: dict[str, str], body: bytes):
    """JSON 이면 파싱 결과, 아니면 None."""
    try:
        return json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None


# ── ① 운영자 자격증명 · ② 데이터 버킷 · ③ 웹 버킷 ────────────────────────────

def check_operator_credentials(ctx: Ctx, rep: DeployReport) -> None:
    if not (ctx.bucket or ctx.web_bucket):
        rep.line(SKIP, "(미지정)", unspecified("--bucket 또는 --web-bucket"))
        return
    ctx.creds = s3_doctor.check_credentials(rep, ctx.region)   # STS GetCallerIdentity — ARN·출처·만료


def _origin_of(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def check_data_bucket(ctx: Ctx, rep: DeployReport) -> None:
    if not ctx.bucket:
        rep.line(SKIP, "(미지정)", unspecified("--bucket"))
        return
    if ctx.creds is None:
        rep.line(SKIP, "(건너뜀)", "① 자격증명 실패")
        return
    # 기존 7 항목(존재·리전·버저닝·암호화·CORS(localhost)·정책·라이프사이클) — s3_doctor 그대로.
    if not s3_doctor.check_bucket(rep, ctx.bucket, ctx.region, LOCAL_ORIGIN, ctx.creds):
        rep.line(SKIP, "CORS(endpoint)", "존재 확인 실패로 건너뜀")
        return
    if not ctx.endpoint:
        rep.line(SKIP, "CORS(endpoint)", unspecified("--endpoint"))
        return
    origin = _origin_of(ctx.endpoint)
    status, body = s3_doctor._s3_call(method="GET", bucket=ctx.bucket, region=ctx.region,
                                      creds=ctx.creds, query={"cors": ""})
    if status == 403:
        rep.line(SKIP, "CORS(endpoint)", "권한 없음 (prod 정책은 진단 제외가 정상 — dev-package/S3.md §1)")
    elif status != 200:
        rep.line(BAD, "CORS(endpoint)", f"AllowedOrigins 에 {origin} 없음 — 구성 자체가 없음 ({status})")
    else:
        origins = [n.text for n in ET.fromstring(body).findall(".//{*}AllowedOrigin")]
        rep.line(OK if origin in origins else BAD, "CORS(endpoint)",
                 origin if origin in origins else f"AllowedOrigins 에 {origin} 없음 — 현재: {origins}")


def check_web_bucket(ctx: Ctx, rep: DeployReport) -> None:
    if not ctx.web_bucket:
        rep.line(SKIP, "(미지정)", unspecified("--web-bucket"))
        return
    if ctx.creds is None:
        rep.line(SKIP, "(건너뜀)", "① 자격증명 실패")
        return
    client = S3Client(bucket=ctx.web_bucket, region=ctx.region, creds=ctx.creds, backoff_base=0.2)
    try:
        size, _etag = client.head_object("index.html")
        ctx.web_index = OK if size > 0 else BAD
        rep.line(ctx.web_index, "index.html", f"{size}B" if size > 0 else "0B — 빈 파일")
    except S3Error as e:
        ctx.web_index = BAD
        rep.line(BAD, "index.html", f"HeadObject {e.status} {e.code} — deploy_web 이 돌지 않았다")
    try:
        first = next(iter(client.list_objects("assets/")), None)
        rep.line(OK if first else BAD, "assets/",
                 "객체 ≥1" if first else "객체 0건 — 번들이 올라가지 않았다 (deploy_web)")
    except S3Error as e:
        rep.line(BAD, "assets/", f"ListObjects {e.status} {e.code}")


# ── ④⑤ DB 연결 ──────────────────────────────────────────────────────────────

def open_db(ctx: Ctx, rep: DeployReport, chain: str, flag: str) -> None:
    path = ctx.db_url_files.get(chain)
    if not path:
        rep.line(SKIP, "(미지정)", unspecified(flag))
        return
    p = pathlib.Path(path)
    if not p.is_file():
        rep.line(BAD, "파일", f"{flag} 가 가리키는 파일이 없다")
        return
    mode = stat.S_IMODE(p.stat().st_mode)
    if mode & 0o077:
        rep.line(BAD, "권한", f"{oct(mode)} — 0600 이어야 한다 (chmod 600). 접속 문자열이 남에게 읽힌다")
    url = p.read_text(encoding="utf-8").rstrip()
    if not url:
        rep.line(BAD, "파일", "비었다")
        return
    host = urllib.parse.urlsplit(url).hostname
    ctx.db_hosts[chain] = host
    # SQLAlchemy 표기(`postgresql+psycopg://`)도 받는다 — core 의 `*_DATABASE_URL_FILE` 을 그대로 줄 수 있게.
    dsn = re.sub(r"^postgresql\+psycopg://", "postgresql://", url)
    import psycopg
    try:
        conn = psycopg.connect(dsn, connect_timeout=5, autocommit=True,
                               options="-c default_transaction_read_only=on")
    except psycopg.OperationalError as e:
        rep.line(BAD, "연결", f"{host} — {redact((str(e).splitlines() or [''])[0])[:160]}")
        return
    except Exception as e:  # noqa: BLE001 — ProgrammingError 는 접속 문자열을 통째로 되비친다
        rep.line(BAD, "연결", f"{type(e).__name__} — 메시지는 접속 문자열을 담을 수 있어 출력하지 않는다")
        return
    ctx.conns[chain] = conn
    role = conn.execute("SELECT current_user").fetchone()[0]
    rep.line(OK, "연결", f"{host} ({role}, read-only 세션)")
    version = conn.execute("SELECT version()").fetchone()[0]
    short = version.split(" on ")[0]
    rep.line(OK if short.startswith("PostgreSQL 16") else BAD, "버전",
             short if short.startswith("PostgreSQL 16") else f"기대 PostgreSQL 16, 실제 {short}")


# ── ⑥⑦ 스키마 head ─────────────────────────────────────────────────────────

def _literal(node: ast.AST):
    try:
        return ast.literal_eval(node)
    except Exception:  # noqa: BLE001
        return None


def repo_head(chain: str) -> tuple[str | None, str]:
    """`db/<chain>/versions/*.py` 의 revision/down_revision 그래프에서 head 하나.
    규칙은 `gates/tools/migration_single_head.py` 와 같다 — 파일을 실행하지 않고 ast 로 읽는다."""
    versions = REPO_ROOT / "db" / chain / "versions"
    files = [f for f in sorted(versions.glob("*.py")) if f.name != "__init__.py"] if versions.is_dir() else []
    if not files:
        return None, f"db/{chain}/versions/*.py 가 0건이다"
    revs: set[str] = set()
    referenced: set[str] = set()
    for f in files:
        tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"), filename=str(f))
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                value = _literal(node.value)
                if target.id == "revision" and isinstance(value, str):
                    revs.add(value)
                elif target.id == "down_revision":
                    for d in ([value] if isinstance(value, str) else list(value or [])):
                        if isinstance(d, str):
                            referenced.add(d)
    heads = sorted(revs - referenced)
    if len(heads) != 1:
        return None, f"레포 head 가 {len(heads)}개 — migration-single-head 게이트를 먼저 green 으로"
    return heads[0], ""


def version_table(chain: str) -> str:
    ini = configparser.ConfigParser(interpolation=None)
    ini.read(REPO_ROOT / "db" / chain / "alembic.ini", encoding="utf-8")
    return ini.get("alembic", "version_table")


def judge_head(chain: str, db_values: list[str]) -> tuple[str, str]:
    """(상태, 한 줄). DB 의 version_num 행들 vs 레포 head."""
    head, why = repo_head(chain)
    if head is None:
        return BAD, why
    if len(db_values) != 1:
        return BAD, (f"{version_table(chain)} 행 {len(db_values)}건 — 마이그레이션이 적용되지 않았거나 "
                     f"둘 이상 적용됐다 (레포 head {head})")
    actual = db_values[0]
    if actual != head:
        return BAD, f"DB {actual} ≠ 레포 head {head} — migrate-{chain} 을 돌린다"
    return OK, f"{head} (DB = 레포)"


def check_head(ctx: Ctx, rep: DeployReport, chain: str, dep: str) -> None:
    conn = ctx.conns.get(chain)
    if conn is None:
        rep.line(SKIP, "(건너뜀)", f"{dep} DB 연결이 없다")
        return
    table = version_table(chain)
    try:
        rows = [r[0] for r in conn.execute(f'SELECT version_num FROM "{table}"').fetchall()]
    except Exception as e:  # noqa: BLE001
        rep.line(BAD, "head", f"{table} 조회 실패 — {type(e).__name__}")
        return
    status, detail = judge_head(chain, rows)
    rep.line(status, "head", detail)


# ── ⑧ RLS 전수 ──────────────────────────────────────────────────────────────

#: `gates/tools/rls-coverage.sh` 의 facts SQL 그대로 — 체인 이름만 파라미터다.
FACTS_SQL = """
    SELECT %s, c.relname,
           CASE WHEN c.relrowsecurity THEN 't' ELSE 'f' END,
           CASE WHEN c.relforcerowsecurity THEN 't' ELSE 'f' END,
           COALESCE((SELECT string_agg(p.polname, ',' ORDER BY p.polname)
                     FROM pg_policy p WHERE p.polrelid = c.oid), '')
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'r' AND n.nspname NOT IN ('pg_catalog','information_schema')
    ORDER BY c.relname"""


def judge_rls_facts(rows: list[tuple[str, str, str, str, str]]) -> tuple[bool, str]:
    """`gates/tools/rls_coverage.py::main` 판정기 재사용 — allow-list 정본을 다시 적지 않는다."""
    tools = REPO_ROOT / "gates" / "tools"
    if not (tools / "rls_coverage.py").is_file():
        raise RuntimeError("gates/tools/rls_coverage.py 가 없다 — 판정기 없이 RLS 를 판정하지 않는다")
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    import rls_coverage
    with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8") as tmp:
        tmp.write("".join("\t".join(r) + "\n" for r in rows))
        facts = tmp.name
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = rls_coverage.main(["rls_coverage.py", facts])
    finally:
        pathlib.Path(facts).unlink(missing_ok=True)
    return rc == 0, buf.getvalue()


def check_rls(ctx: Ctx, rep: DeployReport) -> None:
    missing = [c for c in CHAINS if not ctx.db_url_files.get(c)]
    if missing:
        rep.line(SKIP, "(미지정)", unspecified("--db-url-file 와 --ai-db-url-file 둘 다"))
        return
    if any(ctx.conns.get(c) is None for c in CHAINS):
        rep.line(SKIP, "(건너뜀)", "④/⑤ DB 연결 실패")
        return
    rows: list[tuple[str, str, str, str, str]] = []
    for chain in CHAINS:
        rows.extend(tuple(r) for r in ctx.conns[chain].execute(FACTS_SQL, (chain,)).fetchall())
    ok, out = judge_rls_facts(rows)
    if ok:
        rep.line(OK, "판정", f"테이블 {len(rows)}건 — allow-list 밖 전부 FORCE RLS + 경계 정책 (본체는 본체 정책까지)")
        return
    errors = [ln.strip()[2:] for ln in out.splitlines() if ln.strip().startswith("- ")]
    for e in errors[:8]:
        rep.line(BAD, "결손", e)
    if len(errors) > 8:
        rep.line(BAD, "결손", f"… 외 {len(errors) - 8}건")
    if not errors:
        rep.line(BAD, "판정", (out.strip().splitlines() or ["판정기 red"])[-1])


# ── ⑨ 앱 롤 속성 ────────────────────────────────────────────────────────────

def check_app_role(ctx: Ctx, rep: DeployReport) -> None:
    conn = ctx.conns.get("platform")
    if conn is None:
        rep.line(SKIP, "(건너뜀)", "④ platform DB 연결이 없다")
        return
    # `infra/staging/db-bootstrap.sh verify` 의 두 질의 그대로.
    roles = {r[0]: r[1:] for r in conn.execute(
        "SELECT rolname, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole FROM pg_roles "
        "WHERE rolname IN (%s, %s) ORDER BY 1", (APP_ROLE, OWNER_ROLE)).fetchall()}
    for name in (APP_ROLE, OWNER_ROLE):
        if name not in roles:
            rep.line(BAD, name, "롤이 없다 — db-bootstrap roles/app-grants 가 돌지 않았다")
            continue
        rolsuper, bypass, _cdb, _crole = roles[name]
        bad = [f for f, v in (("SUPERUSER", rolsuper), ("BYPASSRLS", bypass)) if v]
        rep.line(BAD if bad else OK, name,
                 f"{' · '.join(bad)} — 경계 증명이 거짓 green 이 된다" if bad else "NOSUPERUSER · NOBYPASSRLS")
    owners = dict(conn.execute(
        "SELECT tableowner, count(*) FROM pg_tables WHERE schemaname='public' GROUP BY 1 ORDER BY 1").fetchall())
    total = sum(owners.values())
    if total == 0:
        rep.line(BAD, "소유", "public 테이블 0건 — 대상 0건은 통과가 아니다 (마이그레이션 전인가)")
        return
    app_owned = owners.get(APP_ROLE, 0)
    spread = " · ".join(f"{k} {v}" for k, v in sorted(owners.items()))
    rep.line(OK if app_owned == 0 else BAD, "소유",
             f"{APP_ROLE} 소유 {app_owned} (전체 {total}: {spread})")


# ── ⑩ 5 단위 헬스 ───────────────────────────────────────────────────────────

MODE_KEYS = ("storageMode", "sourceMode")


def check_units_health(ctx: Ctx, rep: DeployReport) -> None:
    units = (("core-api", ctx.app_base, "--app-base"), ("pipeline-worker", ctx.worker_base, "--worker-base"),
             ("viz-render", ctx.viz_base, "--viz-base"), ("ai-service", ctx.ai_base, "--ai-base"))
    for unit, base, flag in units:
        if not base:
            rep.line(SKIP, unit, unspecified(flag))
            continue
        try:
            status, headers, body = http_get(base.rstrip("/") + "/healthz")
        except Unreachable as e:
            rep.line(BAD, unit, f"/healthz 연결 실패 ({e})")
            continue
        data = as_json(headers, body)
        if status != 200 or not isinstance(data, dict):
            rep.line(BAD, unit, f"/healthz {status}" + ("" if isinstance(data, dict) else " (JSON 아님)"))
            continue
        rep.line(OK, unit, f"/healthz 200 · {data.get('status', 'alive')}")
        if unit == "core-api":
            continue                                   # core 의 모드·자격증명 출처는 ⑪ 이 본다
        if unit == "ai-service":
            continue                                   # 저장 모드가 없는 단위
        key = next((k for k in MODE_KEYS if k in data), None)
        if key is None:
            # [미확인] worker·viz 가 healthz 에 싣는 키 이름은 V-3(D·E) 가 정한다 — 없으면 정직하게 ─.
            rep.line(SKIP, f"{unit} 모드", "(키 없음 — healthz 에 storageMode/sourceMode 가 없다)")
        else:
            rep.line(OK if data[key] == "s3" else BAD, f"{unit} 모드",
                     f"{key}={data[key]}" + ("" if data[key] == "s3" else " — s3 여야 한다"))
    if not ctx.web_bucket:
        rep.line(SKIP, "frontend", unspecified("--web-bucket"))
    elif ctx.web_index is None:
        rep.line(SKIP, "frontend", "③ 을 못 봤다 (자격증명 실패)")
    else:
        rep.line(ctx.web_index, "frontend", "index.html (③)")


# ── ⑪ 앱 자격증명 출처 ───────────────────────────────────────────────────────

def check_app_credentials(ctx: Ctx, rep: DeployReport) -> None:
    if not ctx.app_base:
        rep.line(SKIP, "(미지정)", unspecified("--app-base"))
        return
    try:
        status, headers, body = http_get(ctx.app_base.rstrip("/") + "/healthz/storage")
    except Unreachable as e:
        rep.line(BAD, "/healthz/storage", f"연결 실패 ({e})")
        return
    data = as_json(headers, body)
    if status != 200 or not isinstance(data, dict):
        rep.line(BAD, "/healthz/storage", f"{status} — core 가 이 경로를 모른다면 이미지가 낡았다")
        return
    mode = data.get("storageMode")
    rep.line(OK if mode == "s3" else BAD, "storageMode", str(mode) + ("" if mode == "s3" else " — s3 여야 한다"))
    if mode != "s3":
        return
    bucket, region = data.get("bucket"), data.get("region")
    ctx.app_bucket = bucket if isinstance(bucket, str) else None
    rep.line(OK if bucket and region else BAD, "버킷·리전", f"{bucket} · {region}")
    source = data.get("credentialSource")
    if source == "imds":
        rep.line(OK, "출처", "imds (EC2 인스턴스 역할)")
    elif source is None:
        rep.line(BAD, "출처", f"없음 — {data.get('error') or '사유 없음'}")
    else:
        rep.line(BAD, "출처", f"{source} — EC2 인스턴스 역할(imds)이어야 한다. env 키는 두지 않는다 (S3.md §1)")
    expires = data.get("expiresAt")
    if isinstance(expires, str):
        try:
            when = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            left = when - datetime.now(timezone.utc)
            rep.line(OK if left > timedelta(0) else BAD, "만료",
                     f"{int(left.total_seconds() // 60)}분 남음" if left > timedelta(0) else "이미 지났다")
        except ValueError:
            rep.line(BAD, "만료", "expiresAt 을 읽을 수 없다")


# ── ⑫ 환경 짝 ───────────────────────────────────────────────────────────────

def env_pair_findings(env: str, *, app_bucket: str | None, bucket_arg: str | None,
                      web_bucket: str | None, hosts: dict[str, str | None]) -> list[tuple[str, str, str]]:
    """(상태, 라벨, 한 줄) 목록 — 버킷 접미사 `-<env>` · DB 호스트에 `-<env>` · 앱 버킷 = --bucket."""
    suffix = f"-{env}"
    out: list[tuple[str, str, str]] = []

    def suffix_line(label: str, name: str | None, flag: str) -> None:
        if name is None:
            out.append((SKIP, label, unspecified(flag)))
        elif name.endswith(suffix):
            out.append((OK, label, name))
        else:
            out.append((BAD, label, f"{name} 가 {suffix} 로 끝나지 않는다 — 다른 환경의 벌이다"))

    suffix_line("앱 버킷", app_bucket, "--app-base (⑪)")
    suffix_line("--bucket", bucket_arg, "--bucket")
    if app_bucket and bucket_arg and app_bucket != bucket_arg:
        out.append((BAD, "버킷 일치", f"앱이 보는 {app_bucket} ≠ --bucket {bucket_arg}"))
    suffix_line("--web-bucket", web_bucket, "--web-bucket")
    for chain, flag in (("platform", "--db-url-file"), ("ai", "--ai-db-url-file")):
        host = hosts.get(chain)
        label = f"DB 호스트({chain})"
        if host is None:
            out.append((SKIP, label, unspecified(flag)))
        elif suffix in host:
            out.append((OK, label, host))
        else:
            out.append((BAD, label, f"{host} 에 {suffix} 가 없다 — 다른 환경의 DB 다"))
    return out


def check_env_pair(ctx: Ctx, rep: DeployReport) -> None:
    if not ctx.env:
        rep.line(SKIP, "(미지정)", unspecified("--env dev|prod"))
        return
    for status, label, detail in env_pair_findings(
            ctx.env, app_bucket=ctx.app_bucket, bucket_arg=ctx.bucket,
            web_bucket=ctx.web_bucket, hosts=ctx.db_hosts):
        rep.line(status, label, detail)


# ── ⑬ 진입·라우팅 ───────────────────────────────────────────────────────────

def check_routing(ctx: Ctx, rep: DeployReport) -> None:
    if not ctx.endpoint:
        rep.line(SKIP, "(미지정)", unspecified("--endpoint https://<cloudfront>"))
        return
    base = ctx.endpoint.rstrip("/")
    probes = (("/", "진입 /"), ("/api/v1/me", "/api/v1/me"), ("/previews/__probe", "/previews/*"))
    for path, label in probes:
        try:
            status, headers, body = http_get(base + path)
        except Unreachable as e:
            rep.line(BAD, label, f"연결 실패 ({e})")
            continue
        html = is_html(headers, body)
        if path == "/":
            rep.line(OK if status == 200 and html else BAD, label,
                     "200 html" if status == 200 and html else f"{status} {'html' if html else '비-HTML'} (기대 200 html)")
        elif path == "/api/v1/me":
            if status == 401 and as_json(headers, body) is not None:
                rep.line(OK, label, "401 JSON — /api/* 가 core 오리진으로 간다")
            elif html:
                rep.line(BAD, label, f"{status} HTML — SPA 로 샜다 (CloudFront 의 /api/* 동작이 core 를 가리키지 않는다)")
            else:
                rep.line(BAD, label, f"{status} (기대 401 JSON)")
        else:
            if html:
                rep.line(BAD, label, f"{status} HTML — SPA 로 샜다 (previews 오리진 동작이 없다)")
            else:
                rep.line(OK if status in (403, 404) else BAD, label,
                         f"{status} 비-HTML" + ("" if status in (403, 404) else " (기대 403/404)"))


# ── ⑭ 백업 24h ──────────────────────────────────────────────────────────────

def newest_object(client: S3Client, prefix: str) -> tuple[int, datetime | None]:
    """ListObjectsV2 로 (객체 수, 최신 LastModified). `list_objects` 는 날짜를 안 주므로 같은 호출을 직접 판다."""
    count, newest, token = 0, None, ""
    while True:
        query = {"list-type": "2", "prefix": prefix}
        if token:
            query["continuation-token"] = token
        _headers, body = client._call(method="GET", query=query)  # noqa: SLF001 — 서명·인코딩을 공유한다
        root = ET.fromstring(body.decode("utf-8", "replace"))
        for node in root.findall("{*}Contents"):
            count += 1
            raw = (node.findtext("{*}LastModified") or "").strip()
            when = datetime.fromisoformat(raw.replace("Z", "+00:00")) if raw else None
            if when and (newest is None or when > newest):
                newest = when
        if (root.findtext("{*}IsTruncated") or "").lower() != "true":
            return count, newest
        token = (root.findtext("{*}NextContinuationToken") or "").strip()


def check_backups(ctx: Ctx, rep: DeployReport) -> None:
    if not (ctx.bucket and ctx.env):
        rep.line(SKIP, "(미지정)", unspecified("--bucket 과 --env 둘 다"))
        return
    if ctx.creds is None:
        rep.line(SKIP, "(건너뜀)", "① 자격증명 실패")
        return
    prefix = BACKUP_PREFIX.format(env=ctx.env)
    client = S3Client(bucket=ctx.bucket, region=ctx.region, creds=ctx.creds, backoff_base=0.2)
    try:
        count, newest = newest_object(client, prefix)
    except S3Error as e:
        rep.line(BAD, "목록", f"ListObjectsV2 {e.status} {e.code} ({prefix})")
        return
    if count == 0 or newest is None:
        rep.line(BAD, "최신", f"{prefix} 객체 0건 — 대상 0건은 통과가 아니다 (백업이 아직 돌지 않았거나 접두사가 다르다)")
        return
    age = datetime.now(timezone.utc) - newest
    hours = age.total_seconds() / 3600
    rep.line(OK if age <= BACKUP_MAX_AGE else BAD, "최신",
             f"{hours:.1f}시간 전 · 객체 {count}건" + ("" if age <= BACKUP_MAX_AGE else " — 24h 를 넘겼다"))


# ── 진행 ────────────────────────────────────────────────────────────────────

def run(ctx: Ctx) -> int:
    rep = DeployReport()
    print()
    with rep.item(1, "운영자 자격증명"):
        check_operator_credentials(ctx, rep)
    with rep.item(2, f"데이터 버킷 설정{'  ' + ctx.bucket if ctx.bucket else ''}"):
        check_data_bucket(ctx, rep)
    with rep.item(3, f"웹 버킷{'  ' + ctx.web_bucket if ctx.web_bucket else ''}"):
        check_web_bucket(ctx, rep)
    with rep.item(4, "DB 연결 (platform)"):
        open_db(ctx, rep, "platform", "--db-url-file")
    with rep.item(5, "DB 연결 (ai)"):
        open_db(ctx, rep, "ai", "--ai-db-url-file")
    with rep.item(6, "스키마 head (platform)"):
        check_head(ctx, rep, "platform", "④")
    with rep.item(7, "스키마 head (ai)"):
        check_head(ctx, rep, "ai", "⑤")
    with rep.item(8, "RLS 전수 (살아 있는 DB)"):
        check_rls(ctx, rep)
    with rep.item(9, "앱 롤 속성"):
        check_app_role(ctx, rep)
    with rep.item(10, "5 단위 헬스"):
        check_units_health(ctx, rep)
    with rep.item(11, "앱 자격증명 출처 (core /healthz/storage)"):
        check_app_credentials(ctx, rep)
    with rep.item(12, f"환경 짝{'  ' + ctx.env if ctx.env else ''}"):
        check_env_pair(ctx, rep)
    with rep.item(13, "진입·라우팅 (endpoint)"):
        check_routing(ctx, rep)
    with rep.item(14, "백업 24h"):
        check_backups(ctx, rep)
    for conn in ctx.conns.values():
        with contextlib.suppress(Exception):
            conn.close()

    print("\n  ── 요약 ──")
    for mark, title, status in rep.items:
        print(f"  {mark} {title:<40} {status}")
    code, text = verdict([s for _m, _t, s in rep.items], allow_skip=ctx.allow_skip)
    print(f"\n  {text}")
    return code


def parse_args(argv: list[str] | None) -> Ctx:
    parser = argparse.ArgumentParser(
        description="배포 상태 검사기 — 14 항목, 읽기 전용 (dev-package/S3.md §2). 값은 파일·URL·이름으로만 받는다.")
    parser.add_argument("--env", choices=("dev", "prod"), help="벌 이름 — 버킷 접미사·DB 호스트·백업 접두사의 짝")
    parser.add_argument("--endpoint", help="CloudFront 진입 URL (https://…)")
    parser.add_argument("--db-url-file", help="platform 접속 문자열이 든 0600 파일")
    parser.add_argument("--ai-db-url-file", help="ai 접속 문자열이 든 0600 파일")
    parser.add_argument("--app-base", help="core-api 베이스 (SSH 터널 뒤, 예: http://127.0.0.1:18000)")
    parser.add_argument("--worker-base", help="pipeline-worker 베이스")
    parser.add_argument("--viz-base", help="viz-render 베이스")
    parser.add_argument("--ai-base", help="ai-service 베이스")
    parser.add_argument("--bucket", help="데이터 버킷 이름")
    parser.add_argument("--web-bucket", help="웹(정적 번들) 버킷 이름")
    parser.add_argument("--region", default="ap-northeast-2")
    parser.add_argument("--allow-skip", action="store_true",
                        help="미지정 항목(─)이 남아도 통과로 친다 — 콘솔 단계 사이의 부분 실행에만. 요약줄에 면제가 적힌다")
    a = parser.parse_args(argv)
    return Ctx(env=a.env, endpoint=a.endpoint,
               db_url_files={"platform": a.db_url_file, "ai": a.ai_db_url_file},
               app_base=a.app_base, worker_base=a.worker_base, viz_base=a.viz_base, ai_base=a.ai_base,
               bucket=a.bucket, web_bucket=a.web_bucket, region=a.region, allow_skip=a.allow_skip)


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
