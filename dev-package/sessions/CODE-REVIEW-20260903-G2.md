# CODE-REVIEW-20260903-G2 — 레인 G2 `fixture-reach gate` 집행 기록

> 근거 — 레인 E(`CODE-REVIEW-20260903-E.md §5·§8`)가 `frontend/scripts/reachable-from-entry.mjs`
> 를 만들었으나 **게이트로 세우지 않았다**(§8 "후속 제안"). rc 로 말하도록 이미 짜여 있어
> (닿으면 `exit 1`) 게이트 껍데기만 있으면 된다는 그 제안을 집행한다.
> 기준 커밋 — `1a26372`(lane-review-clean). 편집 면 — `gates/**`·`.github/workflows/ci.yml`·
> `frontend/scripts/reachable-from-entry.mjs`(인자 하나 추가)·이 기록. 계약·서비스 무수정.
> 브랜치 — 워크트리 격리, push 없음 · 병합 없음 · 대장 번호 발급 없음.

## 1. 무엇을 더했나

### ⑴ `frontend/scripts/reachable-from-entry.mjs` — 인자 하나

`const ENTRY = 'src/main.tsx'` → `const ENTRY = process.argv[2] || 'src/main.tsx'`
(`frontend/scripts/reachable-from-entry.mjs:12`). 루트는 여전히 `cwd` 다 — 게이트가 `cd "$FE"`
로 트리를 지정하고, 셀프테스트가 픽스처 트리를 그 자리에 먹인다. 이 한 줄 말고는 원본 그대로다.

### ⑵ 게이트 — `gates/tools/frontend-fixture-reach.sh`

판정부(`reachable-from-entry.mjs`)를 **그대로** 돈다 — 게이트가 자기 사본을 만들지 않는다
(`frontend-typecheck.sh` 와 같은 원칙, `gates/tools/frontend-fixture-reach.sh:17-19`).

**세 상태** —

| 상태 | 조건 | 종료코드 |
|---|---|---|
| red(준비) | `node` 부재 · `frontend/scripts/reachable-from-entry.mjs` 부재 · 운영 진입점(`src/main.tsx`) 부재 | 78 |
| red(판정) | 경로 별칭(`tsconfig.json` `paths`/`baseUrl` 또는 `vite.config.ts` `resolve.alias`) 선언 · 금지 모듈 도달 · 진입점 말고 도달 모듈 0건 | 1 |
| green | 위 전부 아님 | 0 |

**별칭 가드 (`frontend-fixture-reach.sh:53-79`)** — `resolveSpecifier` 는 `.` 로 시작하는 상대
import 만 따라간다. `tsconfig.json` 의 `paths`/`baseUrl` 또는 `vite.config.ts` 의 `resolve.alias`
가 선언되면 그 뒤로 숨은 import 를 이 워커가 아예 못 보는데, 그 상태에서도 green 을 찍으면
"덜 봤다"가 "문제 없다"로 둔갑한다. 그래서 선언을 발견하면 도달성 판정 자체를 하지 않고
거기서 red 로 멈춘다. **오늘(2026-09-03) 실측 — 둘 다 없음**(레인 E 가 이미 확인했고, 이 회차가
같은 검사를 다시 실측해 재확인했다 — `gates/tools/frontend-fixture-reach.sh` 실행 로그 §3).

**0건 가드** — `reachable-from-entry.mjs` 는 진입점 자신도 도달 집합에 넣는다(`seen.add(file)` 이
확장자 검사보다 먼저다). 그래서 "도달 0건"은 워커 수준에서 나올 수 없고, 이 게이트는
**"진입점 말고" 도달 모듈**(`WALKED = REACHED - 1`)을 따로 세어 그것이 0 이면 red 로 낸다 —
진입점이 아무것도 당기지 않으면 그래프가 사실상 비어 있어 이 게이트가 아무것도 검사하지
않은 것과 같다(`frontend-fixture-reach.sh:88-91`, 픽스처 `empty-entry/` 가 증명).

### ⑶ 셀프테스트 — `gates/tools/frontend-fixture-reach-selftest.sh`

`gates/tools/_expect.sh` 를 그대로 쓴다(종료코드 78 을 "기대한 red"로 접지 않는 판정 갈래 —
2026-09-03 코드리뷰 #6 의 교훈). 픽스처는 워커가 파일 시스템에 아무것도 쓰지 않으므로
`mktemp -d` 사본 없이 `gates/fixtures/frontend-fixture-reach/` 를 **그대로** `COLAB_FRONTEND_DIR`
로 가리켜 돈다.

| 케이스 | 픽스처 | 기대 |
|---|---|---|
| ⓐ 깨끗한 진입점(대조군) | `clean/` | green |
| ⓑ 진입점이 금지 모듈에 실제로 닿는다 | `reachable/` | red |
| ⓒ 진입점 말고 도달 0건 | `empty-entry/` | red |
| ⓓ 경로 별칭 선언 | `alias-declared/` | red |
| ⓔ 판정부 스크립트 부재 | `no-script/` | red(준비 · 78) |
| ⓕ 운영 진입점 부재 | `no-entry/` | red(준비 · 78) |

### ⑷ 픽스처 — `gates/fixtures/frontend-fixture-reach/`

트리 여섯(`README.md` 포함) — 각 트리는 자기 `scripts/reachable-from-entry.mjs` 사본을 든다
(판정부 자체가 없는 상태도 재야 해서). 실물 `frontend/` 는 한 글자도 건드리지 않는다.

### ⑸ 등록

- `gates/run.sh` `ALL_GATES` — `frontend-fixture-reach`·`frontend-fixture-reach-selftest` 추가
  (`gates/run.sh:17`·`gates/run.sh:27`). **셀프테스트 집합은 `*selftest` 이름으로 자동 도출**되므로
  (`gates/run.sh` `selftest` 케이스 — `members`/`exempted` 를 `ALL_GATES` 에서 뽑는다) 이 항목이
  `case` 문 등록과 동시에 `selftest` 집합에 저절로 들어온다. 확인함 — 손목록 없음.
- `gates/config/parallelism.toml` — 둘 다 `"parallel"`(읽기만 하고 공유 쓰기 자원이 없다 —
  frontend-typecheck 와 같은 근거). **레포의 모든 게이트·셀프테스트가 이 표에 항목을 갖고 있어**
  (`ALL_GATES` 48건 전부가 선언에 있음을 스크립트로 대조) 신설분도 항목이 필요했다.
- `gates/README.md` — 게이트 표에 한 행(`frontend-test` 행 앞), 셀프테스트 표에 한 행
  (`generated-selftest` 행 앞).
  ⚠ **손대지 않은 낡은 자리 하나** — `gates/README.md:109`(`CI 배선` 표의 `gate-selftest` 행)가
  `실행 17 ＋ 명시 면제 2` 로 **여전히 손 숫자를 박고 있다**. 이 회차로 실행분이 17 → 18 이 되어
  그 줄이 곧바로 낡는다. `gates/README.md:155` 가 바로 이 무늬("여기에 숫자를 박지 않는다")를
  이미 한 번 고친 자리인데 109 행은 그때 안 고쳐진 채 남아 있었다. **편집 면이 "새 게이트 행
  하나 + 셀프테스트 행 하나"로 못박혀 있어 이 회차에서는 고치지 않았다** — 오케스트레이터
  판단이 필요한 자리로 [미확인] 남긴다.
- `.github/workflows/ci.yml` — `frontend-gates` 잡에 스텝 하나
  (`프런트 픽스처 도달성` · `./gates/run.sh frontend-fixture-reach`). 이 워커는 zero-dependency
  라 `node_modules` 설치를 기다리지 않아도 되지만, 잡 안의 다른 프런트 스텝과 나란히 두어
  "프런트 게이트는 여기 다 있다"는 배치를 지켰다. YAML 검증 — `python3 -c "import yaml;
  yaml.safe_load(open('.github/workflows/ci.yml'))"` → 통과.

## 2. 결과 — 실측

```
$ ./gates/run.sh frontend-fixture-reach
frontend-fixture-reach green — 진입점 src/main.tsx 에서 도달 128개(진입점 제외 127개), 금지 모듈(fixture.ts·graphFixture.ts·localEngine.ts) 0건.
```

레인 E 의 실측(`entry=src/main.tsx reached=128`, `CODE-REVIEW-20260903-E.md §5`)과 그대로 일치한다.

```
$ ./gates/run.sh frontend-fixture-reach-selftest
  ✓ ⓐ 깨끗한 진입점 (green)
  ✓ ⓑ 진입점이 fixture.ts 에 닿는다 (red)
  ✓ ⓒ 진입점 말고 도달 0건 (red)
  ✓ ⓓ tsconfig paths·baseUrl 선언 (red)
[selftest] ⓔ 판정부 스크립트 부재 → red(준비) OK (이 케이스가 재는 것이 준비 실패다)
[selftest] ⓕ 운영 진입점 부재 → red(준비) OK (이 케이스가 재는 것이 준비 실패다)
frontend-fixture-reach-selftest green — 검사 6건 전건 기대대로 (red 3 · red(준비) 2 · green 1).
```

`COLAB_GATE_JOBS=1 ./gates/run.sh selftest` — 1회차(`frontend/node_modules` 없는 상태) 실측:

```
── selftest 요약 ───────────────────────────────────────────
  선언 20 · 실행 18 · 면제 2
  green 16 / red(판정) 0 / red(준비) 2
```

red(준비) 2건 = `frontend-typecheck-selftest`·`frontend-test-selftest` — 둘 다 이 체크아웃에
`frontend/node_modules` 가 없어서다(이 레인이 만든 상태가 아니다). **선언이 19 → 20 으로,
실행이 17 → 18 로 늘었다** — 지시(§5)의 조건 그대로다. `frontend-fixture-reach-selftest` 는
green 이고 위 요약의 `green 16` 안에 포함돼 있다(§2 의 단독 실행 결과와 일치).

`cd frontend && npm ci` 로 의존을 채운 뒤 `frontend-typecheck-selftest` 단독 재실행 —
7 케이스(green 1 · red 4 · red(준비) 2) 전부 기대대로. 전체 `selftest` 재실행(2회차)의 종료
요약줄은 [미확인] — 소요가 길어(도커 기반 셀프테스트 다수) 이 기록에 옮기지 못했다(§4).

## 3. 별칭 실측 — 재확인

```
$ python3 -c "import json,re; raw=open('frontend/tsconfig.json').read(); print(json.loads(raw)['compilerOptions'].get('paths'), json.loads(raw)['compilerOptions'].get('baseUrl'))"
None None
$ grep -n 'alias' frontend/vite.config.ts
(없음)
```

레인 E 의 실측(`CODE-REVIEW-20260903-E.md §8`)과 일치 — 오늘도 별칭 선언 0건.

## 4. `[미확인]`

- **`gates/run.sh all -j 2` 전체 회차** — 지시가 `./gates/run.sh all` 을 돌리지 말라고 못박아
  실행하지 않았다. 다른 게이트와의 병렬 배치에서 `frontend-fixture-reach`·
  `frontend-fixture-reach-selftest` 가 실제로 `parallel` 로 도는지는 다음 `all` 회차가 실측한다.
- **`npm ci` 이후 `selftest` 2회차 전체 요약줄** — 1회차 요약(선언 20·실행 18·green 16·
  red(준비) 2 — §2)은 실측했다. `frontend/` 에 `npm ci` 를 채운 뒤 재실행한 2회차는
  `frontend-typecheck-selftest` 단독으로는 green(7 케이스 전부 기대대로)을 확인했으나,
  **전체 집합의 종료 요약줄**은 도커 기반 셀프테스트(`db-selftest`·`rls-effect-selftest` 등)의
  소요가 길어 이 기록 안에 옮기지 못했다. `declared`·`exempt`·구성원 도출은 `gates/run.sh`
  코드 대조로 확정했다(§2 · python 스크립트로 `ALL_GATES` 대조). 오케스트레이터가 재실행해
  최종 `green / red(판정) / red(준비)` 줄을 확인할 것을 권한다.
- **Actions 런타임** — `ubuntu-latest`·`node-version: 20` 잡 안에서 이 스텝이 실제로 도는지는
  워크트리 안에서 재현하지 못한다. YAML 유효성만 확인했다(§1 ⑸).
- **`gates/README.md:109` 의 손 숫자** — §1 ⑸ 참고. 편집 면 제한으로 이 회차에서 고치지 않았다.

## 5. 등재문 초안 (번호 없음 — 오케스트레이터가 발급한다)

> **프런트 픽스처 도달성 검사를 게이트로 승격.** 레인 E 가 만든
> `frontend/scripts/reachable-from-entry.mjs`(운영 진입점에서 상대 import 를 따라가 `fixture.ts`·
> `graphFixture.ts`·`localEngine.ts` 도달 여부를 rc 로 말하는 워커)가 사람이 손으로 부를 때만
> 돌고 있었다. `gates/tools/frontend-fixture-reach.sh` 로 게이트화하고 `frontend-gates` CI 잡에
> 실었다. 워커의 한계(상대 import 만 해석 — tsconfig `paths`/`baseUrl`·vite `resolve.alias` 를
> 못 봄)를 게이트가 매 회차 재확인해, 별칭이 하나라도 생기면 능력을 실제보다 크게 말하지
> 않기 위해 스스로 red 를 낸다(오늘은 둘 다 없음 — 레인 E·이 회차 이중 실측). 진입점만 있고
> 아무것도 당기지 않는 퇴화 상태(도달 0건)도 red 다. `frontend-fixture-reach-selftest`(6케이스 —
> green 1 · red 3 · red(준비) 2, `_expect.sh` 판정 갈래 사용)가 fail-closed 를 증명하며,
> `ALL_GATES` 의 `*selftest` 파생 규칙을 그대로 타 `selftest` 집합의 선언 수가 19 → 20(면제
> 2건 불변)이 된다. 실측 — 실물 `frontend/` 에서 도달 128개(레인 E 값과 일치) · 금지 모듈 0건 ·
> `frontend-fixture-reach` green.
> 남은 것 — `gates/README.md:109` 의 손으로 박은 셀프테스트 실행 수(현재 스스로 낡음을
> 알린 채 방치, 편집 면 제한으로 이번 회차 미수정) · `gates/run.sh all` 전체 회차의 병렬
> 배치 재현 · Actions 런타임 확인.
