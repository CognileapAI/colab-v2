# 레인 A1 — 업로드 모달 우측 등록 폼을 기획서 rev2 ＋ 기획자 2026-09-13 피드백에 맞춤

- 기점 `origin/main` `b5e8e79f` · 프론트 전용 · **계약·서버·DB·마이그레이션 변경 0건**.
- 오라클 = `업로드_계보_260905_rev2.html` 우측 폼 마크업 ＋ 그 파일의 `makeDataset()` 검증 순서.

## 1. 변경 파일

| 파일 | 내용 |
|---|---|
| `frontend/src/components/upload/RegisterArea.tsx` | `주제` 칸 제거 · `FieldTag` 배지 컴포넌트 신설 · 배지 재배치 · 관측 간격 단위 표시 라벨 · 원천 블록 재구성 |
| `frontend/src/components/upload/UploadModal.tsx` | `topic` 상태·전송 제거 · 등록 게이트 6단 집중 ＋ 토스트 · `sourceVisible` 전송 조건 |
| `frontend/src/components/common/toastCopy.ts` | 등록 게이트 토스트 문면 5종(rev2 `toast()` 인자 축자) |
| `frontend/src/components/upload/upload.css` | `.opttag`(선택 배지) 신설 |
| `frontend/test/upload-form-rev2-20260914.test.tsx` | **신규** 17건 — 이 회차의 오라클 |
| `frontend/test/upload.test.tsx` | 도우미 보강 ＋ 개정 4건 |
| `frontend/test/lv0-source-20260907.test.tsx` | 개정 5건(필수 배지·블록 조건·전송 규율) |
| `frontend/test/interval-period-20260906.test.tsx` | 개정 3건(관측 간격 필수) |
| `frontend/test/register-steps-20260907.test.tsx` · `lineage-unknown-20260907` · `lv-rules-20260907` · `advisor2-b6-20260907` · `fe-small-rc8` | 도우미에 새 필수 두 칸 채움만 추가(재는 대상 무변) |

## 2. 제거 / 추가

**제거**

- `주제`(`reg-topic`) 셀렉트 · 폼 상태 `topic` · 요청 본문 `topic` 열쇠 · `LineageStepContext.topic` 단서값(`null` 고정).
  - 읽기 쪽 무변 — 목록 열 · 상세 칩 · 필터 · 계약 `topic`(optional) · DB 컬럼 · `TOPICS` 상수(`ParentPicker` 가 계속 쓴다).
- 라벨 끝 `(선택)` 괄호 문구 5곳(좌표계 · 격자 설명 · 변수 · 기간 · 관측 간격 · Lv0 두 칸).
- `원천 표기` 라벨.

**추가**

- `FieldTag` — `필수`(`.reqtag`) / `선택`(`.opttag`) 한 컴포넌트. 배지가 붙는 자리 = 필수 7(분류·유형·가공 단계·이름·기간·관측 간격·설명) · 선택 4(변수·좌표계·격자 설명·공개 범위) · Lv0 조건부 2(출처 주소·내려받은 날).
- `INTERVAL_UNIT_LABEL` — 표시 라벨 `초·분·시간·일·월·연`. **저장값 `초·분·시·일·월·년` 무변**(계약·DB CHECK 무변).
- 원천 블록(`reg-source-block`) — 제목 `원천 · 연구실 밖 출처` · 칸 `출처 이름`(`sourceLabel` 필드 그대로) · `출처 주소` · `내려받은 날`. 표시 조건 = `Lv0 || 연결 0건`(`ctx.parents.length`). `내려받은 날` 은 블록 안에서 다시 Lv0 조건. 위치 = 계보 슬롯 **뒤**(기획서 `srcBlock` 자리).
- 등록 게이트 6단(`UploadModal.submit`) — ⑴ 이름 ⑵ 설명 ⑶ 분류·유형 ⑷ 기간 시작 ⑸ 관측 간격(값 > 0 ∧ 단위) ⑹ Lv0 출처 두 칸. 첫 실패 하나만 토스트(`up-register-toast`) ＋ 그 단계 이동 ＋ 초점. 인라인 `.warn` 은 존치.
- 전송 조건 = 표시 조건과 같은 식 — 블록이 숨으면 `sourceLabel` 은 `null`, `sourceUrl`·`sourceDownloadedOn` 은 열쇠 자체를 싣지 않는다.

## 3. PRD 개정 표시 (`dev-package/prd/PRD-260905-적용전기획.md`)

원문을 지우지 않고 취소선 ＋ `⭑ ⟨개정 2026-09-14 · 기획자 2026-09-13 구두 피드백 · Ted 재판정 대기⟩` 를 붙였다. 삽입 17곳, 판정 4건.

| # | 자리 | 종전 | 현재 |
|---|---|---|---|
| ⑴ | `§1` 미결-4 ⓐ | 관측 간격 **선택 입력** | **필수 입력**(숫자 > 0 ＋ 단위) |
| ⑵ | `§1` 미결-11 ⓐ | 원천 표기 **Lv 무관 상시 노출** | 세 칸 한 블록 · `Lv0` 또는 **연결 0건**일 때만 |
| ⑶ | `§2` PRD-19 (제목 · 변경-프론트 · Lv 게이팅 줄 · 수용 기준 5줄 · 감사 교차 확인) | Lv0 두 칸 **선택 입력** · 목업 배지 미채택 | **화면 필수** · 목업 배지 채택. ⚠ **서버 판정 무변**(Lv0 400 · Lv1 400 둘 다 여전히 폐기) |
| ⑷ | `§3` 등록 폼 표 ＋ ③ 검증 목록 | 관측 간격 `선택` · 「막지 않는 것」에 관측 간격·Lv0 출처 | 관측 간격 `필수` · 게이트 6단 순서 명기 · 주제 칸 부재 · 배지 통일 |

코드 주석 개정 표시 2곳 — `RegisterArea.tsx` `LV0_SOURCE_NOTICE` 머리주석(「rev2 목업이 필수 배지를 그렸으나 정본은 선택 입력」) · `StepThree` 머리주석(「원천 표기는 Lv 무관 상시 노출(미결-11 ⓐ)」).

## 4. 기획서에 있으나 폼·계약에 없는 칸 (추가하지 않음)

| 기획서 자리 | 내용 | 미추가 사유 |
|---|---|---|
| `dr-times` `prTs`·`prTe` | 기간 팝오버의 `시작 시각`·`종료 시각` `<input type="time">` | 현행 팝오버가 최소 단위가 여는 자리 칸으로 같은 값을 받는다(PRD-18 · 판정-2 ⓑ). 계약 형상 무변 |
| `dr-units` `최소 단위` 라벨 | 팝오버 안 단위 사다리 라벨 | 현행 `reg-period-unit-*` 버튼이 같은 6값을 낸다. 라벨 문자열만 상이 |
| `metaScope` 3값 | `비공개 · 조건부 공개 · 전체 공개` | PRD-11 대응표 · 미결-1 ⓐ 가 rev1 3값(`연구실 구성원 전체`·`나만 보기`·`지정한 사람만`)을 확정. 기준축이 달라 한 칸씩 어긋난다 |
| 변수 표 `대표` 라디오 · `(여러 개 · 대표 변수 하나를 골라요)` | 변수 표 부제 | 표 자체는 `VariableTable` 이 이미 갖는다. 부제 문면만 상이 |
| `itvNum` `type="number" min=1 step=1` | 관측 간격 숫자 칸의 입력 타입 | 현행 `type="text" inputMode="numeric"`. 판정은 `submit` 이 하고 형상 요구가 계약에 없다 |

## 5. 시험 계수

| 시점 | 계수 | 비고 |
|---|---|---|
| 전(기점 `b5e8e79f`) | 파일 108 / 시험 1326 — 통과 1325 · 실패 1 | 실패 1건 = `upload-transfer.test.tsx:326` 「표준 격자 가…」 대기 만료. **단독 재실행 16/16 통과** — Rosetta 간헐 시간 초과 |
| 신규 시험 최초 실행(RED) | 17건 중 **16 red** · 1 green | red 로그 한 줄 — `TestingLibraryElementError: Unable to find an element with the text: 필수` (`reg-name` 라벨) ／ `AssertionError: expected null to be truthy` 등. green 1건 = ① 분류 3축 배지(종전부터 참) |
| 후 1회차 | 파일 109 / 시험 1343 — **전건 통과** | |
| 후 2회차 | 파일 109 / 시험 1343 — **전건 통과** | 간헐 실패 재현 없음 |

## 6. 게이트

```
frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 1343건 · 실패 0건.
frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.
── 계 : green 2 / red(판정) 0 / red(준비) 0
```

- 배출처 `dev-package/reports/upload-form-rev2/lane-A1-gates/gate-summary.json`(`colab-gate-summary/1` · `task_id` `0b9b043097814f9f98b7580bcb8e2b5f` · before/after 파일 hash 동일).
- 전수 `all` 은 이 레인이 돌리지 않았다 — 병합 직전 1회는 오케스트레이터 몫(`colab-rules §3-1`).

## 7. 원한 결과 대조

지시문의 작업 5건 전부 충족. `dev-package/intent/` 에 이 회차 항목 파일 **없음** — 대조 원본은 지시문 본문.

- **미달** 0건.
- **초과** 2건 —
  1. `frontend/test/` 의 소유 밖 5개 파일(`advisor2-b6-20260907`·`fe-small-rc8`·`interval-period-20260906`·`lineage-unknown-20260907`·`lv-rules-20260907`) 수정. 사유 = 기간·관측 간격·Lv0 출처가 등록 게이트가 되면서 그 파일들의 `데이터셋 만들기` 경로가 전부 막힌다(수정 없이는 red 20건). 수정 성격 = ⑴ 도우미에 두 칸 채움 추가 ⑵ `interval-period` 3건은 「선택 입력」 단언 자체가 판정과 충돌해 개정 표시와 함께 갈아탐.
  2. `reg-name` 라벨에 `필수` 배지 추가. 기획서 rev2 `데이터셋 이름 <span class="req">필수</span>` 축자이고 지시문 배지 목록에도 「이름 = 필수」로 있다. 이름은 종전부터 등록 게이트였고 표시만 없었다.

## 8. 완료 정의

`dev-package/work-items.yaml` 에 이 작업의 항목이 **없다** — 완료 정의 **미작성**. 대장·원장·HANDOFF 무접촉(지시문 지시).

## 9. 후속 항목

1. **Ted 재판정** — PRD 판정 4건(미결-4 ⓐ · 미결-11 ⓐ · PRD-19 · §3 게이트 표)이 「재판정 대기」로 열려 있다. 병합 조건이다.
2. **서버·화면 게이트 비대칭** — 관측 간격·Lv0 출처는 **화면만** 막는다. 서버 `catalog.py` 는 값이 없어도 저장하고 Lv1 이상에서 와도 저장한다(PRD-19 폐기 문면 그대로). API 직접 호출 경로는 막히지 않는다. 이 비대칭이 요구인지 결함인지 판정 필요.
3. **기존 행** — `observationInterval` 이 비어 있는 기존 데이터셋은 상세 수정에서 `DatasetEditForm` 을 탄다. 그쪽 폼은 여전히 관측 간격을 선택으로 다루므로(`detail/editFields.ts`) 등록과 수정의 필수 판정이 갈린다. 어느 검사에도 걸리지 않는다 — 게이트에도 Dockerfile 에도 배포 스크립트에도 없다.
4. **`INTERVAL_UNITS` 두 벌** — `upload/RegisterArea.tsx:50` 과 `detail/editFields.ts:65` 가 같은 6값을 각각 선언한다. 이번에 표시 라벨은 등록 쪽에만 붙어 상세 수정 폼은 `시`·`년` 으로 남는다. 한 자리로 모을지 판정 필요.
