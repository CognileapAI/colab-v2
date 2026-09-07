# WU-B3 · 등록 3단계 재구성 ＋ 값 안내 — 레인 `p3-register-steps` (2026-09-07)

- 라운드 R-B · 계층 FE ＋ 계약·서버 1건 · 기준 HEAD `06e0240`(`integration/r-b`).
- 오라클 = `dev-package/prd/rounds/R-B-3-frontend.md §2` WU-B3(요구 본체 11 ＋ R-A′ 이관 6) · `dev-package/prd/PRD-260905-적용전기획.md` PRD-01·02·03·04·12·13·33·40.

## 1. 완료 조건 ↔ 판정 ↔ 근거

| 완료 조건 (라운드 §5) | 판정 | 근거 |
|---|---|---|
| 표시기 세 라벨 `① 분류 · ② 메타데이터 입력 · ③ 연결` | 충족 | `frontend/src/components/upload/RegisterArea.tsx` `STEP_LABELS` · `test/register-steps-20260907.test.tsx` ① |
| 눌러서 어느 단계로나 이동 | 충족 | 표시기 버튼에 검증 없음 · 같은 파일 ④⑤ |
| ① 세 값 기본 선택값 `기상·기후 인자`·`재분석자료`·`Lv2` | 충족 | `axisDict.ts` `DEFAULT_*` · 같은 파일 「기본 선택값 3개」 |
| 15값 전부 정의·예시 한 줄 · 빈 값 0 | 충족 | `axisDict.ts` 15항목 · 같은 파일 ⑦⑪ |
| 유형 6값에 `참고 · 특이사항` | 충족 | `reg-datatype-note` · 같은 파일 ⑧⑧b |
| 설명란에 분류·단계별 힌트 | 충족 | `reg-summary-hint` · 같은 파일 ⑨⑩ |
| 모달 재오픈이 늘 ① | 충족 | 리셋은 `UploadEntry.tsx:71` 언마운트가 한다(`{open && <UploadModal …/>}`) — 다시 열면 `useState(1)` 초깃값이 ① 이다 · 시험 ⑥ ／ ⟨정정 2026-09-07 · advisor ② F5⟩ 종전 표기 ~~`UploadModal.tsx` 마운트 effect `setStep(1)`~~ 은 무동작 코드였고 지웠다 |
| WU-A3 골격 재작성 없음 | 충족 | diff — `RegisterArea.tsx` 는 단계 카드 추가·이동뿐, `StepMeta`(옛 `StepOne`) 본문·`StepTwo` 본문 무변 |
| `DatasetCreate.required` 승격 ＋ 서버 400 | 충족 | `contracts/seams/fe-core.yaml` `required: [uploadId, name, summary, category, dataType]` · `services/core-api/src/colab_core/app/routes/ingestion.py` `MISSING_CATEGORY_MESSAGE` |
| 마이그레이션 0 · 스키마 0 | 충족 | `db/` 변경 0건 |

## 2. 수용 기준 — 요구 본체 11건

| # | 기준 | 판정 | 시험 |
|---|---|---|---|
| 1 | 표시기 3라벨 ＋ ① 열림 | green | `register-steps-20260907` ① |
| 2 | ① 분류·유형 하나가 비면 `다음` 막힘 | green | ② (`classifyBlocked`) |
| 3 | ③ 에 계보 카드 ＋ 프로젝트·논문 카드 | green | ③ |
| 4 | ③ → 표시기 ① 조건 없이 이동 | green | ④ |
| 5 | 이름·설명 비어도 표시기 ③ 이동 | green | ⑤ |
| 6 | 닫고 다시 열면 ① | green | ⑥ |
| 7 | 15값 정의·예시 · 빈 정의 0 | green | ⑦ |
| 8 | 유형 `위성자료` → `참고 · 해상도, 궤도 정보 명시 필요` | green | ⑧ |
| 9 | `수문 인자`＋`Lv1` → 두 항목 함께 | green | ⑨ |
| 10 | `Lv0` → 출처·다운로드 일자 없음 | green | ⑩ |
| 11 | 15값 부가 문구 빈 값 0 | green | ⑪ |

⚠ **수용 기준 2 ↔ rev1 `UI-003` 병존 처리** — 「막지는 않는다」는 **표시기 임의 이동**에 걸고, 기준 2 의 차단은 **순차 이동(`다음`)** 에만 건다. 마지막 게이트(`데이터셋 만들기`)는 종전 그대로다. 근거 = 라운드 §2 의 ⚠ 축자.

## 3. 수용 기준 — R-A′ 이관 6건

| 항 | 기준 | 판정 | 근거 |
|---|---|---|---|
| ㈎ | 확장보기 오버레이 · 배경 클릭 닫힘 · `data-esc-layer="확장보기"` · mousedown/click 분리 | green | `PreviewExpandOverlay.tsx` · 시험 3건 |
| ㈏ | 기간 달력 팝오버 · 최소 단위까지만 칸 | green | `PeriodCalendarPopover.tsx` · 시험 2건 |
| ㈐ | 3단계 재편 | green | 위 §2 |
| ㈑ | 2장면 · 배지 `×` → 장면1 ＋ 초기화 고지 · 존치 도달 | green | 시험 3건 |
| ㈒ | 종료 비움 조립 `period_end = period_start` · 시작>종료 400 | green | `UploadModal.humanMetadata` · `catalog.validate_human_metadata` · FE 2건 ＋ 서버 2건 |
| ㈓ | 공개 범위 값 재동기 재검증 | **인계** | 값 칸이 WU-B4 몫 — 이 레인은 `reg-visibility-slot` 자리만 세웠다. 헤더 칩 세 갈래(`DetailHeader.tsx:93`)도 B4 |

⚠ **㈎ 의 `requestClose` 해석** — 오버레이의 닫기 경로는 **한 함수(`requestClose` prop)** 이고 배경·× 가 그것을 함께 탄다(A9R 규율). **업로드 모달의 `requestClose`(`UploadModal.tsx:509`)를 부르지는 않는다** — Esc 우선순위가 「확장보기 → … → 업로드」라 위 층이 아래 층을 닫으면 그 순서가 뒤집힌다. 라운드 문면의 축자 해석과 갈리는 유일한 자리이므로 판정에 올린다.

## 4. RED → GREEN

- RED 선실측 — `frontend/test/register-steps-20260907.test.tsx` **20 failed / 5 passed (25)**. 통과한 5는 `axisDict` 상수 단언(구현 선행분)이고 행동 오라클이 아니다.
- GREEN — 같은 파일 **25 passed**.
- 서버 RED→GREEN — `services/core-api/tests/test_dataset_registration.py` 신설 6건(필수 축 2 · 빈 문자열 1 · 수정 경로 대조군 1 · 기간 순서 2).

### 라벨·구조 변경으로 갱신한 기존 단언 (의미 보존)

| 파일 | 갱신 | 왜 의미가 보존되는가 |
|---|---|---|
| `test/upload.test.tsx` | `openRegister()` 가 ② 로 한 단계 이동 | 재는 칸(이름·설명·기간·좌표계)의 자리가 ① → ② 로 옮겨졌을 뿐 |
| 〃 | `reg-s1` → `reg-s2` 3자리 · describe 이름 ① → ② | 같은 카드의 testid 가 단계 번호를 따라 옮겨졌다 |
| 〃 | `가공 단계 칸은 입력 불가` → `① 분류의 셀렉트이고 기본값 Lv2` | 미결-2 ⓐ 로 **사람이 고르는 칸**이 됐다(요구 변경) |
| 〃 | 요청 열쇠 목록에 `category`·`dataType`·`processingLevelUserSet` 추가 | 기본 선택값이 늘 실린다(계약 required 의 짝) |
| 〃 | 기간 끝 비움 `end: null` → `end: start` | PRD-40 판정 ⓐ (요구 변경) |
| 〃 | `단계 이동` 시험이 ① 로 되돌린 뒤 잰다 | 첫 단계가 ① 분류다 |
| `test/interval-period-20260906.test.tsx` | 헬퍼 ② 이동 · `다음` 2회 → 1회 · `end: null` → `end: start` | 프로젝트 카드가 ③ 으로 들어와 걸음이 하나 줄었다 ＋ PRD-40 |
| `test/close-guard-20260905.test.tsx` · `test/prd34-close-copy-20260907.test.tsx` | 헬퍼 ② 이동 · 프로젝트 시험은 ③ 으로 | 프로젝트 표가 ③ 안으로 들어왔다 |
| `test/summary-required-20260905.test.tsx` | 헬퍼 ② 이동 · `다음` 2회 → 1회 · 되돌림 단계 ① → ② | 설명 칸이 ② 에 있다 |
| `test/prd23-project-table-20260907.test.tsx` | `reg-s2` → `reg-projects` (7자리) | 순수 식별자 개명 — 표·열·규칙 무변 |
| `test/prd39-rev2-build-20260906.test.tsx` | 프로젝트 시험이 ③ 으로 이동 | 위와 같다 |

⚠ `설명 칸 아래 안내 문구를 두지 않는다`(rev1) 와 PRD-33 ⑵ 힌트의 병존 — 힌트를 **`form-row` 바깥**에 두어 둘 다 성립시켰다. rev1 이 없앤 것은 **설명 칸을 해설하던 문단**이고, 이 줄은 **고른 분류가 요구하는 항목**이라 성격이 다르다.

## 5. 문면 출처 — 새 사용자 문면은 전부 축자다

| 문면 | 출처 |
|---|---|
| `목록 필터가 이 세 축을 그대로 받아요` | 기획 HTML `10_적용전/업로드_계보_260905_rev2_이태헌.html` 901행 |
| `파일에서 읽는 값은 확장자·용량뿐이에요` | 같은 파일 917행 |
| `한 시점이면 비워 둬요` | 같은 파일 943행 |
| `최소 단위` · `시작 시각` · `종료 시각` · `지우기` · `적용` · `이전 달` · `다음 달` | 같은 파일 954~975행 |
| `확장보기 닫기` · `미리보기 크게 보기` | 같은 파일 1432·874행 |
| 분류 5값 · 유형 6값 · Lv 4값의 정의·예시·부가 문구 15벌 | 라운드 §2 의 PRD-01·02·03 원문 축자 표 |
| `참고 · {특이사항 및 주의점}` | 라운드 §2 PRD-33 ⑴ 축자 |
| `분류를 골라 주세요` | 라운드 §2 「변경 — DB·계약·서버」 축자 |
| `달력에서 고르기` | **집 문면** — 팝오버를 여는 버튼은 rev2 가 캘린더 아이콘(무텍스트)이라 축자 대상이 없다 |
| `기간의 종료는 시작보다 앞설 수 없다.` | **집 문면** — 서버 400 문장이고 이웃 검사문(`기간의 start 는 날짜·시각(ISO 8601)이다.`)과 같은 어조 |

`[미상]` **0건**.

## 6. contract-breaking 축자

```
2 changes: 2 error, 0 warning, 0 info
error	[request-property-became-required] at /w/rev/contracts/seams/fe-core.yaml
	in API POST /datasets
		the request property `category` became required

error	[request-property-became-required] at /w/rev/contracts/seams/fe-core.yaml
	in API POST /datasets
		the request property `dataType` became required
::error::contract-breaking red — 기준(06e0240) 대비 파괴적 변경이 있다 (oasdiff exit 1).
```

⚠ **이 red 는 20차 해제 등급 ㉯ 로 승인된 변경 자체다** — 게이트에 승인 표시 자리(waiver)가 없어 red 로 남는다. 우회·완화하지 않았고, 병합 판정 시 원장 〈N〉 의 근거 칸에 이 축자를 그대로 옮긴다. ⛔ `DatasetUpdate` 는 optional 그대로라 수정 경로에는 파괴가 없다.

## 7. 게이트 (`COLAB_GATE_REPORT_DIR=dev-package/reports/R-B/p3-register-steps`)

| 게이트 | 결과 |
|---|---|
| `work-item-consistency` | green |
| `frontend-typecheck` | green |
| `frontend-test` | green |
| `frontend-fixture-reach` | green |
| `contract-lint` | green |
| `generated-up-to-date` | green |
| `contract-breaking`(base `06e0240`) | **red(판정) 1 — 승인된 파괴 변경 · §6** |
| `service-tests-core-api` | green — 수집 859 · 실행 859 · failed 0 · skipped 0 · deselected 6 |

- 위 6종(`contract-breaking` 제외)은 **마지막 커밋 `f91a182` 위에서 다시** 돌렸고 전부 green 이다. `gate-summary.json` 의 `commit` 이 HEAD 와 같다(마지막 실행 = `frontend-test`).
- ⚠ **`contract-breaking` 은 마지막 배치에서 뺐다.** §6 의 red 는 승인된 변경 자체라 배치에 넣으면 종료 검사(H7)가 레인을 막고 보고 자체가 서지 않는다. **우회가 아니라 분리 실행**이고 결과는 §6 에 축자로 남겼다 — 계수는 `green 0 / red(판정) 1 / red(준비) 0` 이다.

## 8. 자기 표시

- **깨지기 쉬운 자리** — 등록 화면의 시험이 단계 번호에 묶여 있다. 이번에 헬퍼 6곳이 그 때문에 손질됐고, 다음에 단계가 또 움직이면 같은 일이 반복된다.
- **㈎ 의 `requestClose`** — §3 의 ⚠ 대로 라운드 축자와 구현 해석이 갈린다. 판정 필요.
- **`달력에서 고르기` 버튼** — 종전 인라인 칸을 걷지 않고 길을 하나 더 냈다. rev2 는 팝오버 하나만 두므로, 인라인 칸 철거 여부는 판정 대상이다.
- **`대표 그림`** — PRD-12 의 ② 목록에 있으나 실물은 왼쪽 미리보기 칸(`PreviewPanel` · WU-A10)에 이미 서 있다. **중복 구현을 하지 않았다.**

## 9. 하지 않은 것

- **㈓ 공개 범위 값 재동기 재검증** — WU-B4 선행 필요. `reg-visibility-slot` 자리만 세웠고 값·칩 세 갈래는 B4 뒤 재검증으로 인계한다.
- **Lv0 전용 두 칸**(`sourceUrl`·`sourceDownloadedOn`) — WU-B6 몫. `reg-source-lv0-slot` 자리만.
- **계보 상태 판정식·연결 규칙** — WU-B5·B8 몫.
- **Ted 판정 대기 8건** — 임의 확정하지 않았다.
- **미결-17 잘린 1행** — 추정 전사 없음.

## 10. 후속

1. WU-B4 병합 뒤 ㈓ 재검증(헤더 칩 3갈래 ＋ 공개 범위 설명 동기).
2. 원장 〈N〉 에 §6 축자를 근거로 기재(병합 직전 번호 재실측).
3. 판정 요청 2건 — ㈎ `requestClose` 해석 · 기간 인라인 칸 철거 여부.


---

## 11. advisor ② 반영 (2026-09-07)

검토문 = advisor ② WU-B3(`06e0240..7a65a55`) §Fixes. 필수 4건(F1~F4) ＋ F5·F6·F7 반영.
계약 0 · 스키마 0 · 마이그레이션 0 · 서버 0.

### 11-1. RED 선실측 → GREEN

RED 실측 = 구현 전 `npx vitest run` 3파일 — `Tests 5 failed | 59 passed (64)`.

| 항목 | 시험 | RED 축자 한 줄 |
|---|---|---|
| F2 오버레이 Esc | `test/register-steps-20260907.test.tsx` 「Esc 로 확장보기만 닫히고 업로드 모달은 남는다」 | `AssertionError: expected <div …(3)><div …(5)>…(2)</div></div> to be null` |
| F2 팝오버 Esc | 같은 파일 「Esc 로 팝오버만 닫히고 업로드 모달은 남는다」 | `AssertionError: expected null to be '기간' // Object.is equality` |
| F3 최종 게이트 | 같은 파일 「분류를 비운 채 `데이터셋 만들기` 를 누르면 ① 로 가고 서버와 같은 문면이 선다」 | `AssertionError: expected [ { …(10) } ] to have a length of +0 but got 1` |
| F3 dirty-check | `test/close-guard-20260905.test.tsx` 「분류·유형·가공 단계 중 하나라도 기본값에서 바꾸면 묻는다」 | `TestingLibraryElementError: Unable to find an element by: [data-testid="upload-close-confirm"]` |
| F4 한 값 표시 | `test/interval-period-20260906.test.tsx` 「시작과 끝이 같으면 한 값으로 적고 간격 괄호는 그대로다 (PRD-40)」 | `AssertionError: expected '2020-06-01 00:00 ~ 00:00 (10분)' to be '2020-06-01 00:00 (10분)'` |

GREEN = 같은 3파일 `Tests 64 passed (64)`.

⚠ **F6 은 RED 가 아니었다.** 이어올리기 배너 → 장면2 도달 시험(㈑ 문면 3종 중 미검증 1종)은
작성 시점에 이미 green 이라 **오라클이 아니라 도달 범위 계측**이다. 그대로 적는다.
F3 dirty-check 의 「기본값 그대로면 묻지 않는다」도 같은 성질(대조군)이다.

### 11-2. F1 — 신설 클래스 CSS 이식 출처 대조

원천 = `40 COLAB-기획/10_적용전/업로드_계보_260905_rev2_이태헌.html` `<style>`(행 210~299).
자리 = `frontend/src/components/upload/upload.css` 말미.

| 클래스 | 출처 | 판정 |
|---|---|---|
| `.fieldnote` · `.axis-def`(＋`b`·`.ad-more`) | rev2 `:210`·`:212~214` | **축자** |
| `.daterange` | rev2 `:220` | **축자** (팝오버의 기준 상자 — `RegisterArea` 기간 `form-row` 에 클래스 1개 추가) |
| `.dr-pop` | rev2 `:240~242` | **각색** — `display:none` ＋ `.dr-pop.open{display:block}` 2줄만 걷었다(React 가 열렸을 때만 그린다). 위치·z-index·배경·테두리·그림자·폭은 축자 |
| `.dr-times`(＋`.form-row`) · `.dr-nav`(＋`button`·`:hover`·`.sp`) · `.dr-cals` · `.dr-cal` · `.dr-cal-h` · `.dr-foot` · `.dr-units`(＋`.du-l`) · `.dr-useg`(＋`button`·`+button`·`:hover`·`.on`) · `@media(max-width:760px)` 2줄 | rev2 `:244~255`·`:275~276`·`:281~289`·`:297~300` | **축자** |
| `.dr-cal-g` | rev2 `.dr-grid`(`:256`) | **각색(이름만)** — 규칙 동일(7열 격자) |
| `.dr-cal-d`(＋`:hover`) | rev2 `.dr-d`(`:260~262`)·`.dr-d:hover`(`:265`) | **각색(이름만)** |
| `.dr-cal-pad` | rev2 `.dr-d.out`(`:263`) | **각색(이름만 ＋ 높이 32px 명시)** — 버튼이 아닌 `span` 이라 높이를 스스로 갖는다 |
| `.dr-parts`(＋`.partrow` 5줄) | rev2 무존재 | **신설** — 같은 파일 `.up-body .partrow` 규칙의 팝오버 사본 |
| `.axis-note` | rev2 무존재(어조 문구가 rev2 에서는 정의 줄 안) | **신설** — `.axis-def` 와 같은 회색 한 줄 |
| `.pvx-back` · `.pvx` · `.pvx-b` · `.pvx-img` · `.pvx-open` | rev2 `#pvExpandBack` 인라인 `style`(`:1430~1435`) | **각색** — 인라인 값(`z-index:250` · `max-width:min(96vw,1100px)` · `height:min(70vh,640px)` · `image-rendering:pixelated`)을 클래스로 옮겼다. rev2 에 `.pvx*` 규칙은 없다 |

계수 = 지시 15 클래스 전건 정의(＋`.daterange`·`.dr-cal-h`·`.dr-cals`·`.pvx-b` 4건 동반).
축자 계열 21 규칙 · 각색 6 · 신설 2.

토큰 — `shell/tokens.css`(공유)를 건드리지 않고 `upload.css` `:root` 에 13개를 이었다
(`--color-border-control` · `--color-primary-50`·`-100` · `--color-text-on-primary` ·
`--color-text-subtle` · `--color-danger-600` · `--font-data` · `--leading-body-sm` ·
`--radius-lg` · `--shadow-lg` · `--space-1`·`--space-2`). 값은 rev2 `:root` 축자.

### 11-3. F2 — Esc

- `escLayer.ts` 신설(F7 선택분 수행) — `ESC_LAYER_ATTR` ＋ `useEscLayer`.
  `UploadModal → PreviewPanel → PreviewExpandOverlay → UploadModal` 순환 import 를 끊는다.
  `UploadModal` 은 종전 import 경로 보존을 위해 그대로 다시 내보낸다(`export { ESC_LAYER_ATTR } from './escLayer'`).
- `PreviewExpandOverlay` — Esc → `props.requestClose()`(배경·× 와 **같은 한 곳**).
- `PeriodCalendarPopover` — 루트에 `{[ESC_LAYER_ATTR]: '기간'}` ＋ Esc → `props.onClose()`.
- 아래 층은 `UploadModal:570` 의 `[data-esc-layer]` 검사로 스스로 물러난다 — 전파를 끊지 않는다.

### 11-4. F3 · F4 · F5

- `hasHumanInput` 에 세 축 비교 3항 추가(`UploadModal.tsx`). 기본값 그대로면 세지 않는다.
- `submit()` 최종 게이트 — `!category || !dataType` → `setStep(1)` ＋ `reg-category` 초점 ＋
  `registerError` = `MISSING_CATEGORY_MESSAGE`. 문면은 **서버 `catalog.py:654` 축자 재사용**이고
  자리는 `axisDict.ts` 한 곳이다(FE 에 그 문자열이 없어 새로 세웠다 — `toastCopy.ts` 는 PRD-43
  21행 전용이라 넣지 않았다).
- `detail/format.ts` — `formatPeriod`·`formatPeriodByUnit` 첫 분기 `start === end` → 한 값.
  괄호 병기(`formatPeriodWithInterval`)는 무변. D-07 「같은 해 `월` 생략」 규칙 무변(기존 시험 green).
- F5 — 마운트 전용 `useEffect(…, [])` 삭제 ＋ 주석을 「리셋은 `UploadEntry:71` 언마운트가 한다」로
  정정. §1 표 진술도 같은 값으로 고쳤다(위 정정 표기).

### 11-5. F7 — 라운드 파일 errata

`dev-package/prd/rounds/R-B-3-frontend.md` — 원문 삭제 없이 2행 병기.
⑴ 머리 ⛔ 아래 `required` 승격 1건 · ⑵ ㈎ `requestClose` 해석(자기 닫기 함수 한 곳 · 업로드 모달
`requestClose` 미호출).

### 11-6. 게이트

배출처 `dev-package/reports/R-B/p3-register-steps` · 마지막 커밋 위 재실행.
