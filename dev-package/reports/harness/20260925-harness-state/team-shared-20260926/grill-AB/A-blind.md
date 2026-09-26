# A — 우려 항목(선택지만 · 초안 권고 숨김)

### A-#1
- 항목: `model.txt` 값
- ⓐ: `claude-fable-5-1`(README:108 정본 · 09-08·09-12 회차 실측 모델)
- ⓑ: `claude-opus-5-5`(회차 `5b84d899` 실측 `canonicalModel` · 8.1 USD)

### A-#1a
- 항목: #1 의 조건 — 정본 모델 접근 불가(rate limit · 권한)
- ⓐ: 러너 78(`run.sh:154-156` · `claude -p` rc≠0) · 대체 모델로 재지 않음 · #1 ⓐ 채택 시 T12 는 Fable 가용 시점까지 대기 · PR 2 회차 순서(머리 「PR 2 회차 앞 병합」)도 같이 밀림 · 모델 접근권이 없는 팀원도 같은 78
- ⓑ: 가용 모델로 정본을 바꿔 회차(= #1 ⓑ 로 전환 · `model.txt` 변경 = 해시 변경 → 재실측)

### A-#2
- 항목: PR A ∥ B 동시 open 조건
- ⓐ: A 선병합 고정 — B 는 `gates/fixtures/intent-ref/*.json` 을 바꾸므로 A 병합 전엔 집합 안(현 `gates/**`) · B 가 먼저 들어가면 A 재실측
- ⓑ: B 가 fixture 변경 커밋을 A 병합 뒤로 미룸(나머지 `scripts/harness/**` · `dev-package/**` 는 집합 밖)

### A-#3
- 항목: `:(exclude).agents/ci-producers.json` 포함 여부
- ⓐ: 포함(제안 3 · 총괄 `:224` · `:232` S-dep 회차 0 의 전제 · 「제안 2–12 전부 수용」)
- ⓑ: 제외(intent `:627` Q2 문장은 `gates/**` 만)

### A-#4
- 항목: `dev-package/reports` 뿌리
- ⓐ: 이번 PR 은 확정 3개만 · PR B 반입물의 `<repo>` 치환은 B 자신의 검사
- ⓑ: `dev-package/reports` 도 추가(`compatibility_read_roots:93` 에 이미 있음)

### A-#5
- 항목: 요약줄 모델 표기 위치
- ⓐ: 요약줄 끝 ` · 모델 <정본>`(정규식 3곳 갱신 · 회차 표 한 줄에 모델)
- ⓑ: 별도 줄만(`- 모델 —`) · 정규식 무변경

### A-#6
- 항목: `model_usage` 빈 목록
- ⓐ: 러너는 기록만 · `verify` 가 78 `model-mismatch`(정본 ∉ [])
- ⓑ: 러너가 즉시 78

### A-#7
- 항목: 기존 증거·레거시 10줄 처리
- ⓐ: 치환(results 6줄 `<repo>` · prd 4줄 `~/`)
- ⓑ: `home_path_allow` 에 실행자 홈 등재
