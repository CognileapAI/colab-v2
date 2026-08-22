# D2 — 계약 게이트 조각 (`contract-lint` · `contract-breaking`)

D2의 완료 판정은 "spectral + oasdiff 게이트 green"(`WORK-UNITS.md §6`)이다.
이 세션은 **그 두 오라클을 실제로 동작하게** 만들었다. seam 스펙 자체는 이 세션의 범위가 아니다
(`contracts/seams/` · `events/` · `schemas/`에는 한 글자도 쓰지 않았다).

---

## 1. 무엇이 어디에 있는가

| 파일 | 역할 |
|---|---|
| `contracts/.spectral.yaml` | 린트 룰셋. `spectral:oas` 확장 + 프로젝트 고유 룰 6개 |
| `contracts/package.json` · `package-lock.json` | 도구 버전 고정 (`@stoplight/spectral-cli` 6.16.3) |
| `contracts/.gitignore` | `node_modules/` 제외 |
| `gates/tools/contract-lint.sh` | spectral 실행기 |
| `gates/tools/contract-breaking.sh` | oasdiff 실행기 |
| `gates/tools/contract-selftest.sh` | 두 게이트의 fail-closed 증명 |
| `gates/run.sh` | `contract-lint` · `contract-breaking` · `contract-selftest` 배선 |

`gates/run.sh`의 기존 관례를 그대로 유지했다 — 미구현 게이트는 여전히 red, 인자 없음은 usage + exit 2,
알 수 없는 이름은 exit 2. `planning-freshness`와 같은 `exec` 위임 형태다.

---

## 2. 룰셋 — 왜 이 룰들인가

`spectral:oas` 기본 룰 중 seam 동결에 치명적인 것을 **warn → error로 승격**했다
(`operation-operationId`, `-unique`, `-valid-in-url`, `operation-description`, `info-description`,
`oas3-valid-schema-example`, `oas3-valid-media-example`). seam은 동결 대상이라 "경고인 채로 머무는 계약"이라는
중간 상태가 없다. 실행 시에도 `--fail-severity=warn`을 줘서 남은 warn도 red로 센다.

프로젝트 고유 룰 6개 (각 룰에 근거 주석이 파일에 달려 있다):

| 룰 | 강제하는 문서 규칙 |
|---|---|
| `colab-error-envelope-ref` | 4xx/5xx 본문은 `common.json#/$defs/ErrorEnvelope`를 `$ref` — 공통 에러 형태 정의 |
| `colab-operation-has-error-response` | 모든 오퍼레이션에 실패 응답 1개 이상. 위 룰이 공허해지는 것을 막는 짝 룰 |
| `colab-id-must-ref-ulid` | `id`·`*_id`는 `common.json#/$defs/Ulid`를 `$ref` — CLAUDE.md §3-6 |
| `colab-no-numeric-confidence` | 확신도/점수를 숫자 타입으로 노출 금지 — CLAUDE.md §3 "숫자·퍼센트 필드 없음" |
| `colab-no-batch-approval` | `approve-all` 류 경로 금지 — CLAUDE.md §3 "[모두 승인] 없음" |
| `colab-no-absolute-server-url` | `servers`에 환경 고정 절대 URL 금지 — 배포 단위 5개가 환경마다 오리진이 다르다 |

앞의 두 `$ref` 룰은 `resolved: false`다. spectral이 `$ref`를 풀어버리면 "참조했는가"를 판정할 수 없다.

---

## 3. oasdiff — 도구 선택 근거

| 후보 | 판정 |
|---|---|
| **`tufin/oasdiff` 도커 이미지** | **채택.** `docker run`으로 바로 돌았고 `breaking -c`(composed) 모드가 seam 다중 파일을 지원한다. Go 툴체인이 이 환경에 없어도 된다 |
| Go 바이너리 (`go install`) | 탈락 — 환경에 go가 없다 |
| npm `oasdiff` | 탈락 — 레지스트리의 `oasdiff` 패키지는 `0.0.1-security` 플레이스홀더다. 실물이 아니다 |
| `openapi-diff`(OpenAPITools, Java) | 탈락 — java가 없고, OpenAPI 3.1 지원이 뒤처진다 |

이미지는 **태그가 아니라 다이제스트로 고정**했다 (`tufin/oasdiff@sha256:7dbcbd1c…`).
`:latest`는 조용히 바뀌는 게이트이고, 조용히 바뀌는 게이트는 게이트가 아니다.

**비교 기준(frozen seam) = git `HEAD` 판의 `contracts/`, 대상 = 워킹트리 판.**
별도의 frozen 사본을 레포에 두면 그 사본 자체가 새 드리프트 면이 된다(누가 갱신하는가 문제).
seam은 "커밋된 것이 동결된 것"이다. CI에서 PR을 볼 때는 `COLAB_BREAKING_BASE_REF=origin/main`으로 기준을 옮긴다.
`--fail-on ERR`이라 파괴적 변경만 red고, WARN(예: deprecation 예고)은 red로 세지 않는다.

---

## 4. 의존성 고정과 green-by-skip 금지

- 버전은 `contracts/package.json` + `package-lock.json` 한 곳에서만 정한다. **`npx` 최신 끌어오기를 쓰지 않는다.**
- 게이트는 `contracts/node_modules/.bin/spectral`이 없으면 `npm ci`를 한 번 시도하고,
  그것도 실패하면 **red**다. "도구가 없어 검사를 못 했다"는 통과가 아니다.
- docker 부재·데몬 불능·이미지 pull 실패도 전부 red다.
- **대상 0건도 red다.** 계약이 하나도 없는데 계약 게이트가 green이면 D2 완료 판정이 공짜가 된다.
  단 하나의 예외: 기준(HEAD)에 seam이 0건이고 워킹트리에 있으면 그건 **최초 동결**이라
  파괴할 이전 계약이 없다 → `contract-breaking`만 green. `contract-lint`는 그래도 실제 스펙을 린트한다.

---

## 5. selftest가 증명하는 것

`./gates/run.sh contract-selftest` — fixture는 전부 `mktemp -d` 임시 디렉터리다. 실제 계약 디렉터리에 쓰지 않는다.

**contract-lint**
1. 규칙을 지킨 스펙 → green (항상 red를 내는 게이트가 아님을 증명)
2. `operationId` 누락 → red
3. 4xx 인라인 에러 스키마 → red
4. ID 인라인 정의 → red
5. 숫자 확신도 필드 → red
6. 배치 승인 엔드포인트 → red
7. seam 0건 → red
8. spectral 부재 + 설치 실패 → red (skip 아님)

**contract-breaking**
9. 변경 없음 → green
10. 엔드포인트 제거 → red
11. 필수 파라미터 추가 → red
12. seam 0건 → red
13. docker 불능 → red (skip 아님)

---

## 6. 실행 결과와 그 근거

이 세션 도중 다른 작업에서 `contracts/seams/core-ai.yaml` · `core-viz.yaml` 2건이 워킹트리에 나타났다
(아직 커밋 전, `frontend-core`는 미작성). 그 상태에서의 실측:

| 게이트 | 결과 | 이유 |
|---|---|---|
| `contract-lint` | **red** | 실제 위반 7건 — `core-viz.yaml`의 **`/screenshots` POST 응답에 `401` 키 중복**(YAML 파서 오류), 그리고 ID 6곳(`suggestionId`, `appliesToParentDatasetId`, `uploadId`, `paletteId`×3)이 `Ulid`를 `$ref`하지 않고 인라인 정의 |
| `contract-breaking` | **green** | 기준(git HEAD)에 seam이 0건 — **최초 동결**이라 파괴할 이전 계약이 없다. 별도로 `COLAB_CONTRACTS_BASE=contracts`로 자기 자신 대비 비교를 돌려 docker/oasdiff 경로가 실제 스펙(외부 `$ref` 포함)에서 동작함을 확인했다 |
| `contract-selftest` | **green** | 13개 케이스 전부 기대대로 |
| `planning-freshness` | **green** | 15개 임베드 블록 전부 MATCH — 기존 게이트를 깨지 않았다 |
| 인자 없음 / 모르는 이름 | exit 2 | 기존 관례 유지 |

**seam이 비어 있었다면 두 게이트 모두 red가 맞다**는 판단은 그대로다.
빈 계약을 green으로 보는 것은 green-by-skip에 가깝다 — v1 CI가 DB 없이 돌아 RLS 테스트를
green-by-skip 했던 실패와 같은 형태다("검사할 것이 없었다"가 "통과했다"로 기록되는 것).
`contract-lint`의 지금 red는 정확한 신호다: seam 2건이 프로젝트 규칙을 아직 어기고 있고,
`paletteId`처럼 ULID가 아닌 것이 정당하다면 그 판단을 룰의 예외로 **명시**해야 한다(조용히 넘어갈 수 없다).

> 측정 직후 `fe-core.yaml`이 추가되어 현재 seam은 3건이다. 게이트를 다시 돌리면 대상 수만 달라진다.

---

## 7. 남은 한계

1. **`contracts/events/` (async 봉투)는 이 게이트가 보지 않는다.** OpenAPI가 아니라 JSON-Schema 봉투라
   spectral/oasdiff의 대상이 아니다. 이벤트 계약 게이트는 별도로 필요하다.
2. **`schemas/common.json` 자체의 변경은 breaking으로 잡히지 않는다** — seam이 그것을 `$ref`할 때만
   해석된 스키마 차이로 드러난다. seam이 참조하지 않는 정의가 바뀌면 조용하다.
3. **오프라인 CI에서는 첫 실행이 반드시 실패한다.** 의도된 설계(red > skip)지만, CI는
   `npm ci --prefix contracts`와 이미지 pull을 별도 단계로 미리 돌리는 편이 낫다.
4. **oasdiff의 breaking 판정 기준을 우리가 조정하지 않았다.** 기본 룰 그대로다.
   프로젝트에 맞지 않는 오탐이 나오면 `--err-ignore` 설정 파일을 추가하되, 그때는 근거를 여기 적는다.
5. **`generated-up-to-date`(codegen diff)는 여전히 미구현 red다.** contracts/README 규칙 3·4를
   강제하는 게이트로 아직 없다.
