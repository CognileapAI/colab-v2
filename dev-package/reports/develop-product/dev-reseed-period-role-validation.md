# dev 재적재 도구 검증 — 2026-09-16

최신 develop 8c063cf2 기반 구현. 실제 dev 변경·초기화·업로드·브라우저 E2E는 실행하지 않았다.

## 부모 직접 실행

- `python -m pytest -q -p no:cacheprovider dev-package/tools/dev-reseed/tests/test_accounts.py dev-package/tools/dev-seed/tests/test_runner_plan_mapping.py dev-package/tools/dev-seed/tests/test_build_plan.py`: 66 통과, 실패 0, 종료 0.
- `bash gates/run.sh dev-reseed-selftest`: 7 통과, 판정 실패 0, 준비 실패 0, 종료 0.
- 실제 참조자료 경로를 지정한 `build_plan.py --dry-run`: 자료 28, 간선 18, 본체 파일 543, 누락 0, 행 불일치 0, 종료 0.
- 기존 기간 조사와 새 정본 26개 날짜·단위 대조: 불일치 0. DEM·Aspect 2개는 승인된 2023-05 월 단위.
- 스킬 quick_validate 및 git diff --check: 종료 0.

## 확인한 실패 경로

기간 누락·잘못된 날짜·중복 정본·다른 보조입력 대상 차단. 월 정밀도 유지.
보조입력 API 실패 후 등록 ID를 이용해 재개하며 중복 업로드하지 않는다.
기간·설명 검증 미달은 실패로 반환하고 최초·재개 모두 계정 최종화 전에 차단한다.
배포 호출은 기존 `--notification-off` 옵션으로 외부 알림을 비활성화한다.
독립 검토에서 오류 전파·재개·간선 대상 필터를 수정한 뒤 구현 수용 판정을 받았다.

## 남은 실행 조건

사용자의 develop 대상 PR 게시·병합 및 실제 병합 SHA의 CI 증거가 필요하다.
그 뒤 보호된 실행 계획, 새 준비 검사·리허설·삭제 대상 목록 및 삭제 전 검토를 거친다.
실제 5계정 로그인과 모든 자료의 저장·조회·미리보기 검증은 그 실행에서 확인한다.

## 공개 저장소 반영 경계

실제 계정 프로필은 저장소 밖 0600 승인 파일로 분리했다. 공개 예시는 가상 이메일만 사용한다.
보호 파일 부재/권한 불일치 시험 RED 후 수정했으며, 위 66개 시험과 7개 게이트는 분리 후 재실행 결과다.
실제 승인 프로필의 읽기 전용 validate도 종료 0이다. 실제 로그인·계정 변경은 하지 않았다.
