# 레인 A4 — 업로드 모달 ② 메타데이터 단계 레이아웃을 기획서 rev2 에 맞춘다

- 회차 = 업로드 폼 rev2 · 레인 A4. 기점 `5a172e78`(`feature/rtf400_upload_form`).
- 범위 = **프론트만**. 계약·서버·DB·마이그레이션 변경 0건. 폼 상태 열쇠·요청 본문·검증 순서 무변.
- 오라클 = 기획서 rev2 목업 `업로드_계보_260905_rev2.html` 의 `#reg-s1`(`data-regstep="2"`) 카드 본문
  ＋ 그 파일 `<style>` 블록의 `.form-3`·`.daterange`·`.dr-*`·`.itv`·`.req`·`.vartable`·`.vt-*`.
- 착수 근거 = 사용자 지적(2026-09-14 · 스크린샷 대조) 「메타데이터 입력 쪽에 UI 레이아웃이 적용이
  안 됐다 · 입력 순서가 다르다 · 변수 표 형태가 기획서와 다르다」.

---

## 1. 항목별 대조표 (목업 ② ↔ 종전 구현 ↔ 이번 구현)

| # | 목업 ② 항목 | 종전 구현 | 이번 구현 | 판정 |
|---|---|---|---|---|
| 0 | `파일에서 자동으로 읽었어요` ＋ 확장자·용량 2칸(`form-2`) | 같음 | 무변 | 일치(종전부터) |
| 1 | `데이터셋 이름` 필수 · 한 줄 입력 | 같음 | 무변 | 일치(종전부터) |
| 2 | `기간` 필수 · **한 행에 시작·종료 두 칸**(`#prField` = `.dr-field` ＋ `.dr-half` 둘 · 달력 아이콘 · → 화살표) | 짧은 값 한 줄의 **첫 칸**에 `달력에서 고르기` 작은 버튼 1개 ＋ 그 아래 안내 문단 | 이름 바로 아래 **제 행** · `.dr-field` 안에 `시작`/`종료` 두 반쪽 | **고침** |
| 3 | `관측 간격` 필수(수 칸 ＋ 단위 select = `.itv`) | 짧은 값 한 줄 **밖**의 제 행 · `span.pair` | 짧은 값 한 줄의 **첫 칸** · `span.itv` | **고침** |
| 4 | `좌표계` 선택 · 한 줄 입력 | 짧은 값 한 줄의 둘째 칸 | 무변(자리만 한 칸 앞) | 일치 |
| 5 | `격자 (선택)` · **한 줄 입력** | 라벨 `격자 설명` ＋ `textarea rows=2` ＋ 칸 아래 안내 한 줄 | 라벨 `격자` ＋ `input` 한 줄 · 안내 문단 제거 | **고침** |
| 6 | `설명` 필수 · `textarea rows=3` | 같음(자리는 변수 표·짧은 값 줄 뒤) | 무변(자리는 짧은 값 줄 바로 뒤) | 일치 |
| 7 | `변수 (여러 개 · 대표 변수 하나를 골라요)` ＋ **선 있는 표** ＋ 표 아래 `+ 변수 추가` | 데이터셋 이름 **바로 아래** · `label` ＋ `선택` 배지 · 밑줄만 있는 표 · 셀마다 테두리 있는 입력 · 삭제 `삭제` 글자 | 설명 **뒤** · 섹션 제목(`fieldlbl`) · 셀이 선을 긋는 표 · 입력 테두리 제거 · 삭제 `×` | **고침** |
| 8 | `공개 범위` select ＋ 아래 한 줄 안내 | 같음 | 무변 | 일치(종전부터) |
| 9 | 필수 = 라벨 옆 **붉은 작은 글자**(`.req`) · 선택 = 흐린 작은 글자 | 둘 다 **알약 배지**(테두리 ＋ 배경) | 알약을 걷고 목업 글자 스타일로 · **사용처·클래스 이름·`data-testid` 무변** | **고침** |
| 10 | `대표 그림(썸네일)` — 목업은 ② 카드 **맨 아래** | 좌측 미리보기 칸(`PreviewPanel`) | **무접촉**(지시문 「현행 유지」) | 의도된 불일치 |

### 순서 판정 (시험 `upload-meta-layout-20260914.test.tsx` ㈎ 가 문서 순서로 잰다)

`reg-name` → `reg-period-open` → `reg-interval-value` → `reg-crs` → `reg-grid-description`
→ `reg-summary` → `variable-table` → `reg-visibility`.

### 지시문과 목업 실물이 갈린 한 곳

- 지시문 = 「관측 간격 ＋ 좌표계를 **같은 행**에 · 격자는 **한 줄 입력** 별행」.
- 목업 실물 = `form-3` **한 행에 셋**(관측 간격·좌표계·격자) ＋ `@media(max-width:1100px)` 에서 **2열**로 접힘.
- 판정 = **모순이 아니다.** 스크린샷이 잡은 2+1 모양이 곧 1100px 이하 구간이다. 셋을 한 `form-3` 에
  두고 접히는 폭을 목업 축자(1100px → 2열, 그보다 좁으면 1열)로 옮겼다. 격자는 지시문대로 한 줄 입력이다.

---

## 2. 매핑표 (목업 칸 ↔ 우리 폼 열쇠)

| 목업 id | 목업 라벨 | 우리 `data-testid` | 폼 상태 열쇠 | 요청 본문 | 비고 |
|---|---|---|---|---|---|
| `dsName` | 데이터셋 이름 | `reg-name` | `name` | `name` | 무변 |
| `prField`·`prVs`·`prVe` | 기간(시작·종료) | `reg-period-open` · `reg-period-start-value` · `reg-period-single-hint`/`reg-period-end-value` | `granularity`·`startParts`·`endParts` | `period` | 값은 팝오버 `적용` 이 채운다(무변) |
| `itvNum`·`itvUnit` | 관측 간격 | `reg-interval-value`·`reg-interval-unit` | `intervalValue`·`intervalUnit` | `observationInterval` | 무변 |
| `metaCrs` | 좌표계 | `reg-crs` | `crs` | `crs` | 무변 |
| `metaGrid` | 격자 (선택) | `reg-grid-description` | `gridDescription` | `gridDescription` | **칸 종류만** textarea → input |
| `dsDesc` | 설명 | `reg-summary` | `summary` | `summary` | 무변 |
| `varRows` | 변수 표 | `variable-table` · `vt-*` | `variables` | `variables` | 무변 |
| `metaScope` | 공개 범위 | `reg-visibility` | `accessState` | `accessState` | 무변 |

- **새로 만든 열쇠 0건.** `reg-period-start-value`·`reg-period-end-value` 는 화면 표기용 `data-testid`
  이고 폼 상태·요청에 대응물이 없다.
- `reg-period-single-hint` 는 **종료가 빈 값일 때만** 선다(값이 차면 그 자리에 `reg-period-end-value`).
  문면 `한 시점이면 비워 둬요` 는 **무변**이고 자리만 칸 안으로 들어왔다.

---

## 3. 미존재 칸 (목업에 있으나 우리 폼·계약에 없다 — **추가하지 않았다**)

| 목업 항목 | 목업 자리 | 우리 쪽 사정 |
|---|---|---|
| 대표 그림(썸네일) 3요소(`thumbPrev`·`thumbMeta`·`thumbInput`) | ② 카드 맨 아래 | 좌측 미리보기 칸이 이미 그린다(`PreviewPanel` · WU-A10 · PRD-20). 지시문 「현행 유지 · 손대지 않는다」 |
| 최소 단위 `초` 까지의 6단 사다리 표기 | 기간 팝오버 안 | 팝오버는 이 레인 무접촉(`PeriodCalendarPopover`) |
| 공개 범위 3값(`전체 공개`·`조건부 공개`·`비공개`) | 공개 범위 select | 기준축이 연구실 **밖**이라 우리 3값과 한 칸씩 어긋난다. PRD-11 대응표·미결-1 ⓐ 가 rev1 값을 확정했고 이 레인이 되돌리지 않는다 |

---

## 4. 종전 판정과 충돌하는 것 (**Ted 재판정 대기** · 병합 조건)

1. **격자 칸 안내 문단 제거.**
   - 충돌 상대 = `dev-package/prd/specs/2026-09-12-issue-register-hints-parent-picker.md`
     수용 기준 「격자 설명·공개 범위 칸의 안내 위치가 종전과 같다(회귀 아님)」.
   - 이번 판단 = rev2 목업의 이 칸(`#metaGrid`)에는 안내 문단이 **없다**. 지시문이 「안내문은 이 한 줄로」를
     명시했고 근거가 더 최근(2026-09-14 사용자 지적)이라 목업을 따랐다.
   - 되돌리는 비용 = `RegisterArea.tsx` 격자 `form-row` 에 `p.fieldnote` 한 줄 복원 ＋ 시험 2건 문면 복귀.
2. **기간 안내 문단의 자리 이동.**
   - 충돌 상대 = 같은 spec 의 「카드 안 안내 문단을 라벨 → 컨트롤 → 설명문 순으로」(`R-BUGFIX-260912 #31`).
   - 이번 판단 = **문면은 유지**하고 자리만 목업대로 종료 반쪽 안으로 옮겼다. 규칙(설명문이 컨트롤 뒤)은
     남은 안내 문단(공개 범위)에 그대로 적용되고 시험이 계속 진다.
3. **필수/선택 표시의 `(선택)` 괄호.**
   - 지시문 = 「선택은 라벨 뒤 `(선택)` 괄호」 ＋ 「A1 이 만든 배지 컴포넌트는 **스타일만** 바꾸고
     사용처는 유지」.
   - 이번 판단 = **스타일만** 바꿨다. 문면은 `선택` 그대로다 — `(선택)` 괄호로 되돌리면
     `upload-form-rev2-20260914.test.tsx` 의 판정 두 건(「라벨 텍스트에 `(선택)` 괄호가 없다」 ·
     「`선택` 배지가 선다」)과 정면으로 어긋난다. 두 지시 중 「사용처 유지」를 택했다.

---

## 5. 어느 검사에 걸리는가 (`colab-rules §3-3`)

- **`--color-danger-600` 라이트 값 고정** — `frontend/src/components/upload/upload.css` 의 `:root` 블록이
  `#ba3125` 를 박아 `shell/tokens.css` 의 테마 대응 값(`var(--fg-danger)`)을 덮는다. 다크에서 대비가 떨어진다.
  - 걸리는 검사 = **없다.** `design-fix-20260908.test.ts`·`css-residual-rc11.test.ts` 의 「미정의 토큰 참조
    0건」 판정은 `lineageGraph.css` 에만 걸려 있고, 대비 판정은 상세·카탈로그 선택자에만 걸려 있다.
  - 이 레인 처리 = **고치지 않았다**(소유 밖 · 이 레인이 새로 만든 결함 아님). `.reqtag` 는 테마 대응
    토큰 `var(--fg-danger)` 를 직접 읽어 우회했다. 후속 항목으로 올린다.
- **업로드 CSS 의 다크 대응은 게이트가 재지 않는다** — 토큰 참조 여부·대비를 재는 검사가 `upload.css` 를
  대상에 넣지 않는다. 이번 신설 규칙(`.dr-*`·`.itv`·`.reqtag`·`.opttag`)은 전부 테마 토큰만 읽지만,
  그 사실을 강제하는 검사는 없다. 후속 항목.

---

## 6. 시험 (red → green)

- **신설** `frontend/test/upload-meta-layout-20260914.test.tsx` — 12건(순서 1 · 기간 2 · 짧은 값 줄 2 ·
  격자 2 · 변수 표 4 · 필수 표기 1).
- **RED 실측** — 구현 전 `12 tests | 10 failed`. 인용 한 줄:
  `FAIL … > ② 메타데이터 — 사람이 적는 칸의 순서가 목업 순서다 > 이름 → 기간 → 관측 간격 → 좌표계 → 격자 → 설명 → 변수 표 → 공개 범위`
  - 통과로 시작한 2건 = 「`+ 변수 추가` 가 표 아래」·「② 의 `필수` 배지 네 곳」. 둘 다 **종전부터 참**이라
    오라클이 아니다 — 회귀 방지용으로 남긴다(이 사실을 여기 적는다).
- **GREEN** — 구현 후 `12 tests | 12 passed`.
- **고친 기존 시험 3건**(전부 「대상이 옮겨간 것」이고 요구를 줄이지 않았다):
  - `register-steps-20260907.test.tsx` — 안내 문단 3건 판정을 **1건(공개 범위) ＋ 옮겨간 두 건의 새 판정 2건**
    으로 나눴다(총 3 it). 규칙 자체는 무변.
  - `summary-required-20260905.test.tsx` — 짧은 값 한 줄의 세 칸 이름을 `기간`→`관측 간격` 으로 옮기고,
    「기간이 그 줄 밖이고 화면에는 있다」를 함께 잰다(빈 집합 통과 방지).
  - `upload.test.tsx` — 변수 이름표가 `label`＋배지에서 섹션 제목으로 바뀐 것을 잰다.
- **지시문 소유 목록 밖 수정 2건**(초과분 · 사유 명기):
  - `summary-required-20260905.test.tsx` — ② 짧은 값 한 줄을 직접 판정하고 있어, 고치지 않으면 red 가 남는다.
  - `src/components/common/VariableTable.tsx`·`variableTable.css` — 목업 표 모양(선·`×`·테두리 없는 입력)이
    이 컴포넌트 안에 있다. 상세 화면이 같은 컴포넌트를 읽기 전용으로 쓰는데, rev2 의 상세 표(`.vt-row.vt-ro`)도
    **같은 격자**라 두 화면이 갈리지 않는다.

## 7. 게이트

한 실행(`COLAB_TASK_ID` ＋ `COLAB_GATE_REPORT_DIR` 선언 · `bash gates/run.sh task`):

```
frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.
frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 1374건 · 실패 0건.
    Test Files  112 passed (112)
         Tests  1374 passed (1374)
── 계 : green 2 / red(판정) 0 / red(준비) 0
```

- 계수 = **green 2 / red(판정) 0 / red(준비) 0**. 배출 = `dev-package/reports/upload-form-rev2/lane-A4/gate-summary.json`
  (`colab-gate-summary/1` · `counts.green=2`).

### 호스트 부하로 흔들린 시험 7건 — 원인을 실측했다

| 실행 | 대기 만료로 red 를 낸 파일 | 그때 호스트 |
|---|---|---|
| 전수 1 | `lv-display-unify-20260908.test.tsx` | 형제 레인 vitest 동시 실행 |
| 전수 2 | `dataset-preview-zoom.test.tsx` · `s2-map-state.test.tsx` | 같음 |
| 게이트 2 | (요약만 · 1건) | 같음 |
| 게이트 3 | `close-guard-20260905.test.tsx` · `upload-transfer.test.tsx` | 같음 |
| 게이트 1·4 | **0건**(1374/1374 green) | 게이트 1 = 형제 유휴 · 게이트 4 = 형제 종료 후 `load1` 9.7 까지 대기 |

- **원인 실측** — 형제 워크트리 `agent-a29044930ec3f869c` 의 `vitest run` 이 포크 7개로 8코어를 채우고 있었고,
  그 시점 `load averages: 122.06 123.92 80.44` 였다. 규칙 `colab-rules §9`(전수 실행 중 다른 레인 미기동)이
  지키는 것이 이 자리다.
- **판정** — 흔들린 7건 중 **이 레인이 건드린 파일은 0건**이고, 지목된 5파일은 **단독 재실행에서 전건 통과**했다.
  형제가 끝나고 `load1` 이 10 아래로 내려간 뒤 돌린 게이트가 **1374/1374 green** 이다. **판정 red 가 아니라
  환경이다** — 다만 「main 과 같다」로 넘기지 않고 원인·재현 조건·대기 절차를 여기 적는다.

## 8. 남은 위험 · 후속 항목

- 위험 ⑴ — 격자 안내 문단 제거와 기간 안내 자리 이동이 2026-09-12 spec 수용 기준과 갈린다(§4). **Ted 재판정 전 병합 금지.**
- 위험 ⑵ — 다크 테마 실물 확인을 **하지 않았다**(`[미확인]`). jsdom 은 스타일을 계산하지 않아 시험이 색을 재지 못한다.
  푸는 방법 = 브라우저에서 `data-theme="dark"` 로 ② 카드를 열어 `.dr-field`·`.vartable`·`.reqtag` 대비를 눈으로 잰다.
- 후속 ① — `upload.css` 의 `--color-danger-600` 라이트 값 고정을 `var(--fg-danger)` 로 되돌린다(현재 참조처 0건).
- 후속 ② — CSS 계측 시험(`design-fix`·`css-residual`)의 「미정의 토큰 참조 0건」·대비 판정 대상에 `upload.css` 를 넣는다.
- 후속 ③ — 전수 vitest 가 호스트 부하에서 파일 단위로 흔들린다(§7 표). 게이트가 병렬도를 스스로 낮추거나
  `waitFor` 대기 시간을 올리지 않는 한, **레인 두 개를 동시에 돌리면 계수가 뒤집힌다.** 어느 검사도 이 사실을
  잡지 않는다 — 게이트는 자기 실행만 보고 호스트 부하를 보지 않는다.
