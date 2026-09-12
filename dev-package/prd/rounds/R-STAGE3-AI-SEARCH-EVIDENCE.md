> spec: dev-package/prd/specs/STAGE3-AI-SEARCH-EVIDENCE.md
# AI 검색 근거 연결 실행 계획

사용자 요청대로 이 세션에서 직접 진행하고, 제품 구현만 격리 사본에서 수행한다. 중간 단위 종료를 전체 종료로 취급하지 않는다.

**Goal:** 파일 역할 근거 실험과 정직한 제품 조건 설명을 구현·검증한다.
**Architecture:** 실험 수동 주석과 제품의 실제 조회 사실을 구분한다. 제품은 기존 한 줄 근거 계약을 재사용한다.
**Tech Stack:** Python 표준 라이브러리, 기존 FastAPI/pytest, 기존 React 검색 화면.

## 실행 목록

- [x] 1. `eval/k4-search/test_structured_probe.py`: 파일 역할 근거 적용·없는 파일 차단·SPI 제외의 실패 시험 → `structured_probe.py`에 선택적 evidence 입력 구현 → 재실행.
- [x] 2. `eval/k4-search/file-role-evidence.json`: 원 설명서 절을 확인하고 조건 근거·한계를 결과에 투영 → 기존18문항 재실행, 판정 기록.
- [x] 3. 격리 사본 `services/core-api/src/colab_core/app/search_conditions.py`와 `routes/catalog.py`: 질문별 미확인 조건을 한 줄 rationale에 연결. `tests/test_search_condition_rationale.py` 실패→구현→통과.
- [x] 4. 코드 고정 후 독립 질문을 받아 수정 없이 최초 평가. 이후 발견한 결함은 별도 실행 번호로 수정·검증.
- [ ] 5. core 검색 관련 시험 및 frontend 검색 소비 시험, 계약·대장 검사. A층 원 실행기 시도 후 준비 상태와 기준선 대비를 기록.
- [x] 6. 가용 로컬 화면에서 검색→근거→상세 여정 검증. 환경 부재면 실제 실패 증거와 실행에 필요한 입력을 남긴다.
- [x] 7. 결과·미해결·상위7단계 상태·배포 전 남은 작업을 동기화한다. 제품 전체 완료 기준은 축소하지 않는다.

커밋·push·배포·LLM 호출은 이 실행 목록에 없다. 기존 전체 계획의 해당 단계는 실제 수용 기준 충족 시에만 닫는다.

- [x] 8. 실제 LiteralInterpreter→사전→D3 조합에서 파일명 확장자 토큰 회귀까지 수정하고 재측정한다. AI 서비스 단위 시험과 전체 게이트를 확인한다.

진행·검증·미충족 정본: `dev-package/sessions/20260913-ai-search-execution.md`.

- [x] 9. 원 DOCX4개 본문·hash 수집, 주석10개를 snapshot 파일 ID와 연결. 변경 감지/중복 원문/대상 부재/경로 경계 시험5개 및 실제 수집·검증 통과. `source-provenance-01.json`.
- [x] 10. 실제 D3 저장·수정·파일 생명주기·권한 경로 조사, 후속 저장 설계 `../specs/STAGE3-AI-SEARCH-EVIDENCE-STORAGE.md` 기록.

5번은 core1131/AI142/검색 화면38/타입/계약/대장 및 실제 A층 측정까지 실행했다. 전체 frontend-test는 worker 시작 오류5건으로 exit1이므로 통과 체크하지 않는다. 기존 A층 품질은6충족/9미충족/1판정보류다.
