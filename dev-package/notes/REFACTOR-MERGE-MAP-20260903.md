# 코드리뷰 리팩터 6브랜치 → `main` 병합 지도 (2026-09-03)

> 조사 범위 = 읽기 전용. **워크트리·브랜치 무접촉 · 게이트 미실행 · 파일 편집 0(이 문서 제외).**
> 기준 = `main` @ `2849d0d` · 측정 시각 2026-09-03.

## 0. 이 조사가 뒤집은 전제 — 먼저 읽는다

의뢰 문면은 「분기점이 `1526544`·`d4d11b5`·`16f3db7`·`b7ad4f7` 이고 `main` 이 오늘 ~60 커밋 앞섰다」였다.
**실측은 다르다.**

```
$ git merge-base main <6개 브랜치 전부>
d9e89a3a074ba859a27ffc4270579bc180317c81      ← 6건 전부 동일
```

- `1526544`·`d4d11b5`·`b7ad4f7` 는 **분기점이 아니라 브랜치 자신의 커밋**이다(`d4d11b5` = 레인 계획 커밋 = 6브랜치 전부의 공통 조상).
- 진짜 분기점 `d9e89a3` 는 **`main~6`** 이고, **오늘 배포된 서빙 릴리스 SHA 그 자체**다(`dev-package/sessions/V-2-CLOSE-20260903.md:1` 원장 행 `2026-09-03T12:43:56+0900 deploy d9e89a3a074b … green`).
- ⟹ `main` 이 앞선 것은 **60 커밋이 아니라 6 커밋**이고, **그 6 커밋은 전부 문서·대장이다**(코드 0줄).
- ⟹ 브랜치들은 **오늘 `main` 의 코드 전부를 이미 깔고 앉아 있다**. `invalidation.py`·`ownership.py`·`trigger_loop.py`·`preview.py`·`readers.py`·`storage_layout.py` 는 **분기점에 이미 존재**한다(확인 = `git cat-file -e d9e89a3:<path>` 전건 0).

**결론 — 코드 충돌은 구조적으로 불가능하다.** 남는 위험은 전부 §3 의미 충돌이다.

## 1. 계보

| 브랜치 | HEAD | 분기점 | ahead | behind | 최종 커밋 시각 | 실체 |
|---|---|---|---:|---:|---|---|
| `lane-review-clean` | `11462b5` | `d9e89a3` | 6 | 6 | 09-03 13:33 | **D 를 삼킨 병합 브랜치** |
| `worktree-agent-ac72b799fc10afb59` | `bfa50c5` | `d9e89a3` | 10 | 6 | 09-03 13:45 | 레인 B · core-api |
| `worktree-agent-a9df4b7601bb30d66` | `76b0d7a` | `d9e89a3` | 8 | 6 | 09-03 13:33 | 레인 C · viz-render |
| `worktree-agent-a146c87cfdffbbbf2` | `f771353` | `d9e89a3` | 6 | 6 | 09-03 13:37 | 레인 E · frontend |
| `worktree-agent-a160bc4c840f9061d` | `3cdedc4` | `d9e89a3` | 5 | 6 | 09-03 13:26 | 레인 D · pipeline+ai |
| `worktree-agent-a26a95673bf502c9e` | `d4d11b5` | `d9e89a3` | 2 | 6 | 09-03 12:48 | 레인 계획 문서뿐 |

### 1.1 포함 관계 — 6 개가 아니라 **4 개**만 병합하면 된다

```
d9e89a3 (=main~6, 서빙 릴리스)
 └ 1526544 리뷰 산출물 등재
    └ d4d11b5 레인 계획          ← a26a95…(2건)의 HEAD. 나머지 5개 전부의 조상.
       ├ …dafffcf→31d349d→3cdedc4  ← a160bc4…(레인 D)
       │                └ 11462b5   ← lane-review-clean = D 를 머지한 것
       ├ b7ad4f7→…→bfa50c5          ← ac72b7…(레인 B)
       ├ 67c04d1→…→76b0d7a          ← a9df4b…(레인 C)
       └ 3e74dae→…→f771353          ← a146c8…(레인 E)
```

실측 —
```
git merge-base --is-ancestor d4d11b5 <B·C·E·lane-review-clean>  → 전건 0 (조상이다)
git merge-base --is-ancestor 3cdedc4 lane-review-clean          → 0 (조상이다)
```

- **`worktree-agent-a26a95673bf502c9e` 는 병합 대상이 아니다** — 다른 넷 안에 이미 들어 있다.
- **`worktree-agent-a160bc4c840f9061d`(레인 D) 도 별도 병합 불필요** — `lane-review-clean` 이 이미 머지했다(파일 목록 19건 완전 동일).
- ⟹ 실병합 대상 = **B · C · E · lane-review-clean(=D)** 넷.

## 2. 파일 충돌 행렬 — **전 브랜치 0건**

`main` 의 6 커밋이 건드린 파일 **전부**(`git diff --name-only d9e89a3..main`) —

```
dev-package/03-HANDOFF.md          dev-package/notes/REMAINING-20260903-B.md
dev-package/PLAN-SoT.md            dev-package/notes/STAGING-WINDOW-RUNBOOK.md
dev-package/WORK-UNITS.md          dev-package/sessions/V-2-CLOSE-20260903.md
dev-package/notes/QA-STRATEGY-20260903.md   dev-package/sessions/WINDOW-20260903-F2.md
dev-package/work-items.yaml
```

교집합 실측 (`comm -12`) —

| 브랜치 | 영역 | 브랜치 변경 파일 수 | `main` 과 겹치는 파일 | ■ | ▲ | ○ |
|---|---|---:|---:|---:|---:|---:|
| `ac72b7…` (B) | core-api | 22 | **0** | 0 | 0 | 22 |
| `a9df4b…` (C) | viz-render | 20 | **0** | 0 | 0 | 20 |
| `a146c8…` (E) | frontend · gates | 25 | **0** | 0 | 0 | 25 |
| `lane-review-clean` (D) | pipeline-worker · ai-service | 19 | **0** | 0 | 0 | 19 |
| `a160bc4…` (D 원본) | 위와 동일 | 19 | **0** | 0 | 0 | 19 |
| `a26a95…` (계획) | 문서 | 2 | **0** | 0 | 0 | 2 |

**■ 0 · ▲ 0 · ○ 108.** 이유는 두 겹이다 —
1. `main` 의 6 커밋은 `dev-package/` 밖을 **한 줄도** 건드리지 않았다.
2. 브랜치들이 `dev-package/` 에서 만지는 것은 **신규 파일** `sessions/CODE-REVIEW-20260903{,-PLAN,-B,-C,-D,-E}.md` 뿐이고, `main` 이 만진 `PLAN-SoT.md`·`03-HANDOFF.md`·`work-items.yaml`·`WORK-UNITS.md` 는 **어느 브랜치도 안 건드린다.**

### 2.1 병합 시뮬레이션 (인메모리 · 워크트리 무접촉)

```
$ git merge-tree --write-tree main <branch>
lane-review-clean                    → CLEAN
worktree-agent-ac72b799fc10afb59     → CLEAN
worktree-agent-a9df4b7601bb30d66     → CLEAN
worktree-agent-a146c87cfdffbbbf2     → CLEAN
```

**예상 충돌 = 브랜치당 0 건.** 순차 병합에서도 0 이다 — 넷이 공유하는 `CODE-REVIEW-20260903.md`·`-PLAN.md` 는 공통 조상 `d4d11b5` 에서 온 **동일 blob** 이라 두 번째 병합부터는 아무것도 가져오지 않는다.

## 3. 의미 충돌 — diff 가 안 보여 주는 것. **여기가 진짜 작업이다**

### ⓐ ⛔ 레인 C 가 `main` 이 오늘 잰 눈금을 무효화한다 — 유일한 실질 차단

- 브랜치: `services/viz-render/src/colab_viz/app/routes/values.py:43` 에 **`deps.tenant_scope(request)` 한 줄 추가**.
- `deps.py:78` 축자 — 「**경계를 읽는 한 자리** — (연구실, 계정). **없으면 400 이고, 열어 주지 않는다.**」
- `main` 최신 커밋 `2849d0d` 〈304〉 는 **바로 그 op** 을 staging 에서 95회 불러 p95 261 ms 를 확정했다. 그 실측의 자격은 **베어러 하나뿐**이었다(`V-2-CLOSE-20260903.md §2` 축자 — 「부른 op = `POST /api/v1/datasets/{datasetId}/value-lookup` **하나뿐**」, 헤더는 베어러 ＋ UA).
- ⟹ 병합 즉시 **〈304〉 의 재현 경로가 400 으로 죽는다.** 값 자체가 틀렸다는 뜻은 아니지만, **「다시 재면 같은 값이 나온다」가 성립하지 않는다.**
- ⟹ 또한 **호출자(core-api 중계 · 프론트)가 경계 헤더를 싣는지 미확인**이다. 안 싣는다면 값 조회 화면이 통째로 400 이다 — **레인 C 병합 전 반드시 사람이 확인할 항목.**
- ⚠ 브랜치 주석 자신이 「여기서 **대조는 하지 않는다**」고 적었다(헤더 존재만 요구). 즉 보안 이득은 얇고 파손 위험은 두껍다 — **이 한 줄만 떼어 유보하는 선택지가 있다.**

### ⓑ 레인 C 의 캐시 키 변경 → 이미 구운 산출물이 전부 미스가 된다

- `readers.py` 에 `_parse_instant`·`_time_index`·`_instant_labels` 신설, `cache.py` 키에 **시각 ＋ 격자 digest** 추가(커밋 `5de693f`).
- 브랜치 축자 — 종전 `while raw.ndim > 2: raw = raw[0]` 이 **언제나 첫 시각**을 집었고 「**틀린 시각이 모든 시각에 대해 서빙**됐다」.
- ⟹ **기존 캐시·타일이 전부 「틀린 값」이라는 뜻**이다. `main` 의 소유 원장 실측(`03-HANDOFF.md:24` — 대상 49 · 판정 불가 49 · 고아 0)과 지도 타일 계수가 병합 후 **재굽기 전까지는 의미가 없다.**
- ⟹ 병합 후 **산출물 재굽기 + 소유 네 등급 재실측**이 따라붙는다. `main` 이 그 문서에 적어 둔 「바뀌지 않은 것이 정상이다」는 병합 뒤에는 **거짓**이 된다.

### ⓒ 레인 B 가 501 계수를 23 → 4 로 정정한다 — 대장 다섯 자리가 낡는다

- `not_implemented.py:1` 문서화 문자열 「23 개」→「**4 개**」. 브랜치 축자 — 「아래 문단들이 23 → 22 → 20 → 19 → 16 → 9 → 12 → 4 를 한 줄씩 적어 내려가는 동안 **첫 줄만 안 따라갔다.**」
- `main` 측 501 표 기재 = `WORK-UNITS.md:70`(22→20) · `:221`(24→21) · `:691`(5→4) · `03-HANDOFF.md:21`(5→4) · `:27`(8→5) · `:30`(16→8).
- **파일 충돌은 아니다**(브랜치가 저 문서들을 안 건드린다). **정합성 충돌**이다 — 병합 후 정본 계수를 한 번 확정해 대장에 한 줄로 못박아야 한다. 오라클은 브랜치가 지목한 `OPERATIONS` ＋ `tests/test_not_implemented.py`.

### ⓓ 레인 E 가 **게이트를 하나 늘린다** — 43 이 44 가 된다

- 신규 `frontend/scripts/reachable-from-entry.mjs`(53줄) — 운영 진입점에서 닿는 모듈에 픽스처가 있으면 `rc=1`.
- 현재 `gates/tools/` = **58 파일**. 이 스크립트는 `gates/` 밖에 있어 **아직 게이트 목록에 안 잡힌다.**
- ⟹ 「게이트 43 green」 합격선을 그대로 쓰면 **이 검사는 안 돌아간다.** 등재하든(계수 갱신) 유보하든 **결정이 필요하다** — 조용히 넘어가면 브랜치가 만든 회귀 방지가 죽는다.
- 또한 E 는 픽스처 폴백을 **제거**한다(`3e74dae`) — 401 은 인증 경로로, 그 밖은 오류 화면. `frontend-test` 계수(`main` 기준 422)가 **오른다**. 계수 하락이 아니라 상승이므로 차단은 아니다.

### ⓔ `〈294〉`·`〈286〉`·`〈272〉`·`〈271〉` 은 **재검토 대상이 아니다**

의뢰가 지목한 `invalidation.py`(reclaim_plan 〈272〉) · `ownership.py` · `trigger_loop.py`(〈286〉 #60) · `preview.py` 사이드카 〈271〉 · `readers.py` · 생성 상수 〈294〉 는 **전부 분기점 `d9e89a3` 에 이미 있다.** 브랜치들은 그것들을 **깔고** 고쳤다. 특히 —

- 커밋 `a2c8edd`「무효화를 완료 경로로 · 트리거 격리를 봉투 단위로」는 **`invalidation.py` 를 건드리지 않는다** — 실제 편집면은 `trigger_bus.py`(+77) · `triggers.py`(+42) · `jobs.py`(+57). 〈272〉 의 `reclaim_plan` 과 **편집면이 안 겹친다.**
- 커밋 `67c04d1`「테넌트 경계 헤더를 job 에 새기고」는 `jobs.py`·`deps.py` 만 만진다. `ownership.py` 무접촉.
- ⟹ **재작성 필요 없음.** 위 ⓐ~ⓓ 넷만 남는다.

## 4. 대장 충돌 — **0 건**

| 검사 | 결과 |
|---|---|
| 브랜치가 `PLAN-SoT.md` 를 쓰는가 | **아니다** (6건 전부 무접촉) |
| 브랜치가 `work-items.yaml` 을 쓰는가 | **아니다** |
| 브랜치가 `03-HANDOFF.md` 를 쓰는가 | **아니다** |
| 브랜치가 새 결정번호를 **발급**하는가 | **아니다** — 신규 문서 6건에서 발급 0. 참조뿐(`CODE-REVIEW-20260903.md` 의 `〈300〉`, `-D.md` 의 `〈63〉`) |
| 브랜치가 새 항목 id 를 발급하는가 | **아니다** — `WI-`·`PA-`·`LV-`·`VZ-`·`Q-` 패턴 신규 0건 |

`main` 은 이 6 커밋에서 `〈287〉`~`〈304〉` 를 채우고 `TL-1` 항목 하나를 신설했다. **브랜치와 겹치는 번호·id 없음.**

⟹ **병합 후 결정번호를 새로 발급해야 한다.** 리팩터 4레인의 등재가 `§9` 에 아직 없다 — `〈305〉` 이후 4~5 개(레인 B·C·D·E ＋ 병합 회차)를 발급하고, 위 ⓐ~ⓓ 를 그 안에 판정으로 박는다.

## 5. 권고 병합 계획

### 5.1 순서 — **rebase 하지 않는다. merge 한다**

**결정 근거 = 넷의 편집면이 서비스 트리 단위로 완전히 분리돼 있고 `main` 과 겹치는 파일이 0 이다.** rebase 는 이 상황에서 얻는 것이 없고(충돌 0), 잃는 것이 있다(6브랜치 SHA 가 바뀌어 Ted 의 라이브 세션이 깨진다 — 워크트리 6개가 **잠겨 있다**).

| 순 | 브랜치 | 방식 | 예상 충돌 | 이유 |
|---|---|---|---:|---|
| 1 | `lane-review-clean` (=D ＋ 계획문서) | `git merge --no-ff` | **0** | 계획·리뷰 정본 문서를 먼저 들여놓는다. 나머지 셋의 공통 조상 `d4d11b5` 를 흡수해 이후 병합의 문서 델타가 0 이 된다. 코드는 pipeline-worker·ai-service — **다른 셋과 트리 무교차** |
| 2 | `worktree-agent-ac72b799fc10afb59` (B) | `git merge --no-ff` | **0** | core-api 단독. ⓒ 501 계수 정정이 여기서 들어오므로 대장 갱신을 **한 번에** 하려면 먼저 |
| 3 | `worktree-agent-a9df4b7601bb30d66` (C) | `git merge --no-ff` ＋ **한 줄 유보 판정** | **0**(기계) / **1건 사람** | viz-render 단독. ⓐ `values.py:43` 을 **살릴지 뗄지**가 병합 전 결정 사항 |
| 4 | `worktree-agent-a146c87cfdffbbbf2` (E) | `git merge --no-ff` | **0** | frontend 단독. ⓓ 게이트 등재 결정이 붙으므로 마지막 |
| — | `worktree-agent-a160bc4c840f9061d` | **병합하지 않는다** | — | 1번에 포함됨 (`3cdedc4` 는 `11462b5` 의 조상) |
| — | `worktree-agent-a26a95673bf502c9e` | **병합하지 않는다** | — | 전 브랜치의 공통 조상 (`d4d11b5`) |

### 5.2 기계 vs 사람

- **기계 = 전부.** 텍스트 충돌 0건, 4회 병합 모두 `merge-tree` CLEAN.
- **사람 = 셋.** ⑴ ⓐ `values.py` 경계 한 줄의 go/no-go(호출자가 헤더를 싣는지 실측 후) ⑵ ⓒ 501 정본 계수 확정 ⑶ ⓓ `reachable-from-entry.mjs` 게이트 등재 여부.
- **재작업 = 하나.** ⓑ 캐시 키 변경 뒤 산출물 재굽기 ＋ 소유 네 등급 재실측.

### 5.3 go/no-go 체크리스트

각 병합 **직후** —

- [ ] 게이트 `all` — **green 계수를 병합 전에 먼저 재고**, 병합 후와 대조한다. 「43 green」을 기억으로 쓰지 않는다(`CLAUDE.md §0`).
- [ ] `contract-breaking` — **red 0.** 레인 B·C·D 는 계약 델타 0 을 자칭한다(`CODE-REVIEW-20260903-D.md` 「계약 델타 0」). **자칭을 믿지 말고 게이트로 판정한다.**
- [ ] `frontend-test` — E 병합 후 계수가 `main` 기준 **422 이상**. 하락하면 중단.
- [ ] 서비스별 시험 계수 — core-api 519 / viz-render 232 / pipeline-worker 222 / ai-service 145 를 하한으로 대조(`03-HANDOFF.md:24` 실측). **하락 = 중단.**
- [ ] `tsc` 무오류.

4회 병합 **완주 후** —

- [ ] ⓐ 판정 문서화 — `values.py` 경계가 살아 있다면 **〈304〉 눈금을 다시 잰다**(경계 헤더 실은 채). 유보했다면 그 사실을 `§9` 에 적는다.
- [ ] ⓑ 산출물 재굽기 ＋ 소유 네 등급 재실측 → `03-HANDOFF.md` 의 「판정 불가 49」 행 갱신.
- [ ] ⓒ 501 정본 계수 1회 확정 → `WORK-UNITS.md`·`03-HANDOFF.md` 갱신.
- [ ] ⓓ 게이트 등재 결정 → 게이트 계수 갱신.
- [ ] `PLAN-SoT §9` 에 `〈305〉` 이후 발급 · `work-items.yaml` 항목 신설(현재 최댓값 뒤).
- [ ] staging 배포는 **위 넷이 다 닫힌 뒤**. ⓑ 미해소 상태로 배포하면 **틀린 시각의 캐시가 살아 있는 채로 나간다.**

### 5.4 ⚠ 진행 전 확인

워크트리 6개가 **잠겨 있고**(`git worktree list` — `locked` 표시) Ted 세션이 살아 있다. **브랜치 SHA 를 바꾸는 어떤 조작도(rebase·amend·force) 지금 하지 않는다.** 위 계획이 merge 만 쓰는 이유가 이것이다.
