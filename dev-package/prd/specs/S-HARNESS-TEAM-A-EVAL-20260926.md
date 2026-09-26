# Spec: 하네스 개선 — 소형 PR A (팀 공용 · eval 회차의 모델 고정 · 해시 집합 축소 · UTC run id · 78 상세 · 위생 뿌리)
출처 intent: `dev-package/intent/2026-09-25-harness-improvement.md`
출처 절: 10라운드 판정(`:627` · Ted 원문 "pr은 사람이 승인하기만 하면된다 꼭 / 팀에 맥이나 비 wsl호스트가 있음 다른사람일필욘없다 / 나머진 전브 권고로" · 「권고 2–12 전부 수용」 · **소형 PR A** 항목 · Q2 예) · 8라운드 ①(`:618` · `hash_exclude` 명시 목록 허용). 근거(저장소 밖 · PR B 가 반입): `~/.claude/reports/harness-state-20260925/team-shared-20260926/report.md` 판정 ①②·권고 2·3·4·5·충돌·미확인(run id 접미사 · 모델 출처 · 해시 집합 축소 · 실측 모델) · `audit-mechanisms.md` E-1·E-6·E-7 · `audit-process-docs.md` D3·D4·D11 · `audit-cost-concurrency.md` C-1·C-2·C-4·C-11. 총괄 = `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md` §10 행 5a(`:224`) · 10.1 팀 원칙 · T 번호는 총괄 Ted 행동표(T12 실측 · T16 게시 · T13 병합 · T11 재판정은 A·B 뒤).
순서: S-red 병합 뒤 착수 · PR 2 회차 앞 병합 · PR B 와 동시 open 가능(우려 #2 순서 조건) · 회차 1회로 끝낸다(총괄 §10 행 5a). 줄 번호 기준 = develop `5bb3d6fe`(E0 #176 병합 · 2026-09-26 재열람) — S-red 병합이 `run.sh` · `config_hash.py` · `harness-eval.sh` · `config-paths.txt`(S-6a–d)를 옮기므로 레인은 착수 시 재열람한다. 트레일러 규칙 = E0 와 같다(마지막 문단 하나 · `intent-ref` 판정 경로 `eval/harness/**` · `dev-package/**` · `.agents/**` · `gates/**` 안). 훅 정의(`.claude/settings.json` · `.codex/hooks.json`) 무변경 → `/hooks` 재신뢰 0 · 새 ADR 없음(ADR-0011 = PR 2 · ADR-0012 = PR 4 예약 유지).
단위 규칙 = E0 spec 머리와 같다(⑴ 강제 기제 ⑵ 시험 ⑶ 병합 조건 ⑷ 지우는 산문 ⑸ 소유 PR = A · 장치 없는 단위는 「산문 · 맥락만」). 팀 원칙(총괄 §10.1) = 단위마다 「다른 팀원이 다른 머신(OS · 시간대 · 홈 · clone)에서 같은 절차 → 같은 판정 · 같은 보호 · 같은 비용」을 §4 각 단위 끝에 1줄로 답한다.

## 0. 출처 · 순서
- 결정 정본 = intent `:627` 소형 PR A 5항목: ⑴ 모델 정본 `eval/harness/model.txt` + 러너 `--model` + `compute` 에 `model`(정본 + 실측 `modelUsage`) + `verify` 모델 대조(불일치 78 `model-mismatch`) + 요약줄 모델 표기 ⑵ 해시 집합 축소(Q2) ⑶ run id UTC(`date -u` · 접미사 없음 · 정규식 불변) + `check.py` 나이 UTC + README 「id = UTC」 1줄 ⑷ `verify` 78 상세에 dirty(비추적 포함) 상위 5건 ⑸ `harness.yaml hygiene.home_path_roots` += `eval/harness/results` · `dev-package/intent` · `dev-package/prd`.
- 축소 범위의 정본 = 권고 3(`gates/**` · `.agents/ci-producers.json` 제외 후 `gates/tools/harness-eval.sh` · `harness-eval-selftest.sh` · `_readiness.sh` 재등재) = 총괄 §10 `:224` · `:232`(S-dep 회차 0 의 전제). intent `:627` Q2 문장은 `gates/**` 만 적는다 → 우려 #3.
- 이 PR 뒤 첫 회차가 새 기준선(intent `:627` 끝 · 총괄 `:224`). 직전 회차 `20260926-143218`(해시 `5b84d899` · 실측 모델 `claude-opus-5-5[1m]` · `H01.raw.1.json` `modelUsage.canonicalModel` = `claude-opus-5-5`)은 모델이 다르므로 회귀 기준이 아니라 참고값이다(§4.1 「직전」 조건).

## 1. 문제 진술
- 판정 모델이 실행자 기본값이다: `eval/harness/run.sh:136-142` `claude -p` 에 `--model` 없음 · `config_hash.py compute` 기록 필드(`:144-154`)에 모델 없음 · `verify`(`:193-208`)는 hash · selected · 준비 0 · 과제 수만 대조 · `README.md:108` 「러너는 모델을 지정하지 않으므로 호출 환경의 기본값을 탄다」. 실측: `results/20260926-143218/config-hash.json` 은 `claude_version 2.1.283` 만 있고 raw(gitignored)의 `modelUsage` 키는 `claude-opus-5-5[1m]` · README 는 `claude-fable-5-1`. 같은 해시 · 다른 모델 · 다른 판정(09-12 회차 31.55 USD vs 09-26 8.11 USD).
- 해시 집합의 63% 가 제품 게이트다: `config-paths.txt:13` `gates/**` · `:12` `.agents/**`(`.agents/ci-producers.json` 포함) → 제품 PR(#175 등)이 하네스 PR 회차를 78 로 되돌린다(E0 가 재실측 2회 · C-1). eval 과제는 `gates/tools/*.py` 를 입력으로 받지 않는다(`run.sh:135-142` cwd = fixture).
- run id 가 실행자 로컬 시계다: `run.sh:76` `date +%Y%m%d-%H%M%S` · `check.py:96,110,120` naive `strptime` vs `datetime.now()` · `:107-109` 주석이 KST 를 전제 · 「직전」 선정(`config_hash.py:214-220`)이 id 사전순 = 시간순을 전제 → 시간대가 다른 구성원 회차가 역전된다(#176 CI red 가 첫 사례).
- 78 이 원인을 안 찍는다: `verify` 후보 0건 detail(`:209-212`)은 「해시 일치 회차 0건」만 · `compute` 의 `dirty`(`:116-129` · 비추적 포함)는 계산되고 버려진다 → 구성원 기계의 임시 파일 1건이 「게이트가 깨졌다」로 보고된다(C-11).
- 위생 뿌리 밖: `.agents/harness.yaml:100` `home_path_roots` 에 `eval/harness/results` · `dev-package/**` 없음 → 추적 증거 `results/20260926-{125205,140939,143218}/H02.out.{1,2}.txt`(6줄)에 실행자 홈 절대경로가 실려 있고(`git ls-files` 추적 · 이 문서 작성 시 grep 실측) 게이트가 못 잡는다(E-6). `dev-package/prd` 에도 레거시 4줄(`specs/stage3-login-hardening.md:7` · `rounds/R-STAGE3-LOGIN-HARDENING.md:14` · `rounds/R-SELECTED-PREVIEW-TIMING.md:55` · `rounds/R-SELECTED-PREVIEW-TIMING-PR.md:23`) · `dev-package/intent` 0건(`<u>` 표기는 `config.py:29-34` 정규식에 안 걸림).

## 2. 원한 결과 (V-id)
- V-A1 러너가 `eval/harness/model.txt`(1줄 · 해시 집합 안)를 읽어 `claude -p --model <값>` 으로 호출하고, 정본 부재·빈 값이면 78(기본 모델로 재지 않는다) · `config-hash.json` 에 `model`(정본) · `model_usage`(실측 `canonicalModel` 정렬 목록) · `summary.md` 요약줄 끝에 ` · 모델 <정본>` · 별도 줄 `- 모델 — 정본 <값> · 실측 <목록>` — 확인: `eval/harness/tests/run-selftest.sh` 새 케이스 ⓝ·ⓞ·ⓟ.
- V-A2 `verify` 후보 조건 += `model == 정본 ∧ 정본 ∈ model_usage` · 위반 = 후보 제외 · 사유 문자열 `model-mismatch` · 「직전」 후보도 `model == 정본` 인 회차만(다른 모델 회차는 「참고」로 출력 · 회귀 비교 생략) — 확인: `scripts/tests/test_harness_eval_gate.py` VerifyTests 새 케이스 ⓐ–ⓓ · `gates/tools/harness-eval-selftest.sh` 새 케이스 ⓢ.
- V-A3 해시 집합 = `AGENTS.md` · `CLAUDE.md` · `.claude/**` · `.agents/**`(`ci-producers.json` 제외) · `scripts/harness/hooks/**` · `eval/harness/**`(`results/**` 제외) · `gates/tools/harness-eval.sh` · `gates/tools/harness-eval-selftest.sh` · `gates/tools/_readiness.sh` — `gates/x.sh` · `gates/run.sh` · `.agents/ci-producers.json` 변경 = 같은 해시 · `gates/tools/_readiness.sh` 변경 = 다른 해시 — 확인: `test_harness_eval_gate.py` ConfigHashTests 갱신 + 새 케이스 · `harness-eval-selftest.sh` ⓠ fixture 교체 · `test_ci_eval_policy.py` 새 변이.
- V-A4 CI `harness` 필터 == 정본 포함 패턴 ∪ FILTER_ONLY(`.codex/**` · `scripts/harness/**` · `scripts/agent-bridge.py` · `gates/**`) 축자 일치 · `gates/**` 는 필터 전용(면제 게이트·셀프테스트만 깨움 · 모델 호출 0) — 확인: `ci-filter-check.py` ㈏·㈖ green · `test_ci_eval_policy.py:47-55` 기존 단언 유지.
- V-A5 `RUN_ID` = `date -u +%Y%m%d-%H%M%S`(형식 · `RUN_ID_RE` `config_hash.py:36` · `check.py:83` 불변) · `check.py` 나이 = aware UTC 양쪽 · README 「결과」 절 「id = UTC」 1줄 — 확인: FreshnessTests 갱신 + run-selftest ⓠ.
- V-A6 `verify` 후보 0건 78 detail 끝에 ` · dirty N건: <경로 ≤5>[ …]` — 확인: VerifyTests 새 케이스 ⓔ · `harness-eval-selftest.sh` ⓠ 출력 단언.
- V-A7 `harness.yaml hygiene.home_path_roots` 9개 · 현 트리 홈 경로 0건(results 6줄 `<repo>` · prd 4줄 `~/` 치환) · `harness-contract` green(green 줄 `home-path roots 9`) — 확인: 게이트 red→green 로그 · `test_harness_config.py:204-228` fixture 에 roots 반영.
- V-A8 `harness-eval` 면제 게이트 green(PR A head 회차 · 정본 모델 · `hash(head)=hash(회차)`) · 회차 뒤 집합 파일 push 0 · 회차 = 새 기준선(직전 없음 · 참고 `20260926-143218`).
- V-A9 문서: `README.md:108`(「호출 환경의 기본값」) · `:150-151`(집합 목록) · `:164`(「러너는 모델을 지정하지 않아」) · `check.py:79-81` 주석 · `gates/README.md:48`(「필터 전용 3줄」) · `:295`(건수) 가 현 동작으로 교체 · 옛 문장 0건.
- V-A10 Codex 영향 없음: `scripts/agent-bridge.py` · `.codex/**` · `scripts/codex-harness-eval.py` diff 0 · `agent-bridge check` green.

## 3. 해법 개요
- 파일: `eval/harness/model.txt`(신설) · `run.sh`(정본 읽기 · `--model` · `record-usage` 호출 · 요약줄 · `date -u`) · `config_hash.py`(`compute --model` · `record-usage` 하위 명령 · `verify` 모델 조건 · 직전 모델 조건 · dirty 상세) · `config-paths.txt`(집합) · `gates/tools/harness-eval.sh:79`(요약 정규식) · `ci-filter-check.py:44`(FILTER_ONLY) · `.github/workflows/ci.yml:123-134`(필터 3줄) · `scripts/harness/check.py`(UTC) · `.agents/harness.yaml:100`(뿌리 3개) · 증거·레거시 10줄 치환 · 시험 4벌 · 문서 3곳. 훅 정의 · 등록부(`.agents/ci-producers.json` 내용) · `parallelism.toml` 무변경.
- 경계: 「직전」의 조상 조건(`merge-base --is-ancestor`)은 PR 2(권고 7) · 여기서는 모델 조건만 더한다(같은 함수 · PR 2 가 위에 얹는다). `claude_version` 대조(D3 제안)는 10라운드 확정 목록 밖 → 범위 밖. S-6a 의 `$HOME` 치환은 S-red 리뷰 항목(C-9) · 이 PR 은 기존 증거만 치환한다.

## 4. 구현 결정

### 4.1 모델 정본 · 러너 · 기록 · 대조 (단위 A-1)
- `eval/harness/model.txt`: 모델 id 1줄 · 주석 없음 · 끝 줄바꿈 1 · 값 = 우려 #1 판정(권고 `claude-fable-5-1`). `eval/harness/**` 라 집합 안 → 값 변경 = 재실측(의도).
- `run.sh`: `:34` 뒤 `MODEL_FILE="${COLAB_EVAL_MODEL_FILE:-$HARNESS_DIR/model.txt}"`(시험 seam · `:23-26` 목록에 1줄 · 판정을 무르게 하는 값이 아니라 자리) · `:57` 뒤 `[ -s "$MODEL_FILE" ] || ready_red "$MODEL_FILE" "모델 정본이 없다 — 호출 환경의 기본 모델로 재지 않는다(팀 원칙)"` · `MODEL="$(head -1 "$MODEL_FILE" | tr -d '[:space:]')"` · 빈 값 → 같은 78 · `:85-86` compute 에 `--model "$MODEL"` · `:136-142` 호출에 `--model "$MODEL"` · `:252` 루프 뒤 `USAGE="$(python3 "$HARNESS_DIR/config_hash.py" record-usage --run "$OUT")" || ready_red "$OUT/config-hash.json" "실측 모델을 기록하지 못했다"` · `:273` SUMMARY 끝에 ` · 모델 $MODEL` · `:278` 뒤 `- 모델 — 정본 \`$MODEL\` · 실측 \`${USAGE:-[없음]}\``. `:88-90` HASH_LINE 은 불변(선례 정규식 `run-selftest.sh:161` 앵커).
- `config_hash.py` 세 자리:
  - `compute(root, selected, claude_version, model="")` → 필드 `model`(정본 문자열 · `:144-154` 뒤에 추가) · `main()` `compute --model`(기본 "" · 셀프테스트 fixture 호출 호환).
  - 새 하위 명령 `record-usage --run <dir>`: `<dir>/*.raw.*.json` 각각 `modelUsage` 항목의 `canonicalModel`(없으면 키에서 `[…]` 접미 제거 · `H01.raw.1.json` 실측 필드 `canonicalModel: claude-opus-5-5` · 키 `claude-opus-5-5[1m]`) → 정렬 유일 목록 → `<dir>/config-hash.json` 에 `model_usage` 기록(in place · 다른 필드 불변) · stdout = 쉼표 목록 · raw 0건 = 빈 목록(러너는 판정하지 않는다 · verify 가 판정 · 우려 #6) · JSON 못 읽음·쓰기 실패 = 78.
  - `verify`: 정본 = `root/eval/harness/model.txt`(부재·빈 값 = 78 「모델 정본 없음」) · 후보 루프(`:196-208`)에 `data.get("model") != 정본 or 정본 not in data.get("model_usage", [])` → `rejected.append(f"{run.name}: model-mismatch 정본 {정본} · 회차 {data.get('model') or '-'}/{','.join(usage) or '-'}")` · 「직전」 루프(`:215-220`)에 `meta.get(run.name, {}).get("model") == 정본` 조건(해시 없는 옛 결과 · model 없는 결과 = 제외 · 제외된 최신 전수 회차는 detail 에 `참고(다른 모델) <id> green N/M` 로 1회 출력 · 회귀 비교 생략). SCHEMA 문자열 유지(필드 추가 · 옛 회차는 해시가 달라 후보 밖).
- 요약 정규식 3곳: `harness-eval.sh:79` 끝 `판정실패 관측 과제 0$` → `판정실패 관측 과제 0 · 모델 [^[:cntrl:]]+$` · `harness-eval-selftest.sh:198,201` 같은 갱신 · `config_hash.py:37-38` SUMMARY_RE 는 앞부분만 읽으므로 불변 · `run-selftest.sh:130,185` grep 은 접두 대조라 불변.
- 강제 기제: 러너 78(fail-closed · 정본 없이 실행 0) · 게이트 `verify` 78(`model-mismatch` · 다른 모델 회차는 면제 근거 불가) · Claude/Codex 공통(`gates/tools/harness-eval.sh` 가 같은 러너 · `scripts/codex-harness-eval.py` 는 범위 밖).
- 시험(실행 게이트 = `harness-contract-selftest` `gates/run.sh:357` · `harness-eval-selftest` `:535`):
  - `eval/harness/tests/run-selftest.sh` — 스텁(`:42-68`)이 argv 를 `$STUB_ARGS` 에 기록하고 green 응답에 `"modelUsage":{"stub-model":{"canonicalModel":"stub-model"}}` 를 포함.
    - ⓝ `COLAB_EVAL_MODEL_FILE=<파일: stub-model>` 로 ⓔ 실행 → argv 에 `--model stub-model` · `config-hash.json.model == "stub-model"` · `model_usage == ["stub-model"]` · 요약줄 끝 ` · 모델 stub-model` · summary.md 「- 모델 —」 줄.
    - ⓞ `COLAB_EVAL_MODEL_FILE=<부재>` → 78 + 사유에 「모델 정본」 · ⓟ 빈 파일 → 78(같은 사유).
  - `scripts/tests/test_harness_eval_gate.py` — FixtureRepo(`:31-51`)에 `eval/harness/model.txt` = `stub-model` · `write_result(:173-190)` 에 `model` · `model_usage` 인자 · 기존 VerifyTests 는 정본 값으로 통과 유지.
    - ⓐ compute 가 `model` 필드를 쓴다(`--model` 없으면 "") · `record-usage` CLI 가 raw 2건(`canonicalModel` 있음/없음 · `[1m]` 접미 키)에서 정렬 유일 목록을 쓰고 다른 필드를 보존한다.
    - ⓑ 해시 일치 · `model` 다름 → 78 + detail 에 `model-mismatch` · ⓒ `model` 같고 `model_usage` 에 정본 없음 → 78.
    - ⓓ 직전이 다른 모델(3/3 green) · 일치 결과 2/3 → 0 + 「직전 없음」 + `참고(다른 모델) <id>`(회귀 아님) · 직전이 같은 모델이면 기존 회귀 규칙 그대로(`:221-227` 케이스 유지).
  - `gates/tools/harness-eval-selftest.sh` — CFG(`:86-91`)에 `eval/harness/model.txt` · `write_result(:93-109)` 가 `--model` 을 넘기고 `model_usage` 를 쓴다.
    - ⓢ `res-cfg_model`(해시 일치 · model 다름) → 78 + `missing=eval-result:<hash>` + 출력에 `model-mismatch`(`:170-176` 78 검사 목록에 추가).
- 병합 조건 = 위 시험 green ∧ V-A8 · 지우는 산문 = `README.md:108` 모델 행 → 「정본 `model.txt` · 러너 `--model` · 실측은 `config-hash.json.model_usage`」 · `:164` 「러너는 모델을 지정하지 않아 …」 → 「모델은 정본 고정 · CLI 버전은 저장소 밖」 · `check.py:79-81` 주석 동일 취지 · 출처 = 권고 2 · E-1 · C-2 · D3.
- 팀 원칙: 판정 = 저장소 파일이 모델을 정하고 게이트가 대조(같은 판정) · 보호 = 다른 모델 회차는 면제 근거 불가(같은 보호) · 비용 = 모델이 정본이라 회차 비용이 구성원 무관(같은 비용 · 액수는 우려 #1).

### 4.2 해시 집합 축소 · CI 필터 정합 (단위 A-2)
- git pathspec 실측(이 문서 작성 시 · `git ls-files -- ':(glob)gates/tools/harness-eval.sh' ':(exclude,glob)gates/**'` 와 역순 모두 0건 · 명시 3줄 + `eval/harness/**` + `:(exclude)eval/harness/results/**` 는 3 + 112건): exclude 는 순서와 무관하게 이긴다 → 「`:(exclude)gates/**` 뒤 재포함」 꼴은 성립하지 않는다. 정본은 **명시 열거**로 쓴다.
- `config-paths.txt`: `:13` `gates/**` 삭제 → `gates/tools/harness-eval.sh` · `gates/tools/harness-eval-selftest.sh` · `gates/tools/_readiness.sh` 3줄 · `:(exclude).agents/ci-producers.json` 1줄(단일 파일 exclude 는 pathspec 으로 성립 · `.agents/**` 안) · 머리말 `:5-8` 근거에 「10라운드 Q2 · 권고 3 · exclude 는 재포함 불가라 명시 열거」 1줄 · S-6c 주석은 유지.
- `ci-filter-check.py:44` `FILTER_ONLY` += `gates/**`(필터 전용 · 머리말 `:12-13` 문구 「FILTER_ONLY(해시 밖 · 필터 안)」 그대로 · `MUST_MATCH:55` `gates/run.sh` 유지) · `.github/workflows/ci.yml:123-134` `harness` 필터에 3줄 추가(`gates/**` 유지 · ㈏ 축자 일치 `:157-162` · ㈖ `:165-168`). 잡 `harness-eval`(`ci.yml:684-703`)은 면제 모드라 `gates/**` 변경의 추가 비용 0.
- 강제 기제: `config_hash.py` 계산(장치) · `ci-filter-check`(㈏·㈖ 판정 · `harness-eval-selftest.sh:250-259` 경유) · fail-closed(정본·필터 불일치 = 1).
- 시험(red-first):
  - `test_harness_eval_gate.py:143-151` 기대 목록 갱신 — `gates/**` 부재 · 명시 3줄 존재 · `:(exclude).agents/ci-producers.json` 존재 · `include_patterns` 에 exclude 없음.
  - FixtureRepo 에 `gates/tools/_readiness.sh` · `.agents/ci-producers.json` 추가 · `:76` `files` 수 재산정(레인이 실계수 기록) · `:78-84` `test_2_byte_change` 대상 → `gates/tools/_readiness.sh`.
  - 새 ⓕ `gates/x.sh` · `gates/run.sh` · `.agents/ci-producers.json` 변경 = 같은 해시 · `dirty` 에도 없음(집합 밖 pathspec).
  - `harness-eval-selftest.sh:91,132` ⓠ fixture `gates/x.sh` → `gates/tools/harness-eval.sh`(CFG 에 그 경로 생성 · 현 ⓠ 는 집합 축소 순간 red 가 되므로 같은 커밋에서 교체).
  - `test_ci_eval_policy.py` 새 변이 「필터에서 `gates/tools/_readiness.sh` 제거 → 1」 · `:47-55` 기존 단언(`gates/**` 포함) 유지 · `harness-eval-selftest.sh:263-267` 기준 7 → 8.
- 병합 조건 = 위 시험 green ∧ `ci-filter-check` green ∧ V-A8 · 지우는 산문 = `README.md:150-151` 집합 목록 · `gates/README.md:48` 「필터 전용 3줄」 → 4줄 · 출처 = 권고 3 · C-1 · 총괄 `:224` · `:232`.
- 팀 원칙: 제품 병합이 하네스 회차를 무효화하지 않는다(같은 비용 · 무효화율 ≈5.7/일 → 하네스 PR 몫만).

### 4.3 UTC run id · 신선도 (단위 A-3)
- `run.sh:75-76` `RUN_ID="$(date -u +%Y%m%d-%H%M%S)"` · 주석 「UTC · 접미사 없음 · `RUN_ID_RE` 불변 · 기존 8회차 정렬 호환」(충돌·미확인 ① 채택).
- `check.py:96` `stamp = dt.datetime.strptime(...).replace(tzinfo=dt.timezone.utc)` · `:104-110` `eval_age_days`: `now or dt.datetime.now(dt.timezone.utc)` · docstring 교체 「run id 는 UTC(`date -u`) · now 도 UTC · `max(0, …)` 은 기계 시계 skew 만 흡수」 · `:120` 동일 · `:79-81` 주석 「모델은 `model.txt` 고정 · CLI 버전은 저장소 밖이라 시간 신호 유지」.
- `README.md` 「결과」 절 `:125` 뒤 1줄 「회차 id 는 **UTC**(`date -u`) — 시간대가 다른 실행자의 회차도 이름순 = 시간순」.
- 강제 기제: 러너(장치 · 실행자 시간대 무관) · `harness-contract` 신선도(장치) · fail-closed 아님(경고 · 정렬 규약).
- 시험:
  - FreshnessTests `:324-368` — `now` 를 aware UTC 로 · `:361-368` 케이스를 「skew 1h → 0 · 23h → 0 · 3d1h → 3」 으로 개명(KST 전제 삭제) · 새: naive `now` 전달 → `TypeError`(aware 강제 · 조용한 혼용 금지) · `:352-359` green 줄 정규식 유지.
  - `run-selftest.sh` ⓠ — ⓔ 실행 전후 `date -u +%Y%m%d` 두 값 중 하나가 결과 디렉터리 이름 앞 8자와 같다 · `TZ=Pacific/Kiritimati`(UTC+14 · 날짜가 갈리기 쉬운 값)로 재실행해도 같다(로컬 시계 무영향).
- 병합 조건 = 위 시험 green · 지우는 산문 = `check.py:107-109` KST 주석 · 출처 = 권고 4 · E-7 · D11 · C-4 ①.
- 팀 원칙: 회차 순서·30일 경고가 시간대와 무관(같은 판정).

### 4.4 `verify` 78 상세 dirty (단위 A-4)
- `config_hash.py:172-175` `current_meta = compute(root)` 보관 · `:209-212` 후보 0건 detail 끝에 ` · dirty {n}건: {', '.join(dirty[:5])}{' …' if n > 5}`(0건 = `dirty 0건`) · `dirty` = `:116-129`(`--untracked-files=all` · 비추적 포함 기존). 다른 78 갈래(손상 · 뿌리 없음)는 불변.
- 강제 기제: 출력(진단) · 판정 불변 · `harness-eval.sh:105` `$detail` 경유로 게이트 출력에 실린다.
- 시험: VerifyTests 새 ⓔ 집합 안 비추적 `scripts/harness/hooks/tmp.sh` 1건 → 78 + detail 에 경로 · 6건 → 5개 + ` …`. `harness-eval-selftest.sh` ⓠ 출력에 `dirty 1건: gates/tools/harness-eval.sh` 단언.
- 병합 조건 = 시험 green · 지우는 산문 = 없음 · 출처 = 권고 5 · C-11.
- 팀 원칙: 구성원 기계의 임시 파일이 원인으로 이름 붙는다(같은 판정 · 진단 동일).

### 4.5 위생 뿌리 · 기존 증거 치환 (단위 A-5)
- `.agents/harness.yaml:100` `home_path_roots` += `eval/harness/results` · `dev-package/intent` · `dev-package/prd`(9개). 검사 = `config.py:271-323`(`git ls-files --cached --others --exclude-standard -- <roots>` · raw/err 는 `results/.gitignore` 로 제외 · 정규식 `:29-34` · allow 는 exact match `:318`).
- 뿌리만 더하면 `harness-contract` 는 red(판정) 10건이다(§1 실측). 처리 ⓐ = 치환(채택): results 6줄의 `<checkout 절대경로>` → `<repo>`(S-6a 와 같은 토큰 · `results/**` 는 집합 밖이라 회차 무관 · 모델 응답 본문의 의미 불변 · 커밋 메시지에 치환 명령 원문) · prd 4줄의 홈 접두 → `~/`(레거시 문서 · 승인 intent 아님 → append-only 대상 아님 · `Evidence-Ref:` 행은 값만) · `dev-package/intent` 는 0건이라 편집 0. ⓑ = `home_path_allow` 에 실행자 홈 등재 → 홈 경로가 `harness.yaml` 에 실린다 → 기각(우려 #7).
- 강제 기제: `harness-contract`(장치 · fail-closed · red(판정) 1) · Claude/Codex 공통.
- 시험:
  - red-first = 뿌리 추가 상태에서 `bash gates/run.sh harness-contract` → red(판정) 10건 로그(레인 보고 인용 · 경로:줄 10개) → 치환 → green(`home-path roots 9 (scanned N …)`). 로그와 치환은 같은 커밋 ⑤(중간 red 커밋을 남기지 않는다 · 로그는 본문에).
  - `test_harness_config.py:204-228` fixture(`gates/fixtures/harness-contract/home-paths.md` 대조)에 뿌리 3개 반영 · `docs/leak.md` 꼴로 `eval/harness/results/x/H01.out.1.txt` · `dev-package/prd/x.md` 각 1건 추가(뿌리 밖 `dev-package/reports/x.md` 는 안 잡힘 단언 · 우려 #4 경계).
  - `grep -rnE '/home/[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/' eval/harness/results dev-package/intent dev-package/prd` = 0(치환 뒤 · V-A7).
- 병합 조건 = 게이트 green ∧ 치환 diff 가 홈 경로 10줄뿐(`git diff --stat` 10 파일) · 지우는 산문 = 없음 · 출처 = 권고 5 · E-6 · D4.
- 팀 원칙: 어느 구성원의 홈도 증거·계획 문서에 남지 않는다(같은 보호 · diff 동일).

## 5. 시험 결정 (TDD red-first 순서)
1. `test_harness_eval_gate.py` 갱신·추가(A-2 ⓕ · 목록 기대 · A-1 ⓐ–ⓓ · A-4 ⓔ) → `bash gates/run.sh harness-contract-selftest` RED(`compute()` `model` 인자 없음 · `gates/x.sh` 가 해시를 바꿈 · `model-mismatch` 없음 · dirty 없음).
2. `run-selftest.sh` ⓝ·ⓞ·ⓟ·ⓠ · `harness-eval-selftest.sh` ⓢ + ⓠ 단언 + 기준 8 · `test_ci_eval_policy.py` 변이 → `bash gates/run.sh harness-eval-selftest` RED.
3. 커밋 ①(A-2) → ⓕ · 목록 · ci-filter · 변이 GREEN · ②(A-1) → ⓐ–ⓓ · ⓝ–ⓟ · ⓢ GREEN · ③(A-3) → Freshness · ⓠ GREEN · ④(A-4) → ⓔ · ⓠ 단언 GREEN.
4. ⑤(A-5) 뿌리 추가 → `harness-contract` RED 10건 로그 → 치환 → GREEN(같은 커밋 · 로그는 보고에).
5. 기존 시험 무변경 green · 시험 수 증분 기록(`run-selftest.sh:7,308,311` · `harness-eval-selftest.sh:8,281` · `gates/README.md:295` · S-red 뒤 기준 +4 / +1 / 정책 +1 — 실계수는 레인이 적는다) → 커밋 ⑥ 실측.
- seam: `COLAB_EVAL_MODEL_FILE`(신설) · `COLAB_EVAL_TASKS_DIR` · `COLAB_EVAL_RESULTS_ROOT` · `REPO_ROOT`(기존) · `PATH` 스텁 · fixture repo — 제품 게이트에 새 판정 seam 없음.

## 6. 위험 · 롤백
- 회차 비용: 정본을 `claude-fable-5-1` 로 두면 회차가 09-12 실측 ≈32 USD 로 돌아간다(09-26 opus 8.1 USD) · `COLAB_EVAL_BUDGET=2.01` 은 fable 최대 1.0067(`README.md:64`) 기준이라 유지 · T12 승인 액수 = 우려 #1 판정값.
- 기준선 단절: 「직전」 모델 조건으로 첫 회차는 회귀 기준이 없다(0 · 의도 · intent `:627` 「첫 회차가 새 기준선」). 과제 실패 4건(H14–H18 계열)이 fable 에서 red 로 돌아와도 게이트는 0 · 판정은 E1 대비표.
- `record-usage` 가 raw 를 읽는다(gitignored · 실행 직후 로컬 존재) · CI 면제 모드는 raw 를 보지 않는다(verify 는 `config-hash.json.model_usage` 만) · raw 삭제 뒤 재기록 불가 → 회차 커밋에 `model_usage` 가 들어 있어야 한다(V-A8 검사).
- 동시 open: PR B 가 `gates/fixtures/intent-ref/*.json` 을 바꾼다 → A 병합 전 `gates/**` 는 집합 안 → B 선병합 시 A 재실측(우려 #2).
- 요약줄 확장: 정규식 3곳(`harness-eval.sh:79` · selftest `:198,201`) 동시 갱신 · 누락 = ⓔ/`success` red 로 드러난다(fail-closed).
- 롤백 단위: ②(A-1)만 되돌리면 모델 미고정 상태로 복귀(집합 축소 · UTC · dirty · 위생은 남음) · ①(A-2)만 되돌리면 옛 집합(회차 재실측) · ⑤ 치환은 되돌리지 않는다(홈 경로 재유입).
- E0 규칙: 해시 집합 파일 변경 → head 회차 1회(면제 선택지 없음 · Q-A ⓐ) · 회차 뒤 집합 파일 push 금지.

## 7. 레인 지시 (PR A · lane-worker 1개)
- 스폰: `Agent(subagent_type: "lane-worker", isolation: "worktree")` · 기준 = S-red 병합 뒤 develop · 첫 행동 `git merge --ff-only develop` · 줄 번호 재열람(S-6a–d 이동분) · 부모 checkout 판정 정지 규칙 동일 · PR B 레인과 worktree 공유 금지(memory 「공유 워크트리 레인」).
- begin: `python3 scripts/agent-bridge.py lifecycle begin --role lane-worker --gate harness-contract-selftest --gate harness-eval-selftest --gate harness-contract --gate intent-ref --gate exec-bit --gate harness-eval --scope 'eval/harness/model.txt' --scope 'eval/harness/run.sh' --scope 'eval/harness/config_hash.py' --scope 'eval/harness/config-paths.txt' --scope 'eval/harness/README.md' --scope 'eval/harness/tests/run-selftest.sh' --scope 'eval/harness/results/**' --scope 'gates/tools/harness-eval.sh' --scope 'gates/tools/harness-eval-selftest.sh' --scope 'gates/tools/ci-filter-check.py' --scope 'gates/README.md' --scope 'gates/fixtures/harness-contract/home-paths.md' --scope '.github/workflows/ci.yml' --scope 'scripts/harness/check.py' --scope 'scripts/tests/test_harness_eval_gate.py' --scope 'scripts/tests/test_ci_eval_policy.py' --scope 'scripts/tests/test_harness_config.py' --scope '.agents/harness.yaml' --scope 'dev-package/prd/specs/stage3-login-hardening.md' --scope 'dev-package/prd/rounds/R-STAGE3-LOGIN-HARDENING.md' --scope 'dev-package/prd/rounds/R-SELECTED-PREVIEW-TIMING.md' --scope 'dev-package/prd/rounds/R-SELECTED-PREVIEW-TIMING-PR.md'`.
- 커밋 단위 — 각 커밋의 마지막 문단 하나 = 아래 세 줄(memory 「트레일러는 마지막 문단 하나에」 · 두 `-m` 으로 나누면 `intent-ref` 가 못 읽는다):
  ```
  Intent-Ref: dev-package/intent/2026-09-25-harness-improvement.md
  Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_019Mw7WhebGjZa4yVkM79Wpk
  ```
  - ① A-2 — `config-paths.txt` · `ci-filter-check.py` · `ci.yml` 3줄 · `test_harness_eval_gate.py` 목록·ⓕ · `harness-eval-selftest.sh` ⓠ fixture · `test_ci_eval_policy.py` 변이 · 기준 8 · `gates/README.md:48` · `README.md:150-151`.
  - ② A-1 — `model.txt` · `run.sh`(정본 · `--model` · `record-usage` · 요약줄) · `config_hash.py`(compute · record-usage · verify 2조건) · `harness-eval.sh:79` 정규식 · selftest 2벌(ⓝ–ⓟ · ⓢ · `:198,201`) · `test_harness_eval_gate.py` ⓐ–ⓓ · `README.md:108,164` · `check.py:79-81`.
  - ③ A-3 — `run.sh:76` `date -u` · `check.py` UTC · README 1줄 · FreshnessTests · run-selftest ⓠ.
  - ④ A-4 — `config_hash.py` dirty 상세 · VerifyTests ⓔ · selftest ⓠ 단언.
  - ⑤ A-5 — `harness.yaml` 뿌리 3개 · 치환 10줄 · `test_harness_config.py` fixture · 본문에 red 10건 로그와 치환 명령.
  - ⑥ `results/<run>/` 4종(실측 · ⑤ 뒤의 해시 · `config-hash.json` 에 `model` · `model_usage` 포함). 되돌림 단위 = ② · ①.
- 회차(모든 단위 뒤 · 1회): worktree 루트에서 `COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=150 COLAB_EVAL_BUDGET=2.01 bash gates/run.sh harness-eval` → `results/<run>/` 4종 커밋 ⑥ · 중첩 `claude -p` 거부 시 T12(사람이 같은 명령 · 결과를 레인 브랜치에 커밋) · 이 회차 = 새 기준선(직전 없음 · `20260926-143218` 은 참고 출력) · 회차 뒤 집합 파일 변경 금지.
- 게이트: `COLAB_HARNESS_EVAL_EXEMPT=1 COLAB_TASK_ID=<id> bash gates/run.sh task` 1회(⑥ 뒤 · 호스트 단독 · `harness-eval-selftest` 는 serial `parallelism.toml:293`).
- 인계: `lifecycle handoff --task <id> --mode complete --summary '…'` · `COLAB_HANDOFF` · `WORKTREE= BRANCH=` · 보고에 red→green 로그(§5 1·2·4) · 실계수 · 회차 USD. push · 게시(T16) · 병합(T13) = 사람.

## 8. 검증표
| V | 명령(worktree 루트) | 기대 | 완료 기준 |
|---|---|---|---|
| V-A1·A2 | `bash gates/run.sh harness-contract-selftest` · `bash eval/harness/tests/run-selftest.sh` · 수동: `COLAB_EVAL_MODEL_FILE=/nonexistent COLAB_EVAL_TIMEOUT=10 COLAB_EVAL_BUDGET=0.5 bash eval/harness/run.sh` | green · green(ⓝ–ⓠ 포함) · 78 + 「모델 정본」 | 4.1 |
| V-A3·A4 | `python3 eval/harness/config_hash.py compute --root . \| python3 -c 'import json,sys; print(json.load(sys.stdin)["files"])'` · `git ls-files -- ':(glob)gates/**' \| wc -l` · `python3 gates/tools/ci-filter-check.py` | 집합 ≈ 580 − 363 + 3(레인 실계수) · 참고 · green(필터 전용 4) | 4.2 |
| V-A5 | `bash gates/run.sh harness-contract-selftest`(Freshness) · `grep -c 'date -u' eval/harness/run.sh` · `grep -c 'id = UTC\|id 는 \*\*UTC' eval/harness/README.md` · `grep -c KST scripts/harness/check.py` | green · 1 · 1 · 0 | 4.3 |
| V-A6 | 임시 파일 `touch scripts/harness/hooks/zz.sh` 뒤 `COLAB_HARNESS_EVAL_EXEMPT=1 bash gates/run.sh harness-eval` · 삭제 | 78 + `dirty 1건: scripts/harness/hooks/zz.sh` | 4.4 |
| V-A7 | `bash gates/run.sh harness-contract` · `grep -rnE '/home/[A-Za-z0-9._-]+/' eval/harness/results dev-package/intent dev-package/prd \| wc -l` | green(`home-path roots 9`) · 0 | 4.5 |
| V-A8 | `COLAB_HARNESS_EVAL_EXEMPT=1 bash gates/run.sh harness-eval` · `python3 -c 'import json; d=json.load(open("eval/harness/results/<run>/config-hash.json")); print(d["model"], d["model_usage"])'` | 0 + 일치 run id + 두 해시 동일 + 「직전 없음」 + `참고(다른 모델) 20260926-143218` · 정본 == model · 정본 ∈ usage | E0 규칙 |
| V-A9 | `grep -n '호출 환경의 기본값\|모델을 지정하지 않' eval/harness/README.md scripts/harness/check.py` · `grep -c '필터 전용 3줄' gates/README.md` | 0 · 0 | 문서 |
| V-A10 | `python3 scripts/agent-bridge.py check` · `git diff develop --stat -- scripts/agent-bridge.py .codex scripts/codex-harness-eval.py .claude/settings.json .codex/hooks.json` | green · 0 | 공통 |
| 공통 | `bash gates/run.sh exec-bit` · `bash gates/run.sh intent-ref` · `bash gates/run.sh harness-eval-selftest` | 0 · 0 · 0(케이스 실계수 · 정책 8) | |

## 9. PR 본문 계획
- 파일 `~/.claude/pr-bodies/PR-BODY-harness-team-A-eval.md` · `pr_contract.py … --mode draft` → 0 · 게시 = T16(사람).
- 첫 줄: 「하네스 개선 팀 공용 A — eval 회차가 저장소 정본 모델로 재고 `verify` 가 모델을 대조하며, 해시 집합에서 제품 게이트를 빼고 run id 를 UTC 로 둔다」.
- `Plan-Ref: dev-package/prd/specs/S-HARNESS-TEAM-A-EVAL-20260926.md`(총괄 §10 행 5a) · 결정 = 정본 `model.txt` 1파일 · 실측 = `canonicalModel` · 직전 = 같은 모델만 · 집합 = 명시 열거(pathspec exclude 재포함 불가 실측) · `gates/**` 는 CI 필터 전용 · run id UTC 접미사 없음 · 증거·레거시 10줄 치환 · 새 ADR 없음 · 검증 = V-A1–A10 + red→green 로그 + 회차 USD · 남은 제약 = `claude_version` 미대조 · 조상 기반 「직전」은 PR 2 · S-6a `$HOME` 은 S-red 리뷰 · B 와의 병합 순서(우려 #2) · Codex 러너 해시 기록은 별도 intent.
- 게시 뒤: 사람 병합(T13) → PR B 병합 → T11 재판정(구성원별 PAT · 총괄 `:226`) → intent ⓐ 결정 → PR 2 착수(2-6 「직전」 조상 조건이 이 함수 위에).

## T-항목 (Ted · 번호 = 총괄 Ted 행동표 · 10라운드 재정의 `:250-256`)
| T | 행동 | 명령/UI | 기록 |
|---|---|---|---|
| T12 | 우려 #1 판정(모델 정본 값) 뒤 PR A head 실측 승인 — 액수 = 정본이 fable 이면 ≈32 USD · opus-5-5 면 ≈8 USD · 면제 선택지 없음 · 레인이 중첩 `claude -p` 를 못 돌리면 사람 실행 | 대화 판정 · 실행 = §7 회차 명령(worktree 루트) | intent 「판정 기록」(모델 값) · 「확인」(run id · USD · `model_usage`) |
| T16 | PR 게시 — 메인 세션 초안(§9) · 사람이 `gh pr create --base develop` | 개인 터미널 | PR 번호 → intent 「확인」 |
| T13 | 사람 병합(승인 수 0 유지 · 작성자 본인 가능 · Q1) · B 보다 먼저(우려 #2) | GitHub UI Merge | 병합 SHA |
| T11(뒤) | A·B 병합 뒤 구성원별 에이전트 PAT 재판정(총괄 `:226`) — 이 PR 의 조건 아님 | — | — |

## 우려 항목
| # | 항목 | ⓐ | ⓑ | 권고 | 판정 |
|---|---|---|---|---|---|
| 1 | `model.txt` 값 | `claude-fable-5-1`(README:108 정본 · 09-08·09-12 회차 실측 모델) | `claude-opus-5-5`(회차 `5b84d899` 실측 `canonicalModel` · 8.1 USD) | ⓐ — 과제 20건은 판정 과제(README:94 「판정을 재지 수정 능력을 재지 않는다」)이고 Ted 계획의 판정·권고 모델은 Fable(9·10라운드 blind 판정 · 감사 3건 · 이 spec)이다. 판정 모델로 잰 회차만 「같은 판정」의 기준선이 된다. 대가 = 회차 ≈32 USD(09-12 실측 · T12 액수). ⓑ 는 싸지만 계획의 판정 모델과 다른 모델의 기준선을 만든다 | 〈판정 대기〉 |
| 2 | PR A ∥ B 동시 open 조건 | A 선병합 고정 — B 는 `gates/fixtures/intent-ref/*.json` 을 바꾸므로 A 병합 전엔 집합 안(현 `gates/**`) · B 가 먼저 들어가면 A 재실측 | B 가 fixture 변경 커밋을 A 병합 뒤로 미룸(나머지 `scripts/harness/**` · `dev-package/**` 는 집합 밖) | ⓐ — 순서 1줄이 장치 없이 성립 · B 병합 뒤 A 는 이미 병합 상태라 재실측 0 · 총괄 §0 팀 규칙(해시 집합 PR 동시 1건)과 일치 | 〈판정 대기〉 |
| 3 | `:(exclude).agents/ci-producers.json` 포함 여부 | 포함(권고 3 · 총괄 `:224` · `:232` S-dep 회차 0 의 전제 · 「권고 2–12 전부 수용」) | 제외(intent `:627` Q2 문장은 `gates/**` 만) | ⓐ — 등록부는 모델 입력이 아니고 단일 파일 exclude 는 pathspec 으로 성립(실측) | 〈판정 대기〉 |
| 4 | `dev-package/reports` 뿌리 | 이번 PR 은 확정 3개만 · PR B 반입물의 `<repo>` 치환은 B 자신의 검사 | `dev-package/reports` 도 추가(`compatibility_read_roots:93` 에 이미 있음) | ⓐ — 기존 reports 의 홈 경로 건수 미실측 · 추가는 PR 2 총괄 갱신 때 실측 뒤 | 〈판정 대기〉 |
| 5 | 요약줄 모델 표기 위치 | 요약줄 끝 ` · 모델 <정본>`(정규식 3곳 갱신 · 회차 표 한 줄에 모델) | 별도 줄만(`- 모델 —`) · 정규식 무변경 | ⓐ — intent `:627` 「요약줄 모델 표기」 축자 · 별도 줄은 실측 목록용으로 함께 둔다 | 〈판정 대기〉 |
| 6 | `model_usage` 빈 목록 | 러너는 기록만 · `verify` 가 78 `model-mismatch`(정본 ∉ []) | 러너가 즉시 78 | ⓐ — 스텁 회차(셀프테스트)와 실회차를 한 규약으로 · 판정은 한 자리(`verify`) | 〈판정 대기〉 |
| 7 | 기존 증거·레거시 10줄 처리 | 치환(results 6줄 `<repo>` · prd 4줄 `~/`) | `home_path_allow` 에 실행자 홈 등재 | ⓐ — ⓑ 는 홈 경로를 계약 파일에 싣는다 · 치환 대상은 집합 밖 · 승인 intent 아님 | 〈판정 대기〉 |

## 정책 대조
- 시스템 우선(총괄 §0 · 10.1): A-1 = 러너 78 + `verify` 78(장치) · A-2 = 계산기 + `ci-filter-check` ㈏·㈖(장치) · A-3 = 러너·`check.py`(장치) + README 1줄(포인터) · A-4 = 출력(진단) · A-5 = `harness-contract`(장치). 산문 전용 단위 0.
- 병합은 사람(Q1): 이 PR 의 병합 조건 문구는 「사람 병합(T13)」 · 승인 수 0 유지 · 에이전트 토큰 병합 불가는 T11 재판정(A·B 뒤).
- 승인 intent append-only(ADR-0007): intent 편집 0 · `dev-package/prd` 레거시 4줄은 intent 아님. ADR 이력 무수정: 새 ADR 없음 · 0011/0012 예약 유지. 훅 정의 무변경: diff 0(V-A10).
- 팀 원칙 3항: 판정(정본 모델 · UTC · 집합) · 보호(다른 모델 회차 면제 불가 · 홈 경로 red) · 비용(제품 병합 무효화 0 · 회차 액수 = 모델 정본으로 고정) — 단위별 답은 §4 각 끝 줄.
- 게이트 종료코드: 0/1/78 의미 유지 — 정본 부재 · 모델 불일치 · 후보 없음 = 78(못 읽음/못 잼) · 회귀 = 1 · 필터 불일치 · 홈 경로 = 1(읽었는데 위반).

## 범위 밖
- 「직전」 조상 조건(`merge-base --is-ancestor` · 권고 7 · PR 2) · `claude_version` major.minor 대조(D3 제안 · 미확정) · CI 실행 모드 `harness-eval-run`(intent ⓐ) · Codex 러너 `scripts/codex-harness-eval.py` 해시·모델 기록(별도 intent) · S-6a `$HOME` 치환(S-red 리뷰) · `CLAUDE_CONFIG_DIR` 격리(충돌·미확인 ② 미검증 · 1회 실측 뒤 별건) · `dev-package/reports` 뿌리(우려 #4) · 승인 형식·`intent_ref.py`·보고서 반입(PR B) · 총괄 §0·§6 팀 규칙 문구(PR 2 총괄 갱신) · 훅 · 등록부 · `parallelism.toml` · `.codex/**` diff 0.
