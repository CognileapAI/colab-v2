# WU-A7R — 연관 한 표 ＋ 유형 열 ＋ 이름 중복 검사 (R-A′ · 레인 `p3-project-table`)

- 회차 = R-A′ · 통합 브랜치 `integration/r-a2` · 기점 HEAD `21bf4a1`.
- 정본 = `dev-package/prd/rounds/R-A2.md §2-③` · `dev-package/prd/specs/R-A2.md:45` ·
  `dev-package/prd/PRD-260905-적용전기획.md` `#### PRD-23`(개정본) · `#### PRD-42` · PRD-43 `J-12`.
- 계약 0 · 스키마 0 · 마이그레이션 0.

## 1. 완료 조건 ↔ 판정 ↔ 근거

| 완료 조건(축자) | 판정 | 근거 `파일:행` |
|---|---|---|
| 표 한 장에 행을 쌓는다 | 충족 | `frontend/src/components/upload/RegisterArea.tsx:520` `<table className="projtable" data-testid="reg-proj-table">` · 시험 `frontend/test/prd23-project-table-20260907.test.tsx:107` |
| 열이 `유형`·`이름`·`해제` | 충족 | `RegisterArea.tsx:523-525`(`<th scope="col">`) · 시험 `prd23-project-table-20260907.test.tsx:129` |
| 유형 배지가 저장값 `kind` 에서 온다 | 충족 | `RegisterArea.tsx:533` `data-testid="reg-proj-row-kind"` 가 `p.type` 을 그린다(정규식 판정 0건) · 시험 = 이름에 `논문` 이 든 국가과제 `prd23-project-table-20260907.test.tsx:182` |
| 연관 0건이면 표가 화면에 없다 | 충족 | `RegisterArea.tsx:519` `props.picked.length > 0 &&` · 시험 `prd23-project-table-20260907.test.tsx:164`·`:174` |
| `+ 새 프로젝트 만들기` 는 영역 맨 아래 한 곳 | 충족 | `RegisterArea.tsx:596-599`(표 뒤 `PermissionGate` 안 1개) · 시험 `prd23-project-table-20260907.test.tsx:190` |
| 같은 연구실 · 이름 겹치면 거절(유형 달라도) | 충족 | `services/core-api/src/colab_core/app/routes/project.py:158` `errors.bad_request("같은 이름의 프로젝트가 이미 있어요. 목록에서 골라 주세요")` · 시험 `services/core-api/tests/test_project_name_duplicate.py:32`·`:41` |
| 다른 연구실의 같은 이름은 성공 | 충족 | 경계는 RLS 가 건다(`domains/d6_project.py:47-53` `_NAME_TAKEN` 주석) · 시험 `test_project_name_duplicate.py:51` (201) |
| 빈 이름 문면 무변 | 충족 | `frontend/src/components/project/ProjectFormModal.tsx:56` 무편집 · 음성 시험 `test_project_name_duplicate.py:68` · `prd23-project-table-20260907.test.tsx:257` |
| J-12 문면이 `toastCopy.ts` 에서 온다 | 충족 | `RegisterArea.tsx:17`·`:642` `{QUICK_PROJECT_NOTE}` ← `frontend/src/components/common/toastCopy.ts:55` · 시험 `prd23-project-table-20260907.test.tsx:210` |

## 2. RED → GREEN

| 시험 | RED 실측 | GREEN |
|---|---|---|
| `frontend/test/prd23-project-table-20260907.test.tsx` (표·열·배지·0건 숨김·J-12) | `Test Files 1 failed (1) / Tests 10 failed \| 1 passed (11)` — `TestingLibraryElementError: Unable to find an element by: [data-testid="reg-proj-table"]` | 13건 전부 통과(중복 문면 2건 추가 후) |
| `services/core-api/tests/test_project_name_duplicate.py` (같은 연구실 400 · 유형 달라도 400) | `FAILED tests/test_project_name_duplicate.py::test_same_name_in_the_same_lab_is_refused_with_the_rev2_message - AssertionError: {"code":"CONFLICT","message":"같은 이름의 프로젝트가 이미 …` (2건 failed) | 4건 통과 |
| 게이트 전체 RED 계수(구현 전) | `service-tests-core-api — 선택자 «not e2e» · 수집 830 · 실행 830 · skipped 0 · deselected 6 · failed 3 · errors 0 · 소요 111.6초` | 아래 §3 |

- RED 3건 중 셋째(`test_project_screens.py::test_list_projects_never_crosses_the_lab_boundary`)는 **새 시험이 만든 다른 연구실 행이 같은 회차에 남아** 발생. 시험이 `deleteProject` 로 자기 행을 되돌리게 고쳐 해소(`test_project_name_duplicate.py:62-66`). 어느 검사에 걸리는가 = `service-tests-core-api` 게이트.

## 3. 게이트 (배출처 `dev-package/reports/R-A2/p3-project-table`)

```
frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.
frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 840건 · 실패 0건.
service-tests-core-api — 선택자 «not e2e» · 수집 830 · 실행 830 · skipped 0 · deselected 6 · failed 0 · errors 0 · 소요 107.3초
service-tests-core-api green — 실행 830건 전부 통과 (skipped 0 · deselected 6 은 요약줄에 드러나 있다).
```

계 = green 3 / red(판정) 0 / red(준비) 0.

## 4. 기존 중복 건수 실측

**[미측정].** 사유 = 실데이터를 담은 DB 에 이 레인이 닿지 않는다.
- `~/.colab-v2-test.env` 의 `COLAB_CORE_TEST_DATABASE_URL` 은 접속 거절 —
  `FATAL: password authentication failed for user "colab_app"` (자격 회전 이후 값 미갱신).
- 게이트가 쓰는 postgres 는 **회차마다 새로 만들고 지우는 일회용**(`gates/tools/_pg.sh`)이라
  시드 행만 있고 연구실 실데이터가 없다 — 거기서 센 0건은 실측이 아니다.
- staging·dev DB 접근은 이 레인 밖(`rules §2-3`).

읽기 전용 질의(측정할 자리에서 그대로 쓴다) —

```sql
SELECT lab_id, btrim(lower(name)) AS n, count(*) AS c
  FROM d6_project GROUP BY 1, 2 HAVING count(*) > 1;
```

기존에 겹치는 행은 **지우거나 고치지 않았다.** 신규 생성만 막는다(`project.py:150-158` 주석).

## 5. 자기 표시

1. **목업과 열 순서가 다르다.** rev2 원문(`업로드_계보_260905_rev2_이태헌.html:1069-1075`)의 표는
   `이름 · 유형 · (빈 칸 · × 단추)` 다. 구현은 **라운드 파일·PRD-23 개정본의 `유형 · 이름 · 해제`** 를 따랐다
   (`R-A2.md §2-③` 축자 · 완료 조건도 같은 순서). 목업과 갈리는 자리이므로 여기 적어 둔다.
2. **`해제` 열의 조작은 글자 단추다.** 목업은 `×` 이고 접근 이름이 `프로젝트 빼기` 다.
   구현은 열 머리와 같은 말(`해제`)을 단추 글자로 쓰고 접근 이름을 `<이름> 해제` 로 뒀다.
3. **종전 두 패널 시험 파일을 지웠다** — `frontend/test/project-panels-20260905.test.tsx`.
   그 파일의 주제가 「두 패널로 갈린다 · 0건 패널도 남는다」 전부라 개정본과 정면으로 어긋난다
   (판정 축자 「두 패널 분리를 걷는다」). 살아 있는 수용 기준(링크 1개 · 유형 먼저 · 행이 아래로 붙음)은
   새 파일 `prd23-project-table-20260907.test.tsx` 로 옮겨 전건 유지했다. **존치 6종이 아니다.**
4. **생성 거절의 상태코드를 409 → 400 으로 바꿨다**(`project.py:158`). 라운드 파일이 「400 with message
   verbatim」을 명시한다. **수정(`updateProject`) 쪽 409 는 건드리지 않았다** — 그쪽은 이 문면을 띄우는
   자리가 아니다. 기존 시험 1건의 기대값을 함께 고쳤다(`test_lab_and_project_update.py:116-127`).
5. **거절 문면을 화면에서 다시 적지 않았다.** 서버가 보낸 문장을 `projectSource.create`
   (`frontend/src/components/upload/projectSource.ts:20-25`)가 그대로 올리고 화면이 띄운다
   (`RegisterArea.tsx:637`). PRD-43 21행이 아니므로 `toastCopy.ts` 에 넣지 않았다.

## 6. 하지 않은 것

- **DB UNIQUE 제약 신설 0.** 응용 층 검사다(마이그레이션 0 · 라운드 파일 축자). 기존 중복 행이 있으면
  제약 생성이 실패하는 자리라 판정이 필요하다 — 후속.
- **`updateProject` 의 중복 문면·상태코드 무변**(409 · `같은 이름의 프로젝트가 이미 있어요`).
- **빈 이름 문면 무변** — `이름을 적어 주세요. 나중에 찾을 때 쓰는 유일한 이름이에요.`
- **존치 6종 무접촉** — 기준 격자 파일 흐름 · AI 계보 제안 · 2단 등록 게이트 · 이어올리기 배너 ·
  승인·검증 층 · 값 조회 패널. 회귀 시험 삭제 0.
- 계약(`contracts/`) · `db/` · `alembic` · `PLAN-SoT.md` · `03-HANDOFF.md` 무접촉.
