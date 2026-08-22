# WU-D2 세션 기록 — seam 2종: `core-ai.yaml` · `core-viz.yaml`

> **범위** `contracts/seams/core-ai.yaml` · `contracts/seams/core-viz.yaml` 두 파일. 다른 seam·`schemas/`·`events/`·게이트는 이 조각에 없다.
> **근거 규칙** `CLAUDE.md §3-2`(D10→D4 쓰기 경로 부재) · `§3-4`(core-api geo 금지) · `§3-5`(연구실 경계) · `§3-6`(정규 타입은 common.json) · `§3 AI 응답 규격` · `contracts/README.md`(AI seam이 담아야 하는 것).
> **정본 근거** `PRD·Policy_데이터_찾기`(E-02) · `PRD·Policy_업로드와_계보_확정`(E-04) · `Policy_데이터셋_상세`(E-03).
> **검증** `yaml.safe_load` green · `npx @redocly/cli@1 lint` → 두 파일 모두 `Woohoo! Your API descriptions are valid` · `bundle` 로 `../schemas/common.json` 참조 전건 해석 확인 · **레포 룰셋 `contracts/.spectral.yaml`(같은 WU 의 게이트 조각) 으로 재검증 → 두 파일 모두 error 0** (잔여 경고는 `info-contact` 1건씩이며 `fe-core.yaml` 도 동일하다).

---

## 1. 공통 규약 (두 파일에 동일 적용)

| 항목 | 값 | 비고 |
|---|---|---|
| OpenAPI | `3.1.0` · `info.version: 0.1.0` | |
| 필드 표기 | **속성 이름 lowerCamelCase**, enum 값은 정본 한국어 표기 | 작업 착수 시점엔 `fe-core.yaml` 이 없어 `common.json` 의 확정 표기(`labId`·`labName`·`searchedCount`·`totalCount`·`nextCursor`)를 이어 정했다. 세션 중 나란히 작성된 `fe-core.yaml` 과 **대조 결과 동일**(경로 소문자 kebab-case · 속성 camelCase · enum 값은 common.json 에서만) — 세 seam 이 한 관례를 쓴다 |
| 경로 | 소문자 복수형 명사 (`/lineage-suggestions`·`/searches`·`/renders`·`/palettes`·`/screenshots`) | 한국어를 경로에 싣지 않는다(퍼센트 인코딩 회피) |
| operationId | lowerCamelCase 동사구. 전 오퍼레이션 필수 | |
| 오류 | 모든 4xx/5xx = `ErrorEnvelope` | `$ref` 로만 참조 |
| 목록 | `ListEnvelope` | `core-ai` 검색 결과 · `core-viz` 팔레트 목록 |
| 공통 타입 | 전부 `$ref: "../schemas/common.json#/$defs/..."` | enum·ID 인라인 재정의 0건 |
| 인증 | `serviceToken`(http bearer) 루트 `security` | **정본에 항목 없음 — 레포 결정.** 배포 단위 사이의 서비스 자격 증명이지 사람 세션이 아니다. redocly `security-defined` 가 요구하기도 하지만, 없으면 "누가 이 표면을 부를 수 있나"가 계약에 안 적힌다 |

참조한 common 정의 — core-ai: `Ulid`·`Timestamp`·`ErrorEnvelope`·`ListEnvelope`·`Cursor`·`FileKind`·`ParentRole`·`AiConfidence`·`AiRationale`·`AiSearchScope` (10종) / core-viz: `Ulid`·`Timestamp`·`ErrorEnvelope`·`ListEnvelope` (4종).

---

## 2. `core-ai.yaml` — 오퍼레이션 2개

정본이 AI 를 얹은 지점이 둘뿐이므로(`DOMAINS §2 D10`) 오퍼레이션도 둘이다.

| operationId | 경로 | 무엇을 | 정본 근거 |
|---|---|---|---|
| `suggestLineage` | `POST /lineage-suggestions` | 업로드 파일 메타 + KG 조회 → 가공 전 데이터 후보 · 가공 방식 제안 | `Policy_업로드와_계보_확정 §2·§3.1·§8`(제안 카드 확신도/행동) · `PRD §5.1` |
| `searchDatasets` | `POST /searches` | 자연어 질의 해석 → 데이터셋 식별자 + 관련도 + 근거 한 줄 | `Policy_데이터_찾기 §1.3·§5·§8` · `PRD §7`(자연어 검색 엔진 의존) |

`POST` 인 이유는 본문이 필요해서다(파일 메타 / 1~200자 질의). **둘 다 읽기 의미론이고 ai-service 쪽에 아무것도 기록되지 않는다.**

### 2.1 AI 응답 규격을 타입으로 어떻게 강제했나

| 정본 규칙 | 타입 강제 |
|---|---|
| 확신도는 `확실 / 애매 / 모름` enum, 숫자·퍼센트 없음 | `AiSuggestionBase.confidence` = `$ref AiConfidence`, `required`. **숫자형 확신도 필드를 한 개도 만들지 않았다.** `SearchHit.relevanceBar` 는 확신도가 아님을 스키마 description 에 명시 |
| 근거 필수, nullable 아님 | `AiSuggestionBase.rationale`·`SearchHit.rationale` = `$ref AiRationale`, 둘 다 `required`. `AiRationale` 자체가 `minLength 1` + 줄바꿈 금지라 빈 문자열·여러 줄이 스키마에서 걸린다 |
| 한계도 근거 한 줄 안에서 | **한계 전용 필드를 만들지 않았다.** 만들면 "좋은 점만 적는 근거 필드"가 따로 생긴다 (`Policy_데이터_찾기 §4 한계 표시`) |
| [모두 승인] 없음 | 배치 엔드포인트 없음. 제안 묶음에 상태·승인 필드 없음. `approve`/`confirm` 어휘가 스펙 전체에 0회 |
| 정직한 빈 상태 | `suggestions`·`results.items` 빈 배열이 **200**. 0건 전용 오류 코드를 만들지 않았다. 계보 제안의 빈 상태는 `rawDataLikely` 가 함께 말한다(`§3.2 원자료로 보인다`) |
| 뒤진 범위를 먼저 밝힌다 | `scope` = `$ref AiSearchScope`, **두 응답 모두 `required`**. 0건이어도 반드시 실린다 |
| 질의가 데이터 찾기가 아님 | 오류가 아니라 `isDataQuery: false` + 빈 결과 (`Policy_데이터_찾기 §9`) |
| AI 장애가 제품을 멈추면 안 됨 | `Degradable` 을 두 응답에 `allOf` 로 섞었다 — `degraded: boolean` **required**. 5xx 로만 실패를 표현하지 않는다 (`contracts/README.md` · `PLAN-SoT §3.1`) |

### 2.2 D10 → D4 쓰기 경로 부재를 무엇으로 보장했나

관례가 아니라 **없는 것으로** 보장한다. 넷이 겹친다.

1. **커밋 오퍼레이션이 스펙에 없다.** `paths` 는 두 개뿐이고 둘 다 제안 생산이다. 계보를 저장·확정·승인하는 경로가 존재하지 않으므로 ai-service 클라이언트를 생성해도 확정 함수가 나오지 않는다 — 코드에서 부를 수 있는 것 자체가 없다.
2. **`suggestionId` 의 의미를 스키마에 못 박았다.** "한 응답 안에서 항목을 구분하는 값일 뿐이고 저장된 계보 관계의 ID 가 아니다." 이 ID 로 무언가를 확정하는 오퍼레이션이 없다는 문장을 같은 자리에 붙였다.
3. **파생값을 AI 가 내보내지 않는다.** `ProcessingLevel`(Lv)·`LineageState` 를 응답 어디에도 두지 않았다. `rawDataLikely` 는 boolean 이고 Lv 숫자가 아니다 — Lv 는 확정된 계보에서 core 가 계산한다 (`PLAN-SoT §9-⑳`).
4. **파일 상단 주석이 다음 사람을 향해 명시한다.** "제안은 D10 안에서 태어나 D10 안에서 죽는다. `POST /lineage`·`PUT /suggestions/{id}/confirm` 류를 편의상 추가하면 규칙이 관례로 내려앉는다. 필요해 보이면 추가하지 말고 멈추고 보고한다(`CLAUDE.md §4`)."

값 집합 쪽 보증은 이미 `common.json#LineageOrigin` 에 있다 — 집합에 `제안` 이 없어 제안 상태로 저장될 자리 자체가 없다.

### 2.3 판단 — 연구실 경계는 호출자가 명시적으로 넘긴다

`CLAUDE.md §3-5` 의 "서버 주입"은 **core-api 안의 스코프 커널 + RLS** 를 말한다. ai-service 는 별도 배포 단위(`DOMAINS §4`)라 플랫폼 DB 세션이 없고 그 커널의 사정권 밖이다. 셋 중 골랐다.

- ~~AI 가 토큰에서 추론~~ → 경계가 두 곳(core 커널 · AI 휴리스틱)에서 정해져 갈라진다. v1 이 당한 드리프트와 같은 형태다.
- ~~AI 가 플랫폼 DB 를 직접 읽어 경계 확인~~ → `CLAUDE.md §3-1`(타 도메인 테이블 직접 접근 금지) 위반.
- **채택: 요청 본문의 `scope{labId, labName}` 로 명시 전달 + 응답의 `AiSearchScope` 로 되돌려 받기.** 경계는 core 가 정하고 AI 는 받아 쓰며, 응답이 보낸 값과 다르면 core 가 응답을 버린다(fail-closed). 검증 지점이 core 한 곳에 남는다.

`labName` 까지 넘기는 이유 — 응답의 `AiSearchScope.labName` 은 화면 범위 표시줄("우리 연구실(수자원순환연구실) 안에서만 찾았어요")에 그대로 서는 값이다. AI 가 이름을 지어내면 D1 정본값과 갈라진다.

### 2.4 판단 — 관련도(`relevanceBar`)

정본은 관련도를 **막대 하나로만** 표시하고 퍼센트·등급 텍스트를 금한다(`Policy_데이터_찾기 §4`). 그런데 막대는 길이를 필요로 한다. `0~1` 수치 `relevanceBar` 를 두되 이름·description 으로 **렌더 강도값**임을 못 박고, "확신도와 다른 개념이며 사용자에게 숫자로 보이는 순간 정본 위반"을 스키마에 적었다. 확신도(`AiConfidence`)에는 여전히 숫자가 한 개도 없다.

### 2.5 판단 — AI 는 카탈로그 값을 다시 말하지 않는다

`SearchHit` 은 `datasetId` · `relevanceBar` · `rationale` 셋뿐이다(`additionalProperties: false`). 카드의 나머지(이름·포맷·Lv·요약·기간·소유·Verified·잠김)는 core 가 D3·D2 에서 붙인다. 두 곳에서 말하면 갈라지고, Verified·잠김은 D2 의 정책값이라 AI 에 얹으면 AI 가 권한을 판단하게 된다.

따라서 **`Verified 우선 정렬`도 core 가 다시 세운다** — AI 가 돌려주는 순서는 관련도 순뿐이다(`Policy_데이터_찾기 §5 기본 정렬`). **잠긴 데이터를 결과에서 빼는 로직도 AI 에 없다**(`§1.3-6` — 사라지지 않는다). AI 는 잠김을 모른 채 관련도만 말한다.

---

## 3. `core-viz.yaml` — 오퍼레이션 5개

| operationId | 경로 | 무엇을 | 정본 근거 |
|---|---|---|---|
| `createRender` | `POST /renders` | 층 하나의 렌더 작업 생성 | `Policy_데이터셋_상세 §8 지도 표현·시각화 컨트롤` · `Policy_업로드와_계보_확정 §8 미리보기 그리기` |
| `getRender` | `GET /renders/{renderId}` | 진행 단계·결과·실패·부분 실패 조회 | `Policy_데이터셋_상세 §8`(단계로 말한다) |
| `getRenderTile` | `GET /renders/{renderId}/tiles/{z}/{x}/{y}.png` | 타일 서빙 | `PLAN-SoT §7·§8.3`(COG 바이트 범위 타일 서버 + CDN) |
| `listPalettes` | `GET /palettes` | 색상 — 쓸 수 있는 팔레트 목록 | `Policy_데이터셋_상세 §8`(팔레트 3종 — 이름 미열거) |
| `createScreenshot` | `POST /screenshots` | 지금 장면을 PNG 로 | `Policy_데이터셋_상세 §8 스크린샷` |

간격(구간 수)은 별도 오퍼레이션이 아니라 `RenderStyle.classCount`(3~9, 기본 6, `§5`)로 들어간다.

### 3.1 geo 경계를 계약이 어떻게 반영하나 (`CLAUDE.md §3-4`)

이 seam 이 존재하는 이유가 그 규칙이므로, **core 가 좌표·래스터를 해석해야만 채울 수 있는 필드를 요청에서 전부 뺐다.**

- 요청에 좌표계·투영·격자 구조·픽셀·밴드·NoData·리샘플 파라미터가 **없다.** 넘기는 것은 식별자(`datasetId`/`uploadId`/`fileIds`)와 렌더 파라미터(`variable`·`instant`·`paletteId`·`classCount`)뿐이다.
- **지도 표현(격자·경계·점)을 요청에 넣지 않았다.** "무엇으로 그릴지는 사람이 고르지 않는다 — 포맷이 정한다"(`§8 지도 표현`, 목업의 전환 버튼은 데모 장치)가 정본 규칙인데, 요청 필드로 두면 core 나 FE 가 포맷을 해석하게 된다. 판정은 viz-render 안에서 끝난다.
- **`Bounds` 는 WGS84 경위도 고정**이라 요청·응답 어디에도 좌표계 인자가 없다. 원본 좌표계는 viz-render 밖으로 나오지 않는다.
- **래스터 바이트가 core 를 지나가지 않는다.** 결과는 `tileUrlTemplate` + `Legend` 뿐이고, 타일은 지도 위젯이 CDN 을 통해 직접 부른다. 스크린샷만 이미지 바이트를 돌려주는데 이것도 완성 PNG 다.
- 스펙에 파일 바이트를 올리는 경로가 없다 — 파싱은 D5 의 일이다.

주석에 판별 기준을 남겼다: **"요청에 좌표·격자 해석값이 필요해지면 그건 core 가 파일을 해석하고 있다는 뜻이다 — 멈추고 보고한다."**

### 3.2 판단 — 렌더를 동기 응답이 아니라 작업(job)으로

정본이 "미리보기는 서버가 그린다 · 수 초~수십 초 · 진행을 단계로 말한다(`파일 읽는 중 → 지도 그리는 중 → 범례 만드는 중`)"를 명시했다. 동기 응답이면 단계를 말할 자리가 없다. `202` + `RenderJob` 폴링으로 두고, `RenderStage` enum 값은 **정본 문구를 글자 그대로** 썼다.

### 3.3 판단 — 작업 하나 = 층 하나 (겹쳐 보기)

정본은 층마다 **시각과 팔레트를 따로** 고르라고 한다(`§8 층의 시각·층 색상` — 하나로 묶으면 없는 시각을 있는 것처럼 그린다). 그래서 합성 파라미터를 한 요청에 묶지 않고 층당 작업 하나로 뒀다. 켜기/끄기·불투명도는 지도 위젯이 하는 일이라 계약에 없다. **예외는 스크린샷** — 합성이 필요해 장면(층 순서·불투명도·뷰포트)을 통째로 받는다.

### 3.4 판단 — 실패의 모양

| 정본 상황 | 계약 표현 |
|---|---|
| 그릴 수 없는 형식 | `415` + `details.renderableFormats`(그릴 수 있는 형식을 함께 적는다 — 안 되는 것만 말하면 무엇을 올려야 하는지 모른 채 떠난다) |
| 파일이 너무 큼 | `413` (조각 하나 고르기로 복구) |
| 서버 연결 불가 · 시간 초과 · 알 수 없는 오류 | `RenderJob.status = 실패` + `failure`(= `ErrorEnvelope`) 의 `code` 로 구분 |
| **조각 일부를 못 읽음** | `status` 는 **`완료`로 남고** `partialFailure{totalParts, renderedParts, missingParts[]}`. 부분 실패는 전부 실패와 다르게 다룬다 — 읽힌 조각으로 그리고, 못 읽은 조각을 이름·시각으로 밝힌다 |
| 기준 격자 파일 없음 | 오류가 아니라 요청 옵션 `withoutReferenceGrid: true`(짝 파일 없이 그려 보기). 미리 막으면 그릴 수 있는 것까지 못 그린다 |
| 렌더 수명 만료 | 타일 `410` + `RenderJob.expiresAt`. 등록 전 업로드의 미리보기는 임시로만 둔다 |

빈 타일(값 없음)은 `200` + 투명 PNG 다. `404` 로 두면 지도 위젯이 재시도를 반복한다.

### 3.5 판단 — 팔레트 이름을 계약에 박지 않았다 · `palette` 는 ID 가 아니다

정본은 "팔레트 3종"이라고만 하고 이름을 열거하지 않는다. enum 을 만들면 **정본에 없는 어휘를 우리가 발명**하는 것이라(`D2.md §1` 이 같은 이유로 영문 코드값을 거부했다) `GET /palettes` 로 서빙하고 `palette` 를 불투명 문자열로 뒀다. core·FE 는 하드코딩하지 않는다.

필드 이름을 `paletteId` 가 아니라 **`palette`** 로 쓴 이유 — 레포 룰셋이 `*Id` 로 끝나는 필드에 `common.json#/$defs/Ulid` 참조를 강제한다(`CLAUDE.md §3-6`). 팔레트 키는 ULID 가 아니라 viz-render 가 소유한 스타일 키다. 룰을 피하려 예외를 뚫는 대신 **`Id` 어휘를 쓰지 않는 쪽**을 골랐다 — `Id` 로 끝나는 모든 필드가 정규 ID 라는 성질을 깨지 않는다.

---

## 4. 뺀 것 — 정본에 근거가 없거나 경계 밖

| # | 뺀 것 | 왜 | 어디서 닫히나 |
|---|---|---|---|
| 1 | **계보 확정(커밋) 오퍼레이션** | `CLAUDE.md §3-2`. 확정은 사람이 core → D4 로 한다 | `fe-core` · D4 구현 WU |
| 2 | **배치 승인 / 제안 일괄 상태** | 정본이 [모두 승인]을 명시적으로 뺐다 | 영구히 없음 |
| 3 | **제안 수락·거절 피드백 기록 엔드포인트** | 평가셋·실행 원장은 D10 내부이고 정본에 화면·요구가 없다. seam 에 두면 "제안의 뒷일"이 경계를 넘는 것처럼 보인다 | D10 구현 WU(내부) |
| 4 | **가공 방식 어휘 enum** | 정본에 열거값이 없다. HYD 협의 사항 (`DOMAINS §3-③` · `PLAN-SoT §9-㉚`). `methodText` 자유 문자열 1~120자(`Policy §5`)로만 뒀다 | HYD 협의 → 별도 WU |
| 5 | **검색 정렬·필터 파라미터** | 검색 정렬은 고정이고 사용자가 고르지 않는다. `Verified만 보기`는 core 가 D2 값으로 거른다 | core-api |
| 6 | **AI 검색의 잠김·Verified 인지** | D2 정책값을 AI 에 얹지 않는다 | core-api |
| 7 | **`ProcessingLevel`·`LineageState` 응답 필드** | 파생값이고 core 가 계산한다 (`PLAN-SoT §9-⑳`) | core-api |
| 8 | **검색 기록·추천 질문** | `Policy_데이터_찾기 §11` 미정 | 기획 |
| 9 | **지도 표현 선택(격자/경계/점) 파라미터** | 포맷이 정한다. 목업 전환 버튼은 데모 장치 | 영구히 없음 |
| 10 | **시각화 설정 저장 오퍼레이션** | 정본이 "저장하지 않는다 · 스크린샷으로 대신한다"로 닫았다 | 영구히 없음 |
| 11 | **렌더 작업 취소·삭제** | 정본에 취소 화면이 없다. 수명은 `expiresAt` 으로 서버가 관리 | — |
| 12 | **`AiRationale` 길이 상한** | "한 줄"만 있고 글자 수가 정본에 없다 (`D2.md §3-3`). 줄바꿈 금지까지만 | 화면 실측 후(P4) |
| 13 | **다중 연구실 소속** | `PERMISSION-PRINCIPLES §10-⑤` 미정. `scope` 는 단일 `labId` | P1 |
| 14 | **AI 모델·프롬프트 선택 파라미터** | D10 내부 판단이고 정본에 없다. 호출자가 모델을 고르게 하면 실험 주기가 core 배포에 묶인다 | D10 내부 |

---

## 5. 다음 조각의 진입조건

- 세 seam(`fe-core`·`core-ai`·`core-viz`)이 같은 표기 관례를 쓴다 — 경로 kebab-case / 속성 camelCase / 한국어 enum 값 / `ErrorEnvelope`·`ListEnvelope` 전면 사용 / `$ref` 로만 공통 타입 참조. 어긋나면 이 문서와 `.spectral.yaml` 을 근거로 잡는다.
- **계약 게이트에 아직 없는 규칙 2가지** (`.spectral.yaml` 이 ①③은 이미 덮는다):
  1. ~~공통 enum·ID 인라인 재선언 금지~~ → `colab-id-must-ref-ulid` 가 ID 를 덮는다. **enum 쪽은 아직 규칙이 없다** — `AiConfidence`·`ParentRole`·`FileKind` 를 seam 안에서 다시 열거해도 지금은 통과한다
  2. `core-ai.yaml` 에 계보 쓰기·확정 오퍼레이션이 생기면 red — `colab-no-batch-approval` 은 배치 승인 경로명만 막고 **단건 확정 경로는 못 막는다.** `§3-2` 음성 테스트의 계약 쪽 짝이 필요하다
  3. ~~숫자형 확신도 필드 금지~~ → `colab-no-numeric-confidence` 가 덮는다. 다만 `rationale` 이 `required` 에서 빠지는 것은 아직 못 잡는다
- `core-viz.yaml` 의 `RenderTarget.uploadId` 는 D5(업로드 임시 저장)의 식별자를 전제한다. D5 계약이 서면 이름을 맞춘다.
- `serviceToken` 의 실제 발급·회전은 WU-I1(토폴로지·시크릿 관리)에서 닫는다. 타일 경로는 CDN 뒤에 서므로 서명된 URL 로 대체될 수 있다.
