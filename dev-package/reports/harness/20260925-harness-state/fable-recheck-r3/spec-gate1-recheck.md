VERDICT: GO-WITH-CHANGES

- 20건 판정: 1·2·3·4·6·8·9·10·11·12·13·14·15·16·17·18·19·20 반영 / 5 반영(적응 — 지연 평가 위치가 bash 가 아니라 python 엔진 안 · 2번 결정의 귀결이라 수용 · 관측 요건(status/log/gh rev-parse 0회 · dir 캐시) 동일) / 7 잘못 반영(아래).
- 7 결함: §7 V7 「`grep -n 'main/master' git-guard.sh` 0건」인데 실측 `main/master` 는 deny 5곳(:227·:231·:235·:239·:243) 외 주석 :13(머리말 열거 · spec 은 `:11` 머리말 유지) · :151 · :229 · :233 · :237 · :241 · :248 에도 있어 검증표가 그대로면 red. 수정: §4.1 결정 4 정리 범위를 「deny 문구 + 같은 파일 주석 전부(:13 포함)」로 확장하고 V7 은 유지 — 또는 V7 을 `grep -n 'deny "[^"]*main/master'` 0건으로 좁힘. 전자 권고(파일 소유 PR 1).
- 안전 항목 ① git-guard 폴백·레코드 프로토콜 — 코드 앵커 실측 일치(:71 exit1 문장 · :82-83 envelope · :90 도달 불가 · :92 read_fields · :110 mapfile · :143 BRANCH · :167 `set -- $seg` · :271). shim 3행 `exec bash …/../../scripts/harness/hooks/git-guard.sh` 확인 → 본체 BASH_SOURCE = scripts/harness/hooks ✓. 종료 표식 + 접두 정규식 검증 + rc∈{0,2} 분기는 (a)–(f) 전부 폴백/deny 로 귀결 · crash 경로 없음 ✓.
- 안전 항목 ② A6 — decision-number-guard :56-57 도구·경로 선별 · :63-73 BASE/폴백/`exit 0` 실측 일치. readiness 를 「PLAN-SoT 편집에 새 결정 번호 후보 있을 때만」으로 축소한 §4.6 은 :73 삭제 + python 1회 안 판정으로 구현 가능 ✓.
- 안전 항목 ③ A7 — `test_task_runtime.py` :432 `printed()` · :515-518 · :522 · :529 · :538-539 · :408-409 copytree fixture · :551/:560 bridge `additionalContext` 실측 일치. `agent-bridge.py:300-302` 가 `hookSpecificOutput.additionalContext` 재적재 → Codex 무영향 ✓. :461-465 도 `printed()` 경유라 JSON 파싱 전환에 포함됨(명시 권고).
- V16 grep `'평문'` 주의: `bootstrap-diet.sh:23-26` · `worktree-setup.sh:40-42` 에는 '평문' 문자열 없음(실측 0건) — 해당 주석은 내용으로 찾아 고칠 것 · grep 0건이 정정 증거가 되지 못함(researcher-task:14 만 매치). 레인 지시에 1줄.
- run.sh 앵커 실측: `:9` GATE · `:170` mutex · `:284` ALL_GATES · `:310`/`:316` unittest 목록 · `:973`/`:977` exit 2 — spec 정정치 일치 ✓.
- CI 사실: `agent-bridge.yml:64` `unittest discover -s scripts/tests` · 경로 필터에 `scripts/tests/**`·`scripts/harness/**`·`gates/run.sh` 포함 → 19 문장 정확 ✓.
- css-edit-audit `:21` 문구 · `:30` python3 · `:74` `echo "$OUT"` 실측 일치 ✓.
- scope 목록: spec 이 편집하는 18 파일 전부 §8 `--scope` 에 있음 · 무변경 파일(shim · settings.json · hooks.json · lifecycle_contract.py) 미포함 정합 ✓.
- 커밋 단위 ①–⑥ 정합: 각 되돌림 단위 독립 · README.md 가 ①②④⑤ 에 걸치나 행 단위라 충돌 없음 · ② test-file-guard 머리말이 ① 이후 동작 기준이라 순서 고정 명시됨 ✓.
- 범위 확장 없음: A1–A7 + C12 외 항목 0 · KNOWN_GATES 합치기는 `all` 집합 불변 조건부라 A4 안 ✓.
- 조치 후 재게이트 불요 — 7번 문구 정리 범위·V16 grep 주의 2건은 spec 문안 수정 후 그대로 레인 스폰.