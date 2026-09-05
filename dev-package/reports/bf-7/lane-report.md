# BF-7 레인 보고 — 스크린샷 버튼 · 객체 URL 회수 시점

- 대상 항목 = `dev-package/work-items.yaml` `BF-7`
- 브랜치 = `bf-7/screenshot-revoke-timing` (기반 `b0c1f34`)
- 커밋 = `932b3f0` · `fa91aee`(수용 검토 반영)
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

수용 검토 반영분(`§6-2`)이 같은 두 파일에 각각 +18/−7 · +46/−17 을 더 얹었다.

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
- 회수를 `setTimeout(…, OBJECT_URL_RETENTION_MS)` 로 미룬다 — 그 안에서 `a.remove()` 와
  `URL.revokeObjectURL(url)` 을 함께 한다. 미루되 **흘리지 않는다**.
  (지연값은 수용 검토에서 `0` → **4000 ms** 로 바뀌었다 — `§6-2`-⑴.)
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

## §6-2 수용 검토 반영 (조건부 수용 → 집행)

지시 4항을 그대로 집행했다. 커밋 `fa91aee`.

### ⑴ 회수 지연을 `0` → 이름 붙인 상수 4000 ms

- `ScreenshotButton.tsx` 파일 머리에 `OBJECT_URL_RETENTION_MS = 4000` 을 두고 주석에 근거를 적었다 —
  **크롬은 내비게이션이 시작되는 순간 `blob:` 핸들을 붙잡아 두므로 `0` 으로도 되지만,
  파이어폭스는 가져오기가 시작되기 전에 회수될 수 있다.** FileSaver.js 는 40초를 기다리는 선례다.
- 다음 태스크(`0`)는 **크롬 한 종에만 맞는 값**이었다. 나머지는 동일 — 서버 렌더 경로 무접촉.
- 무한정 쥐지 않는다. 이 시간이 지나면 앵커 제거와 회수를 반드시 한다.

### ⑵ 시험 조임 — `not.toBe('sync')` → `toBe('task')`

- ⒞ 를 `expect(phaseAtRevoke).toBe('task')` 로 바꿨다. **`microtask` 를 받지 않는다** —
  같은 tick 이 끝나기 전에 도는 자리라 회수 시점으로 이르다.
- 지연이 초 단위가 됐으므로 실제 시간을 기다리지 않는다. `vi.useFakeTimers()` 를 **이 `it` 안에서만**
  쓰고 `finally { vi.useRealTimers() }` 로 되돌린다 — 다른 시험으로 새지 않는다.
- 가짜 시계를 **누르는 순간부터** 켠다. 렌더 대기(`findByTestId`)까지 가짜 시계로 덮으면
  대기가 멈춰 시험이 5000 ms 타임아웃으로 죽는다(실제로 그렇게 한 회차가 red 였다). 시계 전환 뒤에는
  `waitFor` 대신 `vi.advanceTimersByTimeAsync(0)` → `vi.runAllTimersAsync()` 로 흘린다.
- ⒟ 를 `document.querySelector('a[download]')` 에서 **이 시험이 만든 앵커의 `isConnected`** 로 바꿨다.
  같은 파일의 앞선 시험(「받은 PNG 를 그대로 내려 준다」)이 실제 시계로 클릭해 회수 타이머가 돌기 전에
  끝나므로, 그 앵커가 `document.body` 에 남아 문서 전역 조회에 걸린다. 남의 잔재를 이 시험의 판정으로
  쓰지 않는다.

### ⒝ 단독 RED 실측

앞 회차 RED 는 **⒜ 에서 먼저 걸려 ⒝ 를 증명하지 못했다.** 그래서 ⒜ 는 통과하고 ⒝ 만 걸리는
중간 상태(**앵커는 문서에 붙이되 회수는 같은 tick**)를 워크트리에 임시로 만들어 재었다.

```
 ❯ test/dataset-preview-screenshot.test.tsx (9 tests | 1 failed) 449ms
     × 앵커는 문서에 붙은 채 클릭되고, revoke 는 sync 도 microtask 도 아닌 다음 태스크에 온다 35ms
AssertionError: expected 'sync' not to be 'sync' // Object.is equality
 ❯ test/dataset-preview-screenshot.test.tsx  // ⒝ expect(phaseAtRevoke).not.toBe('sync')
 Test Files  1 failed (1)
      Tests  1 failed | 8 passed (9)
```

- 위는 **최종 시험 파일** 그대로에 대고 잰 값이다. 임시 상태는 측정 뒤 되돌렸고 커밋에 없다.
- 참고 — 되돌린 원본(앵커 미부착 ＋ 같은 tick 회수)에 대고는 ⒜ 가 먼저 걸린다:
  `AssertionError: expected false to be true` · `1 failed | 8 passed (9)`.
- GREEN (4000 ms 상수 · 최종 상태) = `Test Files 1 passed (1)` · `Tests 9 passed (9)`.

### 게이트 재측정 (조임 뒤 · 축자)

```
frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 596건 · 실패 0건.
    Test Files  38 passed (38)
         Tests  596 passed (596)
```

```
frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.
```

### ⑶ 브라우저 실측의 유효 범위 (변동 없음)

§6 의 브라우저 회차는 **지연 `0`** 상태에서 쟀다. 4000 ms 는 그보다 **더 오래 쥐는** 방향이라
완주 결과가 뒤집히지 않는다 — 회수가 늦어져 다운로드가 깨지는 경로는 없다. 다만 4000 ms 상태에서
브라우저를 다시 돌리지는 않았다. **재측정 없이 완주를 재주장하지 않는다** — 지연을 늘린 방향의
논증이지 새 실측이 아니다.

## §7 대장 `evidence:` 초안 (BF-5 문체)

> 커밋 `932b3f0`(고침 ＋ 시험) ＋ `fa91aee`(수용 검토 반영 — 지연 상수화·시험 조임) · 기반 `b0c1f34`.
> `ScreenshotButton.tsx` `take()` 의 내려받기 앵커를 `document.body` 에 붙여 누르고, 앵커 제거와
> `URL.revokeObjectURL` 을 이름 붙인 상수 `OBJECT_URL_RETENTION_MS`(**4000 ms**) 뒤로 미룬다 —
> 크롬은 내비게이션 시작 시점에 `blob:` 핸들을 잡아 `0` 으로도 되지만 **파이어폭스는 가져오기 전에
> 회수될 수 있다**(FileSaver.js 는 40초 대기 선례). RED = **1 failed / 8 passed** — ⒜(클릭 시점
> `isConnected` 가 `false`) 와, ⒜ 만 통과시킨 중간 상태에서 잰 ⒝(`expected 'sync' not to be 'sync'`)를
> **따로** 냈다 → GREEN **9건 전건 통과**. 게이트 `frontend-test` **38파일 / 596건 전건 통과** ·
> `frontend-typecheck` 오류 0. 오라클은 클릭 대역 안에서 앵커의 `isConnected` 와 회수가 일어난 진행
> 단계를 함께 기록해 회수 시점을 `task` 로 못 박는다 — `microtask` 는 받지 않고, 회수 자체는 여전히
> 단언한다(객체 URL 을 흘리지 않는다). 가짜 시계는 해당 `it` 안에서만 쓰고 `finally` 로 되돌린다.
> ⑶ 브라우저 실측 = 개발 서버 위 실제 컴포넌트 · Chrome/148 · `waitForEvent('download')` 로
> `failure: null` · 1048576 바이트 전량 수신 · 잔존 앵커 0(지연 `0` 상태에서 측정 · 4000 ms 는 더 오래
> 쥐는 방향이라 완주가 뒤집히지 않으나 재측정은 하지 않았다). **단 대조군(고치기 전 관용구)도
> 1·64·256 MiB 전부 완주해 대장이 적은 「취소」는 이 환경에서 재현되지 않았다** — 재현 실패이지
> 반증이 아니며, 같은 tick 회수·앵커 미부착은 사양상 경합이라 고침을 유지한다. 스크린샷을 서버가
> 그린다는 파일 머리 주석의 계약대로 서버 렌더 경로 무접촉. 근거 `reports/bf-7/lane-report.md`.

## §8 §9 등재문 초안 (번호 미부여)

> **〈N〉 BF-7 — 스크린샷 내려받기의 객체 URL 은 클릭과 같은 tick 에서 거두지 않는다.**
> 값 = `ScreenshotButton.tsx` `take()` 의 내려받기 앵커를 `display:none` 으로 문서에 붙여 누르고,
> 앵커 제거와 `URL.revokeObjectURL` 을 이름 붙인 상수 `OBJECT_URL_RETENTION_MS`(**4000 ms**) 뒤로 미룬다.
> 근거 = `a.click()` 이 돌아온 뒤 브라우저가 별도 태스크에서 `blob:` 을 읽는데, 같은 tick 에서
> 회수하면 읽을 자리가 먼저 사라진다. 문서에 붙지 않은 앵커는 구현에 따라 클릭이 먹지 않는다.
> **다음 태스크(`0`)로는 부족하다** — 크롬은 내비게이션 시작 시점에 핸들을 잡지만 파이어폭스는
> 가져오기가 시작되기 전에 회수될 수 있다(FileSaver.js 40초 대기 선례). 그래서 몇 초를 쥔다.
> 오라클은 클릭 대역 안에서 앵커의 `isConnected` 와 회수 시점의 진행 단계를 함께 재어,
> 회수를 `task` 로 못 박는다 — `sync` 도 `microtask` 도 받지 않는다.
> **미루되 흘리지 않는다** — 회수 자체를 단언한다.
> ⭑ 실측 단서 — 브라우저 회차에서 **고치기 전 관용구도 완주했다**(Chrome/148 headless · 1·64·256 MiB).
> 대장이 적은 「크롬 다운로드 취소」는 이 환경에서 **재현되지 않았다.** 고침은 증상 제거가 아니라
> **사양상 경합의 제거(하드닝)** 으로 등재한다. 실브라우저(headless 아님)·파이어폭스 재확인은 열려 있다.
> ⭑ 그래서 항목 이름과 완료 정의 ⑶ 을 실측에 맞춰 고쳐 적는다 — `§9-2`.

## §8-2 대장 `name`·`completion_def` ⑶ 수정 초안

종전 `name` 이 「크롬 다운로드 **취소**」를 사실로 적는데 그 증상은 실측되지 않았다.
실측된 것은 **경합의 존재**이지 증상이 아니다.

- `name` (초안) —
  > 스크린샷 버튼 — 객체 URL 같은 tick 회수·앵커 미부착 경합 (하드닝 · 크롬 취소 증상 미재현)
- `completion_def` ⑶ (초안) —
  > **완주 실측(증상 미재현 기록)**

`entry_conditions`·`completion_def` 의 줄번호 앵커는 심볼 앵커로 바꿔 적는다.

| 종전 | 고쳐 적을 것 |
|---|---|
| `ScreenshotButton.tsx:72-77` | `ScreenshotButton.tsx` `take()` 의 내려받기 앵커 구간 |
| `ScreenshotButton.tsx:9-10` | `ScreenshotButton.tsx` **파일 머리 주석**(「그리는 일은 한 줄도 하지 않는다」) |

줄번호는 이번 수정으로 이미 밀렸다. 앞으로도 밀린다.

## §9 대장 문안과의 차이

1. 대장 `entry_conditions`·`completion_def` 가 줄번호 앵커(`ScreenshotButton.tsx:72-77`·`:9-10`)를
   쓴다. 이번 회차 산출물에는 줄번호를 쓰지 않았다 — 이번 수정으로 그 줄이 밀린다.
   대체 심볼 앵커는 `§8-2` 표.
2. `completion_def` ⑵ 의 「`setTimeout`/`load` 뒤」 중 **`setTimeout` 갈래**를 골랐다. `load` 는
   `<a download>` 에 걸리는 사건이 아니라 이 자리에서 오라클이 되지 못한다.
   ⭑ 지연값은 대장이 정하지 않았다 — **4000 ms** 로 정했다(근거 `§6-2`-⑴).
3. `completion_def` ⑶ 「크롬에서 다운로드가 **완주**함을 실측」 = 충족. 다만 항목 `name` 이 단언한
   「객체 URL 즉시 revoke 로 크롬 다운로드 **취소**」라는 **증상**은 재현되지 않았다(§6).
   항목 이름을 그대로 두면 실측되지 않은 증상이 대장에 사실처럼 남는다 — 사람 판정 자리다.
   수정 초안은 `§8-2`(`name` 을 「하드닝 · 크롬 취소 증상 미재현」으로 · ⑶ 을 「완주 실측(증상 미재현 기록)」으로).
4. 상태 전이는 이 레인이 하지 않았다. 대장·`PLAN-SoT §9`·`03-HANDOFF` 무접촉(지시대로).
   `CLAUDE.md §0` 기준 완료 = staging 배포 green 이므로 `BF-5` 선례대로 배포 창이 전환한다.
