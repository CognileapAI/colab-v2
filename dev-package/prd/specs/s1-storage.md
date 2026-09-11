# S3 미등록 업로드 회수와 완료 전송 메타 보관

출처: `stage1-stage2-closeout.md`, `dev-package/sessions/20260910-stage12-decisions.md` Q2·Q7. U-2는 배포·실제 삭제 승인 전 완료 처리하지 않는다.

## 범위·소유

- core app의 유지보수 함수가 D5 후보·D2 가시성·D3 소유 Port와 S3 회수 Port를 조립한다. pipeline은 D5 소유이며 D2/D3 조회를 복제하지 않는다.
- pipeline `SqlLedger.expire`와 core의 미사용 `UploadLedgerAdapter.reap_expired` 원장 선삭제 경로를 관측·보존으로 전환한다. core 경로는 현재 제품 호출 0이며 잠재 재연결 회귀만 방지한다.
- 신규 회수는 `observe` 기본. `apply` 명시 시만 객체·원장 변경. 설정은 배포 시의 안전 스위치이며 이번에 운영 설정을 변경하지 않는다.
- 기존 미완료 transfer 정리와 신규 완료 transfer 메타 prune은 구분한다. 완료 transfer는 completed_at 이후 7일 경과 시 회수 가능하며 S3 삭제 대상에 포함하지 않는다.

## 정확한 회수 조건

1. 연구실 스코프와 REPEATABLE READ 읽기/쓰기 트랜잭션을 먼저 고정한다.
2. D5 만료·미등록·비처리중 후보를 FOR UPDATE SKIP LOCKED로 잠근다. 등록의 mark_registered UPDATE보다 먼저 잠근 경우 등록은 기다렸다가 원장 소멸을 확인한다. 등록이 선행하면 후보에서 제외한다.
3. upload.accepted의 본체·기준격자 FileRef 전건이 있어야 한다. 유효 ID·종류·이름·규약 키와 D5 실원장 키의 정합을 검사한다. 축 미확정 격자도 사건의 규약키로 포함한다. 이벤트 부재·빈목록·중복/상이한 소유·열린 transfer는 보존한다.
4. D3 dataset은 연구실 경계 RLS만, d3_file은 body_access 추가 제한이다(`db/platform/schema.sql`). D2 Port가 모든 scoped dataset의 현행 body_access 조건을 확인하고 하나라도 불허면 unknown이다. file_count는 전 종류 d3_file INSERT/DELETE/MOVE 증분 트리거이며 dataset별 COUNT 대조는 보조 방어만 한다. 같은 snapshot에서 D3 targetID/fileID/exact key 충돌을 확인한다.
5. 소유 Port 부재·실패·unknown이면 객체와 원장을 보존한다. 다른 연구실 소유 부재까지 증명했다고 확대하지 않는다. 기존 uploadId 키 규약은 lab prefix가 아니므로 무근거 lab prefix를 새로 가정하지 않는다.
6. S3 exact-key 삭제 전 목록을 고정한다. 버킷 목록 조회 금지. 부분 실패 시 원장을 보존하고 재시도한다. 성공 후 원장을 삭제하고 동일 트랜잭션 commit까지 후보 잠금 유지. DB rollback 시 S3는 되돌릴 수 없으므로 없는 키 재삭제 멱등으로 다음 회수에서 정리한다.
7. local 원본은 core storage 소유지만 이번 S3 회수 범위 밖이다. local noop를 성공으로 세어 원장을 지우지 않는다.

## 메타 보관·운영 경계

- 완료 transfer와 transfer_file 메타만 7일 기준 prune. d5_upload/d5_upload_file/d3_dataset/d3_file·원본 객체 불변.
- 진입은 기존 S3 initiate/list 요청의 유지보수 호출. 요청이 없으면 7일보다 더 오래 남을 수 있다. cron 설치·외부 운영 호출은 하지 않는다.
- 보고 계수: 후보·삭제 업로드·완료 메타 삭제·보존 사유. 대상 0과 mode observe를 명시한다.
- 실제 S3 삭제·main push·배포는 구체적인 대상·SHA를 제시한 뒤 별도 승인.

## 검증

- 실DB: 등록 선행/회수 선행 경쟁, 열린 transfer, event 없음/빈목록, axis 미확정 grid, exact key mismatch, D3 소유 충돌, 비공개 dataset(파일 0 포함), 가시성 정책·dataset별 계수 불일치, S3 부분 실패·DB rollback 재시도, scope없음, 기본observe, completed_at 7일 경계.
- S3 HTTP 전송 대역만 사용하며 emulator/운영 S3 호출 없음. 실제 AWS 검증은 이번 실행 범위 밖으로 명시한다.
- core/pipeline 서비스 게이트와 import/db 경계 게이트. pipeline dbint는 기본 서비스 게이트 제외이므로 별도 일회용 DB 러너에서 실행·계수 기록한다.
