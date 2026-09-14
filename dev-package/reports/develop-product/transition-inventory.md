# develop·product 전환 조사

2026-09-15 읽기 실측. 비밀 값·파일 내용·운영 자격 hash는 기록하지 않는다.

후속 변경: 기본 develop/product 생성·보호 적용 완료. 현재 상태는 [cutover.md](cutover.md). EC2 읽기 권한 추가 후 IP 54.116.55.178 확인, SSH 로그인은 미실행. 아래 권한 거부·main 상태는 전환 전 이력이다.

## GitHub 전환 전 상태
- 저장소: CognileapAI/colab-v2, public. 기본 브랜치 main.
- 기준 HEAD: `6db30323a78a4e63f3e28810db0f325b69551979`.
- 열린 PR 0건. 저장소 ruleset 0건.
- main: force push·삭제 금지. 필수 검사·필수 PR 리뷰·push 제한 없음, 관리자 적용 꺼짐.
- merge commit/squash/rebase 허용, auto merge 꺼짐.
- 따라서 현재 설정만으로는 새 product PR-only·사람 병합을 강제할 수 없다. 원격 설정 변경은 아직 하지 않았다.

## 로컬 준비
- 통합 브랜치 `integration/r-develop-product`를 현재 main tip에서 생성했다. 계획 문서의 기존 미커밋 변경을 보존했다.
- `lane/product-source`와 `lane/product-release`는 각각 별도 Git worktree이며 작성자가 분리된다.
- 두 사본에 승인 intent/spec/round를 복사하고 바이트 일치를 확인했다. 복사본은 작업 입력이며 승인 재작성 대상이 아니다.

## 실행 참조 변경 지도
- 원천 검사·기록: `infra/_lib/ship-gate.sh`, dev/prod `ship.sh`, `services/core-api/ops/deploy_doctor.py`.
- 태그: `infra/dev/tag-release.sh`, 운영의 기존 prod 태그 검사.
- CI: `.github/workflows/ci.yml`, 계약 비교 명령의 실제 PR base ref 전달.
- reseed: `dev-package/tools/dev-reseed/preflight.sh`, `reseed.sh` 기본 ref.
- 문서: `docs/BRANCHING.md`, `CLAUDE.md §10`, 배포 규칙·문서와 dev/prod README의 현행 절.
- 과거 로그·세션·fixture의 main 표기는 전환 성공으로 재해석하지 않는다. fixture는 의미에 따라 legacy/ref 부재 시험으로 유지 또는 변경한다.

## 전환 순서
1. 로컬에서 환경별 원천 검사·배포 이벤트·최초 기록·점검을 구현하고 음성 시험한다.
2. 로컬 검증과 사용자 제공 운영 설정의 내부 대상 일치를 확인한다.
3. GitHub 필수 검사·허용 사람·직접 push 제한과 실행 호스트를 실제 권한으로 확인한다. 브랜치 전환과 운영 배포 준비를 구분한다.
4. 자동 배포가 비활성인 상태로 main rename 및 기본 develop 전환, product 기준점 생성을 수행한다.
5. 실제 origin/develop 기준으로 dev 단일 완주를 검증하고 운영 입력·백업·점검 준비를 완료한다. 첫 배포 PR이 차이를 갖도록 bootstrap 버전과 첫 배포 manifest를 순서대로 반영한다. 생성 이벤트는 배포하지 않는다.
6. 사람이 첫 PR을 병합하면 head/base/manifest 검증 결과를 실제 merge SHA와 결속하여 최초 배포한다.

## 운영 입력
- 사용자가 Downloads의 `colab-platform (2)` 폴더를 제공했다. 내부 `colab-platform` 폴더에 dev/prod 환경 파일·SSH 키·DB URL·계정 파일이 존재한다.
- macOS 부가 메타데이터 폴더는 설정 입력이 아니다.
- 파일 존재는 현재 원격 자격의 유효성·실제 환경 일치를 뜻하지 않는다. 파일 간 비교 결과와 실환경 리허설을 분리해 기록한다.
- 운영 버킷 `colab-platform-data-prod`, 리전 `ap-northeast-2`, 두 DB 이름 `colab_platform`·`colab_ai`는 제공 파일과 기존 infra가 일치한다. 제공 owner URL의 역할은 `colab_owner`다. 원격 실물은 미확인이다.
- 기존 운영 CloudFront는 `E1HUNU140VL6BK` / `d1aje00ns2hjsl.cloudfront.net`, EC2 식별자는 `i-07e7b2b740bb79619`로 문서에 기록돼 있다. 현재 SSH 호스트는 파일에 없다.
- 제공 AWS 자격으로 해당 EC2를 읽기 조회했으나 `UnauthorizedOperation`이었다. 사용자에게 현재 SSH 호스트를 요청했고 응답 대기 중이다. 키 값은 출력·복사하지 않았다.
- 운영 runtime env의 ownership UID/GID, `account-admin-database.url`, `ownership-platform-db.url`, `operator-database.url`이 빠져 있다. 실제 역할/권한 확인과 비공개 설치가 필요하다. NTFS의 표시 권한을 운영 0600 설치 완료로 간주하지 않는다.
- dev 자격은 3계정·4주체, 제공 prod 자격은 1계정·1주체다. 비밀번호 일치 여부만 메모리에서 비교해 일치를 확인했으며 값·자격 hash는 기록하지 않았다. 운영 전체 계정 구성은 승인대로 dev와 맞추는 작업이 남아 있다.
- 기존 DB 백업 스크립트만으로 저장 파일 복원을 보장할 수 없다. 첫 PR에는 두 DB dump와 모든 삭제 key의 보존 사본·바이트 hash 목록을 결속하고 복원 리허설을 별도로 검증한다. S3 current key 삭제는 과거 버전의 물리 삭제를 뜻하지 않는다.

## 검증 한계
- GitHub 설정·로컬 파일 비교·AWS EC2 조회 실패까지 확인했다. SSH·DB·S3 접속, 원격 변경, 배포, 삭제는 실행하지 않았다.
