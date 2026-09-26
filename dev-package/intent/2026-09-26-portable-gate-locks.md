# Intent: 게이트 잠금 원시 연산의 이식 — util-linux `flock` 실행 파일 → python3 `fcntl.flock`(판정 규약 무변경)
메타 — 발의자: Ted · 작성 2026-09-26 · 승인 미승인(초안 · /grill-me 판정 예정)
- 출처: 부모 intent `dev-package/intent/2026-09-25-harness-improvement.md` 10라운드 판정(`:627`) — 질문 5 「팀에 macOS · 비WSL 호스트가 있는가」 → Ted 원문 "팀에 맥이나 비 wsl호스트가 있음" → 「`gates/tools/_lock.sh` · `_pg.sh` 의 flock 을 python `fcntl.flock` 로(판정 규약 무변경) intent 지금 발행」 · 「별도 intent 3: ⓑ fcntl 잠금」. 감사 종합 `~/.claude/reports/harness-state-20260925/team-shared-20260926/report.md` 권고 12ⓑ(`:21`) · 충돌·미확인(`:37`) · 질문 5(`:44`) · 부록 E-3(`:66-68`) · 원문 `audit-mechanisms.md:18-21`.
- 판정 원칙(10라운드 · 이후 모든 그룹): 하네스 결정마다 「다른 팀원이 다른 머신에서 같은 절차를 밟아도 같은 판정 · 같은 보호 · 같은 비용인가」. 고정: 동작·제약은 시스템으로 · 병합은 사람 · 승인 intent append-only · ADR 이력 무수정 · 훅 정의 무변경 · ADR 번호 PR 2 = 0011 · PR 4 = 0012.
- 표기: 「판정」 자리는 전부 〈판정 대기〉. 초안 권고와 다른 판정은 「초안 권고 ⓧ → 판정 …」로 적어 두 값이 모두 남는다. 줄 번호 기준 = 브랜치 `claude/harness-s-red` = develop `5bb3d6fe` · 2026-09-26 재열람.

## 문제
- 호스트 뮤텍스 · 도구 설치 잠금 · pg 슬롯이 util-linux `flock` **실행 파일**을 요구한다 — `_lock.sh:32` `command -v flock`(설치 잠금) · `:40` `flock 9` · `:89` `command -v flock`(호스트 뮤텍스) · `:104` `flock -n` · `:112` `flock -w` · `_pg.sh:82` `command -v flock` · `:100` `flock -n "$PG_SLOT_FD"`. 부재는 면제 없이 `red(준비 · 78)` 다(`_lock.sh:11` · `_pg.sh:59-68` · ADR-0005 `:52-54` 「면제 변수를 두지 않는다 … 없는 호스트가 합류하는 날 그때 3상태 변수를 만든다」).
- macOS 에는 util-linux `flock` 이 없다. 팀에 macOS · 비WSL 호스트가 있다(Ted 확인). 그 구성원은 로컬에서 `serial` 선언 게이트(`parallelism.toml:23` · 45건) 와 DB 게이트 전부를 한 건도 판정할 수 없다 — 전부 78. 「같은 절차 → 같은 판정」이 OS 로 갈린다(감사 E-3 · 심각도 높음).
- 선택지 둘 중 ADR-0005 가 예고한 「3상태 면제 변수」는 green-by-skip 통로다(`_pg.sh:68` 「쓸 일이 없는 면제 변수를 미리 두면 그것이 곧 green-by-skip 통로」). 남는 길은 잠글 **수단**을 실행 파일 의존이 없는 것으로 바꾸는 것이다.
- `flock(1)` 을 전제로 한 자리 전수: `_lock.sh:32,40,89,104,112` · `_pg.sh:82,100` · `gate-host-mutex-selftest.sh:70,78`(fixture 점유 `flock -x … -c`) · `:153-166`(ⓓ flock 부재 PATH 수술) · `:280`(`flock -n "$LOCK" true`) · `:291`(`flock -w 5`) · `db-selftest.sh:442-456`(슬롯 고갈 fixture `flock -n 8`) · `:463-475`(flock 부재 PATH 수술 · `_pg.sh` 와 `_lock.sh` 두 벌) · 문서 `gates/README.md:13`(ⓓ) · `:100` · `:112` · `:126-130` · `parallelism.toml:23` · spec `2026-09-18-gate-host-mutex.md:16,31,34,63` · ADR-0005 `:46,49,52-54` · 총괄 계획 `:64`(2-3 「`flock -w` 상한 초과 = 78 유지」) · PR 2 spec `:100`. `ops-schedule-selftest.sh:127`(`flock -n 9` · 다른 게이트의 fixture)은 범위 밖에 적는다.

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
- Q1 잠금 원시 연산 → 〈판정 대기〉. ⓐ `fcntl.flock`(`flock(2)` · open file description 에 붙는 잠금 · fork/exec 로 물려받은 fd 에 그대로 남고 마지막 fd 가 닫힐 때 풀린다 — util-linux `flock <fd>` 와 같은 커널 호출) ⓑ `mkdir` 원자 잠금(커널이 풀지 않는다 → 죽은 잠금 · pid/나이 휴리스틱 = 새 정책) ⓒ `fcntl.lockf`(POSIX 레코드 잠금 · 같은 프로세스가 그 파일의 **어느** fd 를 닫아도 풀리고 fork 자식에 상속되지 않는다 → `gate_mutex_spawn` 모델과 ⑴⑵ 의 의미가 바뀐다) ⓓ perl `flock`. 권고 ⓐ — 판정 규약 「잠금은 fd 로 산다 · 죽으면 커널이 푼다」(`_lock.sh:72-75`)를 한 글자도 바꾸지 않는 유일한 선택지이고, 저장소 선례(`deploy_release.py:103`)와 같다.
- Q2 잠금이 bash 프로세스 트리를 어떻게 건너는가 → 〈판정 대기〉. ⓐ bash 가 종전대로 `{VAR}>` 로 fd 를 열고, python3 **자식**이 그 fd 번호를 인자로 받아 `fcntl.flock(fd, …)` 뒤 종료한다 — 잠금은 bash 가 쥔 open file description 에 남는다(python 은 상속 fd 를 시작 시 닫지 않는다) · exec 생존 · 사망 해제 · `gate_mutex_spawn` 의 `{fd}>&-` 가 그대로 유효 ⓑ python3 장기 보유 프로세스 + 파이프(bash 가 죽어도 보유자가 남을 수 있다 → 죽은 잠금). 권고 ⓐ — fd 모델 무변경이라 ⑴⑵ · `run.sh:913-928`(pool 부모가 쥐고 자식은 fd 닫음) · `frontend-visual.sh:84` 호출부가 한 줄도 안 바뀐다.
- Q3 상한 대기(`flock -w`)의 구현 → 〈판정 대기〉. ⓐ python3 안에서 blocking `LOCK_EX` + `signal.alarm(wait_s)` · 핸들러가 예외를 던져 EINTR 재시도(PEP 475)를 끊는다 → 종료 0 획득 / 1 상한 · 실경과는 종전대로 bash 가 `date +%s` 로 잰다(`_lock.sh:110-114`) ⓑ bash 폴링 `LOCK_NB` + `sleep 1`(`_pg.sh:98-108` 모양). 권고 ⓐ 호스트 뮤텍스 · ⓑ pg 슬롯(현행 루프 유지) — 뮤텍스는 프로세스 1개로 `flock -w` 와 같은 벽시계 · 슬롯은 슬롯 i 마다 fd 를 바꿔 여는 구조라 루프가 이미 bash 에 있다. 슬롯 루프의 python3 기동 비용(최대 4회/초 · 1회 ≈ 20-30 ms)은 미해결 5 로 실측.
- Q4 헬퍼의 자리 → 〈판정 대기〉. ⓐ `gates/tools/_flock.py` 파일 1개(`<fd> --nb | --wait <초>` · 종료 0/1 · stdlib only) 을 `_lock.sh` · `_pg.sh` · 두 셀프테스트 fixture 가 같이 부른다 ⓑ 각 호출 자리에 `python3 -c '…'` 인라인. 권고 ⓐ — 「한 디렉터리가 표식·정책을 두 벌로 갖지 않는다」(`_pg.sh:40` · `_lock.sh:19`) · 단위 시험 가능 · 셸 인용 오류 0. 파일은 `gates/tools` 안이라 소형 PR A 뒤 해시 집합 밖(영향 범위).
- Q5 「수단 부재」 갈래의 의미 → 〈판정 대기〉. ⓐ ⑴ 갈래 유지 · `command -v python3` 로 검사 · 사유 문구 「python3 이 PATH 에 없다」 · 같은 `readiness_env_wait` 경로 78 ⓑ 갈래 삭제(python3 는 `run.sh:190` 의 전제라 도달 불가). 권고 ⓐ — `_lock.sh` · `_pg.sh` 는 source 로 직접 불리고(셀프테스트 `db-selftest.sh:472-475` · `frontend-visual.sh`) 그 경로에는 `run.sh:190` 이 없다 · 「실행기가 아는 사실은 무의미하거나 판정이거나」(ADR-0005) · 셀프테스트 ⓓ 는 PATH 수술 대상을 `flock` → `python3` 로 바꿔 유지.
- Q6 Windows · WSL 정합 → 〈판정 대기〉. ⓐ 변경 없음 — `dev.ps1:119-122` 가 모든 `gate` 호출을 WSL 로 보내므로 Windows = Linux 경로 · `msvcrt` 분기 0 ⓑ 네이티브 Windows(`msvcrt.locking`) 분기 추가. 권고 ⓐ — 없는 경로에 분기를 두면 그것이 곧 시험되지 않는 갈래다.
- Q7 pg 슬롯 표를 파일로 유지하는가 → 〈판정 대기〉. ⓐ 유지 — `PG_SLOT_DIR/slot-<i>`(`_pg.sh:77,95`) 파일마다 `LOCK_NB` · 슬롯 수 = 파일 수 · 죽으면 커널이 푼다 ⓑ 계수 파일 1개(python 이 읽고-증가-쓰기 · 죽은 슬롯 회수 정책 필요) ⓒ 슬롯 데몬. 권고 ⓐ — 규약 · 셀프테스트 fixture(`db-selftest.sh:444` 가 `slot-0` 을 직접 잡는다) · `COLAB_PG_SLOT_DIR` 의미 무변경.
- Q8 셀프테스트 변경 허용 범위 → 〈판정 대기〉. regime(케이스 · 단언 · 값 증거) 무변경 · fixture 만: `gate-host-mutex-selftest.sh:70,78`(점유자 `flock -x … -c`) · `:280` · `:291` → `_flock.py` 를 부르는 bash 점유자(FIFO 동기화 유지) · `:153-166` ⓓ PATH 수술 = `python3` 제거 · `:263` `/proc/$$/fd` → `/dev/fd` 나열 + `os.fstat` inode 대조(Linux · macOS 공통 · macOS `/dev/fd` 는 symlink 가 아니라 `readlink` 불가) · `:39` `mktemp -d -p` → `mktemp -d "${TMPDIR:-/tmp}/…XXXXXX"` · `db-selftest.sh:442-456` 점유자 `flock -n 8` → `_flock.py` · `:463-475` python3 제거. ⓐ 위 fixture 이식만 ⓑ ⓐ + 케이스 ⓘ 「`flock` 바이너리 부재 · python3 존재 → green」(PATH 수술 · Linux 호스트가 macOS 모양을 값으로 증명) ⓒ 케이스 축소. 권고 ⓑ — ⓘ 없이는 「macOS 에서 된다」가 macOS 1대의 수동 실측에만 남는다 · CI `ubuntu-latest` 가 매 PR 마다 그 모양을 잰다.
- Q9 ADR 자리 → 〈판정 대기〉. ⓐ 새 ADR 「게이트 잠금은 stdlib `fcntl.flock` · 실행 파일 의존 0 · 면제 변수 없음 · 판정 규약은 ADR-0005 개정 블록 그대로」 · ADR-0005 `:52-54` 의 「합류하는 날 3상태 변수」 예고를 이 ADR 이 대체한다고 적고 0005 본문은 무수정 ⓑ ADR 없음(코드 + README 만). 권고 ⓐ — 0005 가 명시한 계획(면제 변수)과 다른 길을 택하므로 그 결정이 기록 없이 코드에만 남으면 다음 사람이 0005 를 읽고 면제 변수를 만든다. 번호 = 병합 시점의 다음 빈 번호(0011 · 0012 는 PR 2 · PR 4 예약 · S-auth 는 「lane 착수 시 다음 빈 번호」) — 미해결 3.
- Q10 반입 순서 → 〈판정 대기〉. ⓐ 소형 PR A ∥ B 병합 **뒤** · PR 2 head 회차 **앞** 의 단독 소형 PR(해시 집합 밖 · 회차 불요 · lane 1 · 병합은 사람) ⓑ 소형 PR A 에 합침(A 는 해시 집합 파일 · 회차 1회로 끝내는 PR — 잠금 변경이 섞이면 회차 실측이 잠금 변경까지 덮는다) ⓒ PR 2 에 합침(긴 개방 기간 · 다른 소유). 권고 ⓐ — 10라운드 「소형 PR A 뒤 첫 회차가 새 기준선」과 양립하고 회차 비용 0.

## 미해결 질문
1. macOS `mktemp` 의 `-p` 지원 여부(BSD mktemp 판본 차) — Q8 의 치환은 지원 여부와 무관하게 안전한 형태로 두되, macOS 1대 실측으로 확인.
2. macOS 전수(`gates/run.sh all`) 정합은 이 intent 밖 — 다른 게이트의 GNU 전용 도구(`sed -i` · `date -d` · `readlink -f` · `sha256sum` · `/proc`)는 온보딩 실측(PR 3 `onboarding.md`)에서 목록화. 이 intent 는 잠금 두 파일 + 그 셀프테스트만.
3. 새 ADR 번호 — 0011 · 0012 예약 · S-auth 「0013 또는 lane 착수 시 다음 빈 번호」와의 순서. 이 PR 이 S-auth 보다 먼저 병합되면 0013 을 이 ADR 이 쓰고 S-auth 는 다음 번호(S-auth intent 자체가 그렇게 적혀 있어 충돌 없음) — Ted 확인.
4. `ops-schedule-selftest.sh:127`(`flock -n 9`) 과 그 대상 `run-scheduled.sh` 의 잠금 — 다른 게이트 · 다른 소유. macOS 구성원에게 그 게이트는 여전히 78 이다. 같은 `_flock.py` 로 옮길지 별도 소형 PR 로 낼지.
5. pg 슬롯 루프의 python3 기동 비용(최대 `COLAB_PG_MAX_CONCURRENT`회/초) — 대기 중에만 발생 · `db-selftest` 「슬롯 고갈」 케이스의 실경과로 실측 · 상한 판정에 영향 0 확인.
6. macOS bash 판본 — Homebrew bash ≥ 4.1 을 온보딩 전제로 적는 자리(PR 3) · 이 intent 는 전제 무변경만 확인.

## 범위 밖 (명시 제외)
- 면제 변수(`COLAB_*_LOCK_EXEMPT` 류) 신설 — ADR-0005 「green-by-skip 통로」 · 두지 않는다.
- 잠금 의미 변경 — 키(`TMPDIR` 하나) · 단위(게이트 1건) · 상한 기본값(900) · 면제 집합 · 표식 형식 · 요약줄. `serial`/`parallel` 선언표 자체.
- `gate_lock_fd` 의 fd 9 고정 · 무한 대기(`_lock.sh:52`) 개편 — 원시 연산만 바꾸고 API 유지.
- CI runner 변경(macOS runner 추가) · `.github/workflows/ci.yml` — `ubuntu-latest` 유지.
- 다른 게이트의 GNU 도구 정합(미해결 2) · `ops-schedule` 잠금(미해결 4) · Codex bridge · 훅 정의 · `.claude/settings.json`.
- 소형 PR A · B 의 내용(모델 정본 · 해시 집합 축소 · 승인 형식) — 이 intent 는 그 뒤에 선다.

## 확인
- 프론티어 공집합 확인: 〈판정 대기 · /grill-me 뒤 기입〉
- Ted 확인 문장(원문 그대로): "팀에 맥이나 비 wsl호스트가 있음 다른사람일필욘없다 / 나머진 전브 권고로"(10라운드 · 발행 근거) · 승인 문장 〈판정 대기〉
- 재개봉 금지: 〈판정 대기〉
- macOS 1대 실측 기록(`gate-host-mutex-selftest` · `db-selftest` 종료코드 · 요약줄 · `command -v flock` 빈 값 증거): 〈판정 대기 · 병합 전 기입〉
- WSL flock 제거 셸 실측 · CI 두 게이트 green: 〈판정 대기 · 병합 전 기입〉

## 참조
- 기획 원본: 없음 — 원천은 부모 intent 10라운드 판정(`:627`) · 감사 종합 권고 12ⓑ · 질문 5.
- 부모 intent: `dev-package/intent/2026-09-25-harness-improvement.md`(10라운드 `:627` · 판정 원칙 · Q5 확정).
- 총괄 계획: `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md` — 순서표 `:16-28`(행 4 와 5 사이 소형 PR A ∥ B · §10 10라운드 개정) · 2-3 `:64`(`flock -w` 상한 78 유지 = 이 intent 가 원시 연산만 바꾸는 근거).
- 저장소 밖 근거: `~/.claude/reports/harness-state-20260925/team-shared-20260926/report.md:21,37,44,66-68,130` · `audit-mechanisms.md:18-21,83`(소형 PR B 로 `dev-package/reports/harness/20260925-harness-state/` 반입 예정).
- 선례 · 코드: `gates/tools/_lock.sh:28-47`(설치 잠금) · `:76-133`(호스트 뮤텍스) · `:143-146`(`gate_mutex_spawn`) · `gates/tools/_pg.sh:76-115`(슬롯) · `gates/run.sh:190,224-245,905-928` · `gates/tools/gate-host-mutex-selftest.sh:60-80,153-166,246-312` · `gates/tools/db-selftest.sh:440-479` · `gates/tools/_venv.sh:21` · `contract-lint.sh:31` · `event-lint.sh:46` · `frontend-visual.sh:84` · `scripts/deploy_release.py:95-107` · `scripts/product_release.py:287` · `scripts/dev.ps1:119-122` · `.github/workflows/ci.yml:18`.
- ADR: `docs/decisions/0004-gate-verdict-three-states.md` · `0005-harness-controls-are-declarative.md:42-54`(개정 블록 · 무수정) · 새 ADR 후보(Q9).
- spec: `dev-package/prd/specs/2026-09-18-gate-host-mutex.md`(`:16,31,34,60,63` — 원시 연산 `flock -w` 를 전제한 문장 · 무수정 · 새 spec `S-HARNESS-PORTABLE-LOCKS-<날짜>.md` 는 승인 뒤 작성) · `S-HARNESS-LANE-HYGIENE-20260924.md:27`(F1 fd 모델).
- 라운드 파일: `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md` · `R-GATE-HOST-MUTEX.md`
- 결정: 〈N〉 (병합 시 기입)
