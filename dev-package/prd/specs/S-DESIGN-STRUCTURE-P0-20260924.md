# Spec: 디자인 구조 P0 — 「시각 변경 0」을 증명하는 캡처·픽셀 대조 도구
출처 intent: `dev-package/intent/2026-09-24-design-system-structure.md` (승인 2026-09-24 · Ted 원문 "권장안대로 하자." · Q8 대조 도구 도입 예)
계획: `dev-package/reports/design-system/20260924/architecture.md §2-3·§3 P0`

## 문제 진술
- P1~P3 의 완료 조건은 「보이는 값이 같다」인데, 저장소에 재현 가능한 캡처 구동부도, 픽셀 대조 도구도, 현재 HEAD 기준 캡처도 없다. 09-12 전체 회차의 캡처 스크립트는 git 에 없고(`representative/capture.py` 는 장면 4개짜리) `scenes.json` 은 계측값이지 캡처 명세가 아니다. 09-12 PNG 360장은 그 뒤 93개 파일 변경(#73~#123) 이전 상태다.
- 09-12 장면 30개에는 그 뒤 신설·개편된 화면이 없다 — 계정 관리(`AccountAdminPage` · #84·#121) · 비밀번호 변경(`PasswordChangePage`) · GNB 더보기 메뉴(`GnbMoreMenu` · 09-14).

## 해법 개요
- 장면 명세 파일 하나 + 캡처 구동 스크립트 하나 + 픽셀 대조 스크립트 하나를 `frontend/scripts/visual-baseline/` 에 둔다. 사람이 한 명령으로 「기준 찍기 → 고치기 → 다시 찍기 → 대조」를 돌린다.
- 캡처는 기존 audit 빌드(`frontend/audit.vite.config.ts` · `audit-design.html`·`audit-upload.html`)와 `agent-browser` 를 그대로 쓴다. 새 브라우저 도구를 들이지 않는다.
- 대조는 `pixelmatch` + `pngjs`(devDependency 2개 · Q8 승인)로 PNG 두 장을 픽셀 단위 비교한다. 차이 픽셀이 1개라도 있으면 그 장면은 red 이고 차이 이미지를 남긴다.
- 도구 자체의 신뢰는 **같은 HEAD 를 두 번 찍어 전 장면 차이 0** 으로 증명한다. 흔들리는 장면이 있으면 숨기지 않고 이름·원인을 보고서에 적는다.

## 사용자 스토리
1. 오케스트레이터로서 P1 레인이 「시각 변경 0」이라고 보고하면 대조 보고서(장면별 차이 픽셀 수·차이 이미지)로 확인하고 싶다, 말로 하는 「같다」를 받지 않기 위해.
2. 레인 작업자로서 착수 HEAD 에서 한 명령으로 기준 캡처를 만들고, 수정 뒤 한 명령으로 대조 결과를 얻고 싶다, 수동 캡처 절차를 매번 다시 짜지 않기 위해.
3. Ted 로서 차이가 난 장면만 전·후·차이 이미지 세 장으로 보고 「의도한 정정인가」를 판정하고 싶다.

## 구현 결정
- 모듈 · 인터페이스 (전부 `frontend/scripts/visual-baseline/`):
  - `scenes.json` — 장면 명세. 항목 = `{name, entry: "audit-design.html"|"audit-upload.html", query: {...}, widths: [375,768,1440], themes: ["light","dark"], fullPage: bool, actions?: [{click: selector}|{wait: ms}]}`. 09-12 의 30장면 이름을 그대로 승계하고 `account-admin`·`password-change`·`gnb-more` 3장면을 더한다(**33장면 × 3폭 × 2테마 = 198 캡처**). `design=full` 로 GNB 를 포함해 찍는다(제품과 같은 마운트).
  - `capture.py` — 명세를 읽어 `python3 scripts/agent-bridge.py run-tool browser -- --session <s> …` 로 열고 찍는다(09-12 `representative/capture.py` 와 같은 호출 방식). 순서 = viewport 설정 → open → `wait --load networkidle` → `document.fonts.ready` → `actions` → 정착 대기(고정 ms · 명세 값) → screenshot. 출력 = `<out>/<name>-<theme>-<width>.png` + `<out>/index.json`(장면 목록 · 명세 sha256 · 캡처 시각 · git HEAD · audit 빌드 경로). 병렬은 테마당 세션 1개(최대 2)로 제한한다.
  - `diff.mjs` — `node diff.mjs <baselineDir> <candidateDir> <reportDir>`. 두 `index.json` 의 장면 집합이 다르면 **exit 78**(대조 대상이 갈렸다 · 준비 실패). 각 쌍을 `pixelmatch` 로 비교(`threshold` 0.1 · 안티앨리어싱 무시 켬)해 차이 픽셀 수·비율을 세고 차이 이미지 `report/<name>.diff.png` 를 쓴다. 크기가 다르면 그 장면은 차이로 센다(크기 차이 표기). 출력 = `report.json` + `report.md`(장면별 표 · 총계 · red 목록). 차이 픽셀 > 0 인 장면이 하나라도 있으면 **exit 1**, 없으면 **exit 0**, 대상 0건이면 **exit 78**.
  - `package.json` scripts: `visual:capture` = `python3 scripts/visual-baseline/capture.py --out <dir>` · `visual:diff` = `node scripts/visual-baseline/diff.mjs`. devDependencies: `pixelmatch`·`pngjs` 고정 버전(`^` 없이).
  - 출력 자리: 캡처 PNG 는 `frontend/.visual/<label>/`(**gitignore** · PNG 는 커밋하지 않는다). 보고서 `report.md`·`report.json` 만 `dev-package/reports/design-system/<날짜>/<단계>/visual/` 로 복사해 커밋한다. 차이 이미지는 red 장면의 것만 복사한다.
  - 장면 추가(fixture 코드): `frontend/audit-design.tsx` 에 `account-admin`(`AccountAdminPage` · 계정 ≥5행 · 긴 이메일 1행 포함) · `password-change`(`PasswordChangePage`) · `gnb-more`(`lab` 장면 + 더보기 버튼 클릭 action) 분기를 더한다. 필요한 fixture source 가 `frontend/test/factories` 에 없으면 audit 파일 안에 로컬 fixture 로 둔다. **제품 코드(`src/`)는 건드리지 않는다.** 필요한 port 가 없어 fixture 로 만들 수 없으면 멈추고 보고한다.
- 스키마 · 마이그레이션: 없음.
- API 계약: 비파괴 · 변경 없음.
- 결정성(같은 HEAD 두 번 → 0): 시간·난수 의존 요소는 명세에서 고정한다 — 날짜는 fixture 값, 지도 타일은 로컬 `audit-tile.svg`, 애니메이션은 정착 대기 뒤 캡처, 캐럿은 `caret-color: transparent` 를 캡처 세션에서 주입. 그래도 흔들리는 장면은 `report.md` 「불안정 장면」에 이름·차이 픽셀·추정 원인을 적고 **P1 대조에서 제외하지 않는다** — 제외는 그때 Ted 판정.

## 시험 결정
- 외부 행위 기준 검증 항목:
  - ⓐ `visual:capture` 가 198 PNG + `index.json` 을 낸다(장면 33 × 6 · 0바이트 파일 0).
  - ⓑ 같은 HEAD 에서 두 번 찍어 `visual:diff` 가 **전 장면 차이 0 · exit 0**. 흔들린 장면은 표에 이름으로.
  - ⓒ red 픽스처 — 후보 디렉터리의 PNG 한 장을 1픽셀 바꾼 사본으로 대조하면 그 장면만 red · exit 1 · 차이 이미지 생성. 장면 하나를 빼면 exit 78.
  - ⓓ `frontend/test/visual-diff.test.ts` — `diff.mjs` 의 비교 함수를 작은 PNG 픽스처(동일 2장 → 0 · 1픽셀 다름 → 1 · 크기 다름 → 크기 차이)로 잠근다. 실제 브라우저 없이 돈다.
  - ⓔ 새 장면 3개가 실제로 그 화면을 그린다 — `account-admin` 캡처에 표 머리글 8개, `password-change` 에 폼, `gnb-more` 에 열린 메뉴가 보이는지 `live_probe` 류 DOM 질의로 확인(스크린샷만으로 판정하지 않는다).
  - ⓕ 09-12 이후 변경 파일 93개(`git diff --stat 09b97a34 HEAD -- frontend/src`)를 장면에 대응시킨 커버리지 표를 `report.md` 에 둔다. 대응 장면이 없는 파일은 이름으로 남긴다(숨기지 않는다).
- 재사용 seam: audit 빌드 · `agent-browser` 호출(`scripts/agent-bridge.py run-tool browser`) · `live_probe.js` · `frontend/test/factories`. 신설 seam: `scenes.json` 명세 형식 하나.
- 해당 서비스 단독 게이트 이름: `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach`(audit 파일이 `main.tsx` 에서 닿지 않아야 한다 — 지금도 그렇다). 새 게이트는 만들지 않는다(집행 게이트는 P1 의 `frontend-design-lint`).
- green-by-skip 방지: `diff.mjs` 는 대상 0건·집합 불일치를 78 로 낸다. ⓑ 의 보고서에 장면 수 198 을 명시한다. 시험 ⓓ 의 픽스처 수를 시험 이름에 적는다.

## 정책 대조 (작성 시점 제약)
- `.agents/rules/product.md §3` 불변 규칙 중 저촉 항목: 없음(도메인·계약·생성물·절대경로 무관). 문서·보고서에 절대경로를 적지 않는다.
- `§5` 「절대 하지 않는 것」 중 저촉 항목: 새 의존성 2개(`pixelmatch`·`pngjs`) — intent Q8 로 Ted 승인. 그 밖의 도구 도입 없음. Playwright 를 들이지 않는다(`gates/README.md` `frontend-test` 행).
- 계약 동결 해제 필요: 아니오.
- legacy 대장: 새 BF·결정번호 없음. `work-items.yaml` 변경 없음.

### 디자인 제약 확인
대상 화면: 해당 없음 — 제품 CSS·TSX(`frontend/src/**`) 변경 0. 바뀌는 것은 fixture 진입점(`frontend/audit-design.tsx`)과 스크립트뿐이다. 새 장면의 화면 자체는 현재 HEAD 그대로 찍힌다(정정하지 않는다).

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 전체 페이지 캡처는 스크롤바 제거 과정에서 오른쪽 끝이 잘린 것처럼 보이는 경우가 있었다(09-12 `visual-review.md`). 대조는 뷰포트 캡처로 할까, 전체 페이지로 할까 | 뷰포트(900px 높이) — 안정적이지만 아래쪽을 못 본다 | 전체 페이지 — 다 보지만 흔들릴 수 있다 | ⓑ 로 하되 흔들리면 그 장면만 ⓐ 로 내리고 표에 적는다 |
| 2 | 캡처 병렬도 — 09-12 는 테마당 세션 1개(2병렬)였다 | 2병렬 | 1병렬(느리지만 결정적) | ⓐ · ⓑ 의 두 번 찍기가 0 이 아니면 ⓑ 로 재시도해 원인(병렬 부하)을 가른다 |
| 3 | `gnb-more` 장면은 클릭 action 이 필요하다 — 첫 장면에 상호작용을 넣는 것 | 넣는다(명세 `actions`) | 뺀다 | ⓐ · 열린 메뉴는 09-14 커밋의 유일한 검증 대상이다 |

## 범위 밖
- 제품 CSS·TSX 변경, 토큰 이동(P1), 게이트 `frontend-design-lint`(P1), 09-12 PNG 재사용, 실제 서버·운영 화면 캡처, iOS/Safari.
- 캡처 PNG 의 git 커밋. 커밋·push·PR 게시(사용자).

## 산출 계획
- 라운드 파일: 만들지 않는다(신규 task 는 legacy 라운드에 등재하지 않는다 · `AGENTS.md`). 진행 상태는 이 spec 과 `dev-package/reports/design-system/20260924/p0/` 보고서.
- 예상 레인 수: 1(직렬). 레인 = `lane-worker` · `isolation: worktree` · 워크트리에 `npm ci` 선행(훅 없음 · 메모리 「전수 측정은 준비된 워크트리에서만」).
- 레인 산출: 위 파일들 + `dev-package/reports/design-system/20260924/p0/report.md`(ⓐ~ⓕ 결과 · 게이트 3계수 · 불안정 장면 · 커버리지 표) + 로컬 PR 요약 `~/.local/state/colab/pr/design-structure-p0.md`(저장소 밖).
