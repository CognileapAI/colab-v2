# 단계 보고 — B0 기준 캡처(측정만 · 코드 변경 0)

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 부록 I 「B0」 행 · 「레인 확정」 절
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-b0` · 기준 `f869cfc1`(통합 브랜치 `claude/device-width-input-impl` 머리)
- task: `011b43c31c2142bb955a8667fd2da227`(게이트 `frontend-visual` · 범위 이 보고 폴더)
- 판정: **B0 완료.** 450장 기준 캡처(수치 모드) · 다시 빌드한 두 번째 캡처와 차이 0 · 507x820 수치 전용 4파일 · 판정 red(기대 결과) · `frontend-visual` green.
- 바뀐 파일: 이 보고 1개. 제품 코드 · 도구 · 시험 · 장면 목록 변경 0.

## 1. 측정한 트리

| 항목 | 값 |
|---|---|
| 커밋 | `f869cfc1be60f12d01b2bb9c0e57eb7113708968` |
| 트리 | `4d29d11495c205a23e7b7241cc2a64b3cbcb3345`(task begin 의 `started_identity.tree` 와 같음) |
| 작업 사본 | 추적 파일 깨끗함 · 두 캡처 색인 모두 `gitDirty false` |
| 장면 목록 sha256 | `dbe3db01f40576a6c387232aaae4dfa27e7ee86a158129a8d08dcd7aa5cf1a2e` |
| 수치 입력 sha256 | `measure.js` `7fbcbb7e…` · `targets.json` `30f6c511…` · `judge-exempt.txt` `bc4130fd…`(두 캡처 같음) |
| 준비 | `frontend/` 에서 `npm ci` 종료 0 · agent-browser 0.27.0 · node 22.22.1 |

## 2. 캡처(추적 제외 · `frontend/.visual/` · 이 워크트리에 보존 · E 의 기준)

| 폴더 | 명령 | 결과 | 시간 |
|---|---|---|---|
| `frontend/.visual/dwi0926-base` | `capture.py --label dwi0926-base --metrics`(audit 빌드 포함 · 병렬 2) | 종료 0 · 450장 · 수치 파일 450 · `click` 스크롤 42회 | 1419초 |
| `frontend/.visual/dwi0926-base-rebuild` | `capture.py --label dwi0926-base-rebuild --metrics`(**다시 빌드** · `--skip-build` 없음) | 종료 0 · 450장 · 수치 파일 450 · `click` 스크롤 42회 | 1436초 |
| `frontend/.visual/dwi0926-base-507` | `capture.py --label dwi0926-base-507 --skip-build --metrics-only --scene <장면> --viewport 507x820`(장면 `detail-preview-map` · `detail-preview-map-value` × 테마 2) | 두 실행 종료 0 · 수치 파일 4 · `run-*.json` 2 | 9초 · 12초 |

- 450 = 기존 34장면 × 12 ＋ `gnb-more` 6 ＋ 새 장면 3 × 12. 색인 `captureCount` 450 · 장면 38.
- 스크롤 42회 = 업로드 3장면 × 2테마 × 844x390 의 `reg-open`(L0a 와 같은 6회) ＋ 새 지도 · 확장보기 장면 36회(L0b §5-2 와 같음).
- 507x820 은 두 번째 캡처의 빌드(같은 커밋 · §3 에서 차이 0)를 썼다.

## 3. 빌드 결정성 — 차이 0

| 대조 | 결과 |
|---|---|
| `diff.mjs dwi0926-base dwi0926-base-rebuild`(보고 `frontend/.visual/dwi0926-base-rebuild-diff`) | **종료 0 · 450장 · red 0 · 엄격 픽셀 0** |
| `diff.mjs --viewport 1440`(보고 `frontend/.visual/dwi0926-base-rebuild-diff-1440`) | 종료 0 · 74장 · 엄격 픽셀 0 |
| 수치 파일 450개 바이트 대조(`diff -rq` · PNG · `index.json` 제외) | 차이 0 |

- 두 번째 캡처는 audit 빌드를 새로 만들었다. 같은 커밋에서 빌드를 다시 해도 캡처 · 수치가 바뀌지 않는다. E 의 `dwi0926-final`(새 빌드)을 이 기준과 그대로 대조할 수 있다.

## 4. 판정 스크립트(레인 거르기 없음 · 기대 결과 red)

- 명령: `node scripts/visual-baseline/judge.mjs --out <보고> frontend/.visual/dwi0926-base frontend/.visual/dwi0926-base-507`
- 결과: **종료 1** · 파일 454 · **red 4166** · 준비 0 · 「재지 않음」 654 · 캡처 사각 7 · 면제 적중 0 · 면제 구멍 0 · 목록 밖 작은 누름 칸 90.
- 참고: 450장만 판정 → 종료 1 · red 4110(44 3132 · 16 952 · 넘침 8 · 가림 18).
- spec 기대(V3 · V7 「B0 에서는 0보다 커야 한다」 · 시험 결정 「B0 판정이 red(가림 · 작은 누름 칸 > 0)」): 가림 22 > 0 · 44 3180 > 0. 충족.

### 4-1. 지표별 red

| 지표 | red | 뷰포트별 |
|---|---|---|
| 44(누름 칸) | 3180 | 390 384 · 844x390 592 · 820 592 · 1024 782 · 1180 782 · 507x820 48 · 1440 0(마우스는 대상을 재지 않음) |
| 16(입력 글자) | 952 | 390 0 · 507x820 0 · 844x390 240 · 820 240 · 1024 236 · 1180 236 |
| 넘침(루트) | 12 | 390 8 · 507x820 4 · 나머지 0 |
| 가림(네 도구 합) | 22 | 390 6 · 844x390 6 · 820 6 · 507x820 4 |
| 면제 | 0 | 면제 목록 줄 0 |

### 4-2. 44 — 레인별(부록 B 레인 열)

| 레인 | red 캡처 수 | red 대상 수 / 레인 대상 | red 가 없는 대상 |
|---|---|---|---|
| L1 | 226 | 3 / 3 | — |
| L2a | 1590 | 9 / 9 | — |
| L2b | 1200 | 24 / 34 | 13 · 37 · 38 · 캡처 사각 15–17 · 28 · 47–49 |
| L3b | 164 | 2 / 2 | — |
| —(50–53 · 세로만) | 0 | 0 / 4 | 50–53 |

- 대상별 390 대표값(예): 1 번 26x26 · 5 번 36x44 · 23 번 94.9x22.4 · 29 번 358x20.8 · 36 · 45 번 13x13 · 39 번 19.3x21.
- 390 에서 red 가 없고 넓은 터치 크기에서만 red 인 대상: 2 · 3 · 6 · 7 · 10 · 14 · 30 · 34 · 46. 3 · 4 번(폭 숨김)은 1024 · 1180 에서 red.

### 4-3. 16 · 넘침

- 16: 모두 820 이상 터치 크기다(390 · 507x820 은 0 — 부록 G 의 하한 규칙이 640px 이하 조건 안에만 있음과 일치). 많은 선택자: 맨 위 메뉴 테마 선택 228 · 프로젝트 도구줄 선택 96 · 미리보기 조작 선택 32 · 업로드 파일 선택 32 · 팔레트 선택 32 · 구간 수 입력 32 · 연구실 검색 입력 28.
- 넘침 루트: 새 상세 지도 두 장면에서만. `dh-file`(상세 머리 파일 경로 · 390 4 · 507x820 4) · `preview-target-file`(390 4). 나머지 36장면 모든 크기 0.

### 4-4. 가림(네 도구 합 % · 지도 칸 폭 < 810 판정 장면)

| 장면 | 390 | 507x820 | 844x390 | 820 |
|---|---|---|---|---|
| `detail-preview-map` | 100(칸 332) | 56.4(칸 449) | 13(칸 754) | 14.2(칸 730) |
| `detail-preview-map-value` | 84(칸 332) | 61.3(칸 449) | 17.5(칸 754) | 19.2(칸 730) |
| `preview-done` | 14.7(칸 358) | — | 14.7(칸 780) | 14.7(칸 756) |

- 두 테마 같은 값. 기록만(칸 ≥ 810): `detail-preview-map` 1024 6.7 · 1180 4.1 · 1440 3 / `detail-preview-map-value` 1024 8.8 · 1180 5.1 · 1440 3.6 / `preview-done` 1024 · 1180 · 1440 14.7. 상세 두 장면의 1024 · 1180 은 V3 기대값 12% 이하 안.
- 확대 묶음(기록만): `detail-preview-map` 390 20.5 · 507x820 10.3 · 844x390 1.9 · 820 2. `upload-preview-expand` 네 도구 0(지도 칸 없음 · 기록만) · 확대 묶음 844x390 15.9.
- 모든 지도 캡처의 뷰포트 `touch-action` = `none` · 끌기 축 기록 없음.

## 5. 값 결과 장면 `map.valueState`(`detail-preview-map-value`)

| 뷰포트 | 라이트 | 다크 |
|---|---|---|
| 390 | 안내 | 안내 |
| 507x820 | 안내 | 안내 |
| 844x390 | 값 | 값 |
| 820 | 값 | 값 |
| 1024 | 값 | 값 |
| 1180 | 값 | 값 |
| 1440 | 값 | 값 |

- `detail-preview-map`(탭 없음)은 모든 크기 「안내」.
- 390 · 507x820 은 지도 중심 탭이 조회에 닿지 않는다(L0b §6: 중심의 「확대」 단추가 받음). V4 의 「전에는 안내」와 같다.

## 6. `frontend-visual`(장면 URL 선언 · 면제 없음)

- URL 22건 = 부록 I L1–L3b `frontend-visual` URL 합집합 21장면(`detail` · `preview` · `preview-done` · `detail-preview-map` · `detail-preview-map-value` · `upload-preview-expand` · `primitives` · `catalog` · `gnb-more` · `login` · `not-found` · `search` · `search-down` · `lab` · `projects` · `project-detail` · `project-dialog` · `settings` · `members` · `account-admin` · `lineage-picker` · 각 `audit-design.html?scene=<장면>&design=full`) ＋ 업로드 입구(`audit-design.html` · 장면 목록의 `upload` 질의가 비어 있음).
- 제공: `frontend/` 에서 `vite preview --config audit.vite.config.ts --host 127.0.0.1 --port 47391 --strictPort`(캡처 도구와 같은 audit 빌드).
- 명령: `COLAB_VISUAL_URLS=<22건> COLAB_TEST_ENV_FILE=~/.colab-v2-test-32.env COLAB_TASK_ID=011b43c31c2142bb955a8667fd2da227 bash gates/run.sh task`

| 실행 | 결과 |
|---|---|
| 1회 | **red(준비) 1** · 종료 78 — 호스트 뮤텍스 대기 928초 > 상한 900초(다른 체크아웃의 게이트가 잡고 있었음 · 판정하지 않음) |
| 2회(뮤텍스가 빈 뒤 · 같은 입력) | **green 1 / red(판정) 0 / red(준비) 0** — 페이지 22건 · 13px 미만 0 · 대비 < 4.5 0 · 스크린샷 44장 · 허용 접두사 0 |

- 이 게이트는 1440x900 · 읽기 전용이다. `gnb-more` 는 클릭 없이 연 화면(더보기 메뉴 닫힘)을 잰다.
- 보고서 커밋 뒤 같은 명령으로 한 번 더 돌려 인계한다(gate-summary 경로는 인계 메시지).

## 7. 예상과 다른 것 · 후속

- 16 red 952 가 모두 820 이상 터치 크기에 있다. V8 은 터치 5크기 모두 0 을 요구하는데, 레인 자기 게이트는 390 수치 전용 실행만 판정한다 — 820 · 844x390 · 1024 · 1180 의 16 은 E 의 거르기 없는 판정에서만 드러난다.
- 값 결과 장면은 844x390 이상에서 이미 「값」이다. V4(390 탭 도달)의 전후 대조 대상은 390 이다.
- 507x820 가림은 56.4 · 61.3 이다. spec 문제 진술 · 부록 K 의 507 66.3% 는 점검 하네스 수치이고 이 도구의 픽스처 장면 값과 다르다(기록만).
- `preview-done` 가림은 1024 · 1180 · 1440 에서도 14.7 이다(칸 ≥ 810 · 기록만).
- 캡처는 호스트 뮤텍스를 쓰지 않는다. 두 캡처 중 다른 세션의 부하 유무는 재지 않았다(두 캡처 차이 0).
- agent-browser 세션: 캡처 도구가 만든 실행별 이름(`vb-…`)과 게이트 판정부의 `la-…` 만 쓰였고 각 도구가 닫았다. 직접 연 세션 0.
- 작업용 파일(추적 제외 · `frontend/.visual/dwi0926-b0-work/`): 판정 보고 JSON · 로그 · 요약 스크립트 · 게이트 실행 래퍼.
- (오케스트레이터 추기 · advisor ② 후속) 미리보기 서버 종료에 쓴 `pkill -f 'vite preview --config audit.vite.config.ts --host 127.0.0.1 --port 47391'` 은 이 레인이 띄운 고유 포트 한 개만 맞는다. 다른 세션 서버 · agent-browser 세션(`dev-op-501` · `dev-test-admin` · `default`)은 살아 있음을 확인했다. 이후 레인은 시작 때 저장한 PID 로만 종료한다.
