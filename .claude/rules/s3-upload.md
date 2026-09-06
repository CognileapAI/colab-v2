---
paths:
  - "services/core-api/**"
---

# 업로드(S3) — 고칠 때 알아야 할 것

⭑ 출처 = `CLAUDE.md` 의 같은 이름 절. 2026-09-06 P-S 에서 **본문 그대로** 이 파일로 옮기고
`CLAUDE.md` 에는 3줄 포인터만 남겼다(≤200행 상한). 규약은 무변경 — 문면이 정본이다.

업로드 바이트 저장이 **로컬/S3 로 갈린다** (`PLAN-SoT §9 〈337〉·〈338〉` · 운영 정본 `dev-package/S3.md`).
로컬 개발은 local 모드(form-data→디스크)가 기본이라 AWS 없이 그대로 돈다.

- 분기점은 저장 Port(`ports/storage.py`)와 전송 라우트(`routes/upload_transfers.py`) 둘뿐이다.
  s3 모드는 `COLAB_CORE_STORAGE_MODE=s3` + 버킷·리전 — 반쪽 설정은 기동이 거부된다
- **SigV4 는 표준 라이브러리 자작이다** (`kernel/sigv4.py`) — boto3 없음. S3 API 호출에 본문이
  있으면 `content-type: application/xml` 을 명시해야 한다 (urllib 기본값이 서명을 깨뜨린다).
  그래서 **에뮬레이터(MinIO 등) 검증 금지** — 관대한 통과가 진짜 S3 의 403 을 숨긴다
- **파트의 정본은 S3 ListParts 다** — 재개·완료 검증 어디서도 클라이언트 자기 보고를 믿지 않는다
- **완결이 곧 접수다** — `completeUploadTransfer` 전에는 `d5_upload` 도 `upload.accepted` 도 없다
- 만료 전송 정리는 **원장이 아는 것만** 지운다. 버킷 루트 스캔 금지 — 시드 lab_id 가 겹치는
  버킷에서 남의 데이터를 지운다. 최후 백스톱은 라이프사이클 abort-7d
- 폴더 업로드의 경로는 저장 키가 아니라 원장 메타(`relative_path`, d5→d3 승계)다 — 키 규약(생성물)은 불변
- **다운로드는 302 가 아니라 200 티켓이다** — 브라우저 `<a href>` 는 Bearer 를 못 싣는다. 바이트 op
  (`/downloads/{ticket}`)는 `security: []` 지만 티켓 클레임으로 `apply_scope` 를 심어 RLS 가 다시 판정한다.
  `session_secret` 이 없으면 500 `DOWNLOAD_UNAVAILABLE`(`createSession` 과 같은 자리) — 조용한 폴백을 두지 않는다
- AWS 검증은 콘솔 눈이 아니라 `services/core-api` 에서 `.venv/bin/python ops/s3_doctor.py` / `ops/s3_smoke.py`
- 시크릿 키는 채팅·커밋에 절대 넣지 않는다
