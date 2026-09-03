"""`Y-1` 자동 무효화 — 사건 감지 → 무효화 범위 계산 → 재생성.

**stage 1 의 「자동 재생성을 하지 않는다」(`〈74〉`-㉴ 축자)가 여기서만 뒤집힌다**
(`Y-1` 완료 정의 ⓓ). ⭑ **⟨2026-08-31 · Ted RULING ⑲ · `PLAN-SoT §9 〈247〉`⟩ 그 예외의
범위는 「렌더 산출물 한정」이다** — 원본·기준 격자·데이터셋은 **어떤 트리거로도** 다시
만들지 않는다. 이 파일의 절반이 그 바깥을 잠그는 **음성 시험**인 이유가 그것이다.

오라클은 축자다 —
  · 트리거 3종 = 「**미리보기 뒷단 재실행** · 격자 변경 · 파일 추가」(`Y-1` 행 · `〈206〉`-㉮)
  · 무효화 대상 = 「**렌더 산출물**」이고 「그 밖의 산출물을 지우지 않는다」(완료 정의 ⓐ)
  · 「**사람이 부르는 경로가 남아 있되, 자동 경로와 수동 경로가 같은 무효화 범위
    계산기를 지난다**」(완료 정의 ⓒ)
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from colab_viz.domains.d7_visualization import invalidation
from colab_viz.kernel import storage_layout

from conftest import AUTH, make_client


def _wait(predicate, timeout: float = 20.0) -> bool:
    """조건이 설 때까지 기다린다 — **시험이 실행기를 대신 돌리지 않는다.**"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


# ── 도우미 ───────────────────────────────────────────────────────────────────
def _artifact(previews_root: Path, key: str, ext: str) -> invalidation.StaleCandidate:
    """구워진 산출물 하나를 실제로 디스크에 놓고 후보로 만든다."""
    p = storage_layout.preview_path(previews_root, key, ext)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")
    return invalidation.StaleCandidate(cache_key=key, path=p)


_KEY_A = "a" * 64
_KEY_B = "b" * 64


# ── ① 사건 감지 ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("trigger", [
    invalidation.TRIGGER_BACKEND_RERUN,
    invalidation.TRIGGER_GRID_CHANGED,
    invalidation.TRIGGER_FILE_ADDED,
])
def test_트리거_3종이_각각_무효화를_일으킨다(tmp_path, trigger):
    """완료 정의 ⓑ — **셋이 각각** 오라클을 갖는다. 하나로 뭉쳐 세지 않는다."""
    previews = tmp_path / "previews"
    event = invalidation.InvalidationEvent(trigger=trigger, target_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    plan = invalidation.plan(event, produced=[_artifact(previews, _KEY_A, ".png")],
                             previews_root=previews, keep_keys=())
    assert plan.trigger == trigger
    assert plan.stale, "트리거가 왔는데 무효화 범위가 비었다"
    assert plan.regenerate is True


def test_트리거는_셋뿐이고_모르는_사건은_무효화를_일으키지_않는다(tmp_path):
    """**음성** — 트리거 목록을 넓히는 것은 판정이 필요한 일이다(`Y-1` 행 말미 ⚠).
    「색 범위 잠정→확정 전환」이 목록에 없는 것도 그래서다."""
    assert invalidation.TRIGGERS == (
        "미리보기 뒷단 재실행", "격자 변경", "파일 추가"), "트리거 이름은 대장 축자다"
    with pytest.raises(invalidation.UnknownTrigger):
        invalidation.InvalidationEvent(trigger="색 범위 확정",
                                       target_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")


# ── ② 무효화 범위 계산 ───────────────────────────────────────────────────────
def test_새로_구운_키는_범위에서_빠진다(tmp_path):
    """재생성이 낸 산출물까지 지우면 방금 만든 그림이 사라진다."""
    previews = tmp_path / "previews"
    old = _artifact(previews, _KEY_A, ".png")
    new = _artifact(previews, _KEY_B, ".png")
    event = invalidation.InvalidationEvent(trigger=invalidation.TRIGGER_FILE_ADDED,
                                           target_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    plan = invalidation.plan(event, produced=[old, new], previews_root=previews,
                             keep_keys=(_KEY_B,))
    assert [p.name for p in plan.stale] == [old.path.name]
    assert new.path in plan.kept


def test_지도_타일은_무효화_대상이_아니다(tmp_path):
    """**음성 · 완료 정의 ⓐ 「그 밖의 산출물을 지우지 않는다」.**

    같은 슬롯(`미리보기 산출물`)에 **두 규칙**이 산다 — 렌더 산출물(접두사 없음)과
    파이프라인이 구운 지도용 산출물(`tile-` 접두사 · `map_tile_content_key`). 뒤엣것은
    **D5 소유**라 D7 의 무효화가 건드릴 자리가 아니다. 접두사가 그 경계의 실물이다.
    """
    previews = tmp_path / "previews"
    tile_key = storage_layout.map_tile_content_key(
        sourceDigest="d", sourceByteSize="1", gridDigest=storage_layout.GRID_DIGEST_EMBEDDED,
        conversionKind="cog", overviewResampling="average", compression="deflate")
    assert storage_layout.is_map_tile_key(tile_key)
    render = _artifact(previews, _KEY_A, ".png")
    cog = _artifact(previews, tile_key, ".tif")
    event = invalidation.InvalidationEvent(trigger=invalidation.TRIGGER_BACKEND_RERUN,
                                           target_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    plan = invalidation.plan(event, produced=[render, cog], previews_root=previews, keep_keys=())
    assert cog.path not in plan.stale
    assert cog.path in plan.kept
    assert plan.stale == (render.path,)


def test_접수분_루트의_경로는_범위_계산에_들어오면_거절이다(tmp_path):
    """**음성 · `〈247〉` 의 바깥을 잠그는 자리.** 원본·기준 격자는 **미리보기 루트가
    아니라 접수분 루트**에 산다(`layout.json` `roots` 둘). 후보로 들어오는 것 자체가
    버그이므로 **조용히 걸러내지 않고 예외**다 — 걸러내면 그 버그가 다음에도 온다."""
    previews = tmp_path / "previews"
    previews.mkdir()
    uploads = tmp_path / "sources"
    body = storage_layout.storage_path(uploads, "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                                       file_id="01ARZ3NDEKTSV4RRFFQ69G5FAW",
                                       kind=storage_layout.BODY_KIND)
    body.parent.mkdir(parents=True)
    body.write_bytes("원본".encode("utf-8"))
    event = invalidation.InvalidationEvent(trigger=invalidation.TRIGGER_GRID_CHANGED,
                                           target_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    with pytest.raises(invalidation.OutOfScope):
        invalidation.plan(event,
                          produced=[invalidation.StaleCandidate(cache_key=_KEY_A, path=body)],
                          previews_root=previews, keep_keys=())
    assert body.read_bytes() == "원본".encode("utf-8"), "거절하면서도 원본을 건드리지 않는다"


def test_집행은_미리보기_루트_밖을_지우지_않는다(tmp_path):
    """**음성 · 이중 방어.** 범위 계산이 뚫려도 집행이 한 번 더 본다."""
    previews = tmp_path / "previews"
    previews.mkdir()
    outsider = tmp_path / "원본.bin"
    outsider.write_bytes("원본".encode("utf-8"))
    plan = invalidation.InvalidationPlan(
        trigger=invalidation.TRIGGER_FILE_ADDED, target_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        stale=(outsider,), kept=(), regenerate=True)
    with pytest.raises(invalidation.OutOfScope):
        invalidation.apply(plan, previews_root=previews)
    assert outsider.exists(), "집행이 거절했는데 파일이 사라졌다"


def test_집행은_범위_안의_렌더_산출물만_지운다(tmp_path):
    previews = tmp_path / "previews"
    stale = _artifact(previews, _KEY_A, ".png")
    kept = _artifact(previews, _KEY_B, ".png")
    plan = invalidation.InvalidationPlan(
        trigger=invalidation.TRIGGER_FILE_ADDED, target_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        stale=(stale.path,), kept=(kept.path,), regenerate=True)
    removed = invalidation.apply(plan, previews_root=previews)
    assert removed == (stale.path,)
    assert not stale.path.exists()
    assert kept.path.exists()


# ── ③ 재생성 ─────────────────────────────────────────────────────────────────
def _render(client, target_id: str) -> dict:
    r = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": target_id}, "style": {"palette": "단색-파랑"}})
    assert r.status_code == 202, r.text
    return client.get(f"/viz/v1/renders/{r.json()['renderId']}", headers=AUTH).json()


def test_자동_재생성이_실제로_새_산출물을_굽는다(source_root, put_target, tiny_geotiff):
    """**stage 1 원칙이 뒤집히는 그 한 자리** — 사람이 안 눌러도 다시 구워진다."""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    _render(client, tid)
    store = client.app.state.jobs
    event = invalidation.InvalidationEvent(trigger=invalidation.TRIGGER_BACKEND_RERUN,
                                           target_id=tid)
    outcome = store.regenerate(event, source=client.app.state.source)
    assert outcome.job is not None and outcome.job.status == "완료"
    assert outcome.plan.trigger == invalidation.TRIGGER_BACKEND_RERUN
    for a in outcome.job.artifacts.all():
        assert a.path.exists()


def test_재생성해도_원본과_기준_격자는_한_바이트도_안_바뀐다(source_root, put_target,
                                                       tiny_geotiff):
    """**음성 · `〈247〉` 의 본문.** 「보여주기 위한 산출물만」 다시 만든다 —
    원본 데이터·데이터셋은 **어떤 트리거로도** 다시 만들지 않는다."""
    import numpy as np
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff],
                     grid={"lat2d.npy": np.zeros((2, 2)), "lon2d.npy": np.zeros((2, 2))})
    _render(client, tid)
    base = storage_layout.target_dir(source_root, tid)
    before = {p.relative_to(base).as_posix(): p.read_bytes()
              for p in sorted(base.rglob("*")) if p.is_file()}
    assert before, "대상 디렉터리가 비었다 — 시험이 아무것도 안 재고 있다"
    assert len(invalidation.TRIGGERS) == 3, "트리거가 비면 이 시험은 아무것도 안 돌린다"
    for trigger in invalidation.TRIGGERS:
        client.app.state.jobs.regenerate(
            invalidation.InvalidationEvent(trigger=trigger, target_id=tid),
            source=client.app.state.source)
    after = {p.relative_to(base).as_posix(): p.read_bytes()
             for p in sorted(base.rglob("*")) if p.is_file()}
    assert after == before, "재생성이 원본·기준 격자를 건드렸다"


def test_재생성은_대상_디렉터리를_다시_읽는다(source_root, put_target, tiny_geotiff):
    """「파일 추가」 트리거의 뜻 — 추가된 조각이 새 산출물에 들어간다."""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    first = _render(client, tid)
    (storage_layout.target_dir(source_root, tid) / "두번째.tif").write_bytes(
        tiny_geotiff.read_bytes())
    outcome = client.app.state.jobs.regenerate(
        invalidation.InvalidationEvent(trigger=invalidation.TRIGGER_FILE_ADDED,
                                       target_id=tid),
        source=client.app.state.source)
    assert len(outcome.job.spec.target.parts) == 2
    assert first["renderId"] != outcome.job.render_id


def test_운영_기본_실행기에서도_무효화가_실제로_집행된다(source_root, put_target,
                                                  tiny_geotiff):
    """⭑ ⟨2026-09-03 · 코드리뷰 #2⟩ **레이스가 아니라 상시였다.**

    종전 `regenerate` 는 `submit()` **직후** `job.invalidation` 을 읽었는데, 기본
    실행기(`COLAB_VIZ_EXECUTION=thread`)에서 그 필드는 렌더가 끝난 뒤에야 채워진다 —
    즉 운영에서는 **언제나 `None`** 이었고 `invalidation.apply` 호출처가 레포에 그 한
    곳뿐이라 **낡은 미리보기가 한 번도 지워지지 않은 채** 트리거만 ack 됐다.
    오류가 없어서 아무도 몰랐다. 이 시험은 **inline 이 아니라 thread** 로 잰다.
    """
    client = make_client(source_root, "thread")
    tid = put_target(copy_from=[tiny_geotiff])
    r = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid}, "style": {"palette": "단색-파랑"}})
    assert r.status_code == 202
    store = client.app.state.jobs
    first = store.get(r.json()["renderId"])
    assert _wait(lambda: first.status == "완료"), "첫 렌더가 끝나지 않았다"
    old = [a.path for a in first.artifacts.all()]
    assert old and all(p.exists() for p in old)

    # 조각을 하나 더 놓는다 → 원본 해시가 바뀌어 **다시 구우면 키가 달라진다.**
    (storage_layout.target_dir(source_root, tid) / "두번째.tif").write_bytes(
        tiny_geotiff.read_bytes())
    outcome = store.regenerate(
        invalidation.InvalidationEvent(trigger=invalidation.TRIGGER_FILE_ADDED,
                                       target_id=tid),
        source=client.app.state.source)

    assert outcome.job.status == "완료", "재생성이 끝나기 전에 결과를 돌려줬다"
    assert outcome.plan is not None, "thread 실행기에서 무효화 범위가 None 이다"
    assert outcome.removed, "무효화 범위는 있는데 집행이 한 건도 안 됐다"
    assert outcome.removed == outcome.job.invalidation_removed
    assert not any(p.exists() for p in old), "낡은 산출물이 그대로 남았다"
    for a in outcome.job.artifacts.all():
        assert a.path.exists(), "새로 구운 산출물까지 지웠다"


def test_사람이_부른_렌더는_앞의_산출물을_지우지_않는다(source_root, put_target,
                                                tiny_geotiff):
    """**음성 · 집행은 트리거 경로에서만 선다.** 무효화 범위 계산은 두 경로가 함께
    지나지만(완료 정의 ⓒ), **지우는 것**은 사건이 있을 때뿐이다 — 아니면 스타일만
    바꿔 다시 그리는 평범한 요청이 앞의 그림을 지운다."""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    first = client.app.state.jobs.get(_render(client, tid)["renderId"])
    old = [a.path for a in first.artifacts.all()]
    (storage_layout.target_dir(source_root, tid) / "두번째.tif").write_bytes(
        tiny_geotiff.read_bytes())
    second = client.app.state.jobs.get(_render(client, tid)["renderId"])
    assert second.invalidation is not None and second.invalidation.stale, \
        "범위 계산은 두 경로가 함께 지나야 한다"
    assert second.invalidation_removed == (), "수동 경로가 집행까지 했다"
    assert all(p.exists() for p in old), "사람이 부른 렌더가 앞의 산출물을 지웠다"


def test_재생성이_실패하면_낡은_그림을_지우지_않는다(source_root, put_target, tiny_geotiff):
    """`regenerate` 독스트링 축자 — 「굽기 전에 지우면 실패했을 때 볼 그림이 하나도
    안 남는다 — **새 것이 선 뒤에 낡은 것을 치운다**」. 새 것이 서지 못했으면 치우지
    않는 것이 그 문장의 나머지 절반이다."""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    first = client.app.state.jobs.get(_render(client, tid)["renderId"])
    old = [a.path for a in first.artifacts.all()]
    # 그릴 수 없는 바이트로 갈아 끼운다 → 재생성이 실패로 끝난다.
    for p in storage_layout.target_dir(source_root, tid).iterdir():
        p.write_bytes(b"\x00" * 64)
    outcome = client.app.state.jobs.regenerate(
        invalidation.InvalidationEvent(trigger=invalidation.TRIGGER_BACKEND_RERUN,
                                       target_id=tid),
        source=client.app.state.source)
    assert outcome.job.status == "실패"
    assert outcome.removed == ()
    assert all(p.exists() for p in old), "실패한 재생성이 낡은 그림을 지웠다"


# ── ④ 수동 경로 흡수 (완료 정의 ⓒ) ───────────────────────────────────────────
def test_사람이_부르는_경로가_그대로_남아_있다(source_root, put_target, tiny_geotiff):
    """「완료 조건 = **사람이 부르는 경로가 남아 있되**」 — 버튼을 트리거 발신부로
    개조하지 않는다(⚠ ⓒ)."""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    assert _render(client, tid)["status"] == "완료"


def test_수동_경로와_자동_경로가_같은_무효화_범위_계산기를_지난다(source_root, put_target,
                                                          tiny_geotiff):
    """완료 정의 ⓒ 의 축자. **두 경로가 각자 규칙을 갖지 않는다.**"""
    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    _render(client, tid)
    manual = client.app.state.jobs.get(_render(client, tid)["renderId"]).invalidation
    auto = client.app.state.jobs.regenerate(
        invalidation.InvalidationEvent(trigger=invalidation.TRIGGER_BACKEND_RERUN,
                                       target_id=tid),
        source=client.app.state.source).plan
    assert manual is not None, "수동 경로가 계산기를 지나지 않았다"
    assert manual.trigger is None, "수동은 트리거가 아니다 — 경로다"
    assert auto.trigger == invalidation.TRIGGER_BACKEND_RERUN
    assert type(manual) is type(auto) is invalidation.InvalidationPlan
    assert manual.stale == () or all(q.parent == manual.stale[0].parent for q in manual.stale)


# ── ⑤ 경계 (완료 정의 ⓔ · `CLAUDE.md §3-1`) ─────────────────────────────────
def test_D7은_트리거를_발신하지_않는다():
    """**음성 · ⓔ.** 무효화·재생성은 D7 소유, **트리거 발신은 D5** 다. 그래서 이 단위에
    있는 것은 **받는 자리(Port)** 뿐이고, D5 의 표·큐에 붙는 코드가 없다."""
    import io
    import tokenize
    # ⚠ **산문이 아니라 코드를 잰다** — 주석·독스트링에 그 낱말이 나오는 것과 그것을
    # 부르는 것은 다른 사실이다. 문자열·주석 토큰을 버리고 식별자만 남긴다.
    src = Path(invalidation.__file__).read_bytes()
    names = {t.string for t in tokenize.tokenize(io.BytesIO(src).readline)
             if t.type == tokenize.NAME}
    for forbidden in ("publish", "outbox", "psycopg", "sqlalchemy", "requests", "httpx",
                      "boto3", "kafka"):
        assert forbidden not in names, f"트리거 발신·원장 접속이 D7 에 들어왔다: {forbidden}"
    assert hasattr(invalidation, "TriggerPort"), "받는 자리가 Port 로 서 있어야 한다"


def test_원본을_지우거나_덮어쓰는_경로가_이_단위에_없다():
    """**음성 · `〈247〉` 의 바깥을 코드 전체에서 잠근다.** 지우는 자리는 **하나뿐**이고
    그것이 미리보기 루트를 검사한다."""
    root = Path(invalidation.__file__).resolve().parents[2]   # colab_viz/
    offenders = []
    for p in sorted(root.rglob("*.py")):
        text = p.read_text(encoding="utf-8")
        for token in ("shutil.rmtree", "os.remove", "os.unlink"):
            if token in text:
                offenders.append(f"{p.name}:{token}")
        # ⭑ ⟨증보 2026-08-31 · `〈253〉`⟩ 지우는 자리가 **둘**이고 둘 다 갇혀 있다:
        #   `invalidation.py` = 미리보기 루트 안의 렌더 산출물 · `trigger_bus.py` = 이벤트
        #   버스 안의 **알림 파일**(산출물이 아니다). 목록을 넓힌 것이 아니라 **자리마다
        #   자기 울타리를 증명한다** — `test_trigger_intake.py` 의 「버스 밖의 파일은
        #   지우지 않는다」가 뒤엣것을 잠근다. ⚠ 이름을 하나 더 넣는 것은 판정 사안이다.
        if ".unlink(" in text and p.name not in ("invalidation.py", "trigger_bus.py"):
            offenders.append(f"{p.name}:unlink")
    assert offenders == [], f"지우는 자리가 늘었다: {offenders}"
