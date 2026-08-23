# WU-P1 · 레인 `P1-api` — 레인 보고

> 소유 디렉터리 `services/core-api/src/` · `services/core-api/tests/` **만** 만졌다.
> 커밋하지 않았다 — 커밋과 `03-HANDOFF`·`PLAN-SoT` 갱신은 메인 세션 몫이다 (P1.md §5-④).

## 1. 결론

- **4 op 을 501 표에서 뺐다** — `getDataset` · `listDatasetFacets` · `listLabMembers` · `saveLabMemberPermissions`
- 501 목록 **29 → 25** (`NOT_IMPLEMENTED_P1` 22 → 18 · `NOT_IMPLEMENTED_NO_STORE` 7 유지)
- 실동작 op **5 → 9**. 계약은 **한 글자도 고치지 않았다** (34 op·필드·enum 동결)
- 시험 **109 → 144** (신규 35). 게이트 12종 + `selftest` 전부 green

## 2. 순서 — red 를 눈으로 봤다 (CLAUDE.md §4)

| 단계 | 실측 |
|---|---|
| 착수 전 기준선 | `144 → 109 passed` (구현 전 전량 green) |
| 실패 시험 작성 후 | **`39 failed, 3 passed`** — 통과한 셋은 인증 게이트(`test_requires_a_subject` ×3)뿐이고, 501 핸들러가 이미 인증을 걸고 있어 정당하게 green 이었다 |
| 구현 후 | `144 passed` |

- **red 가 정본을 한 번 고쳤다.** `잠긴 상세에서 올린 사람이 승인 요청을 할 수 있다`고 쓴 시험이 red 였는데,
  `Policy_승인_처리 §8` 적용 지점 표는 **잠긴 상세 = 잠김 안내 + 접근 요청 자리**뿐이라고 못 박는다.
  **코드가 아니라 시험이 틀렸다** — 시험을 정본 쪽으로 고치고, 잠긴 상세에 액션이 하나뿐임을 증명하는
  시험(`test_a_locked_detail_offers_only_the_access_request`)을 새로 얹었다.

## 3. op 별 — 무엇을 어디에 근거해 냈나

### 3.1 `getDataset` (S-05 헤더 + 기본 정보)

| 값 | 근거 | 실측 |
|---|---|---|
| **잠긴 데이터도 200** | `Policy_승인_처리 §8` · P-13 | 403 을 쓰면 접근 요청 흐름이 죽는다 |
| **잠기면 `basicInfo` 통째 null** | 정본 S-05 §7 · P1.md §2-④ | `projects` 도 함께 null. 카탈로그가 잠긴 행에 `조각 N` 을 띄우는 것과 달라 보이는 것은 **의도** |
| **묘비 = 404** | `Policy_데이터셋_상세 §7` | 경계 밖 404 와 **같은 404** 로 낸다 — 구분해 주면 그 자체가 존재의 누설이다 |
| `기본 정보` 아홉 칸 | §5 | 구성·좌표계·기간·격자·포맷·파일·원천 표기·소유자·올린 사람. 열 번째를 만들지 않았다 |
| `파일` 칸 | §5 | 조각 수 + 용량 합계 + 기준 격자 파일 유무. **조각을 나열하지 않는다** |
| **조각 수의 출처** | `PLAN-SoT §9-㊼` | `d3_dataset.file_count` 메타 열. `d3_file` 을 `count(*)` 하지 않는다 |
| 헤더 우측 한 자리 | `Policy_승인_처리 §8` | ① 미승인+올린 사람·소유자 → 요청 ② 검토 대기+교수 → 승인 ③ 승인됨+교수 → 취소 |
| 삭제 | §6 | 소유자 또는 교수 |
| 계보 수정 | §6 | `업로드·편집` 스위치 |

- **`P0` 의 잔재를 하나 고쳤다** — `d3_catalog` 의 목록 질의가 아직 `(SELECT count(*) FROM d3_file …)` 이었다.
  `body_access` RESTRICTIVE 아래서 잠긴 행이 0 을 내는 바로 그 경로다. `d.file_count` 로 바꿨고,
  **그 사실 자체를 시험으로 박았다**(`test_file_count_comes_from_the_meta_column_not_from_counting_rows`) —
  같은 트랜잭션에서 `count(*)` 는 0, 응답의 조각 수는 1 임을 함께 확인한다.

### 3.2 `listDatasetFacets` (열 메뉴의 값별 건수)

- 조건을 걸 수 있는 열은 **다섯**(`주제·Level·업로더·계보·Verified`). 나머지 셋은 정렬만 갖는다 (`Policy_데이터_찾기 §5`)
- **다른 열의 조건을 먼저 적용한 뒤 센다.** 자기 열의 조건은 뺀다 — 자기 조건까지 걸면 고른 값만 남아
  다른 값으로 갈아탈 수가 없다
- **0건인 값을 지우지 않는다.** 계보 4값은 enum 이 고정이라 행에서 뽑지 않고 넷을 늘 내린다
  (한 값이 0건이 되는 순간 그 조건이 화면에서 사라지면 안 된다)

### 3.3 `listLabMembers` · `saveLabMemberPermissions` (권한 값의 원천)

- 스위치는 **정확히 4개**. 다섯 번째 이름이 오면 400
- **교수 행 고정** (P-5) — 네 스위치가 켜진 채로 내려가고 `editablePermissions` 는 **빈 배열**. 교수 행을 고치려 하면 403
- **재위임 금지를 서버가 강제한다** (P-31 · 정본 E-01 §6)
  - 행별 `editablePermissions` — 교수는 4열, `연구실 설정` 위임자는 `업로드·편집`·`프로젝트 생성` **2열**
  - 편집 불가 열도 **값은 보인다** — 열을 지우면 표 구조가 깨지므로 여기서는 `P-12`(숨김)를 적용하지 않는다
  - 위반은 **403**. 그리고 **한 요청에 허용 칸과 금지 칸이 섞이면 통째로 거부**한다 — 절반만 저장하면
    사용자가 방금 확인한 격자와 저장된 격자가 갈라진다
- `연구실 설정` 이 없으면 **읽기도 403** — 고치는 자리는 그 한 곳이다 (P-18 · P-11)
- **스위치 하나 = 이력 한 줄** (P-33). 두 칸이 바뀌면 두 줄. 값 저장과 이력 append 를 **한 트랜잭션**에 묶었다 —
  값만 바뀌고 이력이 없는 상태가 생기면 감사 기록이 「대체로 맞는 기록」이 되고, 그건 기록이 아니다
- 경계 밖·없는 계정은 **404** (P-9·P-10)

## 4. 경계 (CLAUDE.md §3-1)

- cross-domain 은 전부 **Port 경유**. 도메인끼리 직접 import 하지 않는다
- Port 를 **셋 늘렸다** — 기존 `catalog.py` 의 `_compose` 패턴 그대로다
  | Port | 소유 | 쓰임 |
  |---|---|---|
  | `DatasetVerification` + `DatasetAccessPort.verification()` | D2 | 상세의 Verified 기록(승인자·시각·취소자·사유) |
  | `MemberPermissions` | D2 | 격자 표 한 행의 역할 + 스위치 4종 |
  | `ProjectUse` + `ProjectLinkPort.uses_of()` | D6 | 상세의 활용 프로젝트 — 카탈로그의 `대표 1건 + 외 N` 과 형태가 다르다 |
- 조립은 `app` 이 한다. `d1_identity` 는 여전히 위층을 모른다
- `import-boundary` **8 계약 전부 통과**

## 5. 게이트 · 시험 실측

```
$ pytest -q   (COLAB_CORE_TEST_DATABASE_URL = 일회용 p1api_pg 앱 롤)
144 passed in 6.82s

import-boundary          GREEN   Contracts: 8 kept, 0 broken.
banned-import            GREEN
ai-no-lineage-write      GREEN
contract-lint            GREEN
contract-breaking        GREEN
event-lint               GREEN
event-breaking           GREEN
migration-single-head    GREEN
rls-coverage             GREEN
planning-freshness       GREEN
rls-effect               GREEN   본체 음성 · 메타 양성(P-13) · cross-tenant 전수 0행
schema-diff              GREEN   db/platform · db/ai 두 체인 각각 선언 = 적용
selftest                 GREEN   exit 0 — 다섯 셋 전부
  contract-selftest green / event-selftest green / boundary-selftest green
  db-selftest green / rls-effect-selftest green   (139 케이스)
```

- 검증 DB 는 `RESTART.md §2-④` 대로 일회용(`p1api_pg`, `--tmpfs` + `PGDATA` + `postgres:16-alpine`,
  **호스트 포트 미공개**)으로 세웠고 **레인 종료 시 제거**했다
- `schema-diff` 용 적용 DB 는 같은 컨테이너 안에 `applied_platform` · `applied_ai` 를 만들어
  체인별 `alembic upgrade head` 로 올렸다 (platform head = `0002_p1_file_count`)
- 게이트를 **끄거나 검사 대상을 줄인 곳이 없다**

## 6. 정본 무근거 · 판단이 들어간 자리 (메인 세션 확인 요망)

> 아래는 **값을 지어낸 곳이 아니라, 정본이 값을 주지 않아 「지금 참일 수 있는 것」으로 좁힌 곳**이다.

| # | 자리 | 지금 값 | 왜 |
|---|---|---|---|
| ① | `DatasetDetail.accessRequestPending` | **항상 `false`** | 접근 요청의 **저장처가 P0 스키마에 없다**(`createAccessRequest` = `NOT_IMPLEMENTED_NO_STORE`, P6). 저장처가 없으면 참일 수 있는 값이 하나뿐이다. **P6 이 여기를 반드시 되짚어야 한다** |
| ② | `actions.canApproveVerification` | **항상 `false`** | 정본은 `② 검토 대기 + 교수`를 요구하는데 **검토 대기의 저장처가 없다**(P6). 「교수」라는 이유만으로 켜면 없는 대기 건을 승인할 수 있는 것처럼 보인다 |
| ③ | `DatasetDetail.fileName` (묶음 이름) | 잠기면 **null** | 정본 S-05 §8 은 파일명을 헤더 줄로 두지만, **잠긴 상세의 노출 범위 정본은 `Policy_승인_처리 §8`** 이고 거기 목록은 `이름 · 요약 · 헤더 태그`까지다. 파일명이 없어 좁은 쪽을 골랐다 — **[정본 무근거]** |
| ④ | 값별 건수의 `업로더` 값 | **`accountId`** | 계약의 필터가 계정 ID 로 걸리므로 값도 ID 로 맞췄다. 화면에 뿌릴 이름은 목록 응답이 이미 준다. 정본은 값의 형태를 말하지 않는다 — **[정본 무근거]** |
| ⑤ | 구성원 격자의 **행 순서** | **이름 → ID** | 정본이 순서를 주지 않는다. 화면이 매번 다른 순서를 보지 않게 하는 최소 규칙만 뒀다 — **[정본 무근거]** |
| ⑥ | 위임자가 **자기 행**을 고치는 것 | **막지 않는다** | P-31 은 「위임자는 두 열만」까지만 말하고 자기 행을 따로 다루지 않는다. 규칙을 사람마다 갈라 적으면 그 자체가 새 규칙이라 균일하게 뒀다 — **[정본 무근거]** |

## 7. STOP · 넘기는 것

- **계약을 고칠 사유는 없었다.** 34 op·필드·enum 그대로 구현이 닫혔다
- **범위 밖으로 넘긴 것 없음.** 4 op 전부 실동작이며 부분 완료로 닫은 자리가 없다
- 넘기는 것 하나 — `services/core-api/.venv` 에 **`alembic` 을 설치**했다(`schema-diff` 용 적용 DB 를 올리려고).
  `.venv/` 는 `.gitignore` 안이라 레포에는 남지 않지만, CI 가 같은 게이트를 돌리려면 **적용 DB 를 만드는 주체가
  게이트 밖에 필요하다**는 사실은 그대로다 (`D3-db.md §3` 이 이미 그렇게 설계했다)
