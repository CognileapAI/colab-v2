# 제품 CI 최종 독립 리뷰 — 2026-09-08

대상: ci.yml, agent-bridge.yml, ci-filter-check.py, ci-schema-diff.sh,
test_ci_* 및 test_planning_gate.py. 제품 코드와 동시 작업 중인 agent-bridge.py는 수정하지 않았다.

## 판정: 발견한 권한 누락 수정 확인, 추가 차단 사항 없음

**[P1] PR 변경 경로 판독에 필요한 권한 누락.** `.github/workflows/ci.yml`의 최상위
permissions는 contents:read만 지정하며 changes 잡에 별도 권한이 없다.
`dorny/paths-filter`는 PR 이벤트에서 REST API로 변경 파일을 읽으므로 pull-requests:read가 필요하다.
PR에서 changes가 실패하면 의존하는 제품/스키마/기획 잡이 실행되지 않는다.
새 diff에 처음 생긴 문제는 아니지만 이번 CI 실행 가능성의 차단 요인이다.
changes 잡에 contents:read와 pull-requests:read를 좁게 지정하는 수정을 권고했다.
메인 반영 후 실제 ci.yml을 다시 읽어 changes 잡에 두 read 권한이 추가됐음을 확인했다.
이 발견은 해결됐으며 현재 검토 범위에서 추가 차단 사항은 없다.
근거: [paths-filter 공식 Supported workflows](https://github.com/dorny/paths-filter#supported-workflows).
이 리뷰는 원격 Actions 실행을 재현한 것이 아니라 실제 설정과 요구 권한을 대조한 것이다.

## 나머지 대조

- schema wrapper는 게이트 venv를 준비하고 적용용 platform/ai DB를 일회용 PostgreSQL에 생성한다.
  기존 schema-diff가 upgrade와 비교를 수행하며 tmpfs/cleanup은 기존 _pg.sh를 재사용한다.
  운영 URL/외부 검사 대체 입력을 제거하고 슬롯 2개 미만은 준비 실패로 종료한다.
  db 필터는 wrapper/schema-diff/_pg/_venv/requirements/ci.yml 변경을 포함한다.
- planning 잡은 실제 원본 검사를 수행했다고 주장하지 않는다. 스텝명과 notice 양쪽에서
  합성 fixture 회귀와 실제 원본 로컬 필수 검사를 구분한다. 원본 검사기 자체의 fail-closed는
  유지돼 있다. 다만 이 CI green만으로 원본 최신성이나 병합 가능성을 증명하지 못한다.
- harness 잡은 명시 면제와 로컬 러너/판정부 회귀를 실행하고 API 키에 의존하지 않는다.
  일부 과거 주석에 '실과제/모델 비용' 표현이 남았으나 실제 스텝은 모델 미실행을 명시한다.
- agent-bridge workflow는 PyYAML 공통 핀 설치 후 unittest를 실행한다. scripts/tests 변경과
  ci-filter-check.py/ci.yml 변경은 트리거에 포함된다. 이 리뷰는 동시 변경 중인 어댑터 본문에
  관한 완료 판정을 내리지 않는다.
- 메인 보고의 실 DB 2개 green/cleanup 0, 전체 unit 23, frontend 41은 전달받은 실행 근거다.
  본 리뷰에서는 DB와 프론트 검사를 중복 실행하지 않았다. 이를 원격 CI·모델 eval·E2E 완료로
  확대하지 않는 현재 보고 범위는 타당하다.

## 독립 재실행

WSL에서 test_ci_*.py 4 tests 및 test_planning_gate.py 5 tests를 직접 실행해 전부 통과했다.
이는 로컬 설정·판정부 회귀 증거이며 PR 토큰 권한 및 원격 job 성공의 대체 증거가 아니다.
