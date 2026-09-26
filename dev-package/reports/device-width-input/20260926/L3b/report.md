# 레인 보고 — L3b 업로드 터치 문구 · 체크 칸 · 대표 라디오 누름 칸(V7 체크 칸 2 · V11 · V12 업로드)

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` V7(부록 B 36 · 45) · V11 · V12 · 우려 2ⓐ · 우려 9ⓐ · 「새 문구안」 3–5 · 부록 I 「L3b」 행 · 「레인 확정」(파일 끝 터치 블록 · 세로 넘침 대조 · 문구 확정 · `frontend-visual` 임시 규칙)
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-l3b` · 기준 `00b929cc` · 구현 `862bbe62`
- task: `49de549bdada48ceb8f34fcf165a7e13`(범위 선언 8경로 · 게이트 `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint` · `frontend-visual`)
- 판정: **구현 · 게이트 · 수치 완료.** 시험 RED 21 실패(L3b 17 · L2b 4) → GREEN 106(L3b 22 · L2b 84) · 전체 152파일 2210건 통과 · 게이트 green 5 / red(판정) 0 / red(준비) 0 · 페이지 3 = 선언 URL 3 · 390 레인 L3b 판정 red 0 · 준비 red 0 · 레인 밖 44 red 2 → 0 · 1440 마우스 대 B0 픽셀 0(6장면 12장).

## 0. 시작 확인

- advisor ① 4 — L0b 측정은 36 · 45 를 label 상자로 잰다: `frontend/scripts/visual-baseline/measure.js:71`(입력이 label 안이면 label 상자 · `via: label`) · `targets.json` notes 「label 안의 입력은 대상과 무관하게 label 상자를 잰다(36 · 45 번)」. 정지 사유 없음.
- advisor ① 1 — 중복 문자열 검사(`frontend/test/toast-copy-20260906.test.tsx` 「하드코드 중복 0건」)는 `toastCopy.FIXED_COPY` 의 문면이 상수 모듈 밖 `src/` 에 따옴표 · JSX 맨몸 글자로 다시 있는지 센다. 새 터치 문구 3개는 `toastCopy.ts` 에 없고 `FIXED_COPY` 와 겹치지 않는다(`toastCopy.ts` 에 「고르」 · 「끌어다」 문자열 0 · L3b 시험이 두 조건을 단언). 검사는 전체 실행에서 green.

## 1. 바뀐 것

| 파일 | 변경 |
|---|---|
| `frontend/src/components/upload/FileDropCard.tsx` | `:53`–`56` 상수 쌍 `DROP_TITLE`/`DROP_TITLE_TOUCH` · `DROP_SUB`/`DROP_SUB_TOUCH`(마우스 원문 바로 다음 줄이 터치 문구) · `:156` 입력 방식 훅 · `:220` · `:225` 갈래. 폴더 주석에 터치 한 줄 |
| `frontend/src/components/upload/UploadModal.tsx` | `:89`–`90` 상수 쌍 `RESUME_HINT`/`RESUME_HINT_TOUCH` · `:249` 입력 방식 훅 · `:1488` 갈래(`up-resume-hint` · `ub-hint` 그대로). 안내 문구 밖 변경 0 |
| `frontend/src/components/members/MemberPermissionGrid.tsx` | `:200` 권한 체크 칸을 글자 없는 label 로 감쌈(`aria-label` · `disabled` · `onChange` 그대로) |
| `frontend/src/components/common/VariableTable.tsx` | `:160` 대표 라디오를 글자 없는 label 로 감쌈(편집 · 읽기 전용 같음) |
| `frontend/src/components/members/members.css` | `:53` 조건 없는 `.memtbl td.pc > label { display: block; }` · 파일 끝 터치 블록 안 `:142` `.memtbl td.pc > label`(flex 가운데 · 최소 높이 · 최소 가로 `var(--control-height)`) |
| `frontend/src/components/common/variableTable.css` | `:100` 조건 없는 `.vartable td > label { display: block; }` · 파일 끝 터치 블록 안 `:148` `.vartable td > label`(같은 선언) |
| `frontend/test/device-width-input-20260926-L3b.test.tsx`(새) | 아래 §2 |
| `frontend/test/device-width-input-20260926-L2b.test.ts` | 머리 주석대로: `TAPS` 에 36 · 45(`lane: 'L3b'`) · `TAPS.length` 34 → 36 · 레인 L2b 34 대조는 레인 거르기(`L2B_TAPS`) · 레인 L3b 2항목 단언 추가 · `L3B_ONLY` 기대값을 L3b 선택자 목록으로. 단언 삭제 0 · 블록 = 1 · 파일 끝 단언 그대로 |

- 셸 · 토큰 CSS 변경 0 · `toastCopy.ts` 변경 0 · 대상 목록 · 측정 도구 변경 0 · 다른 시험 수정 0.

## 2. 시험 RED → GREEN

- RED(시험만 · 제품 코드 0 · `00b929cc` 위): L3b `Tests 17 failed · 5 passed (22)` · L2b `Tests 4 failed · 80 passed (84)`. 예: `expected undefined to be '파일을 끌어다 놓으세요'`(상수 없음) · `expected '파일을 끌어다 놓으세요' to be '눌러서 파일을 고르세요'` · `expected 'TD' to be 'LABEL'` · `members: expected [ '.settabs .st' ] to deeply equal [ '.memtbl td.pc > label', …(1) ]`. 처음부터 통과한 5 = 대상 3쌍 개수 · 등록부 겹침 0 · 마우스 문구 2(원문 그대로라 이미 참) · CSS 대상 개수.
- 시험 작성 중 발견: vitest 설정의 CSS 스텁이 `members.css?raw` · `variableTable.css?raw` 를 빈 문자열로 만든다(`frontend/vite.config.ts` `css.include` 밖). CSS 원문은 L2b 시험 선례대로 `node:fs` 로 읽는다(설정 변경 0 · 규칙 수 > 5 를 먼저 단언).
- GREEN(`862bbe62`): `Tests 106 passed (106)` · 전체 `Test Files 152 passed · Tests 2210 passed` · 타입 검사 오류 0. 단언 삭제 0.
- 구성: ⑴ 문구 자리 — 3쌍 각각 마우스 · 터치 상수 값 · 두 문자열이 `src/` 전체에서 자기 파일 한 곳에만 있음 · 터치 상수가 마우스 상수 바로 다음 줄 · 등록부 겹침 0. ⑵ 드롭 영역(모듈 모의 두 갈래 · 요소 수를 먼저 셈) — 터치 제목 · 보조 줄 정확 일치 · 영역 글자에 「폴더」 · 「끌어다」 0 · 「파일 고르기」 · `multiple` 유지(V11) / 마우스 원문 정확 일치. ⑶ 이어 올리기 안내 — 진입 컴포넌트 실물(재개 요청으로 무장)에서 안내 1개를 센 뒤 두 갈래 정확 일치. ⑷ label — 두 갈래 모두 체크 칸 8 · 라디오 2(편집 · 읽기 전용) 가 label 바로 안 · label 글자 0 · 자식 1 · `for` · `aria-label` 없음 · 칸의 자식 = label 1 · 역할 · 이름 조회가 그 입력. 한 번 누름 = 바뀜 한 번(§4). ⑸ CSS — 조건 없는 `display: block` 한 규칙 · 터치 블록 선언 5개 정확 일치(글자 선언 0) · label 을 고르는 규칙 = 두 개뿐.

## 3. 문구(「새 문구안」 3–5 확정 원문 · 우려 9ⓐ)

| 자리 | 터치 | 마우스 · 판별 불가(변경 없음) |
|---|---|---|
| 드롭 영역 제목 `.big` | 눌러서 파일을 고르세요 | 파일을 끌어다 놓으세요 |
| 드롭 영역 보조 줄 `.muted` | 여러 개를 한 번에 고를 수 있어요 | 여러 개를 한 번에, 폴더째 끌어다 놓아도 돼요 |
| 이어 올리기 안내 `up-resume-hint` | 같은 파일을 다시 고르면 남은 조각부터 이어서 올라가요. | 같은 파일을 다시 끌어다 놓으면 남은 조각부터 이어서 올라가요. |

- 기존 시험 `upload.test.tsx:496`(마우스 보조 줄) · `up-resume-hint` 3곳 · 업로드 장면 잠금 시험 수정 없이 green.

## 4. label 감싸기 근거(우려 2ⓐ · advisor ① 3)

- 이름: 입력의 `aria-label` 그대로(label 글자 0) — 시험이 체크 칸 「{이름} · {열}」 · 라디오 「대표 {n}」 이름으로 그 입력을 찾는다(두 갈래 · 편집 · 읽기 전용).
- 한 번 누름 = 한 번: 구성원 — 편집 시작 뒤 label 을 누르면 해제 → 선택 · 바뀐 칸 표식, 이어 체크 칸을 누르면 원래대로(두 번 불리면 첫 누름에서 되돌아감). 다른 사람 칸 불변. 변수 표 — label 한 번 누름 → `onRows` 1회(대표 [거짓, 참]) · 라디오 한 번 누름 → 누계 2회.
- 마우스 모양: label 을 더해 마우스 DOM 이 바뀌었으므로 1440 픽셀 비교가 유일한 증거다 → §6-2 픽셀 0.

## 5. 게이트(task 실행 · 호스트 단독)

- 실행: `gates/run.sh task`(선언 5개 한 번) · `COLAB_TEST_ENV_FILE=~/.colab-v2-test-32.env` · `COLAB_TASK_ID=<task>` · `COLAB_VISUAL_URLS` = 이 레인이 띄운 audit 빌드(`vite preview --config audit.vite.config.ts --host 127.0.0.1 --port 47483 --strictPort` · 시작 때 PID 저장 · 그 PID 만 종료)의 3건: `audit-design.html?scene=members&design=full` · `audit-design.html?scene=detail&design=full` · 업로드 입구 `audit-upload.html?upload=1&labSettings=0&operator=0`. `COLAB_VISUAL_EXEMPT` 미사용.

| 게이트 | 결과(`862bbe62` 트리) |
|---|---|
| `frontend-typecheck` | green — 오류 0 |
| `frontend-test` | green — 2210 통과 · 실패 0 |
| `frontend-fixture-reach` | green — 도달 213 · 금지 모듈 0 |
| `frontend-design-lint` | green — 파일 22 · a–h 0 · 문서 표 갈림 0 |
| `frontend-visual` | green — **페이지 3(= 선언 URL 3)** · 13px 미만 0 · 대비 < 4.5 0 · 스크린샷 6 |
| 계 | green 5 / red(판정) 0 / red(준비) 0 |

- 이 보고서 커밋 뒤 같은 명령으로 한 번 더 돌려 인계한다(최종 gate-summary 절대경로와 3계수는 인계 메시지).

## 6. 수치(자기 캡처 · audit 빌드 = `862bbe62` 트리)

- 실행: `capture.py --label dwi0926-l3b-cap --parallel 2 --metrics --only members,detail,upload,upload-metadata,detail-preview-map,detail-preview-map-value`(빌드 포함 · 72장 · 종료 0). 45 번이 그려지는 장면 넷(`detail` · `upload-metadata` · 상세 지도 두 장면)을 모두 넣었다.

### 6-1. 390 터치 판정

- `judge.mjs --lane L3b`(부록 I 자기 장면 `members` · `detail` · `upload` × 2테마 · 6파일): `files=6 lane=L3b red=0 readiness=0 notMeasured=8 captureBlind=0 exemptHits=0 smallOther=0 outsideRed=16:0,44:0,넘침:0,가림:0 exit=0`.
- 같은 판정을 45 번 장면 전부로 넓힘(12파일): `files=12 lane=L3b red=0 readiness=0 … smallOther=0 outsideRed=16:0,44:0,넘침:0,가림:0 exit=0`.
- 레인 밖 44 red: L3a 보고의 `detail` 대표 라디오 2(두 테마) → **0**.
- 대상 상자(label · `via: label` · 두 테마 최솟값 · 가로×세로):

| # | 장면 | 390 | 844x390 | 820 | 1024 | 1180 |
|---|---|---|---|---|---|---|
| 36 | `members`(12개 × 2테마) | 44×44 | 92×44 | 86.8×44 | 92×44 | 92×44 |
| 45 | `detail` · `upload-metadata` · `detail-preview-map` · `detail-preview-map-value` | 44×44 | 44×44 | 44×44 | 44×44 | 44×44 |

- 5크기 모두 36 · 45 의 가로 · 세로 44 미만 0(B0 에서는 입력 자체 13×13).

### 6-2. 1440 마우스 대 B0

- `diff.mjs --subset --viewport 1440 <B0> dwi0926-l3b-cap` → **12장(6장면 × 2테마) · red 0 · 엄격 픽셀 0 · 종료 0.** B0 = 워크트리 `agent-abf926c2ed31f5520` 의 `frontend/.visual/dwi0926-base`(읽기만).

### 6-3. 세로 넘침 대조(「레인 확정」)

- 방법: 수치 전용 실행기의 측정 직후 같은 세션에서 컨테이너 상자(괄호 = 자손 위–아래 · 컨테이너 위 기준)를 읽는 일회용 래퍼 · 라이트 · 터치 390 · 820 · 1024 ＋ 같은 폭 마우스(`390x844:mouse` · `820x1180:mouse` · `1024x1366:mouse`). 스크린샷은 §6 캡처의 390 · 820 · 1024 터치(`members` · `detail` · `upload` · `upload-metadata`)를 눈으로 확인.

| 장면 · 컨테이너 | 폭 | 터치 | 같은 폭 마우스 | 설명 |
|---|---|---|---|---|
| `members` 사람 카드 행 `.memtbl tbody tr`(3) | 390 | 366.5(11–355.5) | 278.5(11–267.5) | +88 = 권한 칸 4 × 22. 640px 이하 카드 모양의 칸 `td.pc` 39 → 61(label 22 → 44 · 위아래 여백 8) |
| 권한 칸 `td.pc` · label | 390 | 칸 61(9–53) · label 44×44(체크 칸 15.5–28.5) | 칸 39(9–31) · label 높이 22 × 가로 20(체크 칸 3–16) | label 이 칸 오른쪽 44 칸 · 체크 칸은 그 가운데(마우스보다 12px 왼쪽) |
| 표 행 `.memtbl tbody tr`(3) | 820 · 1024 | 65 · 65 · 64.5(0–65) | 61.5 · 61.5 · 61(0–61.5) | +3.5 = 칸 `td.pc` 여백 10.5 × 2 ＋ label 44(이름 두 줄 칸 61.5 보다 큼) |
| label `.memtbl td.pc > label` | 820 · 1024 | 높이 44 × 칸 폭(86.8–104) | 높이 22 × 칸 폭 | 칸 폭을 채움 · 체크 칸 15.5–28.5(가운데) |
| `detail` 변수 표 행 · 대표 칸 | 390 · 820 · 1024 | 44.5 · 칸 44.5(0.5–44.5) · label 44×44 | 36.9 · 칸 36.9(7.5–29.9) · label 높이 22.4 × 가로 40.5 | +7.6 = label 22.4 → 44. 대표 열 폭 40.5 → 44 |
| `detail` 표 틀 `.vt-box` | 390 | 81.8(1–80.8) | 89.2(1–73.2) | 마우스 +7.4 = 가로 스크롤 막대 15 − 행 7.6(터치는 막대를 겹쳐 그림) |
| 같음 | 820 · 1024 | 81.8 | 74.2 | +7.6 = 행 |
| `upload-metadata` 변수 표 행 · 대표 칸 | 390 | 44.5 · label 44×44 | 44.5 · label 높이 22.4 × 가로 40.5 | 640px 이하 입력 44 가 이미 행 높이(두 입력 같음) |
| 같음 | 820 · 1024 | 44.5 | 40.5 | +4 = 빼기 칸 `.vt-del` 44(L2b 43 · 이 레인 변경 아님) · label 44 도 같은 행 안 |
| `upload-metadata` 표 틀 `.vt-box` | 390 · 820 · 1024 | 81.8 | 96.8 · 77.8 · 77.8 | 390 마우스 가로 스크롤 막대 15 · 820 · 1024 +4 = 행 |
| `upload` 드롭 영역 `.dropzone` | 390 | 262.4(35–227.4) | 262.4 | 같음. 보조 줄 폭 165.6 대 228.4(짧은 문구) · 제목 폭 145.9 같음 |
| 같음 | 820 · 1024 | 262.4 | 258.4 | +4 = 「파일 고르기」 `.btn` 토큰 40 → 44(셸 · 기존) |

- 문서 가로 폭: 터치 = 창 폭(390 · 820 · 1024 · 넘침 0). 마우스 390 · 상세 820 · 1024 의 375 · 805 · 1009 는 세로 스크롤 막대 15.
- 스크린샷 판독: 자손이 행 · 칸 · 틀 밖으로 삐져나와 보이는 곳 0. 390 권한 카드의 「프로젝트 생성」 칸만 폭이 좁은(180 대 290) 모양은 B0(`dwi0926-base/members-light-390.png`)에도 같다 — 이 레인 변경 아님(§7 후속).
- 판정: 모든 차이가 ⑴ label 22 → 44(대상 36 · 45), ⑵ 다른 레인 · 셸 토큰 40 → 44, ⑶ 마우스 스크롤 막대 15 가운데 하나로 설명된다. 판정 요청 0.

## 7. 원한 결과 대조 · 이탈 · 남은 것

- 충족: V7(36 · 45) 터치 5크기 label 상자 가로 · 세로 ≥ 44 · 390 레인 L3b red 0 · 준비 red 0 · 레인 밖 44 red 0. V11 — 터치 드롭 영역이 기존 「파일 고르기」 경로를 말한다(단추 · 여러 개 고르기 유지 · 새 입력 0). V12 — 터치 3문구 확정 원문 · 마우스 원문 그대로(정확 일치 시험 · 기존 시험 수정 0). 우려 2ⓐ — 칸을 채우는 label · 터치 44 · 마우스 1440 픽셀 0. 우려 9ⓐ — 터치 문구에 폴더 0.
- 이탈 · 초과:
  - 마우스 문구도 이름 붙은 상수(`DROP_TITLE` · `DROP_SUB` · `RESUME_HINT`)로 옮겼다(L3a 선례 · 화면 글자 불변 · 「터치 상수는 마우스 상수 바로 옆」을 시험으로 고정하려고).
  - label 이 마우스에서도 칸 폭을 채우므로 마우스로 칸의 빈 곳을 눌러도 체크 칸 · 라디오가 바뀐다(모양 불변 · 우려 2ⓐ 의 「칸 전체를 누름 영역으로」가 입력 방식을 가리지 않음).
  - 640px 이하 터치 권한 카드에서 체크 칸이 44 칸 가운데라 마우스보다 12px 왼쪽에 선다.
  - 45 번 장면 넷 · 업로드 메타데이터 장면을 캡처 · 판정 · 1440 비교에 더했다(부록 I 은 `members` · `detail` · `upload`).
  - L2b 시험 두 단언의 제목 글을 새 기대값에 맞게 바꿨다(단언 삭제 0).
- 남은 것 · 후속:
  - 390 권한 카드 「프로젝트 생성」 칸 폭 180(다른 칸 290) — B0 에도 있음 · 판정 스크립트 · 게이트 어디에도 걸리지 않는다(누름 칸 크기는 44 충족). 배치 정리 intent 후보.
  - `vite.config.ts` 의 CSS 스텁이 `css.include` 밖 파일의 `?raw` 까지 빈 문자열로 만든다(`members.css` · `variableTable.css` 등) — `?raw` 로 읽고 개수를 먼저 세지 않는 시험은 「규칙 0」으로 조용히 통과할 수 있다. 어느 게이트에도 걸리지 않음 · 후속 후보.
  - 부록 J 실기기 확인 후보: 터치에서 권한 칸 · 대표 칸의 빈 곳을 눌러 한 번만 바뀌는지 · iPhone 「파일 고르기」 가 여러 파일 고르기를 여는지.

## 8. 캡처 폴더(추적 제외 · `frontend/.visual/`)

- `dwi0926-l3b-cap`(72장 · 수치) · `l3b-390` · `l3b-390-lane`(390 수치 복사) · `dwi0926-l3b-vert`(세로 대조) · `dwi0926-l3b-diff-1440` · 판정 출력 `dwi0926-l3b-judge-390-L3b.json` · `dwi0926-l3b-judge-390-L3b-lane.json` · 일회용 래퍼 `l3b_boxes.py`.
