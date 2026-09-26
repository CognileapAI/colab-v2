## fable:verify-1
FINAL: ISSUES 6
Q5·미해결7·Q7 — 빈 dev(`nonempty_reasons == {}`) schema 를 면제하면 그 회차는 토큰·인가 기록이 없는데, s3-apply 는 「같은 회차 인가 기록 없으면 77 · 새 토큰 없음」이라 previews/ 객체가 남은 빈 dev 회차(`nonempty_reasons` `:263-280` 는 previews/ 를 세지 않음)가 발급 경로 없이 막힌다 · 「인가 기록 건수 == 실행 건수」도 면제 회차만큼 어긋난다 — 빈 dev schema 도 토큰 없이 `decision: empty` 기록을 auth dir 에 쓰고 s3-apply 체인은 `acknowledged|empty` 둘 다 받게 한다(측정 분모 = 기록 건수 · 면제는 토큰만).
Q1·Q9 — `human_auth.py` 는 `COLAB_OPS_ACK_TOKEN·BASIS` 두 이름만 읽는데 reseed 는 고정 제약대로 `COLAB_RESEED_ACK_NONEMPTY·BASIS` 를 유지하고 argv 전달은 금지라 값이 모듈·컨테이너(`-e COLAB_OPS_ACK_TOKEN`)로 가는 경로가 없다 — `stages.sh` 가 RESEED → OPS 로 재export 하는 1줄을 spec 항목으로 명시(모듈 입력 이름은 그대로 둘).
Q1·Q2a·Q7 — ship 은 로컬에서 도는데 challenge 쓰기·nonce 읽기·소진 삭제·인가 기록 쓰기 자리는 EC2 auth dir 이다 · 래퍼는 「호출만」 · 모듈은 stdlib 로 원격을 못 쓴다 → 반입 주체 미정(reseed 는 `:390`·`:397` 로 명시됨 · ship 은 0줄) — spec 에 「모듈 = 바이트 입출력 · `ship.sh` 가 ssh `sudo tee`/`base64`/`rm -f` 로 반입(SSH 배열 `:47` 앞 · 비 TTY 거부는 그 ssh 앞)」을 적는다.
Q10·미해결4 — `agent-bridge` 는 시스템 python3 · venv 없음인데 시험 내용에 purge 「pty+토큰 진행(가짜 DB)」이 있다 · `purge_datasets.py:115` `import psycopg` 가 ImportError 로 끝나 진행 사례를 못 돈다 — purge 는 stub `psycopg` 모듈(fixture · `sys.modules`/PYTHONPATH)을 명시하거나 진행 사례를 reset(주입식)·ship 으로 한정하고 purge 는 거부 경로 + dev 실측 1건으로 적는다.
정정 사실 1행·Q5 — 「TTY 검사는 EC2 컨테이너 안 Python 도구에 둘 수 없다」는 reset 한정 사실인데 일반 문장으로 적혀 Q5 의 purge TTY 검사(`:115` 앞 · `docker run -it`)와 표면상 모순 — 「reseed 경유 reset 도구는」으로 좁힌다.
Q6-1·미해결5 — 「`infra/prod/tests/ship-gate.sh` 무변경 green 을 PR 조건」인데 그 시험은 dev 쪽과 같이 어느 게이트·CI 도 돌리지 않는다(미해결4 grep 0건) — 조건을 「PR 요약 표에 수동 실행 rc 0 실측 줄」로 바꾸거나 dev 쪽과 함께 `dev-reseed-selftest` CASES 에 등록한다.

## fable:verify-2
FINAL: ISSUES 5
미해결7·Q2a·Q3 — reset 경로에서 도구의 nonce 검증이 코드와 어긋남: `stages.sh:397` 이 검증 직후 challenge 를 `sudo rm -f` 로 소진하고 schema 회차 `docker run` 은 그 뒤 `:449-455` 에서 돈다 → 마운트 `/auth` 에 challenge 가 없어 비어 있지 않은 회차는 항상 77 — 소진 주체를 하나로 확정: 기본 = 도구가 `/auth` 안에서 검증 뒤 삭제(실패 = 77 · DROP 앞) · `stages.sh:397` 삭제는 거부·빈 dev 경로에서만 · spec 에 순서 명시
Q9·spec — 「`stages.sh` 가 `docker run` 직전 로컬 `export` 2줄 + `-e COLAB_OPS_ACK_TOKEN`」은 값이 컨테이너에 닿지 않음: schema 회차는 `ssh_script "reset:schema"`(`lib.sh:109-121` · stdin `bash -s`) 로 원격에서 실행되고 ssh 는 env 를 넘기지 않는다 — 재export 2줄을 heredoc 본문(원격 셸) 안에 두고 docker 인자는 bare `-e NAME` 유지(`-e NAME=값` 금지 · `stages.sh:387` argv/ps 주석과 정합) · 시험은 fake ssh 가 stdin 본문의 export 를 확인
Q9 — ⑹ 정규식이 두 벌: `git-guard.sh:181`(bash fallback) 외에 주 경로 파서 `scripts/harness/hooks/git_guard_parse.py:19` `RESEED` 가 같은 패턴 — spec 은 `:181` 만 바꿔 파서 경로가 `COLAB_OPS_ACK_*=` 를 허용(blocked 2건 시험이 주 경로에서 실패) — 두 자리 동시 변경을 spec 항목으로
Q7 — 기록 = 「행위 전 쓰기 · append-only · 파일 1개」인데 스키마에 `exit` 필드 → 행위 전에 알 수 없는 값 · 갱신 금지와 모순 — 기본 = `exit` 필드 제거(종료코드는 script 보고서 `schema.json`/`ship` 증거가 이미 가짐) · 남기려면 행위 후 별도 기록 종류로 분리해 스키마에 명시
Q10·미해결4 — 「거부 사례는 stub 없이(`:115` 앞 종료)」가 사례 표와 어긋남: pty+오토큰 77 은 결속 대조 자리(`_counts :135` 뒤 · `:152` 앞) 라 `import psycopg :115` 를 지나며 · pty+토큰 부재 발급 회차도 계수가 필요 — stub 없는 사례 = 비 TTY 4형태만 · pty 사례(오토큰·발급·진행) 전부 stub `psycopg` 로 명시


## fable:verify-3
FINAL: ISSUES 5
미해결7·Q2a·Q3 — 「거부 회차 = `stages.sh:397` `sudo rm -f`」가 코드와 어긋남: rc≠0 경로는 `:390` 에 challenge 를 갓 쓰고 `:393-394` `return 1` 로 끝나 `:397` 에 닿지 않으며 그 challenge 는 다음 회차까지 남아야 한다 — final.md 미해결7·Q2a·Q3·spec 130 의 소진 주체를 「GO 회차 = 도구 · 빈 dev 회차 = `:397` · 거부 회차 = 소진 없음(`:390` challenge 유지 · TTL 만료 정리만)」으로 고친다.
Q9·spec 132 — 재export 2줄의 literal `"$COLAB_RESEED_ACK_NONEMPTY"` 는 `reseed.sh:40` `set -euo pipefail` 아래 빈 dev schema 회차(env 미설정)에서 unbound variable 로 heredoc 전개가 실패해 `reset-gate.sh` 무변경 green 과 충돌한다 — 두 줄을 `${COLAB_RESEED_ACK_NONEMPTY-}` · `${COLAB_RESEED_ACK_BASIS-}`(`stages.sh:263` 선례) 로 확정한다.
Q1·제약「복제본 금지」 — `human_auth.py` 1벌 판정인데 spec 항목 어디에도 `stages.sh:266-370` inline Python(발급·검증·`:340-343` 자체 검증)의 처리가 없어 토큰 수학이 두 벌로 남는다 — spec 항목에 「`stages.sh` heredoc 의 발급·검증을 로컬 `python3 services/core-api/ops/human_auth.py issue|verify` 호출로 교체 · `RESET_TOKEN_MARK`/`RESET_CHALLENGE_MARK` 출력 계약 유지」 1줄을 넣는다.
intent:30(전사) — 「purge 의 `docker run -it` 래퍼」·「EC2 컨테이너 안 Python 도구(purge · reset)는 결속 토큰 일치로만 · 도구 안 isatty 0건」이 final.md 정정 사실 :106(purge 는 도구 안 `:115` 앞 TTY 검사) · Q2(호스트 래퍼 금지)와 모순이고 같은 줄 뒷문장과도 충돌한다 — 줄 전체를 final.md :106 문장(「TTY 검사는 reseed 경유 reset 도구 안에 둘 수 없다 … purge 는 `docker run -it` 직접 호출이라 도구 안 `:115` 앞 검사가 성립한다」)으로 바꾼다.
intent:23·29(전사) — 검증 문장 ⑴·확인 방법 ⑴ 이 「비 TTY 3형태」인데 final.md 미해결3·spec 141 은 Workflow bypass lane 을 더한 4형태 — 두 줄 끝에 「→ 판정(9라운드) 4형태(Workflow bypass lane 추가)」를 append 한다.

## fable:verify-4
FINAL: ISSUES 2
⑷·Q4·Q5·Q10·spec 140 — 「`reset-gate.sh` 무변경 green」이 확정 판정(GO 회차 `:397` 생략 · challenge 경로 auth dir 이동)과 양립하지 않는다: `tests/reset-gate.sh:218` ⓓ‴ `[ -e "$CHALLENGE" ]` 와 `:230` 재사용 사례는 fake ssh 가 도구를 돌리지 않아 challenge 가 남고 확정적으로 red · `:99` `CHALLENGE="$FIXTURE_REMOTE/reset-challenge.json"` 도 경로가 바뀐다 · spec 130 자체가 ⓑ 계열 fixture 추가를 명시 — 판정을 「`reset-gate.sh` 갱신: ⓓ‴·재사용 사례는 fake docker 가 `/auth` challenge 를 지우는 fixture 로 대체 · `CHALLENGE` = 시험용 `COLAB_OPS_AUTH_DIR` · 나머지 사례 무변 · `dev-reseed-selftest` 안 green」으로 닫고 intent ⑷·Q4 근거·Q5 「유일한 선택」·Q10 「무변경 green」에 재검 정정으로 append(「red 면」 조건문 제거).
Q1×spec 115(ship 발급) — `issue` 는 「stdout 이 TTY 일 때만 토큰 · 비 TTY 면 77」인데 `ops-auth.sh` 는 「모듈 `issue` 출력 바이트를 ssh `sudo tee`」해야 하므로 stdout 을 캡처(파이프)할 수밖에 없어 항상 77 — 재검 3 이 `stages.sh:262` 캡처에 대해 찾은 결함이 ship 경로에 그대로 남았다 — `issue` 는 challenge JSON 을 로컬 파일 경로 인자(`--out <0600 tmp>`)로 쓰고 stdout 에는 토큰만 찍으며(캡처 0), `ops-auth.sh` 는 그 파일을 base64 → ssh `sudo tee` 뒤 unlink · purge 컨테이너도 같은 꼴 `--out /auth/purge-<id>-challenge.json` 으로 spec 115·124 를 고친다.
