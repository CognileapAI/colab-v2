# P1-fe-detail — S-05 데이터셋 상세 **상단**(헤더 + 기본 정보)

> 레인 산출 보고. 커밋·`03-HANDOFF`·`PLAN-SoT` 갱신은 **메인 세션의 일**이다 (`P1.md §5-4`).
> 오라클 = `E-03_데이터셋_상세/documents/Policy_데이터셋_상세.md` (v2.1) 와 그 목업 `데이터셋_상세_260817.html`.

## 1. 한 줄

- S-05 **상단만** 세웠다 — 되돌아가기 · 헤더 4줄 · 기본 정보 9칸 · 잠긴 상세 · 묘비(404).
- 계보 그래프 · 미리보기 · 활용 프로젝트는 **만들지 않았다** (P2·P3·P5).
- `getDataset` 가 501 인 동안 픽스처로 그리고, **서버가 붙어도 화면 코드는 0줄 바뀐다**.

## 2. 만든 것

| 파일 | 역할 |
|---|---|
| `frontend/src/routes/DatasetDetailPage.tsx` | 화면 본체. 되돌아가기 · 헤더 · 기본 정보 · 잠김 · 묘비의 배치만 한다 |
| `frontend/src/components/detail/types.ts` | 계약 생성물 재수출 + `DetailSource` + `DatasetGone` |
| `frontend/src/components/detail/detailSource.ts` | 실서버 우선 · 501/네트워크면 픽스처. **404 는 폴백하지 않는다** |
| `frontend/src/components/detail/fixture.ts` | 정본 목업 값만 담은 픽스처 6건 |
| `frontend/src/components/detail/useDatasetDetail.ts` | 상태 셋 — 읽는 중 · 그린다 · 묘비 |
| `frontend/src/components/detail/DetailHeader.tsx` | 헤더 4줄 + E-06 자리 |
| `frontend/src/components/detail/BasicInfoGrid.tsx` | 기본 정보 9칸 |
| `frontend/src/components/detail/LockedNotice.tsx` | 잠김 안내 + 접근 요청 자리 |
| `frontend/src/components/detail/format.ts` | 기간·용량·파일 칸 표기 |
| `frontend/src/components/detail/detail.css` | 목업 `:root`·블록에서 값 그대로 옮김 |
| `frontend/test/detail.test.tsx` | 정본 대비 시험 **22** |

**공유 파일 수정은 딱 한 곳** — `frontend/src/app/routes.tsx` 에 `/datasets/:datasetId` 라우트 등록(import 1줄 + Route 1줄). 카탈로그가 이미 이 주소로 `navigate` 하고 있었다.

## 3. 정본을 어떻게 지켰나

| 정본 | 화면 |
|---|---|
| `§8` 되돌아가기 = 헤더 **밖 제 줄**에 `← {들어온 곳}` 하나 | `.backrow` 가 `.dt-header` 밖. 링크 1개. 브레드크럼·형제 전환 없음 (`§12` v2.2) |
| `§8` 헤더는 **줄마다 한 가지** — 이름 / 파일명 / 요약 / 칩 | 그대로. 칩은 주제 · `Lv{n}` · (잠김) · Verified 자리뿐 |
| `§12` v1.6 중복 3건 제거 — 소유자·올린 사람·포맷을 헤더에 두지 않는다 | 시험이 헤더 안에 `호랑이`·`소유자`·`올린 사람` 이 없음을 확인 |
| `§8` 헤더 우측 **한 자리**가 상태 × 보는 사람으로 셋으로 갈린다 | `data-slot="verification-action"` `data-fills-in="WU-P6"` 로 비워 둠 |
| `§5` 기본 정보 **아홉 칸**, 공간 범위 칸 없음 | 구성·좌표계·기간·격자·포맷·파일·원천 표기·소유자·올린 사람 (순서 시험) |
| `§5` `파일` 칸은 조각 수와 용량 합계만, 1건이면 파일명·용량 | `조각 4개 · 합계 148 MB` / `nakdong_DEM_10m.tif · …`. 조각을 나열하지 않음 |
| `§7` 잠김(허용 안 됨) = 헤더 요약 + 잠김 안내만 | `basicInfo` null → **기본 정보 블록 통째로 없음**. 상세에는 `조각 N` 이 없다 — 카탈로그와 달라 보이는 것은 의도 (`PLAN-SoT §9-㊼-④`) |
| `§9` 지워진 데이터의 주소로 직접 들어옴 | 404 → "이 데이터는 지워졌어요. 계보 기록은 관련 데이터의 상세에서 볼 수 있어요." + 목록으로 |
| `E-01 §4` · `P-7`·`P-12` 권한 없는 기능은 **숨긴다** | 상단에 편집 컨트롤을 아예 두지 않았고, 노출 판정은 전부 서버의 `actions.*` 로만 간다. 비활성 버튼·툴팁 없음 |
| `§8` Verified 배지는 표시 전용 | `VerifiedBadgeSlot` (P6 이 채움). 누를 수 있는 요소로 만들지 않았다 |

## 4. 501 → 실서버 전환이 0줄인 근거

- 화면은 `DetailSource` 하나만 안다. 픽스처와 `getDataset` 이 **같은 얼굴**이다 (카탈로그 레인의 `CatalogSource` 와 같은 패턴).
- `defaultDetailSource()` 가 실서버를 먼저 부르고 **501·네트워크 실패에만** 픽스처로 내려간다.
- **404(묘비)는 폴백하지 않는다** — 지워진 데이터를 픽스처로 되살리면 화면이 거짓말을 한다.
- 시험 `501 → 실서버 전환에 화면 코드가 바뀌지 않는다` 가 서버 응답을 그대로 넣어 같은 자리가 그려짐을 증명한다.
- 픽스처는 **계약 타입**을 쓰고 픽스처 고유 필드가 없다 — 화면이 픽스처 모양에 붙지 않았다.

## 5. 시험 · 게이트 (실측)

**red 를 먼저 봤다** (`CLAUDE.md §4`) — 첫 실행은 `Failed to resolve import "../src/routes/DatasetDetailPage"` 로 `Tests no tests`.

```
frontend $ npx vitest run
 Test Files  5 passed (5)
      Tests  73 passed (73)      ← 그중 detail.test.tsx 22
frontend $ npm run typecheck     ← tsc --noEmit, 출력 없음(=통과)
```

**시험이 실제로 판정하는지 4방향으로 확인**(변형 → red → 되돌림):

| 변형 | 결과 |
|---|---|
| 기본 정보에 `공간 범위` 칸을 되살림 | × 라벨과 순서 · × 공간 범위 칸을 두지 않는다 |
| 소유자를 헤더로 올림 | × 소유자·올린 사람·포맷을 헤더에 두지 않는다 |
| `파일` 칸의 단일 파일 규칙 제거 | × 파일이 한 건이면 파일명과 용량을 그대로 쓴다 |
| 페이지의 `basicInfo` null 가드 제거 | × `basicInfo` 가 null 이면 그리지 않는다 |

**게이트** (`./gates/run.sh <gate>`):

```
contract-lint            GREEN
contract-breaking        GREEN
event-lint               GREEN
event-breaking           GREEN
generated-up-to-date     RED   ← 미구현 게이트. 이 레인 이전부터 red (gates/README 「현재 상태」)
import-boundary          GREEN
banned-import            GREEN
ai-no-lineage-write      GREEN
migration-single-head    GREEN
rls-coverage             GREEN
planning-freshness       GREEN
```

`schema-diff` · `rls-effect` 는 적용 DB URL·도커가 있어야 판정한다 — 이 레인이 `db/` 를 건드리지 않았으므로 상태를 바꾸지 않는다. `selftest` 는 별도로 돌려 **exit 0 · 판정 139 케이스 전부 의도대로**(`rls-effect-selftest green — 보호 장치를 하나씩 떼면 실제로 red 가 난다. 틀린 롤도 red 다.`) 를 확인했다.

## 6. `[정본 무근거]` — 만들지 않고 남긴다

| # | 항목 | 지금 한 것 |
|---|---|---|
| ① | **빈 값의 표기 문자.** 정본은 `§5` 파일 목록에만 "없으면 없다고 적는다"를 두고, 기본 정보 칸이 비었을 때의 표기는 정하지 않았다 | `—` 한 글자로 통일(`format.ts` `EMPTY`). 정본이 값을 주면 한 곳만 고친다 |
| ② | **기간 표기 규칙.** 목업 예시 `2025-06 ~ 09` 하나뿐이고 일반 규칙이 없다 | 그 예시를 그대로 재현하는 규칙(해가 같으면 뒤 해 생략)만 구현 |
| ③ | **용량 단위 계단.** 목업은 `MB` 만 보여 준다 | MB 기준, GB 이상만 소수 1자리. 계단 자체는 근거 없음 |
| ④ | **레코드 시점(올린 날·마지막 수정)의 자리.** `§4` 가 용어로 정의하지만 헤더에도 기본 정보 9칸에도 없고, 목업의 `recline` 은 9칸 이전 판이다 | **그리지 않았다.** 자리를 정본이 줄 때까지 만들지 않는다 |
| ⑤ | **불러오다 실패했을 때의 안내 문구.** `§9` 표에 이 행이 없다 | 문구를 만들지 않고 빈 `aria-busy` 상태로 둔다. 현재 경로에서는 픽스처 폴백이 있어 도달하지 않는다 |
| ⑥ | 픽스처 4건(`AA2·AA3·AA4·AA6`)은 **상세 목업이 없다** — 카탈로그 목업 6행만 있다 | 구성·좌표계·기간·격자·포맷·원천 표기·용량을 **비워 두었다**(null·0 → 화면은 `—`). 없는 값을 지어내지 않았다 |

## 7. 의도적으로 범위 밖에 둔 것 (다음 WU 가 가져간다)

| 항목 | 근거 | 주인 |
|---|---|---|
| `파일` 칸의 `보기` → 조각 목록 | `listDatasetFiles` op 이 501 이고 P1-api 범위 밖. 501 을 부르는 버튼은 만들지 않는다 | P1-api 이후 / P2 |
| 다운로드 버튼(용량 표시 포함) | `§8` 이 **활용·접근 섹션**에 위치를 못박았다 — 상단이 아니다 | P5 |
| `✓ 승인 요청` · 승인 · 승인 취소 · Verified 배지 실물 · `접근 요청` 버튼 | E-06 정책이 정한다 | P6 |
| 섹션 내비(계보/미리보기/활용·접근) | 가리킬 섹션이 아직 없다 | P2·P3·P5 |
| `accessRequestPending` → `검토 대기` 칩 | 계약 설명이 `Policy_승인_처리`·`Policy_데이터_찾기` 를 근거로 든다 = E-06 | P6 |
| 계보 `이후 수정됨` 표시 | 계보 구역 맨 위 (`§8`) | P2 |

## 8. 메인 세션이 봐 줄 것 (STOP 아님, 확인 요청)

1. **파일 위치.** 지시서 표기는 `frontend/src/pages/DatasetDetailPage.tsx` 지만, 이미 닫힌 레인들의 화면이 전부 `frontend/src/routes/` 에 있어 **`src/routes/DatasetDetailPage.tsx`** 로 두었다. 집 규칙(실물)을 따랐다.
2. **되돌아가기 라벨.** 기본값 `데이터셋 목록`(목업 그대로). 들어온 곳이 프로젝트면 그 이름을 부르려면 부르는 쪽이 `state: { backLabel, backTo }` 를 실어야 한다 — 페이지는 이미 읽는다. 카탈로그(`DatasetsPage.tsx`)는 **남의 레인이라 건드리지 않았다.** P5(프로젝트 상세)가 진입할 때 함께 정하면 된다.
3. **`목업 vs 정본` 충돌 1건.** 목업 `데이터셋_상세_260817.html` 은 기본 정보를 **4칸**으로 그리고 포맷·원천 표기·소유자·올린 사람을 뺐다는 주석을 달고 있다. 정책문서 `§5`(v1.9, 2026-08-18 · 목업보다 나중)와 동결된 계약 `DatasetBasicInfo` 는 둘 다 **아홉 칸**을 못박는다. **정본 문서를 따랐다** (`PLAN-SoT §9-㊸-④-2` 「문서가 정본, 목업은 예시」).
4. **계약은 한 자도 고치지 않았다.** 고쳐야 할 것으로 보인 곳도 없다.
