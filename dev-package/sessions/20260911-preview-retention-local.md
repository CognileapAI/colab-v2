# BF-12 dev S3 관측 경로 — 로컬 구현

## 판정

- BF-12는 여전히 open이다. 완료 정의의 dev 배포와 첫 주기 실로그가 남았다.
- TL-2는 착수하지 않았다. BF-12가 닫힌 뒤에만 시작한다는 선행을 유지했다.
- 실제 S3 객체 삭제, dev 배포, main push는 0건이다.

## 발견과 구현

- dev compose에는 pipeline-worker 이벤트 발행 스풀과 viz-render 구독 스풀이 모두 없었다. 따라서 BF-12 로깅 코드가 있어도 회수 루프는 서지 않았다.
- dev는 source와 preview가 S3인데 기존 ReclaimJob은 로컬 디렉터리만 읽었다. 스풀만 연결하면 주체 0의 준비 실패가 나므로 유효 계수로 세지 않았다.
- S3ReclaimJob을 관측 전용으로 추가했다. uploads/와 previews/만 목록으로 읽고, 대상별 바이트를 S3SourcePort로 materialize한 즉시 SHA-256 기반 후보 키를 계산한다.
- ETag는 다운로드 캐시 판본에만 쓰고 생존 키 재료로 쓰지 않는다. 전체 입력이 workdir 상한을 넘거나 목록·Head·GET·크기 대조가 실패하면 판정을 시작하지 않는다.
- apply 요청 여부와 무관하게 S3 DeleteObjects 호출 경로는 없다. 결과는 항상 삭제 0이다.
- dev compose에 events named volume, uid 10001 초기화, pipeline/viz 양쪽 쓰기 마운트와 동일 스풀 경로를 추가했다.

## TDD와 검증

- RED: 신규 7건 전부 실패 — S3 관측 함수·job·조립 함수 부재 5, dev 스풀/volume 부재 2.
- GREEN: 신규 8건 통과(총량 상한 음성 시험 포함).
- 회수·liveness·S3 source·앱 로깅 관련 묶음 67건 통과.
- service-tests-viz-render: 395 passed, skipped 0, failed/errors 0, 13.8초.
- service-tests-pipeline-worker: 269 passed, skipped 0, failed/errors 0, 6.6초.
- generated-up-to-date: 등기부 13/13, 자칭 생성물 0.
- import-boundary: 8 kept, 0 broken. db-boundary: 단위 7, 대상 370, 위반 0.
- dummy 비밀값으로 docker compose config --quiet 성공. 실제 자격증명·원격 연결은 사용하지 않았다.

## 다음 경계

정확한 SHA와 이미지·롤백 자료를 만든 뒤 dev 배포 직전 사용자 승인을 받는다. 배포 후 8/8 healthy와 첫 주기 로그의 주체/타일/닿음/못 닿음/삭제 0/비밀 0이 모두 확인돼야 BF-12를 닫는다.
