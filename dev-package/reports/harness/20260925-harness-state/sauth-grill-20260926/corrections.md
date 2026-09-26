# 재검 3 정정(resolve-fix-3)

### 미해결7·Q2a·Q3
- 판정(정정): reset challenge 소진 주체는 「GO 회차 = 도구(`reset_dev_environment.py`)가 마운트 `/auth` 안에서 검증 뒤 삭제(실패 = 77 · DROP 앞) · 빈 dev 회차 = `stages.sh:397` `sudo rm -f` · 거부 회차 = 소진 없음」으로 확정한다. 거부 회차는 `:390` `sudo tee` 가 이번 회차 challenge 를 쓰고(직전 challenge 는 덮어써 정리) `:394` `return 1` 로 끝나므로 `:397` 에 닿지 않으며, 그 challenge 는 사람이 토큰을 들고 다시 여는 다음 회차까지 남아야 한다 · 만료 challenge 정리 = 다음 발급 시 `:390` 덮어쓰기 하나(별도 삭제 0).
- 근거: `stages.sh:380-394` rc≠0 분기 — `:388-392` challenge 원격 쓰기 → `:393` `chal_out=""` → `:394` `return 1` · `:396-398` `sudo rm -f` 는 rc=0(빈 dev `done("empty",…,0)` `:327` · GO `done("acknowledged",…,0)` `:349`) 에서만 도달 · Python `:339` 「이번 거부 회차의 1회용 challenge 가 원격에 없다」 = 거부 회차 challenge 잔존이 다음 회차 전제.
- 바꿀 자리: final.md Q2a `:16` 「거부 회차·빈 dev 회차 = `stages.sh:397`」 · Q3 `:21` 「reset 거부·빈 dev 회차 = `stages.sh:397`」 · 미해결7 `:101` 「거부 회차(…)와 빈 dev 회차는 `:397` 이 지금처럼 challenge 를 지운다」 · spec `:130` 「거부 회차·빈 dev 회차 = `:397` 삭제 유지」 / intent `:54` Q2a 판정 괄호 · `:56` Q3 소진 주체 괄호 · `:86` 미해결7 「거부·빈 dev 회차는 `:397` 이 challenge 를 지운다」 · `:113` spec 항목 — 네 곳 모두 「빈 dev 회차 = `:397` · 거부 회차 = 소진 없음(`:390` 이 새 challenge 를 쓰고 `:394` `return 1` · 만료 정리 = 다음 발급 시 덮어쓰기)」로 치환.

### Q9·spec 132
- 판정(정정): `ssh_script "reset:schema"` heredoc 본문 안 재export 2줄은 `export COLAB_OPS_ACK_TOKEN="${COLAB_RESEED_ACK_NONEMPTY-}"` · `export COLAB_OPS_ACK_BASIS="${COLAB_RESEED_ACK_BASIS-}"` 로 확정한다(빈 dev 회차 · env 미설정에서 값 "" 로 전개 · 도구는 빈 dev 면제라 무해).
- 근거: `reseed.sh:40` `set -euo pipefail` 아래 비인용 `<<EOF`(`stages.sh:452-455`) 는 로컬 전개 시 unbound variable 로 heredoc 자체가 실패 → 빈 dev schema 회차가 「스키마 재생성 실패」 로 blocked · `reset-gate.sh` 무변경 green 과 충돌 · `stages.sh:263` `"${COLAB_RESEED_ACK_NONEMPTY-}" "${COLAB_RESEED_ACK_BASIS-}"` 가 같은 파일의 기존 표기.
- 바꿀 자리: final.md Q9 `:55` 판정 · 정정 사실 `:109`(재export 2줄) · spec `:132` / intent `:68` Q9 판정 · `:115` spec 항목 — literal `"$COLAB_RESEED_ACK_NONEMPTY"` · `"$COLAB_RESEED_ACK_BASIS"` 를 `"${COLAB_RESEED_ACK_NONEMPTY-}"` · `"${COLAB_RESEED_ACK_BASIS-}"` 로 치환하고 「(`:263` 표기 · `set -u` 빈 회차 보호)」 부기.

### Q1·복제본 금지
- 판정(정정): spec 항목 1줄 추가 — 「`stages.sh` heredoc(`:266-370`)의 토큰 수학(`token_of` `:272` · challenge 만료·`countBeforeSha256`·토큰 대조 `:338-345` · nonce 발급 `:349-351`)을 제거하고 `sys.path.insert(0, os.path.dirname(RESET_TOOL))` → `import human_auth` 로 모듈 `issue()`/`verify()` 함수를 같은 프로세스에서 부른다 · 계수·기준선·`reset-ack.json`(`done`)·`RESET_TOKEN_MARK`/`RESET_CHALLENGE_MARK` 출력 계약 · `reset_show_token` `[ -t 1 ]`(`:227-241`) 은 무변 · 모듈의 isatty 는 CLI main(ship · purge) 에서만 · `verify` 결과 문구는 기존 `why` 5종 유지」. subprocess `python3 human_auth.py issue|verify` 호출은 쓰지 않는다.
- 근거: `stages.sh:262` `out="$(… python3 - …)"` 가 heredoc stdout 을 캡처하므로 CLI `issue` 의 「stdout TTY 일 때만 토큰」 규칙이 그 안에서는 항상 비 TTY 로 판정돼 `:227-241`·intent `:30`(reseed 의 TTY 자리 = `stages.sh`) 과 충돌 · heredoc 은 계수·기준선(`:298-327`)·`reset-ack.json`(`:283-296`) 과 토큰 수학이 한 프로세스라 분리 호출은 ack 기록을 두 벌로 만든다 · `stages.sh:13` `RESET_TOOL` 이 `services/core-api/ops/` 안이고 spec `:117` 이 `human_auth.py` 를 같은 디렉터리로 확정 · ops 디렉터리에 `human_auth.py` 미존재(함수 API 자유).
- 바꿀 자리: final.md spec `:131` 바로 아래 새 항목 1줄 · Q1 `:8` 교차 해소 끝에 「stages.sh heredoc 수학 제거 = import 경유」 부기 / intent `:114` 아래 spec 항목 1줄 추가 · `:51` Q1 판정 근거 끝에 같은 부기.

### intent:30(전사)
- 판정(정정): 줄 전체를 final.md `:106` 문장으로 교체 — 「정정(9라운드): TTY 검사는 reseed 경유 reset 도구(`reset_dev_environment.py`) 안에 둘 수 없다 — reseed 가 `ssh BatchMode`(`lib.sh:99-100`) → `docker run --rm --network host --user 0`(`stages.sh:38-46` · `-i`/`-t` 없음) 으로 부르므로 그 도구는 항상 비 TTY · reseed 의 TTY 자리 = `stages.sh` `reset_show_token` `[ -t 1 ]`(`:227-241`) · ship 의 TTY 자리 = `ops-auth.sh` `[ -t 0 ] && [ -t 1 ]`. purge 는 사람이 `docker run -it` 로 직접 부르므로(`purge_datasets.py:33` 런북 · 호스트 래퍼 금지 · Q2) 도구 안 `:115` 앞 TTY·토큰 존재 검사가 성립한다(정정 사실 1행).」
- 근거: 현재 `:30` 「purge 의 `docker run -it` 래퍼」·「도구 안 isatty 0건」 이 Q2 `:15-16`(호스트 래퍼 금지) · 정정 사실 `:106`(purge 도구 안 `:115` 앞 TTY 검사) · 같은 줄 뒷문장과 모순 · `stages.sh:38-46` `-it` 없음 · `:227-241` `[ -t 1 ]` 재확인.
- 바꿀 자리: intent `:30` 「- 정정(9라운드): …」 줄 전체 치환.

### intent:23·29(전사)
- 판정(정정): 검증 가능 문장 ⑴(`:23`) 과 확인 방법 ⑴(`:29`) 의 「비 TTY 3형태(Claude Bash · Codex bridge · `bash -c`)」 뒤에 「→ 판정(9라운드) 4형태(Workflow bypass lane 추가)」 를 각각 append 한다 · 원문 3형태 표기는 남긴다.
- 근거: final.md 미해결3 `:81` 「Workflow 레인(bypass) 을 4번째로 추가」 · 정정 사실 `:117` · spec `:141` 「비 TTY 4형태(… Workflow bypass lane)」 · intent `:70`·`:83`·`:123`·`:124` 는 이미 4형태 — `:23`·`:29` 만 3형태로 남아 있다.
- 바꿀 자리: intent `:23` 「⑴ 에이전트 세션(Claude Bash · Codex bridge · `bash -c`)에서 …」 문장 끝 · `:29` 「⑴ 비 TTY 호출 3형태(…) × 대상 4 경로 …」 항목 끝 — 두 자리에 append.

# 재검 4 지적(verify-4 · 닫힌 형태 그대로 intent 에 반영)

FINAL: ISSUES 2
⑷·Q4·Q5·Q10·spec 140 — 「`reset-gate.sh` 무변경 green」이 확정 판정(GO 회차 `:397` 생략 · challenge 경로 auth dir 이동)과 양립하지 않는다: `tests/reset-gate.sh:218` ⓓ‴ `[ -e "$CHALLENGE" ]` 와 `:230` 재사용 사례는 fake ssh 가 도구를 돌리지 않아 challenge 가 남고 확정적으로 red · `:99` `CHALLENGE="$FIXTURE_REMOTE/reset-challenge.json"` 도 경로가 바뀐다 · spec 130 자체가 ⓑ 계열 fixture 추가를 명시 — 판정을 「`reset-gate.sh` 갱신: ⓓ‴·재사용 사례는 fake docker 가 `/auth` challenge 를 지우는 fixture 로 대체 · `CHALLENGE` = 시험용 `COLAB_OPS_AUTH_DIR` · 나머지 사례 무변 · `dev-reseed-selftest` 안 green」으로 닫고 intent ⑷·Q4 근거·Q5 「유일한 선택」·Q10 「무변경 green」에 재검 정정으로 append(「red 면」 조건문 제거).
Q1×spec 115(ship 발급) — `issue` 는 「stdout 이 TTY 일 때만 토큰 · 비 TTY 면 77」인데 `ops-auth.sh` 는 「모듈 `issue` 출력 바이트를 ssh `sudo tee`」해야 하므로 stdout 을 캡처(파이프)할 수밖에 없어 항상 77 — 재검 3 이 `stages.sh:262` 캡처에 대해 찾은 결함이 ship 경로에 그대로 남았다 — `issue` 는 challenge JSON 을 로컬 파일 경로 인자(`--out <0600 tmp>`)로 쓰고 stdout 에는 토큰만 찍으며(캡처 0), `ops-auth.sh` 는 그 파일을 base64 → ssh `sudo tee` 뒤 unlink · purge 컨테이너도 같은 꼴 `--out /auth/purge-<id>-challenge.json` 으로 spec 115·124 를 고친다.
