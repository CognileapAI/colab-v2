# sessions — 작업 단위별 지시서

파일명은 WU 코드와 같다. 세션 하나 = WU 하나.

| 파일 | WU | 상태 |
|---|---|---|
| `R1.md` | 레포 초기화 마무리 — 첫 세션 | ✅ 닫힘 |
| `P0.md` (+`P0-schema.md`·`P0-core-api.md`·`P0-rls-proof.md`·`P0-frontend.md`) | 공통 기반 (에픽 0단계) | ✅ 닫힘 — 레인별 산출 보고 4종 포함 |
| `P1.md` (+`P1-api-report.md`·`P1-fe-detail-report.md`) | 카탈로그 + 데이터셋 상세 헤더 | ✅ 닫힘 — 네 레인 전부 + staging 배포 green |
| `P2.md` | 업로드·계보 확정·S-08 | ⛔ 착수 불가 — `STOP-1`(→D2c)·`STOP-4`(`DR-13`) 이 각각 막는다 |
| `P3.md` ~ `P8.md` | 시각화 → 검색 → 프로젝트 → 승인 → 대시보드 → 적용표 | ⬜ 미작성 — 착수 직전에 쓴다 |
| `K1.md` | 온톨로지 스키마 | ✅ 닫힘 — 시드 테이블 3개, `db/ai` `0002_k1_ontology` |
| `K2.md` | 온톨로지 시드 적재 | ✅ 닫힘 — 적재 22행, 미커버 0 |
| `K3.md` ~ `K5.md` | 계보 제안 · 검색 · 원장 | ⬜ 미작성 |
| `D1.md` | 도메인 확정 | ✅ 닫힘 — 배정표 `DOMAINS §7` (10개 전부 Ted · 판단 근거는 정본, `§9-㊴`) |
| `D2.md` | **계약 동결 — 공통 스키마** | ✅ 정의 21종 |
| `D2-fe-core.md` | seam FE↔core (op 34) | ✅ |
| `D2-ai-viz.md` | seam core↔ai (op 2) · core↔viz (op 5) | ✅ |
| `D2-events.md` | async 봉투 core↔pipeline (이벤트 7종) | ✅ · 게이트 사각지대 → **D2b** |
| `D2-gates.md` | `contract-lint` · `contract-breaking` | ✅ selftest 15 케이스 green |
| `D2b.md` | 이벤트 계약 게이트 | ✅ 닫힘 — `event-lint`·`event-breaking`·`event-selftest` 33 케이스 |
| `D2c.md` (+`D2c-ted-approval.md`·`E04-step-op-map.DRAFT.md`) | 계약 개정 — `fe-core` 를 이벤트 seam 에 맞춘다 (`〈54〉`·`DR-7` 이행) | 🟧 **실행됨 C1~C3 (2026-08-23) · 동결 대기** — fe-core 34→45 op · `seam-consistency`+㉠㉡ green. 잔여: ㉢ Ted 승인(→동결) · D2c-api 501 라우트 11건 · 커밋/리뷰/staging 실측 |
| `D3.md` (+`D3-boundary.md`·`D3-db.md`) | 경계 강제 장치 | ✅ 닫힘 — 게이트 6종 배선, 잔여 RLS 실효 증명은 D3b 로 완결 |
| `D3b.md` | RLS 실효 증명 게이트 승격 | ✅ 닫힘 — `rls-effect`, red fixture 18/18 |
| `I2.md` | walking skeleton staging 배포 | ✅ 닫힘 — 5개 단위 헬스 green, 무중단 롤백 증명 |
| `I3.md` | 배포 자동화 | 📋 지시서 초안 — `[정본 무근거]` 7건 Ted 답 대기 |
| `I0.md`·`I1.md`·`I4.md`·`I5.md` | AWS 계정 → IaC → 운영 → prod | ⏸/⬜ 미작성 (I0·I1·I5 는 `㊻` 보류) |
| `C1.md` ~ `C4.md` | 푸시 확인 · 이관 · 지식 추출 · 방법론 추출 | ⬜ 미작성 — T-C 는 지금 열지 않는다 |
| `G1.md` | **E-00 전달 패키지 재빌드 (DataModel v1.8 · Policy v1.4)** | ✅ 닫힘 — 실측 결과 재빌드가 아니라 **최신성 검사기 + 기록 정정**이 본체 |
| `G3.md` | **E-01 권한 원칙/적용표 분리** | ✅ 닫힘 — 산출 `PERMISSION-PRINCIPLES.md` (P-1~P-34) |
| `G4.md` | **미배치 화면 단계 배정** | ✅ 닫힘 — 순서표 반영 완료 |
| `G5.md` | **DataModel v1.8 ↔ 스키마 대조** | ✅ 닫힘 — 산출 `DATAMODEL-BASELINE.md` |
| `G7.md` | **기획 SSOT 통합** | ✅ 닫힘 — 정본 폴더 하나로 완결. 깨진 링크 38 → 1 |
| `G8.md` | **온톨로지 범위 합의** | ✅ 닫힘 — `㊸` 승인 완료, 산출 `ONTOLOGY-SCOPE.md` |
| `IS2.md` | **터널 라우팅 IaC화** | ✅ 닫힘 — apply 완료, `terraform plan` = `No changes.` |
| `IS3.md` | staging 백업 체계 | ✅ 닫힘 — 백업·복원 1회, fail-closed fixture 11건 red |
| `IS4.md` | terraform state 보관 | 🟧 절차·리허설 완료 — 잔여 2건(마지막 apply · 맨몸 호스트) |
| `SEAM-AUDIT.md` | 네 seam 간 정합 전수 감사 (`DR-7` 입력) | ✅ 감사 기록 — D2c 의 입력 |
| `OPEN-ITEMS-RESOLUTION.md` | `SEAM-AUDIT §6` `[정본 무근거]` 4건 정리 | ✅ 정리 완료 — D2c 의 입력 |
| `DATA-PROCESSING-HARVEST.md` | 구세대 데이터 처리 지식 대조 | ✅ 기록 — D5 의 입력 |
| `NIGHT-20260823.md` | 밤샘 진행 계획 (2026-08-23) | ✅ 기록 — 레인 배분 정본, 종료됨 |

> S1 은 세션 파일이 없다 — 산출이 곧 `../SEED-DATA.md` 다(✅ 닫힘).

## 지시서를 쓰는 시점

**한 WU를 착수하기 직전에 그 지시서를 쓴다.** 미리 다 써두지 않는다 — 앞 WU의 결과가 뒤 지시서의 입력이라서, 미리 쓰면 대부분 틀린 채로 굳는다.

## 지시서에 반드시 들어가는 것

`WORK-UNITS.md §1`의 네 항목 + 두 가지.

1. **진입조건** — 없으면 시작이 헛일이 되는 선행 산출물
2. **범위** — 이 WU가 건드리는 도메인과, **건드리지 않는 것**
3. **산출물** — 파일·커밋·결정 기록
4. **완료 판정(오라클)** — 기계가 green/red를 말하는 것
5. **정본 참조** — 이 WU가 근거로 삼는 기획 문서의 정확한 위치
6. **함정** — PoC·v1에서 같은 자리에 있었던 실패
