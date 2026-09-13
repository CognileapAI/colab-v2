# AI 검색 증분 갱신 — 변경 기록 계약

출처: [AI 검색 intent](../../intent/2026-09-12-ai-search.md).
2026-09-13 사용자 일일 온톨로지/KG 갱신 요구와 후속 “좋아”에 따라 단계 ①을 실행한다.

## 전체 순서

1. 원본 변경 기록·처리 버전·실패 재시도 (이번 구현).
2. 자료별 KG와 출처·파일 revision 연결. 연구실 및 본체 권한 적용.
3. 일일 증분 실행·검증 후 버전 공개·검색 캐시. 실패 시 이전 공개본 유지.
4. 온톨로지 개념과 복합 조건을 결합한 검색.
5. 의미 검색·제한된 Sonnet 해석/재정렬·골든셋 평가. 실제 모델 평가는 기존 보류 유지.

## 단계 ① 수용 기준

- `d3_search_change`는 metadata(dataset ID), file(file ID), evidence(file ID)별 최신 dirty generation을 병합한다.
  감사 이벤트 전체 이력이 아니다. 미러 트리거 때문에 한 사용자 수정이 여러 generation을 만들 수 있다.
- D3 dataset/description/autometa/variable/grid_profile/file/search_evidence의 INSERT/UPDATE/DELETE와
  같은 트랜잭션의 커밋 직전에 기록한다(deferred constraint trigger). 중간 SELECT에는 아직 안 보일 수 있다.
  원본 쓰기를 마친 뒤 큐를 잠가 summary/source_label 잠금 역전을 피한다. 원본 rollback이면 기록도 rollback한다.
- 파일/자료 FK cascade로 기록을 지우지 않는다. 삭제 포인터는 남긴다. 자식 메타 삭제는 부모 자료 삭제와 구분한다.
- 큐에는 ID·버전·시간·처리 상태만 저장한다. 본문/이름/저장 경로/임의 오류 메시지는 저장하지 않는다.
- 연구실 FORCE RLS를 적용한다. 내부 Python 소비 인터페이스만 제공하며 사용자 HTTP API는 없다.
  포인터 접근은 본체 접근 승인이 아니다. 후속 소비자는 원본 권한과 삭제 여부를 다시 판정해야 한다.
- claim은 제한된 묶음을 SKIP LOCKED로 선점하고 버전과 lease generation을 고정한다.
  ack/fail/renew는 같은 연구실·키·generation·captured version·미만료 lease에만 유효하다.
  처리 중 새 변경이 생기면 ack는 당시 버전까지만 완료한다. 만료된 작업자는 상태를 변경할 수 없다.
- 실패는 제한된 오류 코드와 재시도 시각을 남긴다. 재시도는 최신 버전을 처리하며 변경 없는 완료 행은 다시 선점하지 않는다.
- bootstrap은 호출 계정이 볼 수 있는 기존 원본의 ID만 페이지 단위로 읽고 미등록 포인터만 생성한다.
  이미 기록된 처리/대기 상태를 초기화하지 않는다. 전체 본문 읽기나 배포 시 자동 실행은 없다.
- 파일 변경은 후속 단계에서 파일 색인과 해당 파일 근거의 유효성을 함께 재검토해야 한다.
  자료 삭제/권한 회수는 검색에서 원본 권한 판정으로 즉시 차단해야 하며 일일 주기를 기다리지 않는다.

## 경계

이번에는 KG 결과 저장·외부 작업자·스케줄러·LLM 호출·공개 버전 전환을 구현하지 않는다.
lease가 외부 결과 쓰기의 exactly-once를 보장한다고 주장하지 않는다. 후속 결과 쓰기에도 fencing이 필요하다.
온톨로지 보호와 배포 정책은 유지하며 이 브랜치에서 변경하지 않는다. 제품 데이터에 bootstrap을 실행하지 않는다.

## 검증

일회용 PostgreSQL에서 등록/변경/삭제/rollback, 병합, 동시 선점, 처리 중 변경,
만료/reclaim/재시도, 타 연구실 차단, bootstrap 멱등성을 검증한다.
core 전체 회귀와 migration-single-head/schema-diff/rls-coverage/rls-effect/import-boundary 게이트를 실행한다.
