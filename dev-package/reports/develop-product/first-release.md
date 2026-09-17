# 최초 운영 배포 — v1.0.0 (2026-09-17)

- 대상: product 84e9ece8634ba4ac8a3def3582e3cdd99f130c5f (PR #106 병합, 태그 prod-20260917 · v1.0.0)
- 실행기: scripts/deploy_release.py run --plan release.json (state: deploy/prod-v1.0.0-84e9ece8/state.json)
- reseed 없음. 최초 reseed(product-first-reseed-589c627b)는 seed 실패 상태 그대로 둔다(controller failed).

## 단계 결과
- space ✓ · envbak ✓ (/opt/colab-v2/prod.env.bak-prod-v1.0.0-84e9ece8) · ship ✓ (prod-84e9ece8634b) · backup ✓ (_ops/backups/prod/2026-09-17T075426Z-*)
- up ✓ (컨테이너 4 healthy) · deploy_web ✓ (colab-platform-web-prod) · state ✓ · leave_maintenance ✓ (E1HUNU140VL6BK 원본 복원, ETag E1X6FK5RDHNB96, 재읽기 digest 일치, maintenance-state.json state=restored)
- verify 1차: doctor ⑬ endpoint ✗ (/api/v1/me 타임아웃) → 원인 = freeze가 걷어낸 SG 규칙(tcp 8000 ← pl-22a6434b, 옛 sgr-02e0ca9c88aac2191) 미복원
  · 복원: authorize-security-group-ingress → sgr-01041362ade5a8a63 (17:0x KST)
  · 실행기 state.json 은 verification_failed 로 남는다(계획에 resume_checks 없어 재개 불가 — 해시 고정). 1차 산출물 = post-failed-1/, EC2 release-artifacts/prod-v1.0.0-84e9ece8-failed-1
- verify 2차(직접 실행, 같은 run-env): doctor 15/15 ─ 0 (post/doctor.log·post.json) · release_evidence.py post 통과 · web-hash index+assets 95 일치 · EC2 /root/colab-boot/ops.env 삭제 확인

## 실행 전 정리
- 버킷 정책: 정본 2문(freeze Deny 없음). CloudTrail PutBucketPolicy 09-15 16:59:51(freeze)·17:21:58(thaw) 두 건 → 09-15 seed 403 원인 = thaw 후 전파 지연.
- CORS: http://127.0.0.1:18080 제거 (cors-before.json 백업). www.colab-hydro.com 유지(CF 별칭 실재). 정본 파일 infra/prod/iam/cors-data.json 은 www 도메인 미반영 — 후속 PR.
- known_hosts: 54.116.55.178 검증 키를 ~/.ssh/known_hosts 에 등록.

## 계정
- 교수 000000000000000000HYMETSP1: 비밀번호 초기값(이메일)로 reset, mustChangePassword=true, 초기값 로그인 201 확인. 임시 운영자 권한(service_operator) 아직 유지 — 해제는 변경 완료된 다른 운영자가 수행해야 함.
- 운영자 4: 초기값 로그인 201, 변경 전 제한 범위(관리자 API 403, /me 401 무소속). 비밀번호 변경 없음.

## 미결
- 교수 운영자 권한 회수(intent 2026-09-16 admin-full-access 12행) · 무소속 운영자 브라우저 로그인 흐름 실측 · CORS apex(colab-hydro.com) 미포함 · CF 함수 colab-prod-initial-reseed-589c627b 잔존(미연결) · 삭제된 ops 스크립트 복구 · 데이터셋 0건(정본 적재 별도)
