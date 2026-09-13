"""`ops/reset_dev_environment.py` 의 **가드**를 잰다 — DB·AWS 없이 돌아간다.

⚠ 이 시험이 재는 것은 **지우는 일**이 아니라 **안 지우게 막는 장치**다.
실집행은 dev EC2 위 1회이고 여기서 재현하지 않는다(`dev-package/prd/rounds/R-DEV-RESET.md` WU-R2).

무엇을 재는가 —
  ⑴ `--yes-reset-dev` 가 없으면 거부한다(기본이 파괴이면 사고가 조용해진다)
  ⑵ 버킷 이름이 `colab-platform-data-dev` 가 아니면 거부한다(staging·prod 식별자)
  ⑶ DB URL 호스트에 `-dev` 가 없으면 거부한다(`deploy_doctor` ⑫ 규약)
  ⑷ 접속 문자열을 argv 로 받는 인자가 **아예 없다**
  ⑸ 계획 파일에 `_ops/` 키가 1건이라도 있으면 전체를 거부한다(`deploy_doctor` ⑭ 가 보는 자리)
  ⑹ 계획 sha256 이 어긋나면 거부한다 · 계획 파일이 실행자 소유 0600 이 아니면 거부한다
  ⑺ 스키마 집합이 기대와 다르면 거부한다(platform `{public, account_admin}` · ai `{public}`)
  ⑻ `--dry-run` 은 DROP·DELETE 를 한 건도 내지 않는다
  ⑼ 네 단계(count · schema · s3-plan · s3-apply)의 green 경로
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib

import pytest

_PATH = pathlib.Path(__file__).resolve().parents[1] / "ops" / "reset_dev_environment.py"
_spec = importlib.util.spec_from_file_location("reset_dev_environment", _PATH)
reset = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(reset)

DEV_BUCKET = "colab-platform-data-dev"
LAB = "0000000000000000000000000A"

PLATFORM_URL = "postgresql://colab_owner:pw@colab-v2-dev-pg.example.internal:5432/colab_platform"
AI_URL = "postgresql://colab_owner:pw@colab-v2-dev-pg.example.internal:5432/colab_ai"
STAGING_URL = "postgresql://colab_owner:pw@colab-v2-staging-pg.example.internal:5432/colab_platform"


# ── 가짜 DB ────────────────────────────────────────────────────────────────

class FakeCursor:
    def __init__(self, responses: list[tuple[str, list[tuple]]]) -> None:
        self._responses = responses
        self.executed: list[str] = []
        self._rows: list[tuple] = []

    def execute(self, sql, params=None):                       # noqa: ANN001
        self.executed.append(sql)
        self._rows = []
        for needle, rows in self._responses:
            if needle in sql:
                self._rows = rows
                break

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, responses: list[tuple[str, list[tuple]]]) -> None:
        self.cur = FakeCursor(responses)
        self.committed = 0
        self.rolled_back = 0

    def cursor(self):
        return self.cur

    def commit(self):
        self.committed += 1

    def rollback(self):
        self.rolled_back += 1

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _rows(schemas: list[str], counts: int = 0):
    return [
        ("pg_namespace", [(s,) for s in schemas]),
        ("from d1_lab", [(LAB,)]),
        ("count(*)", [(counts,)]),
    ]


class FakeConnFactory:
    """체인마다 다른 응답을 준다. 부른 URL 값은 보관하지 않는다."""

    def __init__(self, platform: FakeConn, ai: FakeConn) -> None:
        self.platform = platform
        self.ai = ai

    def __call__(self, url: str):
        if url.endswith("colab_platform"):
            return self.platform
        if url.endswith("colab_ai"):
            return self.ai
        raise AssertionError("기대하지 않은 접속 대상")


# ── 가짜 S3 ────────────────────────────────────────────────────────────────

class FakeS3:
    def __init__(self, objects: dict[str, int] | None = None,
                 uploads: list[tuple[str, str]] | None = None) -> None:
        self.objects = dict(objects or {})
        self.uploads = list(uploads or [])
        self.deleted: list[str] = []
        self.aborted: list[tuple[str, str]] = []

    def list_objects(self, prefix: str):
        for key, size in sorted(self.objects.items()):
            if key.startswith(prefix):
                yield key, size

    def list_multipart_uploads(self, prefix: str = ""):
        return [(k, u) for k, u in self.uploads if k.startswith(prefix)]

    def delete_objects(self, keys: list[str]) -> None:
        self.deleted.extend(keys)
        for key in keys:
            self.objects.pop(key, None)

    def abort_multipart_upload(self, key: str, upload_id: str) -> None:
        self.aborted.append((key, upload_id))
        self.uploads = [u for u in self.uploads if u != (key, upload_id)]


# ── 공통 준비 ──────────────────────────────────────────────────────────────

@pytest.fixture
def dev_env(monkeypatch):
    monkeypatch.setenv("COLAB_CORE_S3_BUCKET", DEV_BUCKET)
    monkeypatch.setenv("COLAB_CORE_S3_REGION", "ap-northeast-2")


@pytest.fixture
def url_files(tmp_path):
    def make(platform: str = PLATFORM_URL, ai: str = AI_URL) -> tuple[str, str]:
        p = tmp_path / "platform.url"
        q = tmp_path / "ai.url"
        p.write_text(platform, encoding="utf-8")
        q.write_text(ai, encoding="utf-8")
        p.chmod(0o600)
        q.chmod(0o600)
        return str(p), str(q)
    return make


def _argv(phase: str, urls, report, *extra: str, yes: bool = True) -> list[str]:
    platform, ai = urls
    argv = ["--target", "dev", "--phase", phase,
            "--platform-url-file", platform, "--ai-url-file", ai,
            "--report", str(report)]
    if yes:
        argv.append("--yes-reset-dev")
    return argv + list(extra)


def _write_plan(path: pathlib.Path, keys: list[str], uploads: list[list[str]],
                *, bucket: str = DEV_BUCKET, digest: str | None = None,
                mode: int = 0o600) -> str:
    payload = {"schema": reset.PLAN_SCHEMA, "bucket": bucket,
               "keys": sorted(keys), "multipartUploads": sorted(uploads)}
    real = reset.plan_digest(payload)
    body = dict(payload, sha256=digest if digest is not None else real)
    path.write_text(json.dumps(body, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    path.chmod(mode)
    return real


# ── ⑴~⑷ 식별자 가드 ───────────────────────────────────────────────────────

def test_플래그가_없으면_거부한다(dev_env, url_files, tmp_path, capsys) -> None:
    """기본이 파괴이면 사고가 조용해진다 — `--yes-reset-dev` 는 명시여야 한다."""
    rc = reset.main(_argv("count", url_files(), tmp_path / "r.json", yes=False))
    assert rc == 2
    assert "--yes-reset-dev" in capsys.readouterr().err


def test_target_이_dev_가_아니면_거부한다(dev_env, url_files, tmp_path, capsys) -> None:
    argv = _argv("count", url_files(), tmp_path / "r.json")
    argv[argv.index("--target") + 1] = "staging"
    rc = reset.main(argv)
    assert rc == 2
    assert "--target" in capsys.readouterr().err


def test_버킷이_staging_이면_거부한다(monkeypatch, url_files, tmp_path, capsys) -> None:
    """staging 식별자 — 버킷 이름 하나로 환경이 갈린다."""
    monkeypatch.setenv("COLAB_CORE_S3_BUCKET", "colab-platform-data-staging")
    monkeypatch.setenv("COLAB_CORE_S3_REGION", "ap-northeast-2")
    rc = reset.main(_argv("count", url_files(), tmp_path / "r.json"))
    assert rc == 2
    assert "colab-platform-data-dev" in capsys.readouterr().err


def test_버킷이_prod_이면_거부한다(monkeypatch, url_files, tmp_path, capsys) -> None:
    monkeypatch.setenv("COLAB_CORE_S3_BUCKET", "colab-platform-data-prod")
    monkeypatch.setenv("COLAB_CORE_S3_REGION", "ap-northeast-2")
    rc = reset.main(_argv("count", url_files(), tmp_path / "r.json"))
    assert rc == 2
    assert "colab-platform-data-dev" in capsys.readouterr().err


def test_DB_호스트에_dev_가_없으면_거부한다(dev_env, url_files, tmp_path, capsys) -> None:
    """DB **이름**은 staging 과 같은 값이라 판별력이 0 이다 — 호스트를 본다."""
    rc = reset.main(_argv("count", url_files(platform=STAGING_URL), tmp_path / "r.json"))
    err = capsys.readouterr().err
    assert rc == 2
    assert "-dev" in err
    assert "pw@" not in err          # 접속 문자열이 출력에 섞이지 않는다


def test_ai_DB_호스트도_따로_본다(dev_env, url_files, tmp_path, capsys) -> None:
    rc = reset.main(_argv("count", url_files(ai=STAGING_URL), tmp_path / "r.json"))
    assert rc == 2
    assert "ai" in capsys.readouterr().err


def test_접속_URL_을_argv_로_받는_인자가_없다(dev_env, url_files, tmp_path) -> None:
    """값은 **파일 경로로만** 받는다 — argparse 가 미지의 인자로 잘라낸다."""
    argv = _argv("count", url_files(), tmp_path / "r.json") + ["--platform-url", PLATFORM_URL]
    with pytest.raises(SystemExit) as exc:
        reset.main(argv)
    assert exc.value.code == 2


def test_URL_파일_자리에_URL_을_주면_거부한다(dev_env, url_files, tmp_path, capsys) -> None:
    argv = _argv("count", url_files(), tmp_path / "r.json")
    argv[argv.index("--platform-url-file") + 1] = PLATFORM_URL
    rc = reset.main(argv)
    assert rc == 2
    assert "파일 경로" in capsys.readouterr().err


# ── ⑸⑹ 계획 파일 가드 ─────────────────────────────────────────────────────

def test_계획에_ops_접두사_키가_있으면_전체를_거부한다(dev_env, url_files, tmp_path, capsys) -> None:
    """`_ops/` 를 지우면 `deploy_doctor` ⑭(백업 24h)가 red 다. 1건이면 전체를 멈춘다."""
    plan = tmp_path / "plan.json"
    digest = _write_plan(plan, ["uploads/a.bin", "_ops/backups/dev/x"], [])
    s3 = FakeS3()
    rc = reset.main(_argv("s3-apply", url_files(), tmp_path / "r.json",
                          "--apply-plan", str(plan), "--plan-sha256", digest),
                    s3_factory=lambda **kw: s3)
    assert rc == 2
    assert "_ops/" in capsys.readouterr().err
    assert s3.deleted == []


def test_계획_sha256_이_다르면_거부한다(dev_env, url_files, tmp_path, capsys) -> None:
    plan = tmp_path / "plan.json"
    _write_plan(plan, ["uploads/a.bin"], [])
    s3 = FakeS3({"uploads/a.bin": 3})
    rc = reset.main(_argv("s3-apply", url_files(), tmp_path / "r.json",
                          "--apply-plan", str(plan), "--plan-sha256", "0" * 64),
                    s3_factory=lambda **kw: s3)
    assert rc == 2
    assert "sha256" in capsys.readouterr().err
    assert s3.deleted == []


def test_계획_파일이_0600_이_아니면_거부한다(dev_env, url_files, tmp_path, capsys) -> None:
    plan = tmp_path / "plan.json"
    digest = _write_plan(plan, ["uploads/a.bin"], [], mode=0o644)
    rc = reset.main(_argv("s3-apply", url_files(), tmp_path / "r.json",
                          "--apply-plan", str(plan), "--plan-sha256", digest),
                    s3_factory=lambda **kw: FakeS3())
    assert rc == 2
    assert "0600" in capsys.readouterr().err


def test_계획_버킷이_다르면_거부한다(dev_env, url_files, tmp_path, capsys) -> None:
    plan = tmp_path / "plan.json"
    digest = _write_plan(plan, ["uploads/a.bin"], [], bucket="colab-platform-data-staging")
    rc = reset.main(_argv("s3-apply", url_files(), tmp_path / "r.json",
                          "--apply-plan", str(plan), "--plan-sha256", digest),
                    s3_factory=lambda **kw: FakeS3())
    assert rc == 2
    assert "버킷" in capsys.readouterr().err


def test_허용_접두사_판정은_경계값을_가른다() -> None:
    """`uploads-backup/` 는 `uploads` 로 시작하지만 접두사가 아니다."""
    assert reset.plan_key_refusal(["uploads/a", "previews/b"]) is None
    assert reset.plan_key_refusal(["uploads-backup/a"]) is not None
    assert reset.plan_key_refusal(["_ops/backups/dev/x"]) is not None
    assert reset.plan_key_refusal([""]) is not None


# ── ⑺ 스키마 집합 가드 ────────────────────────────────────────────────────

def test_platform_스키마_집합이_다르면_거부한다(dev_env, url_files, tmp_path, capsys) -> None:
    """`account_admin` 이 없으면 0025 가 만든 스키마가 이미 어딘가로 갔다는 뜻이다."""
    factory = FakeConnFactory(FakeConn(_rows(["public"])), FakeConn(_rows(["public"])))
    rc = reset.main(_argv("schema", url_files(), tmp_path / "r.json"), connect=factory)
    assert rc == 3
    assert "account_admin" in capsys.readouterr().err
    assert not any("drop schema" in s.lower() for s in factory.platform.cur.executed)


def test_ai_스키마_집합에_여분이_있으면_거부한다(dev_env, url_files, tmp_path, capsys) -> None:
    factory = FakeConnFactory(FakeConn(_rows(["public", "account_admin"])),
                              FakeConn(_rows(["public", "tiger"])))
    rc = reset.main(_argv("schema", url_files(), tmp_path / "r.json"), connect=factory)
    assert rc == 3
    assert "tiger" in capsys.readouterr().err
    assert not any("drop schema" in s.lower() for s in factory.ai.cur.executed)


def test_스키마_집합_판정은_양쪽_기대값을_쓴다() -> None:
    assert reset.schema_set_refusal("platform", {"public", "account_admin"}) is None
    assert reset.schema_set_refusal("ai", {"public"}) is None
    assert reset.schema_set_refusal("platform", {"public"}) is not None
    assert reset.schema_set_refusal("ai", {"public", "account_admin"}) is not None


# ── ⑻ dry-run ────────────────────────────────────────────────────────────

def test_dry_run_은_DROP_을_내지_않는다(dev_env, url_files, tmp_path) -> None:
    factory = FakeConnFactory(FakeConn(_rows(["public", "account_admin"])),
                              FakeConn(_rows(["public"])))
    report = tmp_path / "r.json"
    rc = reset.main(_argv("schema", url_files(), report, "--dry-run"), connect=factory)
    assert rc == 0
    for conn in (factory.platform, factory.ai):
        joined = " ".join(conn.cur.executed).lower()
        assert "drop schema" not in joined
        assert "create schema" not in joined
        assert conn.committed == 0
    assert json.loads(report.read_text(encoding="utf-8"))["dryRun"] is True


def test_dry_run_은_S3_삭제를_하지_않는다(dev_env, url_files, tmp_path) -> None:
    plan = tmp_path / "plan.json"
    digest = _write_plan(plan, ["uploads/a.bin"], [["uploads/b.bin", "UP1"]])
    s3 = FakeS3({"uploads/a.bin": 3}, [("uploads/b.bin", "UP1")])
    rc = reset.main(_argv("s3-apply", url_files(), tmp_path / "r.json", "--dry-run",
                          "--apply-plan", str(plan), "--plan-sha256", digest),
                    s3_factory=lambda **kw: s3)
    assert rc == 0
    assert s3.deleted == []
    assert s3.aborted == []


# ── ⑼ green 경로 ─────────────────────────────────────────────────────────

def test_계수_단계는_경계를_걸고_센다(dev_env, url_files, tmp_path) -> None:
    """FORCE RLS 아래에서 경계를 안 걸면 `count(*)` 가 조용히 0 이다 — 먼저 건다."""
    factory = FakeConnFactory(FakeConn(_rows(["public", "account_admin"], counts=7)),
                              FakeConn(_rows(["public"])))
    s3 = FakeS3({"uploads/a.bin": 3, "previews/p.png": 4, "_ops/backups/dev/z": 5},
                [("uploads/m.bin", "UP1")])
    report = tmp_path / "r.json"
    rc = reset.main(_argv("count", url_files(), report), connect=factory,
                    s3_factory=lambda **kw: s3)
    assert rc == 0
    executed = factory.platform.cur.executed
    first_boundary = next(i for i, s in enumerate(executed) if "app.current_lab" in s)
    first_count = next(i for i, s in enumerate(executed) if "count(*)" in s)
    assert first_boundary < first_count
    body = json.loads(report.read_text(encoding="utf-8"))
    assert body["phase"] == "count"
    assert body["db"]["platform"]["rows"]["d3_dataset"] == 7
    assert body["s3"]["objects"]["uploads/"] == 1
    assert body["s3"]["objects"]["previews/"] == 1
    assert body["s3"]["multipartUploads"] == 1
    assert "_ops/" not in json.dumps(body["s3"]["objects"])


def test_스키마_단계는_두_체인을_재생성하고_다음_명령을_찍는다(dev_env, url_files, tmp_path, capsys) -> None:
    factory = FakeConnFactory(FakeConn(_rows(["public", "account_admin"])),
                              FakeConn(_rows(["public"])))
    rc = reset.main(_argv("schema", url_files(), tmp_path / "r.json"), connect=factory)
    assert rc == 0
    platform_sql = " ".join(factory.platform.cur.executed).lower()
    assert "drop schema public, account_admin cascade" in platform_sql
    assert "create schema public authorization colab_owner" in platform_sql
    assert "revoke create on schema public from public" in platform_sql
    ai_sql = " ".join(factory.ai.cur.executed).lower()
    assert "drop schema public cascade" in ai_sql
    assert "account_admin" not in ai_sql
    assert factory.platform.committed == 1 and factory.ai.committed == 1
    out = capsys.readouterr().out
    assert "db-bootstrap.sh extensions" in out
    assert "migrate-platform" in out
    assert "db-bootstrap.sh app-grants" in out


def test_재생성은_public_스키마_주석을_되돌린다(dev_env, url_files, tmp_path) -> None:
    """`initdb` 의 `public` 은 주석 'standard public schema' 를 달고 있다.

    `DROP SCHEMA public` ＋ `CREATE SCHEMA public` 하면 그 주석이 NULL 이 되고, `pg_dump` 는
    그 차이를 `COMMENT ON SCHEMA public IS '';` 로 뽑는다 ⟹ `schema-diff` 가 red 다.
    로컬 증명에서 실제로 두 체인 다 이 한 줄로 red 였다(`dev-package/sessions/DR-1a-local-proof.md`).
    """
    factory = FakeConnFactory(FakeConn(_rows(["public", "account_admin"])),
                              FakeConn(_rows(["public"])))
    rc = reset.main(_argv("schema", url_files(), tmp_path / "r.json"), connect=factory)
    assert rc == 0
    for conn in (factory.platform, factory.ai):
        joined = " ".join(conn.cur.executed).lower()
        assert "comment on schema public is 'standard public schema'" in joined


def test_s3_계획_단계는_exact_key_목록과_sha256_을_쓴다(dev_env, url_files, tmp_path) -> None:
    s3 = FakeS3({"uploads/a.bin": 3, "previews/p.png": 4, "_ops/backups/dev/z": 5},
                [("uploads/m.bin", "UP1")])
    plan = tmp_path / "plan.json"
    rc = reset.main(_argv("s3-plan", url_files(), tmp_path / "r.json",
                          "--plan-out", str(plan)),
                    s3_factory=lambda **kw: s3)
    assert rc == 0
    body = json.loads(plan.read_text(encoding="utf-8"))
    assert body["keys"] == ["previews/p.png", "uploads/a.bin"]
    assert body["multipartUploads"] == [["uploads/m.bin", "UP1"]]
    assert body["bucket"] == DEV_BUCKET
    assert reset.plan_digest({k: v for k, v in body.items() if k != "sha256"}) == body["sha256"]
    assert oct(plan.stat().st_mode)[-3:] == "600"
    assert s3.deleted == []


def test_s3_적용_단계는_계획의_키만_지운다(dev_env, url_files, tmp_path) -> None:
    plan = tmp_path / "plan.json"
    digest = _write_plan(plan, ["uploads/a.bin", "previews/p.png"], [["uploads/m.bin", "UP1"]])
    s3 = FakeS3({"uploads/a.bin": 3, "previews/p.png": 4, "_ops/backups/dev/z": 5},
                [("uploads/m.bin", "UP1")])
    report = tmp_path / "r.json"
    rc = reset.main(_argv("s3-apply", url_files(), report,
                          "--apply-plan", str(plan), "--plan-sha256", digest),
                    s3_factory=lambda **kw: s3)
    assert rc == 0
    assert sorted(s3.deleted) == ["previews/p.png", "uploads/a.bin"]
    assert s3.aborted == [("uploads/m.bin", "UP1")]
    assert "_ops/backups/dev/z" in s3.objects          # 무접촉
    body = json.loads(report.read_text(encoding="utf-8"))
    assert body["after"]["objects"]["uploads/"] == 0
    assert body["after"]["multipartUploads"] == 0


def test_계획_요약은_sha256_을_정규_직렬화로_만든다() -> None:
    """키 순서가 달라도 같은 계획은 같은 sha 다 — 대조가 성립하는 근거."""
    a = {"schema": reset.PLAN_SCHEMA, "bucket": DEV_BUCKET,
         "keys": ["uploads/a"], "multipartUploads": []}
    b = {"bucket": DEV_BUCKET, "multipartUploads": [],
         "keys": ["uploads/a"], "schema": reset.PLAN_SCHEMA}
    assert reset.plan_digest(a) == reset.plan_digest(b)
    assert reset.plan_digest(a) == hashlib.sha256(
        json.dumps(a, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()


def test_보고서는_실행자_소유_0600_으로_쓴다(dev_env, url_files, tmp_path) -> None:
    factory = FakeConnFactory(FakeConn(_rows(["public", "account_admin"])),
                              FakeConn(_rows(["public"])))
    report = tmp_path / "r.json"
    reset.main(_argv("schema", url_files(), report, "--dry-run"), connect=factory)
    info = report.stat()
    assert oct(info.st_mode)[-3:] == "600"
    assert info.st_uid == os.getuid()
