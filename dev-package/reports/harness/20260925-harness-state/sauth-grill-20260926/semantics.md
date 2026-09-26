### Q4
- 판정: ⓐ — 인가 거부(비 TTY · 토큰 부재 · 불일치 · 만료 · 재사용 · 기록 쓰기 실패) 전부 **77** 하나, 대상 스크립트 공통. 인자 오류는 기존 2 유지.
- 확신: 높음
- 사실 확인: 기존 코드 분포 — purge 2(인자 `:107-115`) · 3(계수 0/불일치 `:143-149`) · 4(ROLLBACK `:170-176`) · reset `_REFUSE = 2` 가 인자·환경·계획 가드 전부에 쓰임(`reset_dev_environment.py:198` · `:831-883`) · ship 78(증거·sha `:12-17`) · 65(비조상 `infra/_lib/ship-gate.sh:35`) · 64(환경 `:25`) · 2(tar 부재 `ship.sh:42`). 77 선례 있음 — `infra/staging/pipeline/approval/target.sh:60` `exit 77   # EX_NOPERM`. 게이트 계약 0/1/78 은 `gates/README.md:9` 의 게이트 전용이며 스크립트 코드와 별개(맥락 「제약」과 일치).
- 이유: ⓑ 의 2 는 「인자를 고쳐 다시 부르라」로 읽히는 코드라 에이전트의 재시도 루프를 끊지 못하고, 65 는 `ship-gate.sh:10` 「끝나는 자리 셋」과 문서·deploy_doctor 서술에서 「비조상」의 뜻으로 고정돼 있어 겹치면 어느 게이트가 거부했는지 기록·시험이 구분 못 한다. 검증 문장 ⑴ 「모두 같은 종료코드로 거부」와 Q8 `handoff --mode blocked` 분기는 공통 코드 하나를 전제한다. 77 은 2·64·65·78 어느 것과도 겹치지 않고 sysexits 의미(EX_NOPERM)와 저장소 선례가 있다.
- 위험·전제: 거부 사유(비 TTY / 만료 / 불일치)는 코드로 나누지 않고 기록 `decision` 과 stderr 1줄로만 구분한다 — 코드를 나누면 에이전트가 「만료면 재발급」식 분기를 짠다. 기존 호출부는 `rc` 를 그대로 전달만 한다(`stages.sh:1800` `blocked_add "executor run 실패 $rc"`) 라 77 도입에 수정 불요.
- 뒤집힐 조건: 어떤 호출부가 특정 코드 집합만 「정상 거부」로 분류해 77 을 crash 로 취급한다는 grep 결과가 나오면(현재 `stages.sh` · `deploy_release.py:158-163` 에는 없음) 그 호출부 수정이 spec 에 추가되지만 판정 자체는 유지.

### Q5
- 판정: ⓐ + 정정 3건(아래). 검사 자리 = 행위 직전, 면제 = 행위 없는 경로. 시험 전용 우회 env 는 두지 않는다.
- 확신: 중간(자리 판정은 높음 · 실행기 경로 처리가 spec 에서 풀려야 함)
- 사실 확인:
  - ship: dry-run 종료 `:19-21` 이 SSH 변수 요구 `:22-23` 보다 앞 → `test_harness_release_evidence.py:96-104`(DRY_RUN=1 · 증거 부재 78)은 ⓐ 에서 무영향. 검사 자리는 조상 게이트 `:36` 뒤 · 번들 `:43-44`(로컬 쓰기) 뒤 · SSH 배열 `:47` 앞. 반면 `infra/dev/tests/ship-gate.sh:99-105` 는 `$( … )` 캡처(비 TTY)로 전체 경로를 돌려 ⓑ 케이스가 exit 0 을 기대(`:137-160`) → ⓐ 에서도 **깨진다**. 정정 ①: ⓑ 계열만 pty(`reset-gate.sh:433` `pty.spawn` 선례) + 픽스처 nonce 로 옮기고, ⓐ 65 · ⓒ 78 · ⓓ 65 는 인가 지점 앞에서 끝나므로 무변경.
  - purge: `--yes-delete` 없는 dry-run 도 `psycopg.connect` `:129` 를 지나 계수한다(읽기 전용 · 경계 걸림). 검사 자리 = `:107-115` 인자 검증 뒤 · `:129` 앞 · `a.yes_delete` 일 때만. 맥락의 「`--yes-delete` 없음 = 면제」와 일치하되 「접속 앞」이 아니라 「실집행 접속 앞」이다.
  - reset: 도구는 `ssh_dev` → `docker run --rm --network host --user 0`(`stages.sh:40` · `-i`/`-t` 없음 · `:117` 「`-i` 를 쓰지 않는다」) 안에서 돈다 → 도구 안 `isatty()` 는 reseed 경유 **항상 false**. 정정 ②: reset 의 TTY 판정은 사람이 있는 로컬 래퍼(`reset_show_token` `[ -t 1 ]` `:227-241`)에 두고, 도구는 이번 회차에 결속된 전달값(현 `--ack-sha256` = DROP 직전 재계수 sha256 · `:567`) 을 「인가 기록 존재 검사」로 확장해 받는다. 직접 호출(`SKILL.md:148` 런북)은 전달값이 없으므로 도구 자체 TTY+토큰 경로로만 통과. 파괴 phase = `schema`(DROP `:124` `:130`) · `s3-apply`(`delete_objects` `:765`). `count` · `s3-plan`(계획 파일만 씀) · `--dry-run` 은 면제.
  - 실행기 경로(맥락 미해결 2번 정정): `docs/DEPLOY.md:536` 「계획 실행기를 부르지 않는다」는 낡았다 — `stages.sh:134-136` `stage_deploy() { release_plan_execute run; }` → `:1798` `scripts/deploy_release.py run --plan` → 계획 JSON `targets[].deploy` argv(`infra/releases/README.md:29-42` build.sh → ship.sh) → `deploy_release.py:158` `Popen(... stdout=PIPE, stderr=STDOUT)`. 즉 실행기 아래의 ship.sh 는 사람이 터미널에서 띄워도 **stdout 이 항상 파이프**다. 저장소에 `ship.sh` 문자열 호출이 0건인 이유는 호출이 계획 JSON 에 있기 때문이다. 정정 ③: ⓐ 를 두면 reseed deploy 단계와 `product_release.py:360` 경로의 ship.sh 는 77 로 멈춘다. spec 에서 둘 중 하나를 고른다 — (i) `execute_command` 가 자기 stdout 이 TTY 일 때만 자식에 pty 를 물려준다(사람 터미널이 있어야 성립 · 에이전트 Bash 에는 없음) (ii) dev 반입은 사람이 `infra/dev/README.md:63` 꼴로 ship.sh 를 직접 부른다고 못 박고 reseed 는 `--from` 으로 그 뒤부터 잇는다. (i) 가 「무인 진입점」 문서와 정합.
- 이유: ⓑ(진입 즉시)는 무영향이어야 할 세 곳을 깨뜨린다 — 78 기대 시험(TTY 검사가 증거 검사보다 앞이면 77) · purge dry-run 의 에이전트 사전 계수 · reseed deploy 단계 전체. 행위 없는 경로를 열어 두면 에이전트가 사전 검증(dry-run · count · `--check`)까지는 하고 행위만 사람에게 넘기는 Q8 의 흐름이 성립한다.
- 위험·전제: 면제 판정은 env 값이 아니라 **행위 여부**(플래그·phase)로만 한다 — `COLAB_*_SKIP_AUTH` 류 시험 전용 우회를 만들면 그 env 가 에이전트의 우회 경로가 된다. reset 전달값 확장은 기존 `reset-gate.sh` 무변경 green(검증 ⑷) 을 유지해야 한다.
- 뒤집힐 조건: `deploy_release.py` 가 stdout PIPE 를 버릴 수 없다는 판정(로그 정본이 그 파이프)이 나오고 (ii) 도 거부되면, ship 에 한해 「토큰 + 기록」만 요구하고 TTY 는 토큰 발급 단계에서만 요구하는 변형(Q2 와 결합)으로 좁혀야 한다 — 이는 Ted 고정 조건의 해석 변경이라 별도 판정.

### Q6-1
- 판정: ⓐ + 구현 자리 조건 — dev 만 이번 범위, 단 인가 함수는 `infra/_lib/`(ship-gate.sh 와 같은 「한 벌」 자리)에 두고 prod 는 이번 PR 에서 **부르지 않는다**.
- 확신: 높음
- 사실 확인: `infra/_lib/ship-gate.sh:4-7` 「본문은 한 벌이고 dev·prod 가 그것을 부른다」 · prod 는 태그 게이트를 더 요구(`:45-57` · `infra/prod/ship.sh:34`) · prod 도 같은 꼴 SSH 배열(`:69-70`) · RELEASE_PRE 반입(`:78-79`). prod 배포의 사람 결정 형태는 승인 intent 2026-09-15(사람의 develop→product PR 병합 · `deploy.md` 「2026-09-15 승인 정책」) 이고 `scripts/product_release.py:40-56` `select_release` 가 병합 이벤트·허용 actor 로 판정한 뒤 `:360-363` 실행기를 부른다 — 실행기 아래는 비 TTY(Q5 정정 ③). 첫 운영 회차는 미완(`R-DEVELOP-PRODUCT.md:29` 미체크 · `DEPLOY_PRODUCT.md:80`).
- 이유: prod ship.sh 에 TTY 를 넣으면 승인된 운영 배포 모델(병합 이벤트 → 실행기) 과 충돌하고, 그 변경은 이 intent 가 아니라 2026-09-15 intent 의 개정이다. 반대로 함수를 dev 스크립트 안에만 두면 `ship-gate.sh:4-7` 이 막으려던 복사본 갈림이 재발한다. 「한 벌」 자리에 두고 호출만 dev 로 한정하면 prod 편입은 후속 판정에서 한 줄이다.
- 위험·전제: `infra/prod/tests/ship-gate.sh` 무변경 green 을 PR 조건에 넣는다(prod 파일은 손대지 않음을 시험으로 증명). prod 편입 조건 = dev 1회 실측 뒤 + 실행기 pty 처리(Q5 ③) 확정 + 2026-09-15 intent 와의 정합 판정.
- 뒤집힐 조건: 운영 배포가 실제로는 사람이 터미널에서 `infra/prod/ship.sh` 를 직접 부르는 절차로 확정(기억상 현행이 그러함)되고 `product_release.py` 자동 경로가 폐기되면 ⓑ 로 바꿔 이번 PR 뒤 첫 후속에서 prod 를 같이 부른다.

### Q6-2
- 판정: ⓐ 제외 — 단, 범위 밖 절에 「사람 게이트가 다른 기제(병합 이벤트 + hash 결속 manifest + `--provision` 기록 + controller 상태)」라는 사유와 「최초 실행이 수동 절차로 바뀌면 S-auth 후속」 조건을 명시.
- 확신: 중간
- 사실 확인: `reset_product_environment.py` 는 `--check` / `--provision` / `--phase schema|s3`(`:187-190`) · 실행은 controller 기록 `state=running` · `candidate_sha` · `manifest_sha` 일치를 요구(`:170-180`) · 잠금 fd 를 부모에서 상속(`:228-233` `COLAB_PRODUCT_RESEED_LOCK_FD` 등) · 후보 sha 를 env 로 받음(`:224`) — 상위 product-reseed 컨트롤러의 **자식 프로세스** 꼴이지 터미널 진입 꼴이 아니다. `deploy.md` 「2026-09-15 승인 정책」 · `DEPLOY_PRODUCT.md:52-66` 이 별도 경계를 정본으로 둔다. 총괄 계획 S-auth 행(`:131`)에 없음. **휴면이 아니라 대기 중**이다(첫 운영 회차 미완).
- 이유: 이 스크립트에 TTY 를 요구하면 승인된 2026-09-15 intent 의 실행 모델(컨트롤러 아래 단계 실행 · 실패 시 점검 유지 · 사람 재개)을 이 PR 이 바꾸게 된다. 사람 인가는 이미 「허용 actor 의 병합 + 운영자 입력 hash + 명시 `--provision`」으로 형식 판정된다. 포함하면 두 인가 기제가 한 스크립트에 겹쳐 어느 쪽이 정본인지 흐려진다.
- 위험·전제: 저장소에서 가장 파괴적인 스크립트가 S-auth 밖에 남는다. 전제 = product-reseed 컨트롤러 경로가 실환경에서 그대로 쓰인다는 것 — 아직 실측 0회.
- 뒤집힐 조건: 첫 운영 초기화를 컨트롤러가 아니라 사람이 `--phase schema` 를 손으로 부르는 절차로 확정하거나, 컨트롤러 경로가 실환경에서 폐기되면 ⓑ 로 바꿔 같은 `infra/_lib`/Python 공통 모듈을 부르게 한다.

### Q7
- 판정: ⓒ — 정본은 ⓐ(실행 자리 JSON 1개 · 행위 **전** 기록 · 못 쓰면 77) · 같은 바이트를 운영자 기계 `~/.local/state/colab/authorizations.jsonl`(0600 · append-only)에 한 줄 추가 · ship 은 EC2 `/opt/colab-v2/` 에 `RELEASE_PRE.json` 옆으로 사본(0600). 스키마 하나 `colab-ops-authorization/1`.
- 확신: 중간
- 사실 확인: 선례 `reset-ack.json` 은 `RUN_DIR`(`reseed.sh:251-256` = `$COLAB_JOB_DIR/tmp/dev-reseed/<id>` 또는 `dev-package/reports/dev-reseed-runs/<id>` · 후자는 `.gitignore:48`)에 0600 으로 쓰고 nonce 는 sha256 만(`stages.sh:262-274`). reset 도구의 보고서는 원격 `/out`(`REMOTE_OUT` · root 0600)에 서고 래퍼가 base64 로 실행 자리로 가져온다(`:459-463`) — 도구 측 인가 기록도 같은 길이 필요. purge 는 보고서 인자·출력 마운트가 없다(`:36-41` docker run · argparse `:99-105`) → 기록 자리 인자 + `-v` 신설이 필수. ship 은 실행 자리 개념이 없다(`deploy_release.py:73-76` 상태 디렉터리는 `.git` 아래 `deploy-releases`). **정정**: `deploy_doctor.py` 는 `RELEASE_PRE.json` 을 읽지 않는다(grep 0건 · ⑮ 는 `CURRENT_SHA`·`MAIN_SHA` 만 `:713-720`); 읽는 것은 `deploy_doctor_evidence.py --pre`(`:67-79` · `infra/ops/probes/deploy-verification.sh:13`)다. 따라서 ⓐ 의 「deploy_doctor 가 읽을 수 있게」는 자리 확보이지 소비가 아니며, 소비는 맥락대로 15/15 별도 판정.
- 이유: ⓐ 만으로는 가치 가설 ⑸ 「인가 기록 건수 == 실행 건수」를 셀 자리가 없다(회차 폴더가 스크립트마다 · 호스트마다 흩어짐). ⓑ 만으로는 원격 컨테이너에서 도는 purge·reset 의 기록이 행위와 같은 자리에 남지 않아 게이트·사후 대조가 회차 산출물과 짝을 못 맞춘다. 두 사본은 같은 직렬화 바이트(jsonl 한 줄 = 그 JSON minified)라 갈림이 없다.
- 위험·전제: 쓰기 실패 = 거부(77)로 두어야 「기록 없는 행위」가 안 생긴다 — jsonl 추가도 같은 원자 단계에 넣는다. 필드 최소 집합: `schema` · `recordId` · `authorized_at`(UTC) · `operator` · `script` · `target`(지문 원문 필드 + 지문 sha256) · `tokenSha256` · `nonceSha256` · `issuedAt`/`expiresAt` · `tty` · `decision` · `exit`. 토큰·nonce 평문 0(Q9·Q10 시험이 고정).
- 뒤집힐 조건: `metrics.py`(총괄 계획 M) 가 회차 폴더만 입력으로 받기로 확정되면 ⓑ 는 중복이라 ⓐ 로 줄인다. 반대로 purge 가 컨테이너 밖(EC2 호스트 venv)에서 돌기로 바뀌면 마운트 문제가 사라져 ⓐ 의 비용이 내려가지만 판정은 그대로.

### 묶음 메모
- Q5 정정 ③(실행기 stdout=PIPE · `deploy_release.py:158`)이 가장 큰 교차 의존이다 — Q2(같은 터미널 2단계 발급은 실행기 아래서 성립 불가) · Q6-1(prod 자동 경로도 실행기) · spec 의 `DEPLOY.md:536` 정정에 걸린다. 이 사실이 확정되기 전에 Q2 를 닫지 않는 것이 맞다.
- Q5 정정 ②(reset 은 로컬 래퍼가 TTY · 도구는 전달값 검증)는 Q1 공통 모듈의 인터페이스(「기록 발급」과 「기록 검증」 두 함수)와 Q3 지문(reset = 재계수 sha256 재사용)을 결정한다.
- Q4 77 은 Q8 handoff 분기와 Q10 시험(3 스크립트 × 비 TTY/불일치/만료 = 77) 의 상수다.
- Q7 ⓒ 의 필드 고정 시험(Q10)이 Q9 의 「평문 0」을 함께 검증한다 — 별도 시험을 만들지 않는다.
- Q6-1·Q6-2 는 같은 원칙으로 닫힌다: prod 쪽 사람 게이트는 2026-09-15 intent 의 것이며, 이 PR 은 `infra/_lib` 자리만 만들고 호출은 dev 로 한정한다.