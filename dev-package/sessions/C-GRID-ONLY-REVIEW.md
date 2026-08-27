# WU `C` 격자 전용 업로드 — 착수 전 검증 (2026-08-27)

> **판정 근거는 `PLAN-SoT §9 〈111〉`·`〈114〉`·`〈120〉` 에 있다. 여기는 검증 결과다.**
> 읽기 전용 점검이고 코드·정본을 고치지 않았다.

---

## 0. 결론 먼저 — **코드는 이미 집행됐다. 남은 것은 문서와 데이터다**

- **`STAGE2-PREP §2-7` 의 착수 지시가 시효를 지났다.** 거기 적힌 「`d5_ingestion.py:182` 의
  `if not readable:` 를 `if bodies and not readable:` 로」는 **2026-08-26 커밋 `4a8e41b`
  「격자 전용 업로드를 워커 처리에서 제외한다 (Ted 판정 ⓐ)」로 이미 해소**됐다.
  `〈114〉` 로 등재돼 있고 `origin/main` 에 들어 있다(`git branch -a --contains 4a8e41b`).
- **⚠ 그리고 그 한 줄 지시는 채택했더라도 틀린 답이었다.** §2 참조.
- **미집행 셋** — ⑴ `〈79〉-⑷` 문안 개정 ⑵ `STAGE2-PREP §1` 9행·`WORK-UNITS §11` 상태 갱신
  ⑶ `〈120〉` 실패로 굳은 3건 회수(만료 대기).

## 1. 실물 — 무엇이 어디에 있나

`services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py`

| 자리 | 실물 |
|---|---|
| `:160-161` | `bodies = [f for f in work.files if f.kind == "본체"]` · `grids = [... "기준 격자 파일"]` |
| `:165` | `grid_dir, grid_resolution = self._resolve_grid_axes(work, res, grids)` — **감지보다 먼저 돈다** |
| `:167-182` | **격자 전용 분기** — `if not bodies and grids:` → `record_status(ready=True, renderable=False, metadata_complete=False)` → `upload.ready` → `return res` |
| `:184-191` | **빈 업로드 분기** — `if not bodies and not grids:` → ② 발행 후 `_fail(detail="업로드에 파일이 없다")` |
| `:193-206` | 감지 루프 — `for f in bodies:` 만 순회. `readable = {s for s in seen if s is not None}` |
| `:208-211` | `if not readable:` → `_fail(reason="형식 인식 실패", klass="영구", detail="본체 전건이 알려진 매직바이트가 아니다")` |
| `:130-136` | `_fail` = `record_status(ready=False, failed_at=now(), failure_class, failure_reason)` ＋ `upload.failed` 발행 |
| `:294-346` | `_resolve_grid_axes` — 축 확정분만 `record_file_axes_row`, 못 정한 것은 `res.rejected` 로 거절 |

**지금 `:182` 는 `return res` 다.** 착수 지시가 가리킨 행 번호는 옛 파일 기준이며,
`if not readable:` 은 `:208` 로 밀려 있다.

## 2. 제안 문안 `if bodies and not readable:` — **채택했으면 안 됐다**

격자 전용 업로드를 그 한 줄만으로 통과시키면 **셋이 깨진다.**

**⑴ ② 이벤트가 거짓말을 한다.** `bodies == []` 이면 `per_file == []` · `readable == set()` ·
`fmt is None` 이다. 그런데 `:205` 의 `file.format-detected` 발행은 분기보다 **위**에 있어
`format: null` · `perFile: []` 이 그대로 나간다. 계약 `core-pipeline.json#FormatDetectedPayload`
가 `format: null` 을 **감지 실패**로 적었다(`〈114〉-㉮`). 안 읽은 것을 읽어 보고 실패했다고
말하는 자리다. 실제 구현이 ② 를 **아예 내지 않는** 이유가 이것이다.

**⑵ 빈 업로드(본체 0 · 격자 0)까지 함께 통과한다.** `bodies` 가 비면 조건이 거짓이므로
파일이 하나도 없는 업로드도 실패를 안 낸다 — **진짜 실패를 삼킨다.**
실제 구현은 `:184` 로 경우 ⑶ 을 갈라 막았다(상세 「업로드에 파일이 없다」).

**⑶ ⚠ `stage1=False` 경로에서는 실패가 사라지지도 않는다 — 사유만 바뀐다.**
분기를 통과한 뒤 `:220` 파이프라인 루프가 `for f in bodies:` 라 `results == {}` → `ok == {}`
→ `:228 if not ok:` 성립 → `_classify_failure([])` 가 표에 안 걸려 **`("upload.failed", "내부 오류", "영구")`** 로 떨어진다.
즉 「형식 인식 실패」가 **「내부 오류」로 갈아탈 뿐**이다. **stage 2 는 `stage1=False` 로 도는 자리다** —
이 결함은 지금 안 보이고 stage 2 에서 켜진다. 실제 구현은 `:182` early return 이라 stage 여부와 무관하다.

**→ 제안은 「예/아니오」로 아니오다.** 실제 구현(분기 둘 + early return)이 옳다.

### 실제 구현으로 격자 전용이 밟는 경로

`_resolve_grid_axes` (축 판별 · 격자 행 생성) → `:167` 분기 → `record_status(ready=True)` →
`upload.ready(renderable=false · metadataComplete=false · gridResolution=[…])` → 종료.
**`d5_upload.ready = true` · `failed_at IS NULL` · `failure_reason IS NULL`.**
`upload.failed` 도 `file.format-detected` 도 없다.

### 진짜 실패를 삼키지 않는다는 증명

`bodies` 가 1건 이상이면 `:167`·`:184` 두 분기가 모두 거짓이라 **감지 루프와 `:208` 이 그대로 돈다.**
`test_grid_only_upload.py::test_a_body_that_cannot_be_detected_still_fails` 가 본체 1(정크) ＋ 격자 1 로
`upload.failed` 1건 · `reason == "형식 인식 실패"` · `ready is False` 를 못 박는다.

## 3. `〈111〉-㉷` 2차 영향 둘 — 확인·반증

**ⓐ `failed_at` → 「처리 중」 제외 → reaper CASCADE : 절반만 맞다.**
`domains/d5_ingestion.py:45-55` 의 `_PROCESSING` 은 `u.ready = false AND u.failed_at IS NULL AND EXISTS(최근 이벤트)` 다.
`_REAP`(`:123-128`)은 `expires_at <= now AND NOT _PROCESSING` 이므로 **`failed_at` 이 「만료 전 삭제」를 만들지는 않는다** —
없애는 것은 **만료 시점의 유예**다. 고침 뒤에는 `ready = true` 라 이 건도 `_PROCESSING` 에 안 든다.
**즉 고침은 「D3 성공 ↔ D5 실패」 갈림은 없애지만, 만료 시 CASCADE 자체는 그대로다.**
그것은 결함이 아니라 `〈120〉-㉮` 가 택한 회수 경로다. CASCADE 실물 = `0004:171`(`d5_upload_file`) · `0004:207`(`d5_pipeline_event`).
후주입이 끝난 건은 `d3_file` 로 옮겨 가 있으므로 삭제돼도 잃는 것이 없다.

**ⓑ `pending_uploads` 재처리 경로 부재 : 맞다. 그리고 고쳐도 안 생긴다.**
`d5_ingestion.py:466-474` 가 `u.ready = false AND u.failed_at IS NULL AND u.registered_at IS NULL` 을 요구한다.
고침 뒤 격자 전용은 `ready = true` 라 여전히 이 집합 밖이다 — **다만 재처리가 필요 없는 상태다.**
**⚠ 이미 실패로 굳은 3건은 코드 고침으로 낫지 않는다.** `〈120〉` 이 그것을 알고 소급 복구를 기각했다.

## 4. 시험 — **깨지는 기존 단언은 0건이다**

- **`test_stage1_worker.py:94` 는 회귀 지점이 아니다.** 그 단언
  `assert types == ["file.format-detected", "upload.failed"]` 는
  `test_stage1_still_fails_closed_on_an_unknown_format` 의 것이고 **본체 1건(정크 `.bin`)** 을 태운다.
  격자 전용과 겹치지 않는다. `〈111〉-㉷` 의 회귀 지점 지목이 **틀렸다.**
- **`frontend/test/grid-attach.test.tsx:45-66` 도 아니다.** 그 구간은 `fakes()` 의
  `UploadStatus` 픽스처이고 이미 `ready: true` · `failure: null` 이다. 옛 동작을 안 박아 놨다.
- **RED-first 는 이미 충족됐다** — 커밋 `4a8e41b` 가 `test_grid_only_upload.py` 6건을 같은 커밋에 넣었다:
  실패 무발생 · 격자 행·축 발화 · `stage1=True` 동일 · **본체 감지 실패 존치(음성)** ·
  빈 업로드 상세 분기 · 읽히는 본체 무변경. 워커 시험 129 → 135 passed.
- **보강 권고 1건** — `stage1=False` 격자 전용을 못 박는 단언이 없다. §2-⑶ 이 그 경로의 함정이다.
  `test_grid_only_upload_emits_no_failure` 는 기본값(`stage1=False`)으로 돌므로 사실상 덮여 있으나,
  **의도가 이름에 안 적혀 stage 2 에서 지워질 수 있다.** 이름이나 주석에 남긴다.

## 5. `〈79〉-⑷` 개정 문안

**현행 원문**(`PLAN-SoT.md:348`)

> **⑷ `upload.ready` 의 뜻이 한 줄 늘어난다** — 「**본체 감지가 끝났고, 함께 올라온 격자 파일의 축이 확정되거나 거절됐다**」. ⚠ **단계 수(`STAGE_ORDER` 2단계)는 그대로다** — 늘어나는 것은 **ready 의 판정 조건**이지 단계가 아니다. **격자가 거절돼도 `ready` 는 온다** — 거절은 그 격자만 막고 본체 등록을 막지 않는다(`〈63〉-ⓒ`).

**개정안** — 뒤에 붙인다(문장을 지우지 않는다).

> ⟨개정 2026-08-27 · `〈114〉` 반영⟩ **⚠ 「본체 감지」는 본체가 있을 때의 조건이다 — 본체 0건이 `ready` 로 끝나는 상태는 합법이다.** 본체 0 · 격자 1 이상인 **격자 전용 업로드**는 축 판별을 마치면 곧장 `upload.ready` 이며, **`file.format-detected` 도 `upload.failed` 도 내지 않는다**(감지 대상이 공집합이고, 계약이 `format: null` 을 감지 실패로 적었다). 이때 `renderable = false` · `metadataComplete = false` 이고 `d5_upload.failed_at` 은 NULL 로 남는다. **본체 0 · 격자 0(빈 업로드)은 다른 경우다** — 그대로 실패이고 상세 「업로드에 파일이 없다」로 갈라 적는다. **본체가 1건 이상인데 감지가 실패하면 그대로 실패다**(`〈114〉-㉯`).

**동반 갱신 둘** — `STAGE2-PREP §1` 9행 ⬜ → ✅(`〈114〉`) 및 `§2-7` 의 한 줄 지시 정정 ·
`WORK-UNITS §11` 2단 `C` 표기.

## 6. 계약 0 · 마이그레이션 0 — 확인

`git show --stat 4a8e41b` = **파일 2개뿐**
(`services/pipeline-worker/src/.../d5_ingestion.py` +26 · `services/pipeline-worker/tests/test_grid_only_upload.py` +116).
`contracts/` 무변경 · `db/platform/versions/` 무변경 · 스키마 무변경.
`〈79〉` 가 이미 「`0004` 무수정 확정」을 적었고, `〈114〉-㉰` 가 마이그레이션을 부르는 안 ⓑ 를 기각한 결과와 일치한다.

## 7. 놓치면 위험한 것

1. **없는 코드를 또 고치는 것.** 착수 지시대로 `:182` 를 열면 이미 다른 코드가 서 있다.
   그 자리에 `if bodies and not readable:` 을 겹쳐 넣으면 §2 의 결함 셋이 **뒤늦게** 들어온다.
2. **`〈120〉` 3건이 미집행으로 남아 있다**(`03-HANDOFF.md:195` ⬜). 코드 고침은 소급하지 않는다.
   **실행 대상·시점을 이번 회차 진입조건에 다시 적지 않으면 또 넘어간다.**
3. **`stage1=False` 회귀.** stage 2 가 켜는 순간 `:167` early return 이 유일한 방벽이다.
   파이프라인 루프를 재배치할 때 이 분기를 뒤로 밀면 「내부 오류」로 되살아난다.
4. **워커 재배포를 수반한다** — `STAGE2-PREP §2` 의 「1단 재기동과 묶지 않는다」는 유효하다.
   다만 **묶지 말아야 할 것이 코드 변경이 아니라 재배포**임을 유의한다.

---

*작성 2026-08-27. 읽기 전용 검증이고 판정을 담지 않는다 — 판정은 `PLAN-SoT §9`.*
