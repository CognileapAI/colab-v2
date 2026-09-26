# 레인 보고 — L0a 캡처 도구 틀(뷰포트 · 입력 방식 · 상태 확인 · 비교 거르기 · 두 번 찍기)

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 부록 I 「L0a」 행 · 구현 결정 「기준 캡처 도구」
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-l0a` · 기준 `8f754850` · 구현 커밋 `a6514f3d`
- task: `309102ffcc9c4c9e9417847ba6cb4bf1` (게이트 `frontend-typecheck` · `frontend-test` · 범위 `frontend/scripts/visual-baseline/**` · L0a 시험 파일)
- 판정(처음 레인): **L0a 미완 — 두 번 찍기가 캡처 단계에서 78 로 멈춤(§5).** 도구 · 시험 · 게이트 · 상태 확인 78 증명은 끝남.
- 마무리 레인(§8): 브랜치 `claude/dwi-l0a-finish` · 기준 `a24343cb` · 구현 커밋 `02d20b4d` · task `42326c04737648d3a9d1f461b93a0940`(같은 게이트 · 같은 범위).
- 판정(마무리): **L0a 완료 — 오케스트레이터 결정(§5 ⓑ)대로 `click` 이 창 밖 대상을 먼저 창 안으로 스크롤한다. 같은 커밋 두 번 찍기 414장 · 엄격 차이 픽셀 0.**

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

- 미완: 두 번 찍기 414장 픽셀 0(§5 판정 뒤 재실행). → 마무리 레인에서 해소(§8).
- 이탈: `--force-input` 플래그(spec 에 없음 · 78 증명 실행 방법으로 추가). `browser.inputArgs` 를 명세 파일에 둠(spec 은 래퍼 내용만 정함). `--parallel` 기본값은 2 유지(spec 은 최대 4 만 정함).
- 문서: `docs/design-system.md` 의 「3폭 × 2테마」 · 캡처 명령 행은 L4 몫이라 고치지 않았다.
- 후속: agent-browser 0.27.0 은 이미 떠 있는 세션에 `--executable-path` 를 줄 때마다 「ignored: daemon already running」 경고를 출력한다(종료 0 · 동작 영향 없음). 실패 메시지 앞머리가 이 경고로 채워져 실제 원인이 뒤에 나온다 — 어느 검사에도 걸리지 않는다.

## 8. 마무리 레인 — 창 밖 클릭 대상 스크롤 · 두 번 찍기 완료

### 8-1. 오케스트레이터 결정(spec 빈칸 「클릭 대상이 창 밖이면 먼저 창 안으로」)

- §5 판정 필요 ⓐ · ⓑ · ⓒ 중 **ⓑ** 채택. 캡처 동작 `click` 은 누르기 전에 대상 상자가 창 안에 다 들어 있는지 확인하고, 아니면 `scrollIntoView({block: 'nearest', inline: 'nearest'})` 한 뒤 누른다. 창 안 대상은 스크롤하지 않는다.
- 하지 않은 것: 장면별 동작 추가(ⓐ) · 844x390 제외(ⓒ). `scenes.json` 변경 0 · 색인 414 유지.
- 구현: `frontend/scripts/visual-baseline/capture.py` 의 `reveal_script(selector)`(페이지 스크립트 · 결과 `scrolled` · `inside` · `absent`) · `run_action` 의 `click` = 페이지 스크립트 → agent-browser `click`. 스크롤했을 때만 `click <선택자>: scrolled into view` 한 줄 출력. 대상이 없으면 스크롤하지 않고 없음 판정은 `click` 이 그대로 낸다(기존 78 경로 유지).
- 창 안 판정 = 상자 `top ≥ 0 · left ≥ 0 · bottom ≤ innerHeight · right ≤ innerWidth`.

### 8-2. 시험 RED → GREEN

- 시험 파일 `frontend/test/device-width-input-20260926-L0a.test.ts` 에 ⑶ 5사례 추가(실제 `capture.py` 의 `run_action` 을 python 으로 불러 브라우저 호출을 기록하고, 기록된 페이지 스크립트를 `node:vm` 가짜 문서에서 돌린다 · 실제 브라우저 없음): 호출 순서(페이지 스크립트 → 같은 선택자 `click`) · 세로 창 밖(844x390 · 상자 y=411.7 높이 44) 스크롤 1회 · 가로 창 밖 스크롤 1회 · 창 안 스크롤 0 · 대상 없음 스크롤 0.
- RED(구현 전): `Tests  5 failed | 12 passed (17)` — `expected [ 'ab' ] to deeply equal [ 'js', 'ab' ]`(옛 `click` 은 페이지 스크립트 없이 바로 누름). 나머지 4건은 기록된 첫 호출이 `click` 이라 페이지 스크립트로 돌리지 못해 실패.
- GREEN: `Tests  17 passed (17)`. 기존 12사례 단언 변경 0 · 삭제 0.

### 8-3. 두 번 찍기(구현 커밋 `02d20b4d` · 추적 파일 깨끗함 · 호스트 직렬)

| 실행 | 결과 | 시간 |
|---|---|---|
| `capture.py --label dwi0926-det-a`(audit 빌드 포함) | 종료 0 · 414장 · `gitHead 02d20b4d` · `gitDirty false` · 페이지 오류 0 · 스크롤 6회 | 1152.6초 |
| `capture.py --label dwi0926-det-b --skip-build`(같은 빌드) | 종료 0 · 414장 · `gitHead 02d20b4d` · `gitDirty false` · 페이지 오류 0 · 스크롤 6회 | 1153.2초 |
| `diff.mjs det-a det-b` | 종료 0 · 414장 · 35장면 · 차이 장면 0 · 엄격 픽셀 0 · 크기 불일치 0 | — |
| `diff.mjs --viewport 1440 det-a det-b` | 종료 0 · 68장(34장면 × 2테마) · 차이 0 | — |

- 스크롤 6회 = 업로드 3장면(`upload-classify` · `upload-metadata` · `upload-link`) × 2테마 × 844x390 의 `click [data-testid=reg-open]`. 나머지 클릭은 모두 창 안이라 스크롤 0.
- 눈 확인: `upload-classify-light-844x390.png` 에 분류 단계(분류 · 유형 선택값)가 열려 있다.
- 기존 장면 영향 없음 대조: 처음 레인 진단 `dwi0926-l0a-part-a`(옛 커밋 `a6514f3d` · 378장) 대 이번 `det-a` 를 `diff.mjs --subset` 으로 비교 → 종료 0 · 공통 32장면 378장 · 엄격 픽셀 0. 창 안 클릭은 바뀌기 전과 같은 캡처를 낸다.
- 캡처 폴더(추적 제외 · 마무리 레인 워크트리의 `frontend/.visual/`): `dwi0926-det-a` · `dwi0926-det-b` · 비교 보고 `dwi0926-det-diff` · `dwi0926-det-diff-1440` · `dwi0926-finish-vs-part-a`. agent-browser 세션은 도구가 만든 실행별 이름(`vb-<테마>-<입력>-<pid>-<시각>`)만 쓰고 그것만 닫았다.

### 8-4. 게이트(task `42326c04737648d3a9d1f461b93a0940` · 호스트 단독)

| 게이트 | 결과 |
|---|---|
| `frontend-typecheck` | green — `tsc --noEmit` 오류 0 |
| `frontend-test` | green — 146파일 1910건 통과 · 실패 0(처음 레인 1905 ＋ ⑶ 5) |
| 계 | green 2 / red(판정) 0 / red(준비) 0 |

- 위 계수는 구현 커밋 뒤 실행. 이 보고서 커밋 뒤 같은 명령으로 한 번 더 돌려 인계한다(gate-summary 경로는 인계 메시지).

### 8-5. 이탈 · 남은 것

- 이탈: 스크롤했을 때 한 줄 출력(색인 스키마 변경 없음 · 확인용). 두 번 찍기는 구현 커밋에서 찍었고 이 보고서는 그 뒤 커밋이다(도구 · 명세 변경 없음).
- 남은 위험: 창 안 판정은 창(`innerWidth` · `innerHeight`)만 본다 — 창 안이지만 스크롤 영역 경계에 잘린 대상은 스크롤하지 않는다(현재 35장면의 모든 클릭은 414장 × 2회 모두 다음 동작까지 돌았다 · 그런 대상의 유무는 따로 재지 않음).
- 후속: `docs/design-system.md` 캡처 명령 · 뷰포트 설명 갱신은 L4 몫(변경 없음).
