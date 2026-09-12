"""D3 조립 — **데이터셋 삭제(묘비)** 두 op (`DL-1`).

정본은 계약 산문 하나다 (`contracts/seams/fe-core.yaml`) —

  `deleteDataset`            「**소유자 또는 교수만.** 파일·미리보기만 지우고 이름·주제·Lv·
                             계보 관계·프로젝트 연결·Verified 는 남긴다. 되돌리는 전이가 없다.
                             대기 중인 접근 요청은 자동으로 닫힌다 (§9).」
  `getDatasetDeletionImpact` 확인 모달이 말해야 하는 파급 세 칸.

**왜 새 파일인가.** 삭제는 D3(카탈로그)·D2(접근·승인)·D4(계보) 셋의 사실을 한 자리에서
조립한다. `catalog.py` 에 얹으면 그 파일이 조회와 파괴를 함께 들고, 두 레인이 같은 파일에서
만난다. 조립 루트가 도메인 함수를 부르는 무늬는 `routes/access.py` 와 같다.

**⛔ 미리보기는 이 회차가 지우지 않는다.** 계약 산문의 「파일·**미리보기**만 지우고」와의
차이이고, 형제 항목 `DL-2` 가 닫는다(`core-viz.yaml` `reclaimPreviews` · viz 회수 계획).
여기에 릴레이 한 줄을 미리 넣지 않는다 — 실현 안 되는 호출을 남기면 다음 사람이 그것을
「이미 되는 것」으로 읽는다.

**판정 순서는 400 → 404 → 403 이다** (`routes/access.py::_decidable_request` 독스트링 ·
`routes/ingestion.py::_file_target`). 권한을 먼저 보면 남의 연구실 식별자에 403 이 나가고
그 403 이 「그 식별자는 있다」를 알린다 (P-9·P-10).

**계약에 410 이 없다.** 그래서 묘비도 404 다 — 경계 밖·무존재와 **본문까지 같다.** 두 번째
DELETE 도 404 이고, 화면은 묘비면 상세 자체가 410 화면이라 버튼이 서지 않는다.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from ...domains import d2_access, d3_audit, d3_catalog, d4_lineage, d8_insight
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db
from .ingestion import _storage

router = APIRouter(tags=["catalog"])

#: 대기 접근 요청이 자동으로 닫힐 때 남는 사유. **`[정본 무근거]`** — 정본은 「닫힌다」라는
#: 동작만 적었고 문장을 주지 않았다 (Ted 판정 ⓕ). 상태 집합에 「닫힘」이 없어
#: `거절됨` 으로 닫으므로, 요청자에게는 이 문장이 **왜 닫혔는지**를 말하는 유일한 자리다.
ACCESS_REQUEST_CLOSED_REASON = "데이터가 지워져서 요청이 닫혔어요."

#: 운영자 감사 행위 문자열. **레포에 이미 있는 값을 다시 쓴다** —
#: `d3_audit.append_deletion_snapshots`(purge 경로)가 같은 표 `d3_operator_audit` 에
#: 같은 이름으로 적는다. 두 삭제 경로가 다른 문자열을 쓰면 감사 질의가 한쪽을 놓친다.
AUDIT_ACTION_DELETED = "dataset.deleted"

#: 권한 거절 문구 — 정본 조항을 괄호에 달아 「어느 규칙이 막았는가」를 사람이 되짚게 한다.
FORBIDDEN_MESSAGE = "데이터셋 삭제는 소유자 또는 교수만 할 수 있다 (Policy_데이터셋_상세 §6)."


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
    keys = [f["storage_key"] for f in d3_catalog.files_for_download(db, dataset_id)]

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
                             action=AUDIT_ACTION_DELETED,
                             before={"name": core.name, "summary": core.summary},
                             after=None)

    storage = _storage(request)
    for key in keys:
        storage.discard(key=key)
    return Response(status_code=204)
