# PR #141 CI 경합 수정(F-ci) · 실브라우저 확인

- 대상: 브랜치 `worktree-wf_669944f2-38e-1` @ `02f87b40` 을 `git archive` 로 뺀 임시 트리 · audit 픽스처 `audit-upload.html`(upload-classify 계열). 픽스처의 `palettes()` 는 다음 마이크로태스크에 끝나 비활성이 1–2ms 뿐이라, 임시 트리에서만 `?paletteDelay=ms` · `?drawOk=1` 변형을 붙여 쟀다(`variant-fixture.diff` — 저장소엔 넣지 않음).
- 결과(pass 7 · fail 1):
  - 두 단추(`up-preview-draw` · `up-preview-without-grid`) 모두 비활성으로 삽입 → 팔레트 도착 시각에 활성(run B 8 s · run C 90 s 지연 모두 일치) — `run*-observer.json`.
  - 비활성 중 클릭은 그리기를 시작하지 않고 나중에 재생되지도 않음 · 활성 뒤 클릭은 `createRender` 1회 · `up-preview-image` 표시 — `runB-3/4-*.png`.
  - **fail(기존 결함)**: 비활성 단추의 겉모습이 활성과 같다 — 계산 스타일 564줄 전부 동일(커서 pointer · 불투명도 1 · 같은 채움). `.btn`·`.btn-strong`·`.btn-ghost` 에 `:disabled` 규칙이 없다(`runC-*-styles-disabled.txt` · `runC-1-disabled-light-1440.png`). 이번 수정이 만든 것이 아니라 버튼 계열 디자인 결정 사안 — 후속.
- Fable advisor ② 재확인: approve(clean).
