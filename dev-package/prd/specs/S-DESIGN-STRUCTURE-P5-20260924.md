# Spec: 디자인 구조 P5 — 문서 · 프리미티브 갤러리 · 패턴 층 · 스킬 정본 갱신
출처 intent: `dev-package/intent/2026-09-24-design-system-structure.md` (승인 2026-09-24 · 원한 결과 「새 화면을 만들 때 점검표와 토큰·프리미티브 표가 `docs/design-system.md` 에 있고 게이트가 재는 것과 같다」)
계획: `architecture.md §3 P5` · 선행 결과: P0~P3 · P2a · P2b 보고서(`dev-package/reports/design-system/20260924/p*/report.md`) · advisor ① approve-with-changes 8건 반영(`patterns.css` 이동은 **범위 밖으로** · 캡처 순서 · 생성 블록 결정성 · 게이트 h 경계)

## 문제 진술
- 구조는 섰지만(정본 토큰 한 파일 · `@layer` · `primitives.css` · 게이트 a~g) 그것을 설명하는 문서가 없다. 새 화면을 만드는 사람은 규칙을 게이트 red 메시지로만 배운다.
- `design-preview.html` 은 09-12 대표 화면 미리보기 도구다. 프리미티브(버튼·입력·칩·카드·표·모달)를 한 화면에 모아 보는 자리가 없다.
- 페이지 컨테이너·`.page-head h1`·`.form-row` 등 패턴 규칙이 `shell.css` 에 「P5 이관 대기」로 남아 있다(P2b 결정). **이번에도 옮기지 않는다** — patterns 층으로 내리면 화면 7파일의 동률 경쟁 선언(`catalog.css`·`dashboard.css`·`detail.css`·`preview.css`·`project.css`·`search.css`·`upload.css`)과 죽어 있던 `@media` padding 규칙이 살아나 「값 무변」 범위를 넘는다(advisor ① 실측). 문서에 「후보 · `.page` 개명(TSX) 별건과 묶어 이관」으로 적는다.
- `to-spec` 스킬의 「디자인 제약 확인」 표와 `design-review` 스킬 §0 정본 표가 P1 이전 상태(`tokens.css` 만 정본 · 「파일별 `:root` 전역 없음」)를 가리킨다. 게이트 a~h 와 층·프리미티브 규칙을 모른다.

## 해법 개요
- `docs/design-system.md` 하나에 **게이트가 재는 것과 같은 규칙**을 사람 말로 적는다 — 층 · 토큰 표(실물에서 생성) · 프리미티브 표(클래스·기본값·화면 편차 목록) · 「새 화면을 만들 때」 점검표 · 게이트 a~g 의 뜻과 red 가 났을 때 할 일 · 판정 대기 목록(억눌린 상태 · `.chip` 색 등).
- 토큰·프리미티브 표는 손으로 쓰지 않고 **스크립트가 `tokens.css`·`primitives.css`·`primitives.txt` 에서 생성**한다(`frontend/scripts/design-docs.mjs` → 표 블록 갱신 · 게이트 `frontend-design-lint` 에 「문서 표가 실물과 같은가」 조건 h 추가 · 갈리면 red).
- `audit-design.html` 에 `scene=primitives`(갤러리 장면)를 더해 6계열 × 상태(기본·hover 불가 → 정적 상태만 · disabled · 수식자)를 한 페이지에 그린다. `design-preview.html` 의 화면 선택지에 「프리미티브」를 추가. `frontend/scripts/visual-baseline/scenes.json` 에 장면 1개 추가(197장). **캡처 순서**: 커밋 A = 갤러리 장면 + `scenes.json` 만(제품 CSS 무변) → 커밋 A 에서 `p5-before` 197장 → 이후 커밋들 → `p5-after` 197장 → 엄격 차이 0. 장면 추가의 부수 효과 0 은 착수 HEAD 의 196장(`p2b-after` 재사용 가능 · 같은 명세 sha 면)과 커밋 A 의 196장 부분집합 대조로 보인다.
- `patterns.css` 는 **만들지 않는다**(위 문제 진술 · 층 이름만 선언된 채 둔다).
- 스킬 정본 갱신: `to-spec` 「디자인 제약 확인」 표 행을 게이트 a~g 로 바꾸고, `design-review` §0 표의 「토큰」 행을 「`tokens.css`(유일 `:root`) · `primitives.css` · 게이트 `frontend-design-lint`」로, 정적 합격선에 「게이트 green」을 더한다. `architecture.md` 에 「완료 상태」 절을 추가해 P0~P5 결과와 남은 판정 항목을 한 표로.

## 사용자 스토리
1. 새 화면을 만드는 작업자로서 문서 한 장의 점검표대로 하면 게이트가 green 이길 바란다.
2. 검토자로서 프리미티브 갤러리 한 페이지로 버튼·입력·칩·카드·표·모달의 실제 모양을 확인하고 싶다.
3. Ted 로서 남은 판정 항목(시각 변경이 생기는 것)을 한 표로 보고 싶다.

## 구현 결정
- **`docs/design-system.md`** 절 구성: ① 층(`@layer` 순서 · 각 층의 소유 · 층 함정 한 문단) ② 토큰(생성 표: 이름 · 라이트 · 다크 · 「동일」 면제 · 계열 접두사 규칙) ③ 프리미티브(생성 표: 계열 · 클래스 · 기본값 속성 수) + **손글** 화면 편차 목록(P2b 표의 「남긴 특이도 편차」 · 생성 블록 밖) ④ 패턴(후보 · `.page` 개명 별건과 묶어 이관 · 현재 `shell.css` 표지 아래) ⑤ 새 화면 점검표(토큰만 · `:root` 금지 · 프리미티브 맨 정의 금지 · 색 리터럴 금지 · 인라인은 CSS 변수만 · 편차는 화면 범위 선택자 · 캡처 장면 추가) ⑥ 게이트 a~h 표(조건 · red 메시지 · 고치는 법 · 면제 파일) ⑦ 판정 대기 목록(P1~P3·P2b 보고서의 Ted 판정 항목 취합) ⑧ 도구(`visual:capture`·`visual:diff`·`cascade-map.mjs`·`design-docs.mjs`) 사용법. 절대경로 없음. **생성 블록은 입력만으로 결정된다** — 날짜·시각 금지, 대신 입력 파일 sha256 을 블록 안에 적는다(생성 시점은 블록 밖 손글). 문서 앞 30줄에 `auto-generated`·`@generated`·`do not edit` 문구를 쓰지 않는다(`generated-up-to-date` 의 마커 스윕이 「등기부 밖 자칭 생성물」로 red 를 낸다).
- **생성 스크립트 `frontend/scripts/design-docs.mjs`**: `tokens.css`·`primitives.css`·`primitives.txt`·`same-in-dark.txt`·`primitives-exempt.txt` 를 읽어 문서의 블록 두 개를 다시 쓴다 — 표지는 `<!-- generated:tokens -->`…`<!-- /generated:tokens -->` · `<!-- generated:primitives -->`…`<!-- /generated:primitives -->`(짝 닫힘 표지 필수). `--check` 모드 = **블록 안만** 비교(블록 밖 문장만 고친 docs-only PR 은 green) · 갈리면 exit 1 · 문서·블록·입력 파일 부재 78. 문서 경로는 env `COLAB_DESIGN_LINT_DOC`(기본 `docs/design-system.md`)로 덮어쓸 수 있다(selftest 가 이 경로로 갈림 red·부재 78 을 만든다). 게이트 `frontend-design-lint` 조건 **h** = `design-docs.mjs --check` 통과(요약줄 `문서 표 갈림 h`). CI 경로 필터가 `docs/design-system.md` 변경에서도 `frontend-gates` 를 돌리는지 확인해 안 돌면 `ci.yml` 필터에 그 경로를 더한다. selftest 케이스 2(갈림 red · 문서 부재 78).
- **갤러리 장면**: `frontend/audit-design.tsx` 에 `scene=primitives` — 정적 마크업으로 6계열(`.btn`·`.btn-primary/secondary/ghost/danger/sm` · `.inp`·`.sel` · `.chip`·수식자 · `.card`+`.card-h/.card-b` · `.tbl` 3행 · `.modal--dialog` 열린 상태)을 라벨과 함께. 제품 컴포넌트를 import 하지 않는다(fixture-reach 무관 · 프리미티브 CSS 만 검증). `frontend/scripts/visual-baseline/scenes.json` 에 `primitives` 장면(3폭 × 2테마 · fullPage) 추가 → 197장 · 위 캡처 순서(커밋 A).
- **스킬·문서 갱신**: `.agents/skills/to-spec/SKILL.md` 디자인 제약 표(행 = 게이트 a~h · 캡처 장면 유무 · **frontmatter `disable-model-invocation: true` 보존**) · `.agents/skills/design-review/SKILL.md §0` 정본 표(「토큰」 행 → `tokens.css`(유일 `:root`) · `primitives.css` · 게이트 `frontend-design-lint` a~h · 정적 합격선에 「게이트 green」) · `frontend/README-audit.md` 갤러리 URL · `architecture.md` 「완료 상태」 절(P0~P5 결과 표 · 판정 대기 · 후속). Claude 어댑터(`.claude/skills/*`)는 링크만이라 무변 확인.
- 스키마 · 마이그레이션: 없음. API 계약: 비파괴. 제품 TSX 변경 0(audit 파일만).

## 시험 결정
- ⓐ `design-docs.mjs --check` exit 0 · 표를 일부러 바꾸면 exit 1(selftest) · 게이트 h green.
- ⓑ 시각 변경 0 — 커밋 A(갤러리 장면 · CSS 무변)에서 `p5-before` 197장 → 이후 커밋 뒤 `p5-after` 197장 → 엄격 차이 0. 부수 효과 0: 착수 HEAD 196장 ↔ 커밋 A 196장 부분집합 차이 0. 계산값 대조 197페이지 0. 이번 단계는 제품 CSS 를 바꾸지 않으므로(patterns 이동 없음) 차이는 0 이어야 한다.
- ⓒ 갤러리 DOM 질의 — 6계열 라벨과 각 클래스 요소가 그려짐 · 다크에서도.
- ⓓ 문서 점검표의 각 항목이 게이트 조건 이름(a~h)을 가리킨다(grep) · 절대경로 0.
- ⓔ `frontend-design-lint`(+selftest)·`frontend-typecheck`·`frontend-test`·`frontend-fixture-reach` green.
- green-by-skip 방지: `--check` 는 문서 부재·블록 부재 78 · 캡처 197 명시.

## 정책 대조
- `product.md §3·§5` 저촉 없음(의존성 0 · 값 변경 0 · 절대경로 0). 스킬 원본은 `.agents/**` 에서 한 번만 수정(`dual-agent.md` 표). 계약 동결 해제: 아니오.

### 디자인 제약 확인
대상 화면: 전 화면(패턴 규칙 이동 · 값 무변) + 갤러리 장면(신설 · fixture 전용). 캡처 차이 0 · 계산값 0 이 증거.

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 화면 편차 목록(P2b · 버튼 높이 32 vs 40 등)을 문서에 「편차」로 둘지 통일 후보로 표시할지 | 편차 목록 + 「통일은 Ted 판정」 표기 | 통일안까지 제시 | ⓐ |
| 2 | 갤러리를 제품 라우트로 노출할지 | audit 빌드 전용(운영 번들 밖) | 제품 `/design` 라우트 | ⓐ · 제품 범위 밖 |
| 3 | `scenes.json` 변경으로 P0~P2b 기준과 명세 sha 가 갈린다 | 커밋 A 에서 새 명세 기준을 새로 찍고, 196장 부분집합으로 이전 기준과 이음(보고서에 명시) | 장면 추가 없이 갤러리는 probe 로만 | ⓐ |
| 4 | `patterns.css` 이동 | 이번엔 문서화만(권고) | 이동 + 화면 7파일 경쟁 선언 삭제(범위 확장) | ⓐ · `.page` 개명 별건과 묶는다 |

## 범위 밖
- `patterns.css` 이동(`.page` 개명 별건과 묶음) · 편차 통일 · `.page` 개명(TSX) · 제품 라우트 갤러리 · 억눌린 상태 복원 · 커밋·push·PR 게시(사용자).

## 산출 계획
- 레인 1(직렬) · `lane-worker` · `isolation: worktree` · 기준 = P2b 병합 뒤 통합 브랜치. 보고서 `dev-package/reports/design-system/20260924/p5/report.md` + `p5/visual/`. 통합 PR 본문의 P5 행.
