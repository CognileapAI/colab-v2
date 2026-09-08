# HSR `.bin.gz` 업로드 — 「다음」 영구 비활성 원인 (2026-09-08 · 읽기 전용 조사)

조사 트리 = 워크트리 `.claude/worktrees/hf` · 브랜치 `integration/hotfix-upload` · HEAD `8158e87`.
staging 가동 이미지 = `colab-v2/*:8158e87c5bb9` (전 단위 `Up 12 minutes (healthy)`).

## 1. 클라이언트

- `status` 출처 = `GET /api/v1/uploads/{uploadId}`(`getUploadStatus`) — `frontend/src/components/upload/UploadModal.tsx:399-404`.
- 폴링 = `STATUS_POLL_MS = 1000`(`UploadModal.tsx:88`) · 조건 `if (!s.ready && !s.failure)` 로 재예약(`:404`). **타임아웃·최대 시도 없음.**
- 게이트 = `const analyzing = !props.status?.ready`(`RegisterArea.tsx:1010`) → `disabled={analyzing || classifyBlocked}`(`:1147`) · 하단 문구 `NEXT_BLOCKED_HINT = '분석이 끝나면 다음으로 넘어갈 수 있어요'`(`:76`, 사용 `:1127`).
- **`analyzing` 판정식에 `failure` 가 없다.** 실패해도 문구·버튼은 「분석 중」 그대로.
- 실패 시 분석 3단계 칩 블록은 `!status?.failure` 조건으로 **사라진다**(`UploadModal.tsx:1009`) — 화면에서 진행 표시만 없어지고 사유는 어디에도 안 뜬다.
- `status.failure` 를 그리는 자리 = **레포 전체 0건**(FE 전수 grep: `UploadModal.tsx:428`·`:1009` 두 곳뿐, 둘 다 게이팅).

## 2. 서버

- 엔드포인트 = `services/core-api/src/colab_core/app/routes/ingestion.py:272-300` — `"ready": record.ready`(`:292`) · `"failure": None if record.failure_reason is None else {"reason": record.failure_reason}`(`:299`).
- `ready` 를 세우는 곳 = pipeline-worker `domains/d5_ingestion.py` `record_status(..., ready=True)` (`:263`·`:316`·`:384`).
- `.bin.gz` 분류는 **정상**이다 — `d5/detect.py:136-142` gzip 해제 후 `_plausible_hsr_header`(`:63-77`) → `_sniff_bytes` 가 `"Binary"` 반환(`:118`). 「확장자로 싸잡아 분류」는 이 사건의 원인이 **아니다**.
- 실패 자리 = `d5/pipeline.py:213-221` — HSR 은 `crs_embedded=False` 라 기준 격자 필요, `grid_dir=None` → `GridUnavailableError` → `_fail("좌표/격자 없음 …")`. `DATA-REFERENCE.md:73,79` 축자 「HSR = 유일하게 기준 격자 파일이 진짜 필요한 포맷 · 못 찾으면 FAILURE 가 옳은 동작」.
- 분류 = `_FAILURE_MAP`(`domains/d5_ingestion.py:75`) → `좌표계 변환 실패` · `재시도 가능`. `_fail`(`:192-200`)이 `failed_at` 을 찍어 **`ready` 는 영원히 false**.
- **이 분기는 stage 2 에서만 돈다.** 같은 파일 `:72-75` 주석 축자 — 「stage 1 에서는 이 분기가 안 돌고 … 업로드는 실패하지 않는다」. staging 은 `infra/staging/compose.i2.yml:263` `COLAB_WORKER_STAGE2: "on"`.
- 타임아웃·실패 상태 = 서버에는 있다(`failure`), **화면에 없다.**

## 3. staging 실측 (읽기 전용 SELECT · 접속 문자열 미출력)

- `d5_upload` × `d5_upload_file` — `upload_id 01M20ATXRB7S0H592YXPGCW4MF` · 본체 12건(`RDR_CMP_HSR_PUB_2025081310{00..55}.bin.gz`, 각 약 1.26~1.30 MB) · `detected_format = Binary` · `ready = f` · `created_at 2026-09-08 11:00:46.98+00`(KST 20:00) · `failed_at 2026-09-08 11:00:51.98+00` · `failure_reason = 좌표계 변환 실패` · `registered_at = NULL`. 격자 파일 행 0건.
- 같은 파일명의 앞선 시도 1건 더 = `01M1Z5RVZXSRMC0TKQ8W8ZZQKS` · `2026-09-08 00:13` · 동일 사유.
- `d5_pipeline_event` 3행 — `upload.accepted 11:00:46` → `file.format-detected 11:00:51`(`"format": "Binary"`) → `upload.failed 11:00:51.983` · payload `{"class": "재시도 가능", "detail": "좌표/격자 없음 — 지어내지 않는다 (DR-9): 기준 격자 디렉터리가 지정되지 않았다; …"}`.
- 컨테이너 로그 = 12분 전 recreate 로 11:00 구간 유실. `docker logs --since 5h colab_v2_staging_pipeline_worker` 의 `upload.accepted` 는 1건(다른 `.nc` 업로드)뿐이고 `RDR` 문자열 0건 · `error|traceback` 0건. core-api 로그도 해당 시각 구간 [미상] — **원장 3행이 근거다.**

## 4. 판정

- **근본 원인 = 제품 결함 2건의 합.** ㈎ 화면이 실패 상태를 그리지 않는다(`RegisterArea.tsx:1010` 이 `failure` 를 안 본다 · 계약 주석 축자 「화면 문구는 정본 §9 가 소유하고 **화면이 그린다**」 `frontend/src/generated/fe-core.ts:2361-2368`). ㈏ staging 이 stage 2 로 돌아, 코드 주석이 「업로드는 실패하지 않는다」고 적은 격자 부재를 **업로드 전체 실패**로 만든다(`compose.i2.yml:263`).
- 파이프라인 분류(㈎ 의 전제로 의심된 「`.bin.gz` 미상」)는 **정상 동작**이다 — `Binary` 로 옳게 판정됐다.
- 사람이 봐야 할 것 = 「이 자료(HSR 레이더)는 기준 격자 파일이 함께 있어야 해요」 ＋ 격자 고르기 버튼 ＋ 다시 시도. 지금은 「분석이 끝나면 다음으로 넘어갈 수 있어요」가 무한히 서 있다.
- 최소 수정 = ⑴ `RegisterArea.tsx:1010` 을 `analyzing = !props.status?.ready && !props.status?.failure` 로 가르고, `failure` 일 때 `NEXT_BLOCKED_HINT` 대신 사유 문구 ＋ 재시도/격자 첨부 동선을 그린다(`FailureReason` 6값에 문구 표 1개). ⑵ 별건으로 staging 의 `COLAB_WORKER_STAGE2` 값을 판정한다 — 격자 없는 HSR 을 실패로 볼 것인가(stage 2) 등록은 되고 미리보기만 보류할 것인가(stage 1 · `_FAILURE_MAP:72-75` 산문). **⑵ 는 Ted 판정 사항이고 코드가 정할 것이 아니다.**
- 원장 자리 = 기존 항목 없음(`work-items.yaml` 전수 grep — `upload.failed` 1건은 `:1510` 격자 전용 업로드 건이고 다른 사안, `HSR|bin.gz|status.failure|무한 폴링` 0건). **신규 항목이 맞다** — 업로드 마법사 계열 `X-9`(done)·`X-10`(open, stage2·디자인 묶음)과 별개의 `X-11` 급 1건.
- dev = `infra/dev/compose.yml:69-85` 에 `COLAB_WORKER_STAGE2` **미선언** → `worker.py:204` 「미선언 — stage 1 만 돈다」 → 감지 다음이 곧 `ready=True`(`d5_ingestion.py:311-317`)라 **같은 파일이 dev 에서는 「다음」이 열린다**(격자 없이 등록까지 진행, 미리보기만 보류). ⚠ 화면 결함 ㈎ 는 dev 에도 그대로 있다 — 다른 사유(형식 인식 실패 등)로 실패하면 dev 도 무한 「분석 중」이다. dev 실배포에서의 실행 확인은 [미상](이 조사에서 dev 스택 미접촉).
