> spec: dev-package/prd/specs/knowledge-lifecycle.md
# Knowledge Lifecycle Implementation Plan

> **For agentic workers:** 기본 직렬 1레인. 승인된 구현은 `executing-plans`로 실행하며, 병렬 쓰기는 격리 사본이 확보된 경우에만 허용한다. 현재는 로컬 구현 단계다.

**Goal:** 지속 업로드의 사실·개념 연결을 독립 실행으로 축적하고, 검토된 온톨로지 변화가 검색에 안전하게 반영되도록 한다.

**Architecture:** D3/D4 원장과 D9 지식 정본을 유지한다. 기존 변경 큐·독립 runner를 재사용하고 D3 검색 projection은 지식 정본의 버전 있는 조회 모델로 취급한다.

**Tech Stack:** 기존 Python 서비스·PostgreSQL·Port·HTTP 계약·pytest. 새 그래프 DB·브로커·클라우드 실행기를 선택하지 않는다.

**Spec:** [개발 스펙](../specs/knowledge-lifecycle.md)

## Global Constraints
- 2026-09-15 사용자 "그럼 이제 해"로 로컬 구현·검증에 착수했다. 배포·유료 모델 실행은 여전히 별도 승인이다.
- 다른 도메인 SQL/FK 금지, D10 계보 확정 쓰기 금지, platform/AI migration 체인 분리, core-api geo import 금지.
- 삭제·권한 취소는 현재 원장으로 즉시 집행한다. 배치 성공을 권한 근거로 삼지 않는다.
- Sonnet 실제 평가 보류 유지. 결정적 시험·모델 stub 통과로 실제 LLM 품질을 주장하지 않는다.
- commit·push·PR 게시·통합·배포·재시드는 이 계획의 자동 단계가 아니다.
- 의도: [승인 intent](../../intent/2026-09-15-knowledge-lifecycle.md). ADR: [경계](../../../docs/decisions/0001-knowledge-lifecycle-boundaries.md), [실행](../../../docs/decisions/0002-knowledge-refresh-execution.md).

## 현재 상태와 의존
- [x] 의도 승인 및 기존 코드의 재사용/공백 구분.
- [x] spec·ADR·실행 단계 초안 작성.
- [x] 설계 방향 및 시험 방법 구체화 승인(2026-09-15 사용자 "그래 그러자").
- [x] [계약 상세안](../specs/knowledge-lifecycle-contract.md): 권한·Port·generation·receipt·검토 절차·14개 수용 시나리오 문서화.
- [ ] 새 D9 반영/검토 계약과 권한 모델 동결.
- [ ] 제품 구현·회귀·실제 사용자 여정 검증.
- [ ] 모델 평가 및 운영 배치 승인(별도 경로).

계약 → source/KG/projection 수명주기 → 증분 실행 → 제안·release → 외부 여정 검증 순서다.
현재 아래 파일 후보와 시험 이름은 구현자가 따라갈 설계 제안이지 이미 존재하는 API/테스트 선언이 아니다.
Port signature와 행위 규칙은 계약 상세안을 따른다. Task 1에서 wire schema·생성 소비자·음성 시험을 구현하고 검증한 뒤 Task 2 이후의 실행 세부안을 갱신한다.
따라서 이 문서는 단계별 구현 계획 초안이며, 지금 바로 실행 가능한 계약 동결본이라고 주장하지 않는다.

## Task 1: 소유권·반영 계약을 동결한다
진행: DTO/validation 하위 단계 구현. source authority·권한 adapter가 미구현이므로 전체 계약 동결은 아직 아님.
- [x] 공통 ID와 기존 evidence predicate를 참조하는 JSON Schema 및 양 서비스 동일 생성 DTO.
- [x] RED 후 타입·버전·추가 필드·근거 참조·개념 ID 제한 검증. 부모 재측정: Python 29건, JSON Schema AJV 2건 통과.
- [x] CI 생성기 Python 준비 및 schema 시험 연결. 준비 없는 일회용 사본에서 generator exit127 → 준비 후 exit0 확인.
- [x] DTO 증분 검증: core 1447pass/0skip/6deselected(직렬), AI 194pass/0skip/27deselected, lint3, breaking3, generated19. 근거는 이번 부모 실행의 로컬 임시 로그이며 영구 저장소 근거가 아니다. core 이후 생성 타입의 동일 제한을 local alias로 정리했으므로 전체 최종 tree 검증은 후속 구현 뒤 다시 수행한다.
- 이전 core 실행은 1446pass/1fail. 보고서 분할을 오판한 테스트를 실제 조각 일치+복원 검증으로 보완했다. 과거 실패는 삭제하지 않는다.
**Files:**
- Review: `dev-package/DOMAINS.md`, `contracts/`, `services/core-api/src/colab_core/ports/ontology.py`
- Modify on approval: `dev-package/prd/specs/knowledge-lifecycle.md`, 위 ADR 2개, 이 계획
- Create on approval: `contracts/schemas/knowledge-lifecycle.json`
- Test on implementation: `services/ai-service/tests/test_knowledge_contract.py`

**Interfaces:** source identity·processing identity·scoped principal·replace/invalidate command → 버전 검증된 KG receipt. 논리 필드는 spec 계약 절을 따르며 wire는 이 작업에서 확정한다.

- [ ] 기존 ontology wire·서비스 인증·D9 읽기 소비자를 조사하고 새 쓰기 권한을 기존 조회 토큰에 추가하지 않는 설계를 고정한다.
- [ ] 자료 최신 상태·tombstone의 D3→D9 검증 계약, 승인자의 권한 검증, receipt issuer와 버전 호환 규칙을 정확한 schema로 작성한다.
- [ ] 개별 제안의 조회·검토·승인·거절을 수행할 운영 진입점과 인증·감사 기록을 동결한다. 새 UI 없이 승인자가 실제 수행 가능한지 확인한다.
- [ ] cross-lab 명령·누락 source revision·위조 receipt·기존 read token write를 거절하는 계약 시험을 작성한다.
- [ ] 시험 RED를 측정한 뒤 최소 validator를 구현하고 GREEN을 확인한다. 계약 동결 전 후속 endpoint 구현은 차단한다.
- [ ] 기존 공개 계약 diff를 확인하고 파괴 변경이 있으면 별도 승인을 받는다.

Run (구현 시): `bash gates/run.sh contract-lint`, 이어서 `bash gates/run.sh contract-breaking`.
증명: 유효 command/receipt 왕복, 잘못된 권한·버전 입력 거절. schema 0건/시험 0건을 성공으로 처리하지 않는다.

## Task 2: 원본 근거와 D9 자료 지식의 수명주기를 연결한다
진행: D3 영속 source authority부터 구현. 현 증분은 reviewed evidence를 서버가 직접 정규화하고 mappings=[]로 제한한다. 승인된 매핑 원장과 tombstone 전용 권한은 후속 연결 대상이며 임의 데이터로 대체하지 않는다.
- [x] 내부 source authority 증분: 영속 generation·hash-only grant·canonical facts, 현재 source/manifest/계정 검증. HTTP 인증 경로는 아직 없음.
- [x] 독립 검토의 session 조회 경합을 실제 credential DB로 RED 재현 후 반환 identity/version 대조로 수정. private 접근 취소·직접 RLS 조회·source 수정 경합도 확인.
- 작업자 실측: 개별 DB 시험14pass, core 전체 직렬1461pass/0fail/0skip/6deselected. 부모는 코드와 summary exit0을 확인했다. task runtime 미등록인 로컬 증거이며 정식 lifecycle 완료가 아니다. 최종 tree 전체 재검증은 남아 있다.
- 다음 내부 저장 증분: 별도 `knowledge` schema의 source fence·facts/mappings·receipt, 고정 주입 authority 검증 후 source 전체 key로 SET LOCAL/RLS. 기존 공용 ontology와 D10 read role에 writer 권한을 더하지 않는다.
- D9 일반 reader·HTTP·invalidate는 조회 권한 및 tombstone 전용 authority 구현 전 동결하지 않는다. 별도 실행 entrypoint/설정으로 writer credential을 D10 프로세스와 분리한다.
- [x] 내부 D9 replace 증분: 별도 knowledge schema, 전체 source key RLS, canonical ULID, generation/receipt 멱등 저장, D9 자체 manifest 재검증. 기존 read role은 KG 접근 불가, 시험용 writer는 공용 5표 SELECT만 허용한다.
- [x] AI DB 시험을 기본 게이트에 포함하고 xdist별 일회용 DB로 격리. 중첩 persistent mount 거절과 SQLSTATE별 권한 음성 시험을 보완했다. 부모 직접 직렬 실행 244pass/0skip/0deselected.
- Task2b runtime `9e93ce5312bd43a5847737e912556010`, 최종 run `fb82c2f98f314ead92ea696f78aafcf9`: 선언9gate green/판정0/준비0. 부모가 9gate와 당시 파일 hash를 직접 verify-report로 확인. 이전7green/2red·8green/1red 회차는 보존했다. 후속 수정 뒤에는 다시 검증한다.
- 다음 HTTP 증분: 고정 source callback의 tracked session 검증 → 별도 D9 knowledge entrypoint replace 왕복. principal claim·token 혼용·logout·private·callback 장애 음성 시험을 먼저 작성한다. reader/tombstone·무인 job delegation은 별도 후속 단계다.
- [x] Task2c HTTP 증분: 실제 tracked session과 전용 callback 인증, 별도 knowledge ASGI, principal 전체 대조, bounded fixed callback, logout/private 거절. 부모 직접 재측정 core HTTP+실제 두 서비스 왕복17pass, AI HTTP19pass. 로그인 화면 E2E가 아닌 정상 발급 세션 이후의 왕복 시험이다.
- Task2c runtime `7d8b0c58bf2948f38a630c513ee4fd9d`, run `37429e625e8244569520debc1f50c9b3`: 선언9gate green/판정0/준비0, core1478pass/skip0/deselect6·AI263pass/skip0/deselect0(JOBS1). 부모가 전체9gate·당시 파일 hash를 verify-report로 확인했고 advisor 수용 검토 clean. 별도 contract-selftest20·db-boundary-selftest22는 묶음에 합산하지 않는다. 이후 수정은 이 실행의 검증 범위 밖이다.
- 다음 reader 증분: 발급자 grant와 무관한 현재 viewer 권한·source/fence/canonical digest 검증 → D9 자체 current receipt·manifest 재대조 → payload 반환. 읽기는 grant 발급/generation 증가를 하지 않는다. 기존 factory의 READ ONLY 트랜잭션을 재사용하되 DB credential 격리로 주장하지 않는다. projection·tombstone은 이후 연결한다.
- [x] Task2d reader 증분: 현재 viewer·canonical digest·현재 receipt/release 및 grant 없는 payload 정합 검증. 부모 직접 core 관련39pass, AI 전체285pass/skip0/deselect0. 별도 reader API 권한과 실제 READ ONLY를 구현했으며 DB 자격 격리는 아니다.
- Task2d runtime `55c13ce5f1b04013a30af983303186eb`, run `0be0a1203b254ca5a23760bcbdfba77c`: 선언8gate green/판정0/준비0, core1486pass/skip0/deselect6·AI285pass/skip0/deselect0(JOBS1). 부모 verify-report로 전체8gate·당시 파일 hash를 확인했고 advisor clean. 이후 변경은 별도 검증한다.
- 다음 tombstone 증분: private command와 분리한 body-free 영속 generation fence, 정확한 evidence 삭제 revision, 고정 lab의 삭제 전용 API capability를 연결한다. 원본 hash·ontology 없는 별도 삭제 DTO/receipt로 처음 삭제도 fence를 남긴다. 기존 SQL factory 재사용은 API 권한 분리이며 DB 자격 격리가 아니다.
- 삭제 소유 경로 실물: 파일 실제 DELETE 및 dataset tombstone 후 파일 DELETE가 evidence CASCADE/deferred change trigger로 연결된다. 현재 제품 soft-file restore API는 없다. evidence 재삽입의 높은 revision과 과거 삭제 거절을 검증하되 제품 복원 기능 구현으로 보고하지 않는다.
- [x] Task2e 삭제 증분: body-free fence/삭제 grant, 별도 삭제 DTO/receipt, 고정 lab 삭제 API 및 명시 활성/비활성 설정. 첫 삭제·중복·역순·로그아웃·ontology 장애·invalidated 조회 거절을 구현했다. 부모 직접 core 관련54pass, AI 전체304pass/skip0/deselect0. 숨긴 행 이관도 관련 시험에 포함된다.
- Task2e runtime `6e9a18e710d94fa8a1d661bf663468a2`, run `954c854a82124254b902da643f921740`: 선언11gate green/판정0/준비0, core1500pass/skip0/deselect6·AI304pass/skip0/deselect0(JOBS1), platform0038/AI0008 단일 head 및 schema drift0. 부모 verify-report로 전체11gate·당시 파일 hash를 확인했고 advisor clean. 사용량 제한으로 한 차례 중단 후 같은 task/baseline으로 재개한 이력을 유지한다.
- 다음 projection 증분: 고정 D9 reader client → 현재 세션/원본/fence/release 검증 → 기존 fact snapshot 처리와 새 receipt ledger/queue ack를 같은 D3 트랜잭션에 반영. mappings=[]만 지원하며 nonempty를 기존 literal annotation으로 위장하지 않는다. 현재 조건 검색은 원본 evidence를 직접 소비하므로 이 증분을 검색 품질 개선으로 보고하지 않는다.
- 멱등 상태 조회와 작업 완료를 구분한다. 같은 receipt/snapshot이 유효하고 queue도 이미 완료된 경우만 무변경 already_applied다. 재queue/pending/새 lease가 있으면 현재 claim을 검증해 처리한다. 기존 facts.process가 ack하므로 이중 ack하지 않는다. 네트워크 동안 mutex/DB lock을 잡지 않는다.
- [x] Task2f projection 증분: 독립 `KnowledgeProjector`, 현재 viewer 재인증, source/fence/release/fact 집합 재검증, snapshot/ack/receipt ledger의 원자적 저장. snapshot 삭제 후에도 sequence를 보존한다. 기존 SearchRefreshTools wrapper·자동 worker 연결은 변경하지 않았다.
- Task2f runtime `a356304b261f4128b09c2d5916e4aefc`, run `5bcc79ac3d0f4cce90ba64d40b224805`: 선언9gate green/판정0/준비0, core1553pass/skip0/deselect6·AI304pass/skip0/deselect0(JOBS1), platform0039/AI0008 단일 head 및 양 schema drift0. 부모 직접 관련88pass(40.32초), 전체9gate verify-report 및 당시 hash `5581bbbd40dfeeac609102b8b1e0e8c11ad63b3b00735ecb20b9d5ce0977d496` 확인, advisor clean과 lifecycle 인계 완료. 이후 문서·제품 수정은 이 실행의 범위 밖이다.
- 통신 deadline의 본문 stall·헤더 trickle 결함을 RED로 재현했다. 고정 stdlib child에 stdin으로 요청을 전달하고 부모의 제한된 nonblocking IPC·timeout kill/reap으로 보완했다. 정확히 N초 반환이 아니라 deadline 초과 후 중단 및 OS 정리 시간이 추가된다. 호출별 시작 비용은 후속 처리량 평가 대상이다. 상속 applied DB 주소의 예비 schema 연결 실패(exit1)와 시험 실패 이력을 성공에 합산하지 않는다.
- O1 근거 경계: D3 autometa에는 사람 수정이 섞이고 D5 기존 header event는 첫 성공 파일의 집계값이다. 이를 file_measurement로 승격하지 않는다. D4 변경 추적은 아래 retained revision 증분에서 연결한다. 앞선 revision/outbox 후보는 최신 상태 수렴에 필요한 단일 revision 표로 구체화했다.

### 파일별 측정 근거: 구현·검증된 증분
- 승인된 최소 범위는 측정 → 등록 bytes 검증 → file source grant → D9 → typed projection이다. mappings는 비어 있고 실제 조건 검색 소비·개념 매핑·자동 worker는 후속이다.
- D5 처리마다 소유 snapshot을 만들어 동일 bytes로 magic/hash/parse/변환한다. digest는 tile key와 재사용하고 parse 직후 원본 측정값을 후처리 CRS와 분리한다. 공유 local symlink/S3 cache를 불변 입력으로 가정하지 않는다. 기존 S3 expected_etag 조건부 읽기를 사용하며 ETag를 SHA로 취급하지 않는다.
- D5 immutable receipt와 최종 bytes를 대조한다. 측정 receipt가 있는 등록은 `prepare_registration`으로 목적지를 복사·검증하고 원본을 보존한다. local은 hardlink가 아닌 copy, S3는 조건부 copy 및 최종 SHA 확인이다. 알려진 receipt와 digest 불일치는 등록 실패이며 조용히 binding만 생략하지 않는다. receipt 없는 기존 경로는 유지한다.
- 등록 전용 `Depends(scope="function")`이 root DB commit을 응답보다 먼저 끝낸 뒤 원본을 정리한다. local identity/S3 If-Match로 정리 대상 교체를 검사한다. rollback 시 원본 보존, commit 불확실 시 orphan 보존, commit 후 cleanup 실패 시 경고를 남기고 등록 성공 유지다. 분산 원자성·자동 orphan 회수·POSIX unlink 경합 완전 차단은 보장하지 않는다.
- 등록 transaction에서 필요한 bounded receipt snapshot(ID·발급 provenance·parser version·digest/size·측정값)만 D3 fileID/content_revision/storage identity에 결합한다. caller 제공 receipt·비밀·임시 경로·원문은 저장하지 않는다. 이후 합법 viewer는 D3 권한과 현재 binding으로 조회한다. 정정: 앞선 upload-owner RLS 표현은 부정확했다. D5 RLS는 lab-only이며 업로더 제한은 Port/app 계층이다. D5 정정/철회는 별도 invalidation이 필요하다.
- magic 감지와 parse 성공이 모두 확인된 format `NumPy→npy`, `NetCDF→netcdf`, `GeoTIFF→tif`, `HDF5→hdf5`만 `file_measurement`로 승격한다. CRS·datetime 기간·변수 이름·grid shape·autometa에서 의미/해상도/관측 여부를 추론하지 않는다.
- 기존 file_name/kind snapshot과 측정 loader·extractor/type을 구분한다. source/grant/fence/deletion/projection의 file 지원은 새 migration과 현재 권한 검사로 연결하고 기존 evidence 경로를 보존한다. supported replace·삭제 후 binding/grant/projection stale을 검증한다. 원장 밖 임의 storage 덮어쓰기 탐지는 보장하지 않는다.
- 소유 범위: pipeline D5/원장/입력 snapshot, core D5 Port·등록/storage·D3 측정 및 source/projection, platform 신규 migration/schema, 관련 시험. strict 집계 이벤트와 D9 wire는 재사용한다. 기존 pipeline 기본 게이트에 일회용 DB와 `not e2e` selector를 제공해 dbint도 포함하고 준비 실패78/0건 실패를 자체시험으로 보존한다.
- 먼저 실패시킬 시험: 다중 파일 혼합·동일 크기 다른 bytes·측정 후 교체·늦은 binding·S3 조건부 실패·parse 부분 실패·등록 rollback·타 lab/file 대입·일반 API 위조·동일 identity 재시도·변경 identity 새 receipt·실제 grant/D9/projection 왕복. 기존 evidence/삭제/reader/검색/pipeline DB 회귀를 유지한다.
- 선언 후보14gate: core/pipeline/AI service-tests, service-tests-selftest, stage2-markers, contract-lint, contract-breaking, generated-up-to-date, import-boundary, db-boundary, ai-no-lineage-write, migration-single-head, rls-coverage, schema-diff. 실제 시작 시 환경·대상을 확인하며 검사를 줄여 통과시키지 않는다. migration 번호는 시작 시 head에서 재확정한다.
- [x] Task2g runtime `c9ac29ef8fbd4834baee3584b9c1f81f`, run `f7bd6adac6d7467b9365490d1b01013c`: 위14gate green/판정0/준비0. core1588pass/skip0/deselect6(383.10초), pipeline310/0/26, AI304/0/0, stage2 일반87/0/249(JOBS1). platform0040/AI0008 단일 head, 양 schema drift0. 부모 전체14gate verify-report·hash `9d983ca0dd0ba8b1ba15773e242f89e29cbbb8317d91f87e7c3b10358efe7b56` 직접 확인, advisor clean, lifecycle 인계 완료. 이후 문서 변경은 이 보고서의 검증 범위 밖이다.
- 부모 직접 회귀: fixture 보완 전 core 관련149pass·pipeline310pass, 보완 후 측정/authority46pass(17.09초). 실제 NumPy parser→SqlLedger→등록 HTTP→별도 D9 프로세스→reader/projection 왕복이다. DEV 자료·로그인 UI·실제 S3·모델 평가가 아니다. 기존 pipeline worker 진입점을 재사용했고 stage2 selector에는 dbint가 없다. CI 조건/환경은 로컬 검증했으며 원격 CI 실행은 아니다.
- 실패 이력: run `82cf554c2caa40feb7941f3facb55246`은13/1/0(core1584pass/1fail), 첫 claim100 안에 대상이 있다는 공유lab 시험 가정 실패. 고유lab 및 타lab backlog0/101 불변 검증으로 격리했다. 이어 run `ca06e467215141c9ac947664e6503f68`도13/1/0(core1585pass/1fail): 최신file 행이 있는 DB에서 과거0038을 재실행한 시험 오류였다. 실제0037 일회용 DB→숨긴 canonical1행→NOBYPASS 소유자0038 이관·RLS 복원으로 교정하고 timeout/TERM 정리 음성2건을 추가했다. 두 실패를 최종 성공에 합산하지 않는다.
- 외부 요청 사고 이력: storage 단위시험의 stream transport mock 누락으로 고정 가짜 자격·bucket 요청이 실제 AWS에 도달해400 InvalidBucketName을 받았다. 성공한 객체 작업은 관측되지 않았다. 즉시 중단 후 일반/stream fake transport와 외부 접속 차단을 보완했다. 이 요청을 승인된 실제 S3 검증으로 처리하지 않는다. 등록 bind/activity/commit rollback 및 응답201 시점 결함, snapshot bytes·SQL·fixture 준비 실패의 RED 이력도 보존한다.

### 확정 관계 변경: 구현·검증된 증분
- [x] `ports/lineage.py`에 `LineageRevision(dataset_id,revision,deleted)`와 `revisions(dataset_ids)` 읽기 Port를 추가하고 D4 adapter를 고정 조립한다. 단일 SQL snapshot이며 write lock을 잡지 않는다. 존재/권한 확인 없는 누락을 revision1로 바꾸지 않는다. 정상 빈 자료 초기 revision1 및 기존 자료 backfill을 명시한다.
- [x] `domains/d4_lineage.py`와 신규 platform migration에 retained `(lab_id,dataset_id,revision,deleted)`를 둔다. 실제 head0040 뒤 번호를 확인한다. dataset FK/CASCADE 없이 삭제 marker를 보존한다. 별도 outbox는 만들지 않으며 중간 이벤트 재생이 아닌 최신 상태 수렴만 보장한다.
- [x] `app/routes/{ingestion,lineage,deletion}.py`에서 D4 lab lock→기존 D3/관계 row locks→revision 변경 순서를 통일한다. 등록 DB쓰기 전·삭제 lock_dataset 전에 잡고 대기 후 존재/삭제/수정권한을 재검사한다. add/remove/method는 양끝, unknown은 자신만 증가하며 add+unknown 해제는 한 번, 실제 무변경은 증가0이다.
- [x] 자료 softdelete는 같은 TX에서 자기 deleted marker와 이웃 revision을 갱신하되 기존 edge/unknown/confirmation을 보존한다. 실패 시 모두 rollback. 운영 hard purge·삭제ID 재사용/복원 기능은 이번 범위 밖이다.
- [x] `app/knowledge_source_authority.py`·`domains/d3_knowledge_source.py`에 고정 Port를 주입한다. `Dependency(owner="D4",resource_id=dataset_id,revision=n)`은 incident 확정 관계 집합+unknown 상태 버전이다. issue의 payload/command 재사용에 dependencies equality를 포함하고 validate/authorize_read에서 현재성을 대조한다. 관계 ID/confirmed_at은 원본 계보에 유지한다.
- [x] `app/knowledge_projector.py`·`domains/d3_knowledge_projection.py`에서도 같은 읽기 Port로 의존성을 재검사한다. source/ontology/queue 잠금 뒤 D4 write lock을 추가하지 않는다. 배치 소비 전에도 낡은 receipt 조회/반영을 거절한다. 분산 commit이나 조회 이후 race의 원자성은 주장하지 않는다.
- [x] 신규 `domains/d3_knowledge_dependencies.py`의 `requeue_if_lineage_changed`는 source별 last processed D4 revision과 requeue/generation 무효화를 같은 D3 TX에 반영한다. 신규 `app/knowledge_dependency_refresh.py`의 `run_once(session_token,after_source,limit)`는 기존 tracked principal만 사용한다. 순환 전수 sweep으로 cursor 뒤 변경도 다음 회차에 잡고 새 source는 미처리로 본다. 접근 불가/실패에 성공 cursor를 쓰지 않는다. 무인 계정 위임·상시 worker는 후속이다.
- [x] RED: 모든 mutation/no-op/rollback·양끝 영향, 관계 추가/등록 대 삭제 경합, 숨김≠빈집합·forbidden≠deleted, source bytes 불변인데 의존 변경 시 새 command, 소비 전 stale read/projection 거절, crash/replay/부분 실패/cursor 뒤 변경 재포착을 실제 DB/HTTP 시험으로 고정한다. mappings=[]이므로 관계 기반 fact 생성·선택적 KG edge 삭제 완료로 보고하지 않는다.
- [x] 위 시험 GREEN 후 core/AI service-tests, generated-up-to-date, import-boundary, db-boundary, ai-no-lineage-write, migration-single-head, rls-coverage, schema-diff의9gate를 같은 task 묶음 JOBS1로 검증한다. wire 변경 필요 시 먼저 보고하고 contract gates를 추가한다. advisor 계획 검토의 lock 순서 보완을 반영한 범위이며 부모 핵심 재실행 및 최종 수용 검토를 거친다.
- Task2h runtime `7c892839ce81486bba92bb84a2924529`, run `8c5a5da2cdcc4ffe91ec310fa0e3a7ca`: 선언9gate green/판정0/준비0. core1608pass/skip0/deselect6(406.06초), AI304/0/0(7.40초), platform0041/AI0008 단일 head, RLS70표(명시 면제 별도 표시), 양 schema drift0. 부모 전체9gate verify-report와 당시 hash `de73d480f4650ffefa4f4fa013859341630fd169d2ea2996e733fa4d751a8b1d` 확인, advisor clean 및 lifecycle 인계 완료. 이후 문서 변경은 이 실행의 검증 범위 밖이다.
- 부모 직접 핵심4파일81pass(57.74초), 작업자 관련11파일226pass(94.46초). 실제 0040→0041 NOBYPASS 소유자 이관에서 live/softdeleted 두 lab의 숨긴 행 및 RLS 복원을 확인했다. source bytes revision을 변경하지 않고 D4 dependency mismatch를 기존 `stale_source`로 반환하며 새 issue에서 generation을 올린다. wire/AI 제품 변경은 없다.
- 수용 검토에서 private 선두 source가 공개 자료 처리를 막는 결함과 3자 잠금 cycle을 발견했다. 각각 forbidden 및 실제 PostgreSQL `40P01` RED로 재현했다. LIMIT 전 viewer RLS JOIN, 정렬·중복 제거한 고정 batch의 모든 source lock 선점→대기 후 D4/source 재검사→queue 변경으로 보완했다. 새 key를 선점 뒤 추가하지 않으며 동시 sweep·대기 중 권한/버전 변경·부분 실패 rollback 시험을 유지한다. 보완 전221pass·부모76pass를 이 결함의 통과 근거로 사용하지 않는다.
- 초기 producer/의존성/삭제 미연결 RED 및 시험 fixture의 deleted_by 누락, 등록400/관계추가404 기대값 오류는 별도 실패 이력이다. 기존 제품 응답·migration 이력을 바꾸지 않았다. 실제 등록/관계 추가 대 삭제 경합, D9 HTTP의 소비 전 stale 거절, cursor 뒤 변경 재포착을 검증했다. 조건 검색·관계 fact 생성·무인 운영 완료는 아니다.

### 다음 진입 조건: 자동 실행 권한
- 기존 worker의 `actor()`는 로그인 이름과 credential version을 확인할 뿐 tracked session이나 사용자 위임을 발급하지 않는다. 이를 로그인 세션으로 승격하거나 service bearer/operator로 자료 권한을 대신하지 않는다.
- 2026-09-15 사용자에게 별도 워커 위임 계약의 설계·로컬 구현 여부를 질문했으며 응답 대기다. 권고 방향은 사용자의 현재 자료 접근 범위 안에서 명시 위임·철회·계정 정지/자료 접근 취소의 즉시 집행이며, 실제 자격 발급/운영 활성화는 별도 승인이다. 만료/갱신·logout 영향·비공개 범위·자격 보관/감사는 아직 정책 동결 전이다.
- 기존 승인 안에서는 정상 tracked session을 호출 수명에만 사용하는 bounded 단발 연결이 가능하다. 지속 무인 실행으로 자동 전환하거나 장기 자격을 임의 생성하지 않는다. 다음 Task3의 권한 전제 확정 전 상시 worker는 시작하지 않는다.
**Files:**
- Reuse/modify: `services/core-api/src/colab_core/app/search_refresh_tools.py`
- Reuse/modify: `services/core-api/src/colab_core/domains/d3_search_facts.py`, `d3_search_annotations.py`
- Create on approval: `services/ai-service/src/colab_ai/domains/d9_dataset_knowledge.py`
- Create on approval: `services/core-api/src/colab_core/ports/knowledge.py`
- Test: `services/core-api/tests/test_search_refresh_tools.py`, `services/ai-service/tests/test_dataset_knowledge.py`
- Schema: `db/ai/`의 신규 migration과 schema; 원본·projection 변경이 필요한 경우에만 `db/platform/`의 별도 migration

**Interfaces:** Task 1의 scoped command → 원자적인 source별 KG replace/invalidate → receipt → D3 projection 반영 → queue ack.

- [ ] 파일에서 확인한 사실과 사용자 설명을 구분하는 검증 fixture를 기존 source snapshot seam에 추가한다. 무거운 추출은 D5 소유 Port로 받는다.
- [ ] 아래 상태 순서에 대한 외부 결과 시험을 추가하고 RED를 확인한다.

```text
source v1 처리 시작 → source v2 교체 → v1 완료 시도 → 거절
D9 v2 commit → 프로세스 중단 → 재시작 → 동일 receipt → projection 한 번 반영
source 삭제 → 지연된 v2 commit 도착 → 거절 → 검색 결과 없음
같은 source에 처리 generation 2 완료 → generation 1 지연 완료 → 거절
projection sequence 2 반영 → sequence 1 지연 수신 → 거절
D4 확정 관계 삭제 → 의존 source 재queue → 관계 기반 연결 무효화
```

- [x] 멱등 반영·최신 revision 확인·tombstone·receipt 검증의 최소 구현. 위 증분별 실측 범위를 따른다.
- [x] D4 계보는 읽기 참조만 사용하고 AI의 원본 계보 쓰기 금지 경계를 검사했다.
- [x] D4 자료별 incident-set revision을 처리 의존성에 포함하고 추가·수정·삭제 후 재queue를 검증했다. 별도 outbox 없이 현재성 읽기 Port와 source별 처리 기록을 사용한다.
- [x] 각 DB 단일 head 실측 및 독립 migration 추가. DB 간 FK나 이력 rewrite는 하지 않았다.
- [ ] 기존 stale/rollback/access 시험과 새 D9 수명주기 시험을 실행한다.

Run: `bash gates/run.sh service-tests-core-api`, `bash gates/run.sh service-tests-ai-service`, `bash gates/run.sh migration-single-head`, `bash gates/run.sh import-boundary`, `bash gates/run.sh db-boundary`, `bash gates/run.sh ai-no-lineage-write` (각각 직렬).

## Task 3: 변경분 실행과 일일 조정의 시계를 분리한다
**Files:**
- Modify: `services/core-api/src/colab_core/domains/d3_search_runs.py`
- Modify: `services/core-api/src/colab_core/app/search_refresh_runner.py`, `search_refresh_worker.py`
- Test: `services/core-api/tests/test_search_refresh_runner.py`, `test_search_refresh_worker.py`

**Interfaces:** 영속 pending source → 기존 `run_due(tools, max_jobs=100)` → 요약. 기존 CLI `--once/--loop/--status` 유지.

- [ ] 다음 기대값을 실제 함수/시계 fixture에 연결한 회귀 시험으로 작성한다.

```text
일일 조정 완료 직후 신규 source 변경 → 다음 worker tick에 claim 가능
pending source 없음 → 모델 호출 0
동일 source 100회 변경 신호 → 최신 revision으로 수렴, 중복 facts 없음
worker 2개 동시 claim → 같은 generation을 둘이 확정하지 못함
외부 호출 실패/timeout → lease 회복 → 제한된 retry → 소진 상태 노출
```

- [ ] RED 후 source queue 시계와 manifest/reconcile 시계를 분리한다.
- [ ] batch 100건/180초/실패10건 상한은 유지하고 외부 호출 timeout·retry 상한·budget 소진 상태를 정확한 계약으로 고정한다.
- [ ] 신규 업로드가 backfill에 밀리지 않는 시험과 정상 SIGTERM/강제 종료 후 복구 시험을 추가한다.
- [ ] HTTP 앱을 실행하지 않고 CLI 프로세스만 기동해 처리·중단·재개를 검증한다. DEV에 배치하지 않는다.

Run: `bash gates/run.sh service-tests-core-api`.
증명: 30분은 초기 반영 목표이며 30초 poll을 30초 완료 보장으로 쓰지 않는다. queue age·완료 latency를 별도로 기록한다.

## Task 4: 새 개념·관계의 제안과 release 경로를 구현한다
**Files:**
- Reuse: `services/ai-service/src/colab_ai/app/concept_proposals.py` (기존 선택 기능의 의미 유지)
- Create on approval: `services/ai-service/src/colab_ai/domains/d9_knowledge_proposals.py`
- Modify: `services/ai-service/src/colab_ai/app/ontology_manifest.py`
- Test: `services/ai-service/tests/test_knowledge_proposals.py`, `test_ontology_manifest.py`
- Projection test: `services/core-api/tests/test_search_ontology.py`

**Interfaces:** 원본 근거+기획 근거+유사 개념 → proposal → 개별 승인/거절 → release receipt → 영향받은 source 재queue.

- [ ] 승인 전 제안 비활성, 비승인자 거절, stale source 승인 거절, 공용 승격 시 비공개 근거 유출 거절 시험을 먼저 작성한다.
- [ ] 같은 의미의 alias·정의/단위 충돌을 분리하고 개념 중복 생성 방지 시험을 작성한다.
- [ ] 기존 선택 API와 별도인 proposal/review/release 계약을 구현한다. 모델에게 publish 권한을 주지 않는다.
- [ ] 정정 release가 이전 결정을 보존하며 관련 자료를 재queue하고 무관 자료 모델 호출은 늘리지 않는지 검증한다.
- [ ] 실제 모델 대신 고정 제안 fixture로 정책을 시험한다. Sonnet 보류 해제 없이 실제 평가를 실행하지 않는다.

Run: `bash gates/run.sh service-tests-ai-service`, 이어서 `bash gates/run.sh service-tests-core-api`.

## Task 5: 실제 자료와 외부 여정으로 효과를 검증한다
**Files:**
- Reuse: `eval/k4-search/client-golden.json`, `eval/k4-search/golden-cases.json`
- Create on approval: `eval/k4-search/knowledge-lifecycle-cases.json`
- Report: `dev-package/reports/knowledge-lifecycle-validation.md`

**Interfaces:** 승인된 격리 자료·사용자 계정으로 public upload/search API → 독립 워커 → 결과·근거·권한·처리 상태. UI 여정은 agent-browser로 별도 검증.

- [ ] 현재 자료 ID·파일 version/hash·출처·기대 검색을 대응시킨다. 과거 frozen ID와 현재 28개를 혼용하지 않는다.
- [ ] 실무자 7문항과 기존 12문항 각각 기대 포함·제외·질문 보완·미확인 근거를 고정한다.
- [ ] 신규 업로드·재처리·교체·삭제·권한 취소·crash/retry를 격리 환경에서 실행하고 실제 모델 호출 여부를 기록한다.
- [ ] 모델 미설정 상황에서 기본 검색과 결정적 연결을 검증한다. 이 결과와 실제 모델 품질 결과를 별도 열로 둔다.
- [ ] 활성화 승인 시에만 실모델·부하 평가의 입력 규모·비용 상한·지연 목표를 확정하고 실행한다.

증명: 요청→워커→검색 전체 경로. 내부 DB 함수 성공이나 스크린샷만으로 E2E를 통과 처리하지 않는다.

## 문서 검증·인계
- ADR 구조: `python3 scripts/harness/adr_gate.py --all`.
- 내부 참조 파일의 실존 및 라운드 300행 이하 확인. source path 후보는 생성 예정임을 구분한다.
- 독립 advisor 검토 후 모순·범위 초과·누락을 수정한다.
- 2026-09-15 advisor 결과: 조건부 수용. 처리 generation/publication sequence 역전 차단과 D4 관계 변경 재처리를 spec·Task 1/2에 보완했다. 상세 계약 동결·구현 준비 판정은 유보한다.
- 초기 문서 단계의 intent 대조: O1~O6은 당시 미구현/미검증, O7은 문서 연결로 충족했다. 후속 로컬 구현은 위 증분 기록을 따른다. 현재도 O1~O6 전체 충족은 아니며 무인 자동 처리·개념 매핑/조건 검색 소비·검토/release·외부 여정이 남아 있다. 조회/projection·삭제·D4 변경 추적의 검증 범위를 이 잔여 항목과 구분한다.
- 후속 실행 승인은 이미 받았다. 설계 방향은 반복 질문하지 않으며 운영 활성화·실제 모델 평가는 별도 승인 경로를 유지한다.
- 현재 다음 구현: 자동 실행 권한 전제 확정 → 실행 연결·매핑/검토 및 실제 조건 검색 연결. 파일 측정의 format-only 왕복과 D4 의존 변경은 검증했지만 O1~O6 전체는 미달이다. 기존 메모리 handle이나 과거 발급자 grant를 현재 viewer 권한으로 재사용하지 않는다.
