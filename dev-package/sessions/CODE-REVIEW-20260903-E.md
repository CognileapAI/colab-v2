# CODE-REVIEW-20260903-E — 레인 E `frontend` 집행 기록

> 근거 — `CODE-REVIEW-20260903.md` 9 + 부록(화면 소결함) · 집행 계획 `CODE-REVIEW-20260903-PLAN.md §2` 레인 E.
> 기준 커밋 — `d4d11b5`(lane-review-clean). 편집 면 — `frontend/**` 만. 계약·인프라·서비스 무수정.
> 브랜치 — `worktree-agent-a146c87cfdffbbbf2`. push 없음 · 병합 없음 · 대장 번호 발급 없음.

## 1. 계수 — 전/후

| 눈금 | 착수 전(`d4d11b5`) | 종료 후(`028657d`) | 잰 시점 |
|---|---|---|---|
| `frontend/node_modules/.bin/tsc --noEmit` | 오류 0건 | 오류 0건 | 2026-09-03 |
| `frontend/node_modules/.bin/vitest run` | 32파일 · 520건 통과 | 35파일 · 563건 통과 | 2026-09-03 |
| `./gates/run.sh frontend-typecheck` | (재지 않음) | green | 2026-09-03 |
| `./gates/run.sh frontend-test` | (재지 않음) | green | 2026-09-03 |

게이트 출력 축자 —

```
frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.
frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 563건 · 실패 0건.
    Test Files  35 passed (35)
         Tests  563 passed (563)
```

- 시험 증가 — 파일 +3(`honest-source-20260903` · `screen-guards-20260903` · `upload-preview-poll-20260903`), 건수 +43.
- **기존 실패 0건.** 착수 전 전부 green 이었으므로 「보고만 하고 고치지 않는 기존 실패」는 없다.

## 2. 커밋 셋

| sha | 제목 | 비고 |
|---|---|---|
| `3e74dae` | 프론트 픽스처 폴백 제거 — 401 은 인증 경로로, 그 밖은 오류 상태 + 다시 불러오기 | 항목 1·2 |
| `daf5139` | 화면 소결함 셋 — 값 조회 순서 보호 · 구간 수 빈 칸 · 「오늘」의 경계 | 항목 3·4·5 |
| `028657d` | 업로드 미리보기 폴링 취소 — 옛 렌더가 새 화면을 덮지 않는다 | 항목 6 · **병합 때 떼어낼 수 있는 커밋** |

- `frontend/test/upload.test.tsx` **무수정**(동시 편집 중인 핫 파일). 항목 6 의 시험은 새 파일에 세웠다.

## 3. 항목별 — 변경 · 시험 · 전/후

### ⑴ 정직한 빈 상태 — 픽스처 폴백 제거 (리뷰 9)

**변경**

- `frontend/src/components/catalog/catalogSource.ts:defaultCatalogSource` — `try/catch → stub` 삭제. `NotImplemented`(501) 갈래도 삭제(죽은 사유).
- `frontend/src/components/detail/detailSource.ts:defaultDetailSource` — 같음. 404 → `DatasetGone` 은 유지.
- `frontend/src/components/project/projectSource.ts:defaultProjectSource` — 같음. 404 → `ProjectGone` 유지, 쓰기 다섯은 종전대로 폴백 없음.
- `frontend/src/components/lineage/graphSource.ts:defaultLineageSource` — 같음.
- `frontend/src/components/catalog/useCatalog.ts:CATALOG_LOAD_FAILED`·`reload` — 실패 시 `list`·`facets` 를 비우고 고정 문구를 세운다. 종전에는 `e.message` 를 그대로 써서 네트워크 오류의 `Failed to fetch` 가 사람에게 나갈 수 있었다.
- `frontend/src/components/detail/useDatasetDetail.ts:DetailState` — `{status:'error'}` 신설(종전 실패는 `loading` 으로 되돌아 **영구 빈 화면**).
- `frontend/src/components/project/useProjects.ts:useProjects` — `try/catch` 신설(**종전에는 `catch` 자체가 없어** 목록 실패가 미처리 거절로 샜다) + `failed`·`reload`.
- `frontend/src/components/project/useProjects.ts:useProject` — `{status:'error'}` + `reload`.
- `frontend/src/components/common/LoadFailure.tsx`(신규) — 문장 하나 + 다시 불러오기 하나. 결은 `TodoInbox`(`Policy_홈_대시보드 §9` 「처리할 일을 불러오지 못했어요. 잠시 뒤 다시 시도해 주세요.」+ 「다시 불러오기」).
- `frontend/src/shell/shell.css:.loadfail` — 화면별 CSS 가 갈라져 있어 전역인 셸에 둔다.
- 화면 넷 — `routes/DatasetsPage.tsx`(표 대신 실패 자리) · `routes/DatasetDetailPage.tsx`(상세 · 계보 각각) · `routes/ProjectsPage.tsx` · `routes/ProjectDetailPage.tsx`.

**문구** — 기존 결을 따랐다. 「…을 불러오지 못했어요. 잠시 뒤 다시 시도해 주세요.」 + 「다시 불러오기」.
새 말을 만들지 않았고, **원인을 지어내지 않는다**(서버 응답 원문을 사람에게 내보내지 않는다).

**「없는 것」과 「못 읽은 것」을 가른 자리** — 실패 상태에서는 아래를 세우지 않는다.
`CatalogTable` 의 「조건에 맞는 데이터가 없어요」 · `ProjectsPage` 의 「조건에 맞는 프로젝트가 없어요」 ·
`DatasetDetailPage` 의 「이 주소에는 화면이 없어요」 · `ProjectDetailPage` 의 「이 프로젝트를 찾을 수 없어요」.

**계보** — `LineageSection` 은 여전히 세우지 않고(빈 계보·남의 계보를 그리지 않는다는 종전 규칙 유지),
그 자리에 실패 자리를 둔다. `§8` 「항상 표시」와 어긋나지 않으면서 못 읽은 사실을 말한다.

### ⑵ 인증 만료 신호 — 무엇을 재사용했고 왜

**재사용한 것** — `frontend/src/auth/store.ts:clearToken`.
`AuthGate` 는 `useToken()`(=`useSyncExternalStore(subscribe, getToken)`)으로 그 저장소를 이미 구독하고 있고,
`/me` 가 401 이면 스스로 `clearToken()` 을 부른다. **곧 만료 신호는 이미 존재했다** — 화면 쪽 출처들이 그것을
부르지 않았을 뿐이다. 그래서 `SessionExpired` 같은 새 오류형·새 이벤트를 만들지 않았다.

**둔 자리** — `frontend/src/api/client.ts` 의 `api.use({ onResponse })` 한 곳.
같은 파일의 `onRequest`(토큰 첨부)가 「붙이는 자리가 여럿이면 하나가 빠진 것을 아무도 못 본다」를 이유로
한 곳에 있고, 401 을 알아채는 일도 같은 성질이다. 화면마다 따로 알아채면 빠진 화면만 만료된 세션으로 계속 그려진다.
`POST /sessions`(로그인)는 제외 — 거기서의 401 은 만료가 아니라 자격 오류이고 버릴 토큰도 없다.

**AuthGate 자체** — `/me` 에 `.catch` 가 없어 서버 불통이 `auth-pending` 영구 빈 화면이었다.
못 닿음·5xx 를 `auth-unreachable`(문구 + 「다시 시도」)로 세우고 **토큰은 버리지 않는다** — 로그인 문제가 아니다.
401 만 종전대로 토큰을 버린다.

### ⑶ `ValueLookupPanel` 순서 보호

`frontend/src/components/datasetpreview/ValueLookupPanel.tsx:useValueLookup` — 누름마다 순번(`seq`)을 올리고,
돌아온 값은 순번이 최신일 때만 화면에 적는다. 성공·실패 두 갈래 모두 막는다.
**취소가 아니라 무시**다 — 계약에 조회 취소가 없고 서버는 이미 답을 만들었다.

### ⑷ 업로드 `PreviewPanel` 구간 수 빈 칸

`frontend/src/components/upload/PreviewPanel.tsx:classCountOf`(신규, export) — 빈 칸·공백·숫자 아닌 것은
값이 아니라 없음이므로 기본값 6. 종전 `Number('')` 은 0 이었고 그 0 이 계약 `RenderStyle.classCount`(3~9) 밖이다.

> **지시와 실물의 차이 · 보고** — 레인 지시는 이 결함을 「`preview/` 사본」으로 적었으나, 실물에서
> `preview/PreviewControls.tsx` 의 구간 수는 `<select>` + 고정 후보(3~9)라 `Number('')` 이 날 수 없다.
> 자유 입력(`<input type="number">`)은 `upload/PreviewPanel.tsx` 한 곳뿐이고 리뷰 부록의 행 번호(208)도 그 파일을 가리킨다.
> 그래서 **`upload/PreviewPanel.tsx` 를 고쳤다.** 항목 6 과 같은 파일이지만 커밋은 갈랐다.

### ⑸ `visits.ts` 일 경계

`frontend/src/components/dashboard/visits.ts:relativeTime`·`startOfLocalDay`(신규) —
24시간 창이 아니라 **지역 달력 날짜의 0시** 두 개의 차로 센다. 종전에는 어제 23시에 연 것이 오늘 아침에 「오늘」이었다.
`Math.round` 를 쓴 이유 — 서머타임 지역에서 하루가 23·25시간이라 `floor` 면 날짜 차가 하나 어긋난다.

### ⑹ 업로드 `PreviewPanel` 폴링 취소 — **떼어낼 수 있는 커밋** `028657d`

`frontend/src/components/upload/PreviewPanel.tsx:pollGen`·`draw`·`poll` — 세대 번호를 두어
새로 그리기 시작할 때와 언마운트에서 올리고, 돌아온 값은 세대가 다르면 버린다.
`clearTimeout` 은 **예약된 다음 조회**만 지우므로 이미 응답을 기다리는 조회를 막지 못했다 —
그래서 옛 렌더의 늦은 응답이 새 화면을 덮었고, 떠난 화면 뒤로 폴링이 다시 예약돼 계속 돌았다.

**중복 제거는 하지 않았다** — `preview/usePreviewRender` 와의 통합은 유보 항목(계획 `§4`-11). 취소만 담았다.

## 4. 시험 — 무엇을 추가했고 red 를 언제 봤나

| 파일 | 잠근 것 | red 확인 |
|---|---|---|
| `frontend/test/honest-source-20260903.test.tsx`(신규) | 출처 여섯(catalog list·facets · detail · project list·get · lineage) × **401·500·네트워크·성공** 네 갈래 · 404 와 못 읽음의 분리 · 화면 넷의 오류 자리와 픽스처 부재 · 세션 만료 시 로그인 화면 · `AuthGate` 세 갈래 | `git stash push -- frontend/src` 로 `d4d11b5` 상태에서 실행 → **19건 red** |
| `frontend/test/screen-guards-20260903.test.ts`(신규) | `classCountOf` 빈 칸·공백·비숫자 · `relativeTime` 달력 경계 4건 | 같은 방식 → 4건 red(`classCountOf is not a function` 2 · 날짜 2) |
| `frontend/test/dataset-value-lookup.test.tsx`(추가 2건) | 느린 이전 누름이 최신 값을 덮지 않음 · 늦게 온 이전 실패가 최신 값을 덮지 않음 | 같은 방식 → 2건 red(`expected '111 mm' to be '222 mm'`) |
| `frontend/test/upload-preview-poll-20260903.test.tsx`(신규) | 다시 그리기 뒤 옛 응답 폐기 · 언마운트 뒤 폴링 재예약 없음 | 항목 6 수정 전 실행 → **2건 red** |

## 5. 운영 경로가 픽스처에 닿지 않는다 — 증명

**grep**

```
$ grep -rn "from '.*fixture'\|from '.*graphFixture'\|from '.*localEngine'" frontend/src --include='*.ts' --include='*.tsx'
frontend/src/components/catalog/fixture.ts:4:import { runFacets, runQuery } from './localEngine';
```

- 화면·출처 코드에서 픽스처로 가는 import **0건**. 남은 한 줄은 픽스처가 자기 엔진을 쓰는 것이다.
- `localEngine.ts` 는 **지우지 않았다** — `catalog/fixture.ts` 가 쓰고 있으므로 미사용이 아니다. 픽스처와 함께 시험 전용으로 남는다.

**도달성** — `frontend/scripts/reachable-from-entry.mjs`(신규) 가 `src/main.tsx` 에서 상대 import 를 따라가 닿는 모듈을 세고, 금지 목록에 닿으면 rc=1 로 끝난다.

```
$ node scripts/reachable-from-entry.mjs
entry=src/main.tsx reached=128
금지 모듈에 닿지 않는다: /fixture.ts · /graphFixture.ts · /localEngine.ts
```

- 픽스처는 시험이 **인자로 꽂을 때만** 선다(`test/*.test.tsx` 12파일이 `source={fixtureXSource()}` 로 꽂는다).

## 6. `[미확인]` — 이번에 재지 않은 것

- **브라우저 실동작** — jsdom 은 레이아웃·네트워크 스택·탭 전환을 흉내 내지 않는다. 아래는 이 회차가 재지 못했다.
  - 실제 401 이 왕복하는 동안의 화면 전환(로그인 화면으로 넘어가는 순간의 깜빡임·스크롤 위치).
  - `.loadfail` 의 실제 배치·줄바꿈(전역 CSS 를 새로 넣었으나 vitest 는 `catalog.css` 만 싣는다).
  - 다시 시도 손잡이의 포커스 이동·스크린리더 낭독 순서(`role="alert"` 는 마크업으로만 확인).
  - **푸는 법** — 화면 스모크(Playwright)로 401·500 대역을 세워 네 화면과 `AuthGate` 를 한 번씩 지나가면 풀린다.
- **`AuthGate` 의 자동 재시도** — 넣지 않았다(사람이 눌러야 다시 부른다). 서버가 잠깐 죽었다 살아나는 동안의 체감은 재지 않았다.
- **`relativeTime` 의 서머타임 지역** — `Math.round` 로 막았으나 시험은 한국 시간대(서머타임 없음)에서만 돌았다.
  **푸는 법** — `TZ=America/New_York` 로 vitest 를 한 번 더 돌리면 풀린다.
- **`api/client.ts` 401 미들웨어의 범위** — 이 회차 시험은 화면 넷과 `/me` 만 지난다. 대시보드·검색·미리보기 경로에서도
  401 이 같은 길로 가는지는 **코드 한 곳이라는 사실**로만 서 있고 시험으로 못 박지 않았다.

## 7. 유보 — 이 레인이 손대지 않은 것

- 업로드 `PreviewPanel` 과 `preview/usePreviewRender` 의 **중복 제거**(계획 `§4`-11). 이번에는 취소만.
- **페이징 반쪽**(리뷰 14 · 계획 `§4`-4) — 편집 면 안이지만 레인 항목에 없다. 서버 `totalCount` 실값이 함께 필요하다.
- `LineageStep.tsx` 마지막 카드 거절 후 「1 / 1」 잔류 · `download.ts`/`ScreenshotButton.tsx` 동기 revoke(PLAUSIBLE, 브라우저 의존) — 레인 항목 밖.
- 계보 수정 UI 배선(계획 `§4`-8).

## 8. 등재문 초안 (번호 없음 — 오케스트레이터가 발급한다)

> **프론트 「정직한 빈 상태」 복구 — 픽스처 폴백 제거 · 만료 신호 일원화 · 화면 소결함 넷.**
> 카탈로그·데이터셋 상세·프로젝트·계보의 네 출처가 빈 `catch` 로 401·500·네트워크 오류를 픽스처로 바꿔 그렸다.
> 근거였던 501 은 죽은 사유다(해당 op 넷은 구현돼 있고 `not_implemented.py` 목록에 없다). 폴백이 덮고 있던 것은
> 미구현이 아니라 **장애와 세션 만료**였고, 그래서 만료된 세션이 가짜 여섯 행을 보며 로그인으로 돌아가지 않았다.
> ㉮ 401 — `frontend/src/api/client.ts` 응답 미들웨어 한 곳에서 토큰을 버린다. **새 통로를 만들지 않았다**:
> `auth/store.clearToken` 이 `AuthGate` 가 이미 구독하는 신호다. 로그인 op 은 제외(자격 오류이지 만료가 아니다).
> ㉯ 그 밖의 실패 — 화면마다 「…을 불러오지 못했어요. 잠시 뒤 다시 시도해 주세요.」 + 「다시 불러오기」
> (`components/common/LoadFailure.tsx`). 빈 표의 「조건에 맞는 데이터가 없어요」·묘비 문구로 접지 않는다.
> ㉰ `AuthGate` — `/me` 실패가 영구 빈 화면이었다. 못 닿음·5xx 는 오류 + 다시 시도이고 **토큰은 버리지 않는다.**
> ㉱ 화면 소결함 넷 — 값 조회 순서 보호(늦은 이전 응답이 다른 칸의 값을 그렸다) · 구간 수 빈 칸이 계약 밖 0 으로
> 나가던 것 · 「오늘」을 24시간 창으로 세던 것 · 업로드 미리보기 폴링 취소 불가.
> ㉲ 픽스처는 시험이 손으로 꽂을 때만 선다. `frontend/scripts/reachable-from-entry.mjs` 가 `src/main.tsx` 에서
> 닿는 128 모듈에 `fixture.ts`·`graphFixture.ts`·`localEngine.ts` 가 없음을 rc 로 증명한다.
> 계수 — `tsc --noEmit` 오류 0건(전후 동일) · `vitest run` 32파일 520건 → **35파일 563건** 전건 통과.
> 게이트 — `frontend-typecheck` green · `frontend-test` green.
> 재지 않은 것 — 브라우저 실동작(401 왕복 중의 화면 전환 · `.loadfail` 실제 배치 · 포커스·낭독 순서) ·
> 서머타임 지역의 날짜 경계 · 401 미들웨어가 대시보드·검색·미리보기 경로에서도 같은 길인지.
