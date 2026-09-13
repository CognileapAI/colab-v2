"""D3 조립 — **데이터셋 삭제(묘비)** 두 op (`DL-1`).

정본은 계약 산문 하나다 (`contracts/seams/fe-core.yaml`) —

  `deleteDataset`            「**소유자 또는 교수만.** 파일·미리보기만 지우고 이름·주제·Lv·
                             계보 관계·프로젝트 연결·Verified 는 남긴다. 되돌리는 전이가 없다.
                             대기 중인 접근 요청은 자동으로 닫힌다 (§9).」
  `getDatasetDeletionImpact` 확인 모달이 말해야 하는 파급 세 칸.

**왜 새 파일인가.** 삭제는 D3(카탈로그)·D2(접근·승인)·D4(계보) 셋의 사실을 한 자리에서
조립한다. `catalog.py` 에 얹으면 그 파일이 조회와 파괴를 함께 들고, 두 레인이 같은 파일에서
만난다. 조립 루트가 도메인 함수를 부르는 무늬는 `routes/access.py` 와 같다.

**미리보기도 여기서 지운다** (`DL-2` · 22차 해제 ㉯). 계약 산문의 「파일·**미리보기**만
지우고」를 집행하는 자리는 ⑧-c 한 줄이고, 지울 대상을 고르는 일은 viz-render 안이다
(`core-viz.yaml` `reclaimPreviews`) — core 는 **방금 지워진 `fileId` 집합**만 넘긴다.
／ 종전 ~~「⛔ 미리보기는 이 회차가 지우지 않는다 … 릴레이 한 줄을 미리 넣지 않는다」~~ —
`DL-1` 회차의 사실이었고 `DL-2` 가 같은 PR 에서 닫았다.

**판정 순서는 400 → 404 → 403 이다** (`routes/access.py::_decidable_request` 독스트링 ·
`routes/ingestion.py::_file_target`). 권한을 먼저 보면 남의 연구실 식별자에 403 이 나가고
그 403 이 「그 식별자는 있다」를 알린다 (P-9·P-10).

**계약에 410 이 없다.** 그래서 묘비도 404 다 — 경계 밖·무존재와 **본문까지 같다.** 두 번째
DELETE 도 404 이고, 화면은 묘비면 상세 자체가 410 화면이라 버튼이 서지 않는다.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from ...domains import d2_access, d3_audit, d3_catalog, d4_lineage, d8_insight
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db
from ..relay import RelayRefused, RelayUnavailable
from .ingestion import _storage

router = APIRouter(tags=["catalog"])

#: 대기 접근 요청이 자동으로 닫힐 때 남는 사유. **`[정본 무근거]`** — 정본은 「닫힌다」라는
#: 동작만 적었고 문장을 주지 않았다 (Ted 판정 ⓕ). 상태 집합에 「닫힘」이 없어
#: `거절됨` 으로 닫으므로, 요청자에게는 이 문장이 **왜 닫혔는지**를 말하는 유일한 자리다.
ACCESS_REQUEST_CLOSED_REASON = "데이터가 지워져서 요청이 닫혔어요."

#: 운영자 감사 행위 문자열. **물리 삭제와 다른 값이다.**
#: `ops/purge_datasets.py`(→ `d3_audit.append_deletion_snapshots`)가 같은 표 `d3_operator_audit` 에
#: `dataset.deleted` 로 적는데, 한 데이터셋은 **묘비가 된 뒤 나중에 물리 삭제될 수 있다** —
#: 두 경로가 같은 문자열을 쓰면 같은 `target_id` 에 같은 이름이 2행 쌓이고,
#: 「대상당 1행」을 전제하는 질의(`tests/test_operator_notifications_e2e.py:136`)가 깨진다.
#: 되돌릴 수 있는 정도도 다르다 — 묘비는 행이 남고, 물리 삭제는 행이 사라진다.
#: ⚠ 이 값을 늘리면 **일일 보고의 이름표도 함께 늘려야 한다** — `infra/notifications/digest.py`
#: 가 `LABELS[action]` 을 직접 첨자로 읽어서(`:195`·`:200`) 빠지면 그날 보고가 `KeyError` 로 죽는다.
#: (오케스트레이터 결정 2026-09-12 · Ted 개정 가능)
AUDIT_ACTION_TOMBSTONED = "dataset.tombstoned"

#: 권한 거절 문구 — 정본 조항을 괄호에 달아 「어느 규칙이 막았는가」를 사람이 되짚게 한다.
FORBIDDEN_MESSAGE = "데이터셋 삭제는 소유자 또는 교수만 할 수 있다 (Policy_데이터셋_상세 §6)."

#: 미리보기 회수 실패 봉투 (`DL-2`). **503 이 아니라 500 이다** — 저쪽이 못 답한 것이
#: 사실이지만 사용자에게 일어난 일은 「삭제가 되돌아갔다」이고, 그것이 이 응답이 말해야 하는
#: 것이다. 봉투 코드는 하나이고 **문구가 둘**이다 — 아래 두 상수를 보라.
PREVIEW_RECLAIM_FAILED = "PREVIEW_RECLAIM_FAILED"

#: ⓐ **못 닿았다**(`RelayUnavailable` · 미도달·5xx). 재시도가 유효하다 — 회수도 삭제 재호출도
#: 멱등이라 다시 눌러도 안전하고, 그 사실을 문구가 알린다.
PREVIEW_RECLAIM_UNAVAILABLE_MESSAGE = (
    "미리보기 산출물을 지우지 못해 삭제를 되돌렸어요. 잠시 뒤 다시 시도해 주세요.")

#: ⓑ **읽어 보고 물리쳤다**(`RelayRefused` · viz 4xx). ⛔ **재시도를 권하지 않는다** —
#: 같은 요청은 같은 답을 받는다. 고칠 사람은 사용자가 아니라 우리이고, 그 단서는
#: `details.reason` 의 저쪽 상태·본문이다. 두 갈래에 같은 문구를 쓰면 사용자가 고칠 수 없는
#: 것을 반복하게 만들고, 그 반복이 운영자에게는 「간헐 장애」로 보인다.
PREVIEW_RECLAIM_REFUSED_MESSAGE = (
    "미리보기 산출물 회수 요청이 거절되어 삭제를 되돌렸어요.")

#: viz-render 가 배선되지 않은 배포에서 회수를 건너뛴 사실의 **기계가 긁을 이름**
#: (선례 `app/relay.py SUGGEST_UNAVAILABLE` · `routes/catalog.py::_search_log`).
#: ⚠ **조용히 넘어가지 않는다** — 건너뛴 삭제가 몇 건인지 셀 수 없으면 그 배포에
#: 산출물이 쌓여도 아무도 모른다.
DELETION_LOGGER = "colab_core.deletion"
PREVIEWS_SKIPPED = "dataset.previews_skipped"
PREVIEWS_UNCONFIGURED = "PREVIEWS_UNCONFIGURED"
#: 회수가 실제로 돈 자리. **계수를 남기는 유일한 자리**다 — 「지웠다」와 「지울 것이
#: 없었다」는 둘 다 204 라서 응답으로는 갈리지 않는다.
PREVIEWS_RECLAIMED = "dataset.previews_reclaimed"

_deletion_log = logging.getLogger(DELETION_LOGGER)


def _deletable(db: Session, subject: Subject, datasetId: str) -> d3_catalog.DatasetCore:
    """두 op 이 공유하는 관문 — 400 · 404 · 403 을 **한 자리에서** 가른다.

    ⓵ 모양이 틀리면 400 이다. 404 로 접으면 「없다」와 「그런 모양은 없다」가 같은 답이 되어
       화면이 오타를 못 고친다 (`access.py::_living_dataset` 축자).
    ⓶ `find_dataset_core` 가 `None` 이면 404 — 경계 밖·묘비·무존재가 **한 자리로 접힌다.**
       `find_dataset_core` 는 `deleted_at IS NULL` 을 걸고 RLS 가 남의 연구실 행을 지운다.
    ⓷ 권한은 마지막이다. `d2_access.can_delete_dataset` 이 판정하고 여기서 다시 쓰지 않는다.

    **파급 조회도 같은 관문을 지난다.** 갈리면 「지우지는 못하는데 파급은 읽는다」가 되고,
    그 값에는 접근 요청 대기 건수가 들어 있다.
    """
    if not Ulid.is_valid(datasetId):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    core = d3_catalog.find_dataset_core(db, Ulid(datasetId))
    if core is None:
        raise errors.not_found()
    if not d2_access.can_delete_dataset(db, account_id=subject.account_id,
                                        owner_id=core.owner_id):
        raise errors.forbidden(FORBIDDEN_MESSAGE)
    return core


@router.get("/datasets/{datasetId}/deletion-impact", name="getDatasetDeletionImpact")
def get_dataset_deletion_impact(datasetId: str,
                                subject: Subject = Depends(current_subject),
                                db: Session = Depends(scoped_db)) -> dict:
    """확인 모달이 말해야 하는 파급 세 칸 (계약 `DeletionImpact`).

    **파생 수는 살아 있는 자식만 센다.** 묘비 자식은 열 화면이 없어 「자리가 남아요」의
    대상이 아니다 — 지워진 데이터의 계보에 자리가 남는다고 말하면 사람이 확인할 수 없는
    파급을 읽는다.

    ⚠ **D4 가 D3 를 조인하지 않는다** (`CLAUDE.md §3-1`). `edges_of` 는 관계만 내고
    생존 여부는 D3 가 답하며, 둘을 합치는 것은 이 조립 루트다.
    """
    core = _deletable(db, subject, datasetId)
    dataset_id = Ulid(datasetId)
    children = {e["child_dataset_id"] for e in d4_lineage.edges_of(db, dataset_id)
                if e["parent_dataset_id"] == core.dataset_id}
    living = sum(1 for c in children if d3_catalog.dataset_exists(db, Ulid(c)))
    return {
        "derivedDatasetCount": living,
        "verified": bool(d2_access.verified_state(db, dataset_id)),
        "pendingAccessRequestCount": d2_access.count_pending_access_requests(db, dataset_id),
    }


@router.delete("/datasets/{datasetId}", name="deleteDataset", status_code=204)
def delete_dataset(request: Request, datasetId: str,
                   subject: Subject = Depends(current_subject),
                   db: Session = Depends(scoped_db)) -> Response:
    """묘비로 전환하고 **파일 행과 그 바이트를 회수한다.**

    순서에 이유가 있다 (핸들러 본문 전체가 커밋 **전**이다 — `app/deps.py::scoped_db`) —

    ① `lock_dataset` — 관문 뒤에 묘비가 됐으면 404. 동시 요청 둘이 각자 지나가는 자리를 막는다.
    ② `snapshot_access` ＋ `open_access_for_deletion` — ⭑ **RLS 우회가 아니라 경계를 잠깐
       여는 것이다.** `body_access` RESTRICTIVE 에는 소유자·역할 조항이 없어(스키마 실물)
       잠긴 데이터셋의 `d3_file` 이 소유자·교수에게도 0행이다. 이 두 줄이 없으면 삭제가
       키를 못 읽고 행도 못 지운 채 **조용히 0건**으로 성공한다.
    ③ `files_for_download` — **키는 원장이 들고 있다. 여기서 짓지 않는다.** 접두 스캔이
       아니라 원장 키 목록이 삭제 대상이다(시드 lab_id 가 겹치는 버킷에서 남의 데이터를
       지우는 경로를 만들지 않는다 — `.claude/rules/deploy.md`).
    ④ `tombstone_dataset` — 0행이면 그 사이에 누가 먼저 지운 것이다. 404.
    ⑤ `close_pending_access_requests` — 처리된 행은 `state` 조건이 이미 뺀다(0행이 정상).
    ⑥ `delete_files_of` — 한 문장이라 statement 트리거가 한 번 돌아 조각 수·용량 합계를 민다.
    ⑦ `restore_access` — ⭑ **「열림」 창은 이 트랜잭션 안에서만 존재한다.** 빠뜨리면 잠긴
       데이터가 열린 채로 커밋된다.
    ⑧ 활동 한 줄 — 지운 일도 활동이다 (계약 `listActivities` 산문).
    ⑧-b 운영자 감사 스냅샷 — 데이터셋 쓰기는 `d3_operator_audit` 에 남는다 (`0027` ·
       선례 `d3_catalog.update_dataset`·`routes/project.py::delete_project`).
    ⑧-c 미리보기 회수 — ③ 이 읽은 `fileId` 집합을 viz-render 에 넘긴다 (`DL-2`).
       ⭑ **⑨ 보다 앞이다.** 회수가 실패하면 500 이고 전체가 롤백되는데, 바이트를 먼저
         지워 두면 되돌아간 원장이 **행 있고 객체 없음**을 가리킨다. 순서를 바꾸면 재시도가
         복구가 아니라 손실 확정이 된다.
       ⚠ **실패는 두 갈래이고 문구가 다르다** — `RelayUnavailable`(못 닿음·5xx)은 재시도를
         권하고, `RelayRefused`(viz 4xx · 읽어 보고 물리침)는 **권하지 않는다.** 같은 요청은
         같은 답을 받으므로 재시도 유도는 사용자가 고칠 수 없는 것을 반복하게 만든다.
         **롤백과 봉투 코드는 둘 다 같다**(500 `PREVIEW_RECLAIM_FAILED`).
       ⚠ **중계가 없으면(`app.state.previews is None`) 건너뛰고 한 줄 남긴다.** 싱크 없는
         배포에는 지울 산출물이 없고(dev·prod 는 토큰이 `:?` 필수라 미설정이 곧 기동 거부),
         500 으로 내면 로컬·시험에서 삭제 자체가 불가능해진다. 규율 6(관대한 기본값)과의
         긴장은 회부문 ⓓ4 로 올려 뒀다 — **조용히 넘어가지는 않는다.**
    ⑨ 바이트 — **커밋 전**이다. 저장소가 터지면 예외가 그대로 올라가 **전체가 롤백**되고
       500 이 나간다(선례 `ingestion.delete_dataset_grid_file` · `U-2` ⓑ 와 같은 성질).
       `discard` 는 없는 키에 조용하므로 **재호출이 멱등**이다.
       ⚠ 대가 — 실패한 키 **앞에서** 지워진 바이트는 행이 복원돼 재시도까지 잠깐
       「행 있고 객체 없음」이다. 키 수가 작고 삭제 의도가 확실해 감수한다. 「묘비 먼저
       커밋 → 바이트 → 성공 키 행만 삭제」는 스위퍼가 없어(`U-2` 미착수) 잔존 행이 영영
       남으므로 이번엔 택하지 않는다.

    **`d3_file` 행을 지우는 근거** — 바이트를 지운 뒤 행을 두면 원장이 거짓이 된다
    (`files_for_download`·`list_files`·`body_file_count` 는 `deleted_at` 을 안 본다) ·
    `file_count`·`total_size_bytes` 는 트리거로만 유지된다 · `U-2` 판별식이 원장 행을
    「참조 있음」으로 읽어 실패한 바이트를 영영 못 줍는다. `representative_file_id` 는
    FK `ON DELETE SET NULL` 이 되돌린다.
    """
    core = _deletable(db, subject, datasetId)
    dataset_id = Ulid(datasetId)

    if not d3_catalog.lock_dataset(db, dataset_id):
        raise errors.not_found()      # 관문 뒤에 묘비가 됐다 — 없는 것으로 답한다

    snapshot = d2_access.snapshot_access(db, dataset_id)
    d2_access.open_access_for_deletion(db, dataset_id)
    files = d3_catalog.files_for_download(db, dataset_id)
    keys = [f["storage_key"] for f in files]
    # ⭑ **회수 입력도 같은 한 번의 조회에서 나온다** — 행을 지운 뒤(⑥) 다시 읽으면 0건이고,
    #   그 0건은 에러가 아니라 「지울 것이 없다」로 위장한다.
    file_ids = [str(f["id"]) for f in files]

    if not d3_catalog.tombstone_dataset(db, dataset_id=dataset_id,
                                        actor_id=subject.account_id):
        raise errors.not_found()
    d2_access.close_pending_access_requests(db, dataset_id=dataset_id,
                                            decider_id=subject.account_id,
                                            reason=ACCESS_REQUEST_CLOSED_REASON)
    d3_catalog.delete_files_of(db, dataset_id)
    d2_access.restore_access(db, dataset_id, snapshot)

    d8_insight.record_activity(db, actor_id=subject.account_id,
                               action=d8_insight.ACTION_DATASET_DELETED,
                               target_kind="데이터셋", target_id=dataset_id)
    # ⑧-b **운영자 감사 스냅샷** (`0027` · 선례 `routes/project.py::delete_project` 와
    #      `d3_catalog.update_dataset`). 데이터셋 쓰기는 예외 없이 이 표에 남는다 —
    #      활동 한 줄(`d8_activity`)은 **이름·요약을 들지 않아** 「무엇이 지워졌는가」를
    #      말하지 못한다. 묘비 뒤에는 남는 상태가 없으므로 `after` 는 `None` 이다
    #      (같은 표에 적는 purge 경로 `d3_audit.append_deletion_snapshots` 와 같은 모양).
    #      ⚠ **트랜잭션 안이다** — 실패하면 예외가 그대로 올라가 전체가 롤백되고 500 이
    #      나간다(⑨ 와 같은 성질). 감사 없이 커밋되는 삭제를 만들지 않는다.
    d3_audit.append_snapshot(db, actor_id=subject.account_id, target_id=dataset_id,
                             action=AUDIT_ACTION_TOMBSTONED,
                             before={"name": core.name, "summary": core.summary},
                             after=None)

    # ⑧-c **미리보기 회수** (`DL-2`). 계약 산문 「파일과 **미리보기**만 지워져요」의 집행부다.
    previews = request.app.state.previews
    if previews is None:
        # 이름은 **본문과 `extra` 둘 다**에 싣는다 — 선례 `relay._record_suggest_failure`.
        # 구조화 로그를 안 읽는 배포에서도 grep 한 줄로 건수가 나와야 한다.
        _deletion_log.warning(
            "event=%s code=%s datasetId=%s", PREVIEWS_SKIPPED, PREVIEWS_UNCONFIGURED,
            str(dataset_id),
            extra={"event": PREVIEWS_SKIPPED, "code": PREVIEWS_UNCONFIGURED,
                   "datasetId": str(dataset_id)})
    else:
        try:
            result = previews.reclaim_previews(lab_id=str(subject.lab_id),
                                               account_id=str(subject.account_id),
                                               target_id=str(dataset_id),
                                               file_ids=file_ids)
        except RelayRefused as e:
            # **거절과 장애를 가른다**(선례 `app/relay._refuse_if_client_error`). 4xx 는 우리
            # 요청이 저쪽 계약에 안 맞는다는 뜻이라 **재시도가 무의미**하다 — 문구에 재시도를
            # 붙이지 않고, 고칠 단서(저쪽 상태·본문)를 `details.reason` 에 남긴다.
            # ⚠ **롤백은 ⓐ 와 같다** — 미리보기를 남긴 채 성공하는 자리를 만들지 않는다.
            raise errors.ApiError(500, PREVIEW_RECLAIM_FAILED,
                                  PREVIEW_RECLAIM_REFUSED_MESSAGE,
                                  {"reason": f"viz-render {e.status}: {e.body}"}) from None
        except RelayUnavailable as e:
            # **전체 롤백이다.** 미리보기를 남긴 채 204 를 내면 확인 창의 문구가 거짓이 된다.
            raise errors.ApiError(500, PREVIEW_RECLAIM_FAILED,
                                  PREVIEW_RECLAIM_UNAVAILABLE_MESSAGE,
                                  {"reason": str(e)}) from None
        # 계수는 남긴다 — 「지웠다」와 「지울 것이 없었다」를 나중에 가를 유일한 자리다.
        _deletion_log.info(
            "event=%s datasetId=%s stale=%s removed=%s", PREVIEWS_RECLAIMED,
            str(dataset_id), result.get("stale"), len(result.get("removed") or []),
            extra={"event": PREVIEWS_RECLAIMED, "datasetId": str(dataset_id),
                   "stale": result.get("stale"),
                   "removed": len(result.get("removed") or [])})

    storage = _storage(request)
    for key in keys:
        storage.discard(key=key)
    return Response(status_code=204)
