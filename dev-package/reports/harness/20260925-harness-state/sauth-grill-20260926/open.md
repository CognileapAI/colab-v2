### 미해결 1 pty · 같은 사용자 재계산 경로의 축소 범위(Q2a)
- 판정: Q2a ⓒ 의 정제형 — 규칙 하나 「nonce · 소진 상태는 **행위가 일어나는 호스트의 root 0600 파일**(sudo 로만 읽힘)」. ship · reset = dev 호스트 `$REMOTE_OUT` 계열(reseed 선례 그대로) · purge = 같은 dev 호스트의 같은 디렉터리를 컨테이너에 `-v` 로 건다. DB 안 challenge 표는 두지 않는다. pty · 같은 사용자 재계산 경로는 더 좁히지 않고 「남는 경로」로 문서화하고 측정(인가 기록 건수 == 실행 건수)으로 잡는다.
- 확신: 중간
- 사실 확인: reseed nonce 는 원격 `$REMOTE_OUT/reset-challenge.json` 을 `ssh … sudo base64` 로 읽고 실행 자리에는 `nonceSha256` · `ackTokenSha256` 만 남긴다(`dev-package/tools/dev-reseed/stages.sh:211-223` · `:255-272`). purge 는 `main` 안에서 `import psycopg`(「컨테이너 안에만 있다」) 뒤 소유자 URL 로 접속(`services/core-api/ops/purge_datasets.py:99-129`) → 실행 자리는 EC2 컨테이너이고, DB 는 그 URL 을 쥔 주체라면 누구나 접근한다. 「원격 nonce 도 ssh + sudo 로 읽힌다」는 reseed 가 이미 인정한 남는 경로(`stages.sh:231-233` · `.agents/skills/dev-reseed/SKILL.md` 승인 절).
- 이유: DB challenge 표는 스키마 변경(intent 「계약 파괴 아니오」 문장과 충돌)이면서 purge 가 쓰는 같은 owner URL 로 읽히므로 root 파일보다 격리가 약하다. 행위 호스트 root 파일 한 규칙이면 Q1 ⓐ 공통 함수 하나가 세 스크립트를 덮는다. 이 intent 는 자동 보안 경계를 주장하지 않으므로(제약 문단) pty 경로 봉쇄는 목표가 아니다.
- 위험·전제: purge 를 로컬 터널에서 돌리는 운용이 있으면 nonce 자리가 로컬로 떨어진다 → spec 이 purge 실행 자리를 EC2 컨테이너(`-v <host auth dir>`)로 고정한다.
- 뒤집힐 조건: 선례 `〈366〉` 실집행이 로컬 터널이었다는 기록 · dev 호스트에 sudo 없는 운영자 계정이 생기면 원격 자리 재판정.

### 미해결 2 `docs/DEPLOY.md:536` 「이 도구」의 deploy 단계
- 판정: 정정 + 편입(면제 없음). DEPLOY.md:536 은 낡았다 — 현재 reseed `stage_deploy` 는 `release_plan_execute run` → `scripts/deploy_release.py run --plan` 이고(`stages.sh:133-136` · `:1792-1803`), executor 는 자식을 `Popen(stdout=PIPE, stderr=STDOUT)` 로 띄운다(`scripts/deploy_release.py:158`) → 계획에 ship.sh 가 들어 있으면 **stdout 비 TTY** 로 불린다(stdin 은 상속). 규칙: ship.sh 검사는 그대로 두고, executor 는 **자기 fd0 · fd1 이 TTY 일 때만** 자식을 pty 로 중계하고 아니면 오늘처럼 파이프 → ship.sh 가 거부(Q4 코드) → executor 는 `current_command` 상태로 멈춘다(재개 기제 `deploy_release.py:240-256` 기존). 사람이 자기 터미널에서 토큰 env 를 두고 같은 계획을 다시 돌리면 ship 단계부터 재개. `DEPLOY.md:536` 1줄 정정은 S-auth 문서 범위.
- 확신: 사실은 높음 · 규칙은 중간
- 사실 확인: `ship.sh` 를 부르는 코드 0건(`*.sh · *.py · *.yml` grep — 시험 · 주석 · 문서뿐) · `infra/releases/` 에 계획 파일 없음(README 만 · `:42` 「DV 패킷은 build.sh → ship.sh → up.sh → deploy_web.py 포함」 · 계획은 `/absolute/reviewed/deploy-dv.sh` 처럼 저장소 밖) · 무인 호출 = `infra/dev/install-cron.sh` 는 backup 만, `deploy_release` 자동 경유는 `infra/staging/deploy.sh:24` 뿐(staging · ship.sh 무관).
- 이유: 호출자 신원으로 면제하면 「누가 실행했는가와 무관한 플래그 판정」으로 되돌아간다(문제 문단). executor 자체가 사람 터미널에서 도는 도구이므로 TTY 를 중계하면 한 벌 검사가 그대로 성립하고 두 번째 기제가 생기지 않는다.
- 위험·전제: pty 중계 시 토큰 줄이 executor 로그(`log.write`)에 들어간다 → `RESET_TOKEN_MARK` 표식 선례(`stages.sh:235`)처럼 executor 가 표식 줄을 로그에서 제외 — spec 항목. 실제 dv 계획의 ship.sh 포함 여부는 spec 단계에서 Ted 의 계획 파일 grep 으로 확정.
- 뒤집힐 조건: 실제 dv 계획이 ship.sh 를 부르지 않는다(그러면 executor 수정 0 · 문서 정정만) · executor 가 이미 pty 를 쓴다는 증거(`:158` 기준 없음).

### 미해결 3 T14 실측 결과
- 판정: T14 는 S-auth 설계 입력이 아니다. S-auth 는 **「bypass 세션에 deny 미적용(X)」을 기본 가정**으로 설계 · 검증한다 — 검증 문장 ⑴ 의 비 TTY 호출 형태에 **Workflow 레인(bypass)을 4번째 형태로 명시 추가**(Claude Bash · Codex bridge · `bash -c` · bypass lane)하고 종료코드 · ssh/DELETE 0 을 실측한다. T14 = O 여도 범위 · 시험 축소 없음(deny 는 겹치는 마찰 장치) · X 면 총괄 계획 `:199` 대로 S-auth 가 유일 경계. 어느 쪽이든 영향은 PR 3 병합 조건(`:192` 「T14 실측 표 없이는 병합 금지」)에만.
- 확신: 높음
- 사실 확인: 총괄 계획 §5 PR 3(`:192`) · §6 #6(`:199`) · intent 제약 「검사는 스크립트 안 · hook · permissions · frontmatter 에 의존하지 않는다」 · 순서표상 S-auth 는 PR 4 뒤라 spec 시점에 T14 표가 있을 가능성이 높지만 의존하지 않는다.
- 이유: 스크립트 안 `isatty` 검사는 세션 종류를 보지 않으므로 deny 적용 여부와 직교. X 로 가정하면 O 로 밝혀져도 안전 측 오류.
- 위험·전제: bypass lane 실측은 레인 하나를 실제로 띄워 인가 검사 직전까지 도달시키는 fixture(가짜 ssh · scp · 빈 URL 파일)가 필요 — 미해결 4 의 fixture 재사용.
- 뒤집힐 조건: 설계는 무관. T14 가 「bypass 세션은 hook 도 거치지 않는다」를 보이면 Q9 ⓐ(git-guard ⑹ 확장)의 기대 효과 문장만 낮춘다.

### 미해결 4 시험 · 게이트 등록 자리 · venv
- 판정: 세 자리로 확정 — (a) Python(공통 모듈 · purge · reset) 시험 = `services/core-api/tests/test_ops_authorization.py`(신설 · `test_reset_dev_environment_guard.py` · `test_purge_datasets_guard.py` 의 `importlib` 직접 로드 + `connect=`/`s3_factory=` 주입 패턴 · `reset_dev_environment.py:790`) → `service-tests` 잡(core-api venv · `ci.yml:518-531`) · pytest 자동 수집 · 게이트 신규 등록 없음. (b) bash 쪽 = `infra/dev/tests/ship-gate.sh` 에 pty 사례 추가 **＋ 이 시험을 `gates/tools/dev-reseed-selftest.sh` CASES(`:70-82`)에 등록** — 현재 이 시험은 어느 게이트 · CI 잡에도 등록돼 있지 않다(`gates/**` · `.github/**` · `.agents/ci-producers.json` grep 0건 · `gates/config/parallelism.toml:314` 주석뿐). `reset-gate.sh` pty 사례가 이미 도는 자리이고 ssh · scp PATH 대역 규약이 같으며 `gate-selftest` 잡의 `selftest` 집합으로 돈다(`ci.yml:798`). (c) `harness-contract-selftest` 에는 넣지 않는다 — `scripts/tests/*` 를 시스템 `python3` 로 도는 자리(`gates/run.sh:357`)라 venv 가 없다. spec 의 `scripts/tests/test_ops_authorization.py` 경로는 (a) 로 정정.
- 확신: 높음
- 사실 확인: `run.sh:757-758` SELFTEST_EXEMPT 「서비스 venv 가 필요해 contract-gates 에서 못 돈다」 선례 · `gate-selftest` 잡은 core-api venv 를 만들지만(`ci.yml:787-790`) `backup-freshness.py --self-check` 용이고 harness-contract-selftest 는 그 venv 를 쓰지 않는다 · `dev-reseed-selftest.sh:78` 에 `reset-gate.sh` 포함.
- 이유: purge 는 psycopg 를 main 안에서 import 하고 reset 은 주입식이라 venv 없이도 로드되지만, ops 가드 시험은 이미 core-api tests 에 있다 → 새 잡 · 새 면제 0. ship-gate.sh 미등록은 green-by-skip 상태이므로 pty 사례를 넣으면서 등록하지 않으면 「시험 추가」가 검사가 아니다.
- 위험·전제: `dev-reseed-selftest` 이름이 ship 시험을 담기엔 넓다 — 바른 이름은 `infra-ship-gate-selftest` 신설(ALL_GATES 등록 → selftest 집합 자동 편입 `run.sh:735-745`)이지만 범위 확대라 기본은 CASES 추가 · 이름 문제는 PR 요약 후속 표기.
- 뒤집힐 조건: `infra/dev/tests/ship-gate.sh` 가 다른 경로로 실제 돌고 있다는 증거(내 grep 범위에서 0건).

### 미해결 5 `infra/prod/ship.sh` 편입 시점
- 판정: 공통 함수는 S-auth PR 에서 `infra/_lib/`(예: `ops-auth.sh`)에 두고 `infra/dev/ship.sh` 만 부른다. prod 편입 = **별도 소형 PR** · 트리거 = ① S-auth dev 실측 1회 기록(ship dev 반입 1건 + 인가 기록 파일 EC2 존재) ② **다음 `prod-YYYYMMDD` 태그 전** — 즉 S-auth 병합 뒤 첫 prod 배포 회차의 선행 단계로 못 박는다. 변경 = `infra/prod/ship.sh` 호출 1줄 + `infra/prod/tests/ship-gate.sh` pty 사례 + 같은 ADR 참조 · 새 intent 불요(S-auth intent 「확인」 절 append).
- 확신: 높음
- 사실 확인: prod ship.sh 는 dev 와 같은 `ship-gate.sh` · `ops-bundle.sh` · `repo-bundle.sh` 를 source(`infra/prod/ship.sh:26-31`) · 추가 검사 `ship_gate_require_prod_tag`(`:33`) · SSH 배열 앞 자리 동일(`:76-77`) → 삽입 자리 명확 · `infra/prod/tests/ship-gate.sh` 도 미등록(같은 grep) · 「한 벌」 원칙 `infra/_lib/ship-gate.sh:4-9`.
- 이유: 함수 위치는 「한 벌」이 정하고 시점은 prod 접촉 최소화가 정한다 — pty 중계 · 토큰 재실행 · 기록 반입이 dev 에서 한 번 실측된 뒤가 안전. 「다음 태그 전」으로 못 박아야 미편입 상태로 prod 를 실은 회차가 생기지 않는다.
- 위험·전제: 편입 전엔 「인가 기록 건수 == 실행 건수」 측정이 dev 한정 — 측정 문장에 명시.
- 뒤집힐 조건: dev 실측에서 executor pty 중계 · 토큰 재실행이 설계 수정을 낳으면 prod 편입은 그 수정 뒤로.

### 미해결 6 `deploy_doctor` 항목 편입
- 판정: 편입하지 않는다 — 15/15 무변경. ship.sh 는 `RELEASE_PRE.json` 옆에 `/opt/colab-v2/AUTHORIZATION.json`(0600)을 함께 싣고, ⑮ 는 **상태 계수 밖 정보 줄 1개**(파일 유무 · `authorized_at` · `tokenSha256` 앞 8자)만 찍는다. 항목 16 · ⑮ 판정 조건 변경 · `doctor_summary_full` 정규식 변경은 이 intent 밖 별도 판정.
- 확신: 높음
- 사실 확인: 15 는 `MARKS`(`services/core-api/ops/deploy_doctor.py:63`) · reseed 파서 `^항목 15 — ✓ 15 · ✗ 0 · ─ 0$`(`stages.sh:152`) · 픽스처 `doctor-15-15.txt` · `release_evidence.verify_post` 의 `wanted = {'1'..'15'}`(`scripts/harness/release_evidence.py:79`) · `test_deploy_doctor.py` 하드코딩 → 16 이면 최소 4곳 + DEPLOY.md 표가 깨진다. ⑮ 는 이미 「파일 없음 = ✗」 정책(`deploy_doctor.py:700-722`).
- 이유: 인가 기록은 「배포가 옳게 됐는가」(doctor)가 아니라 「누가 · 언제 인가했는가」(감사)라 소비자가 다르다. 정보 줄은 기록 반입 성공을 dev 실측 표에 근거로 남기는 최소 변경이고 생산자 · 소비자 대조(`test_deploy_doctor.py:461-470`)를 건드리지 않는다.
- 위험·전제: `DeployReport.line` 은 status 를 계수한다(`deploy_doctor.py:98-108`) → 정보 줄 형식(상태 없이 detail 만)은 spec 에서 확정.
- 뒤집힐 조건: Ted 가 「인가 없는 배포 = doctor ✗」 를 원하면 항목 수 무변경으로 ⑮ 실패 조건에 「AUTHORIZATION.json 부재 · candidate 불일치」 추가 — 별도 판정.

### 미해결 7 `reset_dev_environment.py` 파괴 phase 집합
- 판정: 파괴 = `{schema, s3-apply}` × `--dry-run` 아님. 면제 = `count` · `s3-plan`(계획 파일만 씀 · 삭제 0) · `schema --dry-run` · `s3-apply --dry-run`. 검사 위치 = schema: 재계수 · ack 대조 뒤 DDL 루프 직전(`:584` 분기 앞) · s3-apply: 계획 sha256 대조 뒤 삭제 루프 직전(`:756` 앞). 토큰 지문 = schema `(target, "schema", count-at-drop sha256)` — reseed 정지 게이트 토큰의 재료(계수 바이트)와 같아 **reseed 가 발급한 토큰을 그대로 받는다**(확장 · 복제 아님) · s3-apply `(target, "s3-apply", plan sha256)`. `--preflight-only` 는 `reseed.sh` 플래그이지 이 도구의 phase 가 아니다(context 면제 목록 정정).
- 확신: 높음
- 사실 확인: `PHASES = ("count","schema","s3-plan","s3-apply")`(`:188`) · `_phase_count` 는 계수 + 보고서 0600 쓰기만(`:526-536`) · `_phase_s3_plan` 은 계획 작성 · 겹침 시 ack 요구 · 삭제 0(`:623-698`) · `_phase_schema` `if a.dry_run:` 분기(`:584`) · `_phase_s3_apply` `if not a.dry_run:` 아래에서만 삭제(`:756`) · 문서 「이 도구는 ⑴⑵⑸ 만 한다」(`:19`).
- 이유: s3-plan 은 사람이 검토할 입력물이라 TTY 요구 시 에이전트가 계획을 만들 수 없어 절차가 멈춘다. 파괴 판정 기준은 「DROP · DELETE · AbortMultipart 가 나가는가」 하나 → 두 phase 두 자리로 닫힌다.
- 위험·전제: schema 재계수는 DB 접속 뒤라 검사가 「DB 접속 앞」(Q5 ⓐ 문구)이 아니라 「쓰기 문장 앞」 — reset 에 한해 Q5 문구를 「읽기 접속 허용 · DROP/DELETE 앞」으로 정밀화. 빈 dev(`nonempty` 없음)의 schema 는 현재 ack 불요(`:566`) — 기본은 원한 결과 문장대로 빈 dev 도 TTY + 토큰 요구(deploy.md 11번 상시 승인은 「GO 근거 문답 불요」로 좁히는 1줄 개정 동반).
- 뒤집힐 조건: Ted 가 빈 dev 상시 승인 유지를 택하면 면제 = 도구 안 계수 판정 `nonempty_reasons == {}` 인 schema(플래그 아님) · 새 phase 추가 시 집합 재판정.

### 묶음 메모
- 2 ↔ 5: executor pty 중계 + 토큰 재실행이 dev 실측에서 성립해야 prod 편입 트리거가 켜진다.
- 1 ↔ 7: reset 토큰 재료 = 계수 바이트 → reseed 가 원격 root 파일에 남긴 challenge 를 reset 도구가 컨테이너 마운트로 읽는 것이 「확장」의 구체형 · purge 도 같은 마운트 규약.
- 4 ↔ 6: doctor 무변경이므로 시험 추가는 `service-tests` + `dev-reseed-selftest` 두 자리로 끝나고 새 게이트 이름 없음.
- 3 ↔ 4: bypass lane 실측은 4 의 fixture(가짜 ssh · scp · 빈 URL 파일)를 재사용.
- 2 의 `docs/DEPLOY.md:536` 정정은 `.agents/rules/deploy.md` 순차 소유(E0 → S-red → PR 2 → PR 3 → S-auth)와 다른 파일이라 충돌 없음.