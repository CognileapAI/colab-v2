# `R14` · 14차 계약 동결 해제 — 등재문 초안 (번호 미발급)

작성 2026-09-02 · 워크트리 `lane-r14`(브랜치 `lane-r14` · `main` `883e4a1` 기점) · 커밋 `0bf6f39`.
⛔ **레인은 `PLAN-SoT §9` 에 직접 쓰지 않는다**(`CLAUDE.md §1-b` ⑶). 직전 발급은 `〈281〉` 이고
번호 발급·등재는 오케스트레이터 몫이다. 직전 해제 = **13차 `〈276〉`** ⟹ 이 회차는 **14차**.

---

## ㉲ 8필드 등재문 (§9 한 항목 · 표 한 행으로 옮겨 붙일 것)

| 〈n〉 | **데이터셋 기간의 끝을 조건부로 — `DataPeriod.end` 를 nullable 로. 14차 동결 해제** | **집행 ＋ 실측 (2026-09-02 · 워크트리 `lane-r14`)** … 아래 ①~⑧ |

**① 회차 번호** — **14차**(직전 13차 `〈276〉` · 등급 **㉯** · `sessions/X2-FREEZE-PROTOCOL.md §5-㉯`).

**② 값(파일·op·필드 단위)** — **op 총계 불변(54)** · **필드 형 변경 1**
(`contracts/seams/fe-core.yaml` `DataPeriod.end`: `{ type: string, format: date-time }` →
`{ type: [string, "null"], format: date-time }`). `required: [start, end]` 는 **그대로 두었다** —
같은 파일 `ProjectPeriod` 가 이미 쓰는 **required-but-nullable** 모양을 그대로 따랐고,
그래서 새 무늬가 0건이다. 산문에 무기한 의미 3줄 추가.
파일 = 계약 1 · 생성물 1(`frontend/src/generated/fe-core.ts` · `openapi-typescript 7.13.0`) ·
서버 2(`app/routes/catalog.py` · `domains/d3_catalog.py`) · 화면 4(`detail/format.ts` ·
`project/format.ts` · `upload/UploadModal.tsx` · `upload/RegisterArea.tsx`) ·
시험 2(`services/core-api/tests/test_dataset_registration.py` ＋ 신설
`frontend/test/period-open-ended.test.ts` · `frontend/test/upload.test.tsx`) · **DB 0**.

**③ 근거** — Ted 판정 2026-09-02 축자 「기간은 있을 수도 없을 수도 있다(optional). 있으면
시작은 있고 **끝은 조건부**다 — 끝이 없으면 무기한·진행 중이다」. 멈춰 세운 회차 =
`notes/P4X-LEDGER-PENDING.md` ㉮(「계약 개정 없이는 성립하지 않는다」). 열린 판정의 출처 =
`03-HANDOFF §4 #62` 「기간의 입력 형태」(`〈280〉` 이 화면에 두 칸을 넣으면서 남긴 자리).

**④ 가·파 판정과 게이트 출력** — ⚠ **파괴다(계수·실질 둘 다).**
`contract-breaking` = **`7 changes: 7 error, 0 warning, 0 info`** ·
`[response-property-became-nullable]` × 7
(`POST /datasets` 201 · `GET /datasets/{datasetId}` 200 · `PATCH /datasets/{datasetId}` 200 ·
`POST /projects` 201 · `GET /projects/{projectId}` 200 · `PATCH /projects/{projectId}` 200 ·
`PUT /projects/{projectId}/status` 200).
⭑ **요청 쪽만 보면 가산(필수 완화)인데 같은 스키마가 응답에도 서 있다** — 읽는 쪽은
「끝은 언제나 문자열」을 전제할 수 있었고 그 전제가 깨진다. **한 스키마가 요청·응답을 겸하면
완화가 파괴로 나온다** — §4-1 「가산으로 보이는 의미 파괴」의 거울이다.
⚠ **회차 지시문의 전제 「`contract-breaking` 은 ERR 0 이다」는 틀렸다.** 실측이 ERR 7 이다.
**red → 커밋 후 green 전이** — 게이트 기준이 git HEAD 라 커밋 전 red(exit 1), 커밋 후 green.
7차 `〈151〉` 과 같은 모양이다.
전체 = **green 37 / red(판정) 0 / red(준비) 0**(`./gates/run.sh all -j 1` · 직렬 · 기준선과 같다).
`contract-lint`·`generated-up-to-date`·`seam-consistency`·`event-lint`·`event-breaking`·
`migration-single-head`·`schema-diff` 전건 green. **우회·비활성화·검사 축소 0건.**
⚠ **커밋 전 한 번은 `db-selftest` 도 red 였다** — 같은 커밋에서 단독 재현 시 green 이고
커밋 후 `all -j 1` 에서도 green 이다. **판정이 아니라 환경**이다(`CLAUDE.md §1-b` ⑸).

**⑤ 소비자 수와 그 측정법** — **읽기 소비자 2건**(0건이 아니다 · 그래서 ㉯ 다).
측정 = `grep -rn "period\.end\|period\?\.end\|p\.end" frontend/src --include='*.ts' --include='*.tsx' | grep -v generated`
⟹ `detail/format.ts`(`formatPeriod`) · `project/format.ts`(`dataPeriod`) 둘이 `end` 를
비-null 로 읽고 있었다. **둘 다 같은 회차에 고쳤다**(§5-㉰-4 집행 없는 신설·완화 금지).
`project/format.ts` 의 `projectPeriod` 와 `ProjectFormModal.tsx` 는 `ProjectPeriod` 쪽이라
무관하고 이미 null 을 안다. 서버 쪽 `period_end` 참조 전수는 `d5_ingestion`·`ports/ingestion`이
이미 `str | None` 이라 무접촉. `tsc --noEmit` = 신규 오류 0
(`test/e01-apply-points.test.ts` 의 4건은 `main` `883e4a1` 에도 있는 기존 값이다).

**⑥ 마이그레이션 건수** — **0건.** 증거 = `git diff --stat db/` **0줄** · head `0011` 그대로
(`0012` 미사용) · `db/platform/schema.sql:398-399` 축자 `period_start timestamptz` ·
`period_end timestamptz` 로 **둘 다 처음부터 nullable** 이고 :405 의
`CHECK (period_start IS NULL OR period_end IS NULL OR period_start <= period_end)` 도
NULL 을 이미 허용한다. **DB 가 계약보다 먼저 열려 있었다** — 좁혀 놓은 쪽이 계약이었다.

**⑦ 승인자·일자** — **Ted · 2026-09-02**(기간 optional ＋ 끝 조건부 판정 ＋ 14차 해제 승인).

**⑧ 이번에 세지 않은 축** —
- ⓐ **UI 스펙 19 의 문면** — 「기간 = 한 칸 자유 문장」이 그대로다. **레포 밖 문서라 이 회차가
  편집하지 않았다.** 화면은 두 칸 ＋ 끝 선택으로 서 있고 **문면만 낡았다.** 다음 회차 진입조건.
- ⓑ ⚠ **열린 기간의 표기 문면 = `[미확인]`** — 정본이 정하지 않았다. 이 회차가 고른 값은
  상세 격자 `2025-06 ~ 진행 중` · 소속 데이터셋 표 `2025-06~`(같은 파일 `projectPeriod` 의
  꼬리 물결과 맞춘 것). **레포 안 선례를 따른 것이지 정본 근거가 아니다.** Ted 판정 대상.
- ⓒ **staging 배포** — 안 했다. 배포 승인이 없고 staging 무접촉이 회차 조건이었다.
  **배포 전까지 실물은 옛 계약을 든 이미지로 돈다.**
- ⓓ **브라우저 실왕복** — 재지 않았다. 화면 증거는 vitest 층까지다.
- ⓔ **기존 저장 행** — 끝이 NULL 인 `d3_dataset_autometa` 행이 실물에 몇 건인지 세지 않았다
  (staging 무접촉). 종전 응답 코드가 그런 행의 기간을 통째로 떨어뜨리고 있었으므로
  **이번 변경으로 화면에 새로 나타나는 기간이 있을 수 있다.**
- ⓕ **`work-items.yaml` 귀속** — 이 판정을 소유하는 WU 가 **0건**이다. 「기간 입력 형태」는
  `03-HANDOFF §4 #62` 행과 `notes/P4X-LEDGER-PENDING.md` ㉮ 에만 서 있었다. **없는 항목에
  적지 않았다** — 귀속은 오케스트레이터 판정이다.
- ⓖ 병합·병합 순서 — 레인 밖이다.

---

## ㉱ 증거 — 회귀 수치 (전 → 후)

| 단위 | 전(`883e4a1` 기준선) | 후 | 차 |
|---|---|---|---|
| core-api | 534 | **538** | ＋4 |
| frontend | 432 | **438** | ＋6 |
| viz-render | 232 | **232** | 0 |
| pipeline-worker | 238 | **238** | 0 |
| ai-service | 145 | **145** | 0 |
| 게이트 | green 37 / red 0 | **green 37 / red 0** | 0 |
| op 총계 | 54 | **54** | 0 |
| 501 표 | 무변경 | 무변경 | 0 |

**새 시험이 못 박는 것 6** — ⑴ `{start, end: null}` 등록이 201 이고 응답이 `end: null` 로
돌아온다 ⑵ `end` 열쇠를 아예 뺀 등록도 같다(서버가 계약보다 넓은 쪽이라 문면을 안 깬다)
⑶ 두 경우 모두 DB 에 `period_start` 가 남고 `period_end` 가 NULL 이다 ⑷ 시작 없는 끝은
생성·수정 두 경로에서 같은 400 문구다 ⑸ 소속 데이터셋 표가 끝 없는 기간을 떨어뜨리지 않는다
(`periods_of` 회귀) ⑹ 화면 — 끝 칸을 비우면 `end: null` 이 실리고, 시작이 비면 기간을
아예 싣지 않으며, 열린 기간이 `~ 진행 중` / 꼬리 물결로 그려진다(기존 표기는 회귀 시험으로 고정).

---

## 참고 — 이 회차가 `X2-FREEZE-PROTOCOL.md §1` 에 남길 한 줄 (오케스트레이터가 등재 시 함께)

⭑ **회차표 한 행(14차)은 이 레인이 이미 세웠다** — 프로토콜 문서가 회차표를 소유하므로
`§1` 표에 `| **14** | …` 행을 직접 넣었다. **번호 발급이 아니다**(`〈n〉` 자리는 비워 뒀다).
아래 개정 두 줄은 번호가 나온 뒤 오케스트레이터가 붙인다.

**⟨개정 2026-09-02 · `PLAN-SoT §9 〈n〉`⟩ 14차가 발급됐다 — 다음 해제는 15차다.** 원문은 지우지 않는다.
**14차 = `〈n〉`**(`fe-core.yaml` `DataPeriod.end` 를 `[string, "null"]` 로 · `required` 무변경 ·
2026-09-02 Ted 승인 · 등급 ㉯ — **파괴적 변경 ERR 7 ＋ 소비자 ≥ 1**).
⚠ **10차 이래 처음으로 게이트 계수 자체가 ERR ≥ 1 인 회차다** — 7차 `〈151〉` 이후 둘째이고,
7차와 달리 **소비자가 0이 아니다.** 소비자 둘을 같은 회차에 옮겼다.
⭑ **`ProjectPeriod` 의 모양을 그대로 따랐다** — required-but-nullable. 새 무늬 0건이고,
이제 두 기간 타입이 「비어 있음은 `null` 로 말한다」를 한 규칙으로 쓴다.
⭑ **§5-㉰-6(묶음 쪼개기) 회피** — 「계약만 먼저 / 화면은 나중」으로 ㉮ 를 만들지 않았다.
계약·생성물·서버 수용·서버 응답·질의·화면 입력·화면 표기·시험을 **한 회차에** 걷었다.
⚠ **마이그레이션 0 이 이번엔 예외가 아니다** — DB 열이 처음부터 nullable 이었다.
좁혀 놓은 쪽이 계약이었고, 이 회차는 **계약을 실물에 맞춘 것**이다.
