# 디자인 구조 P2a 결과 — 보정 층 `design-system.css` 흡수 · `@layer` 도입

spec: `dev-package/prd/specs/S-DESIGN-STRUCTURE-P2A-20260924.md` · 조사: `p2/design-system-map.md` · 선행: `p0/report.md` · `p1/report.md`

착수 HEAD `7967e001` · task `b3a0acddb8904144b566f2539b3f93fb` · 레인 1(직렬)

## 진행 상태

| 단계 | 상태 |
|---|---|
| 1 착수 캡처 `p2a-before` | 완료 |
| 2 판정 도구 `cascade-map.mjs` · 지도 | 완료(`088f6be6`) |
| 3 흡수 · `design-system.css` 삭제 | 진행 전 |
| 4 `@layer` · 게이트 d 범위 · lint 사각 3건 | 진행 전 |
| 5 vitest 껍질 제거 플러그인 · 시험 경로 | 진행 전 |
| 6 상태 계측 | 진행 전 |
| 7 시각 변경 0 | 진행 전 |
| 8 게이트 | 진행 전 |

## 단계 1 — 착수 캡처

- `npm run visual:capture -- --label p2a-before`(audit 빌드 포함) · 03:52:40~04:00:59 UTC · PNG 196장 + `index.json`(`captureCount` 196 · 명세 sha256 `d6983d71…` · HEAD `7967e001` · 미커밋 변경 없음 · 빌드 포함).
- 같은 빌드 산출물을 `frontend/.visual/p2a-dist-before/` 로 복사해 두었다(상태 계측·계산값 전수 대조의 「전」 쪽 · 로컬만).

## 단계 2 — 판정 도구

- `frontend/scripts/cascade-map.mjs`(의존성 0). `map` = 착수 트리의 규칙 1307개(19파일 · 적재 순서대로)에서 `design-system.css` 192규칙을 (선택자 인자 × 선언) 621단위로 풀어 경쟁 규칙·오늘의 승자·되살아남 후보를 낸다. `verify --base <rev>` = 흡수 뒤 작업 트리에서 DS 선언마다 새 자리(같은 선택자 인자·미디어·속성·값)를 찾고 경쟁 결과를 새 위치·특이도로 다시 계산해 뒤집힘을 낸다.
- 산출: `p2a/cascade-map.md` · `p2a/cascade-map.json`(조사 부록 A 를 대체).
- 착수 트리 합계: 선언 단위 621 · 오늘 지는 단위(키 공유 경쟁 · 값 다름) 40 · 되살아남 후보(키 공유) 348 = 필연 52 · 순서 236 · 순서(셸 본문) 28 · DS쌍 32 · 그중 상태 선택자 4(`.btn-primary:hover` · `.inp[readonly]` 배경·색 · `.login-input:focus-visible`) · 요소/전체 compound 호환 후보 6909(표 밖 · 렌더 장면 계산값 전수 대조로 확인).
- `순서` 후보는 새 위치에 달려 있다 — 실제 뒤집힘은 흡수 뒤 `verify` 가 정한다.
