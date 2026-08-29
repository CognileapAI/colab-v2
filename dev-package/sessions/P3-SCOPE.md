# P3 — 범위 확정과 첫 조각 (2026-08-29)

> **이 문서는 `P3` 회차의 작업 기록이다.** 대장(`work-items.yaml`)·`03-HANDOFF`·`PLAN-SoT`·
> `WORK-UNITS` 는 이 회차에서 **한 글자도 건드리지 않았다** — 갱신은 오케스트레이터 몫이다.

## 1. 진입조건 실측 — 반만 성립한다

`work-items.yaml` `P3` 의 `depends_on: [P2, D5]`.

| 선행 | 대장 표기 | 실물 판정 |
|---|---|---|
| `P2` | `status: done` · 증거 = 2026-08-28 실측(`sessions/P2-MEASURE.md` · `PLAN-SoT §9 〈179〉`) | **성립.** `STAGE2-PARALLEL-MAP` 이 적은 「`P2` conflict」는 그 판정 **이전**의 기록이라 낡았다 |
| `D5` | `status: partial` | **불성립 — 단, 전면 차단은 아니다.** `WORK-UNITS §10.2` 말미가 「`D5` 의 stage 2 파트(파싱·좌표계·**COG**)는 같은 WU 의 stage 1 파트 뒤」라 적고, `§10.3` 3단이 그것을 `P3` 앞에 둔다. ⚠ **「타일은 COG 없이 못 낸다 — `D5` → `P3` 는 선호가 아니라 의존이다」**(`〈158〉-㉳`) |

**결론** — `P3` 전체는 열리지 않는다. **COG 를 요구하지 않는 조각만** 이번 회차에 착지 가능하다.

## 2. 완료 정의 — **있음** (지어내지 않았다)

축자 인용 둘. 정본은 `WORK-UNITS §7` 말미이고, `§10.2` 말미가 두 항목을 그 위에 올렸다.

> **각 P의 완료 판정 (I2 이후 공통)** — 넷 다 충족해야 닫힌다.
> 1. 해당 단계 스토리의 수용 기준 통과
> 2. 도메인 게이트 green (계약·경계·스키마·RLS)
> 3. **staging 배포 green** — 로컬 green은 완료가 아니다
> 4. 목업 대비 화면 검증

> **타일 서빙·확대 · `createScreenshot` 은 `P3` 안에 남는다** — 각주로만 있던 것을 완료 정의로 올린다.

**판정 = 있음.** 다만 「4항」은 **판정 절차**이지 범위 목록이 아니다. 범위 목록의 정본은
`WORK-UNITS §7` 의 `〈63〉-㉮` 상자다:

> **P3 에 그대로 남은 것** — 계보 그래프 · **데이터셋 상세의 2D 렌더 3종**(격자·경계·점) ·
> `createScreenshot` · 표현 종류 확장 · 렌더 성능·상한 조정.
> ⚠ **P3 은 이만큼 작아졌다** — P3 을 착수할 때 **여기 적힌 「빠져나간 것」을 다시 자기 범위로 세지 않는다.**

⚠ **한 자리가 서로 어긋난다** — `〈63〉-㉮` 는 `getRenderTile` 을 **P2 로 내보냈다**고 적고,
`§10.2` 말미는 **「타일 서빙」이 `P3` 에 남는다**고 적는다. **실물이 가른다** — `getRenderTile`
라우트·`tiles.py` 는 P2 에서 이미 서 있고(시험 green), `P3` 에 남은 것은 **서빙이 아니라 확대**,
즉 `RenderResult` 의 **타일 갈래를 실제로 내는 것**이다(stage 1 은 이미지 갈래만 낸다 —
`tests/test_render_result_image.py` · `〈74〉-㉳`). **이 해석은 오케스트레이터 확인 대상이다.**

## 3. 분해 — 독립 착지 가능한 조각 다섯

| # | 조각 | 의존 | 파일 면 | 이번 회차 |
|---|---|---|---|---|
| **㉮** | **`createScreenshot`** — 장면 합성 PNG | `P2`(✅)만. **COG 무관** | `services/viz-render/**` 안에서 닫힌다 | ✅ **골랐다** |
| ㉯ | **타일 갈래·확대** — `RenderResult` 의 `tileUrlTemplate` 갈래를 실제로 내고 FE 가 확대에 쓴다 | **`D5` stage 2 파트(COG) — 불성립** | viz-render ＋ pipeline-worker(COG) ＋ FE | ⛔ 차단 |
| ㉰ | **2D 렌더 3종 중 경계·점** | **미판정 — 그릴 원천이 없다.** `DATA-REFERENCE §1` 의 원천 5종은 전부 래스터다. 벡터 원천이 없으면 「경계·점」의 오라클이 없다 | viz-render ＋ D5 | ⛔ 판정 대기 |
| ㉱ | **계보 그래프** | `P2`(✅) | **`services/core-api/**`**(`d4_lineage`·`routes/lineage.py`) ＋ `frontend/src/components/lineage/**` | ⛔ **이 에이전트 소유 밖** (core-api 미접촉 제약) |
| ㉲ | **렌더 성능·상한 조정** | 없음 | viz-render | 미착수 — 합격선(무엇을 몇 초로) 미기재 |

**고른 이유(㉮)** — ⑴ 선행이 `P2` 하나이고 COG 를 안 탄다 ⑵ 파일 면이 `services/viz-render/**`
안에서 닫혀 다른 에이전트와 겹치지 않는다 ⑶ **계약 개정이 필요 없다** — `/screenshots` 는
`core-viz.yaml` 에 이미 선언돼 있고 구현만 없었다(`X-5` 가 찾는 「선언만 되고 집행이 없는 것」의 실례).

## 4. 구현 — `createScreenshot`

- `domains/d7_visualization/screenshot.py` (신규) — 뷰포트 최근접 표본화 ＋ `over` 알파 합성.
  **색 규칙은 `tiles.py` 와 한 벌**(`_colors_rgba` 재사용) — 두 벌로 두면 화면과 스크린샷 색이 갈린다.
- `app/routes/screenshots.py` (신규) — 계약 스키마 그대로(`layers` `minItems:1` · `opacity` 기본 `0.55`
  · `Viewport` 4096 상한 · `Bounds` WGS84). 인증은 `require_caller`(서비스 토큰)만 — **타일의 서명
  우회로를 여기 열지 않았다.**
- `app/main.py` — 라우터 등록 ＋ 「등록하지 않은 것」 주석 갱신.

**판정 규칙 둘을 기록한다.**
- **수명이 다한 렌더 = 404.** 계약 `/screenshots` 의 응답에 **410 이 없다** — 없는 상태 코드를
  지어내지 않는다(타일 경로는 410 을 갖고 있고, 그 차이는 계약이 정한 것이다).
- **데이터 밖 뷰포트 = 200 투명.** 없는 좌표를 지어내지 않는다(`DR-9`) — 밖은 실패가 아니다.

### 시험 (red → green)

**red 확인** — 구현 전 `tests/test_screenshot.py` **9건 전건 fail**. ⚠ 첫 작성본은 404 두 건이
**라우트 부재의 404 로 우연히 green** 이었다 — 오라클이 아니므로 `code == "NOT_FOUND"` 봉투
단언을 더해 red 로 세웠다(green 으로 시작한 시험을 그대로 두지 않는다).

| 시점 | viz-render |
|---|---|
| 기준선 | **107 passed / 0 failed** (`COLAB_REFERENCE_DATA` 지정 시. 미지정이면 E2E 8건이 **fail-closed** — skip 이 아니다) |
| 최종 | **116 passed / 0 failed** (＋9 = 신규 시험 전건) |

### 게이트 (축자)

| 게이트 | 결과 |
|---|---|
| `contract-lint` | green — seam 3건, 룰 위반 0 |
| `contract-breaking` | green — 기준 HEAD(3건) 대비 파괴적 변경 없음 |
| `generated-up-to-date` | green — 등기부 4건 전부 재생성 일치 (⚠ `frontend/node_modules` 설치 **전에는** 도구 부재 red 였다) |
| `import-boundary` | green — 계약 8 kept / 0 broken |
| `banned-import` | green — .py 115건, 금지 import 0 |
| `db-boundary` | green — 단위 7 · 스캔 218건 · 위반 0 |
| `seam-consistency` | green — G-e 336 · G-b 7 · ㉠ 0 · ㉡ 18 |
| `stage2-markers` | green — 수집 17 · skipped 0 · failed 0 (⚠ `pipeline-worker/.venv` 설치 **전에는** 도구 부재 red) |
| `work-item-consistency` | **red — 이 회차 이전부터의 red 다.** ㈓ 잔존 3건(`PA`·`S2`·`2단-BC120`). 대장·산문은 이 에이전트 소유 밖이라 손대지 않았다 |

## 5. 범위 밖 — 이번에 하지 않은 것

- **`contracts/seams/**` 무수정.** 개정 필요 0건.
- **`services/core-api/**`·`services/ai-service/**`·`services/pipeline-worker/src/**` 무수정.**
- **프런트엔드 무수정** — 스크린샷 버튼·미등록 미리보기 화면(`UnregisteredPreviewPage.tsx`)의
  확대·값 조회·스크린샷은 `P3` 소유이되 **서버 경로가 선 다음**이다. core-api 중계
  (`createScreenshot` 의 FE 도달 경로)가 없으면 버튼이 갈 곳이 없고, 그 중계는 core-api 파일 면이다.
- **staging 배포·배포 판정 안 함** — 완료 판정 3항(staging green)은 **미충족**이다. `P3` 은 닫히지 않는다.

## 6. `[미확인]`

- **㉰ 「경계·점」 표현의 원천** — 벡터 원천이 실제로 있는가. 없으면 이 둘은 그릴 대상이 없다.
  푸는 법 = `40 COLAB-기획/` 정본이 요구하는 「경계·점」의 입력 포맷을 지목하게 한다.
- **㉲ 렌더 성능·상한의 합격선** — 「몇 초·몇 픽셀」이 어느 문서에도 없다.
- **㉱ 계보 그래프의 파일 면 배정** — core-api 를 여는 에이전트가 누구인가.
- **`§10.2` 말미 「타일 서빙」과 `〈63〉-㉮` 「P2 로 나감」의 어긋남** — §2 의 해석이 맞는지.
- **staging 배포 green** — 이번 회차에 재지 않았다(배포 금지 지시).
