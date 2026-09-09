# 좌표 없는 BIN 등록 보존 — 2026-09-09

부모의 실제 브라우저 BIN 업로드에서 분석 완료로 진행하지 못한 실패를 인계받아 처리했다. 기점 `8855102`의 별도 사본, 변경 소유는 pipeline-worker 소스2파일·신규 시험1파일이다. 운영 스택/DB/서버 접촉 없음.

## 원인과 수정

- `d5/pipeline.py::run_file`은 BIN 헤더/기간/블록/격자를 읽은 뒤 기준 격자가 없으면 `FAILURE`로 끝난다.
- `domains/d5_ingestion.py::process_upload`는 성공 결과만 헤더에 사용하고 전부 좌표 부재일 때 `upload.failed`로 끝냈다. 따라서 원래 읽은 메타정보도 버렸다.
- 근거 `sessions/S1-PLAN-REFOUND.md` D.6-4: 좌표/격자 없음은 렌더 보류이고 등록 실패가 아니다.
- 변환 결과에 내부 사실 `coordinates_unavailable`만 추가했다. **run_file은 계속 FAILURE를 반환**하며 기존 변환 실패 음성시험 의미를 바꾸지 않았다. 계약/생성 타입/서버 스키마 변경 없음.
- 업로드 경계에서 파싱된 메타가 있고 좌표 부재인 결과를 등록 가능 묶음에 포함한다. 헤더는 유지하고 `metadataComplete=false`, `ready=true`로 진행한다. 좌표 부재 결과를 unreadableFiles로 표시하지 않는다.
- 좌표 정규화·COG 이벤트 대상은 변환 성공 파일로만 한정한다. 좌표 부재만 있는 묶음은 해당 이벤트를 내지 않고, 정상·좌표 부재 혼합은 정상 파일ID만 싣는다. COG 산출물/좌표를 만들었다고 위장하지 않는다.
- `renderable=true`는 Binary라는 **지원 형식의 능력**이고 그려진 그림 존재 여부가 아니다. 실제 지도 요청의 보류·격자 안내는 기존 D7 경로가 담당한다.

## 검증

- 신규 `tests/test_upload_without_coordinates.py` 3건: 좌표 없는 유효 BIN 등록/메타 유지, 무효 BIN 감지 실패 유지, 정상·좌표 부재 혼합에서 파일별 좌표·COG 정직성.
- RED 2실패/1통과 → GREEN 3통과. 변환·기존 이벤트·지도타일 회귀37건도 통과. 이때 실데이터3건은 원천 환경변수 미선언으로 실패했으며 통과로 세지 않았다.
- 원천 경로를 명시해 `test_map_tile_reuse.py` 전8건 재실행: **8통과/0실패**, 실파일 BIN/NetCDF/HDF 타일 생성 및 다음 실행 재사용 포함. NumPy 바이너리 호환 RuntimeWarning1건 출력됨.
- `service-tests-pipeline-worker`: **263통과/0실패/0skip**, 선택제외46건(e2e/dbint), 21경고. 게이트 **green1 / 판정실패0 / 준비실패0**, 종료0. 기존 게이트 선택자 `not e2e and not dbint` 그대로이며 환경 면제 없음.
- 실제 원천 `RDR_CMP_HSR_PUB_202508131000.bin.gz`, 1,259,571 bytes, SHA256 `317500ebd261adbc3bbe4fe7a95bc69931d3f03ac96b84b97bc0b6fa05270456`를 기준격자 없이 업로드 경계에 입력했다.
  - 발행: `file.format-detected` → `file.header-parsed` → `upload.ready`.
  - `ready=true`, failed_at 없음, 변수 블록1·기간2025-08-13T10:00:00·격자2881x2305·원본바이트1,259,571 보존.
  - CRS null, metadataComplete false, unreadableFiles0, COG0, artifact0. 원천 무수정.
- 수정 전 사본 Edit/Write 훅3종 JSON stdin guard 실행. Python 환경은 기존 원천 사본의 pipeline-worker venv를 이 사본에서 읽기 전용으로 재사용했고 설치/패키지변경 없음. pytest는 이 사본 src/tests를 사용한다.

## 미달·초과와 인계

- 미달: 이 시험은 실제 파일을 사용하되 원장은 MemoryLedger이다. 실제 DB 저장→재접속 및 브라우저 격자 안내/등록 완료는 부모 통합 E2E가 검증한다. DB 동작 완료로 확대하지 않는다.
- 초과0: 지도 변환 성공정책이나 좌표 생성법을 바꾸지 않았고, 승인 요구의 등록 허용/메타 보존을 업로드 경계에 연결했다.
- 부모 사본에 `_process_stage2`로 분리된 코드가 있다면 이 사본의 process_upload stage1 다음 구간과 대응시켜 옮겨야 한다. 전체 파일 덮어쓰기 전 차이를 확인한다.

## 독립 리뷰 후 보완

- 역순 혼합(deferred→converted)에서는 헤더 대표 메타의 CRS가 null일 수 있다. 정규화 이벤트는 **실제 변환된 파일의 메타**에서 sourceCrs를 고르게 분리했다. 역순 RED1→GREEN, 이벤트 계약검증 포함.
- 이미 ready인 좌표 부재 파일을 다시 처리해도 값그림은 갱신 대상이므로 backend-rerun 트리거는 기존 `was_ready` 조건을 유지한다. COG/좌표 성공 대상만 converted로 제한한다. 이 경합 RED1→GREEN.
- 이전 failed 업로드가 복구되면 ready와 failure가 공존하지 않게 failed_at/failure_class/failure_reason을 명시적으로 null로 정리한다. 원장의 상태변경 경계에서 처리하며 기존 실패이벤트 이력은 삭제하지 않는다. RED1→GREEN.
- 좌표부재 등록 후 실제 격자를 후주입하면 실제 COG1건이 생기고 sourceCrs/metadataComplete가 갱신되는 시험 추가. 임의 성공값 없이 파일 존재와 계약을 확인했다.
- 신규 등록경계7건+기존 stale트리거15건 **22통과**. 최종 서비스 게이트 **267통과·46deselected·0skip·0fail**, green1·판정실패0·준비실패0, 종료코드0. 로그 `/tmp/ui-bin-worker-final.log`, 계수 `/tmp/ui-bin-worker-final/gate-summary.json`. 실제 자료가 필요한 별도 map-tile-reuse8건도 통과(앞 절).
