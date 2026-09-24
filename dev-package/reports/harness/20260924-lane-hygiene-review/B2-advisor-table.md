# B2 — 디자인 구조 P0~P5 advisor ①·② 실측표

출처: `origin/claude/design-system-structure`(PR #129). spec·보고서는 `git archive` 로 풀어 읽음. 커밋 본문은 `git log origin/claude/design-system-structure --not origin/develop`.

## 전제 — 기록 자리
- 보고서 6건(`dev-package/reports/design-system/20260924/{p0,p1,p2a,p2b,p3,p5}/report.md`)에는 **advisor ① 기록 0건**. ① 판정은 spec 커밋 메시지와 spec 본문의 「(advisor ① 권고)」 표지에만 있음.
- 심각도(차단급 여부) 표기: 커밋·spec·보고서 모두 **0건**. "차단" 보고서 grep 0건, "block" 은 CSS 선택자 문맥뿐. 아래 심각도 열은 **정정 내용으로 본 판단(추론)** 이며 기록값이 아님.

## Q1. advisor ① 단계별 표

| 단계 | 판정(기록) | 교정 건수 | 근거 위치 | 차단급으로 볼 만한 결함(추론) | spec 최종(줄 · 바이트) | 제품 파일 수(spec 기준) | 새 게이트·훅·계약 |
|---|---|---|---|---|---|---|---|
| P0 | 「정정 9건」(판정어 미기록 · 별도 커밋) | 9 | `0e5b8361`(spec +14/−9) | 있음 — 대조 `threshold 0.1` 은 미세 색 회귀를 버려 거짓 green(→ `threshold: 0` · P0 spec:24) · 캡처 198→196 오기 · `.mjs` import TS7016(typecheck red) · localStorage 비결정성 | 72 · 13,498 | `src/` 0(「제품 코드(`src/`)는 건드리지 않는다」) · 도구·audit·package.json·.gitignore ≥6 | 새 게이트 0(spec:45) · devDependency 2 · 출력 정책 변경 |
| P1 | 「정정 7건」(판정어 미기록 · 별도 커밋) | 7 | `51648762`(spec +11/−8) | 있음 — 900px 미디어 블록 순서(특이도 동률 → 순서가 승자 · 시각 변경) · `design=calm` 경로 다크 소실(P0 명세 29장면이 못 봄) · 게이트 c 사각·면제 구멍 | 93 · 17,032 | 화면 CSS ≥8 + index.html·audit | 새 게이트 `frontend-design-lint`+selftest · run.sh·CI 등록(spec:38-46) |
| P2a | approve-with-changes | 9 | `7967e001` 본문 · spec:39 | 있음 — jsdom 29 가 `@layer` 안 규칙을 계산에서 빼 계산값 시험 6 it 전부 red(spec:39 「advisor ① 실측」) | 91 · 16,160 | CSS 17파일 전수(spec:36) + vite.config.ts | 게이트 d 범위 확대 · test 전용 vite 플러그인 |
| P2b | approve-with-changes | 9 | `60d63683` · spec:34 | 있음 — 낮은 특이도 원소 규칙의 층 함정(시각 변경) → 0단계 base 층 추가 | 64 · 13,956 | 프리미티브 6계열 × 화면 CSS(`.btn` 11파일 등 · spec:7) | 새 게이트 e + `primitives.txt` |
| P3 | approve-with-changes | 7 | `26b8a676` · spec:4 | 판단 보류 — 순서 변경(P3 를 P2b 앞으로) · 치환 후보 라이트·다크 동일 조건 · 게이트 g TS 파서 | 58 · 8,968 | CSS ≥7 + TSX 5 | 새 게이트 f·g + selftest |
| P5 | approve-with-changes | 8 | `37269536` · spec:3 | 있음 — `patterns.css` 이동을 범위 밖으로(화면 7파일 동률 경쟁 선언) · 캡처 순서(명세 sha 불일치 → 78) | 56 · 10,505 | `src/` TSX 0(spec:28) · docs·scripts·audit·scenes.json·스킬 2 | 새 게이트 h · 스킬 정본 변경 |

계수: approve-with-changes 4 · 판정어 없는 「정정 N건」 2(P0·P1) · clean 0 · block 0. 교정 합계 49건. 6단계 모두 결함 발견. P2a~P5 는 ① 반영이 spec 첫 커밋에 합쳐져 ① 전 크기 분리 불가.

## Q2. 초안 생략 규칙 적용

| 단계 | ≤60줄 | ≤4,000자 | 새 게이트 없음 | 제품 ≤3 | 결과 |
|---|---|---|---|---|---|
| P0 | ✗ 72 | ✗ 13,498 | ✓(단 의존성 2) | `src/` 기준 ✓ · 전체 파일 ✗ | 생략 안 됨 |
| P1 | ✗ 93 | ✗ 17,032 | ✗ | ✗ | 생략 안 됨 |
| P2a | ✗ 91 | ✗ 16,160 | ✗ | ✗ | 생략 안 됨 |
| P2b | ✗ 64 | ✗ 13,956 | ✗ | ✗ | 생략 안 됨 |
| P3 | ✓ 58 | ✗ 8,968 | ✗(f·g) | ✗ | 생략 안 됨 |
| P5 | ✓ 56 | ✗ 10,505 | ✗(h) | `src/` 기준 ✓ | 생략 안 됨 |

- 생략 대상 **0단계**. 자수 조건 하나로 6단계 전부 탈락(최소 8,968자 = 기준 2.2배).
- 「생략했을 단계에서 ①이 결함을 찾았는가」 해당 행 없음. 반사실: 줄 수만 통과하는 P3·P5 도 ① 교정 7·8건.
- 시사점: 이 프로그램은 생략 규칙의 판별력을 시험하지 못함(모든 행이 여러 조건에서 동시 탈락). 경계 사례 데이터 없음.

## Q3. advisor ② 증거 취급

| 단계 | ② 기록 | 증거 취급 | 인용 |
|---|---|---|---|
| P0 | accept-with-fixes 3건 중 2건 반영(`a98b084b`) | **증거 경로 누락 지적** → 오케스트레이터가 직접 열어 확인 | p0/report.md:215 「오케스트레이터가 2026-09-24 이 파일을 직접 열어 계수를 확인했다(advisor ② 수정 1)」 · `a98b084b` 「게이트 증거는 Git common dir 의 task runtime 에만 있어 오케스트레이터가 직접 열어 확인했다」 |
| P1 | 보고서 기록 0 · P2a spec:81 「`design-lint.mjs` 사각 3건(advisor ② 권고)」 | 기록 없음 | — |
| P2a | 기록 0(보고서·커밋) | 기록 없음 | — |
| P2b | 수정 2건(`c10d6395`) · p2b/report.md:229 | 기록 없음 — 지적은 diff 내용(면제표 변경 사유 · `.card-h h3` 면제 근거) | — |
| P3 | accept-with-fixes 3건 · p3/report.md:229 | 기록 없음 — 지적은 코드 결함(펼침 style · g · color-mix) | — |
| P5 | accept-with-fixes 4건 · p5/report.md:130 | 기록 없음 — 지적은 selftest 결합·날짜·사유 값·접두사 이중화 | — |

계수: ② 스스로 증거 읽음 **0** · 「증거 누락」 지적 **1**(P0) · 프롬프트 줄 의존 기록 **0** · 기록 없음 **5**.

- 보고서 6건 모두 gate-summary 경로 기재(p0:215 · p1:45 · p2a:134 · p2b:206 · p3:183,263 · p5:72,139). 형식은 「git common dir 기준 `colab-harness/<key>/<task>/<run>/gate-summary.json`」 **상대 경로**이고 `<key>` 가 단계마다 다름(레인 워크트리마다 toplevel 이 달라짐: d38e30…·1e175b…·ff5068…·12892b…·ed554c…·914d29…). advisor 가 열려면 common dir 을 스스로 풀어야 함.
- P1 이후 경로가 보고서에 처음부터 들어간 것은 P0 ② 수정 1의 결과로 보임.
- ② 가 파일을 실제로 열었다는 기록은 P1~P5 어디에도 없음 → 「읽었다」로 셀 근거 0.
