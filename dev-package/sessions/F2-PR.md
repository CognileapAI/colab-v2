# F-3(구 `F-2`) / U-1 PR 본문 초안 — `feature/rtf400_s3_upload` → `main` (2026-08-29)

> 사용자(phj)에게 push 권한이 없어 PR 은 보류 상태다. 이 파일은 PR 을 열 때 붙여넣을 본문이다.
> **제목**: 업로드 S3 직행·중단 재개 + 파일 관리 (동결 해제 8차·9차 — Ted 판정 필요)
> **병합 조건**: Ted 판정(㉯) 전 병합 금지 — 항목은 아래 11항 + `PLAN-SoT §9 〈280〉-⑦`.

---

## 요약

업로드 바이트 저장을 **로컬/S3 로 분기**하고(저장 Port), s3 모드에 **프리사인드 직행 전송 + 중단 재개**를 세웠으며, 회의 결정(2026-08-23)으로 1차 목표에 든 **파일 관리 4종**을 닫았다.

- 저장 Port `ports/storage.py` — local(디스크, 기존 동작 무변경) / s3(`COLAB_CORE_STORAGE_MODE=s3`, 반쪽 설정은 기동 거부)
- 프리사인드 전송 9 op(`/uploads/transfers`) + 전송 원장 `0008` — **완결이 곧 접수**, 파트의 정본은 S3 ListParts
- 폴더째 드래그 앤 드롭 — `relative_path` 가 접수(d5)→등록(d3, `0009`)까지 승계
- 데이터셋 상세 파일 목록(「보기」→ 폴더 트리·크기·시각) · 다운로드(**200 티켓 + 바이트 op**, 파일 단위/묶음 zip, s3 파일 단위는 프리사인드 GET) · 본체 파일 추가·교체·삭제(마지막 본체 409)
- 마이그레이션 `0008`(additive) · `0009`(additive + `total_size_bytes` 트리거·**백필 1회**)
- 정본 등재 `PLAN-SoT §9 〈276〉〈277〉〈278〉〈279〉〈280〉` · 운영 정본 `dev-package/S3.md` · 지시서 `sessions/F2.md`

## ⚠ 병합 조건 — Ted 판정(계약 동결 해제 프로토콜 ㉯) 11항

`PLAN-SoT §9 〈280〉-⑦` 그대로. 판정 전 병합하지 않는다.

1. `〈277〉` 8차 — 프리사인드 전송 9 op + 중단 재개(정본 Policy §7.1·§9 「이어올리기 범위 밖」의 개정 제안)
2. `〈280〉` 9차 묶음 — 파일 관리 op 신설 2 + `downloadDataset` 302→200 + 스키마 필드 추가 + `0009` 백필
3. `〈59〉`-③ 번복 — 본체 파일 추가·교체·삭제 허용
4. 본체 변경 시 `마지막 수정` 이동(권고: 이동 — 계보 상태가 `확인 필요` 로 접힌다)
5. 다운로드 형태 — 200 티켓 + 바이트 op(`security: []`, HMAC·10분), s3 묶음은 core-api 경유 zip
6. `㊻` 개정 — AWS 계정 보류를 dev 벌에 한해 해제(prod ⏸ 유지)
7. `〈78〉` J-10 폴더 드롭 편의 → 기능 승격(사후 등재 — `613df7d` 가 인용 없이 먼저 집행했다)
8. `deleteDataset` 범위 밖 유지
9. worker·viz S3 읽기 방식(V-3 — 완료 정의 미작성)
10. 격자 op 이름(`replaceDatasetGridFile`·`deleteDatasetGridFile`) 유지(권고) vs 개명(ERR 2)
11. `[정본 무근거]` 2건 — `d8_download.file_id` · 활동 문자열 「본체 파일 변경」

정본 원본(`40 COLAB-기획/`)은 작업 호스트에 없어 `〈278〉〈279〉` 는 회의 결정의 **2차 기재**다 — 원본 개정(`DataModel §4.3` 나열 금지 · `Policy_데이터셋_상세 §2·§8` 부분 다운로드 없음 · `§7.1`·`§9`)은 기획 소유.

## 실측

- pytest 516 → **567** · vitest 284 → **316** · tsc 0 · op 53 → **64** · 501 표 20 → **19**
- 게이트 전 종 green — contract-lint · **contract-breaking HEAD 기준 ERR 0(INFO 23) · origin/main 기준 ERR 0(INFO 31)** · generated-up-to-date · seam-consistency(㉠ 신설 인용 전건) · import-boundary · banned-import · rls-coverage · event-lint/breaking · migration-single-head · `0008`/`0009` 드리프트(적용 green · 되돌리면 red 실물 · downgrade 복원) · schema-diff 두 체인. `planning-freshness` 는 작업 호스트에 정본 폴더가 없어 환경 red(브랜치 무관)
- 실호출 증거(원문 레포 보존) — `dev-package/sessions/U1-evidence-8차-transfer.txt`(실버킷 멀티파트 20 MiB · ListParts 재개 근거 · 완결=접수 · `upload.accepted` 1건) · `dev-package/sessions/F2-evidence-9차-download.txt`(local 파일/묶음 다운로드 sha256 일치 · zip 엔트리 = 폴더 경로 · Bearer 없는 발급 401 · 변조 404 · 진짜 S3 프리사인드 GET 200·`content-disposition` 일치·만료 403·잔여 객체 0)
- 로컬 모드 = 기존 시험 전건 무변경 green 이 「로컬 동작 안 깨짐」의 오라클

## 병합 후 할 일

1. staging — **백업 회차 확인 후** `alembic upgrade head`(`0009` 백필이 `0004` 이후 처음으로 `NO FORCE RLS` 창을 연다 · 같은 트랜잭션 안에서 복구·자가검증) 또는 `setup-db.sh` 재실행
2. `cd frontend && npm ci` (mac 에서는 `@rolldown/binding-darwin-x64` 재설치 필요 — npm#4828)
3. 재검증 — pytest 567 · vitest 316 · 5 배포 단위 헬스. staging 은 local 모드 그대로(무영향)
4. nginx — `/api/v1/downloads/` 에 `proxy_buffering off` 권고(대용량 스트림이 임시 파일로 떨어진다)

## 열린 갭 (별 WU)

- **V-3** worker·viz 의 S3 읽기 — s3 모드에선 전송·접수·다운로드까지만 성립, 검사·미리보기는 로컬 경로 전제(완료 정의 미작성)
- **I-D** dev 환경(AWS·s3 모드) — `〈279〉` · 진입 = ㊻ dev 한정 해제 판정 + V-3
- CI 의 `contract-breaking` 이 `COLAB_BREAKING_BASE_REF` 없이 돌아 **구조적 green-by-skip**(`03-HANDOFF §4 #39`) — 게이트·CI 면, 별건
- 삭제 확인 단계 없음(서버 409 만 방어) · 「파일 추가」 낱개는 `relative_path` 미탑재 · 묶음 zip 대용량(>166 MB) 미실측

`frontend/vite.config.ts` 의 dev 프록시는 로컬 편의라 커밋하지 않았다.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01E843FPmKzSLnStzS9YCx97
