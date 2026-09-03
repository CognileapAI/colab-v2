"""비밀값을 **경로로** 받는다 — `COLAB_VIZ_*_FILE`.

⭑ ⟨2026-09-03 · 코드리뷰 `CODE-REVIEW-20260903.md` #15⟩ core-api 는 DB 접속 문자열에
`_FILE` 간접참조를 두었는데(`〈121〉-㉯` — `docker inspect` 의 환경변수 목록에 접속
문자열이 통째로 들어 있어 그 값이 작업 기록에 남았다), **viz-render 의 kernel 에는 그
장치 자체가 없었다.** 서비스 토큰과 타일 서명 비밀이 생 env 로 들어와 `docker inspect`
한 번에 드러났고, `COLAB_VIZ_TILE_SIGNING_SECRET_FILE` 을 설정해도 **오류 없이 무시**돼
표면이 조용히 503 만 냈다 — 무시된 변수 이름은 어디에도 안 나왔다.

⚠ **값을 시험이 출력하지 않는다.** 여기서 다루는 것은 「어디서 읽었는가」이지 값이 아니다.
"""
from __future__ import annotations

import pytest

from colab_viz.kernel import config


def _load(monkeypatch, **env):
    for k in ("COLAB_VIZ_SERVICE_TOKEN", "COLAB_VIZ_SERVICE_TOKEN_FILE",
              "COLAB_VIZ_TILE_SIGNING_SECRET", "COLAB_VIZ_TILE_SIGNING_SECRET_FILE"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return config.load_settings()


def test_생_env_는_그대로_읽힌다(monkeypatch):
    """**음성 · 배포를 깨지 않는다.** `_FILE` 은 더한 길이지 갈아 끼운 길이 아니다."""
    s = _load(monkeypatch, COLAB_VIZ_SERVICE_TOKEN="tok",
              COLAB_VIZ_TILE_SIGNING_SECRET="sig")
    assert s.service_token == "tok" and s.tile_signing_secret == "sig"


@pytest.mark.parametrize("name,field", [
    ("COLAB_VIZ_SERVICE_TOKEN", "service_token"),
    ("COLAB_VIZ_TILE_SIGNING_SECRET", "tile_signing_secret"),
])
def test_FILE_이_있으면_그_파일에서_읽는다(monkeypatch, tmp_path, name, field):
    p = tmp_path / "secret"
    # 끝의 개행만 벗긴다 — 값 안의 공백은 손대지 않는다(core-api 와 같은 규칙).
    p.write_text("어떤 값\n", encoding="utf-8")
    s = _load(monkeypatch, **{name + "_FILE": str(p)})
    assert getattr(s, field) == "어떤 값"


@pytest.mark.parametrize("name", ["COLAB_VIZ_SERVICE_TOKEN",
                                  "COLAB_VIZ_TILE_SIGNING_SECRET"])
def test_둘_다_설정되면_죽는다(monkeypatch, tmp_path, name):
    """**두 출처가 갈리면 어느 것이 진실인지 아무도 모른다.**"""
    p = tmp_path / "secret"
    p.write_text("x", encoding="utf-8")
    with pytest.raises(RuntimeError) as e:
        _load(monkeypatch, **{name: "y", name + "_FILE": str(p)})
    assert name in str(e.value) and "_FILE" in str(e.value)


@pytest.mark.parametrize("name", ["COLAB_VIZ_SERVICE_TOKEN",
                                  "COLAB_VIZ_TILE_SIGNING_SECRET"])
def test_못_읽거나_빈_파일은_죽는다(monkeypatch, tmp_path, name):
    """**조용한 폴백이 없다** — 못 읽은 것을 빈 값으로 넘기면 표면이 503 을 내고,
    무시된 변수 이름은 어디에도 안 나온다. 그것이 이 결함의 모양이었다."""
    missing = tmp_path / "없는파일"
    with pytest.raises(RuntimeError) as e:
        _load(monkeypatch, **{name + "_FILE": str(missing)})
    assert str(missing) in str(e.value)

    empty = tmp_path / "빈파일"
    empty.write_text("\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        _load(monkeypatch, **{name + "_FILE": str(empty)})


def test_둘_다_없으면_None_이고_표면이_503_이다(monkeypatch):
    """**음성 · 지금과 같은 동작.** 없으면 프로세스는 뜨고 렌더 표면만 열리지 않는다 —
    「비밀이 없으니 검사를 건너뛴다」와 정반대다(`app/deps._require_configured`)."""
    s = _load(monkeypatch)
    assert s.service_token is None and s.tile_signing_secret is None


def test_값을_예외_메시지에_싣지_않는다(monkeypatch, tmp_path):
    """**경로와 사유만 적는다** — 죽는 자리가 곧 값이 새는 자리가 되면 안 된다."""
    p = tmp_path / "secret"
    p.write_text("절대노출금지값", encoding="utf-8")
    with pytest.raises(RuntimeError) as e:
        _load(monkeypatch, COLAB_VIZ_SERVICE_TOKEN="다른값",
              COLAB_VIZ_SERVICE_TOKEN_FILE=str(p))
    assert "절대노출금지값" not in str(e.value)
    assert "다른값" not in str(e.value)


def test_접미사는_정확히_FILE_이다():
    """읽는 쪽과 배선하는 쪽의 이름이 한 글자라도 어긋나면 배선은 있는데 아무도 안 읽는
    상태가 되고, **그것은 에러를 내지 않는다.** core-api 와 같은 값이어야 한다."""
    assert config.FILE_SUFFIX == "_FILE"


# ── 공백 처리가 core-api 와 **한 글자도 다르지 않다** (코드리뷰 20260903-F #5) ────
#
# 왜 이 시험이 있나 — `COLAB_VIZ_SERVICE_TOKEN` 은 **두 서비스가 같은 값을 비교**한다.
# core-api 는 `resolve_env_or_file` 에서 생 env 를 `.strip()` 하는데 viz 가 안 하면,
# 배포 env 에 공백 하나가 섞인 순간 core 는 `"tok"` 을 보내고 viz 는 `" tok"` 을 기대해
# **미리보기가 통째로 죽는다.** 그 상태는 설정 오류가 아니라 401 로 보인다.
#
# ⚠ **이것은 손사본이다** — 같은 함수가 두 단위의 `kernel/config.py` 에 두 벌로 산다
# (`CLAUDE.md §3-1` 배포 단위 독립). 지금은 두 벌의 본문이 같다(2026-09-03 실측 · 차이는
# 줄바꿈과 `pathlib.Path` ↔ `Path` 뿐). **이 시험은 그 사실이 흐트러지는 날을 잡는다.**
# 손사본을 없애는 것은 codegen 통일 작업항목의 몫이다
# (`CODE-REVIEW-20260903-PLAN.md §4` 유보 1 — `ids.py`·`errors.py` 와 같은 묶음).

@pytest.mark.parametrize("name,field", [
    ("COLAB_VIZ_SERVICE_TOKEN", "service_token"),
    ("COLAB_VIZ_TILE_SIGNING_SECRET", "tile_signing_secret"),
])
def test_생_env_의_앞뒤_공백은_양쪽에서_똑같이_벗겨진다(monkeypatch, name, field):
    """core-api `resolve_env_or_file` 과 **같은 규칙** — 생 env 는 `.strip()` 이다."""
    s = _load(monkeypatch, **{name: "  tok\n"})
    assert getattr(s, field) == "tok"


@pytest.mark.parametrize("name,field", [
    ("COLAB_VIZ_SERVICE_TOKEN", "service_token"),
    ("COLAB_VIZ_TILE_SIGNING_SECRET", "tile_signing_secret"),
])
def test_파일_값은_끝의_공백만_벗긴다(monkeypatch, tmp_path, name, field):
    """**생 env 와 규칙이 다르고, 그 다름이 의도다** — core-api 도 파일은 `rstrip` 이다.

    앞의 공백을 값의 일부로 둘 수 있는 것은 파일뿐이다(`_FILE` 은 값을 그대로 담는
    자리이지 셸이 자르는 자리가 아니다). 두 규칙을 여기서 이름으로 갈라 둔다 —
    한쪽을 「통일」하려는 다음 사람이 이 시험을 먼저 만난다.
    """
    p = tmp_path / "secret"
    p.write_text("  tok  \n", encoding="utf-8")
    s = _load(monkeypatch, **{name + "_FILE": str(p)})
    assert getattr(s, field) == "  tok"


@pytest.mark.parametrize("name,field", [
    ("COLAB_VIZ_SERVICE_TOKEN", "service_token"),
    ("COLAB_VIZ_TILE_SIGNING_SECRET", "tile_signing_secret"),
])
def test_공백뿐인_생_env_는_배선되지_않은_것이다(monkeypatch, name, field):
    """빈 문자열 토큰을 세우면 **아무 값과도 안 맞는 열쇠**가 서고 표면은 401 을 낸다 —
    「배선 안 됨(503)」과 「토큰이 틀림(401)」이 갈려야 고칠 사람이 정해진다."""
    s = _load(monkeypatch, **{name: "   "})
    assert getattr(s, field) is None

