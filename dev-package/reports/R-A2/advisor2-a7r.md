# advisor ② — WU-A7R (lane p3-project-table · 21bf4a1..2e6f5e5)

For:
- 완료 조건 8행 전부 코드＋시험 근거 실재. `contracts/ db/ alembic` diff 0 실측. RLS 경계 검증 — `services/core-api/src/colab_core/app/deps.py:31-37` `scoped_db` 가 `apply_scope`(SET LOCAL) 후 yield · `db/platform/schema.sql:1094-1096` d6_project FORCE RLS＋`lab_id = current_lab_id()` · `tests/conftest.py:48` 앱 롤 NOBYPASSRLS · 타 연구실 201 시험(`test_project_name_duplicate.py:51`) green.
- 400 은 계약 정합 — `contracts/seams/fe-core.yaml` POST /projects 응답 = 400·401·403·500, 409 미선언. 종전 409 가 계약 밖이었고 레인이 계약 무수정으로 선언 집합 안으로 이동. 응답 봉투 동일(`kernel/errors.py:64-65,74` 둘 다 `ApiError`→`ErrorEnvelope`).
- 삭제 시험 `project-panels-20260905.test.tsx` 8건 → 6건 이관(3행 쌓기·해제·아래로 붙음·링크 1개·유형 먼저·빠른 생성 논문) ＋ 2건 폐기(「0건 패널 잔존」 = 판정 r2-3 ⓐ 와 정면 상충). 존치 6종 무접촉.

Against:
- 레인 노트 §5-4 「라운드 파일이 400 with message verbatim 을 명시」 = 허위 인용. `R-A2.md §2-③`·PRD-42·`specs/R-A2.md`·intent 에 상태코드 0건(grep 400 → PRD-32 만). 코드베이스 자체 규범과도 충돌 — `tests/test_input_error_paths.py:127` 「409 로 접으면 화면은 이미 있어요로 읽고」 · `kernel/errors.py:69` · `d6_project.py:59` `ProjectNameTaken` 「호출자가 409 로 바꾼다」. 생성 400 / 수정 409 로 같은 조건의 코드가 갈림. 계약 인용으로만 방어 가능.
- PRD-42 수용 3행(빈 이름 → 종전 문면) 미달 — 빠른 생성 칸 `RegisterArea.tsx quickCreate` `if (!qName.trim()) return;` 무반응, `만들고 담기` disabled 아님. 노트는 `ProjectFormModal.tsx:56` 무편집으로 「충족」 표기하나 빠른 생성 칸은 그 모달을 쓰지 않음. 시험 :257 은 중복 문면 부재만 확인(오라클 오지정). 기존 결함 → §1 「고치지 말고 보고」 대상.
- 경합 미언급 — 동시 생성 2건이 둘 다 `name_is_taken` 통과 후 삽입(UNIQUE 부재). diff·노트에 「동시/경합」 0건.

Verdict: approve-with-changes — 코드 무변 · 세션 노트 정정 3건 병합 전 필수.

Risks:
1. 프로젝트 화면 경로 `frontend/src/components/project/projectSource.ts:53` 가 서버 문면을 버리고 `프로젝트를 만들지 못했어요.` 로 대체 → 같은 400 이 업로드 화면(축자)과 프로젝트 화면(일반문)에서 두 얼굴. PRD-42 영향 범위가 `ProjectFormModal.tsx` 를 명기.
2. UNIQUE 부재 경합 창 — 후속 마이그레이션 항목이 대장에 없음.
3. 기존 중복 건수 [미측정] — 이번 변경엔 무해(신규만 차단), 후속 UNIQUE 판정의 선행 수치 부재.

Missed:
- 빈 이름 수용 3행 미달(위).
- kind 값 집합 — 원본은 `contracts/schemas/common.json:168-172` enum. FE 리터럴 사본 2곳 잔존(`RegisterArea.tsx` `<option value="국가과제"|"논문">` · `ProjectFormModal.tsx:18 TYPES`). 레인은 셋째 사본 `PROJECT_PANEL_TYPES` 삭제. 회귀 아님·단일 소스 아님.
- `qError` 가 이름 수정 시 미소거(성공·닫기까지 잔존) — jsdom 비가시 실화면 항목.
- PATCH 409 도 계약 미선언(`fe-core.yaml` PATCH 응답 400·401·403·404·500) — 기존·범위 밖, 기록 필요.
- `d6_project.py:59` docstring 「409」 낡음.
- 목업 열 순서(이름·유형·×) 이탈은 자기 표시 적정 — 판정 r2-3 → PRD-23 개정본이 목업보다 상위. 수용.

Fixes:
1. [병합 전 필수] 세션 노트 §5-4 근거 교체 — 「라운드 파일 명시」 삭제 → 「`contracts/seams/fe-core.yaml` POST /projects 선언 응답 400·401·403·500 · 409 미선언」. PATCH 409 미선언 사실 병기 ＋ 후속 항목 지정.
2. [병합 전 필수] 세션 노트 §1 「빈 이름 문면 무변」 행을 「미달·보고」로 전환 — 빠른 생성 칸 무반응 실측 기재 · Ted 판정 요청(고치지 않음).
3. [병합 전 필수] 세션 노트 §6 에 경합 명기 — 「동시 생성 2건은 둘 다 통과(UNIQUE 부재) · 후속 마이그레이션 항목과 연결」.
4. [선택] `d6_project.py:59` docstring → 「생성 400 · 수정 409」.
5. [선택 · R-B 이관] `project/projectSource.ts:53` 도 `r.error.message` 우선 노출로 업로드 경로와 통일.
