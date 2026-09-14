# develop/product 로컬 구현 검증

2026-09-15, 통합 사본 `integration/r-develop-product`. 커밋·push·원격 브랜치 변경·운영 배포·데이터 삭제는 실행하지 않았다.

## 통합한 내용

- dev 원천 develop, prod 원천 product 검사와 기록. 비조상·옛 우회 차단, 좁은 fetch 설정에서도 원천 ref 확보.
- 동일 저장소 develop → product 사람 병합 판정, 병합 전 head/base·manifest·검사 SHA 승인 artifact, 실제 병합 후 API 재대조.
- producer workflow의 두 부모 파일을 외부 검토 SHA256에 대조. 정책 파일 변경은 검토한 운영자 정책 갱신이 필요하다.
- 영속 배포 기록·최초 PR 한정 reseed·일반 배포 분리. 명령별 완료 기록과 검증 전용 수동 재개로 불확실한 변경을 자동 반복하지 않는다.
- 최초 실행의 10단계 기록, 점검 해제 전 검증, 실패/중단 재개. 완료 확인 전용 `--verify-completed`는 명령을 실행하지 않는다.
- 운영 reset은 정확한 대상·schema·key·멀티파트·보존 사본 hash를 대조한다. 삭제 직전 S3 원본을 ETag/If-Match로 읽어 보존 사본과 SHA256을 비교한다.
- 점검은 기본/API/previews 세 경로, LIVE 함수 503, 원격 Deployed/config digest 및 비공개 접근/직접 origin 차단을 확인한다. 해제 실패의 점검 재진입과 실제 상태 불명 기록을 구분한다.
- controller → reset → maintenance 자식까지 잠금을 유지한다. 부모 둘을 중단해도 마지막 자식이 잠금을 보유하는 실제 subprocess 시험을 추가했다.
- dev 프로젝트 이름/ID 추출과 미리보기 최종 상태·실패한 화면 이동 처리 결함 수정.

## 직접 실행한 검증

| 검사 | 결과 | 근거 |
|---|---|---|
| product-release-selftest | exit 0, 74 passed / skip 0, 필수 32 | `integrated-local/gate-summary.json` |
| product-reseed-selftest | exit 0, 87 passed / skip 0, 필수 28 | `integrated-reseed/gate-summary.json` |
| dev-reseed-selftest | 6개 fixture 통과 | `dev-regression/gate-summary.json` 및 최종 `integrated-dev/gate-summary.json` |
| dev ship 경계 | 38개 확인 통과 | 이 세션의 `bash infra/dev/tests/ship-gate.sh` 출력 |
| prod ship 경계 | 48개 확인 통과 | 이 세션의 `bash infra/prod/tests/ship-gate.sh` 출력 |
| workflow 구문 | YAML 3개 파싱 성공 | 로컬 PyYAML; GitHub 실제 실행을 뜻하지 않음 |

각 product 게이트 요약은 green 1 / red(판정) 0 / red(준비) 0이다.
처음 여러 게이트 이름을 한 호출에 전달했을 때 실행기가 첫 인자만 처리한 것을 확인했다.
따라서 한 호출의 결과를 여러 게이트 통과로 계산하지 않았고, 각각 별도 호출·보고서로 검증했다.
CI도 두 게이트를 각각 호출하도록 수정했다.

추가 음성 fixture에서 1 passed / 73 skipped를 성공으로 표시하던 release 게이트를 재현했다.
JUnit의 실제 실행·누락·skip을 대조하도록 수정한 뒤 같은 fixture는 exit 1로 거부된다.
이 fixture의 의도된 skip 73건을 제품 시험의 성공으로 계산하지 않는다.

reset 시험의 첫 실행은 서비스 autouse DB fixture 입력 부재로 준비 단계에서 실패했다.
순수 명령 경계 시험은 `--noconftest`로 실행했으며, 실제 DB/AWS 검증이라고 보고하지 않는다.
이후 같은 파일 원본 변경과 부모 중단을 포함한 실제 회귀 RED→GREEN을 확인했다.

격리 레인의 task report는 각 원본 worktree에서 `verify-report --task`로 확인한 뒤 통합했다.
SubagentStop이 부모 `.git`만 찾는 경로 문제는 정상 통과로 바꾸지 않았고 metadata를 복사해 우회하지 않았다.
부모 통합 사본의 전체 H7 또는 실환경 E2E가 통과했다고 주장하지 않는다.

## intent 대비 미달

1. main → develop/default 전환과 product 생성: 원격 미실행.
2. product PR-only와 잘못된 원천/직접 push 차단: 로컬 판정 구현, GitHub 보호 설정·실제 거부 미검증.
3. 사람 병합만으로 배포: 로컬 이벤트/API 경계 구현, 실제 runner·환경·배포 명령 연결 미완료.
4. 첫 PR의 배포·reseed·검증: 실제 첫 PR·manifest·단계별 운영 명령과 복구 자료 준비 필요.
5. dev 동일 계정·비밀번호·정본 재현: 제공 파일 차이 확인, 실제 적재/로그인과 dev 단일 완주 미실행.
6. 후속 배포 reset 0건: 로컬 상태 시험 통과, 실제 후속 PR 미실행.
7. 실패 시 점검 유지·사람 재개: 로컬 중단/복구 시험 통과, 실제 CloudFront·origin·DB·S3 리허설 미실행. 원격 서비스 자체가 응답하지 않아 복구도 실패하면 공개 여부를 확정하지 않고 unknown으로 기록하며 사람 확인이 필요하다.
8. 제공 운영 설정 연결: 파일 내부 비교 완료, EC2 읽기 권한 추가·운영 IP 확인 후 실제 서버 설정 확인 대기.

초과 제품 기능 0건. 신규 마이그레이션 0건. `DEVELOP-PRODUCT`는 open 유지한다.
브랜치 전환은 cutover.md에 별도 실측했다. 다음 작업은 CI·승격 검사 설치다. 상세 파일 준비는 `docs/DEPLOY_PRODUCT.md`를 따른다.
