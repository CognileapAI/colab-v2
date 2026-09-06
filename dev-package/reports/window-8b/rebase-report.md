# 창 8-b 레인 재정렬 보고 — 새 `main`(R-A 회차) 위로

집행 2026-09-06 · 워크트리 `.claude/worktrees/agent-a1ba745710629d5e9` · 브랜치 `integration/w8b-rebased`
대상 = `origin/integration/w8b-dev-deploy` `0dc56ca`(14 커밋) → `origin/main` `2c3c16f` 위
병합 기저 = `87d5b87`(옛 `main` · 창 8-a done 지점)

**한 줄** — **ff 가 선다.** `2c3c16f` 가 `HEAD` 의 조상이고, 14 커밋 내용이 전건 살아 있으며,
전 게이트 전수는 **한 번의 실행으로 `green 50 / red(판정) 0 / red(준비) 0`** 이다.

---

## 1. 방식 — rebase 를 버리고 병합 커밋 하나로

⛔ **`git rebase origin/main` 은 2/14 에서 이미 충돌했다**(`dev-package/PLAN-SoT.md`).
§9 대장은 커밋마다 행이 붙는 자리라 **14 커밋을 되밟으면 같은 충돌이 커밋마다 반복**되고,
그때마다 개번을 손으로 다시 맞추면 **회차 중간 상태가 서로 어긋난다**(개번은 트리 전체를 한 번에 봐야 한다).

**그래서 `git merge origin/main` 한 커밋으로 갔다.** ff 조건은 그대로 선다 —
병합 커밋의 부모 하나가 `2c3c16f` 이므로 `main` 은 이 브랜치로 **전진만** 하면 된다.

| 축 | 실측 |
|---|---|
| `git merge-base --is-ancestor 2c3c16f HEAD` | **0**(조상이다 · ff 가능) |
| `main` 위 커밋 수 | **16** = 레인 14 ＋ 개번 1 ＋ 병합 1 |
| 레인 14 커밋 보존 | `git log --oneline 0dc56ca --not origin/main` = **14** |
| 텍스트 충돌 | **1건** — `dev-package/PLAN-SoT.md` 뿐 |

⭑ **개번을 병합 **앞**에서 했다.** 병합 기저 `87d5b87` 에 `〈343〉` 이상 인용이 **0건**이라,
병합 전 레인 트리의 `〈343〉`~`〈362〉` 는 **전건 8-b 출처**임이 기계로 판별된다.
병합 뒤에 개번하면 R-A 의 `〈343〉`~`〈347〉` 과 섞여 **한 건씩 출처를 캐야** 했다.

---

## 2. 개번 — `〈343〉`~`〈362〉` → `〈348〉`~`〈367〉` (일괄 ＋5)

규칙 = **병합 직전 `origin/main` 최대 ＋1**. 새 `main` 의 최대는 **`〈347〉`**(R-A) ⟹ 8-b 는 `〈348〉` 부터.

| 옛 번호 | 새 번호 | | 옛 번호 | 새 번호 |
|---|---|---|---|---|
| `〈343〉` | `〈348〉` | | `〈353〉` | `〈358〉` |
| `〈344〉` | `〈349〉` | | `〈354〉` | `〈359〉` |
| `〈345〉` | `〈350〉` | | `〈355〉` | `〈360〉` |
| `〈346〉` | `〈351〉` | | `〈356〉` | `〈361〉` |
| `〈347〉` | `〈352〉` | | `〈357〉` | `〈362〉` |
| `〈348〉` | `〈353〉` | | `〈358〉` | `〈363〉` |
| `〈349〉` | `〈354〉` | | `〈359〉` | `〈364〉` |
| `〈350〉` | `〈355〉` | | `〈360〉` | `〈365〉` |
| `〈351〉` | `〈356〉` | | `〈361〉` | `〈366〉` |
| `〈352〉` | `〈357〉` | | `〈362〉` | `〈367〉` |

- **범위 = 30 파일 · 881 인용.** 보고서 · `03-HANDOFF.md` · `work-items.yaml` · `sessions/` ·
  `CLAUDE.md` · 코드 주석 · 시험 머리말 · 게이트 로그(`*.txt`)까지 **한 벌로** 밀었다.
- ⛔ **R-A 의 `〈343〉`~`〈347〉` 은 한 글자도 건드리지 않았다** — 개번은 병합 **전** 레인 트리에서만 돌았다.
- **치환은 한 번씩만 일어난다** — 정규식 한 번에 함수로 매핑해 `362→367` 이 다시 `367→372` 로 밀리는 연쇄가 없다.
- **검산** — 개번 뒤 `〈343〉`~`〈347〉` 잔존 **0건** · `work-item-consistency` ㈔ 가 결정 번호 **316개**를
  세고 **중복 0**, 건너뛴 번호는 기존 결번 `〈290〉` **1건**뿐이다.

## 3. `PLAN-SoT §9` 충돌 해소 — 두 쪽을 오름차순으로 잇는다

유일한 텍스트 충돌. **R-A 5행을 앞에, 개번한 8-b 20행을 뒤에** 두었다.

- 결과 = `〈343〉` … `〈367〉` **연속 25행** · **결번 0 · 중복 0**
- 어느 쪽도 지우지 않았다 — 양쪽 행이 전건 산다.

## 4. 회차 — 8-b 는 **19차가 아니라 20차**다

**R-A 가 19차를 썼다**(`〈346〉` · `DataPeriod.granularity` ＋ `file_extension` · Ted 승인 2026-09-06).
레인은 자기 회차도 19차로 적었고 **둘이 부딪혔다** ⟹ 8-b 를 **20차**로 민다.

| 자리 | 고친 것 |
|---|---|
| `sessions/X2-FREEZE-PROTOCOL.md` §1 | 행 머리 **19 → 20** |
| 〃 개정 블록 | 「19차가 발급됐다 — 다음 해제는 20차」 → **「20차가 발급됐다 — 다음 해제는 21차」** |
| 〃 잇는 문장 | 「18차(`〈319〉`) 다음이 19차」 → **「19차(`〈346〉` · R-A) 다음이 20차」** |
| `PLAN-SoT §9 〈359〉` | 「회차 19차」·「㉰ 회차 = 19차(직전 18차 `〈319〉`)」 → **20차 · 직전 19차 `〈346〉`** |
| `03-HANDOFF.md` · `lane-report.md` · 드리프트 시험 2건 | 「회차 **19차**」 → **20차** |

⚠ **`§1` 표에 19차 행이 없다** — R-A 가 `PLAN-SoT §9 〈346〉` 에만 등재하고 §1 행을 세우지 않았다.
표가 18 → 20 으로 뛰므로 **그 사유를 개정 블록에 적어 뒀다**(회차의 정본 발급처는 §9 다).
⛔ **`prd/rounds/*` 의 19차 표기는 손대지 않았다** — 그것은 R-A 기획 문서이고 그때의 사실이다.

## 5. 마이그레이션 — 머지 리비전 `0014_merge_ra1_and_topic_vocab`

병합 뒤 `0012_merge_lv1_and_transfer` 위에 **head 가 둘**이 됐다.

    … ─ 0012_merge_lv1_and_transfer ─┬─ 0013_ra1_ext_interval_period ──┐
                                     └─ 0013_topic_vocab_six ──────────┴─ 0014_merge_ra1_and_topic_vocab

- **리비전 id = `0014_merge_ra1_and_topic_vocab` · 30자**(상한 32자 = `alembic_version_platform.version_num` `varchar(32)`)
- `upgrade`·`downgrade` **빈 채로 둔다** — 스키마를 한 글자도 바꾸지 않는다.
- ⛔ **`0013_topic_vocab_six` 는 이름도 부모도 바꾸지 않았다** — **이미 dev 에 적용된 id** 다.
- **순수 병합임을 이름으로 확인했다.** 둘 다 `d3_dataset_description` 을 만지지만 **교집합 0** —
  R-A = `observation_interval_{value,unit}` ＋ 그 제약 2 ＋ `d3_dataset_autometa.file_extension`·`period_granularity` ＋ 제약 1 /
  8-b = `d3_dataset_description_topic_check` **하나**.
- **`schema.sql` 은 두 쪽 합집합**이다 — 주제 CHECK **6값** ＋ R-A 의 신설 열·제약이 함께 선다.
- **실측** — `migration-single-head` **green**(platform head 1 = `0014…` · ai head 1) ·
  `schema-diff` **green**(두 체인 각각 선언 = 적용).

### ⚠ dev 가 다음 배포에서 받을 것

dev 의 `alembic_version_platform` 은 지금 **`0013_topic_vocab_six`** 다(`〈362〉` 재적재 시점).
⟹ **다음 dev 배포가 받는 것은 `0013_ra1_ext_interval_period` ＋ `0014_merge_ra1_and_topic_vocab` 둘**이고,
그 순서로 올라가면 head 는 하나가 된다. `03-HANDOFF §4.5` 에 같은 문장을 증보해 뒀다.

⭑ **판정용 적용 DB 도 같은 자리에 있었다** — `COLAB_APPLIED_DB_URL_PLATFORM` 이 `0013_topic_vocab_six` 였고,
`alembic upgrade head` 로 `0014…` 까지 올린 뒤에야 `schema-diff` 가 green 이 됐다. **dev 와 같은 모양의 예행이다.**

## 6. 두 쪽 행이 함께 사는지 — `work-items.yaml` · `03-HANDOFF`

- `dev-package/work-items.yaml` · `db/platform/schema.sql` · `routes/catalog.py` ·
  `upload/types.ts` · `frontend/test/upload.test.tsx` 는 **자동 병합**됐다(충돌 0).
- `03-HANDOFF.md` **§1 진실원 표** = R-A 행과 8-b 행이 **함께** 선다 —
  `work-item-consistency` ㈐ 가 **99행**을 대조해 불일치 **0**.
- `03-HANDOFF.md` **§4.5** = R-A 진입조건 블록과 8-b 창 블록이 **둘 다** 남았고,
  위 §5 의 마이그레이션 증보 한 줄이 더해졌다.

## 7. 게이트 — 한 번의 실행으로 전수

```
./gates/run.sh all -j 4     (env: ~/.colab-v2-test.env ＋ COLAB_PLANNING_ROOT)
── 계 : green 50 / red(판정) 0 / red(준비) 0        EXIT=0
```

- 로그 = `dev-package/reports/window-8b/gates-all-w8b-rebased.txt` (890줄)
- **잰 트리 = `cb4202dcd1418343f0a1418ee2730e52bfec607e`**(병합 커밋 `085e79c` 의 트리)
- 좁은 게이트 선실측 6건 전부 green — `work-item-consistency` · `planning-freshness` ·
  `migration-single-head` · `schema-diff` · `contract-lint` · `generated-up-to-date`
- ⚠ **전수 뒤에 트리에 더한 것은 셋뿐이다** — 이 보고서 · 게이트 로그 · `03-HANDOFF §4.5` 증보 한 줄.
  코드·계약·마이그레이션·스키마는 **한 글자도 바뀌지 않았다.** 문서를 읽는 게이트
  (`work-item-consistency`)는 그 뒤 **다시 돌려 green** 을 확인했다.

### 배선 준비 — 이 워크트리에서 새로 세운 것

전수 green 은 **배선을 갖춘 뒤**의 값이다(`red(준비)` 는 판정 red 가 아니지만 green 도 아니다).

- 서비스 `.venv` **4벌**(core-api · ai-service · viz-render · pipeline-worker) · `frontend/node_modules`
- `COLAB_PLANNING_ROOT` = 기획 패키지 폴더(**`40 COLAB-기획/00_기획원본/Co-Lab_ver2_…_260818_이태헌`**).
  ⚠ **`40 COLAB-기획` 루트를 그대로 주면 red 다** — 게이트가 찾는 것은 `에픽/` 을 품은 **패키지 폴더**다.

## 8. 남은 것 (이 회차가 닫지 않았다)

- **`db/ai` 체인은 여전히 4값이다** — `d9_topic_synonym` CHECK · 동의어 시드 · `CANON_TOPICS`.
  등록은 `〈365〉`(옛 `〈360〉`)에 그대로 살아 있다. 이 재정렬이 열지 않았다.
- **`schema.sql` 주제 열 머리말 산문이 아직 「넷」·「4값」으로 읽힌다**(선언은 6값 · 제약은 정확하다).
  ⛔ **이 회차가 고치지 않았다** — 레인이 병합 전부터 그 상태였고, 재정렬은 **레인이 판정받은 트리를
  옮기는 일**이지 그 안의 산문을 손보는 자리가 아니다. 다음 회차 후보로 남긴다.
