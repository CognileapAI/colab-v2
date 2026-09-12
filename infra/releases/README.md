# 배포·검증·완료 알림의 실행 진입점

배포는 `python3 scripts/deploy_release.py run --plan <release.json>`으로 실행한다.
배포 명령을 모두 실행한 뒤 모든 환경의 검증 명령을 실행하고, 모두 exit 0일 때 Slack을 한 번 전송한다.
대화 종료나 별도의 `prepare` 호출은 필요 없다. 계획은 신뢰할 수 있는 로컬 실행 코드이므로 실행 전에 검토한다.
계획에 비밀번호·접속 문자열·토큰을 넣지 않는다. 기존 보호된 환경 파일과 자격 공급 방식을 유지한다.

## 계획

다음은 구조 예시이며 경로·버전·hash를 실제 검토한 배포 패킷으로 바꿔야 한다.
`deploy`와 `verify`는 각각 한 개 이상의 argv 배열이다. 셸 문자열이 아니므로 `~`, `$변수`, `&&`는 자동 해석하지 않는다.
명령은 현재 Git 루트에서 실행된다. 다른 작업 사본의 검증이 필요하면 절대 경로 스크립트 안에서 해당 사본으로 이동한다.

```json
{
  "schema": "colab-deploy/1",
  "id": "design-20260912-dv-st",
  "summary": "글꼴과 여백을 정리하고 밝게·어둡게 테마를 반영했습니다.",
  "inputs": [
    {"path": "/absolute/reviewed/bundle-manifest.json", "sha256": "REPLACE_WITH_64_HEX_SHA256"}
  ],
  "targets": [
    {
      "name": "dv",
      "version": "REVIEWED_DV_BUILD_DIGEST",
      "deploy": [["bash", "/absolute/reviewed/deploy-dv.sh"]],
      "verify": [["bash", "/absolute/reviewed/verify-dv.sh"]]
    },
    {
      "name": "st",
      "version": "REVIEWED_ST_IMAGE_DIGEST",
      "deploy": [["bash", "/absolute/reviewed/deploy-st.sh"]],
      "verify": [["bash", "/absolute/reviewed/verify-st.sh"]]
    }
  ]
}
```

DV 전체 배포 패킷은 기존 `infra/dev/build.sh` → `ship.sh` → 원격 `up.sh` → `ops/deploy_web.py`를 포함한다.
프런트만 바꾸면 이미지/DB 단계는 필요 없다. 검증 패킷은 현재 배포 버전과 공개 index/assets hash 대조 및 `deploy_doctor` 전 항목 검사를 포함한다.
ST 전체 배포는 `bash infra/staging/deploy.sh --target staging`을 deploy 명령으로 넣는다.
ST 프런트만 바꾸면 검증된 이미지에 대해 `docker compose ... up -d --no-deps --no-build frontend`를 사용하고,
기존 다른 서비스의 불변, 공개 번들 hash, `verify/verify-deploy.sh`를 검증 패킷에 포함한다.
부분 배포에 불필요한 전체 스택 재생성이나 마이그레이션을 추가하지 않는다.

검증 명령은 단순 `true`나 예전 보고서 읽기가 아니라 **해당 환경의 현재 버전과 동작**을 검사해야 한다.
실행기는 검증 명령의 종료코드를 소비하는 오케스트레이터다. 임의 스크립트의 검사 품질이나 수동 Docker/AWS 호출을 보안 경계로 강제하지 않는다.

```bash
python3 scripts/deploy_release.py run --plan /absolute/release.json --check
python3 scripts/deploy_release.py run --plan /absolute/release.json
python3 scripts/deploy_release.py status design-20260912-dv-st
```

`--check`는 구조와 고정 입력 hash만 검사하며 배포·검증 명령이나 Slack을 실행하지 않는다.
입력은 각 단계 직전에도 재검사한다. 빌드가 새로 생성할 파일 대신 검토한 소스/빌드 패킷 manifest를 고정한다.
실제 배포 파일이 이 manifest와 같은지는 검증 패킷에서 대조한다.

## 기존 진입점

- `infra/staging/deploy.sh --target staging`은 실행기를 자동 경유한다. 파이프라인/cron 호출도 이 경로를 따른다.
- `ops/deploy_web.py`의 실제 업로드는 실행기의 자식 명령에서만 허용한다. 단독 CLI는 쓰기 전에 exit 78로 거부한다.
  `--dry-run`과 Python 라이브러리 `plan`/`sync`는 유지한다.
- `COLAB_DEPLOY_MANAGED`는 자식 프로세스 재진입 방지용이다. 사람이 설정해 진입점을 우회하는 운영 절차로 사용하지 않는다.
- `up.sh`/`ship.sh`는 원격 기동·반입의 부분 작업이다. 이것만 실행하고 전체 배포 완료라고 보고하지 않는다.

## 상태·중복·실패

실행 기록은 Git common directory의 `deploy-releases/`에 둔다. worktree끼리 공유하는 별도 배포 잠금으로 겹친 실행을 거부한다.
이는 기존 staging fd9 잠금과 별개이며 부모의 fd9 상속 규약은 유지한다.
동일 id/동일 계획의 전송 완료 건은 다시 배포하거나 전송하지 않는다. 동일 id에 다른 계획/버전/입력을 넣으면 거부한다.

| 종료코드 | 의미 |
|---|---|
| 0 | 배포·검증·Slack 접수 성공, 또는 이미 전송된 동일 건 |
| 1 | 배포/검증 명령 실패. 전체 완료 알림 없음 |
| 20 | 배포·검증 성공, 알림 설정/거절 실패 또는 전송 결과 불명확 |
| 75 | 다른 배포 실행 중 |
| 78 | 계획·입력·기존 실행 상태를 확인할 수 없음 |

알림 실패는 배포 성공을 취소하지 않는다. 파이프라인/watch도 exit 20을 별도로 표시하며 배포 실패 표식으로 바꾸지 않는다.
설정 부재·Slack의 명시 거절(`notification=failed`)은 아래 명령으로 **배포 없이 현재 상태를 다시 검증한 뒤** 알림만 재시도한다.

```bash
python3 scripts/deploy_release.py run --plan /absolute/release.json --retry-notification
```

자동 ST 실행의 계획은 출력된 기록 옆 `<id>/plan.json`에 보관된다. 그 경로로 위 명령을 실행한다.
타임아웃·전송 중 종료(`sending`/`uncertain`)는 이미 Slack에 도착했을 수 있어 자동 재전송하지 않는다. 채널에서 확인해야 한다.
배포/검증 도중 종료·실패도 같은 id로 무조건 재배포하지 않는다. 실제 상태와 남은 환경을 확인한 후 별도 검토한 복구 계획을 만든다.

웹훅 설정은 기존 `python3 scripts/slack_completion.py setup`을 사용한다. 비밀 파일은 저장소 밖에 유지한다.
이 배포 알림은 개발 완료 Stop 알림과 별개다. 같은 배포만을 위해 Stop 완료 알림까지 추가 등록하지 않는다.

새 운영자 알림 manifest를 쓰는 배포는 operator_notifications.spool_directory에 terminal 사건을 먼저 저장하고 legacy webhook을 호출하지 않는다. 실패 전달 재개는 infra/notifications/README.md의 ID 지정 절차를 사용하며 배포·검증을 재실행하지 않는다.
