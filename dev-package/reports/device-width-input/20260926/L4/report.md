# 레인 보고 — L4 게이트 조건 i · 정본 ⑨ · spec 틀 i 행(V1 · V10 게이트 · V13)

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` V1 · V10 · V13 · 부록 H · 우려 11ⓐ · 「구현 결정」(정본 문서 · 조건 i) · 「시험 결정」(selftest · green-by-skip 방지) · 「승인 요청」 템플릿 ⓐ · 부록 I 「L4」 행 · 「레인 확정」
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md` (a) · (e)
- 브랜치: `claude/dwi-l4` · 기준 `909fe89e`(L0a–L3b · 「레인 확정」 포함) · 구현 `6b57bcb8`
- task: `cf388db8b86347e3b61af84e6ac8590d`(범위 선언 10경로 · 게이트 `frontend-design-lint` · `frontend-design-lint-selftest` · `frontend-test` · `harness-eval`)
- 판정: **구현 완료 · 게이트 3 green · harness-eval red(판정) — 이 레인 변경과 무관(기준 트리에서 같은 과제가 같은 꼴로 실패 · §5).** 시험 RED(L4 vitest 22 실패 · selftest 새 사례 4 실패) → GREEN(L4 27 · selftest 30) · 전체 153파일 2237건 통과 · 저장소 트리 `media_rules=105 hover_rules=33 container_rules=0 i=0 i_exempted_hits=24`.

## 0. 시작 확인

- 기준: `git switch -c claude/dwi-l4 909fe89e` → `git log --oneline -1` = `909fe89e L3b 레인 보고를 더한다 …`. `npm ci`(frontend) 종료 0.
- hover 하위 조건 사전 실측(advisor ① 규칙 2 · 판정부를 켜기 전 같은 규칙의 임시 계수기로 저장소 CSS 22파일):
  - `:hover` 가 든 규칙 33 · 선택자 34 · `(hover: hover)` 밖 0 → 진행.
  - 문자열 `:hover` 37개와의 차이 3 = 주석 안 3개(`frontend/src/shell/primitives.css:6` · `frontend/src/shell/shell.css:13` · `frontend/src/shell/shell.css:146`). 선택자 34 와 규칙 33 의 차이 1 = `shell.css:78`–`79` `.backlink:hover` 두 선택자가 한 규칙.
- 폭 조건 사전 실측(advisor ① 규칙 1 · spec 작성 때의 61 은 쓰지 않음): `@media` 머리 105 · `@container` 0 · 허용 값 밖 폭 머리 **24** = 부록 H 24 와 파일 · 조건 · 개수가 줄마다 같다(차이 0 → 정지 조건 아님).
  - 머리 분포: `(hover: hover)` 33 · `(max-width: 640px)` 20 · `(pointer: coarse)` 15 · `(max-width: 900px)` 5 · `(max-width: 640px), (pointer: coarse)` 2 · `(max-width: 1180px)` 1 · `prefers-*` 5 · 허용 밖 24(부록 H).
  - 105 − 61 = 44 는 앞 레인(L1–L3b)이 더한 머리다(hover 감싸기 33 · 화면 파일 끝 `(pointer: coarse)` 블록 · `(max-width: 1180px)` 등).

## 1. 바뀐 것

| 파일 | 변경 |
|---|---|
| `frontend/scripts/design-families.mjs` | 공용 상수 `WIDTH_STEPS`(4단계) · `WIDTH_MAX` 640·900·1180 · `WIDTH_MIN` 641·901·1181 · `INPUT_ALLOWED` `(pointer: coarse)` · `(hover: hover)` |
| `frontend/scripts/design-lint.mjs` | 조건 i — `@media`·`@container` 머리 정규화 · 쉼표 갈래 · `and` 조건 판정 · 형식 밖(우려 11ⓐ) · 선언 없는 `@container` · 면제 목록(`--media-exempt` · 파일 · 조건 · 개수 · 사유 · 구멍 5종) · hover 하위 조건(둘러싼 모든 `@media` 의 모든 갈래 · 면제 없음 · 끄는 스위치 없음) · 요약 「폭·입력 조건 밖 i(면제 m)」 · 계수 `i= i_media= i_container= i_form= i_hover= i_holes= i_exempt= i_exempted_hits= media_rules= container_rules= hover_rules= media_prefers=` |
| `gates/tools/frontend-design-lint.sh` | env `COLAB_DESIGN_LINT_MEDIA_EXEMPT`(기본 `gates/fixtures/frontend-design-lint/media-exempt.txt`) · 부재 78 · 준비 확인 순서(목록 → 파일 존재) 유지 · 머리말 i |
| `gates/tools/frontend-design-lint-selftest.sh` | 사례 26 → 30 · 두 expect 함수에 목록 env · ⓛ 에 `--media-exempt` · ⓖ 78 사유 확인 줄 · ⓘ1–ⓘ4 · 머리말 · 끝 문장 |
| `gates/fixtures/frontend-design-lint/` | 새 `media-exempt.txt`(부록 H 16줄 · 24건) · 기존 트리 19개 빈 목록 · `green-e/src/shell/primitives.css:3` · `red-e/src/components/x/x.css:3` 같은 줄 감싸기 · 새 트리 `green-i` · `red-i` · `red-i-hover` |
| `gates/README.md` | `frontend-design-lint` 행 i · 78 · 못 보는 것 · selftest 행 **30**(사례 설명) |
| `docs/design-system.md`(손글만) | 머리말 a~i · 표지 밖 목록에 ⑨ · ① 토큰 행 터치 분기 · ⑤ 새 줄 4 · 캡처 규칙 6크기 × 2테마 · ⑥ 제목 a~i · 요약 끝 · i 행 · 준비 실패 · 못 보는 것 · ⑧ 「수치 판정」 행 · 새 ⑨(소제목 7) |
| `.agents/skills/to-spec/SKILL.md` | 디자인 제약 머리 a~i · h 행 다음 i 행 |
| `.agents/skills/design-review/SKILL.md` | 토큰 행 a~i 한 곳(「정적 합격선」 행 불변) |
| `frontend/test/device-width-input-20260926-L4.test.ts` | 새 시험 27건 |

- 생성 블록(h): 입력(`tokens.css` · `primitives.css` · 목록 3종) 변경 0 → 다시 쓸 것 없음(`design-docs.mjs --check` 문서 표 갈림 0). selftest 뼈대 문서 불변 · 세 번째 생성 블록 없음.
- 제품 CSS · TSX · `vite.config.ts` · L2b/L3b 시험 변경 0.

## 2. 시험 RED → GREEN

- L4 vitest(27건): RED `Tests 22 failed | 5 passed (27)` → GREEN `27 passed`.
  - RED 인용: `AssertionError: 절 부재: ⑨: expected -1 to be greater than or equal to 0` · `expected undefined to be '105'`.
  - 먼저 통과한 5건 = 면제 목록 3(시험 작성 단계에서 부록 H 로 만든 목록 파일) · 판정부 종료 0(옛 판정부는 모르는 인자를 건너뜀 · 계수 단언은 RED) · ⑤ 누름 피드백 다음 줄(기존 단언과 같은 내용).
  - RED 단계에서 자기 시험 1건 정정: 「`| btn |` 행 1」이 ③ 화면 편차 표의 `| btn |` 행까지 세어 2 였다 → followups L1 과 같은 거르기(`<button class="btn"`)로 바꿈(기대값 1 불변).
- selftest: RED = 기존 26 전건 기대대로 · 새 i 사례 실패(인용 `ⓘ2 … — red 여야 하는데 통과했다` · `ⓘ4 … — red(준비 · 78) 여야 하는데 rc=0`) → GREEN 30.
  - spec RED 확인(red-e): 같은 줄 감싸기 뒤에도 ⓤ 기대 줄(`x.css:3 .btn-primary:hover` · `e=6 e_bare=4 e_important=0 e_holes=2`)이 그대로 맞아 ⓤ 에 `i_hover=1` 줄을 더하지 않았다. ⓣ 도 그대로(`e_exempted_hits=1 primitives=4`).
- 기존 시험 수정 0 · 단언 삭제 0. 문서 앵커를 고정한 기존 4파일(`design-fix-followups-20260925-L1` · `design-fix-20260924-F-final` · `design-fix-20260924-F-css` · `design-fix-20260924-L1`) 141건 수정 없이 green. `npx tsc --noEmit` 오류 0.

| 묶음 | 단언 |
|---|---|
| ⑴ 공용 상수 | 4단계 · max 640/900/1180 · min 641/901/1181 = 단계 경계 · 입력 2표기 |
| ⑵ 면제 목록 | 부록 H 표 길이 16 · 합 24 먼저 → 목록 = 부록 H · 사유 전부 · 영구 예외 = 1536 하나 · 나머지 23 「다음 intent」 |
| ⑶ 저장소 트리 | 판정부 종료 0 · `media_rules=105` · `hover_rules=33` · `container_rules=0` · `i=0` · 갈래 전부 0 · `i_exempt=16` · `i_exempted_hits=24` · 「폭·입력 조건 밖 0(면제 16)」 |
| ⑷ ⑨ | ⑧ 뒤 · ①–⑦ 앵커 · 소제목 7(순서) · 폭 표 = 상수 · 낮은 높이(≈500 · 잠정 · 다음 intent) · 넓은 표(카드 · 열 고정) · 지도 칸 경계 = `MAP_CELL_BOUNDARY`(코드에서 import) · 허용 값 표 = 상수 · 16줄 · 24건 · ⑨ 안 대비 줄 · btn 행 0 |
| ⑷ ⑤ ⑥ | 머리말 a~i · 문서 a~h 0 · ⑤ 새 줄 4 · 누름 피드백 다음 줄 = 비활성 · 캡처 6크기 × 2테마 · 3폭 0 · ⑥ i 행 · 요약 끝 · 78 줄 · 못 보는 것 · ① 토큰 행 · 대비 줄 1 · btn 행 1 |
| ⑸ | to-spec a~i · h 다음 i 행 · design-review 토큰 행 a~i · 정적 합격선 행 1 · selftest 사례 수 = 끝 문장 = README = 30 |

## 3. 게이트 판정부 조건 i

- 허용: `max-width` 640·900·1180px · `min-width` 641·901·1181px · `(pointer: coarse)` · `(hover: hover)` · `prefers-*`(세기만 · `media_prefers`). 값은 `design-families.mjs` 한 곳.
- 형식 밖(i_form): 높이 · 범위 문법 · em·rem · `orientation` · `aspect-ratio` · `any-pointer`·`any-hover` · `(pointer: fine)` · `(hover: none)` · `not` · `only` · 매체 종류(`screen` · `all`) · 그 밖의 기능.
- 면제 줄 대조 키: 파일 + 정규화한 머리(붙여 쓴 표기 = 띄어 쓴 표기). 구멍 = 형식 오류 · 같은 조건 두 줄 · 빈 사유 · 맞는 것 없음 · 개수 어긋남 — 구멍 줄은 아무것도 면제하지 않는다. `@container` · 형식 밖 조건도 선언하면 면제된다(우려 11ⓐ 「필요하면 면제 목록에 사유와 개수」). hover 하위 조건은 면제 줄을 읽지 않는다.
- hover 하위 조건: `:hover` 가 든 규칙마다 둘러싼 `@media` 가 1개 이상이고, 둘러싼 **모든** `@media` 의 **모든** 쉼표 갈래에 `(hover: hover)` 가 `and` 조건으로 있어야 한다.
- 요약 끝: 판정부 요약줄 끝 = 「폭·입력 조건 밖 i(면제 m)」 · 게이트 셸이 그 뒤에 「문서 표 갈림 h」를 붙인다(기존 구조).

selftest 사례(30 = green 7 · red 16 · red(준비) 7 · spec 의 30 과 같음):

| 사례 | 트리 · 입력 | 기대 | 확인 줄 |
|---|---|---|---|
| 기존 26(ⓐ–ⓩ) | 트리마다 빈 `media-exempt.txt` | 기존 그대로 | ⓖ 에 「대상 CSS 가 0건이다」 줄 추가 · ⓛ 에 `--media-exempt` |
| ⓘ1 | `green-i` | green | 「폭·입력 조건 밖 0(면제 2)」 · `i=0 … i_exempt=2 i_exempted_hits=3 media_rules=8 container_rules=1 hover_rules=1` |
| ⓘ2 | `red-i` | red | `i=17 i_media=4 i_container=1 i_form=9 i_hover=0 i_holes=3 i_exempt=3 i_exempted_hits=0 media_rules=14 container_rules=1 hover_rules=0` · 구멍 셋 문장 · `x.css:12 @media (pointer: fine)` |
| ⓘ3 | `red-i-hover` | red | `i=2 … i_hover=2 i_holes=0` · `x.css:4 .x-page .x-row:hover`(쉼표 OR) |
| ⓘ4 | `green-i` · `COLAB_DESIGN_LINT_MEDIA_EXEMPT=/nonexistent/…` | 78 | — |

- 픽스처 grep(새 사례 트리 제외): 기존 19트리의 `@media` = `(max-width: 640px)` 만 · `:hover` = `green-e/src/shell/primitives.css:3` · `red-e/src/components/x/x.css:3` 두 곳 모두 `@media (hover: hover) { … }` 안 → 조건 밖 `:hover` 0 · 비허용 `@media` 0.

## 4. 정본 ⑨ · 문서 손글

- ⑨ 소제목 7: 폭 4단계 · 판단 기준 · 터치 기기 규칙 · 낮은 높이 규칙 · 넓은 표 원칙 · 지도 · 그림 위 도구 원칙 · 허용 폭 값 · 면제 목록.
- 폭 표 · 허용 값 표는 공용 상수와, 지도 칸 경계 행(810px · `MAP_CELL_BOUNDARY`)은 `frontend/src/components/preview/useMapCellWidth.ts` 의 상수와 vitest 가 대조한다.
- ⑤ 새 줄 4: `9. [i]` · 터치 기기 · 마우스 전용 동작 · 캡처 도구 수치 모드 실행. 캡처 규칙 줄 바로 뒤에 두었다(「누름 피드백」 줄과 비활성 줄 사이 아님).
- ⑨ 에 「대비 4.5:1 이상」 · `| btn |` 행 없음. ①–⑧ 번호 · ⑤ · ⑦ 앵커 불변.
- ① 기본 층 행의 16px 문장은 L2a 가 이미 고쳐 두어(「`shell.css` 의 「640px 이하 또는 터치 기기」 블록 한 곳」) 이번에 바꾸지 않았다.

## 5. 게이트(호스트 단독 · `6b57bcb8` 트리 · 단독 실행)

| 게이트 | 결과 |
|---|---|
| `frontend-design-lint-selftest` | green — 검사 30건 전건 기대대로(green 7 · red 16 · red(준비) 7) |
| `frontend-design-lint` | green — 파일 22 · … · 프리미티브 맨 정의 밖 0(면제 0) · 폭·입력 조건 밖 0(면제 16) · 문서 표 갈림 0 |
| `frontend-test` | green — 153파일 2237건 통과 · 실패 0 |
| `harness-eval` | **red(판정 · 종료 1)** — 과제 20 · 실행 40 · green 17 · 판정실패 관측 3(H15 1/2 · H16 0/2 · H17 1/2) · 초 p50 27.8 / p95 56.0 · 소요 1243초 |

- harness-eval 실행: `COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=93 COLAB_EVAL_BUDGET=2.01`(로컬 구독 CLI · 과제마다 2회). 시험 환경 파일(`~/.colab-v2-test-32.env`)이 `COLAB_HARNESS_EVAL_EXEMPT=1` 을 선언하고 있어 게이트가 「실행이 이긴다 — 면제 선언은 무시했다」를 찍었다. 이 레인은 면제를 선언하지 않았다.
- 원인 분리(같은 호스트 · 같은 설정 · `COLAB_EVAL_ONLY`):

| 과제 | L4 트리(전수 실행) | 두 skill 파일만 `909fe89e` 로 되돌린 트리 | L4 트리 재실행 |
|---|---|---|---|
| H15-zero-targets | 1/2 | 1/2 | — |
| H16-lenient-default | 0/2 | 0/2 | — |
| H17-hidden-skip-count | 1/2 | 2/2 | 2/2 · 2/2 |

  - H15 · H16 은 기준 트리에서도 같은 꼴로 실패한다. 세 과제의 과제 · 픽스처 · 기대 스크립트는 `to-spec` · `design-review` 를 참조하지 않는다. 2026-09-12 실측(`355fd9dc`)에도 H15 · H16 실패가 있다.
  - H17 은 L4 트리 재실행 2회가 모두 2/2 — 전수 실행의 1/2 는 회차 변동이다.
  - H16 실패 줄: `expect red — 상태2(면제)가 건수 노출을 말하지 않는다.` 응답의 상태2 줄은 「`waived — 시험 N건 (합격선 면제)` 을 찍고 exit 0」이다. 기대 스크립트의 문구 대조와 모델 응답 표현의 불일치로 읽힌다 — 판정 필요(기대를 넓혀 green 을 만들지 않았다).
- 러너가 저장소 안에 만든 결과 폴더(`eval/harness/results/<시각>/` 6개)는 레인 범위 밖이라 저장소 밖으로 옮겼다(커밋 0).
- 이 보고서 커밋 뒤 같은 4게이트를 `gates/run.sh task` 로 한 번 더 돌려 인계를 시도한다(최종 gate-summary 절대경로와 3계수는 인계 메시지).

## 6. 원한 결과 대조 · 이탈 · 남은 것

- V1: 충족(⑨ · ⑤ 4줄 · ⑥ i 행 · 머리말 · 캡처 규칙 · 기존 단언 수정 없이 green · design-review 정적 합격선 행 불변).
- V10(게이트): 충족(hover 하위 조건 켠 채 · 쉼표 OR red 사례 · 저장소 `i_hover=0` · `hover_rules=33`).
- V13: 충족(조건 i · 면제 24건 16줄 · 구멍 red · selftest 30).
- 부록 I L4 자기 게이트 `harness-eval`: 미달(red(판정) · 기준 트리 동일 · 위 표).
- spec 수치와 실측 차이: `media_rules` 61(spec 작성 때) → 105(L4 시작 트리 · §0). selftest 사례 수는 spec 과 같은 30.
- spec 초과: red-i 에 우려 11ⓐ 형식 5종(`(pointer: fine)` · `(hover: none)` · `any-pointer` · `not` · `only`) 추가 · 계수 `media_prefers` 추가 · ⑧ 「수치 판정」 행 추가 · 면제 구멍 「같은 조건 두 줄」 추가 · 매체 종류(`screen` 등)를 형식 밖으로 판정(「그 밖의 기능」에 포함해 읽음 · 현재 사용 0).
- 해석 1(판정 필요 시): hover 하위 조건의 「모든 `@media`」를 문언대로 적용 — 바깥 폭 `@media` 안의 `@media (hover: hover)` 도 red(현재 사용 0 · `@media (max-width: 640px) and (hover: hover)` 로 대체 가능).
- 못 보는 것(⑥ · README 기재): JS 폭 측정 배치 · TSX 입력 조건 문자열(입력 방식 훅 한 곳 · L1 vitest) · `src` 밖 HTML · 렌더된 크기(캡처 수치 모드). 추가로 `@custom-media` 같은 문장형 규칙은 게이트 어디에도 걸리지 않는다(현재 사용 0 · 후속 후보).
- 후속 후보:
  - harness-eval H15 · H16 기준 트리 실패(과제 기대 문구 · 모델 응답 표현) — 하네스 intent 에서 판정.
  - `~/.colab-v2-test-32.env` 의 `COLAB_HARNESS_EVAL_EXEMPT=1` 상시 선언(실행 선언이 이기므로 판정은 막지 않지만, 실행 선언을 빠뜨리면 면제로 green 이 된다) — 게이트는 건수를 찍으나 호스트 설정 파일이라 어느 검사에도 걸리지 않는다.
  - 판정부 머리말 사용법 줄(`Usage: …`)이 `--primitives` · `--media-exempt` 를 적지 않는다(P2b 부터 · 어느 검사에도 걸리지 않음).
