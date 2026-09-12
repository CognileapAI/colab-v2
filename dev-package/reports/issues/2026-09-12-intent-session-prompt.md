# 32 CoLAB-v2 · GitHub 이슈 → intent 세션 착수 프롬프트

용도 — `32 CoLAB-v2` 체크아웃(버그·개선 전용)에서 GitHub 이슈 1건(또는 같은 화면 묶음)을 `/grill-me` 로 발의(intent)까지 끌고 가는 세션의 시작 문안. 새 세션마다 복사해 붙인다.

## 착수 절차 (순서 고정)

1. 세션 루트 = `32 CoLAB-v2` (`claude` 를 그 폴더에서 실행). 훅 `bootstrap-diet.sh` 가 라운드 파일 후보를 찍지만 **이 세션은 라운드가 아니다** — 라운드 파일 대신 이 문서와 이슈 회수본을 연다.
2. `git fetch origin && git merge --ff-only origin/main` 으로 `main` 최신화. 브랜치 = `fix/issue-<N>` (bug) · `improve/issue-<N>` (개선). `lane/*`·`integration/*` 는 라운드 전용이므로 쓰지 않는다.
3. 이슈 회수본 `dev-package/reports/issues/2026-09-12-github-open-issues.md` 에서 대상 이슈 절을 읽는다. 원문 확인은 `gh issue view <N> -R CognileapAI/colab-v2`.
4. `/grill-me` 실행 — 입력 = 이슈 본문 + 재현 화면. 종료 조건 = 프론티어 공집합 · Ted 확인 문장 원문 수신.
5. `dev-package/intent/<YYYY-MM-DD>-issue-<N>-<주제>.md` 초안 작성 (`dev-package/intent/TEMPLATE.md` 양식 그대로 · `## 참조` 에 이슈 URL 추가 · `## 미해결 질문` 0건).
6. Ted 교정·승인 뒤에만 `/to-spec` → 구현. 승인 = 커밋.

## 세션 첫 메시지 (복사용)

```
32 CoLAB-v2 에서 GitHub 이슈 #<N> 을 intent 로 발의한다.
- 이슈 회수본: dev-package/reports/issues/2026-09-12-github-open-issues.md 의 #<N> 절
- 브랜치: fix/issue-<N> (origin/main 기점)
- /grill-me 로 프론티어를 비운 뒤 dev-package/intent/2026-MM-DD-issue-<N>-<주제>.md 초안을 쓴다
- 승인 전 spec·구현 금지. 라운드 파일·03-HANDOFF 통독 금지(grep 한 줄만).
```

## 묶음 후보 (같은 화면 = 한 intent 가능 · 판정은 Ted)

- 업로드 진행·취소 — #34 · #33 · #32
- 업로드 메타데이터 탭 — #31 · #24
- 미리보기 이미지·컨트롤 — #26 · #27 · #28 · #29 · #25
- 백로그(범위 밖 후보) — #12 · #11 · #10 · #30

## 규약 상기

- 상태 원본 = `dev-package/work-items.yaml`. 이슈를 WU 로 올릴지는 intent 승인 뒤 결정.
- 「AI 없이도 v2 는 완결된 제품」 · 대화형 UI 금지 · 편의 기능은 후일 묶음(`colab-rules.md §6-2`) — #29·#30 은 이 판정 대상.
- 라벨 `improvemet` 는 레포에 오타로 존재. 정정 여부 별도 판정.
