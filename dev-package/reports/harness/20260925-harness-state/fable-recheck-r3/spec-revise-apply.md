

적용 확인
- 1 반영 — §4.1 결정 2(원칙 · 미종결 heredoc parsed) · 결정 3 · 시험 ⑶ 미종결 fixture · ⑸ `bash -n` rc≠0 단언 · V5
- 2 반영 — §4.1 결정 2(JSON lines 프로토콜 · 판정 위치 = python 1회 · 근거 3점) · 시험 ⑶ 여러 줄 `-m` · 단위 시험 · §11 #4
- 3 반영 — §4.1 시험 fixture(메인 repo feature · `dev co` develop · ⑴ cwd = `dev co`)
- 4 반영 — §4.1 결정 1(read_fields 폴백 전용) · 결정 2(종료 표식 `{"end": N}` · 검증 조건) · 시험 ⑸ (d)(e)(+f)
- 5 반영(적응) — §4.1 결정 3 「branch 지연 평가」: 레코드는 dir 만 · push|merge|pull|branch 진입 때만 rev-parse · dict 캐시 · status/log/gh 0회 단위 시험. 위치는 「bash 쪽」이 아니라 python 엔진 안 — 2번 결정(규칙 판정을 python 1회 안으로)의 귀결이며 관측 요건(호출 0회 · 캐시)은 동일. bash 폴백 엔진은 현행 `:143` 유지
- 6 반영 — §4.1 시험 ⑴ 허용형 `stderr == ''` · 「실사용 corpus 시험」 · §6 fail-open 위험 · V1
- 7 반영 — §7 V7(옛 문구 정확 검색 `grep -nF` · `main/master` 0건) · §4.1 결정 4 거부 문구(`:271` + `:227·:231·:235·:239·:243` PR 1 정리) · §1
- 8 반영 — §4.1 결정 4 gh(`pulls/[0-9]+/merge/?(\?|$)` · graphql 은 머리말 잔여 우회) · 결정 5 · 시험 ⑷ · §12
- 9 반영 — §4.1 결정 4 push(`+` 제거 뒤 · src/dst 모두 · `+HEAD` = force) · 시험 ⑵ hook 수준 3건 · ⑷ `+HEAD`
- 10 반영 — §4.1 파일·앵커 문단(shim 3행 · BASH_SOURCE 해석 · adapter 우려 삭제) · 시험 「`.claude/hooks` shim 경유 고정」 · 결정 2 폴백 stderr 1줄 · 시험 ⑸ 단언
- 11 반영 — §4.1 결정 3(인용 인식 중첩 괄호 · `$((…))` · `cat<<EOF`) · 해석기 단위 시험 3건
- 12 반영 — §4.4(`ALL_GATES` `:284` 정정 · KNOWN = ALL_GATES 유지 · 교차 점검 실측 · KNOWN 전수 unit 1건) · V12 · §11 #3
- 13 반영 — §4.6(readiness 는 경로·내용 선별 뒤 새 결정 번호 후보 있을 때만 · python 1회 유지) · 시험 3케이스 · V14
- 14 반영 — §4.4 영향 조사 마지막 문장(`gates/README.md:78` 1줄 · `all -j` 인자 2개 동작 변화) · §6
- 15 반영 — §8 scope 에 `scripts/tests/test_agent_bridge.py`(조건부) 추가
- 16 반영 — §5 시험 수 기준값(① 뒤 기록 · ③ 증가분 별도) · §8 커밋 ①③ · §9 검증
- 17 반영 — §4.1 결정 1(env seam 제거) · 시험 ⑸ tempdir 복사본 (a)–(f) · 차선 보고 조항 · §3 · §5 · V5b · §11 #2 ⓑ
- 18 반영 — 새 §4.7(A7 · 출력 형태 · 권고 문구 · Codex 호환 · 주석/문서 정정 · 시험 앵커 `:431-434`·`:515-518`·`:538-539` 재확인 · 완료 기준) · 새 §4.8(C12 커밋 ⑥ · `:21` · `:74`) · §0·§1·§2 V16/V17 · §7 · §8 scope·커밋 ⑤⑥ · §9. 정정 1건: README 에 researcher-task 행이 없어(`grep` 0건) `README.md:72` worktree-setup 행만 PR 1 · 행 추가는 C2
- 19 반영 — §9 검증 상태 문장(`agent-bridge.yml:64` unittest discover · 경로 필터 · 비필수) · 남은 제약
- 20 반영 — §9 본문 파일 위치 유지 · §8 레인 지시 「SubagentStart hook 출력은 지금 레인에 안 보인다(A7 전) — 직접 확인」 1줄
- 앵커 정정(재열람): `run.sh` `:308→:310` · `:312→:316` · `:296-306→:284-305` · `:42→:36-41` · `:163-170→:170` · `:971-977→:972-973/:975-977` · lifecycle 시험 `:361-372→:366-380` · `:376-384→:381-396` · `test_agent_bridge.py:463→:461` · `agent-bridge.py:275-278→:278` · `.claude/settings.json` Edit|Write matcher `:69`·`:88`
- 미적용 없음. 판단 여지 1건(5번 위치 적응)은 위에 명시.