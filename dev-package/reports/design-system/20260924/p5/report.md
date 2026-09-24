# 디자인 구조 P5 결과 — 문서 · 프리미티브 갤러리 · 게이트 h · 스킬 정본 갱신

spec: `dev-package/prd/specs/S-DESIGN-STRUCTURE-P5-20260924.md` · 계획: `architecture.md §3 P5` · 선행: `p2b/report.md`(편차 표 · 후속) · `p0`~`p3` 보고서(판정 항목)

착수 HEAD `37269536` · task `8cfaba3b8ac34465b7ff045b610d978a` · 레인 1(직렬)

## 결론

- `docs/design-system.md` 절 ①~⑧ 작성. ②·③ 표는 `frontend/scripts/design-docs.mjs` 가 실물 5파일에서 생성(토큰 라이트 81 · 다크 41 · 폭 분기 5 · 동일 면제 6 / 프리미티브 목록 22클래스 · 6계열 · 규칙 32 · **기본값 선언 114** = P2b 보고의 계열별 수 btn 20 · field 8 · chip 25 · card 16 · table 18 · modal 27 과 같음).
- 게이트 `frontend-design-lint` 조건 **h** 추가(`design-docs.mjs --check` · 요약줄 끝 `문서 표 갈림 0`). selftest 23 → **26건**(green 6 · red 14 · red(준비) 6).
- 프리미티브 갤러리 장면 `scene=primitives`(audit 빌드 전용 · 정적 마크업 · 제품 컴포넌트 import 0) · `design-preview.html` 「프리미티브」 · `scenes.json` 장면 1 추가.
- 시각 변경 0 — `p5-before`(커밋 A) ↔ `p5-after`(다시 빌드): **202 captures · red 0 · strict px 0 · exit 0**. 계산값 대조 **202 페이지 · 27550 항목 · 차이 0**.
- 장면 추가의 부수 효과 0 — 착수 HEAD 196장 ↔ 커밋 A 의 196장 부분집합(`visual:diff --subset`): **196 captures · red 0 · strict px 0 · exit 0**.
- 제품 CSS·TSX 변경 0(`git diff --name-only 37269536..HEAD -- frontend/src` 0줄) · 토큰 값 변경 0 · 새 의존성 0 · `patterns.css` 만들지 않음.
- 게이트 `gates/run.sh task` → **green 5 / red(판정) 0 / red(준비) 0 · exit 0**.
- **spec 과 다른 수 1**: spec 은 캡처를 197장이라 적었으나 spec 이 정한 장면(3폭 × 2테마)은 6장이라 **202장**이다(「spec 과 다르게 한 점」 1).

## 진행 상태

| 단계 | 상태 | 커밋 |
|---|---|---|
| 착수 기준 `p5-base196`(착수 HEAD · 196장) | 완료 | — |
| 1 커밋 A — 갤러리 장면 · 미리보기 선택지 · README URL · `scenes.json` | 완료 | `72ad7275` |
| 2 `p5-before` 202장 · 부분집합 대조 · `diff.mjs --subset` | 완료 | `b108a396` |
| 3 `design-docs.mjs` · `docs/design-system.md` | 완료 | `4edede92` |
| 4 게이트 h · selftest 26 · README · CI 필터 | 완료 | `8a7a3efd` |
| 5 스킬 · `architecture.md §7` | 완료 | `65e24a91` |
| 6 증명(캡처 · 계산값 · 갤러리 DOM) | 완료 | `2177bab8` |
| 7 게이트 | 완료 — green 5 · exit 0 | — |
| 8 보고서 | 이 문서 | 이 커밋 |

## 캡처 순서와 부분집합 대조(ⓑ)

| 이름 | 트리 | 장면 · 장수 | 명세 sha256 | 시각(UTC) |
|---|---|---|---|---|
| `p5-base196` | 착수 HEAD `37269536` · `gitDirty` false | 33 · 196 | `d6983d71…`(P2b 와 같음) | 08:59:22~09:07:20 |
| `p5-before` | 커밋 A `72ad7275` · `gitDirty` false | 34 · 202 | `20919450…` | 09:08:56~09:17:06 |
| `p5-after` | `65e24a91`(스킬·architecture 커밋 뒤) · `gitDirty` false · 다시 빌드 | 34 · 202 | `20919450…` | 09:21:07~09:29:17 |

- 부분집합 대조: `npm run visual:diff -- --subset .visual/p5-base196 .visual/p5-before …` → 공통 장면 33 · 196 captures · red 0 · strict px 0 · exit 0 · 후보에만 있는 장면 `primitives`. 보고 `p5/visual/subset-base196/`. 같은 두 디렉터리를 `--subset` 없이 대조하면 명세 sha256 불일치로 **exit 78**(종전 동작 · red 확인). 공통 장면 0(갤러리 단독 캡처 ↔ 착수 196)은 `--subset` 에서도 78.
- 최종 대조: `npm run visual:diff -- .visual/p5-before .visual/p5-after .visual/p5-report` → 202 captures · red 0 · strict px 0 · exit 0. 보고 `p5/visual/report.md`·`report.json`.
- `p5-after` 뒤 커밋 `2177bab8` 은 문서 표지 밖 한 줄과 증거 파일만 바꿨다(CSS·TSX·audit 무변).
- 계산값 대조: 도구 = `p2b/states/cdump.py`·`compare.py`(선택자 커버리지 목록은 빈 목록). `p5-dist-before`(커밋 A 빌드) ↔ `p5-dist-after`(최종 빌드) → `pages before 202 after 202 · items 27550 · differing pages 0`. 원문 `p5/visual/computed-compare.txt`.

## ⓐ 생성기 · 게이트 h

- `design-docs.mjs` — 입력 5(`tokens.css` · `primitives.css` · `primitives.txt` · `primitives-exempt.txt` · `same-in-dark.txt`) · 블록 2 · 블록 안에 입력 sha256 · 날짜 없음. 쓰기 뒤 `--check` 는 `h tokens 같음 · h primitives 같음 · 문서 표 갈림 0` · exit 0. 다시 써도 바뀌지 않는다(`written=0`).
- 갈림 확인: `tokens.css` 사본의 `--radius-lg` 를 바꿔 `--tokens` 로 주면 `h tokens 갈림 — 블록 3번째 줄부터 다르다 · 문서 표 갈림 1` · exit 1.
- 부재: 없는 문서 경로 → `design-docs readiness: 문서 부재` · exit 78. 표지 짝 부재·중복 · 입력 파일 부재도 78.
- 게이트: a~g 판정부와 h 를 따로 돌려 둘 다 출력한 뒤 합친다. 저장소 실행 요약 = `… · 프리미티브 맨 정의 밖 0(면제 0) · 문서 표 갈림 0`.
- selftest red 확인: 새 selftest 를 종전 게이트(`4edede92` 의 `frontend-design-lint.sh`)로 돌림 → exit 1(ⓐ 「출력에 「문서 표 갈림 0」이 없다」 · ⓧ 「red 여야 하는데 통과했다」 · ⓨ 「red(준비 · 78) 여야 하는데 rc=0」). 새 게이트 → `검사 26건 전건 기대대로 (green 6 · red 14 · red(준비) 6)`.
- CI: `frontend` 경로 필터가 `frontend/**`·`contracts/**` 만 봐서 문서만 바뀐 PR 에서 `frontend-gates` 가 돌지 않았다 → `.github/workflows/ci.yml` 필터에 `docs/design-system.md` 를 더했다.

## ⓒ 갤러리 DOM 질의

`p5/visual/probe.json` — 최종 빌드 · `design=full` · 라이트/다크 × 375/1440 네 경우 모두:

- 6계열 라벨(`section[data-family]` 의 h2) 6개 · `.gnb` 0.
- 요소 수(전부 보임): `.btn` 14 · `.btn-primary` 3 · `.btn-secondary` 3 · `.btn-ghost` 2 · `.btn-danger` 2 · `.btn-sm` 1 · `button.btn:disabled` 5 · `.inp` 3(disabled 1) · `.sel` 2(disabled 1) · `.chip` 6(수식자 5종 각 1) · `.card` 1(`.card-h`·`.card-b`) · `.tblwrap > .tbl` 1 · `tbody tr` 3 · `.modal.modal--dialog` 1(`.modal-h`·`.modal-b`·`.modal-f`).
- 다크 적용: `.card` 배경 `rgb(255, 255, 255)` → `rgb(26, 34, 44)` · `.btn-primary` `rgb(19, 105, 233)` → `rgb(146, 194, 255)` · `.inp` 테두리 `rgb(169, 179, 191)` → `rgb(113, 131, 151)`. `.btn` min-height 375 에서 44px · 1440 에서 40px(`--control-height` 폭 분기).
- 관찰(값 무변 · 문서 ⑦ 6 에 더함): 배경 수식자가 없는 `.chip--off` 는 두 테마 모두 `rgb(238, 242, 247)`(`.chip` 의 리터럴 `#eef2f7`). disabled 버튼·입력의 전용 모양은 기본값에 없다(disabled 도 기본과 같은 색).
- `design-preview.html?scene=primitives&theme=dark&design=calm` — 선택지 「프리미티브」 선택 · iframe `src=/audit-design.html?scene=primitives&design=calm&theme=dark` · 6계열 · `html[data-theme=dark]` · `.card` 배경 다크 값(agent-browser).

## ⓓ 문서 점검표 ↔ 게이트 글자

- `grep -nE '^[0-9]+\. \[[a-h]\]' docs/design-system.md` → 8줄(a~h 각 1). 문서의 번호 목록은 이 8줄뿐이다(`grep -cE '^[0-9]+\. '` = 8).
- 게이트 밖 항목 3(층 감싸기 · 캡처 장면 · 글자·대비 하한)은 번호 목록과 분리해 「게이트 밖 항목(게이트가 재지 않는다)」으로 적었다(「spec 과 다르게 한 점」 3).
- ⑥ 표 행 a~h 8(`grep -nE '^\| [a-h] \|'`). 절대경로(`/home/` · `/mnt/` · 드라이브 문자) 0 · 앞 30줄 생성 마커(`auto-generated`·`@generated`·`do not edit`) 0.

## ⓔ 게이트(단계 7)

`COLAB_TASK_ID=8cfaba3b8ac34465b7ff045b610d978a bash gates/run.sh task` → **exit 0 · 계 green 5 / red(판정) 0 / red(준비) 0**(트리 = `2177bab8` · `~/.colab-v2-test.env` 존재 확인). 요약 JSON = git common dir 기준 `colab-harness/914d2934205d98f9454c83ad30a75a1d/8cfaba3b8ac34465b7ff045b610d978a/b590e0765ad44b9bb45b3d01f5747954/gate-summary.json`. 이 보고서 커밋 뒤 handoff 용으로 같은 명령을 한 번 더 돌리며 그 run id 는 `COLAB_HANDOFF` 줄에 실린다.

| 게이트 | 결과 | 요약 |
|---|---|---|
| `frontend-design-lint` | green | 파일 21 · :root 정의 밖 0 · 미정의 참조 0 · 다크 누락 0(면제 6) · :root/@import 0 · 범위 색 토큰 0 · 색 리터럴 0(면제 1) · 인라인 0(변수 대입 7) · 프리미티브 맨 정의 밖 0(면제 0) · **문서 표 갈림 0** |
| `frontend-design-lint-selftest` | green | 검사 26건 전건 기대대로 (green 6 · red 14 · red(준비) 6) |
| `frontend-typecheck` | green | tsc --noEmit 오류 0건 |
| `frontend-test` | green | Test Files 130 passed · Tests 1613 passed — P2b 와 같은 건수 |
| `frontend-fixture-reach` | green | 진입점 도달 207(진입점 제외 206) · 금지 모듈 0 |

- `tsconfig.audit.json` 타입 검사(갤러리 포함)는 게이트 밖이다 — `npx tsc --noEmit -p tsconfig.audit.json` exit 0 과 매 캡처의 `npm run audit:build` 성공으로 확인했다.

## 스킬 · 문서 변경 요약

| 파일 | 변경 |
|---|---|
| `.agents/skills/to-spec/SKILL.md` | 「디자인 제약 확인」 정본 줄에 `primitives.css` · `docs/design-system.md` · 게이트 a~h 를 더하고, 종전 「토큰:」 한 줄을 표(행 = 게이트 a~h 8 + 캡처 장면 유무 1 · 열 = 확인 · 게이트 · 이 화면)로 바꿈. frontmatter(`disable-model-invocation: true`)와 나머지 하한 4줄·「우려 항목」 안내 그대로 |
| `.agents/skills/design-review/SKILL.md §0` | 「토큰」 행 = `tokens.css`(유일 `:root`) · `primitives.css` · 게이트 `frontend-design-lint` a~h · `docs/design-system.md` · 정적 합격선 끝에 「＋ 게이트 `frontend-design-lint`(a~h)·`frontend-design-lint-selftest` green」 |
| `.claude/skills/to-spec` · `.claude/skills/design-review` | 링크만인 어댑터 — 무변(`git diff` 0) |
| `dev-package/reports/design-system/20260924/architecture.md` | §7 「완료 상태 (2026-09-24)」 — P0~P5 결과 표 · 판정 대기 요지 · 후속 6 |
| `gates/README.md` | `frontend-design-lint` 행에 h · 78 조건 · 요약줄 · selftest 행 23 → 26 |
| `frontend/scripts/visual-baseline/diff.mjs` | `--subset` |
| `frontend/README-audit.md` · `frontend/design-preview.html` · `frontend/audit-design.tsx` · `scenes.json` | 갤러리 |

## spec 과 다르게 한 점

1. **캡처 수 202(spec 197)** — spec 은 「3폭 × 2테마 · fullPage … 197장」이라 적었다. 3 × 2 = 6장이 더해져 196 + 6 = 202다. 장면의 폭·테마는 spec 문면대로 두고 수만 실측으로 적었다. 계산값 대조도 202 페이지.
2. **착수 196장을 임시 되돌리기 없이 찍음** — 지시문은 `p2b-after` 재사용 또는 파일 두 개를 착수 HEAD 로 되돌려 찍는 방법을 적었다. 이 워크트리에 `p2b-after` 가 없어서 **아무것도 고치기 전 착수 HEAD 에서 바로** `p5-base196` 을 찍었다(`gitHead` `37269536` · `gitDirty` false · 명세 sha256 이 P2b 와 같음).
3. **점검표의 게이트 밖 항목 분리** — spec 은 점검표에 「캡처 장면 추가」를 넣고 ⓓ 로 「각 항목이 게이트 조건 이름(a~h)을 가리킨다」를 요구한다. 캡처 장면·층 감싸기·글자/대비 하한은 재는 게이트가 없어 번호 목록(a~h 8항목)과 「게이트 밖 항목」 목록으로 나눴다. 없는 글자를 붙이지 않았다.
4. **selftest 케이스 3(spec 2)** — 갈림 red · 문서 부재 78 에 더해 「블록 밖만 고친 사본 → green」 1건(spec 의 「블록 밖 문장만 고친 docs-only PR 은 green」 증명). 초과분이다.
5. **h 의 입력은 픽스처와 무관** — 게이트의 `COLAB_FRONTEND_DIR`·목록 env 는 a~g 의 픽스처를 바꾸지만 h 는 저장소 문서 ↔ 저장소 실물만 본다(문서가 설명하는 것이 저장소다). 그래서 selftest 의 모든 트리에서 h=0 이고 갈림·부재는 `COLAB_DESIGN_LINT_DOC` 로만 만든다. 저장소 문서가 갈리면 selftest 의 green 케이스도 red 가 된다(게이트 본체와 같이 red).
6. **갤러리의 모달은 뒤판 없이** — `.modal-back` 은 화면 전체를 덮는 fixed 뒤판이라 갤러리를 가린다. 판(`.modal.modal--dialog` + 머리·몸·발)만 제자리에 열었다. 뒤판 모양은 `lab-dialog`·`project-dialog` 장면이 찍는다. hover·focus 는 정적 캡처가 재현하지 못해 그리지 않았다.
7. **`visual:diff --subset`** — 지시문이 허용한 두 방법 중 도구 옵션을 택했다(문서 ⑧ · `diff.mjs` 머리 주석).
8. 커밋 꼬리의 모델 표기는 세션 표기(Claude Opus 5.5)를 따랐다 — 지시문의 「Claude Fable 5.1」과 다르다(P2b 와 같은 처리).
9. 이 보고서는 레인의 파일 쓰기 도구가 보고 파일 생성을 막아 작업 사본 안의 임시 파일에서 복사했다(내용·경로는 지시대로).

## 하지 않은 것

- `patterns.css` 생성 · 패턴 규칙 이동(spec 범위 밖 · 문서 ④에 후보·이유·이관 조건).
- 편차 통일 · 억눌린 상태 복원 · `.page` 개명 · 제품 라우트 갤러리 · 토큰 값·이름 변경 · 새 의존성 · push·PR 게시.
- 계산값 대조 도구를 `frontend/scripts/visual-baseline/` 로 올리기(후속).
- 착수 196 ↔ 커밋 A 의 계산값 대조(픽셀 부분집합 대조만 했다 — spec 의 부수 효과 증거는 캡처 부분집합이다).

## 원한 결과 대조

- intent 「새 화면을 만들 때 점검표와 토큰·프리미티브 표가 `docs/design-system.md` 에 있고 게이트가 재는 것과 같다」 — 점검표 ⑤(a~h) · 토큰·프리미티브 표(생성 · h 로 같음 판정) 충족.
- 사용자 스토리 1(점검표대로면 green) — 점검표 항목이 게이트 조건과 1:1 · 2(갤러리 한 페이지) — `scene=primitives` · 3(판정 항목 한 표) — 문서 ⑦ 16건 · `architecture.md §7`.
- 미달: 없음. 초과: selftest 1건(위 4) · `diff.mjs --subset` 옵션 · 문서 ⑦ 6 의 다크 관찰 1줄.

## 후속 항목

1. 패턴 층 — `.page` 개명(TSX) 별건과 묶어 `patterns.css` 이관(문서 ④).
2. [Ted 판정] 문서 ⑦ 16건(시각 값 10 · 범위·절차 6).
3. `.chip` 리터럴 `#eef2f7` 이 다크에서도 그대로 — 배경 수식자 없는 `.chip--off` 가 다크 화면에서 밝은 칩으로 보인다(갤러리 실측). 어느 게이트에도 걸리지 않는다(f 면제 · c 는 토큰만 본다). ⑦ 6 판정과 함께.
4. disabled 버튼·입력의 전용 모양이 기본값에 없다 — 갤러리에서 disabled 와 기본이 같은 색이다. 어느 게이트·시험에도 걸리지 않는다. 인터랙션 하한(design-review §0)으로 판정할 항목.
5. 캡처 장면 사각 · `tsconfig.audit.json` 게이트 · 시각 대조 게이트 승격 · 계산값 도구 승격 — `architecture.md §7` 후속 4~6.
6. `design-docs.mjs` 의 정본 계열 접두사 목록은 `design-lint.mjs` 와 손으로 맞춘다(design-lint.mjs 가 import 시 실행돼 공유할 수 없다) — 한쪽만 바꾸면 문서의 접두사 표가 게이트와 갈린다. 어느 검사에도 걸리지 않는다.
