# K3 계보 제안 서비스 — 착수 중단 보고 (2026-08-28)

**결론 — 코드를 쓰지 않고 멈췄다.** 생산자(ai-service `suggestLineage`)를 계약대로 세우면
**이미 서 있는 소비자(core-api 중계)의 요청이 계약 위반이라 400 으로 거절된다.** 이 어긋남은
계약 개정 또는 중계 수정 없이는 풀리지 않고, 둘 다 이 작업 항목의 금지 표면이다.

---

## 1. 진입 상태 실측

| 선행 | 대장(`work-items.yaml`, 이 워크트리 기준) | 실물 확인 |
|---|---|---|
| `K2` | `status: done` | 시드 22행 · 노드 49 · 엣지 19 — 코드 주석·시험과 일치 |
| `D2` | `status: done` | `contracts/seams/core-ai.yaml` 서 있음 · `contract-lint` green |
| `P2` | `status: conflict` | **`[미확인]`** — 이 워크트리의 기준 커밋(`8ec41e8`)에 `sessions/P2-MEASURE.md` 도 `sessions/STAGE2-PARALLEL-MAP.md` 도 없다. 2026-08-28 Ted 판정(`PLAN-SoT §9 〈179〉`)은 이 브랜치 범위 밖이다. 푸는 법 = 최신 `main` 을 기준으로 워크트리 재생성 |

완료 정의는 **작성돼 있다** — `평가셋 대비 제안 품질 ＋ D4 쓰기 경로 부재 음성 테스트 green (§8)`.

## 2. 중단 사유 ㈎ — 요청 본문이 계약과 어긋난다 (차단)

계약 `contracts/seams/core-ai.yaml` `LineageSuggestionRequest`

```
required: [scope, file]
additionalProperties: false
properties: scope · datasetNameDraft · subject · file(UploadedFileMeta)
```

소비자 실물 `services/core-api/src/colab_core/app/relay.py`
`HttpLineageSuggestionRelay.suggest` 가 실제로 보내는 본문

```
{"scope": {...}, "uploadId": <ULID>}   (+ datasetNameDraft · subject 는 있을 때만)
```

- `file` 이 **없다** — 계약의 required 다.
- `uploadId` 가 **있다** — 계약의 `core-ai.yaml` 전체에 `uploadId` 라는 낱말이 **0회**다.
  `additionalProperties: false` 라 명시적 위반이다.

**어느 쪽이 낡았나 — 이력으로 갈린다.**

- 계약의 `UploadedFileMeta` = `b151675` (2026-08-22, D2 계약 동결)
- 중계의 `"uploadId": upload_id` = `4fce105` (2026-08-23, P2)

즉 **동결된 계약이 먼저이고 중계가 그 뒤에 다른 모양으로 섰다.**

**왜 아무도 못 잡았나.** `services/core-api/tests/test_lineage_suggestions.py` 의 `_FakeAi` 는
`do_POST` 에서 본문을 읽어 **버리고**(`self.rfile.read(...)` 후 미사용) 고정 응답만 낸다.
요청 모양을 단언하는 시험이 한 줄도 없다. 계약 게이트(`contract-lint`·`contract-breaking`·
`seam-consistency`)는 **정적 스펙**만 보고 실제 요청 바이트를 보지 않는다. green-by-skip 은
아니지만 **검사 대상이 애초에 없는 자리**다.

**이 자리에서 고를 수 있는 것은 셋뿐이고 셋 다 금지 표면이다.**

1. 계약을 `uploadId` 를 받도록 개정 → `contracts/seams/` 미접촉 위반
2. 중계가 업로드 파일 메타를 읽어 `file` 을 조립하도록 수정 → `services/core-api/**` 미접촉 위반
3. 생산자가 계약 밖 필드를 조용히 받아 준다 → **계약을 코드로 개정하는 것**. 이 seam 의
   상단 주석이 금지한 「규칙이 관례로 내려앉는」 모양 그대로다

## 3. 중단 사유 ㈏ — 「가공 전 데이터」 제안을 만들 재료가 구조적으로 없다 (차단)

계약 `ParentCandidateSuggestion` 은 `parentDatasetId`(ULID) · `parentDatasetName` 이 required 다.
그 값의 출처는 D3 카탈로그 하나뿐이다.

- ai-service 는 **D3 커넥션이 없다.** 없는 것이 결정이다 —
  `domains/d10_ai_services.py` 가 「카탈로그 커넥션이 없다. D3 를 읽지도 쓰지도 못한다 —
  경계가 코드에 없는 것으로 지켜진다」로 못 박았고, 2026-08-25 Ted 판정 ㈎(`〈72〉-㉮`)가
  `K4-a` 의 D10→D3 직접 접속을 `CLAUDE.md §3-1` 위반으로 판정해 걷어낸 결과다.
- 요청 본문에도 **후보 목록이 없다.** `scope.searchedCount` 는 호출자가 센 수를 되비추는
  값일 뿐 후보가 아니다.

따라서 생산자는 두 제안 종류 중 「가공 전 데이터」를 **어떤 입력으로도 만들 수 없다.**
남는 것은 `ProcessingMethodSuggestion`(`methodText`) 하나인데, 그 재료인
`file.variables`·`file.format`·`file.gridDescription` 이 ㈎ 때문에 오지 않는다.

**즉 지금 배선에서 계약대로 선 생산자가 낼 수 있는 참인 답은 언제나 `suggestions: []` 다.**
그건 중계가 이미 `honest_empty_suggestions` 로 내고 있는 것과 같다 — 서비스를 세워도
화면이 보는 값이 바뀌지 않는다.

## 4. 중단 사유 ㈐ — 완료 정의의 오라클이 없다 (차단)

완료 정의 앞항 = `평가셋 대비 제안 품질`. **계보 제안 평가셋이 레포에 없다.**
`eval/` 에 있는 것은 `eval/k4-search/`(자연어 검색용 `measure.py`·`seed-15.sql`) 뿐이다.
㈏ 가 풀리기 전에는 제안이 항상 0건이라 품질을 잴 대상 자체가 서지 않는다.
내가 평가셋을 지어내면 **완료 판정의 오라클을 피고가 쓰는 것**이 된다.

완료 정의 뒷항(`D4 쓰기 경로 부재 음성 테스트 green`)은 이미 성립한다 — 아래 4절.

## 5. 이번에 실제로 잰 값 (축자)

**시험 기준선** — `services/ai-service` (venv 신규 생성 · `requirements-dev.txt` 핀 그대로)

```
72 passed, 26 errors in 4.26s
```

26 errors 는 전건 `COLAB_AI_TEST_DICT_DB_URL 이 없다. DB 를 못 붙인 것은 통과가 아니다`.
**skip 이 아니라 fail 로 떨어진다** — `tests/conftest.py` 의 `_require` 가 그렇게 만든다
(green-by-skip 방지 규율이 실제로 작동 중임을 확인). 마지막 알려진 값 `98/0` 과
`72 + 26 = 98` 로 개수는 일치한다. 차이는 **일회용 사전 DB 미배선 하나**다.
**26 을 RED 로 계수한다** — 못 돈 것은 통과가 아니다.

**게이트** (`./gates/run.sh`, 축자 마지막 줄)

```
ai-no-lineage-write green — 계약·코드·체인 세 층 모두에서 쓰기 경로가 없다.
  L1 계약층  seam 3건 (그중 core-ai 1건)
  L2 코드층  ai-service 텍스트 1739건 (그중 .py 1737건)
  L3 체인층  db/ai 마이그레이션 12건 · db/platform 13건

import-boundary green — 계약 전부 통과.
  D10 은 D9 를 Port 로만 읽는다 (직접 import 금지) KEPT
  Contracts: 8 kept, 0 broken.

contract-lint green — seam 3건, 룰 위반 0.
```

`ai-no-lineage-write` 는 **코드를 한 줄도 쓰지 않은 상태에서 green** 이다. 「제안만 한다 —
저장하지 않는다」의 현재 근거는 **없음으로 지켜지는 것**이고, 구현이 들어가는 순간 이
게이트가 처음으로 실제 검사 대상을 갖는다.

## 6. 하지 않은 것

- 생산 코드 0줄. 계약·중계·프런트엔드 미접촉(`git status` 깨끗).
- 온톨로지 미증설(2026-08-28 판정 준수).
- 운영 스택 무접촉 — 일회용 DB 도 띄우지 않았다(구현 전이라 필요가 없었다).
- red 픽스처 증명 없음 — 되돌릴 생산 코드가 없다.

## 7. 풀려면 필요한 판정 (Ted)

㈎ 요청 본문 한 자리. **계약(`file` 메타)과 중계(`uploadId`) 중 어느 쪽을 정본으로 두는가.**

- ㈎-1 계약을 정본으로 → 중계가 업로드 파일 메타를 읽어 `UploadedFileMeta` 를 조립한다.
  바뀌는 것 = `services/core-api` 중계 + 시험. 계약 개정 0.
- ㈎-2 중계를 정본으로 → 계약이 `uploadId` 를 받고 ai-service 가 그것으로 무엇을 하는지
  정한다. 다만 ai-service 는 업로드 표를 못 읽으므로 `uploadId` 만으로는 아무것도 못 한다 —
  ㈏ 를 함께 풀어야 성립한다.

㈏ 「가공 전 데이터」 후보를 **누가 고르는가.** 검색(`〈72〉-㉮`)에서 이미 「찾는 것은
core-api」로 갈랐다. 계보 제안도 같은 모양(core-api 가 후보를 뽑아 요청에 실어 보내고
ai-service 는 순위·근거만)으로 가는지, 아니면 다른 판정인지.

㈐ 계보 제안 평가셋을 누가 만드는가 — ㈎㈏ 확정 후에야 대상이 선다.
