# `P4X` 등재 대기문 — Ted 판정 4건 (2026-09-02 · 워크트리 `lane-p4x`)

⛔ **번호를 발급하지 않았다.** 최신 결정은 〈281〉이고, `PLAN-SoT.md §9` 에 이 회차가 쓰지
않았다. **번호 발급과 등재는 오케스트레이터가 직렬로 한다**(`CLAUDE.md §1-b` ⑶).
아래 넷은 그 자리에 그대로 옮겨 붙일 문안이다.

---

## ㉮ 데이터셋 기간의 끝은 조건부 — **계약 동결 해제가 필요해 멈췄다**

**Ted 판정 (2026-09-02)** — 데이터셋의 기간은 있을 수도 없을 수도 있다(optional). 있으면
시작은 있고 **끝은 조건부**다 — 끝이 없으면 무기한·진행 중이다.

⛔ **집행하지 않았다. 계약 개정 없이는 성립하지 않기 때문이다.** 실측 —
`contracts/seams/fe-core.yaml` `DataPeriod`(2162~2171행) 축자:

```yaml
    DataPeriod:
      description: |
        데이터가 다루는 시간 범위. **레코드 시점 3종과 축이 다르다**(`DataModel §4.1`).
        조각이 여럿이면 합집합이다 (§4.3).
      type: object
      required: [start, end]          # ← end 가 필수다
      additionalProperties: false
      properties:
        start: { type: string, format: date-time }
        end: { type: string, format: date-time }   # ← nullable 도 아니다
```

- `end` 가 `required` 에 들어 있고 `type` 도 `[string, "null"]` 이 아니다 ⟹ **빈 끝을
  받으려면 스키마를 고쳐야 한다.** 그것은 **동결 해제**이고 다음 회차는 **14차**다.
- ⚠ 같은 파일의 `ProjectPeriod`(2173~2186행)는 **이미 `type: [string, "null"]`** 이다 —
  프로젝트 기간은 「진행 중이면 종료가 비어 있다」를 계약이 이미 안다. **데이터셋 기간만
  그 모양이 아니다.** 개정 시 그 형태를 그대로 따르면 새 무늬를 만들지 않는다.
- 고칠 자리 = `required: [start, end]` → `required: [start]`(또는 `end` 를
  `type: [string, "null"]` 로) ＋ 생성 파일 재생성. **이 회차는 손대지 않았다.**

**남는 대기 항목 (레포 밖 · 이 회차가 고치지 않았다)** — 화면 정본 UI 스펙 19 는
「기간」을 **자유 입력 한 칸**으로 적고, 계약은 **두 날짜 칸**이다(〈280〉이 화면에 두 칸을
넣었다). Ted 판정은 **두 칸 + 끝 선택** 쪽으로 정리한다. **스펙 문면 갱신이 남는다 —
문서가 레포 밖이라 이 회차가 편집하지 않았다.**

## ㉯ 카탈로그 `Verified` 열 — 승인 처리 도착 전은 **취소선·회색·비활성**

**Ted 판정 (2026-09-02)** — 승인 처리가 아직 오지 않은 행의 `Verified` 칸은 **글자를
그대로 두되 취소선·회색·꺼진 조작 모양**으로 그린다.

**왜** — 종전 실물은 그 칸을 **비워 두었다**(`CatatlogTable.tsx` `{row.verified && …}`).
비면 「승인이 아니다」와 「아직 안 왔다」가 화면에서 갈리지 않는다. `CT-1` 완료 정의가
그 자리를 `[미확인]` ㈎(문구 부재)·㈏(글자 무근거)로 남겨 두고 **제품 판정을 기다리고
있었다** — 이 판정으로 둘 다 닫힌다.

**집행** — `frontend/src/components/catalog/CatalogTable.tsx` 8번째 칸이 `verified` 가
거짓일 때 `verified verified--pending` 스팬에 글자 `Verified` 를 그린다(`aria-disabled`).
규칙은 `catalog.css` `.verified--pending`(`text-decoration: line-through` ·
`--color-gray-500` · `cursor: not-allowed`). 시험 3건(`frontend/test/catalog.test.tsx`).

## ㉰ 묶음 내려받기에 **기준 격자 파일**을 포함한다

**Ted 판정 (2026-09-02)** — `downloadDataset` 의 묶음(zip)에 데이터셋의 기준 격자 파일을
함께 넣는다. `ST-1` `[미확인]` ㈎(정본 침묵)가 이것으로 닫힌다.

**집행** — `domains/d3_catalog.py` 의 질의를 `kind = '본체'` 에서
`kind IN ('본체', '기준 격자 파일')` 로 넓히고 이름도 `files_for_download` 로 고쳤다.
정렬은 **본체 먼저, 격자 뒤**(`ORDER BY (kind <> '본체'), file_name, id`).
`kind` 두 값은 스키마의 `CHECK` 가 정본이다(`db/platform/schema.sql:435`).

⚠ **경계는 그대로다** — `d3_file` 의 `body_access` RESTRICTIVE 정책은 `kind` 를 보지
않으므로 격자 행도 같은 잠금·같은 연구실 경계를 탄다(`schema.sql:858`). 잠긴 행 403 ·
다른 연구실 404 시험이 그대로 green 이다.
⚠ **`Policy_데이터셋_상세 §5` 의 파일 칸 = 본체 수는 그대로다** — 세는 것과 담는 것이 다르다.

## ㉱ 용량 상한을 두지 않는다 ⟹ **스트리밍 zip**

**Ted 판정 (2026-09-02)** — 내려받기에 용량 상한을 두지 않는다. `ST-1` `[미확인]` ㈏가
이것으로 닫힌다.

**왜 스트리밍이 함께 가야 하나** — 종전 구현은 `io.BytesIO()` 에 zip 전체를 쌓았다
(`routes/catalog.py` `_bundle`). 상한 없이 그대로 두면 **메모리가 데이터셋 크기를 그대로
따라간다** — 「상한 없음」이 「메모리 무한」이 된다. **상한 대신 버퍼를 없앴다.**

**집행** — `kernel/file_store.py` 에 `_ZipSink` ＋ `stream_bundle()` 을 더했다.
`seekable() == False` 인 싱크를 `zipfile` 에 주면 data descriptor 로 쓰므로 되감기가
없고, 조각을 청크(`STREAM_CHUNK = 1 MiB`)로 읽어 넣을 때마다 싱크를 **비워** 내보낸다.
한 번에 든 바이트 = **청크 하나 ＋ 항목 헤더**이고, 중앙 디렉터리만 끝에 붙는다.
`force_zip64=True` 라 4 GiB 를 넘는 조각도 담긴다.

⛔ **라우트 계약은 한 글자도 안 바뀌었다** — 302 두 hop · `Location` · `Content-Disposition`
그대로다. `_bundle` 은 `StreamingResponse(file_store.stream_bundle(...))` 한 줄이 됐다.

**증명** (`services/core-api/tests/test_dataset_download.py`) —
⑴ `stream_bundle` 의 반환이 **생성기**다(`inspect.isgenerator`).
⑵ 64 MiB 조각을 64 KiB 청크로 흘리는 동안 **한 번에 내보낸 최대 조각 ≤ 청크 + 4096** —
   싱크가 비워진다는 뜻이고, 그것이 메모리가 크기를 따라가지 않는 이유다.
⑶ 흘려 낸 zip 이 실제로 **풀리고** 이름·바이트가 원본과 같다(`ZipFile.read`).
⑷ 라우트가 전량 버퍼를 **호출하지 않는다** — `ast` 로 호출만 세어 `BytesIO`·`.getvalue`·
   `.read` 0건. ⚠ **글자 grep 으로 재지 않았다** — 주석·산문의 이름을 결합으로 오판하는
   것이 이 레포가 이미 겪은 오탐이다(`CLAUDE.md §3`).
⚠ **RSS 로는 재지 않았다** — 이 시험 하네스는 프로세스 안이라 피크 RSS 가 다른 픽스처와
   섞인다. **어느 증명을 냈는지 위에 그대로 적는다.**
