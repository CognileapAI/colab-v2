# R3 — 계보 제안의 정직한 빈 상태 · 게이트 직렬 요구 집행

레인 = `wt/lane1-measure` · 회차 2026-08-30 · 운영 스택 무접촉 · 배포 0건 · push 0건.
`main` 병합 = **fast-forward**(`9ec8a0b` → `1ba5be8`) · 충돌 0.

---

## 1. 계보 제안 — 「제안하지 않았다」가 값어치를 갖게 만든다

### 1.1 완료 정의는 이미 Ted 판정을 담고 있다 (확인함, 고치지 않았다)

`dev-package/work-items.yaml` 의 `K3` `completion_def` 는 `〈211〉` 판정문을 그대로 담는다 —
⑴ D4 쓰기 경로 부재 음성 테스트 · ⑵ 정직한 빈 상태 · ⑶ 수치 합격선은 별건. **불일치 없음.**

### 1.2 이번 회차가 막은 것 — 음성 판정이 공짜로 통과하는 자리

제안 기능은 **데이터가 없으면 무엇이든 0건**이다. 그래서 「제안하지 않았다」는 그 자체로는
아무것도 증명하지 않는다. **0건의 뜻을 셋으로 갈랐다.**

| 갈래 | 뜻 | 응답에서 갈리는 값 | 화면 `data-kind` |
|---|---|---|---|
| ㈏ | 뒤질 대상이 **있었고** 서비스가 **답했고** 0건이 **참인 답** — **제안이 가능했으나 하지 않았다** | `degraded=false` · `scope.searchedCount>0` | `searched-none` |
| ㈎ | 뒤질 대상이 **0건** — **제안이 가능했던 적이 없다** | `scope.searchedCount==0` | `nothing-to-search` |
| ㈐ | **물어보지 못했다** — 「없다」가 아니라 **모른다** | `degraded=true` ＋ `degradedReason` | `not-asked` |

**㈏ 가 음성 판정의 본체다.** ㈎ 만으로 green 을 내면 그것이 green-by-skip 이다.

### 1.3 픽스처 (주장이 아니라 시험)

- `services/core-api/tests/test_lineage_suggestions.py` — 신규 3건
  - 살아 있는 ai-service ＋ 연구실 안 후보 실재 ＋ 0건이 참인 답 (㈏)
  - 뒤질 대상 0건 (㈎)
  - **셋이 응답만으로 갈리는지** — 갈리지 않으면 화면은 거짓말밖에 못 한다
- `frontend/test/upload.test.tsx` — 신규 3건 (㈎㈏㈐ 각각의 문구·`data-kind`)
- `frontend/src/components/lineage/LineageStep.tsx` — 빈 상태 문구를 셋으로 갈랐다.
  범위 줄도 `searchedCount==0` 이면 「0건을 살펴봤어요」로 적지 않는다.

### 1.4 변이 시험 — 가르는 것을 되돌리면 red 다

| 되돌린 것 | 결과 |
|---|---|
| 중계가 0건을 전부 `degraded` 로 접게 함 (`relay.py`) | **2 failed** — 「물어보지 못한 것을 제안 안 함으로 세면 안 된다」·「세 0건이 응답에서 갈리지 않는다: {'not-asked'}」 |
| 화면 문구를 한 갈래로 접음 (`LineageStep.tsx`) | **2 failed** — `data-kind` 가 `searched-none` 고정 |

되돌린 코드는 전부 복원했다.

### 1.5 실측

- core-api `474 passed` · 실패 0 (일회용 postgres · `--rm` ＋ tmpfs ＋ 포트 미공개 · 시각 2026-08-30)
- frontend `280 passed` / 13 파일 · 실패 0
- `ai-no-lineage-write`(D4 쓰기 경로 부재 음성) = **green** (아래 `§3`)

### 1.6 ⛔ K3 를 닫지 않았다 — 판정이 남는다

완료 정의 ⑴⑵ 는 이번 회차로 **둘 다 green** 이다(⑶ 은 `〈211〉` 이 별건으로 뺐다).
글자대로 읽으면 `K3` 는 닫힌다. **그런데 계보 제안 서비스 자체가 아직 없다** — ai-service 에
`lineage-suggestions` 구현이 없고, 지금 green 인 것은 **중계와 화면이 0건을 정직하게 말한다**는
사실이다. 「제안 서비스」라는 이름의 항목을 **제안을 한 번도 만들지 않은 채** 닫는 것이
`〈211〉` 이 경계한 바로 그 모양인지, 아니면 판정이 의도한 대로인지는 **제품 판정**이다.
**정본이 말하지 않으므로 여기서 정하지 않는다.** `status` 무변경(`open`).

---

## 2. 게이트 실행기가 게이트의 직렬 요구를 지킨다

### 2.1 무엇이 틀려 있었나

`gates/README.md` 는 「**`db-selftest` 는 병렬로 돌리지 않는다**」고 **선언해 두었는데
실행기가 그 선언을 읽지 않았다.** 그래서 `-j 2` 에서 red · 단독에서 green 이었다 —
**판정이 아니라 배선이 낸 red** 이고, 앞선 거짓 red 와 같은 뿌리다.

### 2.2 고친 방향 (그리고 고르지 않은 길)

**선언을 표로 옮기고 실행기가 집행한다.** 표는 게이트 곁에 있고 실행기 안에 이름 목록으로
박히지 않는다 — `db-boundaries.toml`·`rls-allowlist.toml` 과 같은 배치다.

- 정본 = `gates/config/parallelism.toml` (27 선언)
- 읽는 자리 = `gates/tools/parallelism.py` — **여기서 기본값을 만들지 않는다.** 미선언은 미선언 그대로 넘긴다
- 집행 = `gates/run.sh all` — 단독 게이트를 **먼저 하나씩** 돌리고(그 구간엔 다른 게이트가 하나도 안 돈다),
  그다음 병렬 게이트를 풀에서 돈다. **출력 순서·검사 내용·판정 기준 무변경**

**고르지 않은 길** — 기본 병렬도 인하 ✗ · 재시도 ✗ · 게이트 건너뛰기 ✗. 셋 다 결함을 덮는다.

### 2.3 세 상태 (실측)

| 선언 | 동작 | 실측 출력 |
|---|---|---|
| `serial` | 단독 | `단독  db-selftest  (선언: serial)` |
| `parallel` | 풀 | `단독 1건 · 병렬 26건 · 미선언 0건` |
| **없음** | **단독 ＋ 명시** | `단독  <이름>  (**미선언 — 안전한 쪽을 골랐다.** …)` ＋ 요약줄에 미선언 건수 재기재 |
| 표 부재 | 전부 단독 ＋ 사유 | `⚠ 병렬 선언표를 읽지 못했다 (…) — 전 게이트를 단독으로 돌린다. FileNotFoundError…` |
| 값이 `serial`·`parallel` 아님 | 미선언 취급 ＋ 명시 | `⚠ 선언 값이 serial·parallel 이 아니다: db-selftest = 'maybe' — 미선언으로 보고 단독으로 돌린다.` |
| 표에만 있는 이름 | 드러낸다 | `⚠ 선언표에만 있는 이름: nope-gate (실행 목록에 없다)` |

### 2.4 「단독으로 돌았다」를 주장이 아니라 값으로 남긴다

`COLAB_GATE_OUTDIR=<경로>` 를 주면 게이트별 실행 구간(`<이름>.span` — 시작·끝 epoch)이 남는다.
아래 6회차 전부 **`db-selftest` 구간과 겹친 게이트 0건**을 구간 대조로 확인했다.

### 2.5 6회차 실측 (같은 커밋 · 2026-08-30)

| 회차 | 병렬도 | green | red | `db-selftest` | 단독구간 겹침 |
|---|---|---|---|---|---|
| 1 | `-j 2` | 25 | `schema-diff` · `stage2-markers` | **green** | 24.7s · **0건** |
| 2 | `-j 2` | 25 | `schema-diff` · `stage2-markers` | **green** | 27.7s · **0건** |
| 3 | `-j 2` | 25 | `schema-diff` · `stage2-markers` | **green** | 24.8s · **0건** |
| 4 | `-j 6` | 25 | `schema-diff` · `stage2-markers` | **green** | 24.2s · **0건** |
| 5 | `-j 6` | 24 | `schema-diff` · `stage2-markers` · **`rls-coverage`** | **green** | 24.9s · **0건** |
| 6 | `-j 6` | 25 | `schema-diff` · `stage2-markers` | **green** | 24.3s · **0건** |

**`db-selftest` 뒤집힘 = 6/6 green (종전 `-j 2` red).** 단독 기준선 = 41.6s green.

### 2.6 red 3종의 성격을 가른다

- **`stage2-markers` = 도구 부재** — 이 워크트리에 `services/pipeline-worker/.venv` 가 없다.
  게이트가 그 사실을 red 로 말하는 것이 **옳은 동작**이다. 우회·설치·범위 축소 하지 않았다.
- **`schema-diff` = 환경 부재** — `COLAB_APPLIED_DB_URL_PLATFORM`·`_AI` 미지정. 운영 스택은
  읽기 전용 경계라 이 레인에서 대지 않았다. 「못 돈 것」이지 통과가 아니다.
- **`rls-coverage` (`-j 6` 5회차 1건) = 환경** — 「빈 postgres 에 스키마를 적용하지 못했다」.
  **단독 재현 green.** `_pg.sh` 슬롯이 있어도 부하가 준비 시간을 뒤집는 계열(`〈…〉` 종전 관측)이
  `-j 6` 에 남아 있다. **이번 회차 범위 밖 · `[미확인]`**(푸는 법 = 컨테이너 준비 대기의
  실패 사유를 red 문면에 싣고 `-j 6` 다회 재측정).

---

## 3. 게이트 판정 (2026-08-30 · 이 워크트리)

**27종 = green 25 · red 2**(`schema-diff` 환경 부재 · `stage2-markers` 도구 부재) · **못 돈 것 0건.**
`ai-no-lineage-write` **green** · `db-selftest` **green** · `work-item-consistency` **green**.

---

## 4. `PLAN-SoT §9` 등재문 초안 (번호 미발급 — 오케스트레이터가 발급한다)

> **계보 제안의 0건을 세 갈래로 가른다 ＋ 게이트 실행기가 게이트의 직렬 요구를 집행한다**
>
> **㉮ 계보 제안 — 「제안하지 않았다」를 공짜로 만들지 않는다.** `〈211〉`-㉮-⑵ 「정직한 빈 상태」를
> 집행하면서 **0건의 뜻이 셋**임을 드러냈다: ㈏ **뒤질 대상이 있었고 서비스가 답했는데 0건이 참인 답**
> (`degraded=false` ＋ `scope.searchedCount>0`) · ㈎ **뒤질 대상이 0건**(제안이 가능했던 적이 없다) ·
> ㈐ **물어보지 못했다**(`degraded=true` — 「없다」가 아니라 「모른다」). **㈏ 가 음성 판정의 본체이고,
> ㈎ 만으로 green 을 내면 그것이 이 항목의 green-by-skip 이다.** 셋을 응답(`degraded`·`searchedCount`)과
> 화면(`data-kind`)에서 갈랐다. 픽스처 6건 신규(core-api 3 · frontend 3) · **변이 시험으로 증명**
> (가르는 것을 되돌리면 각각 2 failed). 실측 = core-api `474 passed` · frontend `280 passed` ·
> `ai-no-lineage-write` green. **계약 개정 0 · 마이그레이션 0** — `scope.searchedCount`·`degraded` 는
> 이미 계약에 있던 값이고, 이번에 한 것은 **그 값을 화면이 구별해 말하게 한 것**이다.
> ⛔ **`K3` 를 닫지 않았다.** 완료 정의 ⑴⑵ 는 둘 다 green 이지만 **계보 제안 서비스 자체가 없다** —
> 제안을 한 번도 만들지 않은 채 「제안 서비스」를 닫는 것이 판정의 뜻인지는 **제품 판정**이고
> 정본이 말하지 않는다. `status: open` 무변경.
>
> **㉯ 실행기가 게이트의 선언을 읽지 않고 있었다.** `gates/README.md` 는 「`db-selftest` 는 병렬로
> 돌리지 않는다」고 **적어 두었는데 `run.sh all` 이 그것을 읽지 않아** `-j 2` 에서 red · 단독에서 green
> 이었다 — **판정이 아니라 배선이 낸 red.** 고친 방향은 **병렬도 인하·재시도·건너뛰기 중 어느 것도
> 아니다**: 선언을 정본 표(`gates/config/parallelism.toml` 27건)로 옮기고 실행기가 집행한다(읽는 자리
> `gates/tools/parallelism.py` — **거기서 기본값을 만들지 않는다**). **세 상태** — `serial` 단독 ·
> `parallel` 풀 · **미선언은 안전한 쪽(단독)을 고르고 출력에 그렇게 적는다**(표 부재·잘못된 값·표에만
> 있는 이름도 각각 문면으로 드러난다). **「단독으로 돌았다」를 주장이 아니라 값으로 남긴다** —
> `COLAB_GATE_OUTDIR` 로 게이트별 실행 구간이 남고 겹침을 대조한다.
> **실측 6회차**(`-j 2` 3 · `-j 6` 3) = **`db-selftest` 6/6 green · 단독구간 겹침 6/6 0건.**
> ㉰ **red 를 성격으로 가른다** — `stage2-markers` **도구 부재**(레인에 pipeline-worker venv 없음) ·
> `schema-diff` **환경 부재**(적용 DB 미지정) · `rls-coverage` **환경**(`-j 6` 6회 중 1회 · 단독 재현
> green · 컨테이너 준비 시간 계열). 셋 다 **통과로 세지 않았다.** `rls-coverage` 의 `-j 6` 잔여
> 뒤집힘은 **`[미확인]`** 이고 이번 범위 밖이다.
