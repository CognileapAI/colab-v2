# 레인 보고 — L0a 캡처 도구 틀(뷰포트 · 입력 방식 · 상태 확인 · 비교 거르기 · 두 번 찍기)

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 부록 I 「L0a」 행 · 구현 결정 「기준 캡처 도구」
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-l0a` · 기준 `8f754850` · 구현 커밋 `a6514f3d`
- task: `309102ffcc9c4c9e9417847ba6cb4bf1` (게이트 `frontend-typecheck` · `frontend-test` · 범위 `frontend/scripts/visual-baseline/**` · L0a 시험 파일)
- 판정: **L0a 미완 — 두 번 찍기가 캡처 단계에서 78 로 멈춤(§5).** 도구 · 시험 · 게이트 · 상태 확인 78 증명은 끝남.

## 1. 바뀐 것

| 파일 | 변경 |
|---|---|
| `frontend/scripts/visual-baseline/scenes.json` | 스키마 `colab-visual-scenes/2`. 최상위 `viewports` 6(390 · 844x390 · 820 · 1024 · 1180 터치 · 1440 마우스 · spec 조각 그대로). `viewport.height` 900 삭제 · `deviceScaleFactor` 1 최상위. 장면 `widths` 삭제 · 기본값 전체 6 · `gnb-more` 만 `viewports: ["390","844x390","820"]`. `browser.inputArgs`(touch: pointer coarse · hover none · 터치 이벤트 · 스크롤바 숨김 / mouse: pointer fine · hover) — 명세 sha256 이 입력 설정까지 잠근다. notes 2줄 |
| `frontend/scripts/visual-baseline/capture.py` | 입력별 실행 래퍼 2개(Chrome ＋ `browser.args` ＋ `inputArgs`)를 공백 없는 임시 폴더(`tempfile.mkdtemp`)에 쓰고 `--executable-path` 로 넘김 · 브라우저 실행 파일 없음 78. 세션 = 테마 × 입력(4) · `--parallel` 1–4(기본 2 유지). 상태 확인에 창 높이 · `(pointer: coarse)` · `(hover: hover)` 추가 · 어긋나면 78. 명세 검사(스키마 판 · id 중복 · 알 수 없는 뷰포트 · 남은 `widths`) 78. 파일 이름 `<장면>-<테마>-<뷰포트 id>.png` · 색인 `colab-visual-index/2` · 행에 `viewport` · `height` · `input`. `--force-input` = 상태 확인 78 증명용 |
| `frontend/scripts/visual-baseline/diff.mjs` | `--viewport <id>[,<id>]` 거르기(양쪽 · 장면 · 명세 검사 뒤) · 고른 캡처 0장 78 · 보고 `viewportFilter` · 행 `viewport` |
| `frontend/test/device-width-input-20260926-L0a.test.ts` | 새 시험 12사례(스키마 6 · 거르기 픽스처 CLI 6) |

제품 코드(`frontend/src`) 변경 0. 기존 시험 · 픽스처 변경 0.

## 2. 시험 RED → GREEN

- RED(구현 전): `Tests  9 failed | 3 passed (12)` — 예: `expected 'colab-visual-scenes/1' to be 'colab-visual-scenes/2'`, `expected 420 to be 414`, 거르기 ② `expected 78 to be +0`(옛 diff.mjs 가 `--viewport` 를 사용법 오류 78 로 거절).
  - RED 에서 통과한 3건: ① 거르기 없음 종료 1(픽스처 감도 대조군) · ⑤ 0장 78 · ⑥ 값 없는 플래그 78 — 옛 도구에서도 사용법 오류 78 이 나와 통과했다. 구현 뒤에는 거르기 경로의 78 로 통과한다(메시지 `0 captures selected` 실측).
- GREEN: `Tests  12 passed (12)`. 같은 실행에서 기존 업로드 잠금 시험(`design-fix-followups-20260925-L2.test.tsx`) · `visual-diff.test.ts` 포함 3파일 46건 통과.
- RED 뒤 시험 파일 수정 1회: `node:*` import 에 `// @ts-expect-error` 와 `declare const process` 를 붙였다(선례 `design-fix-followups-20260925-L2.test.tsx:10`–`13` · `tsconfig` 에 node 타입 없음). 단언 변경 0.

## 3. 게이트(task 실행 · 호스트 단독)

| 게이트 | 결과 |
|---|---|
| `frontend-typecheck` | green — `tsc --noEmit` 오류 0 |
| `frontend-test` | green — 146파일 1905건 통과 · 실패 0 |
| 계 | green 2 / red(판정) 0 / red(준비) 0 |

gate-summary 는 task runtime 에 있다(경로는 인계 메시지). 보고서 커밋 뒤 같은 명령으로 한 번 더 돌려 인계한다.

## 4. 상태 확인 78 증명

- 명령: `capture.py --label dwi0926-l0a-state78 --only catalog --skip-build --force-input touch` → **종료 78**.
- 출력: `catalog-light-1440: page state {'coarse': True, 'dpr': 1, 'height': 900, 'hover': False, 'theme': 'light', 'width': 1440} does not match viewport 1440 {... 'coarse': False, 'hover': True}`
- 대조(정상 실행): `--only catalog,gnb-more` 18장 종료 0 — 터치 5크기에서 coarse · hover 없음, 1440 에서 fine · hover, 창 높이가 선언과 같았다.

## 5. 두 번 찍기(`dwi0926-det-a` 대 `dwi0926-det-b`) — 미완 · 78

- `dwi0926-det-a`(audit 빌드 포함 · 커밋 `a6514f3d` · 깨끗한 트리) → **종료 78**, 340장 뒤 정지. `det-b` 는 찍지 않았다.
- 원인 장면: `upload-classify` × `844x390`(라이트 · 다크). 동작 `click [data-testid=reg-open]` 뒤 `select [data-testid=reg-category]` 가 `Element not found`.
- 실측(같은 래퍼 · 844x390 재현): 업로드 모달이 창 높이 390 안에서 스크롤되고 `reg-open` 단추 상자가 `y=411.7 · 높이 44` 로 창 밖이다. `click` 뒤에도 같은 위치이고 분류 단계가 열리지 않았다(`reg-category` 없음 · 대화상자 1). 1440 · 390 에서는 같은 장면이 찍힌다.
- 같은 첫 동작을 쓰는 `upload-metadata` · `upload-link` 도 844x390 라이트에서 같은 `select [data-testid=reg-category]` `Element not found` 를 실측했다(진단 재생 · 같은 래퍼). 막힌 캡처 = 3장면 × 2테마 = 6장(844x390 만).
- 진단 재생(파일 변경 없음): `click [data-testid=reg-open]` 앞에 `scrollIntoView [data-testid=reg-open]` 를 넣으면 세 장면 모두 844x390 라이트에서 모든 동작이 끝까지 돌았다(스크린샷 · 픽셀 대조는 하지 않음).
- 나머지 32장면 진단(공식 라벨 아님): `dwi0926-l0a-part-a` 대 `-part-b`(같은 커밋 · 깨끗한 트리) 378장(31 × 12 ＋ 더보기 6) 전부 종료 0 · 엄격 차이 픽셀 0 · 불안정 장면 없음. `--viewport 1440` 거르기 62장 차이 0 · `--viewport 507x820` 0장 78.
- 판정 필요(레인이 고치지 않음 · spec 에 없는 변경): ⓐ 세 장면의 `click [data-testid=reg-open]` 앞에 기존 동작 어휘 `scrollIntoView` 를 더한다(scenes.json 데이터만 · 위 진단 재생으로 동작 확인 · 다른 크기에서 스크롤 위치가 바뀌면 그 캡처도 바뀔 수 있음) ⓑ `click` 동작이 누르기 전 요소를 창 안으로 스크롤하게 한다(capture.py · 모든 장면의 click 에 적용) ⓒ 세 장면에서 844x390 을 뺀다(색인 414 가 408 로 바뀜 · spec 수치 변경).

## 6. 실행 시간

- `npm ci` 1회 · 스모크(빌드 포함 18장) 58초 · 78 증명 1회.
- det-a(빌드 포함) 340장 뒤 78.
- 진단 part-a 378장 16분 33초(병렬 2 · 빌드 생략) · part-b 같은 수준.
- 게이트 task 1회.

## 7. 이탈 · 남은 것

- 미완: 두 번 찍기 414장 픽셀 0(§5 판정 뒤 재실행).
- 이탈: `--force-input` 플래그(spec 에 없음 · 78 증명 실행 방법으로 추가). `browser.inputArgs` 를 명세 파일에 둠(spec 은 래퍼 내용만 정함). `--parallel` 기본값은 2 유지(spec 은 최대 4 만 정함).
- 문서: `docs/design-system.md` 의 「3폭 × 2테마」 · 캡처 명령 행은 L4 몫이라 고치지 않았다.
- 후속: agent-browser 0.27.0 은 이미 떠 있는 세션에 `--executable-path` 를 줄 때마다 「ignored: daemon already running」 경고를 출력한다(종료 0 · 동작 영향 없음). 실패 메시지 앞머리가 이 경고로 채워져 실제 원인이 뒤에 나온다 — 어느 검사에도 걸리지 않는다.
