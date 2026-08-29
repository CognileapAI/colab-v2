# PV-STORAGE — 미리보기 산출물의 자리를 저장 규약에 세운다 (**여덟 번째 동결 해제**)

> **⟨개정 2026-08-29 · `PLAN-SoT §9 〈200〉`⟩ 제목의 서수는 「여덟 번째」가 아니라 「아홉 번째」다.** 원문은 지우지 않는다.
> **8차는 `〈180〉`(2026-08-28 · 미구현 `422` 두 자리 철회)에 갔다** — 그 회차가 번호를 발급하지 않은 것을 `〈199〉` 가 **사후 기재**로 메웠다.
> 이 문서는 발급처가 아니다 — **회차 번호의 유일한 발급처는 `PLAN-SoT §9`** 다(`X2-FREEZE-PROTOCOL §5-㉲`).

> 값과 근거의 정본은 `PLAN-SoT §9` 다. **이 문서는 §9 항목이 아직 서지 않은 동안의 회차 기록이다** —
> `dev-package/work-items.yaml`·`03-HANDOFF.md`·`PLAN-SoT.md`·`WORK-UNITS*` 는 이번 회차에 다른 에이전트가
> 쓰고 있어 **미접촉**이었다. ⚠ **`§9` 등재 1건이 남아 있다**(아래 §2 형식 그대로) — 회차 번호 발급처는 §9 다.

## 1. 등급 판정 — **㉯ (Ted 승인 필수)** · 승인 = Ted 2026-08-29

`X2-FREEZE-PROTOCOL §5` 로 실물 재확인.

| ㉮ 조건 | 실측 | 충족 |
|---|---|---|
| `contract-breaking` ERR 0 | green (기준 HEAD 3건 대비 파괴적 변경 없음) | ✅ |
| 마이그레이션 0 · 스키마 변경 0 | `db/` diff 0. **미리보기 산출물은 `FileKind` 가 아니다** — 원장 행이 없어 `d3_file.kind` CHECK(`db/platform/schema.sql:361`·`:552`) 를 넓히지 않는다 | ✅ |
| 소비자 0건 | ❌ **아니다** — 신설 함수를 `viz-render` 가 즉시 쓴다(㉰-4 「집행 없는 신설 금지」의 요구) | ❌ |
| 설계 판단 0건 | ❌ **아니다** — **새 저장 단위**를 세웠고 **기각한 대안이 둘**(본체 하위 경로 · 규약 밖) | ❌ |
| 정본 무개정 | `planning/` 무접촉 | ✅ |

→ **㉯.** 설계 판단이 섞였고 기각안이 있다 — 「기각한 대안이 하나라도 있으면 여기다」에 직접 해당.

⚠ **지시받은 등급 근거 셋 중 ⑴ 을 정정한다.** 「파일 종류 CHECK 확장 마이그레이션 ≥1」은 **이 설계에서는 거짓**이다.
미리보기 산출물은 사용자가 올린 파일이 아니라 **다시 만들 수 있는 산출물**이라 `FileKind`·`d3_file` 를 넓히지 않았다
(`db/` diff 0). ⑵(기각안 존재)·⑶(되돌리기 어려움)은 그대로 참이고, **등급 결론 ㉯ 는 바뀌지 않는다.**

## 2. 회차 번호 — ~~**8차**~~ → **9차** (⟨개정 2026-08-29 · `PLAN-SoT §9 〈200〉`⟩)

- `PLAN-SoT §9 〈163〉-㉯` = 「`〈94〉` 5차 · `〈107〉` 6차 · `〈151〉` 7차 · **다음 해제는 8차다**」
- `§9` 전문에서 **8차를 발급한 항목 0건** 확인 → 8차는 비어 있다.
- **소급 확인 1건 (사실만 적는다 · 판정은 이 회차의 것이 아니다)** — `〈180〉`(2026-08-28 · `createRender`·`searchDatasets`
  의 `422` 두 줄 삭제)은 항목 본문에 **동결 해제 회차 번호를 발급하지 않았다.** 「해제」 표기가 없다.
  → **발급 누락으로 보인다.** 소급 기재는 하지 않았다.
  → **⟨개정 2026-08-29 · `〈199〉`⟩ 그 관측이 맞았다.** `〈180〉` 은 절차 대상(등급 ㉯ · Ted 승인 2026-08-28 실재)이었고 번호만 빠져 있었다.
  **`〈199〉` 가 `〈180〉` 에 8차를 사후 기재로 발급했다.** 그 결과 **본 회차는 9차**이고, 아래 8필드의 ① 은 `9차` 로 읽는다.

**§9 에 넣을 8필드 (형식 `㉲`)**

| 필드 | 값 |
|---|---|
| ① 회차 | ~~**8차**~~ → **9차** (⟨개정 · `〈200〉`⟩ · §9 등재 = `〈200〉`) |
| ② 값 | `contracts/storage/layout.json` — `keys` 에 **`미리보기 산출물`** 1종 · `roots` 신설 · `previewsRoot` 신설. 생성물 3종 재생성. 생성 모듈에 `PREVIEW_KIND`·`ROOTS`·`UPLOAD_ROOT`·`PREVIEW_ROOT`·`preview_key()`·`preview_path()` |
| ③ 근거 | **자리가 있어야 이미 구운 것을 찾아 쓴다.** 자리가 없으면 같은 그림을 매번 다시 굽는다 (Ted 2026-08-29) |
| ④ 가·파 | **가산.** `contract-breaking` green · `contract-lint` green · `generated-up-to-date` green · `seam-consistency` green |
| ⑤ 소비자 | **1건** — `viz-render/domains/d7_visualization/preview.py:_write`. 신설과 동시에 집행(㉰-4) |
| ⑥ 마이그레이션 | **0** (`db/` diff 0) |
| ⑦ 승인 | **Ted · 2026-08-29** |
| ⑧ 이번에 안 센 축 | 아래 §6 |

**되돌리는 비용** — `layout.json` 3키 되돌림 ＋ 생성 3파일 재생성 ＋ `preview.py` 한 줄 원복. 마이그레이션·데이터 이동 0.
**디스크의 파일은 이름이 바뀌지 않는다**(키 형식이 종전 `{키}{확장자}` 와 **같다**) — 되돌려도 기존 39건이 그대로 읽힌다.

## 3. 저장소 귀속 — `[미확인]` 해소

**미리보기 산출물은 `previews` 볼륨에 든다. 추론이 아니라 실물이다.**

- 「파일에서 읽고·좌표계를 통일하고·**지도용 영상으로 바꾸는 것**」 = 「미리보기」 (`336356b` 커밋 본문).
  그 코드가 `viz-render/domains/d7_visualization/preview.py` 의 **미리보기 3층**이다.
- 그 3층을 쓰는 자리 = `_write(out_dir=spec.preview_dir …)` → `preview_dir` 기본값 `/srv/viz-previews`
  (`kernel/config.py:42`·`:81`, `COLAB_VIZ_PREVIEW_DIR`).
- `/srv/viz-previews` 마운트 = named volume **`previews`** (`infra/staging/compose.i2.yml:288` rw · `:36` nginx `:ro`).
- 백업 대장도 같은 것을 가리킨다 — 「`previews` | **미리보기 3층 산출물** | 원장에 대응 행이 **없다**」
  (`infra/staging/backup/README.md:118`), 실측 39건(`config.example.env:65`).

→ **「이번 변환 결과물」과 「viz-render 렌더 산출물 39건」은 같은 것**이다. 볼륨 배치는 **바꾸지 않았다** —
규약이 실물을 따라간 것이지 그 반대가 아니다.

## 4. 키 설계 — 세 조건

```
미리보기 산출물 : {미리보기 루트}/{contentKey}{extension}
본체            : {저장소 루트}/uploads/{targetId}/{fileId}
기준 격자 파일  : {저장소 루트}/uploads/{targetId}/{gridDirname}/{fileName}
```

- **ⓐ 재사용** — `contentKey` 는 원본 다이제스트·격자 다이제스트·팔레트·선택 변수·다운샘플·긴 변·좌표계·
  색범위(값 **과** 단계 토큰)를 접은 sha256(`d7_visualization/cache.py#render_cache_key`).
  **같은 입력 → 같은 키 → 이미 구운 것을 찾아 쓴다.** 입력이 하나라도 바뀌면 키가 갈려 무효화가 저절로 된다.
  키를 만드는 자리는 하나다 — `preview_key()` 는 다이제스트를 **만들지 않고 자리만 정한다.**
- **ⓑ 원본과 구분** — **루트가 다르다**(`ROOTS`). `storage_key(kind='미리보기 산출물')` 은 **ValueError 로 거절**한다.
  섞이면 백업·복원·삭제가 「사용자 것」과 「다시 만들 수 있는 것」을 못 가른다.
- **ⓒ 실물 정합** — 볼륨 둘(`uploads`·`previews`)·백업 둘과 어긋나지 않는다. **평평한 배치도 실물 그대로**다
  (대상 ID 를 경로에 넣지 않는다 — 넣으면 같은 그림의 재사용이 대상별로 깨지고, 기존 39건의 이름도 바뀐다).

## 5. 증거 — 출력째

**세 배포 단위 산출물 md5 (재생성 후)**
```
f86527452c6cf2edb6319905abf0cc39  services/core-api/src/colab_core/kernel/storage_layout.py
f86527452c6cf2edb6319905abf0cc39  services/pipeline-worker/src/colab_pipeline/kernel/storage_layout.py
f86527452c6cf2edb6319905abf0cc39  services/viz-render/src/colab_viz/kernel/storage_layout.py
```
**byte-identical.** 셋이 갈리면 그것이 「단위마다 다른 규칙」이고 `03-HANDOFF §4 #20` 의 재발이다.

**실패 시험 먼저 (red → green)** — 구현 전 세 단위 전부 red:
```
FAILED tests/test_storage_layout.py::test_preview_key_is_content_addressed_and_stable
FAILED tests/test_storage_layout.py::test_preview_root_is_not_the_uploads_root
FAILED tests/test_storage_layout.py::test_storage_key_refuses_preview_kind
  - AttributeError: module 'colab_core.kernel.storage_layout'   has no attribute 'PREVIEW_KIND'
  - AttributeError: module 'colab_pipeline.kernel.storage_layout' has no attribute 'PREVIEW_KIND'
  - AttributeError: module 'colab_viz.kernel.storage_layout'    has no attribute 'PREVIEW_KIND'
```
구현 후: core-api **458 passed** · pipeline-worker `test_storage_layout.py` **6 passed** · viz-render **119 passed**
(`COLAB_REFERENCE_DATA` 를 주어 실 원천 E2E 8건 포함 — 미리보기 3층이 실제로 새 키로 구워진다 = **집행 증명**).

**게이트 (2026-08-29 · 워크트리 `pv-storage`)**
```
generated-up-to-date green — 등기부 4건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.
contract-lint        green — seam 3건, 룰 위반 0.
contract-breaking    green — 기준 HEAD (3건) 대비 파괴적 변경 없음.
seam-consistency     green — G-e 336건 · G-b 7건 · ㉠ 0건 · ㉡ 18건.
import-boundary      green — 계약 전부 통과 (8 kept, 0 broken).
banned-import        green — .py 116건, 금지 import 0.
db-boundary          green — 단위 7개 · 스캔 대상 220건 · 위반 0
```
**RED 로 계수할 「도구 부재」 0건** — `frontend/node_modules`(npm ci 147 packages) · `services/viz-render/.venv`(신규 생성) ·
검증용 일회용 postgres(`--rm` ＋ tmpfs ＋ `PGDATA`, 호스트 포트 미공개, 종료 후 제거)를 **만들어서 돌렸다.**

## 6. 이번에 세지 않은 축 (다음 회차의 진입조건)

- **기존 39건의 재사용률** — 새 키가 옛 파일과 같은 이름을 내므로 되읽기가 성립할 **형태**지만, 실제로 캐시 적중이
  일어나는지는 재지 않았다. `_write` 는 지금도 **존재 여부를 묻지 않고 덮어쓴다** — 「자리가 있다」와 「찾아 쓴다」는 다르다.
  **재사용을 실제로 하려면 적중 시 굽기를 건너뛰는 분기가 필요하고, 그것은 이 회차 범위 밖이다.**
- **원장과의 연결** — 미리보기 산출물에는 원장 행이 없다(`backup/README.md:118`). 어느 데이터셋의 것인지 되짚는 수단이
  여전히 없고, 그래서 「원본이 지워질 때 산출물도 지운다」를 기계가 못 한다.
- **사건 발행·소비** — `contracts/events/**` 무접촉(지시). 다음 회차가 이 자리를 가리킨다.
- `PLAN-SoT §9` 8차 항목 등재 · `03-HANDOFF` 갱신 — **이 회차에서 못 했다**(문서 소유가 다른 에이전트).
