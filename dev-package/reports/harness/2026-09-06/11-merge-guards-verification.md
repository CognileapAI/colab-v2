# P-G 병합 가드 — 실행·검증 기록 (2026-09-06)

근거 스펙 = `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` **C절**(H3·H4·H5 행 ·
「삭제한 훅과 대체」 표) · **H 8행**(P-G 검증 항목) · **D절**(게이트 3상태) · **J-9**(훅 등록 위치 ·
README 킬스위치) · **K절**(문서 인용 검증 V1~V4 · 미검증 1). 규율 원본 = `.claude/rules/colab-rules.md §4`.

브랜치 = `worktree-harness-fable51-spec` · 기준 `origin/main` = `f2b61cd`.

---

## 1. 무엇이 생겼나

| 자리 | 무엇 | 성격 |
|---|---|---|
| `.claude/hooks/git-guard.sh` | H3 · `PreToolUse` matcher `Bash` | **차단**(exit 2) |
| `.claude/hooks/migration-guard.sh` | H4 · `PreToolUse` matcher `Edit\|Write` | **차단** |
| `.claude/hooks/decision-number-guard.sh` | H5 · `PreToolUse` matcher `Edit\|Write` | **차단** |
| `.claude/settings.json` | 위 셋을 `bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/<x>.sh"` 로 등재 | H1·H2 유지 |
| `dev-package/prd/tools/renumber-decisions.sh` | 〈N〉 재번호(dry-run 기본 · `--apply`) ＋ `--selftest` | 도구 |
| `dev-package/tools/merge-work-items.py` | `work-items.yaml` 전용 3-way 병합 드라이버 | 도구 |
| `dev-package/tools/merge-work-items-selftest.sh` | 위 드라이버의 자기 증명 6종 ＋ 실물 소요 측정 | 증명 |
| `dev-package/tools/README.md` | 드라이버 설정 두 줄 · 자동/충돌 갈래표 | 문서 |
| `.gitattributes` | `dev-package/work-items.yaml merge=work-items` | 선언 |
| `gates/tools/exec-bit.sh` · `exec-bit-selftest.sh` | 게이트 ＋ 셀프테스트 | 게이트 |
| `gates/run.sh` · `gates/config/parallelism.toml` · `.github/workflows/ci.yml` · `gates/README.md` | 위 게이트 등록 | 배선 |
| `README.md` 「하네스 훅」 | 훅 5개 1줄 설명 · `COLAB_HOOKS=0` · `settings.local.json` | J-9 집행 |
| `.claude/hooks/worktree-setup.sh` | 병합 드라이버 설정을 스폰 시점에 건다(증보 1블록) | H2 증보 |

---

## 2. 훅 검증 — 합성 `PreToolUse` JSON 을 stdin 에 먹여 실측

하네스 = 임시 파이썬 스크립트(레포에 남기지 않는다). 각 케이스는 문서 스키마 그대로의 payload
(`tool_name`·`cwd`·`tool_input.command` 또는 `tool_input.file_path`·`new_string`)를 훅의 stdin 에 넣고
**종료코드와 stderr 한 줄**을 잰다. `main` 브랜치 상태는 **일회용 레포**(`git init -b main`)로 재현했다 —
본 체크아웃을 읽지도 쓰지도 않는다.

### 2-1. 차단이 기대값인 것 — 9/9

| # | 훅 | 케이스 | exit | 차단 사유(stderr 요지) |
|---|---|---|---|---|
| ⑴ | H3 | `git push origin main` | **2** | main/master 로 push — `main` 은 오케스트레이터의 ff 병합으로만 움직인다 |
| ⑵ | H3 | `git push origin HEAD:refs/heads/main` | **2** | 〃 (refspec 목적지를 `refs/heads/` 까지 풀어 본다) |
| ⑶ | H3 | `git push --force-with-lease origin main` | **2** | main/master 로 강제 푸시 — 남의 커밋을 덮는다 |
| ⑷ | H3 | HEAD 가 `main` 인데 refspec 없는 `git push` | **2** | 현재 브랜치가 `main` 인데 refspec 없는 push |
| ⑸ | H3 | HEAD 가 `main` 일 때 `git merge lane`(**`--ff-only` 없음**) | **2** | main 은 전수 green ＋ 〈N〉 재실측 뒤 `git merge --ff-only <레인>` 로만 움직인다 |
| ⑸-b | H3 | HEAD 가 `main` 일 때 `git merge --no-ff lane` | **2** | 〃 (새 병합 커밋이 게이트 밖에서 생긴다) |
| ⑹ | H3 | `gh pr merge 12 --squash` | **2** | PR 병합은 전수 게이트·〈N〉 재실측을 건너뛴다 |
| ⑺ | H3 | `git branch -D main` | **2** | 기준 브랜치를 지운다 |
| ⑻ | H4 | Edit `db/platform/versions/0001_p0_platform.py` | **2** | 계약 파괴: origin/main 에 있는 마이그레이션은 수정 불가 — 새 revision 을 만든다 |
| ⑼ | H5 | Edit `PLAN-SoT.md` 에 `\| 〈500〉 \|` 행 추가 | **2** | 기대값 〈368〉 과 다르다 (기준 origin/main 최대 〈367〉 + 1) |

⭑ **⟨개정 2026-09-06 · P-J 설계 판정⟩ ⑸ 의 판정 기준이 바뀌었다.**
／ 종전 ~~`main` 에서의 **모든** `git merge` 차단(ff-only 포함)~~ — 그러면 오케스트레이터의
**승인된 병합 형태 자체**(`git merge --ff-only <레인>` · `rules §4-2`)가 정상 경로마다
`COLAB_HOOKS=0` 을 요구한다. 상시 무력화된 훅은 훅이 아니다.
**지금** — `main` ＋ `--ff-only` = **통과**(아래 ⑸-c) · `main` ＋ 그 밖의 `git merge` = **차단**.
새 병합 커밋을 만드는 형태만 막는다. 스펙 C 의 ⑶ 을 「ff 가 아닌 병합」으로 좁힌 것이다.

### 2-2. 통과가 기대값인 것 — 11/11 (오탐 반증)

| # | 훅 | 케이스 | exit |
|---|---|---|---|
| ⑸-c | H3 | **HEAD 가 `main` 일 때** `git merge --ff-only <레인>` (⭑ 개정 2026-09-06 · 오케스트레이터의 승인된 병합) | **0** |
| ⑽ | H3 | **레인 첫 줄** `git merge --ff-only origin/main` (비-main 브랜치) | **0** |
| ⑾ | H3 | `git push origin worktree-harness-fable51-spec` | **0** |
| ⑿ | H3 | `git fetch --all --prune` | **0** |
| ⒀ | H3 | `git pull --rebase` | **0** |
| ⒁ | H3 | `git worktree list` | **0** |
| ⒂ | H3 | `git push origin --delete worktree-lane-a` (워크트리 정리 규약 §2-1) | **0** |
| ⒃ | H3 | `npm ci --prefix frontend` (git 이 아닌 명령) | **0** |
| ⒄ | H4 | `README.md` Edit (마이그레이션 아님) | **0** |
| ⒅ | H4 | `db/platform/versions/0099_lane_new.py` Edit (origin/main 에 없다) | **0** |
| ⒆ | H5 | `PLAN-SoT.md` 편집이 기존 `〈363〉` 을 **인용만** 한다 | **0** |
| ⒇ | H5 | `PLAN-SoT.md` 에 `\| 〈368〉 \|`(= max+1) 행 추가 | **0** |

⑽ 은 스펙 H 8행이 명시적으로 요구한 오탐 반증이다(「레인 첫 줄 `merge --ff-only` 1회 통과 확인」).

### 2-3. 킬스위치 — 3/3

`COLAB_HOOKS=0` 을 주면 위 ⑴·⑻·⑼ 가 전부 **exit 0** 으로 즉시 통과한다. 모든 훅 스크립트의
첫 줄이 `[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0` 이다(스펙 C 「킬스위치」).

**계(2026-09-06 도입 시점) — 차단 9/9 · 통과 11/11 · 킬스위치 3/3 · 불일치 0.**

⭑ **⟨P-J 재실측 2026-09-06⟩ H3 전 케이스 재실행 — 차단 8/8 · 통과 8/8 · 킬스위치 1/1 · 불일치 0** (개정분 ⑸·⑸-b·⑸-c 포함. H4·H5 는 이 회차 변경 대상이 아니라 재실행하지 않았다). 실측표 = `dev-package/reports/harness/2026-09-06/12-gate-json-verification.md` §2.

### 2-4. 판정 근거로 삼은 문서 인용 (`https://code.claude.com/docs/en/hooks`)

- 입력 스키마 — `PreToolUse` 는 `session_id`·`transcript_path`·`cwd`·`permission_mode`·
  `hook_event_name`·`tool_name`·`tool_input`·`tool_use_id` 를 stdin JSON 으로 준다.
- `cwd` — "Current working directory when the hook is invoked". 워크트리 문서의 짝 문장 —
  "`cwd` follows Claude … Read it when a hook needs the worktree path" · "`${CLAUDE_PROJECT_DIR}`
  stays put". ⇒ **스크립트 자리는 `$CLAUDE_PROJECT_DIR`, 판정 대상은 `cwd`.**
- `tool_name`·`tool_input` — "The `tool_name`, `tool_input`, and `tool_use_id` fields are
  event-specific." ⇒ Bash 는 `tool_input.command`, Edit·Write 는 `tool_input.file_path`
  (＋ `new_string` / `content`).
- 차단 — exit 2 = "Blocks the tool call" · "The blocking message is the reason from your JSON's
  blocking decision when it makes one, and **your stderr text otherwise**."
- 통과 시 침묵의 근거 — "Stderr from a hook that exits 0 goes to the debug log only, never the
  transcript, and Claude never sees it."
- matcher — "`Bash` matches only the Bash tool; `Edit\|Write` and `Edit, Write` each match either
  tool exactly".

⚠ **exit 1 은 통과다**(스펙 C 축자 「차단은 **exit 2** 만 유효(exit 1 은 통과)」). 세 훅 모두
판정 불가(payload 파싱 실패 · `python3` 부재 · 체크아웃 아님)를 **통과**로 처리한다 — 파싱 실패가
모든 도구 호출을 막으면 훅이 세션을 세운다.

---

## 3. 알려진 한계 — 넓히지 않은 이유

`bash -c "git push origin main"` 처럼 **한 겹 감싼 명령**은 H3 가 잡지 않는다. 잡으려면 문자열
어디에나 있는 `git` 을 세야 하는데 그러면 `echo`·문서 편집 같은 무해한 호출이 걸린다.
**오탐이 붙은 차단 훅은 곧 `COLAB_HOOKS=0` 상시화로 끝난다** — 훅은 마찰 장치이지 보안 경계가 아니다.
이 한계는 각 스크립트 머리말과 `README.md` 「하네스 훅」 끝에 그대로 적었다.

---

## 4. 〈N〉 재번호 도구 — `--selftest` green

`dev-package/prd/tools/renumber-decisions.sh`. 기본은 **dry-run**, 기록은 `--apply`.
기준선은 `git show origin/main:dev-package/PLAN-SoT.md` 이고(규율 축자 「병합 직전 `origin/main`
기준 재실측」), 못 읽으면 `prd/tools/max-decision.sh` 로 물러서며 **그 사실을 사유에 적는다**.

- 행 머리 정규식은 **게이트가 이미 쓰는 것과 같은 것**을 쓴다 —
  `gates/tools/work_item_consistency.py:136` `DECISION_ROW_RE = re.compile(r"^\|\s*〈\s*(\d+)\s*〉\s*\|")`.
  두 벌로 두면 언젠가 갈린다.
- 대상 파일 = 대장 · `03-HANDOFF.md` · `WORK-UNITS.md` · `PLAN-SoT.md` · `sessions/**` · `reports/**` ·
  `prd/**`(`rules §4-1` 「브랜치 전 파일 일괄」).

셀프테스트 실측(임시 픽스처 · 기준선 〈100〉 · 브랜치 새 행 〈120〉~〈124〉) — **12/12 ✓**

| 확인 | 결과 |
|---|---|
| 새 행 5개가 `〈101〉`~`〈105〉` 로 내려왔다 | ✓ |
| 기준선 행 `〈96〉`~`〈100〉` 무수정 | ✓ |
| 대장·HANDOFF·WORK-UNITS·세션 기록·reports 사본의 **인용도 함께 이동** | ✓ (5곳) |
| `origin/main` 쪽 번호 인용(`〈99〉`·`〈100〉`) 무수정 | ✓ |
| 브랜치 밖 번호 인용(`〈119〉`) 무수정 | ✓ |
| **행에 붙은 `intent:`·`spec:` 역링크 보존** (intent 5 · spec 5) | ✓ |
| **표본 5행의 역링크 경로가 실존 파일을 가리킨다** (스펙 H 8행 점검 항목) | ✓ 결손 0 |
| **역링크가 끊기면 red** (파일 하나를 지우고 재실행 → exit 1) | ✓ |

⚠ 실물 `dev-package/intent/` 는 아직 0건이라(P-S 신설분) 증명은 **임시 픽스처**로 했다.
실물 대상 dry-run 실측 = 「기준 origin/main 행 316개 · 최대 〈367〉 · 브랜치 새 행 **0개** · 할 일 없음」.

모호한 자리는 **지어내지 않고 멈춘다** — 브랜치 새 행 번호가 기준 판에서도 인용된 번호면
기계 치환이 인용과 행을 가른다는 보장이 없으므로 exit 1 로 손을 뗀다.

---

## 5. `work-items.yaml` 병합 드라이버 — selftest green

`.gitattributes` 는 **이름**만 선언한다(`dev-package/work-items.yaml merge=work-items`).
실행 명령은 로컬 설정이 준다 — 레포 파일이 명령을 지정할 수 있으면 클론이 곧 코드 실행이라
git 이 그렇게 설계돼 있다. 두 줄은 `dev-package/tools/README.md` 에 있고, **레인 워크트리는
`.claude/hooks/worktree-setup.sh`(H2)가 스폰 시점에 자동으로 건다**(요약줄에 `설정됨` 으로 뜬다).
미설정이면 git 은 조용히 기본 텍스트 병합으로 돌아간다 — 종전처럼 충돌 표식이 남을 뿐 **위험이 늘지 않는다**.

| 케이스 | 기대 | 실측 |
|---|---|---|
| ⓐ 양쪽이 각자 끝에 새 WU 블록을 덧붙였다 | 자동 병합 | ✓ exit 0 · 순서 `R0 WU-X WU-Y`(상대 신규가 끝에) |
| ⓑ 상대만 어떤 WU 를 고쳤다 | 상대 판 채택 | ✓ exit 0 |
| ⓒ 상대가 지웠고 우리는 안 건드렸다 | 삭제를 따른다 | ✓ exit 0 |
| ⓓ **같은 WU 를 양쪽이 다르게 고쳤다** | **충돌** | ✓ exit 1 |
| ⓔ **같은 새 id 를 양쪽이 만들었다** | **충돌**(id 중복) | ✓ exit 1 |
| ⓕ **머리말을 양쪽이 다르게 고쳤다** | **충돌** | ✓ exit 1 |
| ⓖ 실물 대장(572,969 B · 140항목)에 두 레인 덧붙임 | 자동 병합 | ✓ 항목 **142** · **263~270 ms** |

⭑ **스펙 K 미검증 1 해소** — 「572KB·140항목에서 실용 속도인지」 = **0.3초 미만**. 실용 범위다.
⚠ 충돌 3종은 `git merge-file` 로 **표준 충돌 표식**을 남기고 exit 1 한다 — 조용히 한쪽을 고르면
갈렸다는 사실이 사라진다. 결과는 마지막에 `yaml.safe_load` ＋ **id 유일성**으로 다시 판정하고,
어느 하나라도 걸리면 역시 충돌로 물러선다.

---

## 6. `exec-bit` 게이트

판정 = `git ls-files -s -- '*.sh' | awk '$1=="100644"'` 이 한 줄이라도 있으면 **red(판정)**,
위반 파일을 이름으로 낸다. 대상 0건도 red(green-by-skip 금지), 체크아웃이 아니면 red(준비 · 78).

### 6-1. 도입 시점 실측 — red(판정) 57건

```
::error::exec-bit red(판정) — 인덱스 모드가 100644 인 `.sh` 가 57건이다 (전체 117건).
```

⚠ **레인이 만든 결함이 아니라 잠복해 있던 실물**이다(`rules §4-3` — 2026-09-03 draft PR #2 실측
「스크립트 20개, 그중 12개는 main 에도 100644 였으나 exec 하는 잡이 미실행이라 잠복」).
`main` 에서도 같은 값이며, 「main 과 동일」은 수용 근거가 아니다(`rules §3-3`).

### 6-2. 조치 — 57건 전부 `git update-index --chmod=+x`

내용 변경 0 · **모드만** 바뀐다. 게이트를 무르게 고치거나 검사 대상을 줄이지 않았다(`CLAUDE.md §4`).
새로 만든 `.sh` 7건도 같은 명령으로 인덱스에 100755 로 넣었다.

```
exec-bit green — `.sh` 124건 전부 인덱스 모드 100755 (100644 = 0건).
```

### 6-3. 셀프테스트 — green (4케이스)

| 케이스 | 기대 | 실측 |
|---|---|---|
| ⓐ 뿌리에 100644 `.sh` | red | ✓ |
| ⓑ 하위 폴더에 100644 `.sh`(정상 파일과 섞여 있어도) | red | ✓ |
| ⓒ 검사 대상 `.sh` 0건 | red | ✓ |
| ⓓ 전부 100755 | green | ✓ |

픽스처 레포는 `core.fileMode=false` 로 세운다 — 이 레포와 같은 조건(NTFS)에서 재현해야
「chmod 는 했는데 인덱스는 100644」라는 바로 그 상태가 만들어진다.

### 6-4. 배선

- `gates/run.sh` — `ALL_GATES` 에 `exec-bit`·`exec-bit-selftest` 등록 ＋ case 2개.
  셀프테스트 집합은 `ALL_GATES` 안의 `*selftest` 를 자동으로 뽑으므로 손목록 수정이 없다.
- `gates/config/parallelism.toml` — 둘 다 `parallel`(근거: 인덱스 **읽기만** · 일회용 레포 안에서만 씀).
  실측 `parallelism.py` 파싱 = `exec-bit parallel` · `exec-bit-selftest parallel`.
- `.github/workflows/ci.yml` — **`repo-hygiene` 잡 신설 · 경로 필터 없음**(실행비트 결함은
  `db/`·`infra/`·`services/` 어디서나 생긴다). 증명 → 판정 순서로 같은 잡에서 돈다.
- `gates/README.md` — 게이트표 2행 ＋ CI 배선표 1행 추가.

---

## 7. 함께 돌린 원장 게이트

`./gates/run.sh work-item-consistency` → **green**
(대장 140건 · ㈐ 99행 · ㈏ 62건 · ㈑ 37행 · ㈒ 6건 · ㈓ conflict 0 · ㈔ 결정 번호 316개 ·
㈕ stage 3 대조 15건 · 불일치 **0**).

전수(`all -j 4`)는 이 회차에서 돌리지 않았다 — 변경분이 훅·도구·게이트 1종·문서이고,
전수는 병합 직전 1회라는 규율(`rules §3-1`)을 따른다. **다음 병합 전 진입조건이다.**

---

## 8. P-S 후속 정정 (같은 커밋)

vendored 스킬이 **이 레포에 없는 상류 스킬**을 「REQUIRED SUB-SKILL」로 가리키고 있었다
(플러그인 비활성 ＋ 5종만 복사). 실행 불가 지시라 로컬 등가물로 치환했다 — 치환표는
`.claude/skills/VENDORED.md` 「공통 개조 4」.

| 상류 참조 | 치환 | 자리 |
|---|---|---|
| `superpowers:subagent-driven-development` | 위임 원칙(글로벌 `CLAUDE.md`) ＋ `lane-worker` | `writing-plans` 2 · `executing-plans` 1 |
| `superpowers:using-git-worktrees` | `lane-worker` `isolation: worktree`(자동) | `executing-plans` 1 |
| `superpowers:finishing-a-development-branch` | `colab-v2-work` §병합 규약 | `executing-plans` 1 |
| `superpowers:executing-plans` | `executing-plans`(로컬 vendored) | `writing-plans` 2 |

남긴 것 1건 = `test-driven-development/writing-good-tests.md:51` 의 `superpowers:writing-skills` —
문장 안 괄호 인용이고 그 파일은 개조표에서 **무수정**으로 못박혀 있다.
`receiving-code-review`·`verification-before-completion` 에는 상류 참조가 0건이다.

---

## 9. 스펙 H 8행 대조

| 스펙이 요구한 검증 | 실측 |
|---|---|
| 의도적 위반 5종 시도 → 5/5 차단 | **9/9 차단**(요구 5종을 포함해 넓혀 쟀다) |
| 레인 첫 줄 `merge --ff-only` 1회 통과 확인(오탐 반증) | **통과** ＋ 오탐 반증 10건 추가 |
| 재번호 후 표본 5건의 `intent:`·`spec:` 경로가 실존 파일을 가리키는지 | **5행 · 역링크 10건 · 결손 0** ＋ 결손 시 red 임을 증명 |

미이행 0건.
