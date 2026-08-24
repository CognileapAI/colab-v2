# S1 · W0 — 기준선 실측

> **이 문서는 재는 것만 한다.** 고치지 않았고, 리팩터링하지 않았고, `W1` 을 시작하지 않았다.
> 계획의 근거 = `sessions/S1-PLAN.md §5.3` 「기준선 실측 (생략 금지)」.
>
> **측정 시점** 2026-08-24 · **측정 위치** 워크트리 `worktree-p2-exec`(`git status` 깨끗, 커밋 없음)
> **표기** — `[EVIDENCE]` 는 명령과 그 원문 출력이 있는 것. `[RECOMMENDATION]` 은 거기서 내가 **따라 나온다고 본 것**이며 측정이 아니다.
> `[미측정]` / `[미확인]` 은 감추지 않고 그대로 남긴다.

---

## 0. 한 장 요약

| 대상 | 계획이 인용한 값 | **이번 실측** | 판정 |
|---|---|---|---|
| core-api | **`[미측정]`**(venv·DB 부재) | **224 passed · 0 failed · 0 error** | **처음 측정됨 — 전건 green** |
| pipeline-worker | 72p / 17f / 9e | **72 passed · 17 failed · 9 errors** | **일치 (확인)** |
| viz-render | 42p / 6f | **42 passed · 6 failed** | **일치 (확인)** |
| frontend | 147p / 1f | **147 passed · 1 failed** (148 총) | **일치 (확인)** |
| 게이트 14종 | — | **12 green · 2 red** | 아래 §5 |
| 501 op 수 | 「정본 28 · 실측 29」 | **현재 실물 = 24** | 아래 §6 — **24 는 「변경 전」 값이고 28·29 는 「변경 후」 값이다** |

---

## 1. core-api — `[미측정]` 을 닫았다

### 1.1 무엇이 실제로 필요했는가 `[EVIDENCE]`

`services/core-api` 에는 `.venv` 가 **없었다**(`pipeline-worker`·`viz-render` 에는 있다).
필요한 것은 셋이고, **셋 다 이 호스트에서 충족 가능했다.**

1. **venv + 의존** — `services/core-api/README.md:57-62` 의 절차 그대로.
2. **일회용 postgres** — `services/core-api/tests/fixtures/setup-db.sh` 가 이미 레포에 있다.
   포트를 열지 않고 컨테이너 IP 로만 붙는다(`setup-db.sh:2`).
3. **환경변수 둘** — `COLAB_CORE_TEST_DATABASE_URL` **과** `COLAB_CORE_TEST_SUBJECTS_FILE`.
   ⚠ **둘째를 빠뜨리면 54 error 가 난다** — `conftest.py:54` 는 기본값을 주지만
   `test_live_endpoints.py:26-29`·`test_lab_members.py:28-31`·`test_dataset_detail.py:29-32`·
   `test_dataset_facets.py:24-27` 은 **환경변수를 직접 읽어** 없으면 `pytest.fail` 한다.
   즉 **README 의 예시가 둘을 나란히 적은 것에는 이유가 있다.**

### 1.2 실행한 명령과 원문 결과 `[EVIDENCE]`

```
# ① venv (신규 생성 — services/core-api/.gitignore:1 이 `.venv/` 를 무시한다)
cd services/core-api
python3 -m venv .venv                      # Python 3.12.3
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt      # rc=0

# ② 일회용 DB
docker run -d --name s1w0_pg -e POSTGRES_PASSWORD=a2pw postgres:16
docker exec -u postgres s1w0_pg createdb colab_platform
CONTAINER=s1w0_pg DB=colab_platform bash tests/fixtures/setup-db.sh
  → postgresql+psycopg://colab_app:a2app@172.17.0.2:5432/colab_platform

# ③ 시험
COLAB_CORE_TEST_DATABASE_URL=postgresql+psycopg://colab_app:a2app@172.17.0.2:5432/colab_platform \
COLAB_CORE_TEST_SUBJECTS_FILE=<repo>/services/core-api/tests/fixtures/subjects.json \
.venv/bin/python -m pytest -q
```

```
224 passed in 15.61s
```

**실패 0 · 에러 0.** 이 224 는 `03-HANDOFF` 헤더가 적은 「core-api … 시험 224건」과 **수가 같다.**

### 1.3 중간 관측 — 환경변수를 하나만 준 판 `[EVIDENCE]`

`COLAB_CORE_TEST_SUBJECTS_FILE` 없이 돌린 첫 회차:

```
170 passed, 54 errors in 19.16s
```

54 error 는 전부 `Failed: COLAB_CORE_TEST_DATABASE_URL · COLAB_CORE_TEST_SUBJECTS_FILE 가 없다.`
**green-by-skip 이 아니라 fail-closed 다** — 설계대로다(`CLAUDE.md §4`).

### 1.4 남긴 상태 `[EVIDENCE]`

- `services/core-api/.venv/` **를 새로 만들어 두었다**(gitignore 대상, 커밋 아님). 다음 세션이 다시 안 깔아도 된다.
- 일회용 컨테이너 `s1w0_pg` 는 **측정 후 `docker rm -f` 로 지웠다.** 남은 부산물 없음.
- 추적 파일 변경 0건 — `git status --short` 출력 없음.

### 1.5 `[RECOMMENDATION]`

- **`[미측정]` 은 「돌릴 수 없다」가 아니라 「배선이 문서에만 있었다」였다.** 도구는 이미 레포 안에 다 있었다.
- core-api 는 stage1 기준선에서 **가장 건강한 레인**이다. `W3`/`C1` 이 여기 손댈 때
  **회귀는 224 대비로 재면 된다** — 기준선이 이제 숫자로 존재한다.
- `dev-package/RESTART.md:72` 가 가리키는 절차가 실제로 동작함을 이번에 확인했다.

---

## 2. pipeline-worker — 계획 인용값 확인

### 2.1 명령과 결과 `[EVIDENCE]`

```
cd services/pipeline-worker && ./.venv/bin/python -m pytest -q
```

```
17 failed, 72 passed, 11 warnings, 9 errors in 7.56s
```

**계획의 `72p/17f/9e` 와 정확히 일치한다 — 정정 없음.**

### 2.2 red 의 정체 `[EVIDENCE]`

| 구분 | 건수 | 원인 (출력 원문) |
|---|:--:|---|
| failed | **17** | `Failed: COLAB_REFERENCE_DATA 가 원천 디렉터리를 가리키지 않는다 — E2E 는 skip 하지 않는다` |
| errors | **9** | `Failed: COLAB_PIPELINE_DB_URL 가 없다 — DB 시험을 DB 없이 green 으로 세지 않는다` |

파일별 — `test_axis_detect_real.py`(3) · `test_e2e_real.py`(6) · `test_grid_canonical_nc.py`(1) ·
`test_tiff_classes_pipeline_real.py`(5) = 15 실파일 계열 + 나머지 2 / `test_outbox_db.py`(9) = DB 계열.

### 2.3 `[RECOMMENDATION]`

- **26건 전부가 「환경 부재」 red 이고, 코드 결함 red 는 한 건도 관측되지 않았다.**
  `COLAB_REFERENCE_DATA`(원천 `03 Reference-Data`)와 `COLAB_PIPELINE_DB_URL` 을 주면 판정이 달라진다 —
  **다만 그건 이번 W0 의 범위가 아니다**(실데이터 E2E 는 `§6` 조건 2 의 자리다).
- 이 red 를 「stage1 범위 축소 때문」으로 읽을 여지는 없다. **원인이 출력에 한국어로 적혀 있다.**

---

## 3. viz-render — 계획 인용값 확인

### 3.1 명령과 결과 `[EVIDENCE]`

```
cd services/viz-render && ./.venv/bin/python -m pytest -q
```

```
6 failed, 42 passed in 5.51s
```

**계획의 `42p/6f` 와 정확히 일치한다 — 정정 없음.**

6 failed 는 전부 `tests/test_e2e_real.py`(`test_e2e_1_geotiff` ~ `test_e2e_6_…`)이고
사유는 pipeline-worker 와 같은 `COLAB_REFERENCE_DATA 가 원천 디렉터리를 가리키지 않는다` 다
(`tests/test_e2e_real.py:30` 의 `pytest.fail`).

### 3.2 `[RECOMMENDATION]`

- `viz-render` 는 **휴면 후보**지만 `〈71〉-㉰`(완료 정의 13)에 따라 **CI 에서 계속 돌고 계속 통과해야 한다.**
  지금 42 passed 는 그 「통과」의 기준선이다. **6 failed 는 휴면과 무관한 환경 red 다.**
- ⚠ 조건 13 은 `pytest -m stage2` 가 CI 로그에 **존재하고 green** 일 것을 요구한다.
  이번 실측은 **마커 없이 전건**을 돌린 것이라, **`stage2` 마커 셋의 단독 계수는 `[미측정]`** 이다.
  (`W7` 에서 마커를 붙일 때 재측정 대상)

---

## 4. frontend — 그 **1 건**의 진짜 원인

### 4.1 명령과 결과 `[EVIDENCE]`

```
cd frontend && npx vitest run --reporter=dot
```

```
 Test Files  1 failed | 6 passed (7)
      Tests  1 failed | 147 passed (148)
   Duration  82.77s
```

**계획의 `147p/1f` 와 정확히 일치한다 — 정정 없음.**

### 4.2 실패 원문 `[EVIDENCE]`

```
FAIL  test/upload.test.tsx > §8 등록 결정 게이트 — 등록이 의무가 아님이 화면에서 읽힌다
      > `보기만 할게요` 는 아무것도 등록하지 않는다 — `createDataset` 0회
AssertionError: expected 1 to be +0 // Object.is equality
- Expected  0
+ Received  1
 ❯ test/upload.test.tsx:544:28
```

### 4.3 ⭑ 원인 — **FE 배선 오류다. 범위 축소와 아무 관계가 없다** `[EVIDENCE]`

증거는 네 자리이고, 전부 `cat -n` 으로 행번호를 확인했다.

| # | 위치 | 내용 |
|:-:|---|---|
| ① | `frontend/test/upload.test.tsx:539-546` | 시험은 「`reg-viewonly` 를 누르면 `calls.register` 가 **0**」을 단언한다 |
| ② | `frontend/test/upload.test.tsx:118-123` | `calls.register` 는 `UploadSource.register(body)` **호출 횟수**를 세는 fake 다 |
| ③ | **`frontend/src/components/upload/UploadModal.tsx:226-233`** | `data-testid="reg-viewonly"` 버튼의 핸들러가 **`onClick={() => void submit()}`** 이다 |
| ④ | `frontend/src/components/upload/UploadModal.tsx:153-177` | `submit()` 은 `:165` 에서 **`await upload.register({...})`** 를 호출한다 |

즉 **「보기만 할게요」 버튼이 등록 제출 함수에 연결돼 있다.**
같은 파일 `:275` 의 등록 폼 `onSubmit` 과 **동일한 `submit()`** 을 부른다 — 두 버튼이 같은 동작을 한다.

의도된 동작은 바로 위 `:147-151` 의 **`requestClose()`**(등록 단계가 열려 있지 않으면 그대로 `props.onClose()`)로 보인다.
`:238-241` 의 `reg-open` 만이 등록 흐름(`setRegisterOpen(true)`)을 열도록 짜여 있기 때문이다.

**부수 관측** — 같은 시험의 다음 줄 `:545`(`upload-modal` 이 사라졌는가)는 **통과했을 것**이다.
`submit()` 이 성공 경로에서 `:176` `props.onClose()` 를 부르기 때문이다.
**즉 「모달이 닫혔다」는 이 버그를 가려 준다** — 눈으로 보면 정상으로 보이고, 시험만이 등록이 일어난 것을 잡는다.

### 4.4 못 박아 둔다 `[RECOMMENDATION]`

- **이 red 는 stage1 범위 축소보다 앞선다.** 원인은 `UploadModal.tsx:230` 한 줄의 핸들러 배선이며,
  미리보기·가공·가시화·격자 중 **무엇을 빼든 이 줄은 그대로 등록을 부른다.**
  나중에 「범위를 줄여서 깨졌다」로 오인될 여지를 여기서 닫는다.
- **제품 위험은 시험 실패보다 크다.** 정본이 「등록은 의무가 아니다」를 화면 규격으로 못 박았는데,
  현재 코드는 **「보기만 할게요」를 눌러도 데이터셋이 만들어진다.** 사람이 등록하지 **않기로** 한 결정이 무시된다.
- **고치는 것은 W0 의 일이 아니다.** 소유 레인(FE 업로드)이 `W3` 에서 손댈 때 함께 닫아야 한다.
  ⚠ 고칠 때 `:154` 의 `if (!uploadId) return` · `:155` 의 이름 검사 때문에
  **fake 이름이 비어 있었다면 이 시험은 다른 이유로 통과했을 것**이라는 점도 같이 본다 — 지금은 통과하지 않았다.

---

## 5. 게이트 — 14종 실행

`gates/run.sh` 에는 **전체 실행 타깃이 없다**(`gates/run.sh:120-123`, 인자 없으면 `usage` 후 `exit 2`).
그래서 `gates/README.md` 의 게이트 표대로 **하나씩** 돌렸다. selftest 셋(7종)은 이번 범위에서 제외했다 — `[미측정]`.

```
./gates/run.sh <게이트>        # 14회, 종료코드 기록
```

| # | 게이트 | rc | 판정 | 한 줄 |
|:-:|---|:--:|---|---|
| 1 | `planning-freshness` | 1 | **RED** | **⚠ 예상 밖 — §5.1** |
| 2 | `contract-lint` | 0 | GREEN | |
| 3 | `contract-breaking` | 0 | GREEN | |
| 4 | `event-lint` | 0 | GREEN | |
| 5 | `event-breaking` | 0 | GREEN | |
| 6 | `import-boundary` | 0 | GREEN | `services/` 에 코드가 생겨 green 이 됐다 — `gates/README.md` 의 「red — 코드가 없다」 줄은 **낡았다** |
| 7 | `banned-import` | 0 | GREEN | 위와 같음 |
| 8 | `ai-no-lineage-write` | 0 | GREEN | 위와 같음 |
| 9 | `migration-single-head` | 0 | GREEN | |
| 10 | `schema-diff` | 1 | **RED** | **설계대로 — §5.2** |
| 11 | `rls-coverage` | 0 | GREEN | |
| 12 | `rls-effect` | 0 | GREEN | 본체 음성 · 메타 양성(P-13) · cross-tenant 셋 다 green |
| 13 | `seam-consistency` | 0 | GREEN | |
| 14 | `generated-up-to-date` | 0 | GREEN | `03-HANDOFF` 의 P2 W0-7 실측과 일치 |

**12 green · 2 red.**

### 5.1 red ① `planning-freshness` — **설계대로가 아니다. 워크트리 때문이다** `[EVIDENCE]`

```
::error::planning-freshness red — 1건
  - 정본 폴더가 없다 (위치 확인 — planning/README.md §1):
    <워크트리>/.claude/worktrees/40 COLAB-기획/…/에픽
```

게이트가 정본 패키지 경로를 **레포 루트 기준 상대**로 잡는데, 이 세션은 `.claude/worktrees/p2-exec` 안에서 돌아
루트가 워크트리로 바뀌었다. 그래서 **정본 폴더의 실제 자리(메인 레포 옆)를 못 찾는다.**

**정본이 낡았다는 신호가 아니다** — 정본을 아예 못 읽은 것이고, 게이트는 그 경우 skip 하지 않고 red 를 내도록 짜여 있다(`gates/run.sh:13-14`). **fail-closed 는 정상 동작이다.**

⚠ **`W1` 에 직결된다.** `W1` 은 정본 개정 24자리 단독 물결이고, 그 완료 판정이 `planning-freshness` green 이다.
**워크트리 안에서는 이 게이트를 green 으로 만들 수 없다.** → §7 블로커 ①

### 5.2 red ② `schema-diff` — **설계대로 red** `[EVIDENCE]`

```
::error::schema-diff red — 적용 DB 가 지정되지 않았다:
     - COLAB_APPLIED_DB_URL_PLATFORM (db/platform)
     - COLAB_APPLIED_DB_URL_AI (db/ai)
   **DB 가 없을 때 skip 하는 것이 v1 CI 의 실패였다.** 한 체인이라도 없으면 red 다.
```

`gates/README.md` 가 이미 「체인별 URL 을 **둘 다** 주면 green. 하나라도 없으면 red」라고 적어 둔 그대로다.
**게이트를 끄거나 우회하지 않았고, 환경변수를 임의로 주입해 green 을 만들지도 않았다.**

### 5.3 `[RECOMMENDATION]`

- **게이트 기준선은 실질적으로 「전 게이트 green, 단 두 red 는 둘 다 환경 미배선」이다.**
  `C1` 의 통과 조건 「전 게이트 green」은 **환경 배선 문제이지 코드 문제가 아니다.**
- `gates/README.md` 의 「현재 상태 (2026-08-23)」 표에서 **6·7·8 행이 낡았다**
  (「red — `services/` 에 코드가 없다」 → 실측 green). `DATA-REFERENCE §0 M-6`(문서를 실물 확인 없이 인용하지 않는다)의
  전형이라 여기 적어 둔다. **이번 세션은 문서를 고치지 않았다** — 메인 세션 소관이다.
- selftest 7종(`contract`·`event`·`boundary`·`db`·`rls-effect`·`seam-consistency`·`generated`)은 **`[미측정]`** 이다.

---

## 6. 501 — 현재 실물은 **24** 다

### 6.1 명령과 결과 `[EVIDENCE]`

```
python3 -c "import re,pathlib; \
  t=pathlib.Path('services/core-api/src/colab_core/app/routes/not_implemented.py').read_text(); \
  ops=re.findall(r'Op\(\"(\w+)\"',t); print(len(ops))"
```

```
24
```

**전체 목록 (`not_implemented.py:47-82`)**

| # | operationId | code | 행 |
|:-:|---|---|:--:|
| 1 | `updateLab` | `NOT_IMPLEMENTED_P1` | 47 |
| 2 | `deleteDataset` | `NOT_IMPLEMENTED_P1` | 48 |
| 3 | `getDatasetDeletionImpact` | `NOT_IMPLEMENTED_P1` | 49 |
| 4 | `downloadDataset` | `NOT_IMPLEMENTED_NO_STORE` | 51 |
| 5 | `getDatasetLineage` | `NOT_IMPLEMENTED_P1` | 52 |
| 6 | `createAccessRequest` | `NOT_IMPLEMENTED_NO_STORE` | 53 |
| 7 | `listPendingAccessRequests` | `NOT_IMPLEMENTED_NO_STORE` | 55 |
| 8 | `approveAccessRequest` | `NOT_IMPLEMENTED_NO_STORE` | 57 |
| 9 | `rejectAccessRequest` | `NOT_IMPLEMENTED_NO_STORE` | 59 |
| 10 | `requestVerification` | `NOT_IMPLEMENTED_NO_STORE` | 61 |
| 11 | `listPendingVerificationRequests` | `NOT_IMPLEMENTED_NO_STORE` | 63 |
| 12 | `approveVerification` | `NOT_IMPLEMENTED_P1` | 65 |
| 13 | `cancelVerification` | `NOT_IMPLEMENTED_P1` | 67 |
| 14 | `listProjects` | `NOT_IMPLEMENTED_P1` | 69 |
| 15 | `getProject` | `NOT_IMPLEMENTED_P1` | 70 |
| 16 | `updateProject` | `NOT_IMPLEMENTED_P1` | 71 |
| 17 | `deleteProject` | `NOT_IMPLEMENTED_P1` | 72 |
| 18 | `setProjectStatus` | `NOT_IMPLEMENTED_P1` | 73 |
| 19 | `unlinkProjectDataset` | `NOT_IMPLEMENTED_P1` | 74 |
| 20 | `getDashboardSummary` | `NOT_IMPLEMENTED_P1` | 76 |
| 21 | `getDataMap` | `NOT_IMPLEMENTED_P1` | 77 |
| 22 | `listActivities` | `NOT_IMPLEMENTED_P1` | 78 |
| 23 | `updateDataset` | `NOT_IMPLEMENTED_NO_STORE` | 80 |
| 24 | `linkProjectDataset` | `NOT_IMPLEMENTED_NO_STORE` | 81 |

**계수 — `NO_STORE` 9 · `P1` 15.** `test_not_implemented.py:80` 의 `assert len(p1) == 15` 와 일치하고,
`:61` 의 `assert len(OPERATIONS) == 24` 도 **현재 green** 이다(§1.2 의 224 passed 에 포함).

### 6.2 「28 vs 29」의 정체 `[RECOMMENDATION]`

**세 숫자는 서로 다른 시점을 가리킨다. 모순이 아니라 시점 혼동이다.**

| 값 | 무엇인가 | 근거 |
|:--:|---|---|
| **24** | **지금 실물.** stage1 이 아무것도 바꾸기 전 | 이 절 §6.1 — 실측 |
| **29** | 24 **＋ 되돌릴 5행** = `createPreviewRender`·`getPreviewRender`·`addDatasetFile`·`replaceDatasetGridFile`·`deleteDatasetGridFile` | 산술. `03-HANDOFF` 헤더의 「stage1 에서 29(실측)」이 이 값 |
| **28** | `〈71〉-㉮` 가 정본으로 확정한 값 | `S1-PLAN.md §6` 조건 3 |

즉 **`24 + 5 = 29 ≠ 28`** 이고, **차이는 정확히 1 이다.** 이 1 이 어디서 나는지는 이 실측만으로 판정되지 않는다 — **`[미확인]`**.
`S1-PLAN §6` 조건 3 이 이미 이렇게 지시해 두었다: **「정본 값을 바꾸지 않고, 실물 대조 결과를 `PLAN-SoT §9` 에 기록해 맞춘다.」**

**W3/C1 이 쓸 하드 기준선은 이것이다 — 변경 전 `len(OPERATIONS) == 24`, 목록은 위 표 24행.**
`W3` 이 표를 고칠 때 **위 24행 중 무엇도 사라지지 않았고 5행만 늘었는지**를 이 표와 1:1로 대조하면
「1 의 차이」가 산술 오차인지 목록 중복인지가 그 자리에서 드러난다.

⚠ **같은 커밋에서 `test_not_implemented.py` 세 단언(`:61` · `:23-36` · `:80`)과 시험 이름(`:59` `test_the_24_…`),
docstring(`:60`)까지 함께 고쳐야 한다** — 안 그러면 다음 사람이 「시험을 고쳐 통과시켰다」로 읽는다(`S1-PLAN §6` 조건 3 ⓑⓒⓓ).

---

## 7. `W1` 착수를 막는 것 — 블로커

### ① `planning-freshness` 는 이 워크트리에서 green 이 될 수 없다 `[EVIDENCE + RECOMMENDATION]`

- **사실**: 게이트가 정본 패키지를 레포 루트 상대로 찾는데, 워크트리에서는 그 경로가 실재하지 않는다(§5.1 원문).
- **함의**: `W1` 은 **정본 개정 9파일 24자리 단독 물결**이고, 그 개정의 유일한 기계적 수호가 이 게이트다.
  **워크트리 안에서 개정하면 「고쳤다」를 아무도 검증하지 못한다.**
- **선택지 (판단은 메인 세션)**: ⓐ `W1` 을 **메인 레포 체크아웃에서** 수행 ⓑ 정본 폴더를 워크트리에서도
  보이게 배선 ⓒ `W1` 개정 커밋 후 메인 레포에서 게이트를 한 번 돌려 확인.
  **어느 쪽도 이번 세션이 임의로 정하지 않는다** — 게이트를 우회하는 모양이 되기 때문이다.

### ② 그 밖에는 `W1` 을 막는 것이 없다

- `W1` 의 진입조건은 `S1-PLAN §5.3` 상 「W0 완료」 하나이고, **W0 은 이 문서로 완료된다.**
- `schema-diff` red 는 환경 미배선이고 **`W1`(문서 개정)과 무관**하다. `C1` 조건 「전 게이트 green」에서 다시 만난다.
- **stage1 범위와 무관한 제품 결함 1건이 발견됐다** — §4.3 의 `UploadModal.tsx:230`.
  `W1` 을 막지는 않지만, **`W3` FE 레인의 작업 목록에 반드시 올라가야 한다.**

---

## 8. 이번 세션이 재지 **않은** 것 (감추지 않는다)

| 항목 | 상태 | 왜 |
|---|---|---|
| 게이트 selftest 7종 | `[미측정]` | W0 지시 범위 밖. `C1` 전에 한 번은 돌려야 한다 |
| `pytest -m stage2` 마커 셋 단독 계수 | `[미측정]` | 마커가 아직 안 붙었다. 완료 정의 13 의 대상 |
| 실데이터 E2E(`COLAB_REFERENCE_DATA` 부여 후) | `[미측정]` | 완료 정의 2 의 자리이지 기준선이 아니다 |
| ai-service 시험 | `[미측정]` | 계획의 기준선 실측 목록에 없다 |
| 「28 vs 29」의 1 차이 | `[미확인]` | §6.2 — `W3` 실물 대조로만 닫힌다 |
| staging 배포 상태 | `[미측정]` | 컨테이너가 떠 있는 것은 봤으나(`docker ps` 4건 healthy) **`docker compose ps` 는 판정이 아니다**(`P2-EXEC §6`) |

---

## 9. 재현

```bash
# core-api
cd services/core-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
docker run -d --name s1w0_pg -e POSTGRES_PASSWORD=a2pw postgres:16
docker exec -u postgres s1w0_pg createdb colab_platform
URL=$(CONTAINER=s1w0_pg DB=colab_platform bash tests/fixtures/setup-db.sh)
COLAB_CORE_TEST_DATABASE_URL="$URL" \
COLAB_CORE_TEST_SUBJECTS_FILE="$PWD/tests/fixtures/subjects.json" \
  .venv/bin/python -m pytest -q
docker rm -f s1w0_pg

# 나머지
cd services/pipeline-worker && ./.venv/bin/python -m pytest -q
cd services/viz-render     && ./.venv/bin/python -m pytest -q
cd frontend                && npx vitest run --reporter=dot

# 게이트 (전체 타깃 없음 — 하나씩)
./gates/run.sh <게이트>
```
