# B — 우려 항목(선택지만 · 초안 권고 숨김)

### B-#1
- 항목: legacy 63건 전환 규칙
- ⓐ: 형식 OR (legacy ∧ 동결 스냅샷 `intent_legacy_approved.txt` · base 1회 생성 · 도입 뒤 불변(차이 red) · 영구)
- ⓑ: 형식만 · legacy 63건은 비보호로 두고 필요 시 새 intent 재발행

### B-#2
- 항목: handle 검증
- ⓐ: 형식만(GitHub login 정규식 · 네트워크 0 · 토큰 0)
- ⓑ: `gh api users/<handle>` 실재 확인

### B-#3
- 항목: ADR 기록
- ⓐ: ADR-0007 「결과와 감수한 비용」 끝에 날짜 줄 1개 추가(ADR-0003 `:35` 「2026-09-17 추가 —」 선례 · 기존 줄 무수정 · 번호 0011/0012 무영향)
- ⓑ: 새 ADR-0013(0011·0012 는 PR 2·4 예약 · 병합 순서와 번호 역전)

### B-#4
- 항목: `2026-09-08-harness-evals.md`(실승인 · 메타 「미승인」 · v1 `:13-15` 의도된 비보호)
- ⓐ: 그대로(비보호 유지 · 사람이 원하면 새 꼴로 메타 줄 수정 = 미승인이라 편집 가능 · 날짜는 수정 커밋일)
- ⓑ: 스냅샷에 예외로 넣어 보호

### B-#5
- 항목: 반입 보고서의 홈 경로 검사
- ⓐ: 이 PR = grep 검사 · `home_path_roots` 는 A 의 `.agents/harness.yaml` 몫 → A 에 `dev-package/reports/harness` 1토큰 추가(같은 파일 · 같은 회차 · 단 기존 `dev-package/reports/**` 에 홈 절대경로(`HOME_PATH` 꼴 · `scripts/harness/config.py:29-33`) 잔존 0 확인 뒤)
- ⓑ: B 에서 `harness.yaml` 수정

### B-#6
- 항목: `~/.claude/...` 상대 표기 40곳
- ⓐ: 원문 유지 + README 대응 1줄
- ⓑ: 반입 경로로 재작성
