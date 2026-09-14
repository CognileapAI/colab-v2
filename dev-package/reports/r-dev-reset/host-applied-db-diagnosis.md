# 공용 적용 DB 소유자 진단 (읽기 전용 조사)

- 조사일 2026-09-13. 대상 = `~/.colab-v2-test.env` 가 가리키는 `schema-diff` 적용 DB(`COLAB_APPLIED_DB_URL_PLATFORM`·`_AI`). 어떤 DB·컨테이너·파일도 변경하지 않았다.

## 1. 적용 DB 접속 정보 (host/port/dbname 만)

- `172.17.0.7:5432` / `colab_platform_applied` — `gates/tools/schema-diff.sh` 가 읽는 `COLAB_APPLIED_DB_URL_PLATFORM` 대상(`~/.colab-v2-test.env:26`).
- `172.17.0.7:5432` / `colab_ai_applied` — 같은 파일 `COLAB_APPLIED_DB_URL_AI`(27행).
- user/password 는 이 문서에 적지 않는다.

## 2. 컨테이너 식별

- `docker ps` 대조 결과 `172.17.0.7` = 컨테이너 `colab_lane_applied`(이미지 `postgres:16-alpine`, 생성 `2026-09-12T05:17:10Z`, 조사 시점 기준 가동 27시간). 포트 미공개.
- 이름·생성 방식이 **staging 스택 패턴(`colab_v2_staging_*`, `docker-compose` 망 `colab-v2-staging_default`)과 다르다.** staging 의 실제 DB 는 `colab_v2_staging_pg`(`172.18.0.8`, 별도 망)이며 `colab_lane_applied` 는 기본 브리지(`172.17.0.0/16`) 위의 임시·테스트류 컨테이너(`colab_v2_gatepg_*`·`colab_applied_bugfix260912c`·`colab_v2_lanepg`·`colab_ai_t7_pg` 와 같은 계열)다.

## 3. alembic 스탬프 실측 (읽기 전용 `SELECT`)

- 표 이름이 `alembic_version` 이 아니라 체인별 `alembic_version_platform`·`alembic_version_ai`(`gates/tools/schema-diff.sh` 배선과 일치).
- `colab_platform_applied.alembic_version_platform` = `0032_private_owner_access`.
- `colab_ai_applied.alembic_version_ai` = `0007_merge_vocab_and_category`(플랫폼 문제와 무관, 변화 없음).
- 대조 — 이 문서를 쓰기 전날(2026-09-12) 작성된 `dev-package/reports/bugfix-260912/gate-db-rerun.md` §3 은 같은 컨테이너·같은 DB 의 스탬프를 `0030_merge_audit_and_backoffice`로 실측하며 **"다른 세션 소유"**라 적었다. 하루 사이 `0030` → `0032` 로 다시 전진했다 — 그 사이 최소 한 세션이 이 공용 DB 에 `alembic upgrade`를 실행했다.

## 4. `origin/local-stage` 병합 상태

- `git log --oneline -3 origin/local-stage` 최상단 커밋 `d5867e0f` "ST 온톨로지 소유권을 분리하고 삭제 경로를 차단한다".
- `0032_private_owner_access` 를 담은 커밋은 `75cd069b`("Ted 2026-09-13 비공개 소유자 접근과 품질 수치 검색 회귀를 수정한다") — 커미터 **Ted**, 일자 2026-09-13(오늘).
- `git branch -r --contains 75cd069b` = `origin/codex/deployment-policy` · `origin/local-stage` 둘뿐. `origin/main` 은 포함되지 않는다(`git merge-base --is-ancestor 75cd069b origin/main` → 조상 아님, exit 1).
- 즉 `local-stage`는 `main`에 **미병합**이고, 공용 적용 DB 는 그 미병합 브랜치의 최신 리비전으로 전진해 있다.

## 5. 판정

- **(a)** — 진단 결과 `colab_lane_applied`는 staging 운영 스택(`colab_v2_staging_pg`)이 **아니다**. staging 과 별개의 네트워크·이름 계열이므로 staging 과 혼동해 다루면 안 된다.
- **(b)** — `colab_lane_applied`는 이름·생성 경위·과거 조사문 모두에서 **전용 테스트/스크래치 DB** 로 확인된다. 그러나 "전용"이되 **소유자가 없는 공용 스크래치**다 — 2026-09-12 조사문도 "다른 세션 소유"라 적었을 뿐 특정 인격을 지목하지 못했고, 그 뒤로도 최소 한 세션이 임의로 전진시켰다. 같은 DB 를 여러 사본이 번갈아 `alembic upgrade`하는 구조 자체가 이번 충돌(0032)과 전날 충돌(0030) 두 번을 낸 원인이다(`gate-db-rerun.md §6` 이 이미 이 패턴을 후속 항목으로 지목).
- 결론 = **(b) 성격의 DB지만, 되돌리기(다운그레이드)는 권고하지 않는다.** 지금 이 순간에도 다른 세션이 `0032` 위에서 작업 중일 가능성을 배제할 근거가 없고(같은 DB 가 반복해서 "남이 방금 전진시킨" 상태로 발견됐다), 되돌리면 그 세션의 진행을 깨뜨린다. **비가역 조작이므로 이 조사에서 실행하지 않았다.**

## 6. 권고 절차 (실행하지 않음 — 제안만)

- **최선책(게이트 쪽 수정, 비파괴)** — `dev-package/sessions/DR-1a-local-proof.md §8`이 이미 실증한 절차를 표준 배선으로 승격한다. 즉 `schema-diff` 판정은 공용 상주 DB 대신 **회차 전용 일회용 적용 DB**를 그 자리에서 세워 쓴다.
  ```
  docker run -d --rm --name colab-v2-<회차>-applied --tmpfs /pgdata:uid=70,gid=70 \
    -e PGDATA=/pgdata/db -e POSTGRES_PASSWORD=<임의값> -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine
  # infra/staging/db-bootstrap.sh roles 로 역할 구성
  # ~/.colab-v2-test.env 사본에서 COLAB_APPLIED_DB_URL_PLATFORM·_AI 두 줄만 이 컨테이너로 교체(0600·레포 밖)
  COLAB_TEST_ENV_FILE=<사본> bash gates/run.sh schema-diff
  docker rm -f colab-v2-<회차>-applied   # 회차 종료 시 회수
  ```
  이 경로는 `colab_lane_applied`를 전혀 건드리지 않으므로 다른 세션과 충돌하지 않는다.
- **차선책(공용 DB 자체를 0031로 되돌리는 안, (b) 전제일 때만)** — 실행 전 반드시 어드바이저 게이트 ③(비가역 go/no-go)과 Ted 승인을 거친다.
  ```
  docker exec colab_lane_applied psql -U postgres -d colab_platform_applied \
    -c "select version_num from alembic_version_platform;"   # 실행 직전 재확인 — 0032 그대로인지
  # core-api venv 의 alembic 으로 다운그레이드 (COLAB_PLATFORM_DB_URL 을 이 컨테이너로 지정)
  alembic downgrade 0031_search_evidence
  ```
  다운그레이드는 `0032_private_owner_access`가 만든 스키마 변경(비공개 소유자 접근 관련 컬럼/제약)을 되돌리므로, 그 사이 이 DB 를 쓰는 다른 세션이 있으면 그 세션의 작업을 파손한다.

## 7. 미확인

- `0032`를 실제로 올린 세션의 정체 — git 커밋 저자(Ted)만 확인했고, 어느 에이전트 세션이 그 커밋을 이 컨테이너에 `alembic upgrade`했는지는 로그가 없어 특정할 수 없다.
- `origin/codex/deployment-policy` 브랜치의 현재 활성 여부 — 이 조사 범위 밖.
