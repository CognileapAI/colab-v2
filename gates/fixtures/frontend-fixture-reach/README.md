# frontend-fixture-reach 픽스처 — `frontend-fixture-reach-selftest` 가 쓰는 red/green 트리

이 자리의 트리는 진짜 `frontend/` 가 아니다. `gates/tools/frontend-fixture-reach.sh` 가
`COLAB_FRONTEND_DIR` 로 이 트리들을 하나씩 가리켜 **게이트가 red 를 낼 수 있는지**를 잰다.
각 트리는 자기 `scripts/reachable-from-entry.mjs` 사본(진짜 `frontend/scripts/` 와 동일 파일)을
들고 다닌다 — 판정부 자체가 없는 상태(`no-script/`)도 재야 하기 때문이다.

| 트리 | 무엇을 재나 | 기대 |
|---|---|---|
| `clean/` | 진입점이 `app.ts` 하나만 당긴다. 금지 모듈 없음, 도달 2건 | green |
| `reachable/` | 진입점이 `fixture.ts`(금지 모듈)에 실제로 닿는다 | red |
| `empty-entry/` | 진입점이 아무것도 `import` 하지 않는다 — **다른 모듈 0건 도달** | red |
| `no-script/` | `scripts/reachable-from-entry.mjs` 자체가 없다(판정부 부재) | red(준비 · 78) |
| `no-entry/` | `src/main.tsx`(운영 진입점)가 없다 | red(준비 · 78) |
| `alias-declared/` | `tsconfig.json` 이 `compilerOptions.paths`·`baseUrl` 을 선언한다 — 이 워커는 상대 import 만 따라가므로 별칭 뒤는 못 본다. 진입점 자체는 깨끗하다(`clean/` 과 동일) | red |

`reachable-from-entry.mjs` 는 상대 import 만 따라가고 파일 시스템 밖에 아무것도 쓰지 않으므로,
`mktemp -d` 로 복사하지 않고 이 트리를 **그대로** 가리켜 돈다(읽기만 한다).
