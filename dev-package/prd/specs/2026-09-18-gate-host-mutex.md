# Spec: 게이트 호스트 뮤텍스 — `serial` 선언을 실행기가 프로세스 경계 너머로 강제한다
출처 intent: `dev-package/intent/2026-09-17-gate-host-mutex-enforcement.md` (승인 2026-09-18 · 미결 2건은 아래 「구현 결정 §A」에서 권고대로 확정)
근거 사슬: `.agents/rules/colab-rules.md §3-1`(원본 규칙) → ADR-0002(superseded 2026-09-18) → [ADR-0005](../../../docs/decisions/0005-harness-controls-are-declarative.md) 「2026-09-18 개정」의 **후속 PR ②**.

⚠ 이 spec 은 **한 레인·한 PR** 이다. ADR-0005 개정이 ② 를 단독 PR 로 못박았고, `gates/run.sh` 하나가 유일한 실질 표면이다.
⚠ 형제 spec `2026-09-18-harness-evidence-hooks.md`(ADR-0005 ③④)와 **코드 표면은 독립이나 문서 3곳을 공유한다** — `gates/README.md` · `docs/decisions/0005-…md:58-60`(인접 행) · `R-HARNESS-PR-CENTRIC.md`. 레인은 **직렬**로 돈다(형제 먼저, 이 spec 나중). 이 레인은 커밋 3 직전에 develop 을 대조해 형제 PR 이 병합됐으면 rebase 하고, 아니면 자기 행(② · README 새 절 · 자기 R-HARNESS 행)만 건드려 병합 시 인접 행 충돌을 사용자가 푼다. 게이트 회차도 두 레인이 겹치지 않게 오케스트레이터가 직렬화한다(병합 전까지 §3-1 은 사람의 규칙이다).
⚠ intent 의 결정 6건 중 2·3·5 는 **PR #116(`1f56028c`)으로 이미 끝났다** — `_pg.sh` 세 갈래·`_lock.sh` 의 78 승격, ADR-0005 개정과 ADR-0002 supersede. 이 spec 은 그것을 다시 하지 않는다.

## 문제 진술
- `gates/config/parallelism.toml` 의 `serial` 선언(오늘 17건)은 `gates/run.sh all` 의 **한 프로세스 안에서만** 효력이 있다. 선언표를 읽는 자리가 `all)` 갈래(`gates/run.sh:694-697`) 뿐이고, 단독 호출 `gates/run.sh frontend-test` 는 선언을 한 글자도 읽지 않는다.
- 그래서 「게이트 레인은 호스트에 하나」는 오케스트레이터가 레인 지시문에 그 문장을 넣어서 지켜졌다. 지시문을 읽지 않은 프로세스(다른 세션·Codex·사람 손)는 걸리지 않는다. ADR-0005 개정의 규칙 「실행기가 아는 사실은 무의미하거나 판정이거나」에 정면으로 걸리는 갈래다.
- 잠금을 세울 수 없는 환경에서 조용히 통과하면 위 규칙의 「조용한 `return 0`」이다. 판정할 수 없으면 red(준비 · 78)여야 한다(ADR-0004).

## 해법 개요
- 호스트 전역 `flock` **하나**를 두고, **`serial` 로 선언된 게이트를 실행하는 부모 프로세스만** 잡는다. `parallel` 선언 게이트는 잡지 않는다 — 그것이 곧 면제이며 새 면제 변수는 두지 않는다.
- 잠금이 이미 점유돼 있으면 `::gate-waiting::` 표식을 찍고 상한까지 기다린다. 상한 초과·`flock` 부재·잠금 파일 생성 불가는 전부 기존 보고 경로 `readiness_env_wait`(`gates/tools/_readiness.sh:31-40`)로 red(준비) ＋ 종료코드 78. **새 보고 경로를 만들지 않는다.**
- 결과: 레인 둘이 각자 게이트를 돌려도 `serial` 게이트가 겹치지 않는다. 사람의 순차 대기 대신 실행기가 줄을 세운다.

## 사용자 스토리
1. 오케스트레이터로서 레인 두 개에 동시에 게이트를 돌리게 하고 싶다, 프롬프트 직렬화로 벽시계를 태우지 않기 위해.
2. 레인으로서 내 `serial` 게이트가 다른 프로세스의 `serial` 게이트와 겹치지 않기를 원한다, 판정이 부하로 오염되지 않기 위해.
3. 게이트를 읽는 사람으로서 「기다렸다·얼마나·무엇을」이 요약에 값으로 남기를 원한다, 78 이 왜 났는지 재현 없이 알기 위해.

## 구현 결정

### A. intent 의 미결 2건 — 권고대로 확정
- (a) **대기 후 상한 초과 시 78.** 즉시 78 은 오늘처럼 프롬프트로 직렬화된 회차 전부를 red 로 만든다. 대기 중에는 `::gate-waiting::gate=<g>|waited=<s>|limit=<s>|lock=<path>` 를 stdout 에 찍는다(요약 분류기는 `^::gate-readiness-failure::`·`^::gate-failure::` 만 보므로 충돌 없음 — `gates/run.sh:783`·`:801`).
- (b) **잠금 키 = `TMPDIR` 하나.** 경합 자원(호스트 부하·도커 데몬)이 레포별이 아니다. 레포 경로를 키에 넣으면 워크트리마다 잠금이 갈려 실효 한도가 배수로 늘어 intent Q4 가 기각한 실패로 간다.

### B. 잠금 원시 — `gates/tools/_lock.sh` 에 함수 2개 추가 (새 파일 없음)
- `gate_host_mutex_acquire <게이트>` / `gate_host_mutex_release`. 기존 `gate_lock_fd` 는 fd 9 고정 ＋ 상한 없음이라 재사용 불가. 새 함수는 `_pg.sh:95` 관용구(`{ exec {FD}>"$path"; } 2>/dev/null` ＋ 동적 fd)를 따르고 `flock -w <상한>` 을 쓴다(호스트 `flock` 은 util-linux 2.39.3 · `-w` 가용 확인).
- 잠금 파일: `${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host`. **새 경로 변수는 두지 않는다.** 키가 `TMPDIR` 하나(§A-b)이므로 selftest 는 `TMPDIR` 을 자기 `mktemp -d` 로 바꿔 부르면 실제 호스트 잠금을 건드리지 않는다 — 주입구 변수가 있으면 그것이 곧 워크트리별 잠금 분리 통로가 된다(ADR-0005 「쓸 일 없는 면제 변수는 그 자체가 green-by-skip 통로」 · 선례 `COLAB_PG_SLOT_DIR` 의 같은 구멍은 이 spec 범위 밖).
- 상한: `COLAB_GATE_MUTEX_WAIT`, 기본 **900초**(선례 `COLAB_PG_SLOT_WAIT` 900 · `_pg.sh:79`). 잠금은 **게이트 1건 단위**라 최장 대기 = 상대 레인의 `serial` 게이트 1건이고, 직전 전수(67건 9분 52초)에서 단일 게이트가 15분을 넘긴 적이 없다(우려 #1).
- 세 실패 갈래 전부 `readiness_env_wait "$gate" "호스트 뮤텍스($path)" "<상한>초" "<실경과>초" "<사유>"` ＋ `return 78`: ⑴ `flock` 부재 ⑵ 잠금 디렉터리 `mkdir -p` 실패 / 파일 열기 실패 ⑶ 상한 초과. 면제 변수 없음(ADR-0005 개정 · intent Q9 「두지 않는다」).

### C. 배선 — `gates/run.sh` 세 자리, 규칙은 하나: **잠금을 쥔 부모 아래의 자식만 면제된다**
- 면제 키는 **`COLAB_GATE_MUTEX_HELD=1`** — 잠금을 잡은 부모가 자식을 부를 때만 세운다. `COLAB_GATE_SUMMARY_CHILD=1` 을 면제 키로 쓰면 `task` 경로(`run.sh:29-32` → `lifecycle_contract.py run_gates:364-365` 가 게이트마다 `CHILD=1` 로 자식을 부른다)의 `serial` 게이트가 **무잠금으로 돈다.** ADR-0005 `:58` 의 「`COLAB_GATE_SUMMARY_CHILD=1` 재진입 면제」는 목적(재진입 교착 방지)을 적은 것이며, 키를 분리해야 그 목적이 `task` 에서도 성립한다(우려 #2).
- 선언 읽기를 `all)` 밖으로 끌어올려 `gate_mode_of <게이트>` 하나로 공유한다. `all)` 의 `:694-697` 도 이 리더를 쓴다. 리더는 둘이 되지 않는다(`scripts/harness/check.py:30-32` 의 규율 — 선언표 파서는 `gates/tools/parallelism.py` 하나).
- `run.sh` 는 지금 `_lock.sh` 를 어디서도 source 하지 않고 `_readiness.sh` 도 `:184`(env 파일 부재 갈래) 안에서만 읽는다. 커밋 1 은 `:118` 앞에 `. "$REPO_ROOT/gates/tools/_lock.sh"` 를 둔다(`_lock.sh:25` 가 `_readiness.sh` 를 읽는다).
- ⑴ **단독 호출**: 획득 자리는 **요약 래퍼 `:118` 앞**이다. 래퍼는 `COLAB_GATE_REPORT_DIR`/`COLAB_GATE_OUTDIR` 가 있을 때만 자식을 부르고(`:118-119`·`:122`) 부모는 `:158` 에서 끝나므로, `case`(`:217`) 앞에 두면 레인·H7 경로(항상 OUTDIR 을 준다)에서는 면제된 자식만 도달해 **잠금 0건**이 된다. 조건 = `[ -z "$COLAB_GATE_MUTEX_HELD" ]` ∧ `GATE ∉ {all, task}` ∧ `gate_mode_of "$GATE" = serial`. 획득 실패는 그 자리에서 `exit 78`. 래퍼가 `:122` 에서 자식을 부를 때 `COLAB_GATE_MUTEX_HELD=1` 을 함께 준다.
- ⑵ **`all` 의 단독 구간**: `run_one()`(`:737-743`) 안에서 **solo 게이트 1건마다** 획득 → 자식 실행(`HELD=1`) → 해제. 단독 구간 전체(17건)를 한 번에 잠그면 반대 레인이 17건을 기다려 상한을 넘긴다. `.span`(`:742`)은 그대로 둔다. 병렬 풀(`:750-755`)의 게이트는 잡지 않고 `HELD` 도 주지 않는다.
- ⑶ **`task` 경로**: `run_gates`(Python)는 잠금을 잡지 않고 `HELD` 를 세우지 않는다 → 게이트마다 자식이 ⑴ 로 스스로 잡는다. 결과적으로 `all` 의 run_one 과 같은 「solo 1건마다」 규칙이 된다. 잠금 원시는 bash 한 벌뿐이고 Python 에 복제하지 않는다.
- ⑷ selftest 집합(`:603`)의 자식은 부모가 잠금을 잡지 않으므로(`serial` 선언인 selftest 만 자기 ⑴ 에서 잡는다) `HELD` 없이 부른다.
- 교착 없음: `parallel` 게이트는 뮤텍스를 아예 안 잡으므로 host-mutex ↔ `gate_lock_fd`(venv 설치 잠금) 순환이 없다. `_pg.sh` 슬롯은 뮤텍스 안쪽에서 잡히며 역순은 없다.
- 요약(`:804` 계수줄 아래)에 한 줄: `  ── 호스트 뮤텍스 : 잠금 N건 · 면제(parallel 선언) M건 · 대기 누계 Xs`. N＋M ＝ 실행 건수. 대기 누계는 `::gate-waiting::` 의 `waited` 합. `all` 의 대기는 부모가 직접 찍는다(자식 출력은 파일로 돌아간다). JSON(`:821-826`)의 `counts` 키 집합은 **바꾸지 않는다** — ADR-0004 재검토 조건에 걸리지 않게.

### D. 문서 3곳 ＋ ADR 갱신
- `gates/README.md` `:80-87` 블록 아래에 「호스트 뮤텍스」 절: 무엇을 잡는가·`::gate-waiting::` 형식·`COLAB_GATE_MUTEX_WAIT`·세 갈래 78. 면제 변수 없음을 명시.
- `gates/config/parallelism.toml` 헤더(`:12-19`)에 「`serial` 은 이제 호스트 전역이다 — 프로세스 경계를 넘는다」 한 문장.
- `docs/decisions/0005-harness-controls-are-declarative.md:58` 후속 ② 항목을 완료로 갱신(PR 번호는 사용자가 게시 뒤 적는다 — 레인은 「이 브랜치」로 적는다).
- `.agents/rules/colab-rules.md §3-1` 은 **건드리지 않는다**(원본 규칙은 그대로이고 강제 수단이 생긴 것).
- 모듈 · 인터페이스: `gates/tools/_lock.sh`(함수 2개 추가) · `gates/run.sh`(리더 끌어올림 ＋ 획득 2자리 ＋ 요약 1줄) · `gates/tools/gate-host-mutex-selftest.sh`(신설).
- 스키마 · 마이그레이션: 없음.
- API 계약: 비파괴. `colab-gate-summary/1` 그대로. `_lock.sh` 기존 함수 서명 불변.

## 시험 결정
- 신설 seam: `gate-host-mutex-selftest`. 등록 5곳 — `gates/tools/gate-host-mutex-selftest.sh` · `run.sh:217` case · `run.sh:194` `ALL_GATES` · `parallelism.toml`(**`parallel`** 로 선언 — 자기 `mktemp -d` 를 **`TMPDIR`** 로 물려 실제 호스트 잠금을 잡지 않는다; 빠지면 `harness-contract` 가 red(판정)·exit 1 — `scripts/harness/check.py:68-71`) · README 표 한 행 ＋ `exec-bit`. `harness.yaml:52-58` `required_files` 는 어댑터 5개뿐이라 새 파일을 요구하지 않는다.
- 대상 게이트는 `COLAB_GATE_PARALLELISM_MANIFEST`(`run.sh:694` 가 이미 존중) 픽스처 toml 로 `exec-bit` 를 `serial` 선언해 쓴다. 단언 도구는 `_expect.sh:56-108` ＋ `db-selftest.sh:407-419` 의 `expect_ready_red`(exit 78 ＋ `waited_for/limit/elapsed` 표식) 를 재사용한다.
- 케이스 6건(외부 행위 기준):
  - ⓐ 점유 중 대기 → 78: 배경 `flock -x $TD/host -c 'sleep 5'` ＋ `COLAB_GATE_MUTEX_WAIT=2` → exit 78 · `::gate-waiting::` 존재 · 실경과 ≥ 2초 · `::gate-readiness-failure::` 의 `waited_for` 에 뮤텍스 경로.
  - ⓑ 점유 해제 뒤 green: 배경 `sleep 1` 점유 ＋ `WAIT=10` → green · `::gate-waiting::` 존재 · `waited` ≥ 1.
  - ⓒ 잠금 디렉터리 `chmod 500` → 78.
  - ⓓ PATH 수술로 `flock` 부재(`env -i` bash · `db-selftest.sh:445-459` 선례) → 78.
  - ⓔ `parallel` 선언 게이트는 점유 중에도 green ＋ 요약의 면제 건수 ≥ 1; `COLAB_GATE_MUTEX_HELD=1` 자식은 점유 중에도 기다리지 않는다; `COLAB_GATE_SUMMARY_CHILD=1` **만** 있는 호출은 점유 중이면 기다린다(`task` 경로의 형태).
  - ⓕ 레인 경로: `COLAB_GATE_OUTDIR=$TD/out` 을 주고(래퍼 `:118` 경유) 점유 중 호출 → `::gate-waiting::` 이 **부모** 출력에 있고 78. 차단 1 의 회귀 케이스다.
- 해당 서비스 단독 게이트 이름: `gate-host-mutex-selftest`(신설) · `harness-contract`(`.agents/harness.yaml:27` 필수 · 선언표 ⊆ 단언) · 보조 `harness-contract-selftest` · `db-selftest`(`_lock.sh` 의 기존 78 케이스 회귀) · `exec-bit`.
- green-by-skip 방지: ⓐ 의 실경과 ≥ 2초와 ⓑ 의 `waited` ≥ 1 이 「잠금이 실제로 걸렸다」의 값 증거다. 표식 문자열만 grep 하는 케이스는 두지 않는다.

## 커밋 순서 (레인이 그대로 따른다)
1. `_lock.sh` 함수 2개 ＋ `run.sh` 리더 끌어올림·획득 2자리·요약 1줄 — **한 커밋**(run.sh 가 미정의 함수를 부르는 중간 상태를 만들지 않는다).
2. `gate-host-mutex-selftest` 신설 ＋ 등록 5곳.
3. 문서 3곳 ＋ ADR-0005 ② 갱신 ＋ 라운드 파일.

## 완료 조건 (레인이 스스로 대조한다)
1. `gates/run.sh <serial 게이트>` 를 두 프로세스에서 동시에 부르면 한쪽이 `::gate-waiting::` 을 찍고 기다린다(selftest ⓑ).
2. 상한 초과·`flock` 부재·디렉터리 불가 셋 다 78 ＋ `::gate-readiness-failure::`(ⓐⓒⓓ).
3. `parallel` 게이트와 자식 재진입은 잡지 않는다(ⓔ).
4. 전수 `-j 4` 1회 green, 요약에 「호스트 뮤텍스 : 잠금 17건 · 면제 M건 · 대기 누계 0s」 — 17 = `parallelism.toml` 의 `serial` 건수와 일치.
5. `harness-contract` green(새 selftest 가 선언표에 있다).

## 검증 계획
### ① 단독 게이트로 증명하는 것
- `gate-host-mutex-selftest` 6케이스 green. **ⓐ·ⓑ 의 시간값이 증명이다.**
- `harness-contract` · `harness-contract-selftest` · `db-selftest` · `exec-bit` green.
### ② 호스트 독점 전수 실행으로만 증명되는 것
- 완료 조건 4. 전수 1회. 이 회차 동안 호스트에 다른 게이트 프로세스를 두지 않는다 — **이 spec 이 병합되기 전까지는 §3-1 이 아직 사람의 규칙이다.**
- 전수 2회 동시 실행으로 「겹치지 않음」을 재는 것은 **하지 않는다**(우려 #3).
### ③ 하지 않는 것
- 재시도·상한 인상·`TMPDIR` 을 갈라 잠금을 피해 green 만들기. `gates/run.sh:775`·`:813` 축자 금지.
- 실브라우저 검증. UI 변경 0건.

## 정책 대조 (작성 시점 제약)
대조 원본 `.agents/rules/product.md` §3·§5 — **이번엔 원문을 직접 읽었다.**
- §3-1~7(도메인 경계·AI 쓰기 경로·마이그레이션 체인·geo import·연구실 경계·ID 타입·생성물 손수정): **저촉 없음.** 변경 전부가 게이트 셸·선언표·문서다. 제품 코드·DB·계약에 닿지 않는다.
- §3-8 절대경로 금지: **준수.** 잠금 경로는 `TMPDIR` 기반 실행값이고 문서엔 변수명만 적는다.
- §5 게이트 우회·비활성화: **반대 방향.** 프롬프트 규율을 실행기 판정으로 올린다.
- §5 「나중에」: **해당 없음.** ADR-0005 개정이 미룬 ②를 이 spec 이 닫는다. ③④ 는 형제 spec(`2026-09-18-harness-evidence-hooks.md`)이 담는다.
- §5 범위 늘리기: **저촉 없음.** intent 승인 절의 범위(run.sh 잠금 하나)를 넘지 않는다.
- 계약 동결 해제 필요: **아니오.** `counts` 키 집합 불변.
- 결정 로그: 신규 legacy 결정번호 없음(intent 결정 6). 새 ADR 없음(결정 3). GitHub 이슈 없음(결정 6).
### 디자인 제약 확인
**해당 없음.** 백엔드·하네스 전용, 화면 코드 0건.

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 대기 상한 기본값. 게이트 1건 단위 잠금이라 최장 대기는 상대 레인의 게이트 1건인데, 그 1건의 실측 상한을 아무도 재지 않았다. 너무 짧으면 정상 회차가 78 로 뒤집힌다. | 900(슬롯 선례 · 직전 전수 총 9분 52초가 근거) | 3600 으로 넉넉히 두고 주석에 근거 | ⓐ — 78 이 나면 그 값이 곧 실측이고, 그때 올린다(ADR-0004 「상한 연장으로 green 금지」는 회차 안의 재시도를 말한다) |
| 2 | **(Ted 한 줄 확인)** 면제 키를 `COLAB_GATE_SUMMARY_CHILD=1`(ADR-0005 `:58` 문면)이 아니라 별도 `COLAB_GATE_MUTEX_HELD=1` 로 둔다. 이유 = `task` 경로가 게이트마다 `CHILD=1` 자식을 부르므로 CHILD 를 키로 쓰면 측정 레인의 `serial` 게이트 전부가 무잠금이다. | 키 분리(§C) — ADR 문면의 목적을 지키고 `task` 도 덮는다 | ADR 문면 그대로 CHILD 를 키로 — `task` 경로는 무잠금으로 남고 그 사실을 ADR 에 적는다 | ⓐ — ⓑ 는 「실행기가 아는 사실을 삼키는」 갈래를 하나 새로 만든다 |
| 3 | 「레인 2개가 동시에 전수를 돌려도 오염되지 않는다」의 끝단 증명을 전수 2회 동시 실행으로 할지. 비용이 크고 호스트 부하 자체가 판정을 흔든다. | 하지 않는다 — selftest ⓐ·ⓑ 의 시간값 ＋ 전수 1회의 「잠금 17건」으로 갈음 | 병합 뒤 별도 측정 레인 1회 | ⓐ, 필요하면 ⓑ 는 measurement-lane 이 후속으로 |
| 4 | `parallel` 선언 게이트가 뮤텍스를 안 잡으므로, `serial` 게이트가 잠금을 쥔 동안 다른 프로세스의 `parallel` 게이트는 돈다. 이것은 의도(선언이 곧 면제)지만 `serial` 게이트가 「혼자 돌았다」는 뜻은 아니다. | 문서에 그대로 적는다 — 「`serial` = 다른 `serial` 과 겹치지 않는다」 | `serial` 이 잡은 동안 `parallel` 도 막는 읽기-쓰기 잠금 | ⓐ — intent Q2 가 결정한 형태이고 ⓑ 는 선언표의 의미를 바꾼다 |

## 범위 밖
- (intent 승계) `_pg.sh` 슬롯의 레포 루트 키잉 — Q4 기각.
- (intent 승계) `parallelism.toml` 선언값 변경·`serial` 17건의 재판정.
- ADR-0005 후속 ③ `WATCH` 확장 · ④ 측정 레인 `SubagentStop` — 형제 spec.
- `colab-gate-summary/1` → `/2` · `counts` 키 변경 · 새 게이트 상태.
- `gates/tools/parallelism.py` 파서 변경. 리더는 그대로 쓴다.
- Codex 실행기에서의 동작 차이. `gates/run.sh` 는 실행 주체와 무관한 셸이다.
- 커밋·push·PR 게시·이슈 댓글. PR 게시는 사용자가 한다.

## 산출 계획
- 라운드 파일: `dev-package/prd/rounds/R-GATE-HOST-MUTEX.md`(≤300행, 첫 줄에서 이 spec 을 링크). 미작성 — 레인 커밋 3 에서 쓴다. `R-HARNESS-PR-CENTRIC.md` 에는 이 PR 항목이 없다 — 한 행 추가한다.
- 예상 레인 수: **1 (직렬).** `gates/run.sh` 하나가 표면이다. 형제 spec 레인 **뒤에** 돈다(머리말 ⚠ 참조).
- 커밋 3개, PR 1건.
- 게이트 3계수·종료코드·selftest ⓐⓑ 의 실측 시간값·전수 1회 요약줄·사용자 게시용 로컬 PR 요약(저장소 밖)을 남긴다.

## 미확인 (레인이 구현 전에 확인한다)
1. `flock -w` 가 기다리는 동안 `::gate-waiting::` 을 **주기적으로** 찍을지 한 번만 찍을지. 권고 = 획득 시도 직전 1회 ＋ 획득 후 실경과 1회(값 두 개면 충분하고 로그가 안 는다).
2. `gates/tools/*.sh` 밖(`scripts/` · `.claude/hooks/`)에서 `run.sh` 를 `HELD` 없이 다시 부르는 곳이 있는지 — 있으면 잠금을 쥔 채 자식이 다시 잡아 교착이다. `gates/tools/` 안은 `ci-schema-diff.sh:36`(CI 보조 · `ALL_GATES` 밖) 하나뿐임을 확인했다.
- 닫힌 것: ~~래퍼가 모든 단독 호출에서 자식을 부르는지~~ → 배출처가 있을 때만(`:118-119`), §C⑴ 에 반영. ~~`required_files` 가 새 selftest 를 요구하는지~~ → 요구하지 않는다(`harness.yaml:52-58`).
