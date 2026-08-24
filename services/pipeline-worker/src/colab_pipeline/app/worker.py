"""워커 조립 루트 — 접수분 처리 · 릴레이 · reaper 를 돌린다. 도메인 판단은 여기 없다.

세 고리를 **한 프로세스 안에서 차례로** 돈다:
  ⓪ **처리** — 접수됐지만 아직 `ready` 가 아닌 업로드를 stage 1 파이프라인에 태운다(`〈73〉`)
  ① **릴레이** — outbox 의 미발행 이벤트를 내보내고 발행 시각을 찍는다(at-least-once)
  ② **reaper** — 만료된 미등록 업로드를 지운다(`〈64〉-ⓒ`). TTL 초과분 회수는 README 요구다

**⭑ `〈73〉` 이 뒤집은 것 — 「비동기 기계를 걷어내는 것이 아니라 켜는 것」이다.**
실측(`sessions/S1-upload-path-audit.md`)이 밝힌 것은 **기계가 애초에 배선돼 있지 않았다**는
사실이었다: `Dockerfile` 이 헬스 서버만 CMD 로 걸었고, `process_upload` 의 production
호출자가 **0건**이었다. 그래서 `ready` 가 영원히 false 였고 FE 가 1초마다 무한 폴링했다 —
**Ted 가 말한 「대기」의 실물은 가공 코드가 아니라 가공을 기다리는 형태였다.**
⓪ 이 그 자리를 메운다.

**stage 1 파이프라인 모양은 두 단계다** — 감지 → `file.format-detected` → `upload.ready`.
파싱·좌표·COG 는 stage 1 밖이다. **미리보기가 stage 1 로 돌아왔다는 사실이 이것을 바꾸지
않는다** — `〈74〉`·`〈75〉` 의 미리보기는 워커 파이프라인 안이 아니라 **화면 요청형**이고
그리는 것은 D7(viz-render)이다(`S1-PLAN-REFOUND §D.6`). 늘어난 것은 단계가 아니라
`ready` 의 판정 조건뿐이다(`〈79〉-⑷` — 격자 축이 확정되거나 거절됐다).

**발행 대상(큐·브로커)은 아직 고르지 않았다** — `〈61〉` 동결 계약은 봉투만 못박았고 전송
수단은 정본이 값을 주지 않았다(`[정본 무근거]`). 그래서 기본 발행자는 **표준 출력 한 줄**
이고, 실제 전송 수단이 정해지면 `publish` 를 갈아 끼운다. **원장에 남는 사실은 같다.**
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from ..domains.d5_ingestion import (
    IngestionService,
    SqlLedger,
    UploadFileWork,
    UploadWork,
    reap_expired_uploads,
    relay_unpublished,
)
from ..kernel import storage_layout
from ..kernel.db import apply_scope, make_engine, make_session_factory

ENV_DB = "COLAB_PIPELINE_DB_URL"
ENV_LAB = "COLAB_WORKER_LAB_ID"
ENV_ACCOUNT = "COLAB_WORKER_ACCOUNT_ID"
#: 접수한 바이트가 놓인 자리. **core-api 의 `COLAB_CORE_UPLOAD_DIR` 과 같은 곳**이어야 한다 —
#: 워커가 파일을 못 열면 감지가 통째로 실패하고, 그 실패는 「형식 인식 실패」로 위장한다.
ENV_UPLOAD_DIR = "COLAB_WORKER_UPLOAD_DIR"
#: 워커가 산출물을 두는 자리. stage 1 은 산출물을 만들지 않지만 `run_file` 이 stage 2 에서
#: 쓰므로 인자를 비워 두지 않는다.
ENV_WORKDIR = "COLAB_WORKER_WORKDIR"

#: 한 바퀴에 처리할 업로드 수의 상한. **없으면 한 바퀴가 얼마나 걸릴지 아무도 모른다.**
BATCH = 20


def stdout_publish(envelope: dict) -> None:
    print(json.dumps(envelope, ensure_ascii=False), flush=True)


def _storage_path(root: Path, upload_id: str, file_id: str, *,
                  kind: str = storage_layout.BODY_KIND,
                  file_name: str | None = None) -> Path:
    """접수한 바이트의 자리 — **규칙은 `kernel/storage_layout` 한 곳에만 있다.**

    ⚠ 예전에는 같은 규칙이 여기와 `core-api` 두 곳에 손으로 적혀 있었고, 이 주석이
    「갈라질 자리다」라고 경고하고 있었다. **실제로는 세 곳이었다** — `viz-render` 가
    또 다른 배치를 보고 있었고, 그래서 사람이 올린 격자가 렌더러에 영영 닿지 않았다
    (`03-HANDOFF §4 #20`). 저장 키를 이벤트에 싣지 않는 이유는 그것이 **배포 내부 사정**
    이라서다(`fe-core.yaml createUpload` 산문) — 그래서 계약이 아니라 **생성되는 규약**
    (`contracts/storage/layout.json`)으로 못 박았다.
    """
    return storage_layout.storage_path(root, upload_id, file_id=file_id, kind=kind,
                                       file_name=file_name)


def _named_view(blob: Path, holder: Path, file_name: str) -> Path:
    """저장된 바이트를 **원래 이름으로** 한 번 더 보이게 한다.

    ⚠ **왜 필요한가 — 저장 키에는 확장자가 없다.** `core-api` 의 `_storage_key` 는
    `uploads/{uploadId}/{fileId}` 이고 `fileId` 는 ULID 다. 그런데 축 판별 사다리
    (`d5/axis.py:174`)는 `.npy` 를 **접미사로 가른다** — 확장자가 없으면 격자를 통째로
    못 읽고, 그 실패는 **에러가 아니라 「축 미상」으로 조용히 나온다**(`DATA-REFERENCE §0` 무늬).

    이름을 되살리면 사다리 ④(파일명)도 정직하게 선다. **파일마다 제 디렉터리를 준다** —
    이름이 겹쳐도 덮어쓰지 않고, `basename` 만 쓰므로 경로 탈출이 성립하지 않는다.
    링크가 안 되는 파일시스템이면 복사한다 — 바이트는 같다.
    """
    safe = Path(file_name).name or blob.name
    holder.mkdir(parents=True, exist_ok=True)
    view = holder / safe
    if view.exists():
        return view
    try:
        view.symlink_to(blob.resolve())
    except (OSError, NotImplementedError):
        import shutil
        shutil.copyfile(blob, view)
    return view


def drive_uploads(ledger, *, upload_dir: Path, workdir: Path, limit: int = BATCH,
                  service=None) -> list[str]:
    """접수분을 stage 1 로 태운다. 돌려주는 것은 **처리한 업로드 id** 다.

    **한 건이 실패해도 나머지를 멈추지 않는다** — `process_upload` 는 실패를 예외가 아니라
    `upload.failed` 로 표현하고, 예외가 나는 것은 배관이 깨진 경우뿐이다. 그런 건은 이
    바퀴에서 건너뛰고 다음 바퀴가 다시 집는다(`ready` 가 아직 false 라 집합에 남아 있다).
    """
    service = service or IngestionService(ledger)
    done: list[str] = []
    for row in ledger.pending_uploads(limit=limit):
        upload_id = row["id"]
        files = []
        for ref in ledger.accepted_files(upload_id):
            file_id = ref.get("fileId")
            if not file_id:
                continue
            kind = ref.get("kind") or storage_layout.BODY_KIND
            name = ref.get("fileName") or file_id
            key = storage_layout.storage_key(upload_id, file_id=file_id, kind=kind,
                                             file_name=name)
            blob = _storage_path(upload_dir, upload_id, file_id, kind=kind, file_name=name)
            # **격자는 이미 제 이름으로 놓여 있다** — 배치가 이름을 보존하기 때문이다
            # (`layout.json`). 본체만 이름을 잃으므로 그쪽에만 이름 붙은 뷰를 만든다.
            path = blob if storage_layout.is_grid(kind) else _named_view(
                blob, workdir / upload_id / "inputs" / file_id, name)
            files.append(UploadFileWork(file_id=file_id, path=path, kind=kind,
                                        file_name=name, storage_key=key))
        if not files:
            # 접수 이벤트가 파일을 안 실었다 — 지어내지 않는다. 다음 바퀴가 다시 본다.
            continue
        service.process_upload(UploadWork(
            upload_id=upload_id, lab_id=row["lab_id"],
            actor_account_id=row["uploader_account_id"],
            workdir=workdir / upload_id, files=files), stage1=True)
        done.append(upload_id)
    return done


def run_once(*, publish=stdout_publish) -> tuple[list[str], int, list[str]]:
    """처리 1회 + 릴레이 1회 + reaper 1회.

    돌려주는 것은 (처리한 업로드, 내보낸 건수, 지운 업로드).
    **순서가 중요하다** — 처리가 먼저여야 그 바퀴에 생긴 이벤트가 같은 바퀴에 나간다.
    셋이 **한 트랜잭션**이라 반쪽이 남지 않는다.
    """
    url = os.environ.get(ENV_DB)
    if not url:
        raise RuntimeError(f"{ENV_DB} 가 없다 — 원장 없이 워커를 돌리지 않는다")
    lab, account = os.environ.get(ENV_LAB), os.environ.get(ENV_ACCOUNT)
    if not lab or not account:
        # 경계는 이벤트에도 실린다 — 큐에서 꺼낸 메시지에는 주체가 없다(envelope.json labId).
        raise RuntimeError(f"{ENV_LAB}·{ENV_ACCOUNT} 가 있어야 연구실 경계를 세운다")
    upload_dir = os.environ.get(ENV_UPLOAD_DIR)
    if not upload_dir:
        # 바이트를 못 여는 워커는 **감지를 못 하면서 「형식 인식 실패」를 낸다** —
        # 없는 것을 있는 척하지 않고 뜨지 않는 쪽을 고른다 (core-api 의 업로드 저장처와 같은 규칙).
        raise RuntimeError(f"{ENV_UPLOAD_DIR} 가 없다 — 접수한 바이트를 못 여는 워커는 안 돈다")
    workdir = Path(os.environ.get(ENV_WORKDIR) or (Path(upload_dir) / "_work"))

    engine = make_engine(url)
    factory = make_session_factory(engine)
    session = factory()
    try:
        session.begin()
        apply_scope(session, lab_id=lab, account_id=account)
        ledger = SqlLedger(session)
        processed = drive_uploads(ledger, upload_dir=Path(upload_dir), workdir=workdir)
        sent = relay_unpublished(ledger, publish=publish)
        reaped = reap_expired_uploads(ledger)
        session.commit()
        return processed, sent, reaped
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def serve(interval_seconds: float = 5.0) -> None:  # pragma: no cover - 배관
    while True:
        run_once()
        time.sleep(interval_seconds)


def main() -> None:  # pragma: no cover - 배관
    """**헬스 서버와 워커 루프를 한 프로세스에서 함께 돈다** (`〈73〉` 배선 ①).

    이전 `Dockerfile` 은 헬스 서버만 CMD 로 걸었고, 그래서 이 단위는 **살아 있다고 대답만
    하고 아무것도 하지 않았다.** 헬스를 버리고 루프만 걸면 오케스트레이터가 이 컨테이너의
    생사를 못 보므로, 둘 다 돈다 — 헬스는 데몬 스레드, 루프는 본 스레드다.
    **루프가 죽으면 프로세스가 죽는다**(restart 정책이 집는다). 조용히 멈춘 워커가
    「healthy」로 보이는 상태를 만들지 않는다.
    """
    from .health import serve as serve_health

    threading.Thread(target=serve_health, daemon=True, name="healthz").start()
    serve()


if __name__ == "__main__":  # pragma: no cover - 배관
    main()
