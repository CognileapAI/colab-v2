# BF-8 레인 보고 — `LabPage`(S-01) 뿌리 규칙 부재

- 브랜치 `bf-8/labpage-root-padding` · 기준 `main` `b0c1f34`
- 커밋 `89f0357` (코드·시험) · 본 보고 커밋은 뒤따름

## 1. 진입조건 재실측 (전건 참)

| 대장 진술 | 실측 |
|---|---|
| `routes/LabPage.tsx` 뿌리 `<div data-screen="S-01">` 클래스 0건 | 참 — `data-screen`·`data-fills-in` 두 속성뿐, `className` 없음 |
| `dashboard.css` `.dash-columns` 가로 여백 0 | 참 — `display`·`grid-template-columns`·`gap`·`margin-top` 만, `padding` 규칙 없음 |
| 자기 여백을 가진 것은 히어로뿐 | 참 — `search.css` `.search-hero { padding: 40px 20px 28px; max-width: 720px; margin: 0 auto; }` |
| BF-5 가 세운 관례 | 참 — `project.css` `.project-page { padding: 24px 20px 40px; max-width: 1200px; margin: 0 auto; }` · `.project-detail { max-width: 1200px; margin: 0 auto; padding: 32px 24px 96px; }` |

## 2. 최대폭 값 — 화면 간 불일치 1건

- `project.css` `.project-page`·`.project-detail` = **1200px**
- `detail.css` `.detail-page` = **1200px**
- `catalog.css` `.catalog-page` = **최대폭 없음** (`padding: 24px 20px 40px` 만, 좁은 창 media query 별도)
- 채택 = **1200px**. 대장 문구는 「카탈로그·상세 화면의 값」이나 카탈로그엔 그 값이 없다 —
  지시대로 `project.css` 가 쓰는 값을 택했고, 최대폭을 실제로 선언한 두 화면(`project`·`detail`)이 일치한다.
- 가로 여백 = **20px** — `project.css`·`catalog.css`·`search.css` 가 공통으로 쓰는 값.

## 3. 변경

| 파일 | +/- | 내용 |
|---|---|---|
| `frontend/src/routes/LabPage.tsx` | +1/-1 | 뿌리에 `className="lab-page"` |
| `frontend/src/components/dashboard/dashboard.css` | +18 | `.lab-page` 뿌리 규칙(최대폭·여백) · `.lab-page .search-hero` 좌우 여백 0 |
| `frontend/test/dashboard.test.tsx` | +27 | 시험 2건 |
| `frontend/vite.config.ts` | +1/-1 | `test.css.include` 에 `/dashboard\.css(\?raw)?$/`·`/search\.css(\?raw)?$/` 두 항목만 추가 (기존 배열 서식 무수정) |

`project.css`·`detail.css`·`shell.css` 는 건드리지 않았다.

## 4. ⑶ 여백 이중화 — 어떻게 확인했나

- 히어로는 **가장자리까지 가는 요소가 아니다** — `max-width: 720px; margin: 0 auto` 로 가운데 선다.
  따라서 뿌리에 최대폭 1200px·여백 20px 을 줘도 「뿌리 여백이 히어로를 좁힌다」는 설계 문제는 없다.
- ⚠ **초판 정정** — 「보이는 폭은 720px 그대로」는 틀렸다. `shell.css` 가 `* { box-sizing: border-box }` 를
  걸고 있어 **720px 은 좌우 여백을 포함한 폭**이다. 좌우 여백만 0 으로 두면 히어로 **내용 폭이
  680 → 720px 으로 40px 넓어진다**(넓은 창에서 제목·입력칸이 커진다). BF-8 은 여백 규칙을 세우는
  회차지 S-01 모양을 바꾸는 회차가 아니므로 `.lab-page .search-hero` 에 `max-width: 680px`(720 − 40)
  을 함께 박아 **모든 창 폭에서 BF-8 이전과 같은 모양**을 유지한다. 시험이 이 값을 못박는다.
- 다만 창 폭 760px 미만에서는 뿌리 20px + 히어로 20px = **40px 로 겹친다**. 그래서
  `.lab-page .search-hero` 에서 좌우 여백만 0 으로 되돌린다. 위·아래 여백(40px/28px)은 유지 —
  히어로의 세로 리듬이므로 뿌리와 겹치지 않는다.
- 스코프를 `.lab-page` 안으로 한정해 `search.css` 를 공유하는 S-06(검색 결과)엔 닿지 않는다.
- 시험이 이것을 잰다 — 히어로 계산 `padding-left`/`padding-right` == 0.

## 5. RED → GREEN (축자)

- RED (`npx vitest run test/dashboard.test.tsx`, CSS 미적용 상태)

```
 Test Files  1 failed (1)
      Tests  2 failed | 23 passed (25)
```

  실패 사유 2건 — 뿌리 `paddingLeft` `expected +0 to be greater than 0` · 히어로 `expected 20 to be +0`.
  히어로가 20 으로 측정된 것은 `search.css` 가 실제로 실렸다는 증거다(스텁이면 빈 문자열 → NaN).

- GREEN (같은 명령)

```
 Test Files  1 passed (1)
      Tests  25 passed (25)
```

## 6. 게이트 (각각 단독 실행)

| 게이트 | 결과 |
|---|---|
| `./gates/run.sh frontend-test` | **green** — 38 파일 · **597 통과 / 0 실패** (종전 595 + 신규 2). `css.include` 확장으로 흔들린 기존 시험 0건 |
| `./gates/run.sh frontend-typecheck` | **green** — `tsc --noEmit` 오류 **0건** |

- 워크트리에 `node_modules` 가 없어 `frontend` 에서 `npm ci` 를 먼저 돌렸다(설치만, `package-lock.json` 무변경).
- `node:fs` 미사용 — 계산값(`getComputedStyle`)만 썼다.

## 7. 원장 `evidence:` 초안 (BF-5 문체)

> 실측 — `routes/LabPage.tsx` 뿌리 `<div data-screen="S-01">` 클래스 0건 · `dashboard.css` `.dash-columns` 가로 여백 0 · 자기 여백을 가진 것은 `search.css` 히어로뿐. 이 레포엔 공용 PageShell 이 없고 화면 뿌리 클래스가 자기 여백을 적는 관례라(BF-5 가 `project.css` 에 세운 것) S-01 만 그 규칙이 빠져 히어로 밖 두 구획이 창 가장자리에 붙었다. `LabPage.tsx` 뿌리에 `lab-page` 클래스를 주고 `dashboard.css` 에 `.lab-page { max-width: 1200px; margin: 0 auto; padding: 24px 20px 40px; }` 을 더한다 — 1200px 은 `project.css`·`detail.css` 가 쓰는 값이다(`catalog.css` 는 최대폭을 선언하지 않아 기준으로 삼지 않았다). 히어로는 720px 로 가운데 서는 요소지만 좁은 창에서 여백이 40px 로 겹치므로 `.lab-page .search-hero` 에서 좌우 여백을 0 으로 되돌리고, `shell.css` 의 `* { box-sizing: border-box }` 때문에 그것만으로는 내용 폭이 680 → 720 으로 넓어지므로 같은 규칙에 `max-width: 680px` 을 박아 BF-8 이전 모양을 유지한다(S-06 은 같은 `search.css` 를 쓰므로 스코프로 격리). 계산값으로 재려면 규칙 파일이 실려야 해 `vite.config.ts` `test.css.include` 에 `dashboard.css`·`search.css` 를 더했다. 시험 2건 — 뿌리 좌우 여백>0 · 최대폭 1200px · 히어로 좌우 여백 0 · 히어로 최대폭 680px. RED 2 failed / 23 passed → GREEN 25 passed(히어로 최대폭 단언 추가분 RED 1 failed / 24 passed → GREEN 25 passed). 게이트 `frontend-test` 597/597 · `frontend-typecheck` 오류 0.

## 8. §9 항목 초안 (번호 없음)

> **S-01 연구실 화면 뿌리에 여백·최대폭을 둔다 — 화면 뿌리가 자기 여백을 갖는 관례를 마지막 한 화면에 적용.**
> 이 레포엔 공용 PageShell 이 없고 각 화면 뿌리 클래스가 자기 여백·최대폭을 적는다(`project.css`·`detail.css`·`catalog.css`). S-01 만 뿌리에 클래스가 없어 검색 히어로 밖의 두 구획이 창 가장자리에 붙었다. 값은 `.lab-page { max-width: 1200px; padding: 24px 20px 40px; margin: 0 auto; }` — **최대폭 1200px 의 근거는 `project.css`·`detail.css`** 이고, `catalog.css` 는 최대폭을 선언하지 않으므로 「카탈로그와 같은 값」이라는 표현은 이 회차에서 성립하지 않는다. 히어로는 `max-width: 720px` 로 가운데 서므로 뿌리 여백이 그 폭을 줄이지 않는다 — 다만 좁은 창의 여백 이중화를 막으려 `.lab-page` 안에서만 히어로 좌우 여백을 0 으로 되돌린다. 같은 `search.css` 를 쓰는 S-06 은 영향을 받지 않는다.

## 9. `[미확인]`

- **`catalog.css` 최대폭 부재** — 카탈로그는 표 화면이라 의도적으로 창 폭을 다 쓰는 것인지, 누락인지 정본 확인 필요. 해소 = `Policy_데이터_찾기`/E-02 목업에서 카탈로그 최대폭 진술을 찾거나 기획자에게 확인. 이번 범위 밖이라 손대지 않았다.
- **좁은 창 여백** — `catalog.css` 는 900px 미만에서 여백을 16px 12px 32px 으로 줄이고 `env(safe-area-inset-*)` 를 쓴다. `.lab-page` 는 `project.css` 관례를 따라 그 media query 를 두지 않았다. 해소 = 화면별 좁은 창 여백 규칙을 한 번에 정하는 별도 항목.

## 9-A. 수용 검토 반영 (2026-09-05)

- 지적 — `shell.css` `* { box-sizing: border-box }` 때문에 히어로 여백을 0 으로 두면 내용 폭이 40px 넓어진다.
  초판 §4 의 「보이는 폭 불변」 진술이 틀렸다. 판정 = **S-01 모양을 바꾸지 않는다**.
- 조치 — `.lab-page .search-hero` 에 `max-width: 680px` 추가(사유 주석 동봉) · 시험에 `maxWidth === '680px'` 단언 1건 추가.
- RED (CSS 전, 단언만 넣고 실행) — `Tests  1 failed | 24 passed (25)` · `Received: "720px"`.
- GREEN — `Tests  25 passed (25)`.
- 게이트 재실행 — `frontend-test` **green 597/597 (38 파일)** · `frontend-typecheck` **green 오류 0건**.
- `vite.config.ts` 는 추가 수정 없음.

## 10. 대장 문구와의 차이

- **대장 완료정의 ⑴ 정정 요청** — 현행 「**카탈로그**·상세 화면과 같은 최대폭」 → **「`project.css`·`detail.css` 와 같은 값(1200px)」**.
  근거(실측) = `catalog.css` `.catalog-page` 에는 `max-width` 선언이 **0건**이며 `padding: 24px 20px 40px` 뿐이다.
  즉 **S-03 카탈로그는 창 폭 − 40px 로 그려진다** — 최대폭 기준으로 삼을 값 자체가 없다.
  최대폭을 실제로 선언한 화면은 `project.css`(`.project-page`·`.project-detail`)·`detail.css`(`.detail-page`) 뿐이고 셋 다 1200px 이다.
- 대장 완료정의 ⑵ 「`dashboard.css` **또는** 뿌리 클래스」 — 둘 다 했다(클래스 부여 + `dashboard.css` 규칙). 뿌리 `div` 에 클래스가 없으면 규칙을 걸 자리가 없기 때문이다.
