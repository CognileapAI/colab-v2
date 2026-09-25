# design-review 20260924 — L4b (apple-design §15 Typography)

- 범위: `frontend/src/**/*.css` 21종 + `frontend/src/shell/tokens.css` 타입 토큰
- 축: apple-design §15 (tracking size-specific · leading inverse · weight+size+leading 세트 · px/rem · 시스템 폰트) 만. 대비·13px 미만·모션 등 타 축은 판정하지 않음(§6).
- task_id: ad5c4d16ea394b47a47de5b008823d8e (lifecycle begin --legacy)

## 1. 판정표

| # | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|
| 1 | §15 tracking | letter-spacing 값이 토큰화되지 않은 채 파일마다 개별 리터럴로 중복된다 | 있음 | `login.css:29`(0.01em, 크기 미상속 룰) · `catalog.css:36,64,66`(0, normal, 0.04em) · `dashboard.css:206`(-0.02em, 28px) · `detail.css:15,64,96,130,143,164,166`(0.05em×5, -0.03em×1, 0×1, 13~28px) · `lineageGraph.css:79`(.05em, 13px) · `members.css:20`(-0.023em, 28px) · `project.css:31,362`(-0.03em/31px, -0.02em/20px) · `search.css:7`(-0.02em, 28px) · `upload.css:242,252`(0) · `shell.css:123,430`(-0.02em, 17px/28px) — `--tracking-body: 0` 토큰 1개만 존재, 나머지 ~19건은 하드코딩 | Ted 판정 |
| 2 | §15 tracking | 동일 크기 토큰(`--text-h2` 28px)에 letter-spacing 값이 -0.02em(`shell.css:430` `.page-head h1`, 전 화면 공용) / -0.023em(`members.css:20` `.settings-page h1`) / -0.03em(`detail.css:15` `.dt-header h1`, `search.css:7` `.search-hero h1`은 -0.02em)로 셋으로 갈린다 | 있음 | `shell.css:430`(-0.02em) vs `members.css:20`(-0.023em) vs `detail.css:15`(-0.03em) — 모두 font-size: var(--text-h2)=28px | Ted 판정 |
| 3 | §15 tracking | 방향성(대형 음수 / 소형 양수 / 본문 0)은 전반적으로 준수 — `--text-caption`(13px) 계열 라벨 다수가 +0.04~0.05em, h1/h2(20~31px)가 -0.02~-0.03em, 본문은 `--tracking-body: 0` | 없음 | `catalog.css:66`(13px, +0.04em) · `detail.css:64,96,130,143,164`(13px, +0.05em) · `dashboard.css:206`(28px, -0.02em) · `project.css:31`(31px, -0.03em) · `shell.css:3`(본문, var(--tracking-body)) | — |
| 4 | §15 leading | line-height는 크기와 역방향으로 대체로 일관 — 제목(h1/h2/h3, 16~31px) 1.2~1.5, 본문(13~15px) 1.55~1.9, 뱃지/칩(12~15px, 고정 높이) 1(예외로 타당) | 없음 | `shell.css:430`(h1 28px, 1.3) · `primitives.css:87`(h3 16px, 1.5) · `dashboard.css:207`(28px 숫자타일, 1.2) · `members.css:75`(본문 14px, 1.7) · `detail.css:78`(본문 1.65) · `catalog.css:121,125,141,145`·`detail.css:39,42`(칩, 1) | — |
| 5 | §15 px/rem | font-size 선언이 px 계열 202건 vs rem/em 0건 — 토큰(`--text-*`) 자체도 tokens.css:89-94에서 전부 px로 정의돼 var() 160건도 결국 px 근원. 사용자 브라우저 기본 글자 크기(Dynamic Type류) 설정과 무관하게 고정 | 있음 | `frontend/src/shell/tokens.css:89-94` (`--text-h2: 28px` 등 6개 전부 px) · 레포 전체 `font-size:\s*[0-9]+px` 202건, `rem` 0건 | Ted 판정 |
| 6 | §15 시스템 폰트 | `--font-sans`가 커스텀 웹폰트(Pretendard Variable)를 1순위로 두고 `-apple-system`·`Segoe UI`·`Malgun Gothic`·`Noto Sans KR`·시스템 스택을 폴백으로 둔다 — 이유: 한글 UI(레이턴트·자간 최적화 없이는 시스템 폰트 간 한글 자간 편차가 큼)로 근거 있는 오버라이드 | 없음 | `tokens.css:84-87` | — |
| 7 | §15 hierarchy | weight+size+leading이 세트로 일관되게 조합됨 — h1(700/28px/1.3), 라벨 k(700/13px/1, 대문자 트래킹형), 본문(400~600/14~15px/1.5~1.7) 조합이 파일 간 반복 | 없음 | `shell.css:430` · `detail.css:64,96,130` · `members.css:75` | — |

## 2. 이월 재판정

| 이전 항목 | 출처 | 재판정 | 근거 |
|---|---|---|---|
| 판정-20 「글자 간격 값이 글자 크기와 무관하게 하나로 고정돼 있다」 + D-13(토큰 신설·리터럴 치환) | `design-review-20260908.md:275-276,311` | **잔존** | `tokens.css`에 `--tracking-body: 0` 1개만 존재, D-13이 명시한 구간 토큰(예: heading/caption tracking) 신설과 `login.css`·`catalog.css`·`shell.css` 리터럴 치환이 실행되지 않음 — 해당 3파일 모두 여전히 하드코딩 letter-spacing 보유(위 #1) |
| `design-review-20260908-L4.md` / `design-review-20260912.md` 내 §15 관련 행 | 두 문서 | 해당 없음 | grep으로 §15/타이포그래피/letter-spacing/line-height 행을 찾지 못함 — 두 문서에 이 축을 다룬 별도 행이 없어 재판정 대상 없음 |

## 3. 소계

- 있음 3건(#1, #2, #5) · 없음 4건(#3, #4, #6, #7) · [미상] 0건
- Ted 판정 후보 3건(#1, #2, #5) · 즉시 수정 후보 0건
- 이월: 잔존 1건(판정-20)

## 4. Ted 판정 후보

- **letter-spacing 토큰 부재(#1, #2)** — 방향성 자체는 지키고 있으나(대형 음수/소형 양수/본문 0), 수치가 파일마다 손으로 박혀 -0.02/-0.023/-0.03em처럼 미세하게 갈린다. ⓐ `tokens.css`에 `--tracking-tight`(예: -0.02em, 20px+ 제목용) · `--tracking-caption`(예: 0.04em, 13px 라벨용) 두 구간 토큰만 신설하고 기존 리터럴을 치환 — 값 자체는 지금 지배적인 -0.02em/0.05em로 통일. ⓑ 현행 유지(파일별 자율값, 문서화만) — §15는 "크기별로 다르면 됨"을 요구할 뿐 토큰화까지는 요구하지 않으므로 위반은 아니라는 해석. 권고: ⓐ. D-13이 이미 이 방향으로 합의돼 있었고(판정-20), 20/23/30 세 값이 같은 28px 제목에 섞여 있는 것은 의도적 차이로 보이지 않는다.
- **font-size px 전용(#5)** — ⓐ `tokens.css`의 `--text-*` 6개만 rem 기반으로 전환(1rem=16px 가정 시 28px→1.75rem 등)하고 나머지 202건 하드코딩 px는 범위 밖(별도 작업)으로 둔다. ⓑ 전면 rem 전환(토큰+202건 리터럴 전부). 권고: ⓐ 먼저 — 토큰만 바꿔도 var() 160건이 함께 rem화되어 커버리지가 크고, 202건 리터럴 전수 치환은 회귀 위험 대비 이득이 작다.

## 5. css_audit 오탐

- 이번 축(§15)에서 `css_audit.md`의 8건 "정의되지 않은 토큰"(`--pv-*`/`--dash-*`)은 타이포그래피 무관(레이아웃/색상 계열)이라 본 레인에서 판정하지 않음 — L1/L2 등 담당 축으로 남김.

## 6. 이번에 세지 않은 축

- 대비(AA 4.5:1), font-size 13px 미만(정적 캐논, L1–L3 담당), 모션/스프링/드래그, neg margin, card shadow, border 2-layer, spacing 소유권 — 모두 §15 외 축이라 미판정.
