# 제품 CI 변경 수용 검토 — 2026-09-08

For: 기존 schema-diff에 적용 DB를 공급하고 이미 면제인 eval 잡의 불필요한 API 키 선검사를 제거하는 것은 확인된 준비 결손을 직접 고친다. 기존 모델 실행 경로와 과제 건수를 유지하므로 키 제거 자체는 검사 범위 축소가 아니다.
Against: schema wrapper의 일회용 격리 주장은 현재 호출 구조에서 성립하지 않는다. 외부 환경 파일이 URL을 다시 덮어써 기존 DB upgrade를 실행할 수 있으므로 현재 wrapper 실행/수용은 반려한다. eval 변경까지 폐기할 근거는 없다.
Verdict: schema wrapper reject; eval/key 제거 approve-with-changes(원격 실행 증거는 별도).

## 실제 수정 필요

### P1 — 일회용 URL 뒤에 외부 env가 다시 로드된다

- 위치: `gates/tools/ci-schema-diff.sh` 마지막 URL export/unset 및 `bash gates/run.sh schema-diff`; `gates/run.sh:133-138`; `gates/tools/schema-diff.sh:109,130-131`.
- run.sh는 `COLAB_TEST_ENV_SOURCED`가 없으면 기본 `~/.colab-v2-test.env` 또는 지정 파일을 source한다. CI 플래그도 파일이 존재하면 로딩을 막지 않는다.
- 따라서 wrapper가 새 DB URL과 SKIP_UPGRADE 제거를 확정해도 파일의 같은 변수가 뒤에서 이긴다. schema-diff는 그 URL에 실제 upgrade head를 실행한다.
- 수정: wrapper에서 테스트 환경 파일 로딩을 명시적으로 차단하고, DB_DIR/네트워크/skip 등 실제 입력을 CI 계약에 맞춰 확정한다. 외부 파일의 sentinel URL/skip 값이 자식에 반영되지 않는 음성 시험이 필요하다. 실제 운영 URL을 시험에 쓰지 않는다.

### P2 — 두 postgres를 중첩 확보해 슬롯 한도1에서 자기 대기한다

- 위치: `gates/tools/ci-schema-diff.sh` `pg_start ci-schema-diff` 이후 자식 호출; `gates/tools/schema-diff.sh:145`; `gates/tools/_pg.sh` `pg_slot_acquire`와 기본 wait900초.
- wrapper가 적용 DB 컨테이너 슬롯을 잡은 채 자식 schema-diff가 선언 DB 컨테이너 슬롯을 추가로 요구한다. `COLAB_PG_MAX_CONCURRENT=1`이면 슬롯이 절대 풀리지 않아 준비 실패한다. wrapper 여러 개가 한도를 모두 점유해도 같은 구조다.
- CI 기본4/단일 wrapper는 이 조건이 아니다. 현재 문제는 환경 입력을 상속하는 wrapper 계약이 두 슬롯 요구를 밝히거나 보장하지 않은 점이다.
- 수정: 독립 CI 작업의 두 컨테이너 자원 요구를 명시하고, 최소 한도/동시 wrapper 처리 방식을 결정한다. 한도를 무조건 높여 공유 자원 규약을 우회하지 않는다.

## 확인된 적정 사항과 검증 한계

- parent와 child의 trap은 별도 Bash 프로세스에 있으므로 child trap이 parent PGC 변수를 덮어써 parent 컨테이너를 직접 지우는 구조는 아니다. `_pg.sh` source가 각 프로세스 PGC를 초기화한다. 정상/오류 종료 실제 잔존 컨테이너 계수는 이번 리뷰에서 측정하지 않았다.
- API 키 검사 제거 전에도 `COLAB_HARNESS_EVAL_EXEMPT=1`이었다. 실제 모델 실행을 새로 빼는 변경은 아니다. 새 runner/gate selftest 호출과 면제 건수 노출이 추가됐다.
- `ci-filter-check.py`는 실제 실행 증명이 아니라 문자열/구조 근사 검사다. 새 회귀 경로 존재 검사도 그 한계 안에 있다. 파일 자체가 근사임을 출력하므로 이것만 원격 CI 성공 증거로 쓰지 않는다.
- workflow harness 필터의 옛 주석(4경로 변경 때 실과제/모델 호출)은 현 면제 설명과 맞춰 정정할 수 있다. 기능 반려 사유는 아니다.
- migration 파일 수정0이며 wrapper는 기존 두 체인의 head upgrade와 schema-diff를 재사용한다. revision 체인 정합 및 실제 적용 성공은 미검증.
- 메인이 보고한 runner selftest7/7, gate selftest4/4, 명시면제20건은 메인 측정값이다. 본 리뷰는 재실행하지 않았다. 실제 모델 eval, 원격 CI 변경 후 성공, 제품 E2E 성공을 주장하지 않는다.

## Spec 대조

- 충족 방향: 기존 검사기 재사용, API 키 없는 명시 면제, 로컬/원격 성공 구분, 제품 범위 유지.
- 미달: schema wrapper 격리 및 실 upgrade 검증, 기획 원본 공급, 19개 제품 후보 수용, agent-browser 여정, 전체 게이트와 dev 최종 판정. 전체 제품 마감은 아직 수용 대상이 아니다.
- 초과: 요청 없는 기능 추가 또는 제품 계약 변경은 검토 diff에서 발견하지 않았다.
- 근거: `dev-package/prd/specs/product-finish.md`; `dev-package/prd/rounds/R-PRODUCT-FINISH.md`; `.github/workflows/ci.yml`; `gates/tools/ci-filter-check.py`.

코드 수정·게이트 실행·운영 접촉0. 읽기 전용 수용 검토이며 위 두 지적은 호출 흐름으로 확인했다. 미측정 실행 결과를 생성하지 않았다.

## 수정 후 재검토

- 메인 수정 파일 재읽기: `COLAB_TEST_ENV_SOURCED=1`이 첫 부분에 확정됐다. 기존 P1의 홈 env 재로딩 경로는 코드상 해소. sentinel 음성 실행은 여전히 미측정.
- 슬롯1 즉시78 거부가 추가됐다. 다만 `_pg.sh`는 0/비숫자를1로 정규화하므로 문자열 `==1`만으로는 같은 자기대기를 막지 못한다. 양의 정수 >=2 계약 검증이 필요하다. 여러 wrapper 동시 실행 제한도 명시해야 한다.
- 추가 P2 입력 정밀화: `COLAB_DB_DIR`가 상속되면 현 저장소 두 체인 대신 외부 fixture를 검사한다(`schema-diff.sh:42`). CI wrapper는 `$REPO_ROOT/db`로 확정해야 한다.
- `_venv.sh`의 `COLAB_GATE_VENV`/`COLAB_GATE_REQUIREMENTS`는 selftest override다. wrapper CI 도구 정본을 확정하려면 해당 값도 저장소 경로로 확정해야 한다. `COLAB_ALEMBIC` 자체는 wrapper가 덮어쓰므로 직접 상속 문제 없음.
- `COLAB_PLATFORM_DB_URL_FILE`/`COLAB_AI_DB_URL_FILE`가 상속되면 두 URL 판독기의 direct/file 공존 거부가 발동한다. 파일 읽기 전에 거부하므로 운영 파일로 우회하는 경로는 아니지만 일회용 검사 준비를 실패시킨다. wrapper에서 제거 권고. 원본 홈 env 또는 자격 파일은 읽지 않았다.
- `COLAB_PG_NETWORK`가 상속되면 기본 bridge라는 wrapper 설명과 달라진다. `COLAB_PG_IMAGE`도 환경에서 선택된다. CI wrapper가 지원하는 네트워크/이미지 계약을 정하고 자식까지 동일하게 확정해야 한다.
- 갱신 판정: 기존 P1 수정 확인. 나머지 입력/슬롯 계약 정정 및 실제 성공/실패 cleanup 확인 후 schema wrapper 수용 가능. eval 변경의 기능상 추가 반려 사유는 발견하지 않았다.
