# P3 — 지도 화면을 타일 방식으로 (2026-08-31 · 워크트리 `lane-tile`)

> **판정 정본은 `PLAN-SoT §9 〈238〉` 하나다** — 값·근거·기각안을 두 곳에 적지 않는다.
> 이 문서는 **회차의 명령과 수치**를 남긴다.

## 1. 착수 전 실측 — 장부를 믿지 않고 다시 쟀다

| 잰 것 | 값 |
|---|---|
| 완료된 렌더 결과(등록 데이터셋 · 지도형)의 키 | 아홉 — `tileUrlTemplate` **없음**. `jobs.py` 의 「stage 1 은 이미지 갈래만 낸다」 분기가 실물이었다 |
| 타일 서빙 | **선다** — `GET /viz/v1/renders/{id}/tiles/{z}/{x}/{y}.png` **200 ＋ `image/png`** · 서명 발급도 그대로 |
| 계약 `RenderResult` | `oneOf: [imageUrl] \| [tileUrlTemplate]` ＋ `dependentRequired {tileUrlTemplate: [bounds]}` — **두 갈래가 이미 있다** |
| 화면 소비부 | `preview/tiles.ts` 는 서 있으나 타일 갈래를 **0/0/0 한 장**으로만 그렸다 — 표면이 아니었다 |
| 게이트 `all` (before) | **green 35 / red 0** · `render-latency` p95 **2.065초** |
| 시험 (before) | viz-render **146** · frontend **368** · core-api **505** · pipeline-worker **204** · `tsc` **0** |

⚠ **워크트리에는 `.venv`·`node_modules` 가 없다** — 본 체크아웃의 것을 심볼릭으로 잇고 나서야
게이트가 판정을 낸다. 잇기 전 첫 회차는 `red(준비) 3 / red(판정) 1` 이었고 그것은 **환경이 낸
red 이지 이 브랜치가 낸 red 가 아니다.** 원장에 지우지 않고 적어 둔다.

## 2. red 로 먼저 세운 시험 — 오라클은 정본과 계약뿐이다

| 자리 | 건수 | red 확인 | 오라클 |
|---|---|---|---|
| `services/viz-render/tests/test_render_result_tiles.py` | 6 | **3 red** (나머지 셋은 성질을 잠그는 음성·회귀 시험) | 계약 `core-viz.yaml#RenderResult` · `CLAUDE.md §3`(경계를 지어내지 않는다) |
| `frontend/test/dataset-preview-tiles.test.tsx` | 15 | **14 red** | 정본 `Policy_데이터셋_상세` **v2.6 §8** 확대 조건 **일곱** 축자 ＋ 계약 `tileUrlTemplate` |

**「추정으로 오라클을 쓰지 않는다」** — 시험 파일 머리글이 인용한 문장은 전부 정본·계약 축자이고,
없는 수치(픽셀 상한 · 레벨 수)는 시험이 정하지 않는다.

## 3. 구현한 것

- `d7_visualization/jobs.py` — `RenderJob.tile_branch` 신설. **지도형 ＋ 등록 데이터셋 ＋ 서명 비밀**
  셋이 모두 참일 때만 결과가 `tileUrlTemplate` 을 싣고 `imageUrl` 을 **뺀다**(`oneOf` 택일).
- `frontend/src/components/preview/tileGrid.ts` — 웹 메르카토르 역변환 · 기본 레벨 · 배율→레벨 ·
  **보이는 조각만** 셈. 지도 라이브러리 **0건**.
- `frontend/src/components/preview/PreviewPanels.tsx` — `TileMosaic`. **변환은 층 묶음 하나에**
  걸리고 조각에 걸리지 않는다(조건 ⑸).
- `frontend/src/components/preview/useZoomPan.ts` — 원본 해상도를 **밖에서 받는 자리**
  (`onNativeWidth`) ＋ 화면 크기 재측정. **모르면 확대하지 않는다**(조건 ⑷).
- `frontend/src/components/datasetpreview/{types,datasetPreviewSource,DatasetPreviewSection}.ts(x)` —
  사이드카에서 원본 해상도를 **한 번만** 읽는 경로.

**계약 개정 0건**(동결 해제 직전이 11차 — 그대로) · **생성물 재생성 0건 · 손수정 0건** ·
**마이그레이션 0건** · core-api·pipeline-worker **무접촉** · staging **무접촉**.

## 4. 비지도형 — 없는 경계를 지어내지 않았다

좌표가 없는 결과는 **타일 갈래로 가지 않는다.** 시험이 음성으로 잠근다
(`test_비지도형은_타일_갈래로_가지_않는다` — `tileUrlTemplate` 없음 · `bounds` 없음 ·
`imageUrl == valuePreviewUrl`). 직전 회차가 그 자리에 스크린샷 버튼을 두지 않은 선례와 같은 결이다.

## 5. 회귀 재측정 — 확대 조건 일곱 ＋ 렌더 합격선

| # | 조건 | 타일 표면에서의 판정 |
|---|---|---|
| ⑴ | 확대·축소·이동 | ✔ |
| ⑵ | 설정·범례 불변 | ✔ (범례는 층 묶음 **밖**) |
| ⑶ | **렌더 재요청 0건** | ✔ — 확대·휠·되돌리기 **13회**에 `createPreviewRender` **0건** · `getPreviewRender` **1건 이하** · 사이드카 **1건 이하** |
| ⑷ | 데이터 해상도가 한계 | ✔ — 사이드카 `width` 4096 / 화면 512 = 한계 8 · 「원본 해상도까지 봤어요」 · **모르면 확대 안 함** |
| ⑸ | 모든 층에 함께 | ✔ (구조로 — 겹쳐 보기는 여전히 없다) |
| ⑹ | 보기 권한 · 저장 0 | ✔ (`localStorage.setItem` **0회**) |
| ⑺ | **100 ms** | ✔ — 확대·축소 1회 **p95 2.081 ms · 최대 2.758 ms** · 끌어 옮기기 **p95 1.384 ms · 최대 1.423 ms**(각 표본 20) |

**미리보기 최초 표시**(게이트 `render-latency` · 표본 25 · 포맷 5종) — **before p95 2.065초 → after p95 2.189초**
(중앙값 0.566 · 최대 2.257초 · 합격선 **p95 10초** · 상한 **60초**). **회귀 없음** — 이 회차가 서버 렌더 경로를
건드리지 않았고(바뀐 것은 결과에 무엇을 싣는가다) 두 값의 차는 같은 눈금 안의 회차 편차다.

**조건 ⑶ 을 정본 문면대로 판정했다.** 타일은 조각을 더 받으므로 요청 수 자체는 늘어난다.
정본이 금지한 것은 「**렌더를 다시 거는 것**」이고 판정 칸이 「확대 조작 중 **새 렌더 작업 생성**
0건」이다 — **사용자 조작이 서버 렌더를 다시 트리거하지 않는다**가 재는 것이고, 그것이 0건이다.
조각 수신은 「이미 그린 결과 안에서」 일어나는 일이라 그 금지에 걸리지 않는다.

## 6. 남은 것 — `P3` 를 닫지 않는다

「각 P 의 완료 판정」 4항 중 ③ **staging 배포 green** 이 **이 변경분에 대해 없다.**
도는 릴리스는 `2ef0276ab349` 이고 거기에는 타일 갈래가 없다. **배포 권한 밖이라 멈추고 보고한다** —
`P3` 는 `status: open` 으로 남는다. **부분 완료로 닫지 않는다.**
