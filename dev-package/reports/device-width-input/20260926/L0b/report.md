# 레인 보고 — L0b 캡처 수치 · 판정 · 새 장면

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 부록 I 「L0b」 행 · 구현 결정 「기준 캡처 도구」·「새 장면」 · 시험 결정 · 부록 B
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-l0b` · 기준 `15b9226c`(통합 브랜치 `claude/device-width-input-impl` 머리) · 구현 커밋 `b1c77494`
- task: `9e58483b99a840e3aab59b42ba9227c9` (게이트 `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · 범위 `frontend/scripts/visual-baseline/**` · `frontend/audit-design.tsx` · `frontend/audit-map.png` · 픽스처 2 · L0a/L0b 시험)
- 판정: **L0b 미완 — 새 장면 두 번 찍기가 차이 3장(137px × 3)으로 78 에서 멈춤(§4).** 도구 · 판정 · 대상 목록 · 장면 연결 · 시험 · 게이트는 끝남. 원인은 제품 화면의 경과 시간 글자(`dt-preview-total`)이고, 고치는 방법은 spec 에 없어 판정이 필요하다(§4-1).

## 1. 바뀐 것

| 파일 | 변경 |
|---|---|
| `frontend/scripts/visual-baseline/capture.py` | `--metrics`(캡처마다 정착 · 상태 확인 · 전제조건 뒤, 스크린샷 전에 `measure.js` → `<이름>.metrics.json` · 색인 행 `metrics` 요약 · 색인 `metricsInputs` sha256). `--metrics-only --scene <이름> --viewport <id 또는 WxH[:touch/mouse]> [--theme]`(스크린샷 · `index.json` 없음 · `run-<장면>-<뷰포트>.json` · `index.json` 있는 폴더면 78). 동작 어휘 `waitImage`(완료 · 원본 폭 > 0 · 15초) · `stable`(상자 · `data-zoom-scale` · 문서 높이가 150ms × 3회 불변 · 15초). 장면 `require`(`imageLoaded` · `box` · `exists` · 거짓이면 78). `click` 전 확인에 스크롤 영역 잘림 추가(§5-2) |
| `frontend/scripts/visual-baseline/measure.js` | 새 측정 스크립트(읽기만). 점검 도구의 측정 코드에서 네 항목을 옮김 · 절대경로 0. 대상 누름 칸(label 안 입력 = label 상자 · 13번 = 행 상자 · 상자 없음 = `box:false`) · 입력 글자 < 16 · 잘림 없는 넘침 루트 · 지도 가림(네 도구 합 · 확대 묶음 따로). 지도 장면은 지도 칸 폭(`section.pv-map`) · 계산된 `touch-action` · 뷰포트 `data-*`(끌기 축) · 배율 · 값 패널 상태 |
| `frontend/scripts/visual-baseline/judge.mjs` · `judge.d.mts` | 새 판정 스크립트(순수 함수 `judge` · `links` ＋ CLI · 종료 0/1/78). 레인 거르기 `--lane` · 장면 연결 `--links` · `--out` |
| `frontend/scripts/visual-baseline/targets.json` | 대상 목록 52(부록 B · 캡처 사각 7 · 폭 숨김 2 · 세로만 4) · `laneScenes`(부록 I) · 대상별 `scenes`(390 에서 상자를 가진 장면 · 3 · 4 번은 `catalog` 1024) |
| `frontend/scripts/visual-baseline/judge-exempt.txt` | 면제 목록(`지표 · 선택자 · 사유`) · 지금 줄 0 |
| `frontend/scripts/visual-baseline/scenes.json` | 새 장면 3(`detail-preview-map` · `detail-preview-map-value` · `upload-preview-expand` · 모두 6크기 · 질의 `{scene, design: 'full'}` · `require`) · notes 3줄. 스키마 판은 2 그대로(선택 키 추가) |
| `frontend/audit-design.tsx` | 상세 지도 두 장면 = 실제 `DatasetDetailPage` ＋ 픽스처 미리보기 원천 · 데이터셋 이름 80자(머리 · 뒤로 링크 `backLabel`) · 파일 경로 72자. 확장보기 장면 = `PreviewPanel` 단독(`STANDALONE` 에 더함 · 맨 위 메뉴 없음) |
| `frontend/src/components/datasetpreview/fixture.ts` · `frontend/src/components/upload/fixture.ts` | 새 픽스처 원천 2(타이머 0 · 팔레트 3 · 파일 1 · 변수 1(38자) · 만들기 = 그리는 중 → 첫 조회 완료 · 범례 6구간 · 값 조회 고정 0.0412). 이름이 `fixture.ts` 라 `frontend-fixture-reach` 금지 목록에 걸린다(운영 진입점 도달 0 · §3) |
| `frontend/audit-map.png` | 새 그림 1장(1024x833 · 33,303 B · 점검 하네스 그림 그대로 · 합성 등고 무늬) |
| `frontend/test/device-width-input-20260926-L0b.test.ts` | 새 시험 53사례 |
| `frontend/test/device-width-input-20260926-L0a.test.ts` | 「기존 장면」 단언 2개(장면 35 · 캡처 414)를 새 장면 3을 뺀 집합으로 센다. 단언 삭제 0 · 기대값 불변(§7) |

제품 화면 코드(`frontend/src` 의 픽스처 밖) 변경 0.

## 2. 시험 RED → GREEN

- RED ①(시험만 · 구현 0): `Failed to resolve import "../scripts/visual-baseline/judge.mjs"` — 파일 전체 적재 실패. 같은 실행에서 L0a 17건 통과.
- RED ②(판정 스크립트 · 대상 목록 · 픽스처만 있음): `Tests  12 failed | 41 passed (53)` — 예: `expected 35 to be 38`(장면 목록) · `module 'capture' has no attribute 'check_require'` · `ENOENT … measure.js` · 스크롤 영역 잘림 `expected [] to deeply equal [ { block: 'nearest', … } ]` · 장면 연결 `expected [ 1, 2, 5, … ] to deeply equal []`.
- GREEN: `Tests  70 passed (70)`(L0b 53 ＋ L0a 17). 장면 연결 2사례는 390 실측으로 `targets.json` 의 `scenes` 를 채운 뒤 green(§5).
- 시험이 잠근 것: 대상 길이 먼저(52 · 사각 7 · 폭 숨김 2 · 세로만 4 · 레인 L1 3 · L2a 9 · L2b 34 · L3b 2 · — 4) · 레인 장면 · 장면 38 · 캡처 450 · 모든 행 `query` · 새 장면 동작 · 전제조건 · audit-upload 잠금 거르기 불변 · 픽스처 원천(긴 이름 80 · 72 · 38 · 팔레트 3 · 첫 조회 완료 · 타이머 0) · 판정 픽스처(44 · 50–53 세로만 · 1–49 우선 · 「재지 않음」 · 16 · 넘침 · 마우스 캡처 · 가림 332/809/810/1190 · 판정 장면 지도 칸 폭 없음 78 · 확장보기 폭 없음 허용 · 장면 선언 대상 모두 불일치 78 · 레인 거르기(밖은 개수만 · 재지 않은 레인 대상 78 · 사각 제외 · 폭 숨김 1024 보충 · 가림은 L1 만) · 모르는 레인 78) · 면제 목록(형식 · 빈 사유 · 모르는 지표 · 구멍 red · 적중 개수 · 찍을 때 목록과 다르면 78) · `links` · CLI 0/1/78 · `waitImage` · `stable` · `require` · `parse_viewport` · 스크롤 영역 잘림.
- 기존 업로드 잠금 시험(`design-fix-followups-20260925-L2.test.tsx`) · `visual-diff.test.ts` 수정 없이 green.

## 3. 게이트(task 실행 · 호스트 단독)

| 게이트 | 결과 |
|---|---|
| `frontend-typecheck` | green — `tsc --noEmit` 오류 0 |
| `frontend-test` | green — 147파일 1963건 통과 · 실패 0(L0a 끝 1910 ＋ L0b 53) |
| `frontend-fixture-reach` | green — 도달 209 · 금지 모듈 0(새 `fixture.ts` 2개 도달 0) |
| 계 | green 3 / red(판정) 0 / red(준비) 0 |

- `audit-design.tsx` 는 위 게이트의 `tsconfig.json` 범위 밖이다. `tsc --noEmit -p tsconfig.audit.json` 을 따로 돌려 오류 0 을 확인했다(`visual:capture` 의 빌드도 같은 검사를 한다).
- 이 보고서 커밋 뒤 같은 명령으로 한 번 더 돌려 인계한다(gate-summary 경로는 인계 메시지).

## 4. 새 장면 두 번 찍기(`dwi0926-det-c` 대 `dwi0926-det-d`) — 78 · 멈춤

| 실행 | 결과 |
|---|---|
| `capture.py --label dwi0926-det-c --only <새 3> --metrics`(audit 빌드 포함) | 종료 0 · 36장 · `gitHead b1c77494` · `gitDirty false` · 199초 |
| `capture.py --label dwi0926-det-d --only <새 3> --metrics --skip-build` | 종료 0 · 36장 · 같은 HEAD · 깨끗함 · 191초 |
| `diff.mjs det-c det-d` | **종료 1 · 36장 중 차이 3장 · 엄격 픽셀 411(137 × 3)** · 같은 HEAD(불안정 장면) |

- 차이 장면: `detail-preview-map-dark-844x390` · `detail-preview-map-value-light-1440` · `detail-preview-map-value-dark-820`(모두 137px). 나머지 33장 차이 0. `upload-preview-expand` 12장 차이 0.
- 원인(실측 · 두 PNG 같은 자리 확대): 「보기」 아래 `총 0.0초` 대 `총 0.1초`. 제품 코드 `components/datasetpreview/DatasetPreviewSection.tsx` 의 `dt-preview-total`(`performance.now()` 로 잰 「보기 → 그림 표시」 실제 경과 시간 · 소수 첫째 자리)이다. 픽스처는 타이머가 없고 첫 조회에 완료하지만, 그림 디코드까지의 실제 시간이 0.05초 경계를 오가면 글자가 바뀐다.
- spec 대조: 부록 I L0b 「새 장면 3 × 12 = 36장 픽셀 차이 0 · 아니면 장면을 적고 78로 멈춤」. spec 의 원천 조건(타이머 없음 · 첫 조회 완료)만으로는 이 글자를 고정할 수 없다. 레인은 고치지 않았다.

### 4-1. 판정 필요(레인 선택지 · 모두 제품 화면 코드 변경 0)

- ⓐ 두 상세 지도 장면에서 `[data-testid=dt-preview-total]` 을 `visibility: hidden` 으로 가린다(자리 · 높이 유지 · 그 글자 픽셀만 사라짐). 방법: `audit-design.tsx` 가 두 장면에서만 스타일 1줄을 넣거나, 장면 목록에 가림 선택자 키를 두고 `capture.py` 가 넣는다.
- ⓑ `audit-design.tsx` 에서 두 장면의 `performance.now` 를 고정 값 증가로 바꾼다 — 확대 · 이동 관성(`useZoomPan`)도 같은 시계를 써 동작이 바뀔 수 있다(권하지 않음).
- ⓒ 반복 두 번 찍기로 재시도한다 — 결정성 증명이 아니다(권하지 않음).
- 레인 권고: ⓐ(측정 대상이 아닌 실시간 글자만 가리고 배치 · 수치는 그대로).

## 5. 대상 목록의 장면 연결 — 종료 0(통과)

- 실행: 레인 장면 25개(부록 I 합집합) × 390 × 라이트, `--metrics-only` 직렬 25회 · 157초 · 전부 종료 0. 폭 숨김용 `catalog` × 1024 1회.
- `judge.mjs --links`: `scenes=25 missing=- declaredNotDrawn=0 exit=0`. 레인 L1–L3b 이고 캡처 사각 · 폭 숨김이 아닌 대상 39개(L1 3 · L2a 7 · L2b 27 · L3b 2)가 모두 자기 레인 장면에서 390 상자를 가졌고, 50–53 은 레인 장면에 있다. `targets.json` 의 `scenes` 를 이 결과로 채웠다(3 · 4 번 = `catalog` · 1024 실측 110x34 · 86.3x36 · 390 은 `box:false`).
- 가장 좁은 연결: 23 → `preview` · `preview-done` · 30 → 새 지도 장면 3 · 36 → `members` · 45 → `detail`(L3b 장면) · `upload-metadata` · 13 · 14 → `catalog` · 18 → `search` · 21 → `not-found` · 38 → `login` · 43 · 44 → `upload-metadata` · 46 → `upload-link`.

### 5-2. click 전 스크롤 — 스크롤 영역 잘림(L0a 남은 위험 · advisor 메모)

- 창 확인에 더해, 대상이 창 안이어도 overflow 가 visible 이 아닌 조상(고정 위치 경계까지)에 잘리면 `scrollIntoView({block: 'nearest', inline: 'nearest'})` 한다. 다 보이면 스크롤 0. 시험 3사례(잘림 없음 0 · 잘림 1 · 영역 안 0) ＋ L0a 5사례 그대로 green.
- 기존 장면 영향: 클릭이 있는 기존 7장면(`project-table` · `approval-dialog` · `upload-classify` · `upload-metadata` · `upload-link` · `upload-register-ok` · `gnb-more`) 78장 캡처(`dwi0926-l0b-clickscenes`) → 스크롤 6회 · 모두 `click [data-testid=reg-open]`(L0a 와 같은 6회). 확장이 기존 클릭을 바꾸지 않았다.
- 새 장면의 스크롤 36회(det-c)는 「보기」 · 지도 뷰포트가 창 아래에 있어서다. 새 장면 클릭 대상 중 스크롤 영역에만 잘린 것이 있었는지는 따로 재지 않았다(결과 문자열이 창 · 영역을 가르지 않음).

## 6. 판정이 red 를 낼 수 있다는 시연(현재 트리 · B0 아님)

- 입력: §5 의 390 라이트 25장 ＋ `catalog` 1024 1장(26 파일). `judge.mjs`(거르기 없음) → **종료 1 · red 178 · 준비 0** · 「재지 않음」 56 · 캡처 사각 7 · 목록 밖 작은 누름 칸 9.
  - 44: 166건(예: 29번 `.pv-pick-values summary` 358x20.8 · 23번 뒤로 링크 94.9x22.4).
  - 가림: `detail-preview-map` 390 **100%**(지도 칸 332 · 범례 87 · 값 조회 12.2 · 좌표 5 · 스크린샷 5.3 · 확대 묶음 20.5 기록) · `detail-preview-map-value` 390 84% · `preview-done` 390 14.7%(지도 칸 358). `upload-preview-expand` 390 은 기록만(네 도구 0 · 지도 칸 없음).
  - 넘침: 새 상세 지도 두 장면 390 에서 루트 2개씩 — 파일 경로 72자 `dh-file`(오른쪽 539) · `preview-target-file`(501). 나머지 23장면(기존 22 ＋ 확장보기) 390 넘침 0 · 25장면 390 16 미만 0(점검 기록과 같음).
  - 16: `catalog` 1024 에서 5건(맨 위 메뉴 테마 선택 13px · 목록 거르기 선택 14px × 4).
- `judge.mjs --lane L1`(L1 장면 6 파일) → 종료 1 · red 14 · 밖 red(44) 41건.
- 점검 대표값 대조: 390 범례 87% 가 점검(`dev-package/reports/responsive-audit/20260925/`)과 같다.
- 값 결과 장면 390 의 「지도 중심 누름」은 지도 한가운데의 「확대」 단추가 받았다(배율 0.742 → 1.484 · 값 패널 「안내」 유지). 지금 트리에서 탭이 조회에 닿지 않는다는 V4 전제와 같다.

## 7. 이탈 · 결정 · 남은 것

- 미완: 새 장면 두 번 찍기 픽셀 0(§4 · 판정 뒤 재실행).
- 이탈 · 레인 결정(spec 빈칸):
  - 넘침 측정: 점검 코드의 「창 오른쪽을 넘는 상자의 잘림 없는 루트」만으로는 긴 이름 글자 넘침(문서 폭 539 · 넘는 상자 0)을 못 잡았다. 자기 상자보다 넓은 내용(`scrollWidth` · overflow-x visible)이 창을 넘는 가장 안쪽 요소도 루트로 세고, 그래도 없는데 문서가 옆으로 스크롤되면 `html` 을 루트로 센다.
  - 값 결과 장면의 「값 결과를 기다린다」는 값 글자 대기가 아니라 값 패널 `stable` 로 했다 — B0 에서는 값이 오지 않는 것이 기대(V4 「전에는 안내 문장」)라 값 대기는 B0 를 78 로 막는다.
  - 면제 목록 선택자는 캡처 때 측정 스크립트가 요소에 맞춘다. 수치 파일에 찍을 때 목록을 적고, 판정 때 목록과 다르면 78. 구멍(맞는 것 없는 줄)은 거르기 없는 실행에서만 red, 레인 거르기 실행에서는 `exemptUnused` 로만 낸다(다른 레인 장면의 줄이 구멍으로 보이기 때문).
  - 레인 대상 미측정 78 은 레인 거르기 실행에서만 판정한다(B0 · E 의 507x820 단독 판정이 78 로 막히지 않게).
  - 장면 선언 대상 불일치 78 은 터치 캡처에만 적용한다(마우스는 대상을 재지 않음).
  - 수치 전용 실행에 `--theme` 선택을 더했다(장면 연결은 라이트만 잼).
  - 수치 파일 추가 기록: 잘린 넘침 루트 5개(`clipped`) · 지도 배율(`zoom`).
- L0a 시험 수정: 「기존 장면 캡처 수 = 414」 · 「장면 35」 두 단언을 `EXISTING`(새 3 제외) 기준으로 셈 — spec 이 기존 414 ＋ 새 36 = 450 을 정했으므로 뜻은 그대로다.
- 부록 H(게이트 면제 24건)는 L4 의 디자인 검사 면제 목록이라 이 레인의 판정 면제 목록과 다르다 — 쓰지 않았다.
- 후속:
  - `DatasetPreviewSection` 의 경과 시간 글자는 캡처 결정성을 깬다 — 어느 게이트에도 걸리지 않는다(§4-1 판정 대상).
  - agent-browser 0.27.0 의 「daemon already running」 경고는 L0a 보고와 같다(동작 영향 없음).
- 캡처 폴더(추적 제외 · `frontend/.visual/`): `dwi0926-det-c` · `dwi0926-det-d` · `dwi0926-det-cd-diff` · `dwi0926-l0b-links` · `dwi0926-l0b-links-1024` · `dwi0926-l0b-clickscenes` · `dwi0926-l0b-smoke`. agent-browser 세션은 도구가 만든 이름(`vb-…`) · 시험용 `l0b-abtest` · `l0b-probe` 만 쓰고 그것만 닫았다.
