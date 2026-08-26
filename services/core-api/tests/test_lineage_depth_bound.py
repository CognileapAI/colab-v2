"""계보 재귀의 **깊이 상한**과 Lv **클램프**.

정본이 값을 준다 — 지어낸 안전장치가 아니다.

- `VAL-005` 가공 단계 = `Lv0 · Lv1 · Lv2`, **상한 Lv2**
- `POL-020` 자동 보정값 = 「연결된 가공 전 데이터 중 가장 높은 Lv + 1, **상한 Lv2**」
- 용어 = 「Lv0 원자료 · Lv1 1차 가공 · Lv2 집계·분석용. 상한 Lv2」
- 재검토 판정 = 「**Lv3 은 존재할 수 없는 값이다**」

**Lv 은 깊이가 아니라 종류다.** 5홉 떨어진 데이터도 여전히 「집계·분석용」이므로
Lv2 로 접어도 잃는 것이 없다 — 깊이는 계보 그래프에 그대로 남는다.

그리고 **깊은 사슬은 합법이다.** `POL-020` 은 자르기만 하고 금지하지 않는다. 따라서
상한 초과를 오류로 만들면 정본이 허용한 데이터를 막게 된다. 재귀를 2 에서 끊는 것도
절단이 아니다 — 그 너머는 어차피 클램프되어 값이 바뀌지 않는다.
"""
from __future__ import annotations

import time

from conftest import TOKEN_RES, auth
from test_lineage_confirm import _add_parent, _new_dataset

from colab_core.app.main import API_PREFIX


def _lv(client, dataset_id: str) -> int:
    r = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()["processingLevel"]


def _chain(client, length: int) -> list[str]:
    """`주입력` 한 줄 사슬. 앞이 부모, 뒤가 자식."""
    ids = [_new_dataset(client, "사슬 0")]
    for step in range(1, length):
        child = _new_dataset(client, f"사슬 {step}")
        r = _add_parent(client, child, ids[-1], parentRole="주입력", method="집계")
        assert r.status_code == 201, r.text
        ids.append(child)
    return ids


# ═════════════════ ① Lv 클램프 — 상한 Lv2 (POL-020 · VAL-005) ═════════════════
def test_lv_is_clamped_at_2_because_it_is_a_kind_not_a_depth(p2_client) -> None:
    """**Lv3 은 존재할 수 없는 값이다.** 4단 사슬이어도 마지막은 Lv2 다."""
    client = p2_client()
    ids = _chain(client, 4)

    assert _lv(client, ids[0]) == 0, "부모가 없으면 Lv0 (원자료)."
    assert _lv(client, ids[1]) == 1, "Lv0 의 자식은 Lv1 (1차 가공)."
    assert _lv(client, ids[2]) == 2, "Lv1 의 자식은 Lv2 (집계·분석용)."
    assert _lv(client, ids[3]) == 2, (
        "Lv2 의 자식도 Lv2 다 — POL-020 이 상한 Lv2 로 자른다. "
        "Lv3 이 나오면 정본이 「존재할 수 없다」고 한 값을 만든 것이다.")


def test_a_long_chain_never_exceeds_the_cap(p2_client) -> None:
    """사슬이 길어져도 Lv 는 2 를 넘지 않는다. **깊은 사슬 자체는 합법이다** —
    `POL-020` 은 자르기만 하고 금지하지 않으므로 오류가 아니라 클램프다."""
    client = p2_client()
    ids = _chain(client, 8)
    for dataset_id in ids[2:]:
        assert _lv(client, dataset_id) == 2, "상한을 넘는 Lv 가 나왔다."


# ═════════════ ② 다이아몬드 — 합법이고, 응답이 상한 안에서 끝난다 ═════════════
def test_a_diamond_lineage_is_legal_and_the_catalog_still_opens(p2_client) -> None:
    """**다이아몬드는 순환이 아니다.** `A → {B, C} → D` 는 완벽한 DAG 이고
    순환 검사를 전부 통과한다 — `would_create_cycle` 이 막는 그래프가 아니다.

    `_SUMMARY` 의 재귀항이 `UNION ALL` 이고 깊이 상한도 방문 집합도 없으면 CTE 가
    뽑는 것은 **노드가 아니라 경로**이므로 k 겹에서 행 수가 2^k 로 간다. 그리고
    `catalog.py:69`(목록)·`:273`(상세)가 둘 다 `summaries()` 를 부르므로
    **카탈로그를 여는 것만으로 터진다.**
    """
    client = p2_client()
    depth = 18
    current = _new_dataset(client, "마름모 뿌리")
    for level in range(depth):
        left = _new_dataset(client, f"마름모 {level} 좌")
        right = _new_dataset(client, f"마름모 {level} 우")
        merged = _new_dataset(client, f"마름모 {level} 합")
        for branch in (left, right):
            r = _add_parent(client, branch, current, parentRole="주입력", method="분기")
            assert r.status_code == 201, r.text
            r = _add_parent(client, merged, branch, parentRole="주입력", method="합류")
            assert r.status_code == 201, r.text
        current = merged

    started = time.monotonic()
    r = client.get(f"{API_PREFIX}/datasets", headers=auth(TOKEN_RES))
    elapsed = time.monotonic() - started

    assert r.status_code == 200, r.text
    assert elapsed < 5.0, (
        f"카탈로그 목록이 {elapsed:.1f}s 걸렸다 — 재귀가 경로를 열거하고 있다. "
        f"마름모 {depth} 겹이면 경로가 2^{depth} 이다.")
    assert _lv(client, current) == 2, "다이아몬드여도 상한은 Lv2 다."
