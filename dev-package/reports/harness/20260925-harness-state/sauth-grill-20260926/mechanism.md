### Q1
- 판정: ⓐ의 변형 — 「새 선택지 ⓐ′: 토큰식·challenge 발급/소진·검증·기록을 stdlib-only Python 모듈 1벌(`services/core-api/ops/human_auth.py` · CLI 겸용)에 두고, bash 쪽(`infra/_lib/human-auth.sh`)은 `[ -t 0 ] && [ -t 1 ]` 검사·env 전달·모듈 호출만 한다」. bash 에 토큰 수학을 두 번째로 구현하지 않는다.
- 확신: 높음
- 사실 확인:
  - reseed 정지 게이트의 토큰 로직은 이미 Python 이다 — `stages.sh:266-370` 이 `python3 - … <<'PY'` heredoc 으로 sha256·만료·소진 판정을 하고, bash 는 `[ -t 1 ]` 출력(`:227-235`)과 원격 challenge 쓰기/지우기(`:390` · `:397`)만 맡는다. 「bash 구현 vs Python 구현」이 아니라 「heredoc 을 모듈로 빼내는 일」이다.
  - `ship.sh:18` 은 이미 `python3 "$REPO/scripts/harness/release_evidence.py"` 를 부른다 — bash 진입점이 Python 모듈을 CLI 로 부르는 선례가 같은 파일에 있다.
  - 도구 쪽 검증 지점도 이미 Python — `reset_dev_environment.py:254 ack_token_refusal` · `:563-573`(DROP 직전 재계수 sha256 ≠ ack 면 `_PRECONDITION`) · `:882`.
  - ⚠ 정정(context 「원한 결과 ⓐ `sys.stdin.isatty()`」): `reset_dev_environment.py` 는 항상 비 TTY 로 돈다 — reseed 가 `ssh -o BatchMode=yes`(`lib.sh:99-100` · `-t` 없음) → `docker run`(`-it` 없음 · `stages.sh:38-46`) 으로 부른다(`:455`). 이 파일 안에 isatty 를 넣으면 reseed 정본 경로가 스스로 거부된다. purge 도 같은 모양(`purge_datasets.py` docstring 「docker run --rm … python /tmp/purge.py」). 따라서 TTY 검사는 **토큰을 찍는 진입 셸**(reseed `stages.sh` · `ship.sh` · purge 는 `docker run -it` 필수 또는 호스트 래퍼)에 두고, EC2 안의 Python 도구는 「결속 토큰 일치」로만 판정한다 — 이것이 reseed 선례 그대로다(도구 `reset.py` 에는 TTY 검사 0건 · 토큰 대조만).
- 이유:
  - 「한 벌」 원칙(`ship-gate.sh:4-7` · dev/prod 복사본이 갈려 doctor ✗ 를 낸 전례)이 토큰식에 그대로 적용된다 — 두 언어 두 구현은 만료 비교·hex 검증·nonce 결속이 어긋나는 첫 자리다.
  - 모듈을 stdlib-only 로 두면 로컬(reseed · ship.sh · venv 없음)과 EC2 컨테이너(purge · reset) 양쪽에서 같은 파일이 돈다. `stages.sh:266` heredoc 이 이미 stdlib-only 라 이전 비용이 낮다.
  - 시험 fixture 도 1벌 — challenge JSON · 계수 바이트 · 기대 토큰 세트를 `test_ops_authorization.py` 와 `reset-gate.sh`(`token_for` 함수 `:433`) 가 공유한다.
- 위험·전제: 모듈 파일이 EC2 컨테이너에 마운트되어야 한다(`reset_docker_prefix` 에 `-v` 1줄 추가 · `ops-bundle.sh` 편입 여부는 spec). `services/core-api` venv 없이 `python3` 만으로 돌아야 한다는 제약을 시험이 고정해야 한다.
- 뒤집힐 조건: EC2 컨테이너 이미지의 python 이 로컬 python3 와 stdlib 동작(`hashlib` · `datetime.isoformat(timespec)`)에서 갈린다는 실측 · 또는 spec 이 purge 를 컨테이너 밖 호스트 python 으로 옮기기로 하면 bash 비중이 커져 ⓐ 원안(bash 구현 별도)으로 돌아간다.

### Q2
- 판정: ⓐ (2단계 · reseed 모양 확장)
- 확신: 높음
- 사실 확인:
  - reseed 는 첫 회차가 거부하며 challenge 를 원격에 남기고(`stages.sh:356-377` · `:388-392`) 토큰을 `[ -t 1 ]` 일 때만 찍고(`:227-235`), 사람이 env 두 개를 두고 `--from reset` 으로 다시 연다(`SKILL.md:138-139`). 붙여 넣을 완성 명령은 찍지 않는다(`SKILL.md:136`). 검사 `reset-gate.sh:421-440` 이 pty 사례로 이 2단계를 고정한다. git-guard ⑹(`git-guard.sh:180-183`)은 env **할당 꼴**만 본다 — 2단계 env 방식이어야 이 훅이 겹친다.
  - ⓒ 의 전제 검토: `/dev/tty` 는 controlling terminal 이 없는 에이전트 Bash 에서는 열리지 않지만 `pty.spawn` 은 controlling terminal 을 만든다(`reset-gate.sh:432` 가 그 방식으로 stage_reset 을 돌려 토큰을 stdout 에서 받는다). 잔여 경로는 ⓐ와 같고, 줄어드는 것은 없다.
  - ⓑ 의 전제 검토: 로컬 파일은 같은 uid 의 에이전트가 읽는다(`deploy.md:69-72` 「env 파일·Write 도구 주입」과 같은 급). purge · reset 은 EC2 컨테이너에서 도니 로컬 `~/.local/state` 를 읽을 수 없다 — 파일을 EC2 로 실어야 해서 채널이 하나 더 생긴다(중복 기제 금지 위반).
- 이유:
  - Ted 고정 조건 「선례를 확장 · 복제 금지」에 정확히 맞는 것은 ⓐ뿐이다. ⓑ·ⓒ 는 두 번째 토큰 기제다.
  - 2단계가 주는 실질: 「사람이 계수/대상을 본 회차」와 「GO 를 준 회차」가 프로세스로 분리되어 기록(`reset-ack.json` `decision: refused → acknowledged`)이 두 행위를 각각 남긴다. ⓒ 는 한 프로세스 안에서 출력·입력이 닫혀 「보고 나서 GO」가 기록상 증명되지 않는다.
  - env 이름은 hook ⑹ 의 거부 대상이 되고(Q9 ⓐ 와 결합), argv 가 아니라 `ps` · 셸 이력에 남지 않는다.
- 위험·전제: purge · reset 직접 호출 런북(`purge_datasets.py` docstring · `DEPLOY.md:519-527`)에 `docker run -it` 가 없다 — 그대로면 사람이 돌려도 `[ -t 1 ]` 이 거짓이라 토큰이 안 찍힌다. 런북 갱신이 spec 의 필수 항목이다. 2단계는 원격 왕복이 한 번 더 있으므로 ship.sh 첫 회차(거부)도 ssh 1회를 쓴다 — 비 TTY 거부는 그 ssh **앞**에서 끝나야 한다(Q5 ⓐ 와 결합).
- 뒤집힐 조건: git-guard ⑹ 확장(Q9)이 ⓑ로 판정되어 env 이름이 훅 대상에서 빠지면 ⓐ의 마찰 이점 하나가 사라진다(그래도 ⓐ 유지 · 확신은 중간으로).

### Q2a
- 판정: 새 선택지 — 「ⓐ′: nonce 는 언제나 **파괴 행위가 실제로 일어나는 호스트**의 root 전용 0600 파일에 둔다 · DB 표 없음 · 로컬 `~/.local/state` 없음」. ship · reset = dev 호스트(reseed `REMOTE_OUT` 급 · ssh `sudo tee`) · purge = **같은 dev 호스트**의 root 0600 디렉터리를 컨테이너에 마운트.
- 확신: 높음
- 사실 확인:
  - reseed challenge 자리 = `REMOTE_OUT=/tmp/colab-reseed-out`(`stages.sh:14`) · `umask 077; base64 -d | sudo tee … && sudo chmod 600`(`:390`) · 소진 = `sudo rm -f`(`:397`) · 표준입력으로 실어 argv·원격 ps 에 남기지 않는다(`:389`).
  - ⚠ 정정(ⓐ의 전제 「purge 는 원격 자리가 없다」): purge 는 로컬에서 도는 도구가 아니다 — 「EC2 위 · `docker run --rm --network host --user 0 -v /etc/colab/…:ro`」(`purge_datasets.py` docstring 「쓰는 법」 · `DEPLOY.md §6-1`). 실행 호스트가 곧 dev 호스트라 reset 과 같은 자리(root 0600 파일)를 쓸 수 있고, `--user 0` 이라 컨테이너가 그 파일을 쓰고 지울 수 있다. ec2-user ssh 세션은 sudo 없이 못 읽는다 — reset 선례와 같은 수준.
  - DB 안 challenge 표는 스키마 변경이다 — 이 intent 의 「제품 코드 · 스키마 · `contracts/**` 무변경」과 충돌하고, `deny_update_delete` 류 감사 표 규약(`purge_datasets.py` docstring 3)까지 건드린다.
  - 로컬 `~/.local/state/colab` 은 저장소 안 도구 어디에도 아직 쓰지 않는다(`scripts` · `infra` · `dev-package/tools` · `gates` grep 0건). 새 자리이며, 같은 uid 의 에이전트가 읽어 재계산할 수 있다.
- 이유:
  - 「nonce 는 실행 자리에 두지 않는다」(`968d16a1` · `stages.sh:216-218`)의 본질은 「토큰 재료 두 개(계수·nonce)를 같은 uid 가 읽을 수 없게 분리」다. ⓑ는 그 분리를 없애고, ⓒ는 스크립트별 분기라 「한 벌」이 깨진다.
  - purge 를 원격 파일로 두면 세 도구가 한 코드 경로(root 0600 파일 · 만료 · 1회 삭제 · 실패 시 정지 `:397-398`)를 쓴다 — Q1 ⓐ′ 모듈의 저장 backend 가 하나로 끝난다.
  - ship.sh 도 dev 호스트에 `RELEASE_PRE.json` 을 이미 `chmod 0600` 으로 두는 관행이 있다(`ship.sh:54-55`) — challenge 도 같은 자리 규약을 따른다.
- 위험·전제: `/tmp` 는 재부팅에 지워진다(challenge 소실 = 토큰 무효 = 다시 연다 · 안전한 쪽으로 실패). spec 이 `/opt/colab-v2/auth/`(root 0700) 같은 영속 자리를 고르면 만료·소진 검사와 함께 옛 challenge 정리(현재 `RESET_STALE_FILES` 삭제 `:225` · `:420` 선례)를 옮겨야 한다. 로컬에는 challenge 가 메모리로만 오간다는 전제(`:259-260`)를 세 도구 모두에 시험으로 고정해야 한다(`nonce_leaks` `reset-gate.sh:437`).
- 뒤집힐 조건: purge 를 EC2 밖(로컬 · RDS 직결)에서 돌리는 운영 경로가 정본이 되면 purge 의 「실행 호스트」가 로컬이 되어 ⓒ(스크립트별)로 되돌아간다. dev 호스트 root 파일을 비 sudo 사용자가 읽을 수 있다는 실측이 나오면 자리 자체를 재설계한다.

### Q3
- 판정: ⓐ + 지문 정의 보강 — purge 지문 = **dry-run 산출 바이트**(lab · 정렬 `--id` 목록 · 표별 예정 행수 · DB 호스트)의 sha256, reset = 기존 계수 바이트(무변), ship = FULL_SHA ‖ environment ‖ PRE evidence sha256 ‖ **대상 호스트(`COLAB_DEV_SSH`)**. 만료 1800초 · 1회 소진 유지.
- 확신: 높음
- 사실 확인:
  - 토큰식 = `sha256(raw + b"\n" + nonce)` · raw = `count-before.json` 바이트 그대로(`stages.sh:270-273`) · challenge 가 `countBeforeSha256` 을 품고 자료가 바뀌면 거부(`:340-341`) · 만료 = `stamp(now) >= expiresAt`(`:342-343`) · TTL `RESET_ACK_TTL_SECONDS=1800`(`:224`) · 소진 = 원격 파일 삭제(`:397`).
  - 도구 쪽은 결속을 **검증 시점에 다시 계산**한다 — `reset_dev_environment.py:558-567` DROP 직전 재계수 sha256 ≠ ack 면 `_PRECONDITION`. 「지문 = 저장값 대조」가 아니라 「지문 = 지금 다시 센 값」이 선례다.
  - purge 는 이미 실집행 전에 `planned = _counts(cur, ids)`(`purge_datasets.py:135`)를 세고 `planned == actual` 이 아니면 ROLLBACK 한다(`:157-167`). 지문 재료가 코드에 이미 있다 — ⓐ 원안의 「lab · id 목록 · DB 호스트」만으로는 dry-run 과 실집행 사이에 행이 바뀌어도 토큰이 살아 있다.
  - ⓑ(무결속 · 300초)는 2026-09-24 사고 구조(「승인 있음」이 대상과 무관하게 성립)를 짧은 TTL 로 되풀이한다 — `deploy.md:74-75` 세 번의 사고 중 어느 것도 「승인이 늦어서」가 아니라 「승인이 대상에 묶이지 않아서」였다.
- 이유:
  - 대상 결속은 「지난 토큰 · 다른 대상의 토큰 · 만료 토큰은 TTY 에서도 거부」(context 검증 문장 ⑶)를 토큰식만으로 만족시킨다 — 별도 상태 없이.
  - 1800초는 사람이 계수를 읽고 GO 근거를 적는 시간이며 `reset-gate.sh` 가 그 값을 상수로 고정한다. 300초는 재열기 실패를 늘려 「토큰을 미리 받아 두는」 습관을 유도한다(결속 약화 압력).
  - ship 에 호스트를 넣으면 같은 sha·같은 evidence 로 다른 EC2(향후 prod · Q6-1 ⓑ 편입 시)에 재생되지 않는다 — prod 편입 때 지문 정의를 다시 열지 않아도 된다.
- 위험·전제: purge 지문을 dry-run 바이트로 하면 첫 회차(거부 · challenge 발급)가 dry-run 을 겸한다 — Q5 의 「행위 없는 경로 = 면제」와 맞물려 「dry-run = 발급 단계」로 정의해야 한다. reset 은 무변 전제(`reset-gate.sh` 무변경 green).
- 뒤집힐 조건: purge 대상 표에 실집행 직전 행수가 정상적으로 변하는 경로(예: 백그라운드 file_count 트리거 갱신)가 있어 dry-run 바이트가 매번 달라진다는 실측이 나오면 지문을 「lab · 정렬 id · 표별 행수」의 정규화 JSON 으로 좁힌다(바이트 그대로 → 정규화 값).

### 묶음 메모
- Q1 ⓐ′(Python 모듈 1벌) 은 Q2a ⓐ′(원격 root 파일 하나의 backend) 를 전제한다 — 저장 backend 가 둘이면 모듈의 발급/소진 분기가 생긴다.
- TTY 검사 위치 정정(Q1)이 Q5 를 좌우한다: EC2 안 도구(reset · purge)는 비 TTY 가 정상이라 「진입 즉시 TTY 요구」(Q5 ⓑ)는 reseed 정본 경로를 깨고, TTY 요구는 로컬 진입 셸과 `docker run -it` 런북에만 걸린다.
- Q3 의 purge 지문(dry-run 바이트)은 Q2 2단계와 한 몸이다 — 첫 회차 = dry-run + challenge 발급, 둘째 회차 = `--yes-delete` + 토큰.
- 발견한 문서 불일치(Q5·Q6 담당자에게): `docs/DEPLOY.md:536` 「이 도구는 `deploy_release.py` 를 부르지 않는다」는 낡았다 — `stages.sh:133-134` · `:1792` · `:1803` 이 `scripts/deploy_release.py run --plan` 을 부르고, executor 는 단계를 `stdout=subprocess.PIPE`(`deploy_release.py:158`)로 돌린다. 계획에 `infra/dev/ship.sh` 가 들어 있으면 reseed deploy 단계의 ship 은 항상 비 TTY 다 — S-auth 가 ship 을 막으면 reseed deploy 가 막히므로, reseed 가 자기 TTY 단계에서 ship 토큰을 먼저 받아 넘기거나 계획 단계를 면제 목록으로 다뤄야 한다(저장소에 계획 파일의 ship.sh 문자열은 0건 · 계획은 실행 시 `--plan` 인자).
- Q9 는 Q2 ⓐ 의 env 이름을 받는다 — 이름은 `COLAB_RESEED_ACK_*` 와 같은 접두 규약으로 하나 더 늘리는 쪽이 ⑹ 정규식 한 줄 수정으로 끝난다.