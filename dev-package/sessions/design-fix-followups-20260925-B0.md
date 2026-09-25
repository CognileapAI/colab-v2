# design-fix 후속 20260925 — B0 기준 측정

spec: `dev-package/prd/specs/S-DESIGN-FIX-FOLLOWUPS-20260925.md` 부록 B(B0) · 부록 E · V11
측정 트리: 브랜치 `worktree-design-fix-followups-grill` 커밋 `78a66b82`. develop `80aa95ac` 이후 이 브랜치에서 바뀐 것은 문서(intent · spec)뿐이다 — 프론트 트리 = develop HEAD.

## 결과
- `frontend-visual`: 계 green 1 / red(판정) 0 / red(준비) 0 · exit 0.
  - task `d2162a5a36324c7bbc3c52db832f0e3f` · run `5c147ebc1fb1493885a040026c56d260` · gate-summary 는 Git common dir `colab-harness/c6d644755625b30347303841b6060683/d2162a5a36324c7bbc3c52db832f0e3f/5c147ebc1fb1493885a040026c56d260/gate-summary.json`.
  - 실행기 요약 줄: 「frontend-visual green — 페이지 48건 · 13px 미만 0건 · 대비<4.5 0건 · 스크린샷 96장 (허용 접두사 0개)」.
  - 대상: audit 빌드(`127.0.0.1:4291` · `audit-design.html?design=full&scene=<장면>`) · `scenes.json` 34장면 × 라이트/다크 = 68 URL 선언.
- 캡처 기준: `frontend/.visual/fixfu0925-base/`(무시 파일) · png 202장 + `index.json`. 34장면 중 `gnb-more` 는 정의상 375 · 768 폭만 있어 33 × 6 + 1 × 4 = 202 — 누락 0.
- 남은 서버 · agent-browser 프로세스: 0(측정 뒤 `pgrep` 확인).

## 한계 — 판정 범위
- 선언 68 URL 중 게이트가 판정한 페이지는 **48건**이다. `live_audit.sh` 가 결과 파일 이름을 잘라(장면 이름 9자) 긴 이름 장면의 라이트 · 다크, `project-detail` · `project-dialog` 가 같은 파일 이름이 되어 결과가 덮어써졌다. 덮어써진 20 URL 은 독립 판정되지 않았다.
  - 이 결함은 하네스 intent `dev-package/intent/2026-09-25-harness-design-round-residuals.md` H1(파일 이름 절단)과 같다. 이 회차에서 고치지 않는다(범위 밖).
  - 따라서 이 보고의 「develop HEAD `frontend-visual` green」은 48페이지 범위의 주장이다. E 단계는 같은 선언으로 재어 B0 와 같은 범위끼리 비교한다.

## 보충 B0b — 업로드 진입점
- B0 는 업로드 4장면(`upload` · `upload-classify` · `upload-metadata` · `upload-link`)도 `audit-design.html?scene=<장면>` 으로 선언했다. `frontend/audit-design.tsx` 는 이 장면 이름을 처리하지 않아(`:235`–`:248` 분기 없음) 그 5페이지(다크 1 포함 · 절단 충돌 뒤)는 업로드 모달이 아니라 대체 화면을 쟀다. 업로드 장면의 진입점은 `scenes.json` 기준 `audit-upload.html`(질의 없음 · 단계는 동작으로 이동)이다.
- 보충: 같은 트리 · 같은 audit 빌드로 `audit-upload.html` 라이트 · 다크 2 URL 을 `frontend-visual` 로 한 번 쟀다(task 없음 · 오케스트레이터 실행). 계 green 1 / red(판정) 0 / red(준비) 0 · 「페이지 2건 · 13px 미만 0건 · 대비<4.5 0건 · 스크린샷 4장」 · 요약 `dev-package/reports/design-fix-followups-20260925/B0b/gate-summary.json`(생성물 · 커밋 안 함).
- 이후 단계의 선언 = 디자인 30장면 × 라이트/다크 ＋ `audit-upload.html` × 라이트/다크 = 62 URL(L2 · E 는 등록 성공 장면 URL 을 더한다). 캡처(`visual:capture`)는 `scenes.json` 진입점을 그대로 써서 이 오류와 무관하다.

## 진행 기록
- 측정 레인(`measurement-lane`)이 60턴 한도에서 최종 보고 없이 끝났다. 위 값은 오케스트레이터가 디스크(gate-summary · 실행 로그 · 캡처 폴더 · 프로세스 목록)에서 확인했다.
- `lifecycle handoff --mode complete` 는 오케스트레이터 대리 호출에서 exit 78(「missing, stale, changed-during-run or other-task evidence」)로 차단됐다. 게이트 실행 뒤 같은 체크아웃에서 캡처 · 빌드를 돌린 것이 원인으로 추정되나 확인하지 않았다. 재측정은 하지 않았다 — 측정 값은 gate-summary 에 있다.
- 게이트 보고 폴더 `dev-package/reports/design-fix-followups-20260925/B0/` 는 생성물이라 커밋하지 않는다.
