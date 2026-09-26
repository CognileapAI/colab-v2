VERDICT: ACCEPT-WITH-CHANGES

## 필수 변경
1. 자리 4.1 축소 검사 · V-B5 · 시험 ② — 문제: 「이름 추가 = green」이라 새 intent 를 legacy 표기(「승인」)로 쓰고 같은 PR 에서 스냅샷에 이름 1줄 추가하면 handle 없이 approved·보호가 된다(Q4 「그 꼴만 승인」 우회 · 스냅샷은 head 에서도 읽으므로 `:55` 설계상 즉시 성립) — 고칠 내용: 규칙을 「base 에 `LEGACY_SNAPSHOT` 이 있으면 head 블롭과 바이트 동일해야 한다 · 차이(추가·삭제·주석) = red · base 부재(도입 PR) 만 생략」으로 교체. V-B5 = 「스냅샷은 도입 뒤 불변」. §6 두 번째 항목·§9 「병합 직전 재동결」은 base 부재 상태(B 자체)에서만 가능하므로 그대로 유효. `legacy_names` 는 base 우선 · 없으면 head 로 단순화.
2. 자리 4.2 「실행 게이트」 · 4.1 강제 기제 · §9 — 문제: `harness-contract-selftest` 를 CI 가 어디서 돌리는지 없다. 실측: `ci.yml` 에 이름 0건 · `.agents/ci-producers.json` 0건 · `gate-selftest` 잡은 `contracts` 필터(`ci.yml:70-74` `contracts/**`·`gates/**`)라 B 경로에서 안 깬다 · 도는 곳은 `.github/workflows/agent-bridge.yml:61`(paths `scripts/harness/**`·`scripts/tests/**`) 뿐이고 ruleset 필수 check 는 `ci-required` 하나(`T1-develop-ruleset.json` `required_status_checks`) — 고칠 내용: 4.2 에 「CI = agent-bridge.yml `compatibility`(필수 check 아님) · 병합 차단은 `intent-ref` 잡(`ci.yml:851`) 뿐」 명기 · 병합 조건에 「compatibility green 을 병합자가 확인」 1줄 · §9 PR 본문 「남은 제약」에 동일 문장.
3. 자리 §7 스폰·begin 앞 — 문제: 결정 출처 10라운드 줄(intent `:627`) · S-auth 추가 기록 4줄 · 총괄 +57줄 · spec A/B · intent ⓐⓑ 가 전부 미커밋(`git diff HEAD --stat` 3 파일 +62 · untracked 4)이라 「기준 = develop」인 lane 의 head 에 B-5 「`:628` 뒤」·`Plan-Ref` 대상이 없다 — 고칠 내용: 「선행: 메인이 위 편집을 develop 에 커밋·병합(intent 2건은 줄 추가 = intent-ref green) 또는 B 브랜치 커밋 ⓪(같은 트레일러)」 1줄 · 커밋 단위에 ⓪ 추가.

## 개선(비차단)
1. 인용 줄 정정: ADR-0007 「알려진 비보호」= `:26`(`:30` 아님) · 「메타 형식이 바뀌어」= `:30`(`:34-35` 아님) · 「훅은 두지 않는다」= `:15` · 시험 legacy 문자열 = `:245` `:254`(`:236` `:245` 아님) · TEMPLATE 단언 = `:383`.
2. v2 정답표 「84 파일 = 63/15/6」 은 TEMPLATE.md(unapproved) · README.md(no-meta) 를 행으로 센 값(intent 만은 82 = 63/14/5) — `rule` 열에 `excluded` 값 또는 `protected:false` 열을 명시.
3. T-표 T19 `@<Ted handle>` → `@<승인자 handle>` · T13/T16 「Ted」 → 「병합자·게시자」(PR 4 앞이라도 이 표는 역할어로).
4. `--freeze-legacy` 출력을 `sys.stdout.buffer.write`(LF 고정)로 — Windows python 텍스트 stdout 은 CRLF 라 V-B3 바이트 동일이 OS 로 갈린다. 4.4 `sed -i` 는 GNU 전용 → 「1회 반입 명령 · 결과 파일이 정본 · 재현 대상 아님」 1구.
5. 4.3 TEMPLATE 주석 줄의 예시 형식 문자열이 `META`(`^메타`) 에 안 걸리는 사실을 시험 ⑦ 옆에 1줄(오탐 방지 근거).

## 확인한 사실
- `scripts/harness/intent_ref.py:29-34` 상수 · `:41-49` classify(첫 메타 줄 · 미승인 → unapproved · 승인 → approved) · `:52-53` is_protected · `:77-79` show · `:149-151` intent_names · `:153-160` base∪fork 보호 · `:175` 출력 · `:179-184` argparse — 전부 spec 인용과 일치.
- `gates/run.sh:356-357` harness-contract-selftest 가 `test_harness_record_gates.py` 실행 · `:365-369` intent-ref · `:14,32` ALL_GATES 등재 · `ci.yml:663-677` intent-ref 잡(base/head sha) · `parallelism.toml:44` parallel.
- `eval/harness/config-paths.txt:8`(scripts/harness/*.py 밖) · `:12` .agents/** · `:13` gates/** — B 의 scope 파일 전부 집합 밖 · 회차 불요 성립.
- 현 규칙 approved intent = 63(HEAD `5bb3d6fe` · TEMPLATE/README 제외 82 중) — spec 63 과 일치 · untracked intent ⓐⓑ 메타 「승인 미승인」.
- v1 정답표 `:2` 0a3b9923 · `:4` 62 · 44/13/5 · `:12-14` intended_unprotected — 일치. `test_harness_record_gates.py:24-26` APPROVED · `:148` 클래스 · `:153-161` repo() — 일치.
- `TEMPLATE.md:2,13,26` 실명 · `README.md:1-2` 「Ted 가 교정 · 승인 = 커밋」 — 일치. `harness.yaml:100-101` home_path_roots 에 dev-package 없음 · allow `/home/user/` — 일치.
- 보고서 원본 88 파일 · 1.6 MB · `<home>` 33곳(measurement.json 17 · guard_probe 1 · intent-draft 2 · 13×1 = spec 9+5+19) · 비밀 패턴 0 · `dev-package/reports/harness/2026-09-06/README.md` 존재.
- `.gitignore:35` `*.log` · `:83` gate-summary.json · `exec-bit.sh:16` `.sh` 만 · `decision-number-guard.sh:60` PLAN-SoT 만 — 일치. ADR-0003 `:18-19` · `:35` 선례 — 일치. ADR-0007 `:14` — 일치.
- `lifecycle_contract.py:543-549` begin 이 `--role/--gate/--scope` 를 받고 handoff complete 가 scope 밖 변경을 막는다 · `gates/run.sh:63` task 게이트 존재 · `scripts/tests/fixtures/` 는 신규 디렉터리(제약 시험 없음).
- 10라운드 확정(Q1 승인 0 · 사람 병합 · Q4 형식 · 소형 PR B 범위)과 spec §0·4.3·4.4·정책 대조 — 충돌 없음. 우려 #1 ⓐ(legacy 스냅샷)는 「그 꼴만 승인」의 명시 확장이며 판정 대기로 표시됨.
