> spec: dev-package/prd/specs/2026-09-18-gate-host-mutex.md
# 게이트 호스트 뮤텍스 — `serial` 선언을 실행기가 프로세스 경계 너머로 강제한다

**Goal:** 「게이트 레인은 호스트에 하나」를 프롬프트가 아니라 실행기가 지킨다.
`gates/config/parallelism.toml` 의 `serial` 선언이 **한 `run.sh` 호출 안**이 아니라
**호스트 전역**에서 효력을 갖게 하고, 강제를 걸 수 없으면 조용히 통과하지 않고 red(준비 · 78)로 낸다.

**출처 intent:** `dev-package/intent/2026-09-17-gate-host-mutex-enforcement.md`(승인 2026-09-18).
**근거 사슬:** `.agents/rules/colab-rules.md §3-1`(원본 규칙) → ADR-0002(superseded 2026-09-18)
→ [ADR-0005](../../../docs/decisions/0005-harness-controls-are-declarative.md) 「2026-09-18 개정」의 **후속 PR ②**.

## 제약

- 게이트 셸·선언표·문서만 바뀐다. 제품 코드·DB·계약 0건. 화면 코드 0건.
- `colab-gate-summary/1` 의 `counts` 키 집합은 **바꾸지 않았다**(ADR-0004 재검토 조건 회피).
- `gates/tools/parallelism.py` 파서와 표 형식은 **읽기만** 한다 — 손대지 않았다.
- ADR-0005 후속 ③④ 는 형제 spec `2026-09-18-harness-evidence-hooks.md` 의 몫이다.
  이 라운드는 `lifecycle_contract.py`·`scripts/tests/*`·`.claude/settings.json`·`.codex/hooks.json` 을
  건드리지 않는다. 이 브랜치는 형제 브랜치 `claude/harness-evidence-hooks`(8c684f74) **위에 쌓였다**.
- PR 게시는 사용자가 한다. 병합·push-to-develop 은 이 레인의 범위 밖이다.

## 확정된 판정 (spec 「우려 항목」)

| # | 항목 | 확정 |
|---|---|---|
| 1 | 대기 상한 기본값 | ⓐ **900초**(선례 `COLAB_PG_SLOT_WAIT`). 잠금 단위가 게이트 1건이라 최장 대기 = 상대 레인의 `serial` 게이트 1건 |
| 2 | 면제 키 | ⓐ **`COLAB_GATE_MUTEX_HELD` 로 분리**(Ted 2026-09-18). `COLAB_GATE_SUMMARY_CHILD` 를 키로 쓰면 `task` 경로의 `serial` 게이트가 전부 무잠금 |
| 3 | 끝단 증명 방법 | ⓐ 전수 2회 동시 실행은 **하지 않는다.** selftest ⓐ·ⓑ 의 시간값 ＋ 전수 1회의 「잠금 17건」으로 갈음 |
| 4 | `serial` 이 잡은 동안 `parallel` 은 돈다 | ⓐ **문서에 그대로 적었다** — `serial` 은 「다른 `serial` 과 겹치지 않는다」이지 「혼자 돌았다」가 아니다 |

## 구현 전 확인 (spec 「미확인」 2항)

1. **`::gate-waiting::` 을 몇 번 찍나** — 권고대로 **두 번**이다: 획득 시도 직전 1회(`waited=0`) ＋
   획득 직후 실경과 1회. 잠금이 비어 있으면 **한 줄도 찍지 않는다**(안 기다린 회차에 대기 로그를
   남기면 값이 값을 못 한다). 값 두 개면 충분하고 로그가 늘지 않는다.
2. **`gates/tools/` 밖에서 `run.sh` 를 다시 부르는 곳** — 실물 조회 결과 교착 위험 **0건**이다.
   - `scripts/harness/hooks/lifecycle_contract.py:386`(`run_gates`) — `COLAB_GATE_SUMMARY_CHILD=1` 만 주고
     `HELD` 를 주지 않는다. **의도된 형태다**(spec §C⑶): 잠금을 쥔 부모가 없으므로 자식이 스스로 잡고,
     결과적으로 `all` 의 `run_one` 과 같은 「solo 1건마다」 규칙이 된다.
   - `gates/tools/ci-schema-diff.sh:36` — CI 보조이고 `ALL_GATES` 밖이다.
   - `infra/staging/deploy.sh`·`scripts/harness/hooks/worktree-setup.sh` — `run.sh` 안에서 불리지 않는다.
   - 추가 안전판: 잠금을 잡은 프로세스는 `COLAB_GATE_MUTEX_HELD=1` 을 **export** 하므로, 게이트 본체가
     무엇을 다시 부르든 그 아래 전부가 면제된다.

**추가 실측(구현 중 확인)** — `{VAR}>` 로 연 fd 는 `exec` 를 건너 살아남는다. `gates/run.sh` 의
`case` 는 게이트 본체를 `exec` 로 갈아타므로 이것이 성립하지 않으면 잠금이 조용히 풀렸을 자리다.
함수 호출에 붙인 리다이렉션(`gate_host_mutex_acquire "$g" >> "$outdir/$g.out"`)도 fd 를 죽이지 않는다.
커널이 프로세스 종료 시 풀어 주므로 죽은 잠금은 남지 않는다.

## 커밋

### 1. 잠금 원시 ＋ 배선 (`9ece9104`)

**Files:** `gates/tools/_lock.sh` · `gates/run.sh`

- [x] `gate_host_mutex_acquire`/`gate_host_mutex_release` 2개 추가. 기존 `gate_lock_fd` 는 fd 9 고정
      ＋ 상한 없음이라 재사용 불가 — 새 함수는 `_pg.sh:95` 관용구(동적 fd) ＋ `flock -w <상한>` 이다.
- [x] 잠금 파일 = `${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host`. **새 경로 변수를 두지 않았다** —
      주입구가 있으면 그것이 곧 워크트리별 잠금 분리 통로다.
- [x] 세 실패 갈래(⑴ `flock` 부재 ⑵ 잠금 자리·파일 불가 ⑶ 상한 초과)를 전부 기존 보고 경로
      `readiness_env_wait` ＋ 78 로. **새 보고 경로 0건 · 면제 변수 0건.**
- [x] 선언 독법을 `all)` 밖으로 끌어올려 `gate_mode_read`/`gate_mode_of` 하나로 공유. 파서는 그대로.
      실효 모드에서 **미선언·표 파손은 안전한 쪽(`serial`)** 이다 — 단독 호출에서 「선언이 없다」를
      「병렬 안전」으로 바꾸는 자리를 만들지 않는다.
- [x] ⑴ 단독 호출 — 요약 래퍼(`:118`) **앞**에서 잡는다. 뒤에 두면 배출처를 주는 레인·H7 경로에서는
      면제된 자식만 도달해 잠금 0건이 된다. 획득 실패는 그 자리에서 `exit 78`.
- [x] ⑵ `all` — `run_one()` 안에서 **solo 게이트 1건마다** 획득 → 자식(`HELD=1`) → 해제.
      단독 구간 전체를 한 번에 잠그면 반대 레인이 17건을 기다려 상한을 넘긴다. `.span` 은 그대로.
      병렬 풀은 잡지 않고 `HELD` 도 주지 않는다. 잠금을 못 얻은 게이트는 **돌리지 않고** 78 로 적는다.
- [x] 요약 한 줄 — `── 호스트 뮤텍스 : 잠금 N건 · 면제(parallel 선언) M건 · 대기 누계 Xs`.
      단독 래퍼와 `all` **양쪽**에 선다(단독 회차에서도 면제가 건수로 드러나야 ⓔ 가 전수 없이 재진다).
- [x] `counts` 키 집합 무변경 · `_lock.sh` 기존 함수 서명 무변경.

### 2. 시험 seam 신설 ＋ 등록 5곳 (`15fd91ee`)

**Files:** `gates/tools/gate-host-mutex-selftest.sh`(신설) · `gates/run.sh` · `gates/config/parallelism.toml`
· `gates/README.md`

- [x] **구현 전에** 케이스 6건을 써서 red 를 실제로 확인했다 — 13개 단언 실패 · exit 1.
      red 로그 축자: `[selftest] ⓐ 실경과 0초 < 2초 — 기다리지 않고 78 을 냈다(잠금이 서지 않았다) ✗`
- [x] ⓐ 점유 중 대기 → 78 · `::gate-waiting::` · 준비 표식에 뮤텍스 경로 · **실경과 ≥ 상한**
- [x] ⓑ 점유 해제 뒤 green · **`waited` ≥ 1**
- [x] ⓒ 잠금 파일 열기 불가 → 78
- [x] ⓓ `flock` 부재 → 78 (PATH 수술 · `db-selftest.sh:466-475` 선례 · 면제 변수가 없으므로 주입 훅 없음)
- [x] ⓔ 면제는 둘뿐 — `parallel` 선언(＋ 요약의 면제 건수 ≥ 1) · `COLAB_GATE_MUTEX_HELD=1`.
      **`COLAB_GATE_SUMMARY_CHILD=1` 만 있는 호출은 점유 중이면 기다린다**(`task` 경로의 모양).
- [x] ⓕ 배출처를 선언한 레인 경로에서도 `::gate-waiting::` 이 **부모** 출력에 있고 78
- [x] ⓖ 선언표를 못 읽으면 단독 호출도 그 메모를 stdout 에 찍고 **안전한 쪽(잠근다)** 으로 접는다
      (커밋 4 · 어드바이저 ② 조건부 수용의 정정 항목)
- [x] 등록 5곳 — 어댑터 · `run.sh` case · `ALL_GATES` · `parallelism.toml`(**`parallel`**) ·
      README 표 한 행 ＋ 인덱스 실행비트 100755(`git update-index --chmod=+x`).
- [x] green-by-skip 방지 — **표식 문자열만 grep 하는 케이스를 두지 않았다.** ⓐ 의 실경과와 ⓑ 의
      `waited` 가 「잠금이 실제로 걸렸다」의 값 증거다.
- [x] 실제 호스트 잠금 **무접촉** — `TMPDIR` 을 자기 `mktemp -d` 로 물린다. 점유 동기화는 벽시계가
      아니라 FIFO 두 개(「잡았다」·「놓아라」)라 부하가 판정을 흔들지 않는다. 고정 `sleep` 은 ⓑ 한 곳뿐.
- [x] 대상 게이트는 `exec-bit`(인덱스 조회 한 줄)이고 픽스처 toml 로 `serial` 선언한다. 실제
      `parallelism.toml` 에서 `exec-bit` 은 `parallel` 이므로 **green 이면 실행기가 표를 실제로 읽은 것**이다.

### 3. 문서 (`7ad972ba`)

**Files:** `gates/README.md` · `gates/config/parallelism.toml` · `docs/decisions/0005-…md`
· `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md` · 이 파일

- [x] `gates/README.md` 「빨리 도는 것과 덜 보는 것은 다르다」의 `serial`/`db-selftest` 블록 아래에
      「호스트 뮤텍스」 절 — 무엇을 잡는가 · 잠금 키 · `::gate-waiting::` 형식 · `COLAB_GATE_MUTEX_WAIT`
      · 세 갈래 78 · **면제 변수 없음** · `parallel` 은 계속 돈다는 사실 · 요약줄.
- [x] `parallelism.toml` 헤더에 한 문장 — 「`serial` 은 이제 호스트 전역이다 — 프로세스 경계를 넘는다」.
- [x] ADR-0005 후속 **② 행만** 완료로 갱신(PR 번호 대신 「이 브랜치」). ③④ 행은 형제 몫이라 무변경.
- [x] `.agents/rules/colab-rules.md §3-1` 은 **건드리지 않았다** — 원본 규칙은 그대로이고 강제 수단이 생긴 것.

### 4. 정정 — 단독 호출이 「표를 못 읽었다」를 삼키던 자리

**Files:** `gates/run.sh` · `gates/tools/gate-host-mutex-selftest.sh` · `gates/README.md` · 이 파일

어드바이저 ② 검토에서 드러났다. 단독 호출이 선언표를 읽게 된 순간 **표를 못 읽었다는 사실도
단독 호출의 것**이 되는데, `GATE_PLAN_NOTES` 를 찍는 자리가 `all)` 안에만 있었다.

- [x] ⓖ 케이스를 먼저 써서 red 확인 — `[selftest] ⓖ 표를 못 읽었는데 단독 호출이 침묵했다 …✗`(exit 1).
- [x] **실제 원인은 출력 누락 하나가 아니었다** — 잠금 판정을 `[ "$(gate_mode_of "$GATE")" = serial ]`
      로 물었는데 **명령 치환은 서브셸**이라 `GATE_MODE` 도 `GATE_PLAN_NOTES` 도 부모로 돌아오지
      않았다. 잠금은 맞게 걸렸고 메모만 조용히 사라지는 모양이었다. 치환 밖에서 `gate_mode_read`
      를 먼저 부르도록 고쳤다(부모가 표를 쥐고, 서브셸은 이미 채워진 것을 읽는다).
- [x] 요약의 「호스트 뮤텍스 :」 줄 뒤에 `GATE_PLAN_NOTES` 를 그대로 출력해 닫는다.
- [x] ⓖ 는 메모 문자열만 보지 않는다 — **잠금 1건**(표 파손 = 미선언 = 안전한 쪽)을 함께 단언해
      메모가 장식이 아니라 실제 결정이었음을 값으로 받는다.

### 5. 정정 2 — `task` 경로 71게이트가 잠금 사실을 통째로 삼키던 자리

**Files:** `gates/run.sh` · `gates/tools/gate-host-mutex-selftest.sh` · `gates/README.md` · 이 파일

측정 레인의 전수 회차에서 **값으로** 드러났다. 「호스트 뮤텍스 : 잠금 N건 …」 줄이 요약 래퍼
블록 안에 있었는데, 래퍼는 `COLAB_GATE_SUMMARY_CHILD` 가 빈 실행에서만 돈다. `task` 경로
(`lifecycle_contract.py` `run_gates`)는 게이트마다 `CHILD=1` 자식을 부르므로 **잠금은 걸렸는데
71게이트 로그 어디에도 그 사실이 0건**이었다. 잠금이 섰다는 것과 그 사실이 남았다는 것은
다른 사실이고, 후자를 삼킨 것이 ADR-0005 개정의 「무의미하거나 판정이거나」에 걸린다.

- [x] ⓗ 케이스를 먼저 써서 red 확인 — `[selftest] ⓗ CHILD=1 자식 stdout 에 호스트 뮤텍스 줄이
      없다 (표식 없음) — task 경로 71게이트가 통째로 침묵한다 ✗` · `줄이 0회` (exit 1).
- [x] 인쇄 자리를 **잠금 여부가 결정된 그 블록**으로 옮겼다. `CHILD` 와 무관하게 찍히고,
      자식 stdout 은 게이트별 로그로 가므로 `task` 경로에도 남는다. 선언표 메모도 같이 옮겼다.
- [x] 래퍼 블록의 기존 줄은 **삭제**했다 — 인쇄 자리는 하나다. ⓗ 가 「정확히 1회」를 단언한다.
- [x] `all` 의 부모 집계 줄은 그대로다. 그 solo 자식들은 `HELD=1` 이라 이 블록에 오지 않아
      중복되지 않는다.

## 검증 결과

### ① 단독 게이트로 증명한 것

| 게이트 | 판정 | 값 증거 |
|---|---|---|
| `gate-host-mutex-selftest` | green | 케이스 **8건**(ⓐ~ⓗ). ⓐ 실경과 **2초** ≥ 상한 2초 · ⓑ **`waited=3`** ≥ 1 · ⓔ1 면제 건수 1 · ⓔ3 exit 78 · 2초 · ⓖ 표 파손 메모 ＋ 잠금 1건 · ⓗ CHILD=1 stdout 에 잠금 1건이 정확히 1회 |
| `harness-contract` | green | `parallel-safety declarations 72`(신설 selftest 가 선언표에 있다) |
| `harness-contract-selftest` | green | — |
| `db-selftest` | green | `_lock.sh` 의 기존 78 케이스 회귀 |
| `exec-bit` | green | 신설 `.sh` 포함 전건 100755 |

**3계수 = green 5 / red(판정) 0 / red(준비) 0 · 종료코드 0.** 한 명령(`gates/run.sh task`)으로
선언 집합을 각각 한 번씩 돌렸고 `verify-report` 가 green 이다.
⚠ 배출처는 `COLAB_GATE_REPORT_DIR` 이 아니라 **task runtime** 이다 — `run.sh:29-33` 의 `task` 갈래가
그 변수를 읽기 전에 `lifecycle_contract.py run-gates` 로 넘어가고, 보고서는 Git common dir 의
`colab-harness/<checkout-id>/<task-id>/<run-id>/gate-summary.json` 에 선다
(`docs/development/lifecycle-evidence.md` 「게이트」). 레포 안 `dev-package/reports/` 에는 아무것도
남지 않는다 — 산출물이 제품 파일을 만들지 않게 한 설계 그대로다.

### ② 하지 않은 것 — 남은 조건

- **전수 1회(`all -j 4`)를 이 레인은 돌리지 않았다.** spec 완료 조건 4(요약의 「잠금 17건」이
  `parallelism.toml` 의 `serial` 건수와 일치)는 **미증명**이며 측정 레인의 몫이다.
  `all` 의 뮤텍스 배선(`run_one`의 solo 획득·해제, 면제 건수 M = 풀 크기)은 단독 경로와 같은
  원시를 쓰지만 **전수 회차로 한 번도 관측되지 않았다.**
- 전수 2회 동시 실행(우려 #3 ⓑ)은 설계상 하지 않는다.
- 실브라우저 검증 — UI 변경 0건이라 해당 없음.
- PR 게시 · push-to-develop · 병합.

## 남은 위험

- **상한 900초의 실측 근거가 없다**(우려 #1 ⓐ 의 자인). 직전 전수 67건 총 9분 52초를 근거로 삼았을
  뿐, 단일 게이트의 최장 실행 시간은 아무도 재지 않았다. 78 이 나면 그 값이 곧 실측이고 그때 올린다.
- **`TMPDIR` 이 세션마다 다르면 전역성이 조용히 깨진다.** intent 어드바이저가 지적한 진짜 구멍이며
  이 spec 의 범위 밖이다(같은 구멍이 `COLAB_PG_SLOT_DIR` 에도 있다).
- 이 브랜치는 형제 브랜치 위에 쌓였다. `gates/README.md`·`docs/decisions/0005-…md`·
  `R-HARNESS-PR-CENTRIC.md` 세 파일을 형제와 공유하므로, develop 으로 바로 열면 인접 행 충돌이 난다.
