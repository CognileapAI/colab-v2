"""**대상 간 재사용이 안 ⑷ 아래에서 계속 성립한다** — `A-1` 완료 정의 ⑺(개정판) 회귀.

⭑ **⟨2026-09-02 · Ted 판정 「안 ⑷ 채택」 · `PLAN-SoT §9 〈270〉`-㉲⟩** 종전 문면이 전제한
  「대상 간 재사용의 소멸」은 **안 ⑴ 이 경로를 `targetId` 로 가를 때** 생기는 손실이다.
  **안 ⑷ 는 경로를 가르지 않으므로 그 손실이 일어나지 않는다** — 승계할 것이 없다.
  ⛔ **316,201 B·632,402 B 는 완료 정의에서 빠졌다.** 일어나지 않는 값이다.

⛔⛔ **이 레인의 실측 정정 (2026-09-02 · 워크트리 `lane-a1b`)**
  「대상 간 재사용」이 **두 갈래로 갈린다.** 처음 세운 시험이 한 갈래를 다른 갈래로 착각해
  red 를 냈고, 그 red 가 참이었다:

    ㉮ **지도 타일 키(D5)는 대상과 무관하다** — 재료 여섯(`sourceDigest`·`sourceByteSize`·
       `gridDigest`·`conversionKind`·`overviewResampling`·`compression`)에 `targetId` 가
       **없다**(`kernel/storage_layout.py` `MAP_TILE_KEY_FIELDS`). **`PV-1` 완료 조건 ⑵ 가
       실측한 「같은 바이트를 다시 올리면 다시 굽지 않는다」가 바로 이 갈래다.** ⑺ 가 지키는 것.

    ㉯ **렌더 키(D7)는 이미 대상 범위에 딸려 있다** — 캐시 키가 색범위의 **단계 토큰**을
       싣고(`cache.py:50`) 그 토큰이 `f"{stage}({scope}:{scope_id})"` 라 `scope_id` 가 곧
       대상이다(`scale.py:72`). **이것은 안 ⑷ 이 만든 손실이 아니라 `〈74〉`-㉴ 가 의도한
       성질이다** — 잠정→확정 승격이 키로 무효화되어야 하므로 범위의 출처가 키에 있어야 한다.
       ⟹ 렌더 산출물의 대상 간 공유는 **안 ⑴ 이전에도 성립한 적이 없다.**

  ⚠ 그러므로 ⑺ 는 「렌더 산출물이 대상을 넘어 공유된다」를 요구하지 않는다. 요구는 셋이다 —
    ⑴ **자리가 평평하다**(경로에 `targetId` 가 없다) ⑵ **지도 타일 키가 대상과 무관하다**
    ⑶ **같은 대상·같은 범위면 다시 굽지 않는다**. 아래 넷이 그 셋을 값으로 잠근다.
"""
from __future__ import annotations

import json

import pytest
from conftest import AUTH

from colab_viz.domains.d7_visualization import cache, invalidation, ownership, scale
from colab_viz.kernel import storage_layout


def _render(client, target: dict) -> dict:
    r = client.post("/viz/v1/renders",
                    json={"target": target, "style": {"palette": "단색-파랑"}},
                    headers=AUTH)
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["status"] == "완료", body.get("failure")
    return body


def _artifacts(client, job):
    return client.app.state.jobs.get(job["renderId"]).artifacts


def _slot(client):
    return client.app.state.settings.preview_dir


# ── ⑴ 자리가 평평하다 — 경로에 `targetId` 가 없다 ───────────────────────────
def test_산출물_경로에_대상_식별자가_들어가지_않는다(client, put_target, tiny_geotiff):
    """`layout.json` `why ③` 축자 「평평하다 — 대상(`targetId`)을 경로에 넣지 않는다」.

    **안 ⑷ 가 지킨 것이 정확히 이 한 줄**이고, 안 ⑴ 이 깨려던 것도 이것이다.
    """
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"uploadId": tid})
    slot = _slot(client)
    for a in _artifacts(client, job).all():
        assert a.path.parent == slot, f"자리가 하위 디렉터리로 갈렸다: {a.path}"
        assert tid not in str(a.path), f"경로에 대상 식별자가 실렸다: {a.path}"
        assert tid not in a.cache_key


# ── ⑵ 지도 타일 키는 대상과 무관하다 — `PV-1` 완료 조건 ⑵ 의 실물 ─────────────
def test_지도_타일_키_재료에_대상_식별자가_없다():
    """이 갈래가 「같은 바이트를 다시 올리면 다시 굽지 않는다」를 성립시킨다."""
    assert "targetId" not in storage_layout.MAP_TILE_KEY_FIELDS
    assert not any("target" in f.lower() or "upload" in f.lower() or "dataset" in f.lower()
                   for f in storage_layout.MAP_TILE_KEY_FIELDS)


def test_같은_바이트는_대상이_갈려도_같은_지도_타일_키다():
    """대상을 재료로 받지 않으므로 **대상을 넘겨줄 자리조차 없다.**"""
    fields = dict(sourceDigest="deadbeef", sourceByteSize="1024", gridDigest="내장",
                  conversionKind="cog", overviewResampling="average", compression="deflate")
    assert storage_layout.map_tile_content_key(**fields) == \
        storage_layout.map_tile_content_key(**fields)
    # 대상을 재료로 **넘길 수조차 없다** — 규약에 없는 재료는 거절된다
    with pytest.raises(ValueError):
        storage_layout.map_tile_content_key(targetId="01J0TARGET00000000000000", **fields)


# ── ㉯ 렌더 키가 대상 범위에 딸린다는 것은 **의도된 성질**이다 ─────────────────
def test_렌더_키는_색범위_단계_토큰_때문에_대상마다_갈린다():
    """⚠ 이것을 「안 ⑷ 의 손실」로 읽지 않는다 — `〈74〉`-㉴ 가 요구한 무효화 장치다.

    승격(잠정→확정)이 키로 무효화되려면 **범위의 출처가 키 안에 있어야** 하고, 그 출처가
    곧 대상이다. 뺄 수 없다 — 빼면 승격 뒤에도 낡은 그림이 산다.
    """
    import numpy as np
    arrays = [np.linspace(0, 100, 100, dtype="f4").reshape(-1, 1)]
    a = scale.for_dataset("01ARZ3NDEKTSV4RRFFQ69G5FAW", arrays)
    b = scale.for_dataset("01ARZ3NDEKTSV4RRFFQ69G5FAX", arrays)
    assert a.token() != b.token(), "단계 토큰이 대상을 싣지 않는다 = 승격 무효화가 깨진다"

    base = dict(source_digest="d", long_side=1024, downsample="blockavg", fills=(),
                palette="단색-파랑", crs=cache.NO_CRS, selection="v")
    assert cache.render_cache_key(color_range=a, **base) != \
        cache.render_cache_key(color_range=b, **base)
    # **같은 범위면 같은 키다** — 재사용의 단위는 「대상」이 아니라 「범위」다
    assert cache.render_cache_key(color_range=a, **base) == \
        cache.render_cache_key(color_range=a, **base)


# ── ⑶ 같은 대상·같은 범위면 다시 굽지 않는다 ────────────────────────────────
def test_같은_대상을_다시_렌더하면_자리가_늘지_않는다(client, put_target, tiny_geotiff):
    """「다시 만들지 않고 찾아 쓸 수 있다」의 실측 — **자리가 늘지 않고 그림이 같다.**

    ⛔ **실측 정정** — D7 은 같은 키를 만나면 **건너뛰지 않고 같은 자리에 덮어쓴다.**
    그래서 사이드카의 `created` 는 회차마다 갱신된다. 재사용의 실물은 「파일을 안 만든다」가
    아니라 **「자리가 하나로 유지되고 그림이 같다」**이고, 그것이 `PV-1` ⑵ 의 축자
    (「그 자리에 기록되어 다시 만들지 않고 **찾아 쓸 수 있다**」)와 맞는다.
    ⚠ 「건너뛰기」로 바꾸는 것은 별도 판정이다 — 여기서 요구로 세우지 않는다.
    """
    tid = put_target(copy_from=[tiny_geotiff])
    job1 = _render(client, {"uploadId": tid})
    slot = _slot(client)
    before = {p.name: p.read_bytes() for p in slot.iterdir()}

    job2 = _render(client, {"uploadId": tid})
    after = {p.name: p.read_bytes() for p in slot.iterdir()}

    assert {a.cache_key for a in _artifacts(client, job1).all()} == \
        {a.cache_key for a in _artifacts(client, job2).all()}
    assert set(before) == set(after), f"자리에 파일이 새로 생겼다: {sorted(set(after) - set(before))}"
    for name, blob in before.items():
        if name.endswith(".json"):
            # 사이드카는 `created` 한 칸만 갱신된다 — 나머지가 갈리면 그림이 갈린 것이다
            a, b = json.loads(blob), json.loads(after[name])
            a.pop("created"), b.pop("created")
            assert a == b, f"{name} 의 사이드카 내용이 갈렸다"
        else:
            assert after[name] == blob, f"{name} 의 바이트가 갈렸다"


# ── 회수가 재사용을 잡아먹지 않는다 ─────────────────────────────────────────
def test_회수는_살아_있는_산출물을_건드리지_않는다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"uploadId": tid})
    slot = _slot(client)
    groups = ownership.scan(slot)
    fids: set[str] = set()
    for g in groups:
        if g.sidecar:
            fids |= set(ownership.source_file_ids(g.sidecar))
    assert fids, "사이드카가 fileId 를 싣지 않았다"
    ledger = ownership.Ledger(dataset_files=frozenset(fids), upload_files=frozenset(fids))

    plan = invalidation.reclaim_plan(groups, ledger, previews_root=slot)
    assert plan.stale == (), "살아 있는 산출물을 회수 대상으로 세웠다"
    assert invalidation.apply(plan, previews_root=slot) == ()
    assert all(a.path.exists() for a in _artifacts(client, job).all())


def test_사이드카_baked_for_는_구운_대상을_적고_자리를_가르지_않는다(client, put_target, tiny_geotiff):
    """⚠ **덫 ① 의 반대편** — `baked_for` 는 대상을 적지만 **키에는 들어가지 않는다.**"""
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"uploadId": tid})
    store = _artifacts(client, job)
    doc = json.loads(store.detail_sidecar.path.read_text(encoding="utf-8"))
    assert doc["baked_for"] == {"target_id": tid, "is_upload": True}
    assert doc["baked_for"]["target_id"] not in store.detail_sidecar.cache_key
