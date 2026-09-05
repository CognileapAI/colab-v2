# BF-7 레인 보고 — 스크린샷 버튼 · 객체 URL 회수 시점

- 대상 항목 = `dev-package/work-items.yaml` `BF-7`
- 브랜치 = `bf-7/screenshot-revoke-timing` (기반 `b0c1f34`)
- 커밋 = `932b3f0`
- 작업일 = 2026-09-05

---

## §1 진입조건 재실측

- 통합 브랜치 `bugfix/20260903-ui-12` 병합 여부 = **충족.** 대장에서 `BF-1`~`BF-6` 전건 `status: done`.
- 원인 코드 = **대장 서술과 일치.** `ScreenshotButton.tsx` `take()` 안에서
  `URL.createObjectURL` → `document.createElement('a')` → `a.click()` → **같은 tick 의**
  `URL.revokeObjectURL(url)`. 앵커를 문서에 붙이는 줄이 없다.
- 서버 렌더 경로 = 파일 머리 주석대로 **화면은 한 줄도 그리지 않는다** — 중계 op
  `props.source.screenshot(request)` 가 준 PNG 를 그대로 내려 준다. 이 경로 무접촉(⑷ 충족).
- 기존 시험 = `frontend/test/dataset-preview-screenshot.test.tsx` 8건.
  `beforeEach` 에서 `URL.createObjectURL`(→ `'blob:x'`)·`URL.revokeObjectURL` 을
  `Object.defineProperty` 로 갈아 끼운다. 회수 **시점**을 재는 시험은 없었다.
- 대장과 코드의 충돌 없음.

## §2 고친 파일

| 파일 | +/- |
|---|---|
| `frontend/src/components/datasetpreview/ScreenshotButton.tsx` | +11 / −1 |
| `frontend/test/dataset-preview-screenshot.test.tsx` | +52 / −0 |

- 형제 레인 소유 파일(`vite.config.ts`·`project.css`·`detail.css`·`shell.css`·`dashboard.css`) 무접촉.
- 잠금 파일(`package-lock.json`) 무변경 — `npm ci` 만 돌렸다.

## §3 시험 — RED → GREEN

- 오라클 = 클릭 순간의 상태를 **클릭 대역 안에서** 기록한다. `HTMLAnchorElement.prototype.click`
  을 감싸 ⒜ `this.isConnected` 를 남기고, ⒝ 진행 단계를 `sync` 로 표시한 뒤 `queueMicrotask`
  ·`setTimeout` 으로 `microtask`·`task` 로 넘긴다. `revokeObjectURL` 대역이 **그때의 단계**를
  기록하므로 「같은 tick 인가」가 값으로 남는다.
- 단언 4항 — ⒜ 클릭 시점 `isConnected === true` · ⒝ 회수 단계 `!== 'sync'` ·
  ⒞ 나중에는 반드시 `revokeObjectURL('blob:x')` 호출 · ⒟ 회수 뒤 `a[download]` 잔존 0건.

RED (구현 전 · 축자)

```
 ❯ test/dataset-preview-screenshot.test.tsx (9 tests | 1 failed) 559ms
     × 앵커는 문서에 붙은 채 클릭되고, revoke 는 같은 tick 이 아니라 뒤에 온다 84ms
AssertionError: expected false to be true // Object.is equality
 Test Files  1 failed (1)
      Tests  1 failed | 8 passed (9)
```

GREEN (구현 후 · 축자)

```
 Test Files  1 passed (1)
      Tests  9 passed (9)
```

## §4 구현 (⑵)

- 앵커에 `style.display = 'none'` 을 주고 `document.body.appendChild(a)` 로 붙인 뒤 누른다.
- 회수를 `setTimeout(…, 0)` 다음 태스크로 미룬다 — 그 안에서 `a.remove()` 와
  `URL.revokeObjectURL(url)` 을 함께 한다. 미루되 **흘리지 않는다**.
- 요청 조립·실패 문구·권한 게이트·`visibleBounds` 무변경.

## §5 게이트 (축자)

```
frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 596건 · 실패 0건.
    Test Files  38 passed (38)
         Tests  596 passed (596)
```

```
frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.
```

- 좁힌 게이트를 하나씩 돌렸다. 대상 축소·건너뛰기 없음.

## §6 ⑶ 브라우저 실측 — **완주 확인 · 단 「취소」 전제는 재현 안 됨**

측정 방법

- `npm run dev`(vite `--port 5199`) 로 띄운 개발 서버 위에 임시 하네스 한 장을 두고,
  **실제 `ScreenshotButton` 컴포넌트**를 마운트했다. `source.screenshot` 은 1 MiB `image/png`
  `Blob` 을 돌려주는 대역이다. **staging 무접촉** · core-api 무접촉.
- Playwright(Chromium **Chrome/148.0.0.0** · Linux x86_64)로 「스크린샷」 버튼을 누르고
  `context.waitForEvent('download')` 를 받았다.
- 하네스 두 파일은 측정 뒤 지웠다 — 커밋에 없다.

결과 (고친 코드)

```
suggestedFilename : preview-01JYZ9K7WQ3N8V4M2X6C5B0RE9.png
failure           : null
download.path()   : non-null
받은 바이트        : 1048576 (요청 1 MiB 전량)
페이지에 남은 a[download] : 0
```

→ **⑶ 확인.** 고친 경로에서 크롬 내려받기가 완주한다.

대조군 — **여기서 대장 전제가 갈린다**

- 같은 창에서 **고치기 전 관용구**(문서 미부착 ＋ 같은 tick `revokeObjectURL`)를 그대로
  실행해 봤다. 1 MiB · 64 MiB · 256 MiB 세 회차 전부 `failure: null` 로 **완주했다.**
- 즉 이 환경(headless Chromium 148)에서는 대장이 적은 「크롬 다운로드 **취소**」가
  **재현되지 않았다.** 재현 실패이지 반증은 아니다 — headless·자동화 창은 다운로드 처리가
  일반 크롬과 다르고, Ted 접수 12건에도 이 증상은 없다(대장 `note`: recon 발견 · Ted 미보고).
- 판단 = 고침 자체는 유지한다. 같은 tick 회수는 사양상 경합이고 앵커 미부착은 관례 위반이라
  **정확성 근거로 충분**하다. 다만 「취소를 고쳤다」가 아니라 「취소가 날 수 있는 자리를
  닫았다」로 적는 것이 실측에 맞다.
- Ted 가 직접 볼 수 있는 명령 = `frontend` 에서 `npm run dev` 뒤 실브라우저(headless 아님)로
  데이터셋 상세를 열어 「스크린샷」 을 누른다.

## §7 대장 `evidence:` 초안 (BF-5 문체)

> 커밋 `932b3f0`(`ScreenshotButton.tsx` +11/−1 · `test/dataset-preview-screenshot.test.tsx` +52) ·
> 기반 `b0c1f34`. RED = **1 failed / 8 passed** — 정확히 신규 1건(클릭 시점 `isConnected` 가 `false`) →
> GREEN **9건 전건 통과**. 게이트 `frontend-test` **38파일 / 596건 전건 통과** · `frontend-typecheck` 오류 0.
> 오라클은 클릭 대역 안에서 ⒜ 앵커의 `isConnected` 와 ⒝ 회수가 일어난 진행 단계(`sync`·`microtask`·`task`)를
> 함께 기록해 **같은 tick 회수**를 값으로 못 박는다 — 회수 자체는 여전히 단언한다(객체 URL 을 흘리지 않는다).
> ⑶ 브라우저 실측 = 개발 서버 위 실제 컴포넌트 · Chrome/148 · `waitForEvent('download')` 로
> `failure: null` · 1048576 바이트 전량 수신 · 잔존 앵커 0. **단 대조군(고치기 전 관용구)도 1·64·256 MiB
> 전부 완주해 대장이 적은 「취소」는 이 환경에서 재현되지 않았다** — 재현 실패이지 반증이 아니며,
> 같은 tick 회수·앵커 미부착은 사양상 경합이라 고침을 유지한다. 서버 렌더 경로 무접촉. 근거 `reports/bf-7/lane-report.md`.

## §8 §9 등재문 초안 (번호 미부여)

> **〈N〉 BF-7 — 스크린샷 내려받기의 객체 URL 은 클릭과 같은 tick 에서 거두지 않는다.**
> 값 = `ScreenshotButton.tsx` 의 내려받기 앵커를 `display:none` 으로 문서에 붙여 누르고,
> 앵커 제거와 `URL.revokeObjectURL` 을 `setTimeout(…, 0)` **다음 태스크**로 미룬다.
> 근거 = `a.click()` 이 돌아온 뒤 브라우저가 별도 태스크에서 `blob:` 을 읽는데, 같은 tick 에서
> 회수하면 읽을 자리가 먼저 사라진다. 문서에 붙지 않은 앵커는 구현에 따라 클릭이 먹지 않는다.
> 오라클은 클릭 대역 안에서 앵커의 `isConnected` 와 회수 시점의 진행 단계를 함께 재어,
> 「같은 tick 회수」를 시험이 잡는 값으로 만든다. **미루되 흘리지 않는다** — 회수 자체를 단언한다.
> ⭑ 실측 단서 — 브라우저 회차에서 **고치기 전 관용구도 완주했다**(Chrome/148 headless · 1·64·256 MiB).
> 대장이 적은 「크롬 다운로드 취소」는 이 환경에서 **재현되지 않았다.** 고침은 증상 제거가 아니라
> **사양상 경합의 제거**로 등재한다. 실브라우저(headless 아님) 재확인은 열려 있다.

## §9 대장 문안과의 차이

1. 대장 `entry_conditions`·`completion_def` 가 줄번호 앵커(`ScreenshotButton.tsx:72-77`·`:9-10`)를
   쓴다. 이번 회차 산출물에는 줄번호를 쓰지 않았다 — 이번 수정으로 그 줄이 밀린다.
2. `completion_def` ⑵ 의 「`setTimeout`/`load` 뒤」 중 **`setTimeout` 갈래**를 골랐다. `load` 는
   `<a download>` 에 걸리는 사건이 아니라 이 자리에서 오라클이 되지 못한다.
3. `completion_def` ⑶ 「크롬에서 다운로드가 **완주**함을 실측」 = 충족. 다만 항목 `name` 이 단언한
   「객체 URL 즉시 revoke 로 크롬 다운로드 **취소**」라는 **증상**은 재현되지 않았다(§6).
   항목 이름을 그대로 두면 실측되지 않은 증상이 대장에 사실처럼 남는다 — 사람 판정 자리다.
4. 상태 전이는 이 레인이 하지 않았다. 대장·`PLAN-SoT §9`·`03-HANDOFF` 무접촉(지시대로).
   `CLAUDE.md §0` 기준 완료 = staging 배포 green 이므로 `BF-5` 선례대로 배포 창이 전환한다.
