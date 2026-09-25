# WU1 리허설(실모드) — 게이트 ③ 판정 패킷

메타 — intent `dev-package/intent/2026-09-24-corpus-expansion-dev-reseed.md` · 레인 lane-worker ·
기준 커밋 `2417e2ed` · 가지 `corpus-wu1-rehearse` · 측정 2026-09-24T07:16~07:19Z ·
**dev 쓰기 0건**(읽기 전용 조회 · preflight · 리허설. 원격에 생긴 것은 ⑸ 가 만들고 같은 스크립트가 지운 임시 폴더뿐).
발췌 로그 = `dev-package/reports/corpus-expansion/wu1-rehearsal-log-2026-09-24.txt`.

**한 줄** — 리허설이 실모드로 **처음 돌았다**(원시동작 10 · 통과 9 · 어긋남 1).
어긋난 하나는 `deploy_doctor` 가 **13/15** 라는 것이고, 그 둘(⑥·⑭)은 재시드가 만든 것이 아니라 **지금 dev 의 상태**다.
그리고 대상 ref 를 `origin/develop` 으로 두면 WU2 는 **시작조차 못 한다** — 아래 §1.

---

## 1. 대상 ref — 기본값 `origin/develop` 을 채택하지 않았다 (기록 · 문의 아님)

지시의 기본값은 `origin/develop`(`02d251d81b5466c64fd38e7367df0c02a2a3b32a`)이었다. **쓸 수 없다.** 근거 셋 —

| # | 사실 | 근거 |
|---|---|---|
| ⑴ | `02d251d8` 은 **PR 병합 커밋이 아니다**(부모 1건 `9191671a`) | `release_evidence.py:42` 가 `pr.merge_commit_sha == sha` ＋ `merged: true` 를 요구한다. 지어내지 않고는 pre 증거가 서지 않는다 |
| ⑵ | 그 sha 의 CI 가 **failure** (run `35939329152`) | `verify_evidence.py:276-277` — 「CI bundle not green」 |
| ⑶ | dev 에 `colab-v2/core-api:dev-02d251d81b54` 이미지가 **없다** | 원격 `docker images` 실측(발췌 로그 말미). `stages.sh:31 core_image()` 가 그 태그를 `reset`·`prelude` 에 마운트한다 — 배포를 건너뛰면 `reset` 이 그 자리에서 죽는다 |

**채택 = `COLAB_RESEED_TARGET_REF=ea21d8c2aa54`** — dev 가 지금 실행 중인 sha.
PR **#123** 병합 커밋(`merged=true` · `base=develop` · `merge_commit_sha` 일치) · `origin/develop` 의 조상 ·
`core-api`·`migrator` 이미지 둘 다 dev 에 실재 · 그 sha 의 push CI(run `35338885223`)는 **green**(green 5 · red 0).

- 지시가 적은 근거(「코퍼스 측정은 일회용 DB 에서 스냅샷을 재생하므로 dev 는 자료＋자동메타만 있으면 되고,
  미병합 `k3-resume` 를 dev 에 배포할 이유가 없다 · develop 병합은 Ted 보류」)는 **그대로 성립한다.**
  이 선택은 그 근거를 더 밀어붙여 **배포를 0건으로 만든다** — `--from reset` 으로 `deploy` 단계 자체를 뺀다.
- 결과 ㉮ dev AI 체인은 `0007_merge_vocab_and_category` 에 머문다(원장 표 `d10_model_call` 없음 — 무해).
  ㉯ 플랫폼 체인은 `reset` 뒤 migrator 이미지(`dev-ea21d8c2aa54`)가 **`0033_admin_body_access`** 로 세운다
  — 리허설의 `alembic current` 두 체인이 모두 `(head)` 로 응답한 것이 그 증거다.

## 2. preflight — **통과 11 · 미달 0** (WU0 의 미달 2 가 둘 다 해소됐다)

| 항목 | 판정 | 값 |
|---|---|---|
| `git` | ✓ | 대상 `ea21d8c2aa54` ∈ `origin/develop` · 작업 트리 깨끗 |
| `dev-sha` | ✓ | dev 실행 sha `ea21d8c2aa54` **= 대상 sha** |
| `aws` | ✓ | sts 갈래 성립 · 계정 …7146 (deploy 단계 없음 — 환경변수 갈래 불요) |
| `qemu` | ✓ | binfmt qemu-aarch64 등록 · buildx `linux/arm64` |
| `leftovers` | ✓ | 진행 중 배포 0 · 임시 컨테이너 0 |
| `ref-root` | ✓ | `DATASETS.md` 4건 존재 |
| `agent-browser` | ✓ | doctor fail 0 |
| `secrets` | ✓ | 9건 존재 · 전건 0600 |
| `resources` | ✓ | 메모리 18,353 MiB · 로컬 831 GiB · **EC2 디스크 2,930,540,544 B**(> 2 GiB) |
| `build-plan` | ✓ | datasets 28 · edges 18 |
| `seed-inputs` | ✓ | 계정·비밀번호 입력 검증 완료(값 미기록) |

- WU0 의 `resources` 미달은 오케스트레이터의 이미지 정리로 해소됐다.
- WU0 의 `dev-sha` 미달은 **deploy 를 켜서가 아니라 대상 sha 를 dev 의 실행 sha 로 맞춰서** 해소됐다
  (`preflight.sh:57-59` — `cur == TARGET_SHA` 면 deploy 단계와 무관하게 ✓).

## 3. 리허설 — 원시동작 **10 · 통과 9 · 어긋남 1** (바꾸는 단계 0건)

| # | 원시동작 | 판정 | 실측 |
|---|---|---|---|
| ⓪ | `executor --check` | ✓ | 후보 계획·pre 증거 통과. build/ship/tree 실제 실행 준비성은 **미측정** |
| ⑴ | `psql_master_query` | ✓ | 작은따옴표 든 SQL 이 그대로 닿는다 |
| ⑵ | `ssh_script` | ✓ | 따옴표·`$`·백틱 되받기 일치 |
| ⑶ | `compose_ps` | ✓ | `core-api` 검출 |
| ⑷ | `migrator_platform` · `migrator_ai` | ✓✓ | 두 체인 `alembic current` = `(head)` |
| ⑸ | `reset_tool_s3_plan` | ✓ | **키 1,778건 · 멀티파트 0 · 접두사 `previews/`·`uploads/` · sha256 `2de0ac82…`** |
| ⑹ | `psql_owner_url` | ✓ | 소유자 URL `select 1` |
| ⑺ | `doctor_summary_line` | **✗** | 기대 `항목 15 — ✓ 15 · ✗ 0 · ─ 0` · 실측 **`✓ 13 · ✗ 2 · ─ 0`** |
| ⑻ | `runner_phase_report` | ✓ | `완료 0 / 28 · 계획 총량 5,176,422,065 B`(본체 3,641,736,593 ＋ 보조격자 1,534,685,472) |
| ⑼ | `agent_browser_title` | ✓ | dev 첫 화면 제목 읽힘 |

- 소요 = preflight 3초 ＋ rehearse 11초. `result.json` = `outcome failed` · `failedStage rehearse` ·
  `blocked[1] = rehearse:doctor_summary_line` · 나머지 9단계 `skipped`.
- **리허설이 재지 못하는 것** — `build`/`ship`/repo-tree 반입의 실제 실행, `reset` 의 정지·DROP, 업로드,
  화면 등재 28건, 미리보기 판정. 리허설은 **원격 줄이 읽히는가**만 잰다.
- ⛔ 도구 사실 하나 — `--rehearse` 는 `--release-plan` 을 **무조건** 요구한다(`stages.sh:1029 → 1015 → 966`).
  `--from reset` 으로 도는 WU2 는 그 계획을 **한 번도 쓰지 않는데**(`stages.sh:113-115` — `release_plan_execute` 는
  `stage_deploy` 전용) 리허설만 그것을 가로막는다. 이번에는 **진짜 증거**로 통과시켰다(§7 입력 자리).

## 4. `doctor` 13/15 의 정체 — WU2 는 **verify 에서 죽는다** (④ deploy 귀결)

| 항목 | 실측 축자 | 정체 |
|---|---|---|
| ⑥ 스키마 head (platform) | `DB 0033_admin_body_access ≠ 레포 head 0032_labless_operator` | dev 의 `/opt/colab-repo` 는 git 이 아니라 **tar 사본**이고 `db/platform/versions` 최신이 `0032` 다(원격 `ls` 실측). DB 는 `0033`. DR-2-runbook:83 축자 — 「`ship.sh` 가 `/opt/colab-repo` 를 같은 회차에 밀지 않아 `deploy_doctor` ⑥ 이 **옛 head 를 정답으로 삼는다**」 |
| ⑭ 백업 24h | `139.6시간 전 · 객체 83건` | dev 백업 cron 이 6일 가까이 돌지 않았다. 재시드와 무관한 선행 상태 |

- 그 트리를 미는 자리는 **배포 패킷의 repo-tree 단계**다(DR-2-runbook §1-3 tar 경로 · 릴리스 계획의 `06-repo-tree.sh`).
  ⇒ **deploy 를 건너뛰면 ⑥ 은 그대로 남는다.**
- `stage_verify` 는 `doctor_once`(`stages.sh:358` → `137-152`)로 **15/15 를 요구**하고 아니면 비영 종료한다.
  ⇒ 지금 이대로 WU2 를 돌리면 **자료·계보·자동메타를 다 심고도 `verify` 에서 red** 로 끝난다.
- 선행 2건 — 둘 다 **파괴 아님 · dev 자료 무접촉** —
  ㉮ `/opt/colab-repo` 트리를 `ea21d8c2aa54` 의 트리로 갱신(DR-2-runbook §1-3: 개발 기계에서 tar → `sudo tar xzf … -C /opt/colab-repo --overwrite`).
     그 트리에는 `0033_admin_body_access.py` 가 들어 있다(이 체크아웃에서 확인) ⇒ ⑥ ✓.
  ㉯ dev 백업 1회(`infra/dev/backup.sh` · cron 은 `infra/dev/install-cron.sh`) ⇒ ⑭ ✓.
  ㉮㉯ 뒤 `--preflight-only` 와 doctor 를 **한 번** 더 내서 `항목 15 — ✓ 15 · ✗ 0 · ─ 0` 을 눈으로 본 다음 `reset` 을 낸다.

## 5. WU2 가 dev 에 하는 일 — 단계별 · 실행 명령 (①)

```bash
# 개발 기계 · 레포 루트(작업 트리 깨끗) · 접속값은 ~/.config/colab-platform/dev-operator.env 에서
# ⛔ COLAB_DEV_SECRETS_DIR 는 unset 한 채로 넘긴다 (한 이름 두 뜻 · SKILL.md:101-106)
COLAB_REF_ROOT='<체크아웃과 나란한 03 Reference-Data>' \
COLAB_DEV_SSH=<…> COLAB_DEV_KEY_FILE=<…> COLAB_DEV_WEB_URL=<dev 주소> \
COLAB_RESEED_TARGET_REF=ea21d8c2aa54 \
bash dev-package/tools/dev-reseed/reseed.sh --from reset \
     --run-dir dev-package/reports/dev-reseed-runs/<시각>
```

- `--release-plan` **불요**(deploy 단계가 없다). `preflight` 는 `--from` 과 무관하게 언제나 먼저 돈다(`reseed.sh:196-217`).
- 도는 단계 **9** = `preflight → reset → bootstrap → up → s3 → prelude → seed → verify → report`.

| 단계 | dev 에 무엇을 하나 |
|---|---|
| `preflight` | 읽기만. 11항목 재판정 ＋ 대상 sha 해석 |
| `reset` | **유일한 파괴 단계.** 앱 4종 정지(①′) → 두 스키마 DROP·CREATE(②) → S3 계획 적용. 실행 **전에** `approval-record.json` 이 실행 자리에 선다 |
| `bootstrap` | `db-bootstrap.sh`(확장·앱 권한·account-admin) ＋ 두 체인 `alembic upgrade`(AI 사전 103행이 여기서 되돌아온다) |
| `up` | 같은 compose·env 로 앱 4종 기동 |
| `s3` | 계획 검토 ＋ 적용 — 접두사 `uploads/`·`previews/` 밖은 손대지 않는다 |
| `prelude` | 연구실·교수 계정 SQL 선행 4단계(DB 직접 쓰기가 허용된 유일한 자리) |
| `seed` | **화면(UI) 경로로 28건 등재 ＋ 업로드 3.64 GB ＋ 계보 18간선.** 자동 메타는 이 업로드 분석에서만 들어온다 |
| `verify` | 계수(28·4·18·「미지정」0·미연결 0) ＋ 미리보기 순회 ＋ `deploy_doctor` 15/15 |
| `report` | `result.json` ＋ 회차 기록 `dev-package/sessions/DR-4-run-<시각>.md` (바꾸는 단계가 돌았으므로 **레포에 남는다**) |

## 6. 무엇이 부서지나 (②)

- **플랫폼·AI 두 스키마 DROP·CREATE** — `services/core-api/ops/reset_dev_environment.py` 머리말 ⑵.
- **AI 사전 손실 0** — dev 의 103행(`d9_concept` 49 · `d9_concept_edge` 19 · `d9_method_term` 13 ·
  `d9_place_alias` 4 · `d9_topic_synonym` 18)은 전부 마이그레이션 시드이고, WU0 이 **키 수준 집합 차분**으로
  손실 0 을 증명했다(`wu0-precheck-2026-09-24.md §1`). 손으로 넣은 행 0.
- **S3 = `uploads/` · `previews/` 접두사 1,778 키**(멀티파트 0 · 계획 sha256 `2de0ac82…` · 이번 리허설 실측).
  `_ops/` 무접촉. staging·product 무접촉.
- 플랫폼 DB 는 **이미 비어 있다**(데이터셋 0 · 계정 0 · 연구실 1 · 자동메타 0 · 계보 0 — WU0 §2-1).
  ⇒ 실제로 사라지는 제품 자료는 **S3 객체 1,778건과 연구실 1행**이고, 그 위의 고정 ID 는 이미 죽어 있다.

## 7. 중간에 무엇이 잘못될 수 있나 · 어떻게 잇나 (③ · DR-4 §9·§11)

- **자동 재시도는 없다**(SKILL.md:142). 한 단계가 비영 종료하면 그 자리에서 멈추고 `--from <단계>` 로만 잇는다.
- `reset` 이 앱을 정지(①′)한 **뒤** 실패하면 도구가 같은 compose·env 로 되살린다 — `result.json` 의 `recovery`.
  정지는 되돌릴 수 없는 걸음(② DROP) **직전**에만 내린다.
- **첫 무인 완주다** — DR-4 §9 축자 「`reseed.sh` 전 10단계를 한 프로세스로 밟은 회차는 **아직 없다**」.
  이번은 9단계(deploy 제외)를 한 프로세스로 밟는 첫 시도다.
- ⛔ **DR-4 §11 진입조건 1 은 미충족이다** — 도구 결함 2건이 그대로다.
  ㉮ §7-2 `project_index()` 앵커 의존 — 목록이 `onClick` 이동이라 앵커 0 이고, **id 없이 `status: done`** 을 적는다(green-by-skip).
  ㉯ §8-1 미리보기 순회기 대기 조건 — `dataset-preview` 등장 직후 세어 gpkg 2행을 「성립」으로 잘못 읽는다.
  intent 가 「선행 조건으로 다루되 이 intent 가 고치지 않는다」로 둔 항목이라 **risk 를 안고 들어간다.**
  판정에서는 `previewJudgment[]` 의 **「판정불가」를 통과로 세지 않는다**(SKILL.md:128).
- **소요는 여전히 [미확인]**. 참고치 = 등재 28건 × 21~23초 ＋ 업로드 3.64 GB ＋ verify ≈ 200초.
  리허설은 원격 왕복이 1~2초임을 보였을 뿐 등재·업로드 속도를 재지 않았다.
- 멈추면 마지막 줄이 단계 이름과 로그 경로를 낸다. **같은 자리에서 두 번 죽으면 잇지 말고 멈춘다.**
- intent 미해결 5 는 도구가 막아 주지 않는다 — **재생성 시각에 dev 를 쓰는 사람이 없는지 사람이 확인한다.**

## 8. go / no-go 권고 (⑤)

**조건부 go.** 순서를 지킨다 —

1. **㉮ `/opt/colab-repo` 트리 갱신 · ㉯ dev 백업 1회** → `doctor` 가 `항목 15 — ✓ 15 · ✗ 0 · ─ 0` 인지 **눈으로 확인**.
   이 둘 전에는 WU2 의 `verify` 가 **반드시** red 다(§4).
2. `reseed.sh --preflight-only` 재실행 → 11/11 재확인(디스크가 다시 2 GiB 밑으로 내려갔는지 포함).
3. dev 를 쓰는 다른 레인이 없는지 사람이 확인(intent 미해결 5).
4. 그다음 §5 의 명령 한 줄. **`--from reset`** 이고 `--release-plan` 은 주지 않는다.

**반대 관점(같이 올린다)** — DR-4 §11-1 이 「도구 결함 2건을 먼저 고치고 `dev-reseed-selftest` 에 red→green
픽스처를 단 뒤에 무인 완주」를 다음 회차 진입조건으로 못 박았고, 그 조건은 **지금도 미충족**이다.
자동 메타를 얻는 것이 목적이라 등재·업로드가 성립하면 목적은 달성되지만, `seed` 의 green-by-skip 은
**프로젝트 미연결을 0 으로 잘못 보고할 수 있다.** 보수적으로 가려면 `seed`·`verify` 를 **사람이 지켜보는 창**에서
돌리고, `result.json` 의 `counts.프로젝트 미연결` 을 화면에서 한 번 더 대조한다.

**no-go 를 부르는 신호** — preflight 미달 1건 이상 · EC2 디스크 여유 < 2 GiB 재발 ·
`leftovers` 검출 · dev 를 쓰는 다른 세션 존재 · ㉮㉯ 뒤에도 doctor 가 15/15 가 아님.

## 9. 파일 · 증거

| 자리 | 무엇 |
|---|---|
| `dev-package/reports/corpus-expansion/wu1-rehearsal-2026-09-24.md` | 이 문서(게이트 ③ 패킷) |
| `dev-package/reports/corpus-expansion/wu1-rehearsal-log-2026-09-24.txt` | preflight·리허설 발췌 ＋ 원격 읽기 실측 |
| `dev-package/reports/dev-reseed-runs/wu1-rehearse/` | 실행 자리 전문(`result.json`·단계 로그) — **추적 제외** |
| `dev-package/reports/dev-reseed-runs/wu1-pf-devsha/` | `--preflight-only` 회차(11/11) — 추적 제외 |
| `dev-package/reports/dev-reseed-runs/wu1-release/{plan.json,pre.json}` | 리허설이 요구한 `--release-plan` 입력 — **추적 제외**(DR-2-runbook §1-1 과 같은 취급: 계획은 레포에 커밋하지 않는다) |
| `dev-package/reports/dev-reseed-runs/wu1-ci-bundle/` | Actions run `35338885223` 의 producer 산출물·`ci-evidence.json` 원본(다운로드본) — 추적 제외 |
| `dev-package/reports/dev-reseed-runs/wu1-make-release-input.py` | 위 둘을 **실제 GitHub 사실로만** 조립한 생성기 — 추적 제외 |

- `pre.json` 의 재료는 전부 실물이다 — PR #123 의 `merged`·`base`·`merge_commit_sha`(GitHub API) ＋
  run `35338885223` 의 `ci-evidence.json`·producer 번들. `release_evidence.py pre` 가 독립으로 통과(exit 0).
- 그 계획의 `deploy`·`verify` 명령은 **exit 78 로 거부하는 한 줄**이다 — 배포 패킷이 아니고, WU2 는 그 단계를 돌지 않는다.
  실제 배포가 필요해지면 DR-2-runbook §1-1 의 회차별 패킷을 따로 만든다.
