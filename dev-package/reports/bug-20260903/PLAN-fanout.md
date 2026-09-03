# 수정 계획 (advisor 게이트 ① 대상) — 2026-09-03

근거: recon-A-lineage.md · recon-B-preview.md · recon-C-layout.md · recon-D-scope.md (같은 폴더)

## 제약
- 다른 세션이 공유 체크아웃 `main` 에서 직접 커밋 중(staging 창 A단계, dev-package 문서). 코드 레인은 전부 `isolation: worktree` + 자기 브랜치. `dev-package/` 는 코드 레인에서 건드리지 않음. 등록은 맨 끝 한 레인, 최신 main 위 append.
- staging 미접촉. 재현·검증은 로컬 테스트로만.
- systematic-debugging: 실패 테스트 red 확인 → 최소 수정 → green. "while I'm here" 금지.

## 즉시 수정 레인 (판정 불필요 — 원인 확정)

| 레인 | 버그 | 파일 | 수정 | 테스트 |
|---|---|---|---|---|
| L-A | 3·5·7 계보 | `frontend/src/.../LineageSection.tsx`, `lineageGraph.css`, `test/lineage-graph.test.tsx` | 고정 4칸 → 존재하는 종류만 칸 생성, 화살표는 인접 칸 둘 다 있을 때만. 기존 `cols.length===4` 단언 교체 | 1-hop·루트·리프 3픽스처로 빈 칸 0·화살표 수 = 칸 수-1 |
| L-B1 | 4 + 흰 줄 | `services/viz-render/.../preview.py:142-152` | 전방 산란 → 역사상(목적지 기준) 리샘플(nearest). 출력 격자의 각 픽셀에 대해 원본 좌표 역변환 후 샘플 | 성긴 원본(126×128) → 채워진 픽셀 비율 ≥ 95% · 전결측 행 0 |
| L-B3 | 8 확대·축소 | `frontend/src/.../useZoomPan.ts:192` | maxScale 하한 보장 (예: `max(4, png/viewport)`) 또는 원본 격자 해상도 기반. 픽스처를 실측값(808/820)으로 red 확인 | maxScale ≥ 4 · 버튼 클릭 시 scale 변화 |
| L-C1 | 1·9 프로젝트 | `frontend/src/.../project.css` | `.project-page`·`.project-detail` 뿌리 규칙 추가 (catalog.css:24·detail.css:27 관례 따라 padding·max-width·카드 면) | vite `test.css.include` 에 project.css 추가 후 getComputedStyle padding > 0 |
| L-C2 | 2 간격 | `frontend/src/.../shell.css:148` | `.gnb-settings { gap: 6px }` | shell.css include 후 gap 계측 |

## 판정 필요 (advisor → Ted 묶음 질문) — 코드 착수 전
| 항목 | 쟁점 | 내 권고 |
|---|---|---|
| B-2 (6) 배경 지도 | POL-021 은 타일 서버·바탕지도 서비스 금지. 내장 해안선 오버레이는 회색지대. 스크린샷 PNG 에 안 실림 | 옵션표를 Ted 에게. 이번 회차엔 착수 안 함 |
| B-4 (13) 기본 배율 | 정본에 정의 없음. 업로드 `max-width:100%` vs 상세 `width:100%` | 두 화면 같은 규칙(컨테이너 폭 맞춤 + 비율 유지)으로 통일하고 이를 정의로 등재 제안. 구현은 작으니 이번 회차 포함 가능 |
| B-5 (14) 정체불명 | 버그 아님 가능성 큼(DEM 페이지 오독). 미리보기 머리에 데이터셋 이름·범례에 변수명 없음 | 표시 추가(L-B5)는 구현하고, Ted 에게 그 화면이 D-02 였는지 확인 |
| C-4 (15) `／` | 정본이 `.dh-sum` 을 「한 줄 요약」으로 못 박음. 표시만 분할(A안) vs 시드 수정(B안) | A안: 상세 화면에서 `／` 를 줄바꿈·불릿으로 표시 분할, 저장·목록은 그대로. 이번 회차 구현 후 Ted 검수 |
| 스크린샷 버튼 | recon 이 `ScreenshotButton.tsx:72-77` 즉시 revoke 버그 발견. Ted 미보고 | 등록만, 이번 회차 수정 안 함 (범위 유지) |

## 병렬성
L-A ∥ L-B1 ∥ L-B3 ∥ L-C1 ∥ L-C2 ∥ (L-B4+L-B5: `PreviewPanels.tsx`·preview.css 공유 → 한 레인 직렬) ∥ L-C4. 파일 겹침 0 확인됨(recon B·C).

## 이후
각 레인 산출 → advisor 게이트 ② → 통합 브랜치에 병합 → `gates/run.sh` 전체 → 대장 등록(BF-1.. + 〈308〉) → PR → 게이트 ③.
