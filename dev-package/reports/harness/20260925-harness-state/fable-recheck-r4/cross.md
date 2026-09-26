CROSS: ISSUES 10
- A6·V14·C2 — spec V14(`:172`) `grep origin/main … README.md` 0건 기대인데 `README.md:74`(migration-guard 행)는 C2·PR 3 몫으로 남아 PR 1 V14 가 red — lane HEAD 901eb02a(커밋 0)이므로 lane 에 1줄 통지: 커밋 ④에서 `:74` `origin/main`→`origin/develop` 한 단어(사실 = `migration-guard.sh:72`) · C2 완료 기준은 A6 단독으로 정정
- C9ⓑ·T10 — 같은 항목이 두 번 판정되고 배치가 다름(C9ⓑ「L7·PR 2 결정에 흡수」 vs T10「불채택 · PR 3 frontmatter 때 재판정」) · advisor.md:39 문안도 2벌 — T10 한 항목으로 통합(결정 입력 = L7 결과 · 편집 = PR 3 · 문안 = T10 판)
- C7 ← L7·T10·C6 — C7 값 확정은 L7(PR 2) 뒤 · C6 와 `agent-bridge.py`·`test_agent_bridge.py` 공유 — PR 3 커밋 순서 C6 → C7(마지막) · Codex toml 대조는 이미 tomllib 로 읽는 `agent-bridge.py:84 check()` 에 두고 check.py 는 Claude frontmatter 만(두 번째 toml 파서 불요)
- C1 — 위험 ①「toml 이 생성물」 기각: `agent-bridge.py:84` 는 `.codex/agents/<role>.toml` 을 읽기만 함 → `:12` 주석 직접 편집 안전 · C7 과 같은 파일이므로 PR 3 에서 C1 을 C7 커밋에 합침
- PR 2 반입 목록 누락 위험 — C3①(ci.yml 주석 → B4) · C8③(lifecycle-evidence measurement-lane 절) · C9①(lane-worker.md:27 → L3) · T8(L1 spec 1줄) · T10(L7 입력) 5건이 stub 인 PR 2 spec 에 흩어짐 — 판정 기록에 「PR 2 phase 2 반입 5건」 1줄로 지금 고정
- C5 ← T1 — T1 적용 형식(branch protection `…/branches/develop/protection` vs ruleset `…/rulesets`)이 미정인데 C5 는 `protection` GET 을, ruleset.json 은 ruleset 형식을 전제 — Ted 가 T1 적용 시 형식을 고르면 C5 는 그 형식 하나로 기록(둘 다 두지 않음) · T1 은 PR 2 open 전에 적용(strict 뒤 PR 2·3 는 Update branch 필요 · B1 문구가 안내)
- T9 → T3 → T5 순서 — T3 위험(32 옛 데몬이 잠금 fd 보유)은 T9 `pgrep -a postgres` 가 먼저 답함 · T5 는 T3 직후 1회 · PR 2 가 `.codex/hooks.json` 을 또 바꾸면(L1 git-guard 확장은 스크립트 본문 · hooks.json 무변경 예상) 재신뢰 2회 — 32 를 PR 3 전에 쓸 일이 없으면 갱신·재신뢰를 PR 3 병합 뒤 1회로 미루는 편이 최소
- T3·T4 독립 확인 — `git worktree list` = 메인(67a03a05 develop) · `agent-a5bf…`(locked) · `harness-improvement`(locked · 901eb02a) 뿐 → 33 은 linked worktree 아님(독립 clone) · T4 의 `git worktree prune` 은 현재 no-op · T4 지금 실행 가능(브랜치가 어느 워크트리에도 checkout 안 됨)
- T8 ← PR 2 L1 — `prune` 문자열 `lifecycle_contract.py`·`agent-bridge.py` 0건 → `lifecycle prune` 미존재 · T8 의 현재 결정은 「L1 spec 에 gone-checkout = 닫힘 상당 1줄」뿐 · 서브에이전트 차단은 판정 기록 :559 대로 PR 2 git-guard 확장(PR 1 A1 재작성본 위)
- C10③·worktree-setup.sh:249 — `origin/main` 주석이 A7 재작성 블록(`:245-267`) 안 → lane 이 그대로 옮기면 PR 3 재앵커, 지우면 C10③ 일부 소멸 → PR 1 병합 diff 로 판정(지금 lane 지시 변경 없음)

### C1
VERDICT: KEEP
- 최종 권고: 전제 문장 교체(serial = 호스트 뮤텍스 · parallel 은 뮤텍스 밖 · postgres 슬롯 호스트 전역) · ADR-0005 근거 · PR 3 · C7 커밋에 합침
- 반박 시도: `scripts/agent-bridge.py:84` tomllib 읽기만 → 생성물 아님 · PR 1 scope(spec `:181`)에 두 파일 없음
- 위험: L6(PR 2) 「역할 문서 1줄」이 `measurement-lane.md` 접촉 시 순차 재앵커

### C2
VERDICT: REVISE
- 최종 권고: 표 삭제·정본 링크 유지 · PR 3 · 단 `README.md:74` 는 PR 1 커밋 ④로 이관(V14 성립 조건) · C2 완료 기준 grep 은 A6 결과 확인용
- 반박 시도: grep 실측 `README.md:74`·`:75` 2건 · spec V14 `:172` 가 README.md 전체 0건 기대 → 현 배분으로는 PR 1 검증 red
- 위험: lane 통지 누락 시 V14 를 lane 이 임의로 `:75` 한정으로 해석

### C3
VERDICT: KEEP
- 최종 권고: ① ci.yml 주석 → PR 2 B4 커밋 · ② gates/README 표 → PR 3 · ③ ⓑ 는 B4 뒤 Ted 판정
- 반박 시도: `gates/README.md:78` 은 A4(PR 1) 접촉 → ② 는 병합 뒤 줄 재앵커 · 다른 반박 없음
- 위험: ① 이 PR 2 「코드」 원칙의 문서 예외 3건 중 하나(C9①·C8③ 과 함께 목록화)

### C4
VERDICT: KEEP
- 최종 권고: `AGENTS.md:18` 포인터 교체(줄 수 불변 · `harness.yaml:98` 120줄 상한 안) · handoff 「이후 이력」 절 · PR 3 마지막 커밋
- 반박 시도: hygiene `always_on_max_lines: 120`(`harness.yaml:98-99`) 확인 → 1줄 교체 무해 · PR 1 scope 에 세 파일 없음
- 위험: C11 이 mtime 노출을 지우면 C4 위험 ② 소멸(무해)

### C5
VERDICT: REVISE
- 최종 권고: PR 3 · T1 적용 형식 하나로만 기록 · `release-evidence.md:43·45` 정정 · T1 미적용 시 폴백 유지
- 반박 시도: 판정 기록 `:546` T1 = ci-required·PR 필수·strict·우회 없음 · 적용 API 형식 미지정 → 두 형식 공존 전제가 약함
- 위험: T1 이 PR 2 open 뒤에 적용되면 PR 2 가 Update branch 강제(B1 문구 의존)

### C6
VERDICT: KEEP
- 최종 권고: PR 3 · adapter 4종 플래그 승계 · `agent-bridge.py check()` 2조건 · VENDORED.md 정정
- 반박 시도: `check()` `:82` 확인 · PR 1 scope 밖 · B4 로 record 경로 편입
- 위험: C7 과 같은 파일 → 순서 C6 먼저

### C7
VERDICT: REVISE
- 최종 권고: PR 3 · harness.yaml `role_registrations` 스칼라 선언 · Claude frontmatter = check.py · Codex toml = `agent-bridge.py:84` 기존 로더 · 값 확정 = L7·T10 뒤 · PR 3 마지막
- 반박 시도: `hook_registrations` 패턴(`harness.yaml:50-62`) 존재 확인 · toml 파서 이미 bridge 에 있음
- 위험: `config.py` 미지 키 거부 여부 미확인

### C8
VERDICT: KEEP
- 최종 권고: PR 3 `dual-agent.md` 만 · ③ lifecycle-evidence 절은 PR 2 · `sources.hook_names`(`harness.yaml:49` · 11개) 참조 유효
- 반박 시도: hook_names 키 실존 확인 · A2/A7 접촉 줄과 분리
- 위험: ③ 이 PR 2 반입 목록에 없으면 유실

### C9
VERDICT: REVISE
- 최종 권고: ⓐ 문장 교정 PR 3 · ① lane-worker.md:27 은 L3(PR 2) · ② advisor.md:39 문안은 T10 판으로 단일화 · grep 기준 한국어로
- 반박 시도: spec `:181` scope 에 `.agents/roles/**` 없음 · 판정 기록 `:558` L3 확인
- 위험: 문안 2벌 잔존 시 PR 3 lane 이 임의 선택

### C9 ⓑ
VERDICT: ABSORBED
- 최종 권고: T10 으로 통합(별도 항목 삭제) · 결정 입력 = L7 결과(PR 2) · 편집 = PR 3
- 반박 시도: T10 과 동일 결론 · 배치만 상이
- 위험: 없음

### C10
VERDICT: KEEP
- 최종 권고: PR 3 · migration-guard 주석 5곳(`:5·:10·:11·:55·:70` grep 실측) + 머리말 · worktree-setup `:249` 는 A7 병합 diff 뒤 재판정
- 반박 시도: V14 대상에 migration-guard.sh 없음 확인 → 미흡수 · A7 블록 `:245-267` 안에 `:249` 포함
- 위험: lane 이 `:249` 를 지우면 C10③ 일부 소멸(무해)

### C11
VERDICT: KEEP
- 최종 권고: PR 3 · ⓑ+ⓒ · 종속 4곳 · 병합 뒤 재앵커
- 반박 시도: `test_*` 2파일 PR 1 scope 확인(spec `:181`) · bootstrap-diet A7 접촉 `:23-26` 만
- 위험: 줄 번호 밀림

### T3
VERDICT: REVISE
- 최종 권고: 32 갱신 = 32 를 PR 3 전에 쓰지 않으면 PR 3 병합 뒤 1회(아니면 PR 1 뒤) · 33 은 독립 clone → archive 이동 · T9 뒤 실행
- 반박 시도: `git worktree list` 에 33 없음 → linked 아님 · T4 와 독립
- 위험: 32 용도(Codex 체크아웃 여부) 미검증

### T4
VERDICT: KEEP
- 최종 권고: ⓑ 로컬 `archive/` 태그 뒤 삭제 · 지금 실행 가능 · prune 은 현재 no-op
- 반박 시도: worktree list 에 해당 브랜치 checkout 없음
- 위험: `push --tags` 오염

### T5
VERDICT: KEEP
- 최종 권고: T3 직후 1회 · 기록은 intent 「확인」 절 · hooks.json diff 병합 뒤만 반복
- 반박 시도: 판정 기록 `:565` Claude 불요 · PR 1 hooks.json 무변경(spec `:128`)
- 위험: Codex 재신뢰 키 미검증

### T6
VERDICT: KEEP
- 최종 권고: T 제외 · PR 3 measurement-lane 항목 · L7 3회 포함
- 반박 시도: 반박 근거 없음
- 위험: advisor n<10

### T8
VERDICT: REVISE
- 최종 권고: 현재 결정 = L1 spec 1줄만 · `lifecycle prune` 미존재(grep 0건) → 나머지 전부 PR 2 병합 뒤
- 반박 시도: `lifecycle_contract.py`·`agent-bridge.py` `prune` 0건
- 위험: 옛 task 증거 참조

### T9
VERDICT: KEEP
- 최종 권고: pgrep 먼저 → mtime 필터 목록 → 승인 → 삭제 · T3 앞에 실행
- 반박 시도: T3 위험(옛 데몬 fd)이 T9 결과에 종속
- 위험: 실행 중 게이트 오삭제

### T10
VERDICT: KEEP
- 최종 권고: Bash 유지 · C9ⓐ 문안 PR 3 · 재판정 = L7 뒤 · C9ⓑ 흡수
- 반박 시도: 이 세션 도구 = Read·Bash 만 · git/gh 사실 확인에 Bash 필수
- 위험: 규율 의존

참조: spec `<repo>/.claude/worktrees/harness-improvement/dev-package/prd/specs/S-HARNESS-IMPROVEMENT-20260925.md:172,181,184` · `.agents/harness.yaml:49-62,98` · `scripts/agent-bridge.py:82-84` · intent `:546,:558-559,:565`.