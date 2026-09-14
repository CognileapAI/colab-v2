# 브랜치 전환 실측 — 2026-09-15

사용자 요청: “그러면 브랜치전략부터 적용할까”. advisor 제한된 ref·보호 전환 approve-with-changes 후 실행.

- GitHub main → develop 이름 변경 및 기본 develop 읽기 확인 완료.
- product 생성 완료. 두 ref SHA: `6db30323a78a4e63f3e28810db0f325b69551979`.
- product 생성 전에 ruleset 23379713 활성화. 우회 주체 없음, 현재 관리자도 never.
- PR 필수, merge commit만 허용, 강제 push·삭제 금지, 대화 해결 필수.
- 필수 검사 product-promotion / product-safety, GitHub Actions app 15368, strict 최신 base 검사.
- 최초 ref 생성에서만 검사 예외 사용, 생성 직후 do_not_enforce_on_create=false로 변경·읽기 확인.
- develop은 기존 main의 강제 push·삭제 금지 보호를 유지한다.
- 열린 PR 0건. Pages는 gh-pages를 사용하여 영향 없음.
- 원격 등록 workflow는 agent bridge / ci / pages 세 개로 운영 배포 workflow 없음.
- 로컬 origin/develop, origin/product fetch 및 origin/HEAD=develop 설정 완료. 미커밋 구현 보존.

## 남은 연결
- 원격 필수 승격 검사 미설치이므로 product 병합은 현재 차단 상태다. PR-only 설정과 실제 develop 출처/사람 병합 검증 완성을 구분한다.
- product base에서 실행할 검증 코드의 최초 설치 절차를 구체화해야 한다. 기존 구현을 단순 첫 PR로 넣으면 base에 스크립트가 없어 검사 실패한다. 검사 면제를 임의 실행하지 않는다.
- 원격 CI의 push 필터는 아직 main이다. develop 코드 통합 전에 CI 연결 개정을 반영·검증해야 한다.
- 운영 배포·reseed 실행 0건. 실제 dev reseed 및 운영 준비·첫 PR은 미완료다.
- EC2 DescribeInstances 권한 추가 후 운영 IP 54.116.55.178 확인. SSH 포트 도달했으나 신뢰 호스트 키 미등록으로 로그인 미실행. 사용자 요청에 따라 SSH 수동 안내를 중단하고 브랜치 전환을 먼저 처리했다.

증거: GitHub branches/default_branch, rulesets/23379713, rules/branches/product, branches/develop/protection, actions/workflows API 응답을 직접 대조했다. 실제 거부 push 실험은 수행하지 않았다.
