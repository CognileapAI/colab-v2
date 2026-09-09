# Partial preview original file names continuation

## 요구와 구현

- 실제 정상 TIF+손상 TIF 묶음에서 일부 그림과 2개 중 1개 읽음은 맞지만 누락 파일 이름이 저장 키로 표시된 결함을 복원한다.
- viz-render의 local/S3 source는 저장 키를 file_name으로 사용한다. core GET RenderJob에는 target 없이 missingParts.fileId가 있으므로 해당 ID를 원장 d3_file/d5_upload_file에 조회한다.
- 새 domains/preview_metadata.py는 RLS가 적용된 세션에서 실제 원본명과 대상 ID만 조회한다. routes/preview.py는 기존 데이터셋 본체 접근/업로드 소유자 판정을 통과한 이름만 partialFailure.missingParts[].fileName에 복원한다. create와 get 응답이 동일 경계를 사용한다.
- 업스트림 원본을 변경하지 않고 응답 복사본의 이름만 바꾼다. 총수·읽힌수·누락 ID·렌더 결과·상태·실패는 보존한다. 이름이 없거나 접근이 거절되면 기존 응답을 유지한다. 새 API/계약/바이트 접근/타일 중계 없음.

## 검증

- 명시 Edit/Write 훅 JSON stdin guard 실행, s3-upload 원문 확인.
- 일회용 PostgreSQL과 실제 HTTP relay 시험 RED: 신규7건 중 4실패·3통과, 업로드/데이터셋 create/get이 저장 키를 그대로 반환하는 결함을 확인했다.
- focused 선택자 `-k "preview_file_names or preview_relay or preview_render_guard"`, marker `not e2e`: **28통과·966deselected·0skip·0failed·0errors**, 종료0. 로그 `/tmp/ui-partial-names-green.log`. 마지막 타업로드 소유자 음성을 포함한 신규 전체8건 별도 `-k preview_file_names`: **8통과·987deselected·0skip·0failed·0errors**, 종료0(`/tmp/ui-partial-names-final.log`). 두 실행 모두 일회용 PG를 별도로 생성/정리했다. 전체 서비스 게이트로 확대하지 않는다.
- 실제 TIF 묶음 브라우저 재검증은 부모 통합 사본에서 수행한다.
