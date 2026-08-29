# Stage 2 착수 전제 3건 — 실행 기록

- 시점 = 2026-08-29 · 브랜치 `env/stage2-prereq`
- 대상 = `sessions/STAGE2-READINESS-AUDIT.md §5` 의 블로커 1·2·3
- 성격 = 환경·시험 뼈대만. 제품 코드 무변경

## 1. `services/ai-service/.venv` 신설

```
uv venv .venv && uv pip install -r requirements.txt -r requirements-dev.txt
```

- 실측 = 환경변수 없이 **72 passed · 26 errors** (감사 문서와 일치)
- 26건은 전부 `COLAB_AI_TEST_DICT_DB_URL` 부재로 `conftest.py` 가 **fail 로 떨군 것** — skip 아님
- `ai-no-lineage-write` 게이트가 이 디렉터리의 모든 텍스트를 훑지만 개발 의존 추가 뒤에도 green (아래 §4)

## 2. `db/ai` 체인 일회용 DB 부트스트랩 신설

- 신규 = `services/ai-service/tests/fixtures/setup-db.sh` (`core-api` 대응물과 **같은 규약** · 다른 것은 체인뿐)
- 하는 일 = ① 소유자 롤 → `db/ai/schema.sql` ② 시드 둘(`k2_ontology_seed.sql` · `k2b_concept_graph_seed.sql`)
  ③ 앱 롤 `colab_ai_app` **SELECT 뿐** · 쓰기 권한이 붙으면 그 자리에서 죽는다
- 앱 롤을 `colab_app` 으로 하지 않은 이유 = 한 자격증명이 두 체인을 다 여는 순간을 만들지 않는다
  (정본 = `infra/staging/db-bootstrap.sh` 의 `app-grants` 주석)
- 출력 = **마지막 한 줄의 접속 URL 하나뿐.** 값은 문서·로그에 남기지 않는다
- 일회용 규칙 준수 = `--rm` · `--tmpfs` · `PGDATA` 지정 · **호스트 포트 미공개**(컨테이너 IP 로만 접속)

## 3. 시험 환경변수 배선

- 자리 = 홈의 **`~/.colab-v2-test.env`**(`0600`). `~/.colab-v2-staging.env` · `~/.colab-v2-staging-backup.env` 와 같은 관행
- 담은 키 5 = `COLAB_CORE_TEST_SUBJECTS_FILE` · `COLAB_REFERENCE_DATA` · `COLAB_CORE_TEST_DATABASE_URL`
  · `COLAB_PIPELINE_DB_URL` · `COLAB_AI_TEST_DICT_DB_URL`
- 쓰는 법 = `set -a; . ~/.colab-v2-test.env; set +a`
- ⚠ **DB URL 세 줄은 일회용 컨테이너(tmpfs)의 값이다.** 컨테이너를 지우거나 호스트를 껐다 켜면 죽는다 —
  다시 만든 뒤 각 체인의 `setup-db.sh` 가 찍는 한 줄로 덮어쓴다. 그 절차는 파일 머리에 적혀 있다
- 반영 문서 = `RESTART.md §2-④` · `services/ai-service/README.md`

## 4. 실측 (2026-08-29 · 이 브랜치)

| 대상 | 값 | 조건 |
|---|---|---|
| core-api | **471 passed** | env 5종 source |
| pipeline-worker | **160 passed** | 〃 |
| viz-render | **119 passed** | 〃 |
| ai-service | **98 passed** | 〃 (미배선 시 72 passed · 26 errors) |
| 게이트 | **green 25 · red 2** | `./gates/run.sh all -j 6` |

- red 2 = `schema-diff` · `work-item-consistency` — **기준선과 같다. 상태 변화 없음**
- frontend 277 은 이번 회차에 재측정하지 않았다 — **`[미확인]`**. 푸는 법 = `cd frontend && pnpm test`

## 5. `[미확인]` · 사람의 자리

- 일회용 컨테이너 둘(`a2_pg` · `ai_pg`)을 **켜 둔 채로 넘긴다** — 지우면 위 env 세 줄이 죽는다.
  세션을 닫을 때 `RESTART §4` 체크리스트대로 지우고, 다음 회차에 다시 만든다
- `schema-diff` · `work-item-consistency` 는 이 레인의 범위 밖이다 (감사 문서 §5 의 6번 항목)
