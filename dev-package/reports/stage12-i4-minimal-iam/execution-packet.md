# I4 deploy-verification 최소 IAM 대안

실행 상태: IAM apply 0, 기존 policy 변경 0, cron 설치 0, webhook 전송 0. 현재 자동 probe는 `13/2/0`이며 이 초안을 적용 전 성공으로 세지 않는다.

## 실제 실패와 최소 범위

`services/core-api/ops/deploy_doctor.py:246-266`의 `check_web_bucket`은 정확히 두 동작만 한다.

1. `HeadObject("index.html")`: IAM action은 `s3:GetObject`, object ARN은 `arn:aws:s3:::colab-platform-web-dev/index.html` 하나다.
2. `ListObjects` with prefix `assets/`: IAM action은 bucket의 `s3:ListBucket`이며 `StringEquals s3:prefix = assets/`로 고정한다.

[정책 JSON](ColabDevPublicWebDoctorRead.json)은 위 두 Allow만 갖는다. Put/Delete, 다른 object key, 다른 prefix, 다른 bucket, data bucket action, IAM action은 0개다. data bucket diagnostics는 현 IMDS role에서 이미 green이다.

대상 role은 `colab-platform-app-dev-role`, 새 inline policy 이름은 `ColabDevPublicWebDoctorRead`다. 기존 role policy를 수정하거나 같은 이름으로 덮어쓰지 않는다. 이 role을 쓰는 제품 앱 컨테이너도 공개 배포물 `index.html` 읽기와 `assets/` 목록 권한을 함께 얻게 된다. root cron만의 권한 분리는 아니며 이 침해 반경을 수용할지 사용자가 결정해야 한다.

## 읽기 전용 사전 확인

현재 로컬 `colab-dev` uploader profile로 `iam:ListRolePolicies`를 호출했으나 AccessDenied(exit 254)였다. 따라서 새 policy 이름의 실제 부재는 아직 판정 불가다. 권한을 확대하지 않았고 이 결과를 부재로 해석하지 않는다. 적용 권한을 가진 operator profile로 다음 precheck가 성공하기 전에는 진행하지 않는다.

운영자 `sts get-caller-identity`의 Account가 **606175197146**이고 `iam get-role`의 ARN이 **arn:aws:iam::606175197146:role/colab-platform-app-dev-role**인지 먼저 일치시킨다. 다른 계정·role·조회 실패면 중단한다. 정책 SHA는 `b5e04c4a09fa6a1329d54aa652f83d90ac41bdf729239e6812baba62ea183157`과 같아야 한다.

```bash
: "${COLAB_AWS_OPERATOR_PROFILE:?operator profile required}"
ROLE=colab-platform-app-dev-role
POLICY=ColabDevPublicWebDoctorRead

# exit 254/AccessDenied면 준비 실패. exit 0이면 이미 존재하므로 내용을 덮어쓰지 않고 중단한다.
if aws --profile "$COLAB_AWS_OPERATOR_PROFILE" iam get-role-policy \
  --role-name "$ROLE" --policy-name "$POLICY" > /tmp/colab-i4-existing-policy.json 2>/tmp/colab-i4-existing-policy.err; then
  echo "policy already exists; stop without overwrite" >&2
  exit 1
fi
# GetRolePolicy의 NoSuchEntity만 부재다. AccessDenied·네트워크·다른 오류를 허용하지 않는다.
python3 - <<'PY'
from pathlib import Path
import re
error = Path('/tmp/colab-i4-existing-policy.err').read_text()
if not re.search(r'An error occurred \(NoSuchEntity\) when calling the GetRolePolicy operation:', error):
    raise SystemExit('policy absence not established; stop')
PY
```

## 승인 뒤 적용

레포 루트에서 정책 파일 SHA-256을 먼저 봉인하고, 기존 inline policy 목록/각 policy document hash를 snapshot한다. 값이 본 패킷과 다르면 중단한다.

변경은 단독 운영 창에서 수행한다. 적용 직전에 위 부재 검사를 한 번 더 수행하며, 그 사이 다른 운영자가 같은 이름을 만들 수 있으면 중단한다. `put-role-policy` 자체에는 create-if-absent 보장이 없으므로 사전 조회만으로 경쟁을 막았다고 주장하지 않는다.

```bash
sha256sum dev-package/reports/stage12-i4-minimal-iam/ColabDevPublicWebDoctorRead.json
aws --profile "$COLAB_AWS_OPERATOR_PROFILE" iam put-role-policy \
  --role-name colab-platform-app-dev-role \
  --policy-name ColabDevPublicWebDoctorRead \
  --policy-document file://dev-package/reports/stage12-i4-minimal-iam/ColabDevPublicWebDoctorRead.json
aws --profile "$COLAB_AWS_OPERATOR_PROFILE" iam get-role-policy \
  --role-name colab-platform-app-dev-role \
  --policy-name ColabDevPublicWebDoctorRead
```

조회 결과를 canonical JSON으로 바꿔 로컬 정책과 statement/action/resource/condition 전건 일치시키고, 기존 policy snapshot hash가 불변인지 확인한다. IAM 전파 뒤 새 일회용 probe 1회만 실행한다.

```bash
ssh -i "$COLAB_DEV_KEY_FILE" -o BatchMode=yes -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes "$COLAB_DEV_SSH" \
  'sudo -n /opt/colab-ops/versions/d56428d6945d/infra/ops/probes/deploy-verification.sh'
```

완료 판정은 같은 단일 실행의 exit 0과 `15/0/0`이다. 특히 web `index.html`과 `assets/` 두 줄이 green이고 credential source가 IMDS인지 확인한다. service-health/backup 결과와 합산하지 않는다. 13/2/0, readiness 78, 또는 다른 red면 cron 설치와 webhook 연결을 시작하지 않는다.

## 원복

정확한 새 policy 이름 하나만 삭제한다. 기존 policy를 put/restore로 덮어쓰지 않는다.

삭제 직전에 `get-role-policy`의 현재 PolicyDocument를 canonical JSON으로 만들고 **이번에 설치·재조회해 봉인한 canonical hash**와 대조한다. 다르거나 조회할 수 없으면 삭제하지 않는다. 새 정책이라는 이름만 보고 이후 타인의 변경을 지우지 않는다.

```bash
aws --profile "$COLAB_AWS_OPERATOR_PROFILE" iam delete-role-policy \
  --role-name colab-platform-app-dev-role \
  --policy-name ColabDevPublicWebDoctorRead
# NoSuchEntity가 확인될 때까지 읽기만 재확인한다. 다른 inline policy snapshot hash는 불변이어야 한다.
aws --profile "$COLAB_AWS_OPERATOR_PROFILE" iam get-role-policy \
  --role-name colab-platform-app-dev-role \
  --policy-name ColabDevPublicWebDoctorRead
```

원복 뒤 동일 probe는 다시 `13/2/0`이 예상되며 이를 장애로 오인하지 않는다. 실제 apply/원복은 사용자 승인과 operator precheck 뒤에만 수행한다.

독립 검토는 이 제한된 공개 배포물 읽기 대안을 수용했다. 적용 후에도 bucket policy/SCP 등으로 거절되면 실제 red를 남기고 중단한다. 추가 권한을 자동으로 넓히지 않는다. cron 설치·외부 알림 승인은 이 IAM 정책 승인에 포함되지 않는다.
