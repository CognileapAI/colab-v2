# P2-fe-preview 실행 보고 — S-08 미등록 파일 미리보기 (W3)

> **작성** 2026-08-23 · 레인 `P2-fe-preview`(W3, `P2-viz` 뒤). **커밋하지 않았다.**
> `contracts/` 무수정 · `frontend/src/generated/` 무수정 — `generated-up-to-date` green 을 확인했다.
> **증거(EVIDENCE)와 해석(INTERPRETATION)을 섞지 않는다**(`M-5`). 관측하지 않은 숫자는 적지 않는다(`M-4`).
> 인용한 `file:line` 은 전부 `cat -n` 으로 확인했다(`M-7`).

---

## 0. 한 줄 결론

정본 §8.1 **8행 전부**를 화면에 세웠고 **23건의 시험이 red → green** 을 지났다.
**다만 정본 §8.1 「기본정보」 행은 절반만 충족된다** — 동결 계약이 미등록 업로드에 대해
포맷·좌표계·기간·격자를 **FE 표면으로 내려 주지 않는다.** 지어내지 않고 **자리째 뺐고**, 이 사실을
`§7-①` 로 올린다. 같은 자리에서 **`listPalettes` FE 중계 부재**(`D2c` C1 열린 항목 ①)가 실제로 화면을
막는 것을 확인했다 — 팔레트를 **고르는 자리가 열리지 않는다.**

---

# 증거

## 1. 진입조건 — 착수 시점 실측

| 전건 | 실측 |
|---|---|
| `generated-up-to-date` green (`P2-EXEC §4 FE 공통 선행` W0-7) | `generated-up-to-date green — 등기부 1건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.` |
| `P2-viz` 4 op (`P2-viz-report §13`-①) | `services/viz-render/src/colab_viz/app/routes/renders.py` · `.../domains/d7_visualization/failures.py` 실재 확인 |
| 중계 2 op (`P2-api-report §A-3`) | `services/core-api/src/colab_core/app/routes/preview.py:47` `createPreviewRender` · 같은 파일 `getPreviewRender` |
| 계약 동결 | `contract-lint green — seam 3건, 룰 위반 0.` / `contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.` |

## 2. 만든 것

전부 소유 디렉터리 안이다.

| 파일 | 줄 | 무엇 |
|---|--:|---|
| `frontend/src/components/preview/types.ts` | 81 | 포트·오류 어휘. **타입은 생성물에서만 온다**(`Schemas['RenderJob']` 등 재선언 0) |
| `frontend/src/components/preview/handoff.ts` | 57 | S-04 → S-08 이어짐(주소 + 라우터 state) |
| `frontend/src/components/preview/tiles.ts` | 13 | `tileUrlTemplate` 치환 **한 함수뿐** |
| `frontend/src/components/preview/previewSource.ts` | 94 | 중계 2 op + 타일 찔러보기 |
| `frontend/src/components/preview/usePreviewRender.ts` | 149 | 상태 기계 — 소비 규약이 여기 모인다 |
| `frontend/src/components/preview/PreviewPanels.tsx` | 180 | 고지·기본정보·단계·실패·부분실패·415·만료·지도·빈 자리 |
| `frontend/src/components/preview/PreviewControls.tsx` | 50 | 컨트롤 둘 |
| `frontend/src/components/preview/preview.css` | — | 화면 스타일 |
| `frontend/src/routes/UnregisteredPreviewPage.tsx` | 142 | 화면 본체 |
| `frontend/test/preview.test.tsx` | 390 | 정본 §8.1 대비 시험 23건 |

**공유 파일** — `frontend/src/app/routes.tsx` 에 **2줄**이 들어갔다(`cat -n` 확인):
`:11` import · `:22` `<Route path="/datasets/preview/:uploadId" element={<UnregisteredPreviewPage />} />`.
⚠ **지시는 「한 줄」이었고 실제는 두 줄이다** — 라우트 한 줄이 성립하려면 컴포넌트 import 한 줄이
반드시 따라온다. **감추지 않고 적는다.** 그 외에는 한 글자도 안 고쳤고, `Gnb.tsx`·`components/upload/`
는 **열지도 않았다**.

## 3. 순서 — RED 를 눈으로 봤다

### RED ① 모듈 부재 단계 (증거, 출력 그대로)

```
Error: Failed to resolve import "../src/routes/UnregisteredPreviewPage" from "test/preview.test.tsx".
 Test Files  1 failed (1)
      Tests  no tests
```

### RED ② 시험이 **하나씩** 자기 단언에서 죽는 단계 (증거, 출력 그대로)

모듈 부재 red 는 「오라클이 작동한다」를 증명하지 못한다. 빈 껍데기 화면(`data-screen="S-08"` 만)을
두고 **23건이 각자 단언에서 실패하는 것**을 봤다.

```
     × 정본 두 문장과 `연구실에 등록 →` 이 한 줄에 있다
     × 읽은 값의 자리만 서고, 못 받은 항목은 행이 아예 없다 (빈 칸·대시를 두지 않는다)
     × 넘겨받은 renderId 를 조회할 뿐 다시 그리지 않는다
     × `그리는 중` 일 때만 단계가 있고 문구가 정본 그대로다
     × status=실패 면 서버가 준 정본 문구를 그대로 말한다
     × 오류 자리가 아니라 안내 자리에 서고, 못 읽은 조각을 이름으로 밝힌다
     × 그릴 수 있는 형식을 함께 말하고 등록 길은 살아 있다
     × 조회가 없는 것으로 답하면 정본 문구를 그대로 낸다
     × 타일이 401 이어도 「권한이 없다」가 아니라 만료로 말한다 (`P2-viz-report A-1`)
     ... (전 21건)
 Test Files  1 failed (1)
      Tests  21 failed | 2 passed (23)
```

**2건이 처음부터 green 인 이유를 밝힌다** — ㈎ 「S-08 주소의 주인 탭이 데이터셋이다」는
`frontend/src/shell/nav.ts:36-37` 이 **이미 S-08 을 이름으로 예상해 두었다**(`// 미등록 미리보기(S-08)를
포함해 … 주인 탭은 `데이터셋`이다`). 내가 만든 것이 아니라 **확인한 것**이다. ㈏ `tileUrl` 순수 함수
시험은 그 파일을 먼저 쓴 탓에 green 이었다 — **오라클로 세지 않는다.**

### GREEN (증거, 출력 그대로)

```
 Test Files  1 passed (1)
      Tests  23 passed (23)
```

`npx tsc --noEmit` — **내 파일에서 오류 0.** 남은 8건은 전부 `test/upload.test.tsx`(형제 레인
`P2-fe-upload` 가 지금 쓰는 중인 파일)이고 **건드리지 않았다.**

## 4. 정본 §8.1 — 행 하나씩 대조

정본 `Policy_업로드와_계보_확정.md:219-230`(v2.3, `cat -n` 확인).

| 정본 행 (`:줄`) | 화면 | 시험 |
|---|---|---|
| **화면 귀속** `:223` | 주소를 `/datasets/preview/:uploadId` 로 둬 `ownerTabOf` 가 `datasets` 를 낸다 | ✅ 「S-08 주소의 주인 탭이 데이터셋이다」 |
| **휘발 고지** `:224` | 정본 두 문장 + `연구실에 등록 →` 을 **한 줄**에. **남은 시간을 숫자로 적지 않는다** | ✅ 2건 (문구 일치 · `/남았|남은 시간|\d+\s*(시간|분|초)/` 불일치 단언) |
| **기본정보** `:225` | 헤더에서 읽은 값만. **없는 항목은 행 자체가 없다** — 대시도 안 쓴다. 이름·주제·프로젝트는 자리 없음 | ✅ 2건 (`좌표계`·`기간`·`격자` 부재 · `—` 부재 · `주제` 부재) — **다만 `§7-①` 참조** |
| **미리보기** `:226` | S-04 가 넘긴 `renderId` 를 **조회**한다. 다시 그리지 않는다 | ✅ 2건 (`create` 호출 0회 · 이어받은 게 없으면 없다고 말함) |
| **계보 · 족보** `:227` | 빈 자리 + `등록하면 AI가 가공 전 데이터를 찾아 줘요` | ✅ |
| **검색 · 공유 · 승인** `:228` | 빈 자리 + `등록하면 연구실이 이 데이터를 찾을 수 있어요` | ✅ |
| **나가기** `:229` | `← 데이터셋 목록` 한 줄 → `/datasets` | ✅ |
| **수명** `:230` | 조회가 없는 것으로 답하면 `이 파일은 더 이상 없어요. 다시 올려 주세요.`(§9 마지막 행 문구 그대로) | ✅ 2건 (조회 404 · 타일 401) |

**부수로 지킨 것** — `§7.1` 「저장 안 됨」: 이 화면이 부르는 것은 **조회·타일·다시 그리기**뿐이고
시험이 호출 집합을 `{get, probeTile}` 로 단언한다. `§7.2` 「미등록 미리보기 → 등록 중」: `연구실에
등록 →` 이 목록으로 이동하며 `openUploadForRegister` state 를 실어 **모달을 열 열쇠만** 건넨다
(모달은 `P2-fe-upload` 소유라 열지 않는다).

**주제 미정**(`P2.md §2-17`-ⓒ) — S-08 에는 **주제 자리 자체가 없다.** 주제는 사람이 붙이는 값이라
등록 전에 자리를 두면 「비어 있는 주제」가 화면에 생긴다. 시험이 `주제` 문자열 부재를 단언한다.

## 5. 렌더 경로 소비 규약 — 하나씩 어떻게 지켰나

| 규약 (`P2-viz-report §13` · 부록 `A-4`) | 지킨 방식 | 시험 |
|---|---|---|
| **실패는 200 + `failure`** | `usePreviewRender` 는 `job.status === '실패'` 를 보고 갈린다. 비-200 은 만료(404/410)·415·503 세 갈래로만 쓴다 | ✅ 「status=실패 면 서버가 준 정본 문구를 그대로 말한다」 |
| **`stage` 는 `그리는 중` 일 때만** | 세 문구 그대로(`파일 읽는 중` → `지도 그리는 중` → `범례 만드는 중`), `완료` 후 `render-stage` 노드가 **사라진다** | ✅ 시험이 세 단계를 한 걸음씩 풀어 전부 화면에서 본 뒤 `로딩 중` 부재·단계 노드 부재를 단언 |
| **팔레트를 하드코딩하지 않는다** | 후보 목록을 **만들지 않았다.** `option` 0개 · 화면 전체에 팔레트 키 문자열 부재를 시험이 단언 | ✅ 2건 — **다만 `§7-②`(중계 부재)** |
| **`tileUrlTemplate` 은 그대로** | 치환은 `{z}`·`{x}`·`{y}` **셋뿐**. 파싱·재조립·캐시 키 없음. 화면이 원본 문자열을 `data-tile-template` 로 들고 있다 | ✅ 2건 (서명 질의부 `?exp=…&sig=…` 보존 단언 포함) |
| **만료된 렌더의 타일은 401** | `probeTile` 이 401/403/410 을 `expired` 로 접고 화면은 **만료 문구**를 낸다. 시험이 `권한|인증|로그인` 이 **안 나오는 것**까지 단언 | ✅ |
| **`partialFailure` 는 실패가 아니다** | `완료` 상태 안에 담기고 `render-failure` 자리에 **서지 않는다**. 지도는 그대로 그려진다 | ✅ |
| **415 ≠ 등록 불가** | 서버 문구 + `details.renderableFormats` 를 `·` 로 이어 붙이고, `등록·계보 확정·다운로드는 그대로 할 수 있어요.` 를 함께 낸다. `연구실에 등록 →` 이 살아 있는 것을 단언 | ✅ |

**문구를 화면이 짓지 않는다** — 실패 3종·415 의 사용자 문구는 전부 **서버가 내려 준 것을 그대로**
쓴다(`services/viz-render/.../failures.py:27-36` 이 정본 문구를 담고 있다). 화면이 만든 한국어는
**정본에 있는 문장**(휘발 고지·빈 자리 안내·만료)과 아래 셋뿐이다:
`이 화면으로 이어진 미리보기가 없어요. 업로드에서 다시 열어 주세요.` ·
`고를 수 있는 팔레트 목록을 아직 불러올 수 없어요.` · `등록·계보 확정·다운로드는 그대로 할 수 있어요.`
— **셋 다 `[정본 무근거]` 로 `§8` 에 올린다.**

## 6. 기본정보 — **뺀 자리와 그 이유** (지시가 따로 요구한 항목)

정본 `:225` 가 이름을 부른 여섯 칸 중 화면에 **선 것은 둘**이다.

| 칸 | 섰나 | 값의 출처 · 못 서면 왜 |
|---|:--:|---|
| 크기 | ✅ | `UploadFileRef.byteSize` (`fe-core.ts:1086-1091`) |
| 변수 | ✅ | **완료된 렌더의 `legend.variable`**(`fe-core.ts:1808-1815` — 「실제로 그린 값의 이름」) |
| 포맷 | ❌ 자리째 뺌 | 동결 `fe-core.yaml` 이 **미등록 업로드에 대해 내려 주지 않는다** |
| 좌표계 | ❌ 자리째 뺌 | 〃 |
| 기간 | ❌ 자리째 뺌 | 〃 |
| 격자 | ❌ 자리째 뺌 | 〃 |

**증거** — `UploadStatus`(`frontend/src/generated/fe-core.ts:1105-1124`, `cat -n` 확인)가 가진 필드는
`uploadId · files · ready · renderable · metadataComplete · expiresAt · failure` 뿐이고, `UploadFileRef`
(`:1086-1091`)는 `fileId · fileName · kind · byteSize` 뿐이다. **헤더 다섯 값을 담는 필드가 없다.**
같은 다섯 값을 담는 `DatasetBasicInfo`(`:1244-1250` — 「기본 정보 **아홉 칸** — 구성 · 좌표계 · 기간 ·
격자 · 포맷 …」)는 **등록된 데이터셋의 `getDataset` 응답에만** 달려 있다.

**해석(INTERPRETATION)** — 정본이 「자리째 뺀다」고 쓴 이유는 **「헤더에서 못 읽은 경우」**이고,
지금 뺀 이유는 **「계약이 안 실어 주는 경우」**다. **두 이유는 다르다.** 화면의 겉모습은 정본 요구와
같지만(빈 칸도 대시도 없다) **원인이 다르므로 충족이라고 단정하지 않는다.** 구조는 열어 뒀다 —
`PreviewBasicInfo` 의 여섯 칸이 전부 선택 항목이라, 계약이 값을 실어 주는 날 **화면 코드를 고치지
않고** 자리가 선다. 판정은 `§7-①`.

## 7. 메인 세션에 올리는 것 — 레인이 닫을 수 없는 것

### ① ⚠ 정본 §8.1 「기본정보」가 **계약으로 도달 불가**다 — 반쪽만 섰다

**사실** — 위 `§6`. **왜 레인이 못 닫나** — `contracts/` 는 동결이고(`CLAUDE.md §4`) 계약을 고치는 것은
멈추고 보고할 자리다. **선택지 셋** ㈎ `UploadStatus` 에 헤더 다섯 값을 더한다(계약 개정 · 값의 출처는
`file.metadata.detected` 이벤트) ㈏ S-04 가 그 값을 **화면 상태로** 들고 있다가 S-08 로 넘긴다(계약 무수정.
단 **새로고침하면 사라진다** — 이어짐이 다시 메모리에 의존한다) ㈐ 이 회차는 두 칸으로 닫고
`§8.1` 기본정보를 **부분 충족**으로 기록한다. **레인이 관례로 정할 자리가 아니다.**

### ② ⚠ `listPalettes` FE 중계 부재가 **실제로 화면을 막는다**

**사실** — `/palettes` 는 `contracts/seams/core-viz.yaml:169`(내부 seam)에만 있고, 동결
`fe-core.yaml`·생성물 `fe-core.ts` 에 `palettes` **문자열이 0건**이다(grep 실측). 한편
`core-api` 의 중계는 모르는 팔레트를 **400 으로 되돌린다**(`services/core-api/src/colab_core/app/
routes/preview.py:61-63`) 그리고 viz 도 그렇다(`.../routes/renders.py:98` 부근).
**결과** — 화면은 팔레트 **후보를 알 방법이 없다.**
**레인이 한 것** — 이름을 지어내지 않았다. 다시 그릴 때는 **완료된 렌더가 실제로 쓴
`legend.palette` 키를 그대로 되쓴다.** 그래서 **구간 수는 완전히 동작하고, 팔레트는 고를 수 없다.**
고르는 자리는 `고를 수 있는 팔레트 목록을 아직 불러올 수 없어요.` 로 **왜 못 고르는지 밝힌 채** 비었다.
**닫으려면 `fe-core` 에 중계 op 이 필요하다 — 계약 개정이라 메인 판단이다.**

### ③ S-04 → S-08 이어짐의 **반대편이 아직 없다**

`P2-fe-upload` 가 이 짐을 실어 줘야 이어짐이 완성된다. 레인 경계를 지키느라 그쪽 파일을 열지
않았으므로 **W5 결합 시험이 이 한 자리를 반드시 본다.** 넘겨야 할 것:
`previewNavigation(handoff)` (`components/preview/handoff.ts`) — `to` 와 `state` 를 함께 돌려준다.
짐은 `{ uploadId, renderId, withoutReferenceGrid, basicInfo, files }`.
**⚠ 형제 레인이 `frontend/src/components/upload/previewSource.ts` 를 따로 만들어 두었다**(실측).
**두 레인이 같은 중계 2 op 을 각자 부르는 표면이 둘**이 됐다 — 갈라질 자리라 **W5 에서 하나로
모을지 판단이 필요하다.** 그쪽은 내 소유가 아니라 열지 않았고, 내용도 대조하지 않았다 — **[미측정]**.

### ④ 「401 을 만료로 읽는다」를 **W3 지시가 아니라 규약으로** 남길지

`P2-viz-report` 부록 `A-4`-⑦ 이 물은 자리다. 이 레인은 **만료로 읽었고 시험으로 못박았다.**
다만 그 판단이 **FE 두 레인의 공통 규약**이어야 하는지는 메인 판단이다.

### ⑤ `planning-freshness` 가 이 워크트리에서 red 다 — **내 변경 때문이 아니다**

```
::error::planning-freshness red — 1건
  - 정본 폴더가 없다 (위치 확인 — planning/README.md §1): …/.claude/worktrees/40 COLAB-기획/…
```
**원인은 워크트리 상대경로에서 정본 폴더(형제 폴더)를 못 찾는 것**이고, `P2-viz-report §9` 가 같은
사실을 이미 적었다. 나는 정본·패키지 **어느 파일도 고치지 않았다.** 본 체크아웃에서의 판정은
메인 세션 자리다.

## 8. `[정본 무근거]` — 지어내지 않고 표시한 것

| # | 무엇 | 정본이 말한 데까지 | 이 레인이 한 것 |
|---|---|---|---|
| **F-1** | **S-08 의 URL** `/datasets/preview/:uploadId` | 정본은 **탭 귀속이 `데이터셋`**(`:223`)이라고만 한다. 주소를 주지 않는다 | `nav.ts:9` 의 선례(「URL 경로는 정본에 없다 — 이 레포의 결정」)를 따라 `/datasets` 아래에 뒀다. **`ownerTabOf` 가 이미 S-08 을 이름으로 예상하고 있었다**(`nav.ts:36`) |
| **F-2** | **`renderId` 를 주소 질의로 싣는다** | 정본은 「그대로 이어서 보여준다」까지 | 메모리에만 두면 **새로고침 한 번에 이어짐이 끊긴다.** 주소에 실어 구조로 만들었다. 헤더 값은 주소에 안 싣는다 |
| **F-3** | **이어받은 미리보기가 없을 때의 문구** | 정본에 그 경우가 없다 (§8.1 미리보기 = 「항상」) | `이 화면으로 이어진 미리보기가 없어요. 업로드에서 다시 열어 주세요.` — **가짜 미리보기를 만들지 않기 위한 자리**다 |
| **F-4** | **팔레트 자리의 안내 문구** | 정본에 팔레트 이름도, 못 고를 때의 문구도 없다 | `고를 수 있는 팔레트 목록을 아직 불러올 수 없어요.` (`§7-②`) |
| **F-5** | **415 뒤에 붙인 한 줄** | 정본 §9 의 복구 방법 칸이 「등록·계보 확정·다운로드 전부」다 — **사용자 문구가 아니라 표의 칸이다** | 그 칸을 문장으로 옮겼다: `등록·계보 확정·다운로드는 그대로 할 수 있어요.` 정본 문장이 아니라 **레포 문장**이다 |
| **F-6** | **타일 찔러보기를 `z=0,x=0,y=0` 한 장으로 한다** | 정본·계약 어디에도 없다 | 만료(401)를 **화면이 그림을 보여 주기 전에** 잡기 위한 최소 확인. 네트워크 실패는 만료로 단정하지 않는다 |
| **F-7** | **폴링 간격 1000ms** | 없음 | 레포 결정. 시험은 주입값으로 돌린다 — **코드에 숫자가 박혀 판정을 좌우하지 않는다** |
| **승계** | 만료 문구 · 실패 3종 문구 · 415 문구 | **정본이 준 문장** | 화면이 다시 쓰지 않고 정본/서버 문자열을 그대로 낸다 |

## 9. 안 한 것 — 명시적으로

**범위 밖이라 안 했다**
- **S-04 업로드 모달** — `P2-fe-upload` 소유. `components/upload/`·`shell/Gnb.tsx` 를 **열지 않았다.**
- **③ 계보 확정 UI** — `P2-fe-lineage`(W4). S-08 의 계보 자리는 정본대로 **빈 자리**다.
- **진짜 슬리피 지도 위젯** — 팬·줌·층 겹치기·불투명도·시각 선택은 **계약에 없다**(`P2-viz-report §9`
  가 같은 이유로 안 했다). 타일 한 장 + 범례까지다.
- **`getUploadStatus` 폴링** — S-08 도착 시점에 업로드는 이미 `ready` 다(그래야 S-04 가 미리보기를
  그렸다). 이 화면에서 상태를 다시 도는 것은 **새 사실을 만들지 않으면서 호출만 늘리는 일**이라 뺐다.
- **FE 픽스처 드리프트**(`components/{catalog,detail}/fixture.ts`) — `P2-EXEC §3` 명시 예외. **안 만졌다.**

**의도적으로 다르게 했다**
- **픽스처 폴백을 두지 않았다.** 카탈로그·상세(`detailSource.ts:32-40`)는 501 이면 픽스처로 그리는데,
  미리보기는 그러면 안 된다 — **사람이 그 그림을 보고 등록을 판단한다.** 그릴 수 없으면 그릴 수
  없다고 말하는 것이 §9 가 요구한 동작이다.

**못 했다**
- **staging·브라우저 실물 확인** — 레인은 staging 을 건드리지 않는다(`P2-EXEC §7`). `P2-EXEC §6`
  이 요구하는 「사람이 `www.colab-hydro.com` 에서 눈으로 S-08 을 본다」는 **W5 자리**다.
  이 보고의 green 은 **jsdom 시험까지**이고 실배포 확인이 아니다.
- **`selftest` 전량** — docker 의존 셋(`db-selftest`·`rls-effect-selftest`·`contract-selftest`)은 DB·docker
  레인 자리라 돌리지 않았다. **돌린 것만 `§10` 에 적는다.**

## 10. 게이트 — 종료 시점 (증거, 출력 그대로)

```
generated-up-to-date green — 등기부 1건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.
generated-selftest green — 9 케이스 전부 기대대로 (green 1 · red 8).
contract-lint green — seam 3건, 룰 위반 0.
contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.
event-lint green — 스키마 2건 컴파일 · valid 5건 통과 · invalid 8건 거부.
event-breaking green — 기준 HEAD (2건) 대비 파괴적 변경 없음.
event-selftest green — event-lint · event-breaking 이 틀린 것을 틀렸다고 말한다 (fail-closed 증명).
seam-consistency green — G-e 258건 · G-b 7건 · ㉠ 0건 · ㉡ 15건.
seam-consistency-selftest green — 13 케이스 전부 기대대로 (green 4 · red 9).
import-boundary green — 계약 전부 통과.
banned-import green — .py 90건, 금지 import 0.
ai-no-lineage-write green — 계약·코드·체인 세 층 모두에서 쓰기 경로가 없다.
boundary-selftest green — 경계 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).
```

**red 1건 —** `planning-freshness`(사유는 `§7-⑤`. 워크트리 경로 · 내 변경 아님).

**시험** (출력 그대로)

```
 Test Files  1 passed (1)
      Tests  23 passed (23)
```

전체 스위트는 `Test Files 1 failed | 6 passed (7)` / `Tests 51 failed | 97 passed (148)` 인데,
**실패 51건은 전부 `test/upload.test.tsx`** — 형제 레인 `P2-fe-upload` 가 **지금 작성 중인 파일**이고
`openModal` 이 아직 없는 모달을 기다려 죽는다. 내 라우트 한 줄과 무관하다(`shell.test.tsx` 포함
나머지 6파일 green). **[미측정]** — 그쪽 실패 원인을 내가 고쳐 확인하지는 않았다(남의 디렉터리).

## 11. 재현

```bash
cd frontend && npx vitest run test/preview.test.tsx    # 23 passed
cd frontend && npx tsc --noEmit                        # 내 파일 오류 0
./gates/run.sh generated-up-to-date                    # green
```
