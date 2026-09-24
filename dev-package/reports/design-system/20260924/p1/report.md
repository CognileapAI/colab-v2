# 디자인 구조 P1 결과 — 토큰 정본 단일화(대안 B) · 게이트 `frontend-design-lint`

spec: `dev-package/prd/specs/S-DESIGN-STRUCTURE-P1-20260924.md` · intent: `dev-package/intent/2026-09-24-design-system-structure.md` · 계획: `dev-package/reports/design-system/20260924/architecture.md §2-1·§2-2·§3 P1` · 선행: `p0/report.md`

착수 HEAD `51648762` · task `8e021e5608634778b0a905bf52a206d1` · 레인 1(직렬)

## 진행 상태

| 단계 | 상태 |
|---|---|
| 1 착수 캡처 · 손 계측 | 완료 |
| 2 게이트 `frontend-design-lint` + selftest · 등록 · 착수 CSS red 기록 | 완료 |
| 3 `tokens.css` 재구성 · 화면 `:root` 제거 | 진행 전 |
| 4 preview 경로(Q7) | 진행 전 |
| 5 시험 · 대장 | 진행 전 |
| 6 시각 변경 0 대조 | 진행 전 |
| 7 게이트 | 진행 전 |

## ⓐ 게이트 — 착수 red

### 착수 캡처(단계 1)

- `npm run visual:capture -- --label p1-before`(audit 빌드 포함) · 03:06:59~03:15:02 UTC · PNG 196장 + `index.json`(`captureCount` 196 · 명세 sha256 `d6983d71…` · `gitHead` `51648762` · `gitDirty` false · `built` true · 2병렬).

### 손 계측(단계 1 · 두 방법)

| 항목 | spec 예상 | node 판정부 초판(면제 목록 비움) | python 정규식 대조 |
|---|---:|---:|---:|
| a 정본 밖 `:root` 정의 | 77 | 77 | 77 |
| b 미정의 참조 | 2 | 2(`--text-title-sm` login.css:198 · `--color-surface-muted` deletion.css:10) | 같은 2 |
| c 다크 누락 | 17+ | 19 = 다크에만 17 + 라이트에만 2(`--color-white` · `--shadow-sm`) | — |
| d 화면 CSS `:root`·`@import` | 8 | 9 = `:root` 8블록(upload 2 · catalog · detail · project · lineage · toast · preview) + `@import` 1(members) | 9 |

### 게이트 red(단계 2 · CSS 무변 · 면제 2건 등록 뒤)

`gates/run.sh frontend-design-lint` → **exit 1**

```
파일 19 · :root 정의 밖 77 · 미정의 참조 2 · 다크 누락 17(면제 2) · :root/@import 9 · 범위 색 토큰 0(다크 미검사)
design-lint-counts files=19 a=77 a_root=77 a_scoped=0 b=2 c=17 c_missing=0 c_dark_only=17 c_holes=0 exempt=2 d=9 scoped_color=0 tokens=1
```

## ⓑ selftest

`gates/tools/frontend-design-lint-selftest.sh` → exit 0 · 「검사 8건 전건 기대대로 (green 1 · red 5 · red(준비) 2)」. 각 red 는 계수 줄(`a_root=1 a_scoped=1` · ` b=1 ` · `c_missing=1 c_dark_only=1` · ` d=1 ` · `c_holes=3`)로 그 규칙 때문에 red 임을 확인한다.

## spec 과 다르게 한 점

1. **d 의 `@import` 범위 = 화면 CSS(`src/shell/` 밖)**. spec 게이트 절은 「tokens.css 밖 CSS 의 `:root` 셀렉터 · `@import`」, 해법 개요·ⓐ 는 「화면 CSS 의 `:root`·`@import` 0」이다. `shell/shell.css` 의 `@import './tokens.css'`·`'./design-system.css'` 는 셸 진입 CSS 가 정본을 싣는 경로이고(`styles.ts` → `shell.css`), `architecture.md §2-2` d 의 오늘 값 「7 · 1」도 셸을 세지 않는다. `:root` 셀렉터는 tokens.css 밖 전부(셸 포함)를 센다. README 「못 보는 것」에 적었다.
2. **판정부 위치** — 픽스처 트리에 판정부 사본을 두지 않고 게이트가 저장소의 `frontend/scripts/design-lint.mjs` 하나를 부른다(`frontend-fixture-reach` 는 트리마다 사본). 0건 케이스용 `empty/` 트리를 spec 의 여섯 트리에 더했다.
3. **등록 두 곳 추가** — `gates/config/parallelism.toml`(`scripts/harness/check.py` 가 `ALL_GATES ⊆ parallelism` 을 강제) · `.agents/ci-producers.json`(`verify_evidence.py record --check` 가 등록을 요구).
4. **면제 목록 부재 = red(준비 · 78)** — spec 의 78 조건(대상 0건 · node 부재)에 더했다. 목록이 없으면 c 를 판정할 수 없다.
5. **b 의 정의 집합에 TS/TSX 의 `'--x'` 문자열을 넣었다** — `style={{'--w': v}}`·`setProperty('--x')` 로 넣는 이름(오늘 `Gnb.tsx` 의 `--shell-gnb-offset` 1건 · CSS 에도 정의됨). architecture P4 가 허용하는 데이터값 대입 경로를 b 가 red 로 막지 않게.
