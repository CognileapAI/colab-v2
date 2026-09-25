# 지식 수명주기 — 도메인 계약 상세안

상위 spec: [knowledge-lifecycle](knowledge-lifecycle.md).
상태: 2026-09-15 설계 방향 승인에 따른 기술 구체화. 구현용 계약 파일·생성 코드·DB는 변경하지 않았다.
이 문서의 함수·필드는 신규 제안이다. 실제 endpoint 존재, schema 동결 또는 보안 구현 완료를 뜻하지 않는다.

후속 실행 상태(2026-09-15): 사용자 "그럼 이제 해" 및 "계속"에 따라 wire DTO, D3 source authority와 D9 replace 저장, 인증된 HTTP·보호된 reader·삭제·독립 projection, format-only 파일 측정 왕복 및 D4 의존 변경의 tracked-user 단발 재처리를 구현·검증했다. 아래 원래 문서 작성 범위는 이력이다. 무인 실행·매핑·검토/release·실제 조건 검색 연결은 남아 있다. 단계별 근거는 [실행 계획](../rounds/R-KNOWLEDGE-LIFECYCLE.md)에 둔다.

## 1. 승인과 변경 범위
- 사용자 승인 원문: "그래 그러자". 대상은 자료·지식·검색의 역할 분리, AI 단독 확정 금지 및 연결 규칙·시험 방법 구체화다.
- 별도 서버·Lambda·모델 활성화·제품 구현은 이번 범위 밖이다.
- 다음 구현에서 이 문서를 기계 판독 계약으로 옮기고 생산자·소비자 음성 시험을 함께 고정한다. 단순 schema 문법 통과로 동결을 주장하지 않는다.

## 2. 권한 행렬
권한은 모델 프롬프트나 요청 본문의 account/lab 값으로 결정하지 않는다.

| 행위자 | 허용 | 금지 |
|---|---|---|
| 자료 소유 도메인 | 현재 자료·권한 검증, 변경/폐기 기록 발행 | D9 테이블 직접 수정 |
| 지식 조정 워커 | 허가된 source 읽기, 검증된 기존 매핑 제출, scoped 무효화 | 새 개념 승인, 임의 account 선택, 계보 수정 |
| D10/모델 | 지정 근거와 개념 범위에서 후보 생성 | KG commit, 제안 승인, release publish |
| 검색 소비자 | 현재 사용자가 볼 수 있는 receipt 조회 | KG 쓰기, 비공개 제안 열람 |
| 도메인 검토자 | 권한 있는 개별 제안 조회·승인·거절 | source 접근 권한 자동 획득, 일괄 승인 |
| D9 release 발행자 | 승인 기록에 정확히 연결된 release 발행 | 승인 없는 후보 포함 |

- 기존 ontology 조회용 service token에 쓰기 권한을 더하지 않는다. 신규 writer credential은 조회 token과 분리하고 D10 실행 환경에는 제공하지 않는다.
- writer 인증만으로 자료 권한이 생기지 않는다. source authority가 account 상태·session version·자료 접근을 검증하고 처리 대상을 묶어야 한다.
- 같은 연구실의 다른 계정도 비공개 자료는 볼 수 없다. lab 일치만으로 KG·제안·receipt를 반환하지 않는다.
- D9 조회와 확정 전 source authority의 최신 검증을 호출한다. unavailable이면 보호된 자료 조회·확정을 fail-closed 처리한다.
- 사용자 권한 취소는 새 조회를 즉시 거절한다. 이미 정당하게 전달된 데이터를 원격 회수할 수 있다고 주장하지 않는다.

## 3. 값과 식별자
JSON 객체는 선언 필드만 허용한다. 정규 ID/시각/오류는 `contracts/schemas/common.json`을 참조하며 새 ULID 정규식을 만들지 않는다.

| 값 | 필수 필드·규칙 |
|---|---|
| SourceKey | lab_id, dataset_id, source_kind, source_id. source_kind는 metadata/file/evidence/lineage의 내부 처리 분류 |
| SourceVersion | revision(단조 증가 양의 정수), digest(SHA-256), deleted(boolean) |
| ProcessingVersion | generation(단조 증가 양의 정수), extractor_version, mapping_version, ontology_release(불투명 content digest) |
| Evidence | fact_id, predicate, value, source_locator, source_version, evidence_kind. 원본 측정/설명 주장/사람 검토를 구분 |
| Mapping | fact_id, concept_id, basis. basis는 승인된 mapping_rule_id 또는 개별 review_id 중 하나 |
| Dependency | owner(D3/D4/D5/D9), resource_id, revision. 계보와 ontology discovery 의존도 포함 |
| SourceGrant | source authority가 발급한 불투명 handle. source/account/session/generation/payload digest/만료에 결합. 비밀이며 로그 금지 |
| KnowledgeReceipt | receipt_id, source_key, source_version, processing_version, publication_sequence, payload_digest, status |

value와 predicate의 허용 형식은 기존 검색 semantics와 파일 추출 계약을 재사용한다. 자유 문장을 임의 predicate로 확정하지 않는다.
숫자·단위가 검증되지 않으면 확정 조건 평가에 사용하지 않는다. model confidence는 확정 권한이 아니다.
검색 receipt에 담긴 account 식별자는 권한 토큰이 아니다. 다른 계정에 전달해도 재검증 없이 사용할 수 없다.

## 4. Port와 전송 경계
이름은 제안 interface다. HTTP 경로는 기존 core-ai seam에 새 버전 작업으로 추가하고 공개 검색 API는 유지한다.

```text
SourceAuthority.read(source_key, principal) -> SourceSnapshot
SourceAuthority.authorize(source_key, source_version, processing_version,
                          principal, payload_digest) -> SourceGrant
SourceAuthority.validate(grant, payload_digest) -> current | stale | forbidden
KnowledgeWriter.replace(grant, facts, mappings, dependencies) -> KnowledgeReceipt
KnowledgeWriter.invalidate(grant, reason) -> KnowledgeReceipt
KnowledgeReader.read(receipt_id, principal) -> AuthorizedKnowledge
Projection.apply(receipt, principal) -> applied | already_applied | stale
ProposalReview.decide(proposal_id, proposal_revision, expected_release,
                      decision, rationale, principal) -> ReviewReceipt
OntologyPublisher.publish(review_id, expected_release) -> ReleaseReceipt
```

- grant는 source authority가 보관한 claim과 payload digest로 검증한다. digest는 변조 탐지이며 발급자 인증을 대신하지 않는다.
- source authority와 D9의 통신은 인증된 adapter를 사용한다. D9가 caller가 준 authority URL이나 임의 storage URL을 따라가면 안 된다.
- grant 재사용은 동일 payload·processing identity에서만 멱등이다. 만료/권한 취소 후 기존 receipt를 다시 얻는 것도 현재 권한 검증을 거친다.
- D9는 다른 DB를 읽지 않는다. source authority는 D3/D4/D5 소유 Port를 통해 snapshot·의존 revision을 조합한다.
- 파일 본문 추출은 D5가 담당하고, source snapshot으로 필요한 제한된 facts만 전달한다. core-api에 geo 의존성을 추가하지 않는다.

## 5. 순서·일관성·중복
1. 소유 도메인은 원본 변경과 영속 변경 기록을 같은 로컬 트랜잭션에 남긴다. 이벤트는 중복·역순 수신 가능하다.
2. source authority는 source별 원하는 processing generation을 로컬 트랜잭션의 잠금/조건부 갱신으로 원자적으로 발급한다. 동시 요청에 같은 generation을 다르게 부여하지 않는다. release hash의 문자열 순서는 비교하지 않는다.
3. 워커는 변경 묶음의 최신 snapshot을 읽고 fact·mapping payload를 만든다. source grant는 그 payload와 generation에 결합한다.
4. D9는 grant의 현재 상태를 검증하고 source별 generation fence를 갱신한 뒤 원자적으로 기록한다. 같은 generation의 다른 digest는 conflict다.
5. D9 receipt는 source별 단조 publication_sequence를 가진다. projection은 현재 원본·권한·처리 의존과 sequence를 재검사하고 적용한다.
6. projection 반영 후에만 작업 ack. 그 전에 crash하면 동일 source/processing/payload로 receipt를 회수하여 재시도한다.

source 검증과 D9 commit 사이에는 분산 race가 있다. 분산 원자성을 주장하지 않는다.
검증 직후 원본이 바뀌어 물리적으로 저장된 결과는 이후 조회·projection의 최신 원본 검사에서 차단하고 새 변경 기록으로 무효화한다.
이미 받은 최신 fence보다 오래된 결과는 D9 저장에서도 거절한다. 아직 전달되지 않은 변경은 원본 재검증과 보정 작업으로 처리한다.
source authority에 접속할 수 없으면 오래된 KG를 확정 근거로 노출하지 않는다. 기본 검색의 별도 원본 권한 검사는 유지한다.

삭제는 source tombstone으로 발행한다. 사용자 접근이 사라졌다는 이유로 무효화 작업이 영원히 실패하지 않게,
소유 도메인의 tombstone grant는 해당 source를 폐기하는 권한만 주고 내용 읽기·다른 source 접근은 주지 않는다.
복원은 더 높은 source revision/generation으로 발행한다. 예전 삭제 이벤트가 새 복원을 덮어쓰지 못한다.
삭제된 ID를 다른 자료에 재사용하지 않는다. 복원은 동일 원본의 명시적 복원이며 새 자료는 새 ID를 사용한다.
D4 관계 변경은 자료별 incident 확정 관계 집합+unknown 상태의 revision으로 전파한다. `Dependency.owner=D4`, `resource_id=dataset_id`이며 관계 자체 ID/confirmed_at은 D4 원장에 보존한다. 관계 삭제 시 파생 연결 제거는 매핑 단계의 최종 요구사항이고 현재 mappings=[] 증분의 완료 항목이 아니다.

## 6. 실패와 재처리 계약
| 결과 | 소비자 처리 |
|---|---|
| invalid_request | 재시도 없이 failed; 민감 본문을 오류에 넣지 않음 |
| forbidden | 권한 재확인 전 중지; 임의 다른 계정으로 재시도 금지 |
| stale_source / stale_generation / stale_release | 과거 payload 재시도 금지, 최신 작업으로 재queue |
| idempotency_conflict | 중지·원인 조사, 기존 receipt overwrite 금지 |
| dependency_unavailable / timeout | 영속 backoff 후 제한된 재시도 |
| budget_exhausted / model_disabled | 모델 단계 중지; 결정적 매핑·기본 검색 지속 |

실행 시각·attempt·다음 재시각은 작업 저장소에 남긴다. 회차 상한은 기존 100건/180초/실패10건을 유지한다.
외부 호출 timeout·retry 횟수·모델 budget은 필수 실행 설정으로 검증하며 누락이면 해당 외부 처리 준비 실패다.
숫자 미설정을 무제한 또는 조용한 성공으로 바꾸지 않는다. 운영량을 측정하지 않은 숫자를 SLA로 동결하지 않는다.

## 7. 사람 검토의 운영 절차
전용 화면 신설 대신 개별 제안을 읽고 결정하는 인증된 운영 CLI/adapter를 구현 대상으로 둔다. 현재 존재하는 명령으로 보고하지 않는다.
- list/show: 현재 접근 가능한 proposal_id·revision·근거·정본 인용·중복/충돌·예상 영향만 표시한다.
- review: 사용자는 특정 proposal_id와 revision, approve/reject, 사유를 명시한다. 와일드카드·모두 승인 옵션은 제공하지 않는다.
- 서버는 실제 인증 주체가 Ted 또는 명시 지정자인지 검증한다. 본문의 reviewer_id나 CLI 문자열만 믿지 않는다.
- 승인 직전에 source·proposal revision·기준 release를 재검증한다. 바뀌었으면 conflict로 다시 검토하게 한다.
- publish는 review_id에 결합된 정확한 개념 변경만 원자적으로 발행한다. 승인 후 payload 수정은 새 제안·새 검토다.
- publish 직전에도 source 유효성·승인자의 현재 권한·review의 유효 상태를 재검사한다. 승인 취소·source 변경·검증 장애는 발행을 막는다.
- 검토된 자료 매핑도 해당 source version에만 유효하다. 정정 release는 새 revision이며 기존 승인 이력은 보존한다.
- 공용 승격은 별도 정제 payload를 사람이 확인한다. 원본 비공개 quote/ID/파일명·임베디드 링크를 그대로 publish하지 않는다.
- 식별자 삭제만으로 공개 가능하다고 판정하지 않는다. 개념 정의 자체가 비공개 내용을 드러내는지도 검토하고, 승인한 정제 payload의 digest를 publish와 대조한다.
- audit에는 실제 주체·시각·proposal/review/release ID·digest를 남긴다. 비밀과 비공개 본문은 일반 로그에 남기지 않는다.

## 8. 계약 수용 시험
아래 14개는 구현 시 독립 시나리오로 계수한다. 이번 문서 작업에서 제품 시험을 실행한 것으로 세지 않는다.

| # | 입력 / 사건 | 반드시 관측할 결과 |
|---|---|---|
| 1 | 기존 ontology read token으로 replace | 거절, KG 쓰기 0 |
| 2 | 같은 lab의 비인가 계정으로 KG/proposal/receipt 읽기 | 근거 노출 0 |
| 3 | grant와 다른 payload / 임의 authority URL | 거절, 외부 임의 URL 접근 0 |
| 4 | 동일 generation·동일 digest 중복 | receipt/sequence 동일, 중복 fact 0 |
| 5 | 동일 generation·다른 digest | conflict, 기존 결과 보존 |
| 6 | generation 2 후 1 완료 / sequence 2 후 1 | 오래된 반영 거절 |
| 7 | authorize 직후 원본 교체·권한 취소 | 늦은 결과 검색 노출 0, 재처리 또는 무효화 |
| 8 | D9 commit 후 crash, projection 전 재시작 | 동일 receipt로 수렴, 이중 publish 0 |
| 9 | 삭제 후 사용자 권한 소멸 | tombstone 폐기 성공, 내용 읽기 권한 없음 |
| 10 | 복원 후 오래된 삭제 delivery | 복원 유지 |
| 11 | D4 확정 관계 수정·삭제 | 관련 연결만 갱신, D4 원장에 AI 쓰기 0 |
| 12 | stale proposal 승인 / 승인 후 payload 변경 | conflict, release 변화 0 |
| 13 | 비공개 근거를 포함한 공용 publish | 거절, 원본 노출 0 |
| 14 | 원본 검증 장애·모델 미설정·변경분 없음 | 각각 보호 근거 차단 / 기본 검색 유지 / 모델 호출 0 |

schema 검사는 기계 판독 타입만, 서비스 시험은 권한·동시성·상태 전이, E2E는 업로드→워커→검색을 판정한다.
기존 실무자 7+12문항 검증은 위 14개를 대체하지 않는다. 실행 수·실패·skip·모델 호출과 대상 SHA를 분리 기록한다.

## 9. 구현 인계
- HTTP 연결 구현 기준: core의 내부 callback은 전용 service token과 실제 tracked 로그인 세션을 함께 검증한다. 세션이 반환한 credential_version을 사용하며, 나중에 읽은 최신 version으로 낡은 세션을 승격하지 않는다.
- D9 writer는 별도 entrypoint/설정으로 실행하며 D10에는 writer 자격을 제공하지 않는다. 요청의 principal은 claim일 뿐이며 고정 source callback의 인증된 principal과 account/lab/version 전체를 대조한 뒤에만 scope·DB에 사용한다.
- writer token·callback token·기존 read token은 서로 달라야 한다. callback URL은 설정으로만 고정하고 redirect·임의 proxy·과대 응답을 거절한다. 세션 token은 요청 수명에만 보관한다.
- 명시 disabled 상태와 enabled인데 필수 secret/주소/timeout/DB 설정이 빠진 준비 실패를 구분한다. callback 이후 logout/원본 변경과 commit 사이의 race는 후속 reader/projection 최신 검사로 차단하며 분산 원자성을 주장하지 않는다.
- 다음 reader 계약: D9 자체 저장 행의 descriptor를 내부 조회하고, 고정 callback으로 현재 viewer의 tracked session·credential·자료 RLS·source version·generation·canonical payload digest를 대조한다. 원래 쓰기 grant의 발급자/만료는 읽기 권한이 아니며 조회는 세대나 grant를 만들지 않는다.
- D9는 자기 manifest와 최종 current receipt를 재확인한 뒤 payload를 반환한다. caller의 receipt/digest는 기대값일 뿐 발급 근거가 아니다. 전용 HTTP reader token은 writer/기존 ontology token과 분리한다. 같은 신뢰 프로세스의 기존 SQL factory + READ ONLY 트랜잭션 재사용은 허용하되 SELECT 전용 DB credential 격리를 구현했다고 주장하지 않는다.
- 최종 row 재확인은 D9 동시 교체만 검출한다. callback 이후의 원본/권한 변경을 원자적으로 막지는 않으며, projection은 현재 원본·release·sequence를 다시 확인해야 한다.
- 다음 삭제 계약: `DeletedSourceVersion{revision, deleted:true}`와 generation-only processing을 별도 명령/receipt로 둔다. source key·전용 grant를 유지하며 payload_digest는 grant를 제외한 삭제 명령 전체의 정규화 hash다. 존재하지 않는 원본 bytes hash나 ontology release를 만들지 않는다.
- 삭제 source authority는 private command와 분리한 body-free 영속 fence를 replace와 공유한다. 현재 evidence change의 정확 key·deleted=true·expected revision 일치만 삭제 증명이다. missing·권한 상실·deleted=false를 삭제로 추론하지 않는다. 처음 삭제도 D9 fence/invalidated receipt를 남긴다.
- 삭제 전용 API capability는 고정 lab 및 명시적인 빈 account scope로 실행한다. adapter는 body-free change/fence/grant의 필요한 열만 사용하며 임의 account/lab·operator scope는 금지한다. 같은 core SQL factory 재사용은 API 경계이며 DB 계정의 본문 접근 불가 보장이 아니다. 운영 credential 발급·별도 프로세스 배포는 여전히 별도 승인이다.
- 전용 삭제 token의 일반 issue/read/replace 거절, 다른 lab 거절, pool account 잔존 없음, 본문 응답·로그 없음, evidence 재삽입 후 과거 삭제 거절을 시험한다. 현재 없는 제품 restore API가 동작한다고 주장하지 않는다.
- 삭제 활성 설정은 `COLAB_KNOWLEDGE_DELETION_ENABLED=true|false`로 명시한다. knowledge/source를 활성화하거나 삭제 설정을 선언한 상태에서 mode가 없으면 준비 실패다. 명시 disabled는 route를 등록하지 않는다. health의 capability enabled는 DB/왕복 readiness 실측이 아니다.
- 다음 projection 계약: 고정 D9 reader의 응답 key/receipt와 typed payload 정합을 대조한 뒤 현재 tracked session·credential·원본/fence/release를 재확인한다. caller가 보낸 principal/receipt 객체나 임의 reader/URL을 권한으로 신뢰하지 않는다. 사용자 session은 호출 수명에만 사용한다.
- D3 receipt ledger는 source별 sequence와 receipt/digest·snapshot 참조를 보존한다. 같은 sequence의 다른 receipt/digest는 conflict, 낮은 sequence는 stale이다. 같은 유효 receipt라도 queue가 pending이면 현재 claim/lease를 검사해 정상 처리하며, 이미 완료된 경우만 상태 변경 없는 already_applied다.
- 현재 지원하는 human_review facts는 같은 source version의 predicate/value/locator 집합과 대조하며 중복 predicate·추가/누락을 거절한다. 기존 facts.process의 snapshot 저장·ack와 ledger를 한 트랜잭션으로 묶고 별도 ack하지 않는다. mappings=[] 경로의 연결을 typed mapping 검색이나 무인 worker 완료로 보고하지 않는다.
- projection 증분은 독립 `KnowledgeProjector`로 구현했다. 기존 SearchRefreshTools의 일회성 handle/동기 mutex는 바꾸지 않았고 worker 연결은 남아 있다. 고정 reader HTTP는 stdlib child와 제한된 부모 IPC를 사용하며 deadline 초과 시 kill/reap한다. 요청은 stdin에만 전달하고 argv/env/stderr에 비밀을 넣지 않는다. OS 프로세스 생성·정리 시간을 포함한 정확한 응답 SLA는 아니다.
- 측정 구현: D5는 실행별 소유 snapshot의 동일 bytes로 확인한 format과 digest를 canonical immutable receipt로 발행한다. 등록 시 D5 Port receipt와 실제 최종 저장 bytes를 검증한 뒤 필요한 bounded snapshot만 D3 fileID/content_revision/storage identity에 결합한다. receipt 없는 기존 등록과 알려진 receipt/digest 불일치의 등록 실패를 구분한다.
- 측정 등록은 prepare-copy/검증→root DB commit→원본 identity 조건부 cleanup 순서다. 등록 전용 function-scope dependency로 commit 실패를 성공 응답으로 보내지 않는다. rollback 원본 보존, commit 불확실/orphan 및 성공 후 cleanup 실패를 분산 원자성·자동 회수 보장으로 과장하지 않는다.
- 이후 source/read/projection은 D3 현재 권한·revision·binding을 재검증한다. 정정: D5 업로더 제한은 Port/app 계층이고 RLS는 lab-only다. 정상 viewer에게 D5 업로더 권한을 재요구하지 않는다. receipt ID·발급 provenance·parser version·digest/size·측정값은 보존하고 credentials/임시 경로/원문은 복사하지 않는다. receipt 정정·철회는 후속 invalidation 계약이 필요하다.
- 자동 측정 fact는 magic+parse 성공 format 네 가지(npy/netcdf/tif/hdf5)로 제한한다. 기존 file_name/kind·human_review와 loader/extractor를 분리하며 CRS/기간/변수/shape를 다른 의미로 승격하지 않는다. supported replace/delete는 즉시 stale이며 원장 밖 임의 storage 변조 탐지는 이 계약의 보장이 아니다.
- D4 구현 계약: retained lab/dataset revision marker 한 표로 최신 상태에 수렴한다. no-op은 증가0, 양끝 관계 변경은 양쪽 증가, unknown은 자기만 증가한다. 삭제 marker는 dataset FK 없이 남기고 제품 softdelete의 기존 계보 보존을 유지한다. 중간 event 재생이 필요하지 않아 별도 outbox는 추가하지 않는다.
- D4 쓰기 조립은 lab lock을 기존 자료/관계 row lock보다 먼저 획득하고 이후 endpoint를 재검사한다. 읽기 Port는 잠금 없는 단일 SQL snapshot이며 D3/AI가 D4 저장소를 직접 읽거나 쓰지 않는다. 누락·접근 불가를 빈 관계 revision1로 추정하지 않는다.
- issue/validate/read/projection은 서버가 조회한 D4 의존 revision을 검사하고 command 재사용에도 dependencies equality를 요구한다. D3 source별 처리 cursor와 재queue는 같은 TX, 탐색은 순환 sweep이며 실패/권한 취소에 성공 cursor를 남기지 않는다. 기존 tracked 사용자 실행만 연결하며 무인 권한은 확대하지 않는다. 세부 시험·파일·게이트는 실행 계획에 둔다.
- sweep는 LIMIT 전에 현재 viewer의 file/dataset RLS로 대상을 고른다. 고정 batch의 source key를 정렬·중복 제거해 모두 잠근 뒤 D4 revision과 원본 권한을 재확인하고 queue를 변경한다. queue 잠금 후 새 source lock을 취득하지 않는다. 의존 불일치는 기존 stale_source이며 파일 bytes revision을 꾸며 올리지 않는다.
- 지속 무인 실행의 delegation/enrollment는 아직 없으며 사용자 정책 결정 전이다. 기존 worker 로그인 이름·service bearer는 tracked session의 대체물이 아니다. 허용된 단발 실행은 정상 세션의 호출 수명 안에서만 수행하며 별도 장기 자격·자동 갱신을 임의 도입하지 않는다.
- 먼저 기존 core-ai seam/공통 schema/codegen 소비자를 확인한 후 신규 내부 계약을 추가한다. 현재 동결된 이벤트 enum을 문서 승인만으로 변경하지 않는다.
- 권한 principal 전달·운영 CLI 로그인·source grant 저장/만료의 구체 adapter는 위 행위 규칙을 만족하는 구현으로 제공하고 음성 시험을 통과해야 한다.
- 이 문서는 사용자에게 기술 선택을 반복 질의하기 위한 문서가 아니다. 합의한 범위의 구현 세부는 개발자가 정하되 정책·권한 확대가 필요하면 그 차이만 검토한다.
- 초기 문서 이후 사용자 "그럼 이제 해"로 로컬 구현이 승인되었다. 현재 증분·실측·잔여 작업은 실행 계획에서 추적한다. 이 문서 자체는 운영 활성화·통합·push·모델 호출 권한을 추가하지 않는다.
