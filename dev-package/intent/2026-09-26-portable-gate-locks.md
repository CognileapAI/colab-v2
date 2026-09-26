# Intent: 게이트 잠금 원시 연산의 이식 — util-linux `flock` 실행 파일 → python3 `fcntl.flock`(판정 규약 무변경)
메타 — 발의자: Ted · 작성 2026-09-26 · 승인 미승인(초안 · 12라운드 판정 기록 · Ted 확인 문구 · GitHub handle 대기)
- 판정 기록 포인터: 출처 · Ted 원문 · 판정 원칙 · 고정 사항 = 부모 intent `dev-package/intent/2026-09-25-harness-improvement.md` 판정 기록 10라운드(`:627` · 질문 5 「예」 · 「별도 intent 3: ⓑ fcntl 잠금」 · 지금 발행) · 감사 = `report.md` 권고 12ⓑ · 질문 5 · 부록 E-3 외 「참조」 절 · 표기 = 「판정」 자리 = 12라운드 판정값(초안 권고와 다르면 「초안 권고 ⓧ → 판정 …」) · 12라운드 판정자 = Opus blind 1 + 교차 점검 1(Fable 주간 한도 소진으로 Opus 가 대행) · 줄 번호 기준 = develop `5bb3d6fe`(총괄 계획 인용은 이 intent 와 같은 커밋의 개정본) · 2026-09-26 재열람.

## 문제
- 호스트 뮤텍스 · 도구 설치 잠금 · pg 슬롯이 util-linux `flock` **실행 파일**을 요구한다 — `_lock.sh:32` `command -v flock`(설치 잠금) · `:40` `flock 9` · `:89` `command -v flock`(호스트 뮤텍스) · `:104` `flock -n` · `:112` `flock -w` · `_pg.sh:82` `command -v flock` · `:100` `flock -n "$PG_SLOT_FD"`. 부재는 면제 없이 `red(준비 · 78)` 다(`_lock.sh:11` · `_pg.sh:59-68` · ADR-0005 `:52-54` 「면제 변수를 두지 않는다 … 없는 호스트가 합류하는 날 그때 3상태 변수를 만든다」).
- macOS 에는 util-linux `flock` 이 없다. 팀에 macOS · 비WSL 호스트가 있다(Ted 확인). 그 구성원은 로컬에서 `serial` 선언 게이트(`gates/config/parallelism.toml` · `grep -c '= "serial"'` = 17건 · `:23` 은 주석 · 종전 45 는 감사 E-3 수치를 옮긴 것) 와 DB 게이트 전부를 한 건도 판정할 수 없다 — 전부 78. 「같은 절차 → 같은 판정」이 OS 로 갈린다(감사 E-3 · 심각도 높음).
- 선택지 둘 중 ADR-0005 가 예고한 「3상태 면제 변수」는 green-by-skip 통로다(`_pg.sh:68` 「쓸 일이 없는 면제 변수를 미리 두면 그것이 곧 green-by-skip 통로」). 남는 길은 잠글 **수단**을 실행 파일 의존이 없는 것으로 바꾸는 것이다.
- `flock(1)` 을 전제로 한 자리 전수: `_lock.sh:32,40,89,104,112` · `_pg.sh:82,100` · `gate-host-mutex-selftest.sh:70,78`(fixture 점유 `flock -x … -c`) · `:153-166`(ⓓ flock 부재 PATH 수술) · `:280`(`flock -n "$LOCK" true`) · `:291`(`flock -w 5`) · `db-selftest.sh:442-456`(슬롯 고갈 fixture `flock -n 8`) · `:463-475`(flock 부재 PATH 수술 · `_pg.sh` 와 `_lock.sh` 두 벌) · 문서 `gates/README.md:13`(ⓓ) · `:100` · `:112` · `:126-130` · `parallelism.toml:23` · spec `2026-09-18-gate-host-mutex.md:16,31,34,63` · ADR-0005 `:46,49,52-54` · 총괄 계획 `:66`(2-3 「`flock -w` 상한 초과 = 78 유지」) · PR 2 spec `:100`. `ops-schedule-selftest.sh:127`(`flock -n 9` · 다른 게이트의 fixture)은 범위 밖에 적는다.

## 원한 결과 (proposed outcome)
- `_lock.sh` · `_pg.sh` 의 잠금 원시 연산이 python3 stdlib `fcntl.flock`(Linux · macOS 공통 `flock(2)`) 으로 바뀌고, 실행 파일 의존이 0 이 된다. 저장소 선례 = `scripts/deploy_release.py:103` · `scripts/product_release.py:287`.
- 판정 규약 무변경 — 호스트 뮤텍스: `serial` 선언만 잡는다 · 잠금 키 `TMPDIR` 하나 · 상한 `COLAB_GATE_MUTEX_WAIT`(900) · `::gate-waiting::` 시도 직전 1회 + 결과 1회 · 세 갈래 78 은 `readiness_env_wait` 한 경로(⑴ 수단 부재 = 이제 「python3 부재」 ⑵ 잠금 디렉터리·파일 불가 ⑶ 상한 초과) · 면제 = `parallel` 선언 · `COLAB_GATE_MUTEX_HELD=1` 둘뿐. pg 슬롯: `COLAB_PG_MAX_CONCURRENT`(4) · `COLAB_PG_SLOT_WAIT`(900) · 슬롯 파일 `slot-<i>` · 고갈 78. 설치 잠금 `gate_lock_fd`: 0/78 API(`_venv.sh:21` · `contract-lint.sh:31` · `event-lint.sh:46` 호출부 무변경).
- 잠금은 여전히 **bash 의 fd 에 산다** — `{VAR}>` 로 연 fd(`_lock.sh:98` · `_pg.sh:95`)가 exec 를 건너 살아남고 · 프로세스가 죽으면 커널이 풀고 · `gate_mutex_spawn`(`_lock.sh:143`)이 데몬 자식에서 fd 를 닫는다. 셀프테스트 ⑴⑵(`gate-host-mutex-selftest.sh:283-312`)는 케이스 · 단언 무변경 green.
- 검증 가능 문장: ⑴ macOS 구성원이 `command -v flock` 이 빈 셸에서 `bash gates/run.sh gate-host-mutex-selftest` 를 돌려 종료코드 0 과 요약줄 「케이스 N건」(ⓐ~ⓗ · ⑴⑵ 전부 OK)을 얻는다 ⑵ 같은 셸에서 `bash gates/run.sh db-selftest`(Docker Desktop)의 「슬롯 고갈 = 준비 실패」 · 「python3 부재 = 준비 실패」 두 구분이 OK 다 ⑶ WSL 호스트에서 `flock` 을 PATH 에서 지운 셸(`env -i PATH=<flock 없는 bin>`)로 같은 두 게이트가 green 이다 — 즉 Linux 호스트가 macOS 의 모양을 값으로 재현한다 ⑷ `python3` 을 PATH 에서 지우면 두 게이트의 해당 구분이 78 이고 `::gate-readiness-failure::` 에 「python3」 가 있다 ⑸ `gates/run.sh all` 요약의 「호스트 뮤텍스 : 잠금 N건」 N 이 `serial` 선언 건수와 같다(README `:117`).

## 가치 가설
- macOS · 비WSL 구성원은 로컬에서 serial · DB 게이트를 CI 와 같은 판정으로 얻는다 — 「다른 기계에서는 CI 가 유일한 판정원」(감사 `:130`)이 해소된다.
- 하네스는 실행 파일 의존 하나를 잃고 면제 변수는 얻지 않는다 — 3상태 규율(ADR-0004 · ADR-0005)이 OS 경계에서도 같은 값으로 선다.
- 확인 방법: PR 요약 「원한 결과 ↔ 실제 ↔ 근거」 표 — ⑴ macOS 1대 실측 로그(`gate-host-mutex-selftest` · `db-selftest` 종료코드 · 요약줄) ⑵ WSL flock 제거 셸 실측 로그 ⑶ CI `ubuntu-latest`(`ci.yml:18` 등 16 잡) 의 같은 두 게이트 green ⑷ 병합 뒤 첫 전수 회차의 「잠금 N건 · 면제 M건 · 대기 누계」가 직전 회차와 같은 자릿수.

## 영향 범위
- 사용자 / 화면: 없음 — 개발 하네스.
- 서비스 · 스키마 · 계약: `gates/tools/_lock.sh` · `_pg.sh` · 신설 헬퍼(Q4) · `gate-host-mutex-selftest.sh` fixture(Q8) · `db-selftest.sh:442-475` fixture · `gates/README.md:13,100,112,126-130` 문구 · `parallelism.toml:23` 주석 · 새 ADR(Q9). 제품 코드 · `contracts/**` · 훅 정의(`.claude/settings.json` hooks · `.codex/hooks.json`) 무변경. `.github/workflows/ci.yml` 무변경(runner 는 `ubuntu-latest` 유지).
- 파일 소유 · 순서(총괄 §3): `_lock.sh` · `_pg.sh` · `gate-host-mutex-selftest.sh` 는 이 PR → PR 2 순차(`:152-154` · Q10) · `gates/README.md` 는 `:155` 에서 E0 → PR 3 소유 → 이 PR(잠금 문구 `:13,100,112,126-130` 만) → PR 3(`:245` C3 · 3-7) 순차 · 순서 행 = `:154`(intent ⓑ 행) · `_flock.py` · `db-selftest.sh` · `parallelism.toml` 은 §3 의 다른 PR 소유 없음.
- 해시 집합: 오늘 `eval/harness/config-paths.txt:13` 은 `gates/**` 를 포함한다 → 소형 PR A(Q2 축소 · `gates/**` 제외 후 `harness-eval.sh` · `harness-eval-selftest.sh` · `_readiness.sh` 만 재등재) **뒤**에 병합하면 이 PR 은 회차 불요. 앞이면 회차 1회(≈8 USD · T12)가 든다(Q10).
- 계약 파괴 여부: 아니오 — 종료코드 · 표식 · 환경변수 이름 · 요약줄 형식 전부 무변경. 바뀌는 것은 잠금을 거는 프로세스(`flock` 바이너리 → `python3`)뿐이다.

## 제약
- 판정 규약 무변경(10라운드 확정) — 상한을 늘리거나 · 재시도하거나 · 면제 변수를 두어 green 을 만들지 않는다. 세 갈래 78 · `::gate-waiting::` 값 2개 · 잠금 키 `TMPDIR` 하나 · 주입구 변수 0(`_lock.sh:64-66`) 유지.
- python3 는 이미 실행기의 전제다 — `gates/run.sh:190` 이 뮤텍스 획득(`:235`) 앞에서 `python3 gates/tools/parallelism.py` 로 선언표를 읽는다. 이 intent 가 새 도구 의존을 더하지 않는다.
- bash ≥ 4.1 — 동적 fd `{VAR}>`(`_lock.sh:98` · `_pg.sh:95`)는 오늘도 macOS 기본 `/bin/bash` 3.2 에서 돌지 않는다. 이 intent 는 그 전제를 바꾸지 않으며 `docs/development/onboarding.md`(PR 3 추가분)가 기계 1대당 절차로 적는다.
- Windows 는 네이티브 경로가 없다 — `scripts/dev.ps1:119-122` 가 `gate` 를 `wsl.exe … python3` 로 넘긴다. WSL = Linux 커널 · `fcntl.flock` 가용.
- ADR 이력 무수정 · 새 규칙은 새 ADR · 승인 intent append-only · 훅 정의 무변경 · 병합은 사람 · 게이트 종료코드 0/1/78(`AGENTS.md`).
- 셀프테스트 regime 무변경 — 케이스 집합(ⓐ~ⓗ · ⑴⑵ · db-selftest 구분) · 값 증거(실경과 ≥ 상한 · `waited` ≥ 1 · 잠금 건수) · 「실제 호스트 잠금 무접촉」(`TMPDIR` 을 `mktemp -d` 로 물림)은 유지. fixture 만 바뀐다(Q8).

## 설계트리 (grill-me 결과)
- Q1 잠금 원시 연산 → 판정 ⓐ(12라운드 · Opus blind). ⓐ `fcntl.flock`(`flock(2)` · open file description 에 붙는 잠금 · fork/exec 로 물려받은 fd 에 그대로 남고 마지막 fd 가 닫힐 때 풀린다 — util-linux `flock <fd>` 와 같은 커널 호출) ⓑ `mkdir` 원자 잠금(커널이 풀지 않는다 → 죽은 잠금 · pid/나이 휴리스틱 = 새 정책) ⓒ `fcntl.lockf`(POSIX 레코드 잠금 · 같은 프로세스가 그 파일의 **어느** fd 를 닫아도 풀리고 fork 자식에 상속되지 않는다 → `gate_mutex_spawn` 모델과 ⑴⑵ 의 의미가 바뀐다) ⓓ perl `flock`. 권고 ⓐ — 판정 규약 「잠금은 fd 로 산다 · 죽으면 커널이 푼다」(`_lock.sh:72-75`)를 한 글자도 바꾸지 않는 유일한 선택지이고, 저장소 선례(`deploy_release.py:103`)와 같다.
  - 판정 근거(12라운드): 같은 `flock(2)` syscall · 선례 `scripts/deploy_release.py:103` · `scripts/product_release.py:287`. WSL(kernel 6.18) 실측 = 자식이 부모 fd 잠금 rc 0 · 부모 보유 중 다른 open 의 `LOCK_NB` rc 1 · 부모 close 뒤 rc 0. ⓑ 는 pid·나이 휴리스틱 = 새 정책 · ⓒ 는 fork 자식 상속 없음 → 자식이 잠그는 모델 불성립 · ⓓ 는 새 도구 의존. 뒤집힐 조건 = macOS 실측에서 `ENOTSUP` 또는 자식 종료 뒤 잠금 해제(검증 명령 second rc 0).
- Q2 잠금이 bash 프로세스 트리를 어떻게 건너는가 → 판정 ⓐ(12라운드 · Opus blind). ⓐ bash 가 종전대로 `{VAR}>` 로 fd 를 열고, python3 **자식**이 그 fd 번호를 인자로 받아 `fcntl.flock(fd, …)` 뒤 종료한다 — 잠금은 bash 가 쥔 open file description 에 남는다(python 은 상속 fd 를 시작 시 닫지 않는다) · exec 생존 · 사망 해제 · `gate_mutex_spawn` 의 `{fd}>&-` 가 그대로 유효 ⓑ python3 장기 보유 프로세스 + 파이프(bash 가 죽어도 보유자가 남을 수 있다 → 죽은 잠금). 권고 ⓐ — fd 모델 무변경이라 ⑴⑵ · `run.sh:913-928`(pool 부모가 쥐고 자식은 fd 닫음) · `frontend-visual.sh:84` 호출부가 한 줄도 안 바뀐다.
  - 판정 근거(12라운드): `{VAR}>` fd 는 CLOEXEC 없음(`_lock.sh:136`) · 셀프테스트 ⑴(`gate-host-mutex-selftest.sh:283-292`)이 exec 두 번 뒤 보유를 값으로 보임 · python 은 상속 fd 를 시작 시 닫지 않음(PEP 446 은 python 이 새로 만드는 fd 만 non-inheritable) · `flock(2)` 잠금은 open file description 에 붙어 bash 쪽 fd 가 남는 한 유지(WSL probe 0 · 1 · 0). ⓑ 장기 보유자는 `_lock.sh:73` 「죽은 잠금이 남지 않는다」를 깬다. 전제 = helper 는 받은 fd 번호에 `flock` 만 한다(`LOCK_UN` · 재open 금지).
- Q3 상한 대기(`flock -w`)의 구현 → 판정 ⓐ 호스트 뮤텍스 · ⓑ pg 슬롯 현행 루프(12라운드 · Opus blind · 슬롯 쪽 = 해소 5). ⓐ python3 안에서 blocking `LOCK_EX` + `signal.alarm(wait_s)` · 핸들러가 예외를 던져 EINTR 재시도(PEP 475)를 끊는다 → 종료 0 획득 / 1 상한 · 실경과는 종전대로 bash 가 `date +%s` 로 잰다(`_lock.sh:110-114`) ⓑ bash 폴링 `LOCK_NB` + `sleep 1`(`_pg.sh:98-108` 모양). 권고 ⓐ 호스트 뮤텍스 · ⓑ pg 슬롯(현행 루프 유지) — 뮤텍스는 프로세스 1개로 `flock -w` 와 같은 벽시계 · 슬롯은 슬롯 i 마다 fd 를 바꿔 여는 구조라 루프가 이미 bash 에 있다. 슬롯 루프의 python3 기동 비용(최대 4회/초 · 1회 ≈ 20-30 ms)은 미해결 5 로 실측.
  - 판정 근거(12라운드): util-linux `flock -w` 도 blocking `flock` + 타이머 · EINTR 로 끊는 같은 구현 · WSL 실측 점유 중 `alarm(2)` → rc 1 · 경과 2.02초. 교차 점검 7 반영 — PEP 475 상 처리기가 예외를 던지지 않으면 `flock` 이 자동 재시도되고 기본 처리면 rc 142 로 죽으므로 「예외를 던지는 SIGALRM 처리기 → 종료 1」을 helper 계약 필수로 둔다. `_lock.sh:87` 이 `COLAB_GATE_MUTEX_WAIT=0` 을 허용하고 `signal.alarm(0)` = 타이머 해제(무한 대기)라 `--wait 0` → `LOCK_NB` 치환 필수.
- Q4 헬퍼의 자리 → 초안 권고 ⓐ(`<fd> --nb | --wait <초>` · 종료 0/1) → 판정 ⓐ + 계약 보강(무한 대기 모드 · 종료 0/1/2/3 · `python3 -I`)(12라운드 · Opus blind). ⓐ `gates/tools/_flock.py` 파일 1개(`<fd> --nb | --wait <초>` · 종료 0/1 · stdlib only) 을 `_lock.sh` · `_pg.sh` · 두 셀프테스트 fixture 가 같이 부른다 ⓑ 각 호출 자리에 `python3 -c '…'` 인라인. 권고 ⓐ — 「한 디렉터리가 표식·정책을 두 벌로 갖지 않는다」(`_pg.sh:41-42` · `_lock.sh:19`) · 단위 시험 가능 · 셸 인용 오류 0. 파일은 `gates/tools` 안이라 소형 PR A 뒤 해시 집합 밖(영향 범위).
  - 판정 근거(12라운드): 호출 자리 = `_lock.sh:40`(무한 대기 · `gate_lock_fd`) · `:104`(nb) · `:112`(wait) · `_pg.sh:100`(nb) · selftest fixture 4곳 · `db-selftest.sh:445` — 초안 인터페이스에 무한 대기 모드가 빠져 `_flock.py <fd> [--nb | --wait <초>]`(인자 없음 = 무한 대기)로 보강. 종료 = 0 획득 · 1 경합/상한 · 2 사용 오류 · OSError · 3 import 실패(판정자 원안 「2 에 import 실패 포함」은 교차 점검 7 로 3 분리). `python3 -I` = PYTHONPATH 의 `fcntl` 가림 · user site 차단 · 기동 단축.
- Q5 「수단 부재」 갈래의 의미 → 초안 권고 ⓐ(`command -v python3` · 「python3 이 PATH 에 없다」) → 판정 조합 ⓐ + 판별식 보강(`command -v python3` 또는 helper 종료 3 → ⑴ · 사유 「python3(fcntl) 실행 불가」)(12라운드 · Opus blind). ⓐ ⑴ 갈래 유지 · `command -v python3` 로 검사 · 사유 문구 「python3 이 PATH 에 없다」 · 같은 `readiness_env_wait` 경로 78 ⓑ 갈래 삭제(python3 는 `run.sh:190` 의 전제라 도달 불가). 권고 ⓐ — `_lock.sh` · `_pg.sh` 는 source 로 직접 불리고(셀프테스트 `db-selftest.sh:472-475` · `frontend-visual.sh`) 그 경로에는 `run.sh:190` 이 없다 · 「실행기가 아는 사실은 무의미하거나 판정이거나」(ADR-0005) · 셀프테스트 ⓓ 는 PATH 수술 대상을 `flock` → `python3` 로 바꿔 유지.
  - 판정 근거(12라운드): ⓑ 삭제 시 python3 부재가 `_pg.sh:93-110` 에서 900초 뒤 「슬롯 고갈」 · `_lock.sh:112` 에서 0초 「상한 초과」로 오귀속 · macOS `/usr/bin/python3` 는 CLT stub 이라 `command -v` 참 · 실행 실패. 판정자 원안 「종료 {0,1} 밖 = ⑴」은 교차 점검 7 로 좁힘 — rc 142(기본 SIGALRM) · 130(KeyboardInterrupt) · 2(사용 오류 · OSError)는 ⑴ 로 읽지 않고, ⑴ 은 import 실패 전용 종료 3 하나. 판정값 78 · 판정 규약 무변경 — 바뀌는 것은 사유 문구뿐.
- Q6 Windows · WSL 정합 → 판정 ⓐ(12라운드 · Opus blind). ⓐ 변경 없음 — `dev.ps1:119-122` 가 모든 `gate` 호출을 WSL 로 보내므로 Windows = Linux 경로 · `msvcrt` 분기 0 ⓑ 네이티브 Windows(`msvcrt.locking`) 분기 추가. 권고 ⓐ — 없는 경로에 분기를 두면 그것이 곧 시험되지 않는 갈래다.
  - 판정 근거(12라운드): `scripts/dev.ps1:14`(도구 이름 제한) · `:119-122`(`wsl.exe --cd … -e python3`) → `gate` 는 WSL 로만 간다. 네이티브 Windows 직접 호출은 `import fcntl` 실패 → helper 종료 3 → Q5 ⑴ → 78(green 아님 · 판정자 원문의 「종료 2」는 교차 점검 7 로 3). 뒤집힐 조건 = 팀이 WSL 없는 네이티브 Windows 게이트 실행을 요구로 확정.
- Q7 pg 슬롯 표를 파일로 유지하는가 → 판정 ⓐ(12라운드 · Opus blind). ⓐ 유지 — `PG_SLOT_DIR/slot-<i>`(`_pg.sh:77,95`) 파일마다 `LOCK_NB` · 슬롯 수 = 파일 수 · 죽으면 커널이 푼다 ⓑ 계수 파일 1개(python 이 읽고-증가-쓰기 · 죽은 슬롯 회수 정책 필요) ⓒ 슬롯 데몬. 권고 ⓐ — 규약 · 셀프테스트 fixture(`db-selftest.sh:444` 가 `slot-0` 을 직접 잡는다) · `COLAB_PG_SLOT_DIR` 의미 무변경.
  - 판정 근거(12라운드): `_pg.sh:75`(`PG_SLOT_DIR` · `COLAB_PG_SLOT_DIR` 주입 · 초안의 `:77` 은 함수 선언 줄) · `:95`(`slot-$i` open) · `:100`(nb) — 원시 연산만 바꿔도 「슬롯 수 = 파일 수 · 죽으면 커널이 푼다」 불변식 유지. ⓑ 계수 파일 · ⓒ 데몬은 회수 정책 = 새 규칙(범위 밖 「잠금 의미 변경」). 대기 중 python 기동 비용은 해소 5.
- Q8 셀프테스트 변경 허용 범위 → 판정 ⓑ(12라운드 · Opus blind · 확신 중간). regime(케이스 · 단언 · 값 증거) 무변경 · fixture 만: `gate-host-mutex-selftest.sh:70,78`(점유자 `flock -x … -c`) · `:280` · `:291` → `_flock.py` 를 부르는 bash 점유자(FIFO 동기화 유지) · `:153-166` ⓓ PATH 수술 = `python3` 제거 · `:263` `/proc/$$/fd` → `/dev/fd` 나열 + `os.fstat` inode 대조(Linux · macOS 공통 · macOS `/dev/fd` 는 symlink 가 아니라 `readlink` 불가) · `:39` `mktemp -d -p` → `mktemp -d "${TMPDIR:-/tmp}/…XXXXXX"` · `db-selftest.sh:442-456` 점유자 `flock -n 8` → `_flock.py` · `:463-475` python3 제거. ⓐ 위 fixture 이식만 ⓑ ⓐ + 케이스 ⓘ 「`flock` 바이너리 부재 · python3 존재 → green」(PATH 수술 · Linux 호스트가 macOS 모양을 값으로 증명) ⓒ 케이스 축소. 권고 ⓑ — ⓘ 없이는 「macOS 에서 된다」가 macOS 1대의 수동 실측에만 남는다 · CI `ubuntu-latest` 가 매 PR 마다 그 모양을 잰다.
  - 판정 근거(12라운드): CI 는 `ubuntu-latest` 에서 `./gates/run.sh selftest`(`ci.yml:798` · `run.sh:24,33` `ALL_GATES`)로 두 selftest 를 돌리고 CI 호스트엔 `flock` 이 있어 ⓘ 없이는 바이너리 의존이 되돌아와도 green — ⓘ 가 「실행 파일 의존 0」을 값으로 잰다. ⓘ 는 두 파일 대칭(host-mutex = `gate_host_mutex_acquire` · db = `pg_slot_acquire` · `gate_lock_fd`) · 요약줄 「케이스 10건」 → 11건 · README `:13` 동반 = regime 확장. 뒤집힐 조건 = Ted 가 「케이스 집합 불변」을 건수까지 고정 → ⓘ 를 ⓓ 안의 green 대조 단언으로.
- Q9 ADR 자리 → 초안 권고 ⓐ(번호 = 병합 시점 다음 빈 번호) → 판정 ⓐ + `대체함: 없음` · 번호 = 파일 ∪ 예약 최댓값 + 1(12라운드 · Opus blind). ⓐ 새 ADR 「게이트 잠금은 stdlib `fcntl.flock` · 실행 파일 의존 0 · 면제 변수 없음 · 판정 규약은 ADR-0005 개정 블록 그대로」 · ADR-0005 `:52-54` 의 「합류하는 날 3상태 변수」 예고를 이 ADR 이 대체한다고 적고 0005 본문은 무수정 ⓑ ADR 없음(코드 + README 만). 권고 ⓐ — 0005 가 명시한 계획(면제 변수)과 다른 길을 택하므로 그 결정이 기록 없이 코드에만 남으면 다음 사람이 0005 를 읽고 면제 변수를 만든다. 번호 = 병합 시점 다음 빈 번호(숫자는 병합 때 확정).
  - 판정 근거(12라운드): 이번 결정은 ADR-0005 `:52-54` 「합류하는 날 3상태 변수」의 반대(변수 영구 부재)라 새 규칙 = 새 ADR · `adr_gate.py:79-93` 은 `대체함` 링크 시 0005 쪽 `상태: superseded` + `대체됨` 편집을 요구해 이력 무수정과 충돌 → `대체함: 없음` · 0005 `:52-54` 예고 문장만 대신한다고 본문에 적는다. 번호 — 파일 0001-0010 · 예약 0011(PR 2 B3) · 0012(PR 4)(총괄 `:160,207`) · 0013(S-auth · spec B `:176`) → 「파일 ∪ 예약(approved intent · 병합 spec) 최댓값 + 1」 = 오늘 0014 · 교차 점검 2 로 CI intent(`2026-09-26-ci-harness-eval-run.md`)와 이 규칙으로 통일 · 병합 순서에 따라 0014/0015.
- Q10 반입 순서 → 판정 ⓐ(12라운드 · Opus blind). ⓐ 소형 PR A 병합 **뒤**(B 와 병렬 · 파일 교집합 0) · PR 2 lane 착수 **전** 병합(= PR 2 head 회차 앞 · 총괄 §10.2 행 5c) 의 단독 소형 PR(해시 집합 밖 · 회차 불요 · lane 1 · 병합은 사람) · 파일 소유 = 이 PR → PR 2 순차(총괄 §3 `:152-153` 이 `_lock.sh` = PR 2 2-3 · `_pg.sh` = PR 2 2-1h 로 둔다 · `:154` intent ⓑ 행 · PR 2 lane 은 이 PR 병합 뒤 develop 기준 = 같은 파일 동시 lane 0) · PR 2 2-3 문구(총괄 `:66` 「`flock -w` 상한 초과 = 78 유지」)는 「`_flock.py --wait` 상한 초과 = 78 유지」로 읽는다 ⓑ 소형 PR A 에 합침(A 는 해시 집합 파일 · 회차 1회로 끝내는 PR — 잠금 변경이 섞이면 회차 실측이 잠금 변경까지 덮는다) ⓒ PR 2 에 합침(긴 개방 기간 · 다른 소유). 권고 ⓐ — 10라운드 「소형 PR A 뒤 첫 회차가 새 기준선」과 양립하고 회차 비용 0.
  - 판정 근거(12라운드): `eval/harness/config-paths.txt:13` 이 `gates/**` 포함 · develop `2ed59e9a` 에 PR A 없음 → 지금 병합하면 회차 1회(≈8 USD · ≈35분)이고 이 계정은 2026-10-02 03:00 KST 까지 로컬 회차 불가. 총괄 `:152-154`(`_lock.sh` = PR 2 2-3 · `_pg.sh` = PR 2 2-1h) · `:227` 행 5c 가 순서를 이미 적음 · PR 파일 집합과 PR A 재등재 3파일 교집합 0 · `_readiness.sh` 무변경(해시 불변 값 2개를 PR 요약에). 뒤집힐 조건 = PR 2 lane 착수까지 PR A 미병합 → 이 PR 을 PR 2 head 회차에 포함(회차 1회 공유).
  - 회차 경로 = `harness-eval-run.yml` dispatch(CI intent PR ① · `2026-09-26-ci-harness-eval-run.md`) — 10-02 대기의 대안. PR ① 병합 뒤에는 뒤집힐 조건의 회차(PR 2 head 회차 공유)를 로컬 10-02 대기 없이 CI dispatch 로 돌린다(교차 점검 9).

## 미해결 질문
- 0건 — 초안의 4건(1 · 4 · 5 · 6)은 12라운드에서 닫았다(아래 「해소된 질문 (12라운드)」). 초안 2(「범위 밖」 이동) · 3(ADR 번호)은 초안에서 이미 닫았고, 3 의 번호 규칙은 Q9 판정(파일 ∪ 예약 최댓값 + 1)으로 갱신했다.

## 해소된 질문 (12라운드)
- 1 macOS `mktemp -p` → 판정 = 판본 차 실측 없이 닫음 · 세 자리(`gate-host-mutex-selftest.sh:39` · `db-selftest.sh:28,48`) 모두 `mktemp -d "${TMPDIR:-/tmp}/<이름>-XXXXXX"`(GNU · BSD 공통 형태 → `-p` 지원 여부 무관). 근거: 초안 목록은 `db-selftest.sh:28,48` 누락 · macOS `TMPDIR` 끝 `/` 로 생기는 `//` 는 경로 해석에 무해 · 잠금 키 비교는 selftest 자신의 `CTMP`(`:49-51`). 증명 = macOS 에서 selftest green 그 자체.
- 4 `ops-schedule-selftest.sh:127` → 판정 = 이 intent 에서 옮기지 않음(범위 밖 확정 · 확신 중간). 근거: 대상 `infra/ops/run-scheduled.sh:27` `flock -n 9` 는 EC2(Linux) 운영 코드 · `infra/**` = deploy 규칙 적용 · 같은 selftest `:128` `sha256sum` 은 GNU 전용이라 flock 만 옮겨도 macOS 판정값이 바뀌지 않음(이득 0). 뒤집는 조건 = PR 3 macOS 온보딩 실측이 `ops-schedule-selftest` 를 로컬 필수 게이트로 목록에 올릴 때 → fixture 만 `_flock.py` 로 옮기는 별도 소형 PR.
- 5 pg 슬롯 루프 python 기동 비용 → 판정 ⓐ 현행 bash 폴링 루프 유지 · `python3 -I` 호출 · db-selftest 「슬롯 고갈」(`COLAB_PG_SLOT_WAIT=2`) 실경과를 WSL · macOS 에서 실측해 PR 요약에(확신 중간). 근거: 비용은 대기 중에만(`_pg.sh:92-110` · 빈 슬롯이면 첫 반복에서 return) · 상한 판정은 벽시계 deadline(`:91,103`)이라 반복이 느려져도 판정 시각만 늦고 green 으로 바뀌지 않음. 뒤집는 조건 = macOS 반복 1회 오버헤드(최대 슬롯 수 × 기동) > 0.5초 또는 고갈 케이스 실경과 > 상한 + 2초 → ⓑ(슬롯 fd 목록 1회 기동).
- 6 macOS bash 판본 전제의 자리 → 판정 ⓐ PR 3 `docs/development/onboarding.md`(기계 1대당 절차) · 이 PR 은 README 에 새 문장을 넣지 않음 · `BASH_VERSINFO` 4.1 미만 → 78 같은 기계 강제는 범위 밖(확신 중간). 근거: `run.sh:181` `declare -A` · `_lock.sh:98` `{VAR}>` 모두 bash 3.2 에서 실패 · `gates/README.md` 는 이 PR 뒤 PR 3 순차 소유(총괄 `:154`). 뒤집는 조건 = macOS 구성원 실행에서 bash 3.2 오류가 78 이 아닌 값(판정 red · 문법 오류)으로 관측 → PR 3 또는 별도 PR 에서 guard 추가.

## 정정 사실 (12라운드)
- `serial` 선언 = 17건 재확인(`grep -c '= "serial"'` · `parallelism.toml:23` 은 주석이라 제외 · 종전 45 는 감사 E-3 수치). 검증 문장 ⑸(`run.sh all` 요약 「잠금 N건」 = 17)는 WSL · CI 전용 — `run.sh:907` `date +%s.%N` 이 BSD 에서 동작하지 않아 macOS 에 요구하지 않고 온보딩 목록(PR 3)에 싣는다.
- fd 상속 기제(실측 확인): `{VAR}>` fd 에 CLOEXEC 없음(`_lock.sh:136`) · python 은 상속 fd 를 시작 시 닫지 않음(PEP 446 은 python 이 새로 만드는 fd 만 non-inheritable) · `flock(2)` 잠금은 open file description 에 붙어 자식 종료 뒤에도 같은 description 을 가리키는 bash fd 가 잠금을 유지. WSL(kernel 6.18) probe = child 0 · second 1 · after close 0.
- PEP 475 EINTR: 신호 처리기가 예외를 던지지 않으면 `flock` 이 자동 재시도되어 `alarm` 이 대기를 끊지 못한다 · 기본 SIGALRM 처리는 프로세스를 rc 142 로 죽인다 → 예외를 던지는 처리기가 필수. WSL 실측 = 점유 중 `alarm(2)` → rc 1 · 경과 2.02초.
- `COLAB_GATE_MUTEX_WAIT=0` 허용(`_lock.sh:87`) · util-linux 는 `-w 0` 을 `-n` 으로 특례 처리 · `signal.alarm(0)` 은 타이머 해제(무한 대기) → helper 가 `--wait 0` 을 `LOCK_NB` 로 바꿔야 같은 동작.
- `_pg.sh` 슬롯 디렉터리 정의 = `:75`(초안 Q7 의 `:77` 은 `pg_slot_acquire` 선언 줄).
- `mktemp -d -p` 자리 = `gate-host-mutex-selftest.sh:39` + `db-selftest.sh:28,48`(초안 Q8 목록은 앞의 1자리만).
- 종전 ⓓ PATH 수술 목록(`gate-host-mutex-selftest.sh:157`)에는 python3 가 없다 → 이식 뒤 ⓓ 는 그대로 「python3 부재 → 78」.
- 초안 Q4 인터페이스에 `gate_lock_fd`(`_lock.sh:40`) 의 무한 대기 모드가 빠져 있었다.
- macOS `/usr/bin/python3` = CLT stub — CLT 가 없어도 `command -v` 는 참 · 실행은 실패 → `command -v python3` 만으로 ⑴ 을 판별할 수 없다.
- ADR 번호: 파일 0001-0010 · 예약 0011(PR 2 B3) · 0012(PR 4)(총괄 `:160,207`) · 0013(S-auth · spec B `:176`) → 초안 「다음 빈 번호」(파일 기준)는 예약과 충돌할 수 있다.

## spec 항목 (12라운드)
- 헬퍼 1개 = `gates/tools/_flock.py`(stdlib only) · 인터페이스 `_flock.py <fd> [--nb | --wait <초>]`(인자 없음 = 무한 대기 · `gate_lock_fd`) · 호출은 `python3 -I` · `_lock.sh` · `_pg.sh` · 두 selftest fixture 가 같이 부른다.
- fd 모델: bash 가 `{VAR}>` 로 fd 를 열고 번호를 넘긴다 · helper 는 받은 번호에 `flock` 만(`LOCK_UN` · 재open 금지) 하고 끝난다 · `gate_mutex_spawn` `{fd}>&-` 무변경.
- `--wait <초>` = blocking `LOCK_EX` + `signal.alarm(초)` · 예외를 던지는 SIGALRM 처리기 → 종료 1 · `--wait 0` → `LOCK_NB` · KeyboardInterrupt 는 1 이 아닌 코드 · 실경과는 종전대로 bash `date +%s`(`_lock.sh:110,113,119`).
- 종료 계약: 0 획득 · 1 경합/상한 · 2 사용 오류 · OSError · 3 import 실패(`fcntl`) → 종료 3(또는 `command -v python3` 실패)만 readiness 78 ⑴ 「python3(fcntl) 실행 불가」 · rc 142 · 130 · 2 는 ⑴ 로 분류하지 않는다.
- pg 슬롯: 파일 `PG_SLOT_DIR/slot-<i>` 유지 · 현행 bash 폴링 루프 유지 · 슬롯마다 `python3 -I _flock.py <fd> --nb` · 「슬롯 고갈」 실경과 WSL · macOS 실측을 PR 요약에(해소 5 뒤집는 조건 2개 대조).
- selftest: fixture 이식(`gate-host-mutex-selftest.sh:39,70,78,153-166,263,280,291` · `db-selftest.sh:28,48,442-456,466-475`) + 케이스 ⓘ 「`flock` 바이너리 부재 · python3 존재 → green」을 두 파일 대칭으로 · PATH 수술의 python3 는 `python3 -c 'import sys;print(sys.executable)'` 실물 링크(pyenv shim 아님) · ⑵ fd 목록 = spawner 가 띄운 python 자식이 `/dev/fd` 나열 + `os.fstat` (st_dev, st_ino) 를 `os.stat(LOCK)` 과 대조 · 요약줄 「케이스 11건」 · README `:13` 동반.
- `mktemp -d "${TMPDIR:-/tmp}/<이름>-XXXXXX"` — `gate-host-mutex-selftest.sh:39` · `db-selftest.sh:28,48` 3자리.
- 새 ADR: 「게이트 잠금 = stdlib `fcntl.flock` · 실행 파일 의존 0 · 면제 변수 없음」 · `대체함: 없음` · 본문에 ADR-0005 `:52-54` 예고 문장(「합류하는 날 3상태 변수」)을 이 ADR 이 대신한다고 기재 · 0005 무수정 · 번호 = 병합 시점 「파일 ∪ 예약 최댓값 + 1」(오늘 0014 · CI intent 와 병합 순서에 따라 0014/0015).
- Windows: `msvcrt` 분기 0 · `scripts/dev.ps1 gate` 진입점 유지.
- PR 요약: 해시 불변 증명(해시 집합 파일 교집합 0 · `_readiness.sh` 무변경) · PR 2 2-3 문구(총괄 `:66` `flock -w`)는 `_flock.py --wait` 로 읽는다.
- macOS 검증 명령(Homebrew bash 안): 사전 `bash --version` · `python3 -I -c 'import fcntl,sys;print(sys.version)'` → fd 상속 `exec {fd}<gates/tools/_lock.sh` · `python3 -I -c 'import fcntl,sys;fcntl.flock(int(sys.argv[1]),fcntl.LOCK_EX|fcntl.LOCK_NB)' "$fd"; echo child=$?`(기대 0) · `python3 -I -c 'import fcntl,sys;fcntl.flock(open(sys.argv[1]),fcntl.LOCK_EX|fcntl.LOCK_NB)' gates/tools/_lock.sh; echo second=$?`(기대 1) · `exec {fd}<&-` 뒤 second 재실행(기대 0) → 병합 뒤 `command -v flock; bash gates/run.sh gate-host-mutex-selftest; echo rc=$?` · `bash gates/run.sh db-selftest; echo rc=$?`.

## 범위 밖 (명시 제외)
- 면제 변수(`COLAB_*_LOCK_EXEMPT` 류) 신설 — ADR-0005 「green-by-skip 통로」 · 두지 않는다.
- 잠금 의미 변경 — 키(`TMPDIR` 하나) · 단위(게이트 1건) · 상한 기본값(900) · 면제 집합 · 표식 형식 · 요약줄. `serial`/`parallel` 선언표 자체.
- `gate_lock_fd` 의 fd 9 고정 · 무한 대기(`_lock.sh:52`) 개편 — 원시 연산만 바꾸고 API 유지.
- CI runner 변경(macOS runner 추가) · `.github/workflows/ci.yml` — `ubuntu-latest` 유지.
- macOS 전수(`gates/run.sh all`) 정합 · 다른 게이트의 GNU 전용 도구(`sed -i` · `date -d` · `readlink -f` · `sha256sum` · `/proc`) — 온보딩 실측(PR 3 `onboarding.md`)에서 목록화 · 이 intent 는 잠금 두 파일 + 그 셀프테스트만(종전 미해결 2) · `ops-schedule` 잠금(미해결 4) · Codex bridge · 훅 정의 · `.claude/settings.json`.
- 소형 PR A · B 의 내용(모델 정본 · 해시 집합 축소 · 승인 형식) — 이 intent 는 PR A 뒤에 선다(B 와는 병렬 · Q10).

## 확인
- 프론티어 공집합 확인: 2026-09-26 12라운드 — Opus blind 판정자 1(10문 + 미해결) + 교차 점검 1 → 미해결 0건
- Ted 확인 문장(원문 그대로): "팀에 맥이나 비 wsl호스트가 있음 다른사람일필욘없다 / 나머진 전브 권고로"(10라운드 · 발행 근거) · 승인 문장 〈판정 대기〉
- 재개봉 금지: 판정 10건 · 해소 4건은 다시 열지 않는다 — 변경은 줄 추가 또는 새 intent
- macOS 1대 실측 기록(`gate-host-mutex-selftest` · `db-selftest` 종료코드 · 요약줄 · `command -v flock` 빈 값 증거): 〈판정 대기 · 병합 전 기입〉
- WSL flock 제거 셸 실측 · CI 두 게이트 green: 〈판정 대기 · 병합 전 기입〉

## 참조
- 기획 원본: 없음 — 원천은 부모 intent 10라운드 판정(`:627`) · 감사 종합 권고 12ⓑ · 질문 5.
- 부모 intent: `dev-package/intent/2026-09-25-harness-improvement.md`(10라운드 `:627` · 판정 원칙 · Q5 확정).
- 총괄 계획: `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md` — 순서표 `:16-28`(행 4 와 5 사이 소형 PR A ∥ B · §10 10라운드 개정) · 2-3 `:66`(`flock -w` 상한 78 유지 = 이 intent 가 원시 연산만 바꾸는 근거) · §3 `:152-154`(`_lock.sh` · `_pg.sh` PR 2 소유 · ⓑ 행) · §10.2 행 5c.
- 저장소 밖 근거: `~/.claude/reports/harness-state-20260925/team-shared-20260926/report.md:21,37,44,66-68,130` · `audit-mechanisms.md:18-21,83`(소형 PR B 로 `dev-package/reports/harness/20260925-harness-state/` 반입 예정).
- 선례 · 코드: `gates/tools/_lock.sh:28-47`(설치 잠금) · `:76-133`(호스트 뮤텍스) · `:143-146`(`gate_mutex_spawn`) · `gates/tools/_pg.sh:76-115`(슬롯) · `gates/run.sh:190,224-245,905-928` · `gates/tools/gate-host-mutex-selftest.sh:60-80,153-166,246-312` · `gates/tools/db-selftest.sh:440-479` · `gates/tools/_venv.sh:21` · `contract-lint.sh:31` · `event-lint.sh:46` · `frontend-visual.sh:84` · `scripts/deploy_release.py:95-107` · `scripts/product_release.py:287` · `scripts/dev.ps1:119-122` · `.github/workflows/ci.yml:18`.
- ADR: `docs/decisions/0004-gate-verdict-three-states.md` · `0005-harness-controls-are-declarative.md:42-54`(개정 블록 · 무수정) · 새 ADR 후보(Q9).
- spec: `dev-package/prd/specs/2026-09-18-gate-host-mutex.md`(`:16,31,34,60,63` — 원시 연산 `flock -w` 를 전제한 문장 · 무수정 · 새 spec `S-HARNESS-PORTABLE-LOCKS-<날짜>.md` 는 승인 뒤 작성) · `S-HARNESS-LANE-HYGIENE-20260924.md:27`(F1 fd 모델).
- 라운드 파일: `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md` · `R-GATE-HOST-MUTEX.md`
- 결정: 〈N〉 (병합 시 기입)
- 12라운드 원문 판정: ~/.claude/reports/harness-state-20260925/team-shared-20260926/grill-intents/(locks-blind.md · locks-context.md · locks-verdict.md · cross.md)
