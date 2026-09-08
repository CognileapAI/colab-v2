# CI `schema-gates` 잡 red 진단 — 2026-09-08

## 결론

`schema-gates` 잡은 **`schema-diff` 게이트의 red(준비 · exit 78)** 로 실패한다. 원인은 `.github/workflows/ci.yml`
`schema-gates` 잡이 적용 DB URL(`COLAB_APPLIED_DB_URL_PLATFORM`·`COLAB_APPLIED_DB_URL_AI`)을 만들어 넘기는 스텝을
**애초에 갖고 있지 않은 것**이다 — 러너가 일회용 postgres 를 세우고 `alembic upgrade head` 를 돌린 뒤 URL 을
export 하는 절차가 잡 정의에 없다(`.github/workflows/ci.yml:240-262`, 스텝은 체크아웃·파이썬 설치·캐시·게이트 실행 4개뿐,
DB 서비스·postgres 컨테이너 스텝 부재). 게이트 자신은 fail-closed 로 정상 동작 중이다 — 입력 미선언을 조용히
넘기지 않고 red 로 낸다(설계 그대로, `CLAUDE.md §4`).

## R-D 기인 여부 — 기존 결함, R-D 신규 아님

- `git diff --stat 18c0228..ccf76ec -- db contracts` = **빈 결과**(마이그레이션·계약 변경 0건). R-D 는 이 경로를
  건드리지 않았다.
- `schema-gates` 잡은 `if: needs.changes.outputs.db == 'true' || core-api == 'true'` 경로 필터가 있어
  최근 회차(2026-09-06~08 실측 20개 run)에서 대부분 `skipped` 였다 — 이번(ccf76ec)은 이 회차가 경로를
  건드려 **드물게 실제로 돌았을 뿐**이다.
- 전체 run 이력(163건) 중 `schema-gates` 가 `skipped` 아닌 회차 45건 전수 확인 — **cancelled 1건을 빼면
  전건 failure**. 최초 관측 2026-08-22(당시 원인은 다름 — `migration-single-head` 미구현, WU-D3 이전),
  같은 「적용 DB 미선언」red(준비) 패턴은 **2026-09-01 부터 관측**(run 33547725504 로그 동일 문구). ccf76ec 이전부터
  존재한 CI 배선 공백이다.
- `X-7`(`dev-package/work-items.yaml:3139`) 은 `service-tests (core-api)` 시험 1건을 다루는 별개 항목이고
  `schema-gates` 는 포함하지 않는다 — 이번 진단이 새 사실이다.

## 배포 가능성 영향

- `gh api repos/CognileapAI/colab-v2/branches/main/protection` — `required_status_checks` 키 **없음**.
  `schema-gates` 는 브랜치 보호 필수 검사가 아니고 `main` 병합을 막지 않는다.
- 완료 판정 정본(`CLAUDE.md` 완료 조건)은 「dev 배포 green + `deploy_doctor` 14/14」이고 이 게이트는 그 경로에
  들지 않는다 — GH Actions `schema-gates` 는 배포 파이프라인의 게이트가 아니다.
- 다만 **CI 상에서 스키마 드리프트를 실제로 검증한 적이 이 잡의 존재 기간 내내 없다** — 잔여 위험은 「드리프트가
  나도 CI 가 못 잡는다」는 커버리지 공백이지, 현재 `main` 이 드리프트 상태라는 뜻은 아니다(로컬 실측 별도 기록,
  `gates/README.md:176` 2026-08-27 두 체인 green).

## 로컬 재현

- `set -a; . ~/.colab-v2-test.env; set +a; COLAB_GATE_REPORT_DIR=dev-package/reports/R-D/ci-schema ./gates/run.sh schema-diff`
  → **red(준비 · exit 78)**, 사유는 CI 와 다르다 — `COLAB_ALEMBIC` 미선언(이 체크아웃 `gates/.venv`·
  `services/core-api/.venv` 에 `alembic` 실행 파일 부재, 워크트리 게이트 환경 미구성 상태). CI 부재 원인(적용 DB URL 자체 미선언)과
  실패 지점이 다르다 — 로컬은 「DB 는 가리켰으나 올릴 도구가 없다」, CI 는 「DB 조차 안 가리켰다」.
- staging 컨테이너(`colab_v2_staging_pg`, IP `172.18.0.2`)와 `~/.colab-v2-test.env` 의 적용 DB(`172.17.0.2/3`)는
  **다른 컨테이너** — 이번 로컬 재현은 staging 을 접촉하지 않았다.

## 선택지와 비용

1. `schema-gates` 잡에 일회용 postgres 서비스(또는 `docker run --rm --tmpfs`) 스텝 + `alembic upgrade head` +
   URL export 스텝을 추가 — 비용: CI 워크플로 편집 1건, gate 실행 시간 증가(로컬 실측 없음, `[미확인]`).
   이 잡이 원래 의도대로(README 설계) 판정을 내게 된다.
2. 현행 유지 — 비용: `schema-gates` 는 계속 red(준비)로만 찍히고 실제 판정은 로컬/수동 실행에 의존.
   배포 판정에는 영향 없으나 회차마다 「빨간 잡 3개(planning-gates·harness-eval·schema-gates)」가 반복 노출돼
   판정 대상 CI 상태를 읽기 어렵게 만든다.

## 권고

옵션 1(CI 배선 보완)을 WU 로 개설. 사유 — 게이트 자체 결함이 아니라 CI 배선 누락이고, `gates/README.md` 가
이미 설계를 명시했으므로 구현 비용이 작다.

## 조치 자리

**WU 개설 필요.** `X-7` 은 `service-tests (core-api)` 전용이라 병합 불가. `dev-package/work-items.yaml` 에
`schema-gates` CI 배선(적용 DB 스텝 부재) 신규 WU 를 별도로 올린다.

배포 판정에 영향: 없음 — `required_status_checks` 미설정으로 `main` 병합 비차단, `deploy_doctor` 경로 밖.
조치 자리: WU 개설 필요(`X-7` 과 별개 — schema-gates CI 배선 공백).
