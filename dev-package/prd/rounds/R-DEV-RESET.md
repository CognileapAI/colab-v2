# R-DEV-RESET — dev 전면 초기화와 참조 데이터 화면 재적재

입력 intent: `dev-package/intent/2026-09-13-dev-reset-reference-scenario.md` · 확정 2026-09-13(Ted 판정 ㈎ 1건 ＋ 에이전트 확정 8건).
등록표 정본: `dev-package/reports/reference-data/2026-09-13-inventory-v2.md` §5 ＋ §5-6.
기점: `worktree-intent-dev-reset-scenario` HEAD `28439223`(origin/main 대비 앞 1 · 뒤 0).
이 파일은 부트스트랩에서 읽는 유일한 문서다(`CLAUDE.md §1`). 다른 문서는 상대경로 ＋ 앵커 문자열로만 따라간다.

## 1. 회차 목적

- dev 에 쌓인 검증용 데이터를 전면 제거하고, 시나리오의 시작 상태를 「초기화 도구 1회 실행 직후」 한 지점으로 고정한다.
- 실물 참조 데이터를 화면 조작으로 재적재해 프로젝트 4 · 데이터셋 28 · 계보 간선 18 을 dev 에 세운다.
- 그 조작 절차를 단계·입력값·기대 화면이 적힌 체크리스트 문서로 레포에 남겨 재실행 가능하게 한다.

## 2. 확정 결정 요약 (intent 원본에 근거 · 재개봉 금지 `.claude/rules/colab-rules.md §8`)

Ted 판정
1. dev 기존 데이터는 검증용이므로 전부 삭제한다.
2. 최소 구성 = 프로젝트 4개(precipitation · vegetation · drought · 포멧테스트).
3. 소유 = 고려대학교 수문학 연구실(전창현 교수).
4. 투입 경로 = 브라우저 화면 조작. 백엔드 시딩·DB 삽입·API 직접 호출을 쓰지 않는다.
5. 그 과정을 재실행 가능한 시나리오로 남긴다.
6. 사전 백업을 하지 않는다 — 임시 데이터다.
7. 클린 수준 ⓑ 완전 초기화 — 두 DB 스키마 재생성 ＋ 버킷 접두사 2개 비우기.
8. 가뭄 자료 = 데이터셋 2건(SPI-4weeks · SPEI-4weeks) · 계보 0간선.

에이전트 확정(근거는 intent 「판정 결과」 절)
9. 포멧테스트는 데이터셋당 대표 파일 1건만 올린다(level 데이터 3개 프로젝트는 전건).
10. hdf5 폴더의 실물은 hdf4 — 데이터셋 이름 `hdf4` ＋ 설명란에 폴더명 병기.
11. 학회 발표 자료 폴더는 적재하지 않는다.
12. 삭제 수단 = dev 전용 초기화 도구 1회 실행(화면 삭제는 501 이라 불가).
13. 연구실 행 이름이 대상과 일치하면 재사용, 아니면 그 단계만 운영 SQL 이고 계정 생성부터 화면.
14. 시나리오는 사람 체크리스트 문서 — 브라우저 자동화 도입은 별도 대장 항목.
15. 원본 다건은 데이터셋 1건에 파일 여러 개로 묶는다.
16. HSR 격자 정본은 npy 위경도 쌍.
17. 타일별 분리(tif 2 · hdf 2)는 데이터셋당 기준 격자 파일 2건 상한에 따른 분리다.

## 3. 진입조건

| # | 조건 | 닫는 법 |
|---|---|---|
| ㄱ | `integration/r-dev-reset` 이 `main` tip 기점으로 서 있고 intent 커밋 `28439223` 이 그 위에 있다 | 오케스트레이터가 브랜치를 만든다(§8) |
| ㄴ | 레인 시작 전 `service-tests-core-api` 단독 green 1회 | `bash gates/run.sh service-tests-core-api` |
| ㄷ | `[미확인]` dev 현재 데이터셋·파일·S3 객체 계수 | 읽기 전용 계수 1회(§5 WU-R2 1단계) — `colab_backup` 롤 또는 API `listDatasets` |
| ㄹ | `[미확인]` 마지막 배포의 `deploy_doctor` ⑥(스키마 head · 서버 저장소 트리)이 ✗ 로 남아 있다 | dev 재배포로 서버 저장소 트리를 동기화한 뒤 doctor 1회 · 근거 `dev-package/reports/r-login-backoffice/task5/deploy-3-verify.md` |
| ㅁ | 원천 드라이브 `03 Reference-Data` 가 붙어 있다(WU-R3 만 해당) | 사람이 연결 확인 |

- ㄷ·ㄹ 은 WU-R1(코드 작업)의 진입조건이 아니고 WU-R2 실행의 진입조건이다.
- ㄹ 이 닫히지 않으면 WU-R2 의 완료 정의(15/15 한 번의 실행)가 성립하지 않는다.

## 4. 실측 근거 (레인이 다시 재지 않는다)

- 마이그레이션 head — platform `db/platform/versions/0031_search_evidence.py` · ai `db/ai/versions/0007_merge_topic_vocab_and_rc7_category.py`(리비전 그래프 계산 실측 2026-09-13).
- 마이그레이션 적용 자리 — EC2 위 `infra/dev/up.sh` 의 ① 단계. 축자 「`dc --profile migrate run --rm migrate-platform`」 ＋ 같은 줄의 `migrate-ai`. 앱 이미지에 alembic 이 없고 `infra/dev/migrator/Dockerfile` 의 별도 이미지가 소유자 롤로 돈다.
- 스키마의 정본 — `infra/dev/db-bootstrap.sh` 머리말 축자 「스키마는 여기서 만들지 않는다 — alembic 체인이 정본이다.」 ⟹ **RLS 정책은 마이그레이션이 만든다.**
- 부트스트랩이 만드는 것 — 롤·DB·GRANT 뿐. `infra/staging/db-bootstrap.sh` 의 `app-grants` 가 `services/core-api/ops/app-role.sql` 을 먹이고 `colab_ai_app` 에 `GRANT SELECT ON ALL TABLES` ＋ `ALTER DEFAULT PRIVILEGES` 를 건다. ⟹ **스키마 재생성 뒤 `app-grants` ＋ `account-admin` 재실행이 필수다**(`GRANT ON ALL TABLES` 는 그 시점의 표에만 걸린다).
- 접속 — 소유자 롤 접속 문자열은 EC2 `$COLAB_DEV_SECRETS_DIR` 의 `platform-owner-db.url` · `ai-owner-db.url`(각 0600). 값은 argv·로그에 싣지 않고 **파일 경로로만** 받는다.
- S3 클라이언트 — `services/core-api/src/colab_core/kernel/s3.py` 의 `S3Client`. SigV4 는 표준 라이브러리 자작(`kernel/sigv4.py`)이고 boto3 를 쓰지 않는다(`.claude/rules/s3-upload.md` 축자 「SigV4 는 표준 라이브러리 자작이다」). **새 도구도 같은 클라이언트를 쓴다.**
- 승인 계획 패턴 — `services/core-api/src/colab_core/app/storage_maintenance_cli.py` 가 `--apply-approved` ＋ `--plan` ＋ `--plan-sha256` ＋ `--expected-bucket`·`--expected-region`·`--expected-code-sha`·`--expected-image-config-id` 를 요구하고, 계획 파일이 실행자 소유 mode 0600 인지 `_private_plan` 이 검사한다.
- `deploy_doctor` 15 항목 — ① 운영자 자격증명 ② 데이터 버킷 설정 ③ 웹 버킷 ④ DB 연결(platform) ⑤ DB 연결(ai) ⑥ 스키마 head(platform) ⑦ 스키마 head(ai) ⑧ RLS 전수(살아 있는 DB) ⑨ 앱 롤 속성 ⑩ 5 단위 헬스 ⑪ 앱 자격증명 출처 ⑫ 환경 짝 ⑬ 진입·라우팅 ⑭ 백업 24h ⑮ 실행 sha ∈ main. **데이터 행을 보는 항목이 없고 ⑭ 만 `_ops/backups/` 객체에 걸린다.**
- 삭제 규칙 축자 — `.claude/rules/deploy.md` 「깨뜨리면 안 되는 것」 11번: 「**데이터셋 행을 지우는 유일한 자리는 `services/core-api/ops/purge_datasets.py` 다.** **고정 id 목록 ＋ `--yes-delete`** 이고 ⛔ **`PLAN-SoT §9` 행과 Ted 의 명시 GO 없이 실행하지 않는다**」.
- 같은 절 10번 축자 — 「**「없다」는 경계가 실린 경로로만 판정한다.**」 · 「`ops/purge_datasets.py` 는 트랜잭션 안에서 `app.current_lab` 을 먼저 걸고, 안 걸면 **DELETE 가 0행에 조용히 성공**한다」.
- 버킷·접두사 — 데이터 버킷 `colab-platform-data-dev` · 접두사 `uploads/` · `previews/` · `_ops/backups/dev/`. 환경변수 이름은 `COLAB_CORE_S3_BUCKET`·`COLAB_CORE_S3_REGION`·`COLAB_CORE_STORAGE_MODE`.
- 화면 삭제 부재 — `deleteDataset` 은 서버가 501(`services/core-api/src/colab_core/app/routes/not_implemented.py`), 화면 호출 자리 0건.
- 연구실 행 2건 — `0000000000000000000000000A` 고려대학교 수문학연구실 · `…B`. 계정은 연구실이 먼저 있어야 붙는다(`services/core-api/ops/provision-account.sql`).

## 5. WU 표

| WU | 이름 | 성격 | 선행 |
|---|---|---|---|
| WU-R1 | 규칙 예외 등재 ＋ dev 전용 초기화 도구 | 레인 1개(`lane-worker`) | 없음 |
| WU-R2 | dev 초기화 실행 | 오케스트레이터 ＋ Ted · 레인 작업 아님 | WU-R1 병합·dev 배포 ＋ Ted 명시 GO |
| WU-R3 | 화면 투입 시나리오 ＋ 실투입 | 문서 레인 1개 ＋ 사람 실행 | WU-R2 |

### WU-R1 — 규칙 예외 등재 ＋ dev 전용 초기화 도구

**(a) 결정 등재 ＋ 규칙 개정**

- `PLAN-SoT §9 〈N〉` 1행 신설. `〈N〉` 을 하드코딩하지 않는다 — 병합 직전 `bash dev-package/prd/tools/max-decision.sh` 로 재실측해 최대값 +1.
- 등재문 초안은 §9-A.
- `.claude/rules/deploy.md` 의 11번 항목 뒤에 예외 문단을 붙인다(11번 문면은 무수정). 제안 문안 —
  > ⭑ ⟨증보 2026-09-13 · `〈N〉`⟩ **dev 한정 예외 — 환경 전면 초기화는 `services/core-api/ops/reset_dev_environment.py` 하나다.** 조건 넷을 모두 만족해야 실행된다 — ⑴ `--target dev` ＋ `--yes-reset-dev` ⑵ 버킷 이름이 `colab-platform-data-dev` 와 일치 ⑶ 두 DB 식별자가 dev 값과 일치 ⑷ 계획 파일의 키가 `uploads/`·`previews/` 접두사 안에만 있다. **`_ops/` 는 무접촉이다**(지우면 `deploy_doctor` ⑭ 가 red 다). staging·prod 식별자에서는 거부한다. 데이터셋 행 단위 삭제는 그대로 `purge_datasets.py` 뿐이고 이 도구가 그 자리를 대신하지 않는다. ⛔ `PLAN-SoT §9` 행과 Ted 의 명시 GO 없이 실행하지 않는다 — **승인은 1회 소진이다.**

**(b) 도구 신설 — `services/core-api/ops/reset_dev_environment.py`**

- 이름 근거 = 기존 `ops/` 관례(`purge_datasets.py`·`deploy_doctor.py`·`s3_doctor.py`·`operator_audit_export.py`) = `동사_명사.py` snake_case. 배포 이미지에 실리지 않는 제품 패키지 밖 자리.
- 거부 조건(하나라도 어긋나면 비영 종료 · 아무것도 지우지 않는다) — `--target dev` 부재 · `--yes-reset-dev` 부재 · 버킷 이름 불일치 · DB 식별자 불일치 · staging·prod 식별자 · 계획 파일에 `_ops/` 접두사 키 1건이라도 포함 · 계획 파일 sha256 불일치 · 계획 파일이 실행자 소유 0600 아님.
- 접속은 `--db-url-file` · `--ai-db-url-file`(0600 파일 경로)로만 받는다. 값은 argv·로그·예외 어디에도 싣지 않는다(`deploy_doctor` 규약과 같다).
- DB 절차 = 두 체인 각각 ⑴ 현재 계수 기록 → ⑵ `DROP SCHEMA public CASCADE` ＋ `CREATE SCHEMA public` → ⑶ alembic upgrade head(`infra/dev/up.sh` 의 migrate 러너와 같은 자리·같은 이미지) → ⑷ `infra/dev/db-bootstrap.sh app-grants` ＋ `account-admin` 재실행 → ⑸ `verify`. **⑷ 를 빠뜨리면 앱 롤에 권한이 없어 서비스가 뜨지 않는다**(§4 근거).
- S3 절차 = `uploads/`·`previews/` 접두사를 exact-key 목록으로 나열해 계획 파일(JSON ＋ sha256)에 쓰고, 그 계획의 키만 삭제한다. `--recursive` 프리픽스 삭제를 쓰지 않는다(선례 `PLAN-SoT §9 〈354〉`). 클라이언트는 `kernel/s3.S3Client`.
- 출력 = 실행 전/후 계수(표별 행수 · 접두사별 객체 수)를 둘 다 찍는다. 부분 실패가 하나라도 있으면 비영 종료한다.
- ⛔ 이 WU 에서 도구를 실환경에 대고 돌리지 않는다. 실행은 WU-R2 다.

**(c) 시험 — fail-closed 픽스처(DB·AWS 없이 돈다)**

- 모델 = `services/core-api/tests/test_purge_datasets_guard.py`(`importlib.util.spec_from_file_location` 로 `ops/` 파일을 직접 적재 · 가드만 잰다 · 실집행 미재현).
- 새 파일 `services/core-api/tests/test_reset_dev_environment_guard.py` 최소 6건 — ⑴ `--yes-reset-dev` 부재 → 거부 ⑵ 버킷 이름 불일치 → 거부 ⑶ 계획에 `_ops/` 키 → 거부 ⑷ staging 식별자 → 거부 ⑸ prod 식별자 → 거부 ⑹ dry-run 이 기본값이고 아무것도 지우지 않는다.
- 각 시험은 **RED 를 먼저 확인**한 뒤 구현한다(green 으로 시작하는 시험은 오라클이 아니다 · `CLAUDE.md §4`).

**(d) 등재**

- `dev-package/work-items.yaml` 에 항목 블록 3건 추가(§9-C 붙여넣기용). `stage: after_stage2`.
- `CLAUDE.md` 의 `<!-- work-items:after_stage2 -->` 괄호에 새 id 를 사전순으로 넣는다 — 게이트 `work-item-consistency` ㈕ 가 대조한다.
- `dev-package/03-HANDOFF.md §1` 갱신 5줄 이내.

**완료 정의** — 다섯을 모두 만족한다. ⑴ `service-tests-core-api` 단독 green **3회 연속** ⑵ `exec-bit` green ⑶ `work-item-consistency` green ⑷ 새 시험 6건이 구현 전 RED 였음이 로그로 남는다 ⑸ `.claude/rules/deploy.md` 예외 문단과 `PLAN-SoT §9 〈N〉` 행의 문면이 서로 같은 값을 말한다.

### WU-R2 — dev 초기화 실행

- **레인 작업이 아니다.** 오케스트레이터가 절차를 밟고 Ted 가 GO 를 준다.
- 선행 = WU-R1 이 `main` 에 병합되고 dev 에 배포됨(`docs/DEPLOY.md`) ＋ Ted 명시 GO 가 `PLAN-SoT §9` 행에 기록됨.
- 절차 —
  1. 읽기 전용 계수 1회 — 경계가 실린 경로(`colab_backup` 롤 또는 API `listDatasets`)로 데이터셋·파일 행수, 운영자 키로 `uploads/`·`previews/` 객체 수를 파일에 고정한다.
  2. EC2 호스트에서 도구 1회 실행(`--target dev --yes-reset-dev` ＋ 계획 파일).
  3. 실행 후 계수 = 0 을 같은 경로로 확인한다.
  4. `deploy_doctor` 15/15 를 **한 번의 실행**으로 확인한다. 부분 실행 둘을 합치지 않는다.
  5. `PLAN-SoT §9` 에 실행 sha · 삭제 계수 · doctor 결과를 기록한다.
- **완료 정의** — 데이터셋 0건(경계 실린 경로 확인) ＋ `uploads/`·`previews/` 객체 0 ＋ `_ops/` 객체 수 무변 ＋ `deploy_doctor` 15/15 한 번의 실행 ＋ 원장 행 1건.
- 버저닝 탓에 삭제 후에도 이전 판이 30일 남는다(즉시 소멸 아님 · `dev-package/S3.md`).

### WU-R3 — 화면 투입 시나리오 ＋ 실투입

- 산출 = `dev-package/scenarios/dev-minimal-data-setup.md`(신설 · 레포에 `scenarios` 디렉터리 부재를 실측 확인).
- 문서 구성 = 단계 · 입력값 · 기대 화면 3열. 순서 —
  1. 로그인.
  2. 연구실 확인 — 기존 행 이름이 고려대학교 수문학 연구실이면 재사용, 아니면 그 단계만 운영 SQL(연구실 생성 화면 부재 · 결정 13).
  3. 계정 생성 화면(`frontend/src/routes/AccountAdminPage.tsx`).
  4. 프로젝트 4건 생성 — precipitation · vegetation · drought · 포멧테스트.
  5. 데이터셋 28건 — 행마다 프로젝트 · 데이터셋 이름 · 파일 glob · 격자 쌍 · 부모. 값의 정본은 `dev-package/reports/reference-data/2026-09-13-inventory-v2.md` §5-1~§5-4 표이고 계수는 §5-6(28 / 18)이다.
  6. 계보 설정 18간선 — precipitation 4 · vegetation 7 · drought 0 · 포멧테스트 7.
  7. 미리보기 확인 5종(grib · nc · bin · tif · hdf4) — 그려지지 않는 포맷은 이름으로 남긴다. 조용히 넘기지 않는다.
  8. `deploy_doctor` 15/15 한 번의 실행.
- 원천 = 외부 드라이브 `03 Reference-Data`(읽기 전용 · 무수정). 문서에는 드라이브 안 상대경로만 적는다.
- 투입은 화면 조작이다 — 백엔드 시딩·DB 삽입·API 직접 호출을 쓰지 않는다(결정 4). `infra/staging/load-seed.py` 를 쓰지 않는다.
- **완료 정의** — dev 목록 화면에서 데이터셋 28건이 보이고 계보 간선 18건이 서며 미리보기 5종의 렌더 결과가 기록된다(미렌더 포맷은 이름으로 열거). 되돌리는 수단은 WU-R2 도구뿐이므로 오입력은 그대로 남는다.

## 6. 레인 규약

- 레인은 `Agent(subagent_type: "lane-worker", isolation: "worktree")` 로 스폰한다. 손으로 만든 형제 워크트리를 쓰지 않는다.
- **레인 하나 = 작업 하나.** 리베이스·조건 수정·구현·전수를 한 지시문에 싣지 않는다(`CLAUDE.md §5-b`).
- 레인 시작은 `git checkout -B <lane> origin/integration/r-dev-reset`. 워크트리 기본 기준이 `origin/main` 이라 ff-only 가 실패한다.
- 반복 검증은 `service-tests-core-api` 단독 게이트. 전수는 병합 직전 1회.
- 새 `.sh` 를 만들면 `git update-index --chmod=+x <파일>` 후 커밋(게이트 `exec-bit`).
- `〈N〉` 을 하드코딩하지 않는다 — 병합 직전 재실측.
- 최종 메시지에 `WORKTREE=… BRANCH=…` 를 적는다. 병합·원격 삭제·태그 push 는 레인이 하지 않는다.
- **지시가 실물과 어긋나면 멈추고 보고한다.** 우회하지 않는다.
- **기존 오류를 발견하면 「기존」이라 적지 말고 그 오류가 어느 검사(게이트·Dockerfile·배포)에 걸리는지 적는다.** 「main 과 동일」은 수용 근거가 아니다.
- 새 워크트리는 `node_modules`·`.venv` 를 승계하지 않는다 — `services/core-api` 는 `uv venv .venv && uv pip install -r requirements.txt -r requirements-dev.txt` 뒤 `uv pip install -e .` 까지 한다. 시험 환경 파일은 `gates/run.sh` 가 스스로 source 한다.
- 작업 시작 전 `python3 scripts/agent-bridge.py lifecycle begin --role lane-worker …`, 종료 시 `handoff`(`docs/development/lifecycle-evidence.md`).

## 7. 운영 경계

- DB 접촉은 읽기 전용이 기본이다. 쓰기·삭제는 승인된 WU 안에서만.
- 비밀 값(접속 문자열 · 키 · 토큰)을 출력·문서·커밋에 싣지 않는다. 파일 경로로만 받는다.
- **거부가 올바른 동작이다** — 조건이 어긋나면 부분 실행하지 않고 멈춘다.
- 삭제 대상은 조건문이 아니라 목록으로 고정한 뒤 실행한다.
- 비가역·파괴적·사용자 노출 행동 앞에 advisor 게이트 ③ 를 붙인다.
- staging 에서 완료 판정을 하지 않는다. prod 는 범위 밖이다.

## 8. 브랜치 처리 (오케스트레이터가 한다)

- 현재 intent 커밋 `28439223` 은 `worktree-intent-dev-reset-scenario` 위에 있고 `origin/main` 대비 앞 1 · 뒤 0 이다.
- 조치 = 그 HEAD 에서 `integration/r-dev-reset` 을 만들어 push 하고, 레인은 그 브랜치를 기점으로 삼는다(`docs/BRANCHING.md` 축자 「`integration/r-N` 은 `main` tip 에서 따고, `main` 으로는 **ff-only 한 줄**」).
- 병합 = `main` 으로 ff-only 한 줄. 병합 뒤 `integration/r-dev-reset` 과 `worktree-intent-dev-reset-scenario` 를 로컬·원격에서 삭제한다.
- 레인 브랜치 `lane/wu-r1-*` 는 통합에 rebase ＋ ff 로 얹은 즉시 삭제한다.

## 9. 붙여넣기용 초안

### 9-A. `PLAN-SoT §9 〈N〉` 등재문 초안 (dev 한정 예외)

> **〈N〉 dev 환경 전면 초기화 도구 신설 — 접두사 삭제·스키마 재생성의 dev 한정 예외 (2026-09-13)**
> ㉮ **문제** — 규칙은 데이터셋 행의 목록 고정 삭제만 허용하고(`.claude/rules/deploy.md` 11번), 접두사 비우기·DB 재생성 경로가 없다. `d8_activity`·`d8_download` 는 `deny_update_delete` 트리거가 DELETE 를 막아 행 삭제로는 비워지지 않는다.
> ㉯ **결정** — dev 한정으로 `services/core-api/ops/reset_dev_environment.py` 하나를 신설한다. 조건 넷(`--target dev` ＋ `--yes-reset-dev` · 버킷 이름 일치 · DB 식별자 일치 · 계획 키가 `uploads/`·`previews/` 안)을 모두 만족할 때만 실행되고, 하나라도 어긋나면 아무것도 지우지 않고 비영 종료한다.
> ㉰ **무접촉** — `_ops/`(백업). 지우면 `deploy_doctor` ⑭ 가 red 다.
> ㉱ **불변** — 데이터셋 행 단위 삭제의 유일한 자리는 `purge_datasets.py` 그대로다. staging·prod 에는 적용하지 않는다.
> ㉲ **승인** — 도구 신설과 실행은 별개다. 실행은 Ted 의 명시 GO 와 이 §9 행이 있어야 하고 **승인은 1회 소진이다**(선례 `〈354〉`·`〈365〉`·`〈366〉`).
> ㉳ **근거** — intent `dev-package/intent/2026-09-13-dev-reset-reference-scenario.md` · 라운드 `dev-package/prd/rounds/R-DEV-RESET.md`.

### 9-B. 회차 등재문 초안

> **〈N+1〉 R-DEV-RESET 회차 — dev 전면 초기화와 참조 데이터 화면 재적재 (2026-09-13)**
> ㉮ WU-R1(도구·규칙 예외) → WU-R2(초기화 실행 · Ted GO) → WU-R3(시나리오 문서 ＋ 화면 실투입) 순서.
> ㉯ 목표 계수 = 프로젝트 4 · 데이터셋 28 · 계보 간선 18(정본 `dev-package/reports/reference-data/2026-09-13-inventory-v2.md` §5-6).
> ㉰ 완료 판정 = dev `deploy_doctor` 15/15 한 번의 실행 ＋ 목록 화면 28건 ＋ 미리보기 5종 결과 기록.
> ㉱ 통합 브랜치 `integration/r-dev-reset` · `main` 으로 ff-only.

### 9-C. 대장 블록 (`dev-package/work-items.yaml` 끝에 덧붙임 · 값은 착수 시 갱신)

```yaml
  - id: DR-1
    name: "dev 전용 초기화 도구 — 규칙 예외 등재와 fail-closed 가드"
    status: open
    stage: after_stage2
    owner: "운영 / core-api ops"
    entry_conditions: ["intent 2026-09-13 dev 초기화·재적재가 확정 상태다", "integration/r-dev-reset 이 main tip 기점으로 서 있다"]
    depends_on: []
    completion_def: "다섯을 모두 만족한다. ⑴ service-tests-core-api 단독 green 3회 연속 ⑵ exec-bit green ⑶ work-item-consistency green ⑷ 가드 시험 6건이 구현 전 RED 였음이 로그로 남는다 ⑸ .claude/rules/deploy.md 예외 문단과 PLAN-SoT §9 행의 문면이 같은 값을 말한다."
    evidence: ""
    deadline: null
    note: "도구를 실환경에 대고 돌리지 않는다 — 실행은 DR-2 다."
    sources: ["dev-package/intent/2026-09-13-dev-reset-reference-scenario.md", "dev-package/prd/rounds/R-DEV-RESET.md"]
  - id: DR-2
    name: "dev 초기화 1회 실행"
    status: open
    stage: after_stage2
    owner: "오케스트레이터 ＋ Ted"
    entry_conditions: ["DR-1 이 main 에 병합되고 dev 에 배포됐다", "Ted 명시 GO 가 PLAN-SoT §9 행에 있다"]
    depends_on: [DR-1]
    completion_def: "데이터셋 0건(경계 실린 경로 확인) ＋ uploads/·previews/ 객체 0 ＋ _ops/ 객체 수 무변 ＋ deploy_doctor 15/15 한 번의 실행 ＋ 원장 행 1건."
    evidence: ""
    deadline: null
    note: "비가역. 승인은 1회 소진이다."
    sources: ["dev-package/prd/rounds/R-DEV-RESET.md"]
  - id: DR-3
    name: "화면 투입 시나리오 문서와 dev 실투입"
    status: open
    stage: after_stage2
    owner: "문서 레인 ＋ 사람 실행"
    entry_conditions: ["DR-2 완료", "원천 드라이브 03 Reference-Data 연결"]
    depends_on: [DR-2]
    completion_def: "dev 목록 화면에서 데이터셋 28건이 보이고 계보 간선 18건이 서며, 미리보기 5종의 렌더 결과가 기록된다(미렌더 포맷은 이름으로 열거). 시나리오 문서가 단계·입력값·기대 화면 3열로 레포에 있다."
    evidence: ""
    deadline: null
    note: "화면 조작만 쓴다 — load-seed.py·API 직접 호출을 쓰지 않는다."
    sources: ["dev-package/reports/reference-data/2026-09-13-inventory-v2.md", "dev-package/prd/rounds/R-DEV-RESET.md"]
```

## 10. 범위 밖 (명시 제외)

- 학회 발표 자료 폴더 적재 · prod 배포 · staging 에서의 완료 판정.
- 새 기능 개발 — 데이터셋 삭제 화면 · 연구실 생성 화면 · 브라우저 자동화 도입.
- 화면에 없는 기능을 API 직접 호출로 대신하기.
- staging·prod 에 대한 초기화 도구 적용.
- 「기준 격자 파일 다건 허용」(데이터셋당 2건 상한 완화) — 별도 항목 후보.

## 11. 후속 항목 (이 회차에서 고치지 않는다)

- 서버 저장소 트리 동기화를 강제하는 자리가 없다 — `deploy_doctor` ⑥ ✗ 의 반복 원인.
- S3 고아 바이트를 치우는 주체가 없다(`dev-package/S3.md`) · 완결된 전송 원장 행이 안 지워진다.
- HSR 격자 정본이 레포 두 자리에 다르게 적혀 있다 — 한 자리 정리.
- `[미확인]` `DROP SCHEMA public CASCADE` 를 `colab_owner` 롤이 수행할 수 있는지(RDS 마스터는 `rds_superuser` 이지 진짜 슈퍼유저가 아니다) — WU-R1 착수 시 EC2 카탈로그 조회 1회로 닫는다.
- `[미확인]` 비운 상태에서 `deploy_doctor` 15/15 가 서는지의 실증 — 데이터 행을 보는 항목이 없다는 것까지는 코드 실측이고, 실제 15/15 는 WU-R2 에서 처음 확인된다.
