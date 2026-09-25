# Spec: 지속 업로드의 근거 기반 지식 수명주기
출처 intent: [2026-09-15-knowledge-lifecycle](../../intent/2026-09-15-knowledge-lifecycle.md) (승인 2026-09-15)

상태: 2026-09-15 사용자 "그래 그러자"로 설계 방향·기술 계약 문서화 승인. 기계 판독 계약 동결·제품 구현·배포는 미실행.
후속: 사용자 "그럼 이제 해" 이후 로컬 구현이 승인되었고 source authority·D9 저장/읽기/삭제·projection·format-only 측정·D4 의존 변경과 tracked-user 재처리 증분을 검증했다. 위 문서 작성 당시 상태와 아래 현행 조사 표는 이력이다. 자동 worker·매핑·검토/release·실제 검색 품질은 미완료이며 현재 근거는 [실행 계획](../rounds/R-KNOWLEDGE-LIFECYCLE.md)을 따른다. 지속 무인 실행의 위임 정책은 사용자 결정 대기이며 통합·배포·모델 평가는 보류한다.
연결 규칙·권한·원자성 한계·14개 수용 시험의 상세안은 [도메인 계약](knowledge-lifecycle-contract.md)에 둔다.

## 문제 진술
- 지속 업로드를 검색 지식으로 연결하고, 그 과정에서 발견한 새로운 의미를 검증해 온톨로지로 축적해야 한다.
- 온톨로지·자료별 KG·검색 인덱스를 같은 정본으로 다루지 않고 독립 실행 가능한 처리 경계를 유지해야 한다.

## 해법 개요
기존 자료 등록과 기본 검색은 유지한다. 자료 변경을 영속 기록하고 독립 워커가 근거를 추출하여 기존 개념에 연결한다.
검증된 사실·매핑은 자료별 KG에 반영하고, 새 개념·불확실한 관계는 제안으로 분리한다.
승인된 온톨로지 release와 자료별 지식 receipt를 검색 조회 모델에 반영한다.
일반 검색 실패는 조사 후보이지 지식을 확정하는 증거가 아니다.

## 현행 근거와 차이
기준: `codex/ai-search-next` HEAD `311410634a955c217a78505f8a133d66962d47cd`, 2026-09-15 읽기 조사. DEV 재측정 아님.

| 현행 | 재사용 / 개발 필요 |
|---|---|
| D3 변경 trigger·queue·lease·generation | 변경분 처리와 오래된 결과 거절 재사용 |
| 자료 facts와 source locator/hash, reviewed evidence | 출처 snapshot 재사용; 원본 파일의 실제 추출 범위는 D5와 연결 |
| D9 manifest·one-hop lookup | 개념 조회와 의존 검증 재사용 |
| Sonnet concept selections | 기존 개념 선택만 가능. 새 개념·관계 생성 기능으로 부르지 않음 |
| D3 concept match·binding | 검색 projection 재사용, D9 KG 정본과 구분 |
| 별도 once/loop/status CLI | 독립 실행 진입점 재사용. 운영 배치 구성은 이번 문서 작업 밖 |
| 완료 후 1일, pending/failed 60초, loop 30초 | 신규 변경 처리 시계와 일일 reconciliation 분리 필요 |
| D9 runtime write·승인·release | 미구현. 아래 계약·보안·DB 설계의 개발 대상 |

## 사용자 스토리
1. 업로더로서 지식 분석을 기다리지 않고 자료 등록과 기본 검색을 사용하고 싶다.
2. 검색자로서 자료의 변수·기간·공간·원래 해상도와 가공 해상도를 구분한 결과를 받고 싶다.
3. 검색자로서 확인되지 않은 조건은 미확인으로 보고 싶다.
4. 자료 관리자로서 파일 교체 후 이전 버전의 분석이 새 파일의 사실로 표시되지 않기를 원한다.
5. 자료 관리자로서 삭제·권한 취소가 지식 배치 완료와 무관하게 검색에 적용되기를 원한다.
6. 도메인 승인자로서 새 개념과 관계의 원본 근거·중복·충돌을 보고 개별 승인 또는 거절하고 싶다.
7. 도메인 승인자로서 오류가 있는 release를 정정하고 영향을 받은 자료만 재연결하고 싶다.
8. 운영자로서 기본 검색을 중단하지 않고 워커를 재시작·재처리하고 싶다.
9. 운영자로서 실패·정체·모델 한도 초과를 성공이나 빈 데이터로 오해하지 않고 싶다.
10. 개발자로서 intent·spec·ADR·시험을 따라 특정 처리의 소유자와 선택 이유를 확인하고 싶다.

## 구현 결정

### 모듈·소유권
| 소유 | 정본 | 다른 영역에 제공하는 것 |
|---|---|---|
| D3 Catalog | 자료·파일 버전·확인된 메타데이터 | 권한 있는 source snapshot와 변경 기록 |
| D4 Lineage | 사람이 확정한 계보 | 확정 관계의 버전 있는 읽기 결과 |
| D5 Ingestion | 파일 파싱·무거운 추출 작업 | 파일 버전·추출기 버전·출처가 있는 결과 |
| D9 Ontology & KG | 개념 release, 자료 엔티티와 근거 연결 | 검증된 개념 proof, scoped KG receipt |
| D10 AI | 해석·후보 제안 | 검토 가능한 후보; 확정 쓰기 권한 없음 |
| D3 검색 조회 모델 | 재구축 가능한 facts/binding/index | 현재 권한·버전에 유효한 검색 후보 |

워커는 새 도메인이 아니라 조정 프로세스다. 도메인 간 직접 SQL/FK와 core-api geo import는 금지한다.
개념 어휘와 관계 의미는 기획 정본을 근거로 하며 없는 의미는 `[정본 무근거]` 제안으로 남긴다.
원본 설명의 주장과 파일에서 측정한 사실을 구분한다. 충돌은 숨기지 않고 확정을 보류한다.

### 계약 초안: source → KG → projection
이 절은 논리 계약 개요다. 상세 Port·권한·grant·receipt·운영 검토 절차는 연결된 계약 상세안을 따른다. wire schema·생성 타입은 제품 구현의 계약 단계에서 검증·동결한다.
- Source identity: lab_id, dataset_id, source_kind, source_id, source_revision, source_hash. 정규 ID는 기존 ULID 계약을 따른다.
- Processing identity: extractor_version, mapping_version, ontology_release, job_generation. 멱등 키에 source identity와 처리 identity를 포함한다.
- Fact: predicate, value, unit(해당 시), source_locator, evidence_kind, source_hash. evidence_kind는 파일 측정/사용자 설명/검토 근거를 구분한다.
- Mapping: concept_id, predicate, fact reference, mapping rule 또는 승인 reference. 모델 선택만으로 confirmed 상태를 부여하지 않는다.
- KG command: replace-source 또는 invalidate-source, 기대 source revision, facts/mappings, scoped principal. 단일 source 단위 원자적 갱신; 최신 revision보다 오래된 결과는 거절한다.
- KG receipt: source identity, accepted processing identity, publication sequence, status, scoped facts/mappings digest. 검색 반영자는 발급자·버전·범위를 검증한다.
- 동일 source revision에서도 처리 요청마다 승인된 단조 증가 generation을 발급한다. KG commit은 현재 generation과 기대 ontology_release/extractor_version/mapping_version의 정확한 일치를 검증한다. 버전 문자열·hash의 사전순으로 신구를 비교하지 않는다.
- projection은 동일 scoped source의 publication sequence가 증가하는 receipt만 적용한다. 동일 sequence 재전달은 멱등, 작은 sequence는 거절한다. ontology rollback도 과거 버전으로 돌아가는 새 generation/release로 발행한다.
- D9는 원본 자료 존재·최신 상태를 신뢰된 source 계약으로 검증한다. 수신한 model text나 caller가 고른 lab_id를 권한 근거로 삼지 않는다.
- D9 commit 성공 후 projection 반영 실패는 같은 멱등 키의 receipt로 재시도한다. projection 완료 확인 전 원본 작업을 최종 ack하지 않는다.
- 삭제 tombstone과 최신 source revision은 늦게 도착한 commit이 자료를 부활시키지 못하게 보존한다. 물리 정리와 접근 차단을 분리한다.
- D4 확정 계보의 추가·수정·삭제는 자료별 incident 관계 집합+unknown 상태의 단조 revision으로 전달한다. `Dependency(owner=D4,resource_id=dataset_id,revision=n)`이며 개별 관계 ID/confirmed_at은 D4 원장에 보존한다. retained marker와 source별 cursor의 순환 대조로 최신 상태에 수렴하므로 별도 outbox/중간 이벤트 재생은 도입하지 않는다. 관계 기반 연결 무효화는 최종 매핑 요구사항이며 현재 mappings=[] 단계와 구분한다. D9에 계보 원장을 새로 만들지 않는다.
- 원본 파일이 바뀌면 이전 facts와 mappings는 검색 판정에 즉시 부적합해진다. 새 분석 중에는 기본 메타 검색과 미확인 설명으로 내려간다.

### 새로운 온톨로지 지식의 검토
- 기존 concept selection과 신규 concept/relation proposal을 별도 계약으로 둔다. 기존 selection API의 허용 범위를 넓혀 우회하지 않는다.
- 제안은 원본 fact locator·제안 사유·기존 유사 개념·충돌·기획 근거·모델/프롬프트 버전을 포함한다.
- 단계: proposed → approved 또는 rejected. 승인 후 D9의 원자적 release publish를 통해 active가 된다. source가 stale이면 승인 전에 재검증한다.
- 명칭만 달라진 동일 개념은 alias 후보로 처리하고 동일 개념을 중복 생성하지 않는다. 정의·단위가 충돌하면 자동 병합하지 않는다.
- 승인자는 현행 DOMAINS에 따른 Ted 또는 명시 지정자. 개별 제안별 검토를 기록하며 모두 승인 경로는 만들지 않는다.
- 승인 취소·정정은 새 release와 supersedes 관계로 남긴다. 이전 결정을 삭제하지 않는다.
- release 변경은 의존한 자료를 재queue한다. 새 alias 등 discovery 변경도 영향을 검출한다. 무조건 전체 LLM 재실행하지 않는다.
- 자료별 사실은 scoped KG에 남고, 공용 온톨로지에는 검토된 일반 개념만 승격한다. 비공개 자료 이름·인용·ID는 공용 release로 복사하지 않는다.

### 실행·스케줄·장애
- 기존 CLI와 bounded runner를 재사용하고 HTTP 앱 안에서 scheduler를 시작하지 않는다.
- source 변경 시 영속 작업을 기록하고 최신 revision으로 합친다. 중복 delivery, 역순 delivery, crash 후 재개를 정상 입력으로 취급한다.
- 변경 작업 처리는 일일 manifest/조정 시계와 별개다. 통상 30분 이내 의미 보강을 초기 목표로 두고 queue age와 end-to-end 지연을 측정한다.
- 초기 안전 상한은 기존 runner의 batch 100건·180초·실패 10건 중단을 유지한다. 이는 단일 외부 호출의 강제 timeout 보장이 아니며 adapter에 별도 timeout이 필요하다.
- 외부 호출 timeout은 작업 lease보다 짧고 retry는 영속 backoff·상한을 가진다. 상한 소진은 terminal failed로 남겨 명시 재처리한다.
- 모델 budget이 없거나 소진되면 모델 단계는 disabled/budget_exhausted로 보이고 기본 검색·결정적 매핑은 계속한다. 비용 예산 숫자는 운영 승인 전 임의 설정하지 않는다.
- 동일 파일이라도 권한 범위를 넘는 cache 공유는 하지 않는다. 다량 업로드는 완료된 원본 단위로 묶고, 실패한 파일 하나가 전체 묶음을 막지 않는다.
- 전체 backfill은 bootstrap checkpoint로 실행하며 신규 변경 처리를 굶기지 않도록 회차별 양을 제한한다.
- status는 pending/running/ready/candidate/failed/stale/disabled의 구분을 보존한다. 수집·처리·실패·skip·모델 호출·최고 queue age를 보고하며 본문·비밀은 로그에 남기지 않는다.
- Lambda는 선택하지 않는다. 분리 프로세스 종료·재기동·중복 실행 시험으로 이동 가능 경계를 검증한다.

### 스키마·마이그레이션
- D3 변경 큐·facts·binding·annotation과 D9 manifest receipt는 기존 schema를 우선 재사용한다.
- D9의 dataset entity/fact/mapping, proposal/review/release 상태는 AI DB 체인에 소유시킨다. platform DB에 D9 정본 테이블을 만들지 않는다.
- 논리 unique: scoped source+processing identity, proposal content+source version, release identity. 원본 DB 간 FK는 금지한다.
- 이번 문서에서 migration 파일·번호를 발급하지 않는다. 구현 시작 시 platform/AI 각각 단일 head를 실측하고 각 체인에만 연결한다. 기존 이력 rewrite는 금지한다.
- 순서는 additive schema → 버전 계약 제공 → worker 전환 → scoped backfill → projection 대조다. 기존 읽기는 검증 전 제거하지 않는다.

### API 계약
기존 업로드·검색 public API는 비파괴 유지가 목표다. 신규 내부 D9 commit/review/release 계약은 별도 버전으로 추가한다.
기존 D9 read-only 경계에 write capability가 추가되므로 동결 계약과 도메인 정책의 확장 검토가 필요하다.
구체 HTTP 경로·인증·권한 scope·wire 형식을 승인·동결하기 전 endpoint를 구현하지 않는다.

## 시험 결정
재사용 seam은 실제 업로드/자료 변경 → 독립 워커 → 기존 검색 API다. 신규 seam은 D9의 scoped 지식 반영/검토 계약만 추가한다.
이 시험 경계는 승인된 연결 규칙·시험 방법 구체화에 포함한다. DB 내부 함수만 호출한 결과를 API/UI E2E로 보고하지 않는다.

| 검증 | 외부 기대 결과 |
|---|---|
| 신규 자료 | 기본 검색 후 해당 자료의 확인된 개념·조건이 의미 검색에 반영 |
| 재처리·중복·순서 역전 | facts/mappings 중복 없음, 최신 결과 유지, 무변경 모델 호출 0 |
| 교체·삭제 | stale 완료 거절, 삭제 자료 재등장 없음 |
| 권한 취소·타 연구실 | 검색·KG·제안·receipt·cache에서 비인가 근거 노출 0 |
| 워커/모델 실패 | 업로드·기본 검색 유지, 재기동 후 lease 복구와 제한된 재시도 |
| D9 commit 후 crash | 같은 receipt로 projection 수렴, 이중 publish 없음 |
| 동일 source의 처리 generation 역전 | 이전 ontology/mapping 결과 거절, 낮은 publication sequence 적용 거절 |
| 확정 계보 추가·수정·삭제 | 의존 자료만 재처리, 제거한 관계의 파생 연결 무효화, D4 원장 무변경 |
| 신규 개념 | 승인 전 확정 검색 근거 아님; 승인 release 후만 활용 |
| release 정정 | 관련 자료 재연결, 무관 자료 모델 재호출 없음 |
| 원래/가공 해상도·LST/기온·관측/예측 | 잘못된 동일시 없음, 근거 부족은 미확인 |
| 기존 28개 및 실무자 7+기존 12문항 | 현재 ID·자료 근거로 기대결과 고정, 미보유 자료의 정직한 빈 상태 |

- 기존 서비스 테스트와 계약/import/DB 경계/RLS/migration 게이트를 변경 범위에 맞춰 실행한다. 실행 계획에 정확한 명령을 둔다.
- 대상 0건은 실패/준비 실패이며 테스트 수·failed/skipped/deselected와 모델 호출 수를 각각 기록한다.
- deterministic 테스트는 실제 모델 평가와 구분한다. Sonnet 실제 평가는 기존 보류를 유지하고 보류 상태에서 LLM 품질 완료를 선언하지 않는다.
- 지연 목표는 시계 주입 시험과 실제 부하 시험을 분리한다. 부하 규모·모델 budget이 미승인인 동안 운영 SLA를 주장하지 않는다.

## 정책 대조 (작성 시점 제약)
- 제품 §2·§3: D9 지식 소유와 D3/D4 원장 유지, D10 계보 쓰기 금지, DB 체인 분리, scoped 조회 유지. 신규 D9 write Port의 권한 경계는 검토 필요.
- 제품 §5: 코드·배포·새 UI·새 서비스/DB 도입을 이번 문서에 포함하지 않는다. 미확정 사항은 아래 차단 항목으로 명시한다.
- 계약 동결 해제 필요: 신규 내부 지식 반영 seam의 승인·동결 필요. 기존 공개 계약의 파괴 변경은 승인하지 않으며 diff로 판정한다.
- 디자인 제약 확인: 해당 없음(이번 설계는 백엔드 문서). 검토 UI가 필요하면 별도 화면 spec을 거친다.

## 우려 항목 (설계 방향 수용, 구현 검증 필요)
| 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|
| 지식 반영 권한 | 조정자 전용 D9 commit과 조회 권한 분리 | 기존 읽기 토큰에 쓰기 권한 추가 | ⓐ, 보안 계약 검토 후 동결 |
| 새 지식 검토 진입점 | 기존 운영 절차에 개별 review 기능 연결 | 전용 승인 화면 신설 | ⓐ, 현행 절차로 수행 가능한지 계약 단계에서 증명; 화면은 자동 추가 금지 |
| 모델 비용·처리량 | 예산 미설정 시 모델 중지·기본 검색 유지 | 임의 예산으로 모델 활성화 | ⓐ, 운영 승인 시 숫자와 부하 기준 확정 |

2026-09-15 사용자 "그래 그러자"로 위 권고 방향을 수용했다. 재승인 질문을 반복하지 않는다.
개별 검토는 인증된 운영 CLI/adapter로 구체화했으며 현재 존재하는 기능으로 주장하지 않는다. source grant·publish 재검증은 계약 상세안에 기록했다.

## 범위 밖
실제 구현·운영 활성화·재시드·배포·유료 모델 평가, 새 그래프 DB·브로커·Lambda, 무근거 자동 온톨로지 확장.

## 산출 계획
- [소유권 ADR](../../../docs/decisions/0008-knowledge-lifecycle-boundaries.md), [실행 ADR](../../../docs/decisions/0009-knowledge-refresh-execution.md): 상세 설계 proposed.
- [실행 계획](../rounds/R-KNOWLEDGE-LIFECYCLE.md): 계약 → 지식 반영 → 증분 실행 → 제안/release → 외부 검증, 기본 직렬 1레인.
- 문서 정합은 ADR 구조 검사·참조 확인·독립 설계 검토로 판정한다. 제품 수용 기준은 후속 실행에서만 완료 처리한다.
