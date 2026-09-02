# 프런트 타입 검사 게이트 신설 — 등재문 **초안** · 번호 미발급

> 이 레인은 `PLAN-SoT.md §9` 에 쓰지 않고 번호를 발급하지 않는다(최신 `〈283〉`). **번호와 등재는 오케스트레이터가 직렬로 한다.**
> 회차 = 2026-09-02 · 워크트리 `.claude/worktrees/lane-tsc` · 브랜치 `lane-tsc` (off `main` @ `4c3de23`)

---

## 0. 사고 진술 — `main` 이 배포 불가였고, 그것을 아무도 재지 않았다

- **상태** — `main` 이 **12:01 부터 22:32 까지 배포 불가**였다. 12:01 = `74deb54` 가 `frontend/test/e01-apply-points.test.ts` 를 넣은 시점, 22:32 = staging 배포가 **이미지 빌드 단계**에서 처음 걸린 시점.
- **깨진 자리** — `frontend/Dockerfile:11` `RUN npm run build` = `tsc --noEmit && vite build`. 오류 4건:
  - `test/e01-apply-points.test.ts(11,53)` `TS2307` `node:fs` 를 찾을 수 없다
  - `test/e01-apply-points.test.ts(12,32)` `TS2307` `node:path` 를 찾을 수 없다
  - `test/e01-apply-points.test.ts(15,19)` `TS2304` `__dirname` 이 없다
  - `test/e01-apply-points.test.ts(45,44)` `TS7006` 매개변수 `l` 이 암묵 `any`
- **뿌리** — `frontend/tsconfig.json:20` 이 `test/` 를 검사 대상에 넣는데 `:8` `types` 에 `node` 가 없다. 브라우저 산출물이라 없는 것이 옳고, **틀린 쪽은 시험이 Node API 를 쓴 것**이다.
- **⭑ 진짜 결함은 그 시험이 아니라 배선이다** — `grep -rl 'tsc --noEmit' gates/` = **0**. 프런트 타입 검사가 **이미지 빌드 안에만** 있었다. 게이트는 전건 green 이었고 배포를 트기 전까지 아무도 못 봤다.
- **⭑ 수용 실패 — 다섯 레인이 보고했고 기존 상태로 받아들여졌다.** 회차 중 레인 다섯이 「tsc 오류 4건 = `main` 동일」을 보고했고, **「`main` 과 같으니 기존 것」으로 수용**됐다. 재는 자리가 없으면 결함은 「원래 그렇다」로 굳는다. 이 사고의 재발 방지는 시험 수정이 아니라 **게이트 신설**이다.

## 1. 집행 — 두 갈래

### ㉮ 시험을 브라우저 API 로 다시 썼다 (`frontend/test/e01-apply-points.test.ts`)

- **범위를 줄이지 않았다** — `tsconfig` `include` 에서 `test` 를 빼는 안은 **검사 대상 축소**라 채택하지 않았다(`CLAUDE.md §3`). 시험의 판정(초안 §1.1 표 ↔ `PermissionGate` 실물, **양방향 집합 동일**)은 그대로 산다. 시험 2건 유지.
- **입력을 바꿨다** — `node:fs` 대신 vite 의 `?raw`(초안 md) ＋ `import.meta.glob('../src/**/*.{ts,tsx}', { query:'?raw', eager:true })`(소스 전수). `@types/node` 를 들이지 않는다.
- **`?raw` 가 왜 비어 보였나 — 실측** : 초안 md 는 `frontend/` **밖**이고 vite 는 루트 밖 파일을 `server.fs.allow` 로 거른다. 실측 오류 = **`Error: Denied ID …/dev-package/sessions/P8-E01-APPLY-POINTS-DRAFT.md?raw`**. 소스 쪽 `?raw`(루트 안)는 처음부터 정상이었다 — 111 파일 · 표본 길이 1691 · `PermissionGate` 적중 9파일.
- **고친 자리** = `frontend/vite.config.ts` — `defineConfig(({ mode }) => …)` 로 바꾸고 **`mode === 'test'` 일 때만** `server.fs.allow = ['.', '../dev-package/sessions']`. 개발 서버는 넓히지 않는다. 적용 뒤 초안 길이 **5641** 로 읽힌다.
- **대안 ⓑ(표의 기계 판독 행을 `.ts`/`.json` 모듈로 옮기고 md ↔ 모듈 일치를 별도 게이트로 확인) 는 기각** — 값이 **두 곳**에 서고 그 둘의 동기화를 지키는 게이트가 하나 더 필요해진다. 이 레포가 반복해 다친 무늬가 「정본이 둘」이다(`CLAUDE.md §7`). ⓐ 는 초안 md 를 **유일 정본**으로 유지한다.
- 암묵 `any` 는 `(l: string)` 로 명시했다.
- **0건 방어를 더했다** — 소스 0건·실물 적용 지점 0건·스위치 0건이면 red. 두 집합이 「둘 다 비어서」 같아지는 통과를 막는다.

### ㉯ 게이트 신설 — `frontend-typecheck` ＋ `frontend-typecheck-selftest`

- **이미지가 도는 그 검사를 그대로 돈다** — `frontend/tsconfig.json` 기준 `tsc --noEmit`(`frontend/node_modules/.bin/tsc`).
- **갈림 방지 두 겹** — `package.json` `build` 가 `tsc --noEmit` 으로 시작하지 않으면 red · `Dockerfile` 이 `npm run build` 를 안 돌면 red. 게이트가 이미지와 다른 것을 보기 시작하면 green 인 채로 배포가 다시 깨진다.
- **범위 축소 금지** — `tsconfig` `include` 에서 `src`·`test` 가 빠지면 red.
- **fail-closed** — `frontend/node_modules` 부재·`.bin/tsc` 부재는 **red(준비 · 코드 78)**. skip 이 아니다.
- **셀프테스트 7 케이스** — red 여섯 · green 하나. ⭑ **ⓕ 가 `74deb54` 실물 결함 재현**(시험 파일이 `node:fs`·`node:path`·`__dirname` 사용) → red, 오류 4건이 이름으로 찍힌다. 판정은 전부 `mktemp -d` 사본 트리에서 나고 진짜 `frontend/` 에는 한 글자도 쓰지 않는다.
- **등재** — `gates/run.sh` `ALL_GATES`(37 → **39**) · 집합 게이트 `selftest` 목록 · `gates/config/parallelism.toml`(둘 다 **`parallel`** — 읽기만 하고 DB·포트·잠금을 잡지 않는다) · `gates/README.md` 한 행 · `.github/workflows/ci.yml` `contract-gates` 잡(이 잡이 이미 `npm ci --prefix frontend` 를 돈다).

## 2. 형제 훑기 — Dockerfile 안에만 있는 빌드 시점 검사

`git ls-files | grep -i dockerfile` 전 6종의 `RUN` 을 전수로 봤다.

| 자리 | 검사 | 게이트에 있나 | 판정 |
|---|---|---|---|
| `frontend/Dockerfile:11` | `npm run build` → `tsc --noEmit` | **없었다** | **이번에 신설** |
| `services/pipeline-worker/Dockerfile:28` | `python -c "import rasterio, rasterio._env, netCDF4, h5py, pyproj, pyhdf.SD"` | 없다 | **후속** — 같은 한 줄이 아니다. GDAL·HDF 네이티브 라이브러리가 이미지 안에 설치돼 있어야 성립하고, 호스트 게이트로 옮기면 「이미지가 아닌 호스트를 재는」 다른 검사가 된다 |
| `services/viz-render/Dockerfile:32` | `python -c "import rasterio, rasterio._env, netCDF4, pyhdf.SD, PIL.Image"` | 없다 | **후속** — 위와 같다 |
| `services/{core-api,ai-service}/Dockerfile` | `pip install` 뿐 | — | 검사 없음 |
| `infra/staging/migrator/Dockerfile` | `pip install` 뿐 | — | 검사 없음 |

- **`ruff`·`mypy`·`pytest` 는 어느 Dockerfile 에도 없다** — `.github/workflows/ci.yml` 에도 없다. 즉 백엔드 린트·타입 검사는 **어디에도 배선돼 있지 않다**(누락이지 Dockerfile 전용이 아니다). 이 회차는 열지 않는다.

## 3. 측정

| 항목 | 값 | 시점·기준 |
|---|---|---|
| `tsc --noEmit` (`frontend/`) | 오류 **0** | 2026-09-02 · 워크트리 `lane-tsc` |
| frontend 시험 | **438 / 24 파일** 통과 | `npx vitest run` · `main` 값과 동일(감소 0) |
| 게이트 `./gates/run.sh all -j 1` | **green 39 / red(판정) 0 / red(준비) 0** | 선언 39(단독 3 · 병렬 36) · **미선언 0** · 종전 37 → 신설 2 |
| core-api / viz-render / pipeline-worker / ai-service 시험 | **538 / 232 / 238 / 145** 통과 | `pytest -q` · 각 서비스 `.venv` · 전 항목 `main` 기록값과 동일(감소 0) |
| 이미지 빌드 | `colab-v2/frontend:lane-tsc-proof` **Built** | `docker compose -f infra/staging/compose.i2.yml build frontend`(deploy.sh ④ 와 같은 명령 · 태그만 레인 전용) |

## 4. 등재문 초안 (번호 `〈 〉`)

| 〈 〉 | **`main` 이 10시간 반 배포 불가였다 — 프런트 타입 검사가 이미지 빌드 안에만 있었다. 시험을 브라우저 API 로 고치고 게이트를 신설했다** | **사고 ＋ 집행 (2026-09-02 · Claude · 워크트리 `lane-tsc`).** **㉮ 사고** — `74deb54` 가 넣은 `frontend/test/e01-apply-points.test.ts` 가 `node:fs`·`node:path`·`__dirname` 을 써 `tsc --noEmit` 이 오류 4건으로 죽었고, 그 검사가 `frontend/Dockerfile:11` **안에만** 있어(`grep -rl 'tsc --noEmit' gates/` = 0) 12:01~22:32 동안 **전 게이트 green · `main` 배포 불가**였다. **㉯ 수용 실패** — 그 사이 레인 다섯이 「tsc 오류 4건 = `main` 동일」을 보고했고 **기존 상태로 수용**됐다. 재는 자리가 없으면 결함은 「원래 그렇다」로 굳는다. **㉰ 시험 재작성** — `tsconfig` 범위를 줄이지 않고(축소 금지 · `CLAUDE.md §3`) 입력을 vite `?raw` ＋ `import.meta.glob` 으로 바꿨다. `?raw` 가 비어 보인 실측 원인 = **`Denied ID`**(초안 md 가 vite 루트 밖 · `server.fs.allow`), 해소 = `vite.config.ts` 에서 **`mode === 'test'` 일 때만** 그 한 디렉터리를 허용. 판정 2건·양방향 집합 동일 그대로. **㉱ 게이트 신설** = `frontend-typecheck` ＋ `-selftest`(7 케이스 · **ⓕ 가 `74deb54` 결함 실물 재현으로 red**). 이미지와의 갈림 방지 두 겹(`build` 스크립트 대조 · `Dockerfile` 대조) ＋ `include` 축소 red ＋ 도구 부재 red(준비 · 78). **㉲ 형제 훑기** — Dockerfile 전용 검사는 프런트 `tsc` 외에 **geo 라이브러리 import 스모크 2건**(`pipeline-worker:28`·`viz-render:32`)뿐이고 네이티브 의존이라 후속으로 남긴다. `ruff`·`mypy` 는 Dockerfile 에도 CI 에도 **없다**. **㉳ 배포는 하지 않았다** — 로컬 이미지 빌드로만 증명 |

---

## 5. 이번 회차가 재지 **않은** 것 (다음 회차 진입조건)

- **백엔드 린트·타입 검사(`ruff`·`mypy`) 배선** — Dockerfile·CI·게이트 어디에도 없다. 신설 여부는 판정 대기.
- **geo 라이브러리 import 스모크의 게이트 이관**(`pipeline-worker:28`·`viz-render:32`) — 이미지 안에서만 성립한다.
- **staging 배포 green** — 이 레인은 배포 금지. `main` 이 다시 배포 가능한지의 최종 확인은 배포 회차 몫이다.
- **frontend 시험 자체를 도는 게이트** — 이번에 신 게이트는 **타입 검사만** 본다. `gates/README.md` 의 「레포에 frontend 시험을 도는 게이트가 없다」는 여전히 참이다.
