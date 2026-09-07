# advisor ② — WU-B4 · lane p3-visibility-3 · d4f4992 (base 3e2dcd8)

For:
- 두 표 CHECK·매핑·NO FORCE 창·소유자 롤 드리프트 오라클(㈑-b·㈑-c 대조군)이 0016 advisor ② 교훈을 그대로 적용했고, 승인 승격·내림 만료가 요청=트랜잭션(`deps.scoped_db`) 안에서 만료→상태 순서로 선다. 12 게이트 green · 871/922 시험 · 계약 파괴 0.
- 접근 판정 함수·`body_access` 정책 무수정이 시험(C-⑴·C-⑵ · `test_designated_rides_the_grant_path`)으로 증명된다. 폐기 비용 = 마이그레이션·계약·FE 3층 재작업.

Against:
- WU 의 완료 조건 「`잠김` ∧ 유효 grant ≥1 이 **어느 시점에도** 0건」을 서버가 잠금 없이 두 쓰기 경로에만 맡겼다 — 승인(T1: INSERT grant → UPDATE state) 과 내림(T2: UPDATE grants → UPSERT state) 이 겹치면 T2 의 grant 만료가 T1 의 미커밋 grant 를 못 보고, 상태 UPSERT 는 T1 커밋 뒤 `잠김` 으로 덮어 불변식이 깨진다. 「어느 시점에도」는 현재 코드로 참이 아니다.
- 등록 화면이 `accessState` 를 **늘** 보낸다(`UploadModal.tsx` 「늘 실린다」). 서버 주석이 스스로 경고한 「기본값을 복사해 넣으면 연구실 기본값을 바꿔도 옛 값으로 굳는다」를 클라이언트가 실행한다. 연구실 기본값 `잠김` 인 랩에서 파일만 올린 사람의 데이터셋이 `열림` 으로 저장된다 — 종전(NULL→기본값 `잠김`)보다 **더 열리는** 행동 변화이고 PRD-11 「NULL = 연구실 기본값(현행 의미 유지)」와 어긋난다.

Verdict: approve-with-changes — ㊀·㊁ 병합 전 필수, 나머지는 후속.

## ① revision 체인
- `0017_rb4_access_state_3` ← `0016_rb2_dataset_variable`, head 1개(파일 목록·`migration-single-head`). 22자.
- downgrade: 두 표 `지정 공개→잠김` UPDATE(각 NO FORCE 창) → CHECK 2값. `default_visibility='지정 공개'` 도 처리됨. 손실 명기됨. ⚠ downgrade 창엔 FORCE 복구 단언이 없다(upgrade 만 있음).
- DO 단언 3종은 NO FORCE 창 안 — 소유자 롤은 NO FORCE 시 RLS 비적용이라 실제 행을 읽는다. ㈑-c 가 창 제거 시 red 임을 기계로 증명. 단언 ⑵가 매핑 후 `잠김 ∧ 유효 grant ≥1 = 0` 을 센다.
- 「유효」= `expires_at > now()` 단일 정의. 철회 컬럼은 없음(만료로만 끊음) — 런타임·정책·이관 셋이 일치.
- schema.sql 두 CHECK 동기. ⚠ `schema.sql:179` 주석 「잠김일 때만 쓰인다」가 이제 거짓(`지정 공개` 에서 쓰인다).

## ② 「main 과 동일」·게이트
- 문구 사용 없음. 게이트·gates/ 파일 변경 0(diff --stat). `COLAB_APPLIED_DB_URL_PLATFORM` DB 에 `alembic upgrade head` = schema-diff 의 정의상 「적용 DB」를 올린 것. 조작 아님. 절차가 게이트·RESTART 밖인 것은 B2 후속과 동일 → 게이트 승격 요구(3회째 반복: drift.sh 미게이트 · alembic 미등재 · applied DB 절차).

## ③ intent 대조 (R-B-1 §5 WU-B4 · 수용 기준 6)
| 기준 | 판정 | 근거 |
|---|---|---|
| 이관 후 유효 grant 잠김 → 지정 공개 · 접근 양성·음성 | 충족 | `0017-existing-rows-assertions.sql` ⑴·⑸(비소유자 롤 t_app2) · ㈑-b red |
| 승인 → 지정 공개 ＋ 본체 열림(같은 tx) | 충족(결과) · **경합 미검증** | `test_approval_flips_…` · 트랜잭션 = 요청 1건(`scoped_db`) |
| 지정 공개＋grant 2 → 내림 → `2명` ＋ 2건 만료 | 충족 | 서버 `test_lowering_…` · FE §4 |
| 어느 시점이든 잠김 ∧ 유효 grant = 0 | **조건부** | 직렬 경로만 시험. 동시성 경로 미보장(아래 ㊀) |
| 잠김 데이터셋 요청 접수(0010 회귀) | 충족 | `test_a_locked_dataset_still_accepts_…` ＋ 지정 공개 갈래 |
| cross-tenant 0건 | 충족 | `test_another_lab_sees_no_access_rows`(대조 A ≥2) · C-⑶ · ⑹ |
- PRD-11 원문 8기준 중 라운드가 뺀 2건: 「나만 보기로 등록 → 다른 구성원 본체 거절」 직접 시험 없음(지정 공개 음성으로 간접) · 「고르지 않고 등록 → 기본값 적용 ＋ 화면 표시」 서버만(FE 는 고르지 않을 수 없다 → ㊁).
- 초과: `DatasetDetail.activeGrantCount`(required · 응답 전용 · oasdiff 비파괴). PRD-11 「{n}명」 되묻기가 저장 **전**에 서야 하므로 필요조건 — 수용. 조건: 〈N〉·C20 원장에 20차 확장분으로 기재(§5-㉰ 목적 단위 판정). `AccessGrant.accessState` = 「decideAccessRequest 응답에 상태」 라운드 문면 그대로. `updateDataset.accessState` = 라운드 「DatasetUpdate 에 accessState」 ＋ 「소유자가 내리면」 → 범위 내.
- `LabDefaultVisibility=지정 공개`: PRD-11 ⚠ 가 「0건으로 시작 = 사실상 나만 보기」로 허용한 상태. 가드 없음이 PRD 와 일치. 단 `LabInfoPanel.tsx:30` 가 2값이라 고를 수 없고, 주석 「계약이 두 값으로 고정한다」는 이제 거짓 — 후속.
- FE 문면: 표기 3값·기본 선택 rev1 축자, 뜻 3줄 PRD 표 축자(`d2_dataset_access_grant`→「허용 목록」치환), 되묻기 PRD 전이표 축자. 지어낸 문면 없음. ⚠ 세션 노트 「셀렉트 아래 한 줄이 0건 시작 사실을 적는다」는 과장 — 실제 노트 문면은 「허용 목록에 오른 사람만. 만료 = …」이고 0건 시작 언급 없음.
- 존치·A3R/A9R/A12R/B3: register-steps 41행 증보 ＋ 922 green. 이상 없음.

## Risks
1. **approve∥lower 경합** → `잠김 ∧ 유효 grant` 성립(READ COMMITTED · 잠금 없음). 완료 조건 문면 「어느 시점에도」 미달.
2. **UploadModal 이 `accessState` 를 항상 전송** → UI 등록분은 연구실 기본값 경로가 영구 소멸 · 기본값 `잠김` 랩에서 `열림` 저장(개방 방향 회귀).
3. 이관 빈틈: 상태 행 NULL/없음 ＋ 연구실 기본값 `잠김` ＋ 유효 grant → 이관 후 실효 `잠김` 인데 허용자 있음. 라운드 spec(NULL→NULL) 의 빈틈이라 레인 이탈은 아님. 드리프트 시드가 기본값 `열림` 이라 미측정.
4. 내림 권한 = `_require_upload_edit`(업로드·편집 스위치 보유자 전원). PRD 문면 「소유자」보다 넓음 — 남의 데이터셋 허용 목록을 편집자가 전부 끊을 수 있다. 기존 updateDataset 규칙 재사용이라 설계 판정 필요.
5. `_EXPIRE_GRANTS` 가 `expires_at = now()` 로 미는데 CHECK 는 `expires_at > approved_at` — 같은 tx 시각(now() 동일)에 승인된 줄이 있으면 CHECK 위반 500. 현 코드에선 두 경로가 같은 tx 에 없어 이론상만.

## Missed
- 동시성 시험 0건 · 비소유 편집자의 내림 시험 0건 · 「나만 보기 등록 → 타인 본체 거절」 직접 시험 0건.
- downgrade FORCE 복구 단언 없음. `schema.sql:179` 주석 낡음. `LabInfoPanel.tsx:29-30` 주석·배열 낡음.
- 세션 노트 「셀렉트 아래 한 줄」 주장과 실제 문면 불일치(위).

## Fixes
- **㊀ 병합 전 필수** — `d2_access.set_access_state` 와 `decide_access_request` 첫 문장에 데이터셋 단위 잠금: `SELECT pg_advisory_xact_lock(hashtext(:dataset_id))`(행 없음 케이스도 덮는다). 회귀 시험 1건: 두 세션에서 승인·내림 교차 후 불변식 셈 0.
- **㊁ 병합 전 필수(판정)** — 택1 후 기록: (a) UploadModal 이 사용자가 셀렉트를 **건드리지 않으면 열쇠 생략**(NULL → 연구실 기본값 · 「현행 의미 유지」 충족) ＋ 초기 표시를 `lab.defaultVisibility` 라벨로; (b) 「UI 등록분은 연구실 기본값을 따르지 않는다」를 PRD-11·〈N〉 에 명시 결정으로 기재. 현 상태(암묵적 (b))로는 병합 불가.
- 〈N〉 등재 문면에 `DatasetDetail.activeGrantCount` 신설을 20차 확장분으로 적는다.
- 후속(병합 후): `*-drift.sh` 게이트 승격(3회 반복 항목) · `alembic` requirements 등재 · applied-DB 절차 RESTART 등재 · `LabInfoPanel` 3값＋0건 안내 · schema.sql:179 주석 · 이관 빈틈 3 에 대한 라운드 판정(NULL→NULL 유지 또는 기본값 `잠김` 랩 한정 보정 마이그레이션) · 내림 권한 소유자 한정 여부 판정.
