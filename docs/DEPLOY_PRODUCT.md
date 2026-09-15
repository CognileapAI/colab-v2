# product 첫 배포 준비

현재는 구현과 로컬 검증 단계다. GitHub 브랜치 전환·운영 배포·운영 삭제는 아직 실행하지 않았다.
승인 결정은 `dev-package/intent/2026-09-15-develop-product-deployment.md`, 전체 상태는
`dev-package/prd/rounds/R-DEVELOP-PRODUCT.md`에서 관리한다.

## 제공된 운영 파일 확인

입력은 사용자가 전달한 `C:\Users\ttlhi\Downloads\colab-platform (2)` 안의 `colab-platform`이다.
환경 파일·DB URL·SSH 키·계정 파일을 비교했으며 비밀 값은 이 문서에 옮기지 않았다.
버킷·DB 이름은 기존 운영 infra와 일치한다. EC2 조회 권한 추가 후 운영 IP를 확인했다.
SSH 호스트 키 확인은 미완료이며 브랜치 전환·CI 연결을 먼저 진행한다. 운영 역할의 실제 권한·DB 스키마·설치 상태는 아직 확인하지 못했다.

실환경 연결 뒤 아래를 준비한다.

- 운영 SSH 호스트와 서버의 실제 UID/GID를 확인한다.
- 비공개 디렉터리에 운영 파일을 설치하고 누락된 account-admin·ownership·operator 연결 파일을 준비한다.
- dev와 같은 계정·역할·소속·비밀번호 입력을 연결한다. 제공 prod 계정 파일 하나만으로는 승인 범위를 충족하지 않는다.
- 운영 실행 호스트의 영속 상태 디렉터리와 PR 검사·배포 실행 환경을 연결한다.
- 기본 화면·API·미리보기 점검과 비공개 적재 경로, 직접 origin 차단, 쓰기 중지 검사를 실제로 확인한다.
- 두 DB와 저장 파일을 같은 쓰기 중지 구간에서 백업하고 읽기 및 복원 리허설을 수행한다.

## 최초 삭제 입력

`dev-package/tools/product-reseed/`의 `manifest.example.json`, `reset-input.example.json`,
`backup.example.json`은 입력 형식 예시다. 빈 값이 있으므로 그대로 실행할 수 없다.

manifest는 정확한 두 DB·스키마·S3 key·멀티파트 ID를 담는다. `uploads/`, `previews/` 밖의
삭제는 거부하며 `_ops/`는 보존한다. key 삭제는 현재 서비스에서 파일을 제거하는 작업이다.
S3 과거 버전까지 물리 삭제하는 명령은 실행하지 않는다.

백업 목록에는 `platform`, `ai` DB dump와 삭제할 모든 S3 key의 보존 사본을 넣는다.
각 항목의 `source`는 DB 체인 이름 또는 정확한 S3 key이고, `path`·`sha256`은 보존 사본을
가리킨다. 실제 보존 파일의 바이트와 삭제 직전 S3 원본 스트림의 SHA256을 대조한다.
원본은 HEAD의 ETag를 If-Match로 묶어 읽는다. 백업 hash 일치는 복원 리허설 통과를 대신하지 않는다.
manifest와 백업 목록, URL 파일, 보존 사본은 실행자 소유의 비공개 일반 파일로 설치한다.

입력 결속 순서는 백업 파일 → 백업 목록 → 운영자 설정 → manifest다. manifest에 자신의
hash 또는 아직 존재하지 않는 병합 SHA를 넣지 않는다. 최종 manifest 바이트 hash를 PR
검사와 최초 실행 기록에 전달한다. 비밀번호·접속 URL·SSH 키 본문은 PR에 넣지 않는다.

`reset-input`의 quiescence는 승인된 읽기 검사 명령과 그 파일 hash 목록이다. 성공하려면
실제 검사 결과 JSON에 `writers_stopped: true`, `origin_isolated: true`, 현재 배포의
`candidate_sha`가 있어야 한다. 고정된 성공 값을 출력하는 대역 명령을 실환경 설정에 쓰면 안 된다.
이 명령의 실제 구현과 서버 대조는 실환경 연결 작업에 남아 있다.

## 입력 검사와 최초 기록 등록

아래 CLI는 저장소 루트에서 실행한다. 경로와 hash는 검토한 실제 입력으로 지정한다.

```bash
python3 services/core-api/ops/reset_product_environment.py \
  --manifest MANIFEST --manifest-sha256 SHA256 --config RESET_INPUT --check
```

`--check`는 파일·대상·백업 입력만 검사한다. 원격 연결·점검 확인·삭제·실행 기록 등록은 하지 않는다.
실환경 준비와 PR 입력 검토가 끝난 뒤 같은 인자로 `--provision`을 명시 실행해 schema와 S3
단계의 ready 기록을 등록한다. 상위 최초 실행 기록과 배포 기록도 각각 사전 등록해야 한다.
일반 배포는 기록이 없다고 새 초기화를 시작하지 않는다.

schema 실행은 상위 최초 실행의 `running/reset`, S3 실행은 `running/s3` 단계에서만 허용한다.
현재 DB·파일 목록과 승인 입력을 대조하고 점검 및 쓰기 중지를 확인한 뒤 변경한다.
부분 실패 기록은 자동 반복하지 않는다. 사람이 실물과 기록을 확인한 뒤 상위 최초 실행의
수동 재개 절차를 사용한다. 첫 성공 뒤의 일반 PR에는 초기화 단계를 포함하지 않는다.

수동 복구를 끝낸 최초 실행의 완료 확인은 `reseed.py --plan PLAN --state-dir STATE --verify-completed`로
수행한다. 같은 입력·후보의 `succeeded` 기록만 성공으로 인정하며 단계 명령은 실행하지 않는다.
상위 배포 재개의 검사 명령에서 이를 사용해 이미 끝낸 초기화를 반복하지 않는다.

GitHub의 `pull_request` 검사는 PR merge ref에서 실행되므로 실제 검사 SHA와 head/base 부모 관계를
함께 확인해야 한다. `pull_request_target`의 workflow 출처는 현재 default branch다.
기본 분기를 develop으로 바꾼 뒤 workflow 출처와 environment 분기 제한이 실제로 맞는지
읽기 확인한다. 과거의 “항상 PR base branch 코드” 설명을 그대로 적용하지 않는다.
근거: [GitHub workflow 이벤트](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
[pull_request_target 출처 변경](https://github.blog/changelog/2025-11-07-actions-pull_request_target-and-environment-branch-protections-changes/).

## 남은 검증

로컬 대역 시험과 실제 운영 검증은 별개다. GitHub 필수 검사·직접 push 차단·사람 병합,
지정 버전 배포, dev 단일 완주, 운영 최초 실행, 로그인·자료·미리보기 확인, 후속 배포의 reset 0건은
전체 계획에 따라 각각 증거를 남겨야 한다. 현재 이 실환경 흐름은 완료되지 않았다.
