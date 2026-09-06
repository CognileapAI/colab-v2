# 레인 `p3-toast-copy` — WU-A13R 공통 토스트 ＋ 문면 21행 (PRD-32 · PRD-43)

- 라운드 R-A′ · 통합 `integration/r-a2` · 기점 `93329a6` · 계약 0 · 스키마 0 · 마이그레이션 0.
- 근거 = `dev-package/prd/rounds/R-A2.md §2-①` · `dev-package/prd/specs/R-A2.md` · `dev-package/intent/2026-09-06-r-a2.md` · PRD-32(`:759`) · PRD-43(`:994`).

---

## 1. 결론

| 완료 조건(대장 축자) | 판정 | 근거 |
|---|---|---|
| 21행이 전부 코드에 있다 | 충족 | `frontend/src/components/common/toastCopy.ts` · `COPY_ROW_IDS` 21개 단언 |
| 하드코드 중복 0건(한 곳에서 온다) | 충족 | `src/**/*.{ts,tsx}` 전수 `?raw` 글롭 훑기, 중복 목록 `[]` |
| 토스트가 스스로 사라지고 포커스를 뺏지 않는다 | 충족 | `frontend/src/components/common/Toast.tsx` · 가짜 시계 시험 ＋ `activeElement` 시험 |
| `F-11`·`D-13` 의 건수가 보간값이다 | 충족 | `datasetCreated(n)` · `bodyPieceHead(n)` — 서로 다른 인자로 다른 값 단언 |
| `D-07` 축약 표기가 `2025-06 ~ 09` 다 | 충족 | `formatPeriodByUnit` 에 단위 `월` 해 겹침 생략 추가 |

---

## 2. RED 선실측 → GREEN

| 시험 파일 | RED | GREEN |
|---|---|---|
| `frontend/test/toast-copy-20260906.test.tsx` | 수집 자체 실패(모듈 부재) → 모듈 신설 뒤 판정 red **2건** | 14건 |
| `frontend/test/ext-mixed-toast-20260906.test.tsx` | 수집 자체 실패 → 모듈 신설 뒤 판정 red **1건** | 3건 |

RED 로그 축자 3줄 —

```
AssertionError: expected '2025-06 ~ 2025-09' to be '2025-06 ~ 09' // Object.is equality
AssertionError: expected <p class="up-toast" …(3)></p> to be null
AssertionError: expected [ …(2) ] to deeply equal []
```

- 1행 = `D-07`. 단위 `월` 이 해를 줄이지 않았다.
- 2행 = 종전 인라인 안내가 **스스로 사라지지 않았다**.
- 3행 = 하드코드 중복 2건 검출(그중 1건은 아래 §5-㈎ 의 오검출이었다).

---

## 3. 21행의 자리와 축자 원천

- 자리 = `frontend/src/components/common/toastCopy.ts` **한 곳**. 표 자체도 같은 파일의 `COPY_ROWS` 에 있고, **문자열을 다시 적지 않고 위 상수를 참조한다** — 파일 안에서도 두 벌을 만들지 않는다.
- 공통 토스트 = `frontend/src/components/common/Toast.tsx` ＋ `frontend/src/components/common/toast.css`.
- PRD-43 표가 문면을 확정하지 않은 두 행은 **표가 가리키는 rev2 원문**에서 축자로 떴다(개발 세션이 짓지 않았다).
  - `S-04` — 표는 `…` 로 줄였다. 원문 `10_적용전/업로드_계보_260905_rev2_이태헌.html` 의 `toast('…')` 축자 = `이 데이터보다 높은 단계라 연결할 수 없어요. 분류에서 가공 단계를 확인해 주세요`.
  - `E-07` — 표는 「편집 토스트 3종」이라고만 적었다. 원문 축자 3종 = `편집 모드예요. 값을 고치고 저장을 누르세요` · `편집 내용을 저장했어요` · `편집을 취소했어요`(원문 `toast(save?'편집 내용을 저장했어요':'편집을 취소했어요')`).
- `V-01` 뷰어 머리는 **좌표계가 앞에 붙는 보간값**이다(원문도 `d.meta.crs + ' · PNG + 경계 좌표'`). 고정 문자열로 적으면 남의 좌표계를 그린다 — `viewerHead(crs)` 로 뒀다.
- `X-05` 는 `S-05` 와 **같은 문면**이라 상수를 다시 만들지 않고 되보냈다(`PICK_TARGET_FIRST_IN_EDIT = PICK_TARGET_FIRST`).

## 4. 하드코드 중복 제거

- 제거 **1건** — `frontend/src/components/upload/FileDropCard.tsx` 의 `MIXED_EXTENSION_NOTICE` 문자열 선언. 문면은 `toastCopy.ts` 로 옮기고 그 자리는 **되보냄**(`export { MIXED_EXTENSION_NOTICE }`)만 남겼다 — 종전 부르는 쪽이 끊기지 않는다.
- 함께 옮긴 것 — 종전 인라인 `<p class="up-toast">` 를 `<Toast>` 로 바꾸고, `upload.css` 의 `.up-toast` 규칙을 `common/toast.css` 의 `.toast` 로 옮겼다(치수·색 동일, 새 모양 발명 0). 규칙을 양쪽에 두면 한쪽만 고쳐진다.
- 사라질 때 `onDismiss` 로 부르는 쪽 상태를 함께 내린다 — 안 내리면 **두 번째 혼합 놓기에서 다시 뜨지 못한다.**

## 5. 판정이 갈릴 수 있는 자리 (Ted 판정 대상 — 이 레인이 정하지 않았다)

### ㈎ 「하드코드 중복」을 부분 문자열로 세지 않았다

- 부분 문자열로 세면 `frontend/src/components/members/MemberPermissionGrid.tsx:67` 의 `편집을 취소했어요. 권한은 그대로예요` 가 `E-07` 의 `편집을 취소했어요` 에 걸린다.
- 그러나 **같은 문장이 아니다.** 그것을 `E-07` 상수로 바꾸면 무관한 두 자리가 한 문면에 묶이고, PRD-43 이 상세 편집 문면을 고치는 날 연구실 권한 화면이 함께 바뀐다.
- 그래서 판정은 **따옴표 안쪽 전체가 같을 때만 중복**으로 뒀다(`toast-copy-20260906.test.tsx` 의 `literal()`). 이 판정이 틀렸다면 지시를 받아 고친다.

### ㈏ 문면이 다른 「같은 자리」 2건을 이 레인이 고치지 않았다

라운드 파일 §2-① 축자 「각 문면은 그 자리를 담는 WU 가 호출한다」에 따라 **호출 배선은 하지 않았다.** 그런데 아래 두 자리에는 PRD-43 과 **다른 문장**이 이미 하드코드로 서 있다. 같은 문자열이 아니라 중복 검사에 걸리지 않고, 바꾸면 사용자가 보는 말이 달라진다.

| 행 | 현재 코드 | PRD-43 축자 | 차이 |
|---|---|---|---|
| `J-12` | `RegisterArea.tsx:615` `여기서는 유형과 이름만 받아요. 프로젝트 화면에서 나중에 채우면 돼요.` | `유형과 이름만 받아요. 나머지는 프로젝트 화면에서 채워요.` | 뜻은 같고 문장이 다르다 |
| `N-11` | `LineageSection.tsx:17` `가공 방식은 화살표 라벨 · 데이터 상자를 누르면 그 상세로 가요` | `각 데이터를 누르면 그 상세로 가요` | PRD 문면이 **「가공 방식은 화살표 라벨」 안내를 잃는다** |

- 판정 필요 = ⑴ 그 자리를 담는 WU(`J-12` = 프로젝트 영역 · `N-11` = 상세 계보)가 PRD 축자로 바꾸는가 ⑵ 아니면 현재 문장을 정본으로 올리고 PRD-43 표를 고치는가.
- 이 레인은 **아무것도 바꾸지 않았다** — 문면 폐기는 판정 사항이고(`rounds §1` 존치 규칙 결), 범위 확대 금지(`CLAUDE.md §5`)에 걸린다.

### ㈐ `D-07` 축약을 단위 `월` 에만 걸었다

- PRD-43 수용 기준 축자가 「단위 `월`」을 지목한다. 단위 `일` 에 같은 생략을 걸면 PRD-18 수용 기준 시험(`test/interval-period-20260906.test.tsx:311` — `2025-06-01 ~ 2025-06-30`)이 red 가 된다. **그 시험을 고치지 않았다**(존치).
- 단위 `년`·`시`·`분`·`초` 의 축약 규칙은 **재지 않았다**(`[미측정]`).

## 6. 서버(core-api) — 이번 레인의 신규 변경 0건

- PRD-32 의 서버 방어선(조각 확장자 2종 이상 → 400)은 **부모 WU-A13 이 이미 세웠고 `main` 에 있다.**
  - 판정 자리 = `services/core-api/src/colab_core/app/routes/ingestion.py:531-535`(등록 전환 `createDataset` 안). 확장자 함수 = 같은 파일 `_extension_of`(`:391`, 소문자 기준).
  - **조각(본체)만 센다** — 기준 격자 파일은 확장자가 달라도 막지 않는다.
- 그 규칙을 거는 검사 = **게이트 `service-tests-core-api`**(`services/core-api/tests/test_ext_mixed.py`, 4건 — 2종 400 · 1종 201 · `.NC`/`.nc` 동종 201 · 격자 제외 201). 게이트 밖에만 있는 검사가 아니다.
- 그래서 이 레인은 **서버 코드도 서버 시험도 새로 쓰지 않았다.** 같은 규칙의 시험을 한 벌 더 만들면 중복이고, 없는 red 를 지어내는 것이 된다.

## 7. 기존 데이터 — 조각 확장자 2종 이상인 데이터셋 **0건**

- 대상 = staging 스택의 `colab_platform`(컨테이너 `colab_v2_staging_pg`). **읽기 전용**으로만 접촉했다 — `SET default_transaction_read_only = on;` ＋ `SELECT` 만. DDL·UPDATE·DELETE 0, 스택 정지 0, 접속 문자열·비밀번호 출력 0.
- 방법 = `d3_file` 에서 `kind = '본체'` 행만 데이터셋별로 묶고, 파일명 꼬리 확장자를 소문자로 접어 서로 다른 값의 개수를 센다(서버 `_extension_of` 와 같은 규칙).
- 실측 = 데이터셋 **14** · 파일 **133** · 2종 이상 **0건**.
- green-by-skip 이 아님을 보인 것 = 데이터셋별 확장자 집합을 그대로 뽑아 `nc`·`gz`·`tif`·`hdf`·`npy` 가 실제로 추출되는지 확인했다(전 14행이 1종).
- ⚠ **재지 않은 축** — dev·prod 의 같은 계수는 `[미측정]`. staging 은 리허설 자리이고 이 값은 그 스냅숏이다. 고친 것·지운 것·쪼갠 것 **0건**(PRD-32 축자).

## 8. 게이트 (마지막 커밋 뒤 1회 · 배출처 `dev-package/reports/R-A2/p3-toast-copy/`)

| 게이트 | green | red(판정) | red(준비) |
|---|---|---|---|
| `frontend-typecheck` | 1 | 0 | 0 |
| `frontend-test` | 1 | 0 | 0 |
| `service-tests-core-api` | 1 | 0 | 0 |

- `frontend-test` 실측 = 시험 파일 **59** · 통과 **809** · 실패 0(종전 57 파일 · 792 시험 → 이번에 시험 파일 2 · 시험 17 증가).
- 전수 `all` 은 돌리지 않았다 — 라운드 끝 1회는 오케스트레이터 몫이다(`rounds §3-㉲`).

## 9. 이번에 하지 않은 것

- 21행 중 `MIXED_EXTENSION_NOTICE`(PRD-32) 외의 **화면 배선 0건** — 라운드 파일 축자대로 그 자리를 담는 WU 몫이다.
- `contracts/` 무접촉 · Alembic head `0013` 무접촉 · `work-items.yaml` 무접촉 · `PLAN-SoT §9` 무접촉 · 〈N〉 발급 0.
- 존치 6종 무접촉(컴포넌트·훅·서버 경로·회귀 시험). PRD-34 닫기 문면 미작성(WU-A9R). A6 달력 팝오버·확장보기 오버레이 미착수(WU-B3).
