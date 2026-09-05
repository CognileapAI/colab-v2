"""환경 판정 — `COLAB_VIZ_SOURCE_MODE`·`COLAB_VIZ_PREVIEW_SINK` 와 s3 필수값 (`〈342〉-㉱`).

순수 시험 — `kernel/config.py`·`kernel/health.py` 만 import 한다.
`../core-api/.venv/bin/python -m pytest tests/test_source_mode_env.py -q --noconftest`

**모르는 값은 기동 거부다.** 오타를 local 로 조용히 접으면 dev 가 EC2 디스크를 읽고도
아무도 모른다 — core 의 `COLAB_CORE_STORAGE_MODE` 와 같은 규칙이다.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from colab_viz.kernel import config
from colab_viz.kernel.config import Settings, load_settings, parse_work_max_bytes, validate
from colab_viz.kernel.health import healthz_body

S3_ENV = {
    "COLAB_VIZ_SOURCE_MODE": "s3",
    "COLAB_VIZ_S3_BUCKET": "bucket-x",
    "COLAB_VIZ_S3_REGION": "ap-northeast-2",
    "COLAB_VIZ_WORKDIR": "/tmp/viz-work",
    "COLAB_VIZ_WORK_MAX_BYTES": "1073741824",
}


@pytest.fixture
def env(monkeypatch):
    for name in ("COLAB_VIZ_SOURCE_MODE", "COLAB_VIZ_S3_BUCKET", "COLAB_VIZ_S3_REGION",
                 "COLAB_VIZ_WORKDIR", "COLAB_VIZ_WORK_MAX_BYTES", "COLAB_VIZ_PREVIEW_SINK",
                 "COLAB_VIZ_PREVIEW_S3_PREFIX", "COLAB_VIZ_SOURCE_ROOT"):
        monkeypatch.delenv(name, raising=False)

    def _set(**values: str) -> None:
        for k, v in values.items():
            monkeypatch.setenv(k, v)
    return _set


# ── 소스 모드 ────────────────────────────────────────────────────────────────

def test_기본은_local_이고_s3_값은_불요다(env):
    s = load_settings()
    assert s.source_mode == "local" and s.preview_sink == "local"
    assert s.s3_bucket is None and s.workdir is None and s.work_max_bytes is None


def test_모르는_모드는_기동_거부다(env):
    env(**{**S3_ENV, "COLAB_VIZ_SOURCE_MODE": " S3 "})   # 공백·대문자는 접는다
    assert load_settings().source_mode == "s3"
    env(COLAB_VIZ_SOURCE_MODE="minio")
    with pytest.raises(RuntimeError, match="COLAB_VIZ_SOURCE_MODE"):
        load_settings()


def test_s3_모드의_필수값이_하나라도_없으면_거부한다(env):
    for missing in ("COLAB_VIZ_S3_BUCKET", "COLAB_VIZ_S3_REGION", "COLAB_VIZ_WORKDIR",
                    "COLAB_VIZ_WORK_MAX_BYTES"):
        env(**{k: v for k, v in S3_ENV.items() if k != missing})
        with pytest.raises(RuntimeError, match=missing):
            load_settings()
        for k in S3_ENV:
            env(**{k: ""})


def test_s3_모드_전부_있으면_뜨고_SOURCE_ROOT_는_불요다(env):
    env(**S3_ENV)
    s = load_settings()
    assert s.source_mode == "s3"
    assert s.s3_bucket == "bucket-x" and s.s3_region == "ap-northeast-2"
    assert s.workdir == Path("/tmp/viz-work")
    assert s.work_max_bytes == 1073741824
    assert s.source_root == config.DEFAULT_SOURCE_ROOT       # 읽히지 않는 자리 — 기본값 그대로


# ── 작업 디렉터리 상한 3상태 ────────────────────────────────────────────────

def test_상한_3상태_숫자_none_미설정():
    assert parse_work_max_bytes("1048576") == 1048576
    assert parse_work_max_bytes(" none ") == math.inf          # 명시 무제한
    assert parse_work_max_bytes("NONE") == math.inf
    assert parse_work_max_bytes(None) is None                  # 미설정 — 호출자가 거부한다
    assert parse_work_max_bytes("   ") is None
    for bad in ("0", "-1", "1.5", "1GB", "unlimited"):
        with pytest.raises(RuntimeError, match="COLAB_VIZ_WORK_MAX_BYTES"):
            parse_work_max_bytes(bad)


def test_미설정_상한은_s3_모드에서_거부되고_none_은_통과한다(env):
    env(**{**S3_ENV, "COLAB_VIZ_WORK_MAX_BYTES": "none"})
    assert load_settings().work_max_bytes == math.inf
    env(COLAB_VIZ_WORK_MAX_BYTES="")
    with pytest.raises(RuntimeError, match="COLAB_VIZ_WORK_MAX_BYTES"):
        load_settings()


def test_직접_만든_Settings_도_같은_규칙으로_검사된다():
    """`create_app` 이 `validate` 를 부른다 — env 를 거치지 않은 설정도 반쪽이면 거부다."""
    validate(Settings(source_root=Path("/x"), service_token="t"))
    with pytest.raises(RuntimeError, match="COLAB_VIZ_SOURCE_MODE"):
        validate(Settings(source_root=Path("/x"), service_token="t", source_mode="gcs"))
    with pytest.raises(RuntimeError, match="COLAB_VIZ_WORK_MAX_BYTES"):
        validate(Settings(source_root=Path("/x"), service_token="t", source_mode="s3",
                          s3_bucket="b", s3_region="r", workdir=Path("/w")))
    validate(Settings(source_root=Path("/x"), service_token="t", source_mode="s3",
                      s3_bucket="b", s3_region="r", workdir=Path("/w"), work_max_bytes=1))


# ── 미리보기 싱크 ───────────────────────────────────────────────────────────

def test_모르는_싱크는_거부하고_s3_싱크는_버킷_리전을_요구한다(env):
    env(COLAB_VIZ_PREVIEW_SINK="disk")
    with pytest.raises(RuntimeError, match="COLAB_VIZ_PREVIEW_SINK"):
        load_settings()
    env(COLAB_VIZ_PREVIEW_SINK="s3")
    with pytest.raises(RuntimeError, match="COLAB_VIZ_S3_BUCKET"):
        load_settings()
    env(COLAB_VIZ_PREVIEW_SINK="s3", COLAB_VIZ_S3_BUCKET="b", COLAB_VIZ_S3_REGION="r")
    s = load_settings()                                    # 소스는 local 이어도 싱크만 s3 가 된다
    assert s.preview_sink == "s3" and s.preview_s3_prefix == "previews"
    env(COLAB_VIZ_PREVIEW_S3_PREFIX="stage/previews")
    assert load_settings().preview_s3_prefix == "stage/previews"


def test_s3_싱크여도_미리보기_URL_기본은_그대로다(env):
    env(COLAB_VIZ_PREVIEW_SINK="s3", COLAB_VIZ_S3_BUCKET="b", COLAB_VIZ_S3_REGION="r")
    assert load_settings().preview_url_base == "/previews"


# ── healthz — deploy_doctor 가 읽는 키 이름은 고정이다 ──────────────────────

def test_healthz_본문에_sourceMode_previewSink_가_있다():
    body = healthz_body(Settings(source_root=Path("/x"), service_token=None))
    assert body["unit"] == "viz-render" and body["status"] == "alive" and body["implemented"] is True
    assert body["sourceMode"] == "local" and body["previewSink"] == "local"

    body = healthz_body(Settings(source_root=Path("/x"), service_token=None, source_mode="s3",
                                 s3_bucket="b", s3_region="r", workdir=Path("/w"),
                                 work_max_bytes=1, preview_sink="s3"))
    assert body["sourceMode"] == "s3" and body["previewSink"] == "s3"
    # 버킷·경로 같은 값은 헬스에 싣지 않는다 — 모드만 말한다
    assert "bucket" not in str(body).lower()
