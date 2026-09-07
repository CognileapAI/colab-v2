# advisor ② — WU-B3 (lane p3-register-steps · 06e0240..7a65a55)

## For
- 계약 diff 가 승인 범위와 정확히 일치(`required` 2열쇠 ＋ 주석) · 서버 집행 1자리 · 수정 경로 optional 유지 · 마이그레이션 0. 15값 사전이 PRD 표와 축자 일치(표본 6/6, 중점 `·` 포함) · 저장값 국문 단일 · 병기는 표시층만.
- 25 시험이 기준 11 ＋ ㈎㈏㈐㈑㈒ 에 1:1 대응하고 대상 건수를 먼저 잰다. 기존 7 파일 갱신은 전부 단계 이동·요구 변경분이며 단언 약화 0(forged 시험에 축을 실어 400 원인이 additionalProperties 로 유지됨).
- WU-A3 골격 무재작성(StepMeta 본문 무변 · StepTwo 재사용) · `[미상]` 0 · 집 문면 2건 자진 공개.

## Against
- 화면 산출물인데 **CSS 변경 0줄**이다. 신설 클래스 15종이 어느 스타일시트에도 없어 달력 「팝오버」는 팝오버가 아니고(인라인 블록으로 폼을 밀어냄) 확장보기 이미지는 크기 제한이 없다. 「이관 ㈏ green」은 jsdom 한정 green 이다.
- A9R 규율(배경·×·Esc 한 판정식)을 인용하면서 두 새 층 모두 Esc 를 처리하지 않는다 — 규율의 세 갈래 중 하나가 빠진 채 「규율 준수」로 보고됐다.
- PRD-40 ㈒ 의 절반(표시 「한 값」)이 코드 무변·시험 무존재다.

## Verdict
approve-with-changes — 아래 Fixes 「병합 전 필수」 4건 반영 후 병합. 판정 위임 2건(F-J1·F-J2)은 차단 아님.

## ① 계약·생성물·서버
- `contracts/seams/fe-core.yaml` 변경 = `required: [uploadId, name, summary, category, dataType]` ＋ 주석·description 문단. 타 스키마 무변. `frontend/src/generated/fe-core.ts` `category?:`→`category:` · `dataType?:`→`dataType:` 동기 ✓.
- 서버 `ingestion.py` create 경로 `MISSING_CATEGORY_MESSAGE = "분류를 골라 주세요"` · 공백 문자열 포함 ✓ · `updateDataset` 미적용 ✓(대조군 시험 존재).
- `db/` 변경 0 ✓.
- 유의: 형이 `[string,"null"]` 인 채 required → `null` 은 스키마 유효·서버 400. 의도된 선택(주석 명시)이나 생성 TS 가 `null` 을 컴파일 통과시킨다. 기록만.

## ② 「main 과 동일」
- 세션 노트에 해당 표현 0건. contract-breaking red 1 = intent 「여는 값 5종 = … required 확장」 안. 병합 시 원장 〈N〉 근거 칸에 §6 축자 이기(재실측 번호).
- 라운드 파일 내부 모순: 머리 ⛔「두 WU 는 계약 개정도 하지 않는다」 ↔ §2 「변경 — DB·계약·서버」. 병합 시 머리 문장 정정(errata) 필요.

## ③ intent 대조 — 기준 ↔ 시험

| 기준 | 시험(`register-steps-20260907.test.tsx`) | 판정 |
|---|---|---|
| 1 표시기 3라벨·① 열림 | ① | ✓ |
| 2 ① 빈 값 → `다음` 차단 | ② (`classifyBlocked`) | ✓ · 단 빈 옵션 자체가 rev2 무존재(아래 F3) |
| 3 ③ 계보＋프로젝트 카드 | ③ | ✓ |
| 4 ③→① 무조건 | ④ | ✓ |
| 5 이름·설명 빈 채 ③ | ⑤ | ✓ |
| 6 재오픈 ① | ⑥ | △ — `UploadEntry:71` `{open && …}` 라 언마운트 리셋. `useEffect([],…)` 는 마운트 전용이라 「DOM 잔존 구현이어도 같다」를 증명하지 못하고 시험 ⑥ 은 기준 트리에서도 green 이었을 가능성이 높다(오라클 아님) |
| 7 15값 정의·예시 | ⑦ | ✓ |
| 8 위성자료 참고 | ⑧ | ✓ |
| 9 수문＋Lv1 힌트 | ⑨ | ✓ |
| 10 Lv0 힌트 배제 | ⑩ | ✓ |
| 11 부가 문구 빈 값 0 | ⑪ | ✓ |
| ㈎ 오버레이 | 표식·배경 mousedown/click·Esc 비삼킴 3건 | △ — **오버레이 자체 Esc 닫힘 미구현·미시험** |
| ㈏ 달력 팝오버 | 단위별 칸·적용 2건 | △ — CSS 0 · Esc/바깥클릭 닫힘 0 |
| ㈐ 3단계 재편 | ①④⑥ | ✓ |
| ㈑ 2장면 | 장면1 DOM 부재(`up-split`·`reg-area`·`up-split-preview` null) · 장면2 · 배지 × → `up-removed-toast` | △ — 이어올리기 배너 도달 미검증. `FILE_REMOVED_NOTICE` 는 import 재사용 ✓ |
| ㈒ PRD-40 | 안내 문면 · 요청 `end = start` FE 2건 · 서버 400/201 2건 | △ — 표시 「한 값」 무변·무시험(F4). 조립은 FE `humanMetadata`, 계약 무변 ✓. 400 검사는 신설(`catalog.py:791~`) · 문면 집 작성(공개됨) · PATCH 경로에도 적용(허용 범위) |
| ㈓ 공개 범위 재동기 | 인계(B4 뒤) · `reg-visibility-slot` 만 | 미달 기록 — 라운드 자체가 B4 선행 인정 |

- 초과 항목: `reg-source-lv0-slot`·`reg-visibility-slot` 빈 자리 2건(다음 WU 몫 자리 · 무해) · 빈 옵션 `아직 고르지 않음`(rev2 무존재) · 서버 기간 순서 검사의 PATCH 경로 적용.
- 판정 대기 4·7(FOOT_HINTS 「분류를 고르고…」)은 ① 라벨 변경으로 문면이 자연 정합 — 라운드 예고대로 「저절로 맞음」 상태. 보고만.

## 자기표시 판정
- **①(requestClose 해석)** — 레인 해석 채택. 근거 ⑴ `UploadModal:565` 가 `[data-esc-layer]` 존재 시 return 하는 설계 = 상위 층은 스스로 닫히고 하위 층은 기다린다 ⑵ rev2 1432행 × 가 `closePvExpand()` 이고 모달 닫기가 아님 ⑶ 배경 클릭이 업로드 모달 `requestClose` 를 타면 확장보기 배경 한 번에 등록 입력 전체가 닫기 확인으로 간다. 라운드 문면의 `:509` 는 「한 함수 경유·직접 close 금지」 규율의 앵커로 읽는다. 라운드 파일 ㈎ 문장에 errata 1줄 병기 권고.
- **②(인라인 존치＋팝오버)** — 판정-2 ⓑ 문면은 「달력 팝오버 채택」이고 인라인 철거를 명시하지 않아 확정 결정 위반 아님. 다만 rev2 는 `dr-field`(시작/종료 표시 버튼)＋팝오버 하나이고, 현 구현은 같은 값에 입력 경로 둘(§6-1 이 경고하는 「동일 행위에 화면 규약 둘」). Ted 질의 1건으로 묶음: ⓐ rev2 충실(인라인 철거 ＋ `dr-field` 표시 신설 · `interval-period-20260906` 인라인 시험 재작성) / ⓑ 이중 경로 유지. 병합 차단 아님.

## Risks
1. 실화면 — 신설 클래스 15종 CSS 부재(`pvx-back`·`pvx`·`pvx-img`·`pvx-open`·`axis-def`·`axis-note`·`fieldnote`·`dr-pop`·`dr-cal`·`dr-units`·`dr-useg`·`dr-parts`·`dr-times`·`dr-nav`·`dr-foot`). `dr-pop` 무위치 지정 → 인라인 흐름. 초점 이동·초점 트랩·포커스 복귀 0(두 층 모두). 표시기 버튼은 키보드 접근 ✓(`button`·`aria-current`).
2. Esc — 팝오버 열린 채 Esc → `UploadModal.requestClose` 실행(입력 있으면 닫기 확인, 없으면 모달 종료). 오버레이 열린 채 Esc → 무동작.
3. 순환 import `UploadModal → PreviewPanel → PreviewExpandOverlay → UploadModal`(`ESC_LAYER_ATTR`). 런타임 무해(함수 본문 참조)이나 번들러 순서 의존.

## Missed
- `hasHumanInput`(`UploadModal:379~398`)이 `category`·`dataType`·`level` 을 기본값과 견주지 않음 → 기본값에서 바꾼 뒤 Esc·배경 클릭 시 무확인 소실(A9R F2 와 같은 증상).
- 빈 옵션 선택 후 표시기 ③ → `데이터셋 만들기` → 서버 400 문면이 `registerError` 로 ③ 에 표시되고 ① 이동·초점 없음(이름·설명 경로 `setStep(2)`+focus 와 불일치).
- 표시 「한 값」: `formatPeriod`(단위 없음) `2020-06 ~ 06` · `formatPeriodByUnit`(시·분·초) 「같은 날」 규칙이 `s === e` 보다 먼저 걸려 `2020-06-01 00:00 ~ 00:00`. 단위 `일`·`월`·`년`만 한 값.
- `gate-summary.json`(HEAD 7a65a55)은 `frontend-test` 1종만 담음 — 6종 green 의 기계 근거는 덧쓰여 부재(세션 노트 진술만).
- 서버 기간 순서 검사: 한쪽만 tz 인 경우 통과 → DB CHECK 위반 500 가능(기존 결함 잔존 · 레인 신설 아님).

## Fixes
- **[병합 전 필수] F1 CSS** — `frontend/src/components/upload/upload.css` 에 위 15 클래스 정의. 최소 = `.dr-pop`(position:absolute·z-index·배경·테두리) · `.dr-cal-g`(grid 7열) · `.pvx-img`(max-width/max-height) · `.axis-def`·`.axis-note`·`.fieldnote`(회색 한 줄). rev2 HTML `<style>` 의 같은 이름 규칙을 축자 이식(`dr-*`·`axis-def`·`pvx*` 는 rev2 에 존재).
- **[병합 전 필수] F2 Esc** — `PreviewExpandOverlay`: `useEffect` document keydown `Escape` → `props.requestClose()`. `PeriodCalendarPopover`: 루트에 `{...{[ESC_LAYER_ATTR]:'기간'}}` ＋ 같은 keydown → `props.onClose()`. 시험 2건 추가(Esc 로 층만 닫히고 `upload-modal` 잔존).
- **[병합 전 필수] F3 dirty-check ＋ 최종 게이트** — `hasHumanInput` 에 `category !== DEFAULT_CATEGORY || dataType !== DEFAULT_DATA_TYPE || level !== DEFAULT_PROCESSING_LEVEL` 추가(기본값 그대로면 0). `register()` 에 `!category || !dataType` → `setStep(1)` ＋ `reg-category` focus ＋ `registerError`=서버 문면 재사용 `분류를 골라 주세요`. `close-guard` 시험 2건(기본값 무확인 · 변경 후 확인) ＋ 최종 게이트 시험 1건 추가.
- **[병합 전 필수] F4 표시 한 값** — `format.ts` `formatPeriod`·`formatPeriodByUnit` 첫 분기에 `start === end` → 단일 값(단위 있으면 `cut(start, unit)`, 없으면 `start.slice(0,10)`) 후 `formatPeriodWithInterval` 괄호 그대로. 시험 1건(`2020-06-01T00:00:00Z` 양끝 ＋ 간격 `10분` → `2020-06-01 (10분)` 류).
- F5 PRD-13 — 마운트 전용 effect 를 걷고 주석을 「리셋은 `UploadEntry:71` 언마운트가 한다」로 정정하거나, `props.onClose` 직전 `setStep(1)` 을 두어 문서와 코드를 일치. 세션 노트 §1 「마운트 effect」 진술 수정.
- F6 ㈑ — 이어올리기 배너 픽스처로 장면2 도달 시험 1건(라운드 ㈑ 문면 3종 중 미검증 1종).
- F7 병합 절차 — 원장 〈N〉 에 §6 축자 · 라운드 파일 머리 ⛔ 문장 errata · ㈎ `requestClose` 해석 errata 1줄 · `ESC_LAYER_ATTR` 를 `escLayer.ts` 로 분리(순환 제거 · 선택).
- F-J1(Ted) 기간 입력 경로 — ⓐ rev2 충실(인라인 철거＋`dr-field`) / ⓑ 이중 유지. 비용 ⓐ = `interval-period-20260906` 인라인 단언 재작성.
- F-J2(Ted) 집 문면 2건 — `달력에서 고르기`(대안 = rev2 dialog aria-label `기간 고르기` 재사용) · 서버 `기간의 종료는 시작보다 앞설 수 없다.`(서버 문면 · 승인만).
