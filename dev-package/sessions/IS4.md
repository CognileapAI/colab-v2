# WU-IS4 — Terraform state 복구 절차

> **상태: 절차 작성 + 리허설 완료.** 원격 백엔드(S3+DynamoDB)는 진입조건 I0(AWS, 사람 블로커)
> 이 없어 **범위 밖**이다(`WORK-UNITS.md` IS4 행). 대신 **복구 절차를 재현 가능한 형태로** 남긴다.
> 이 문서 자체가 완료가 아니라 **인계물**이다 — 원격 백엔드 전환은 I0 이 열리면 그대로 WU 로 착수한다
> (`WORK-UNITS.md` I1/I0 행에 걸어 둔다. "나중에" 로 남기지 않는다 — `CLAUDE.md §5`).

---

## 1. 문제

`infra/staging/tunnel/terraform.tfstate` 는 이 WSL 호스트 로컬에만 있다. 레포에는 못 넣는다
(비밀·리소스 속성이 평문으로 들어간다). 호스트가 사라지면 레포의 `.tf` 선언만으로는
"지금 Cloudflare 에 뭐가 적용돼 있는지" 를 Terraform 이 모른다 — `import` 로 다시 state 를
만들어야 하고, 그 절차가 어디에도 적혀 있지 않았다. 이 WU 가 그 절차를 적고 실제로 돌려본다.

## 2. 복구 절차 — 맨 호스트에서 `terraform plan` = `No changes.` 까지

전제: 레포를 클론했고, 아래 §3 의 값 4개를 손에 쥐고 있다.

```bash
# 0. Terraform 설치 (사용자 수준 — sudo·apt 저장소 불필요)
#    IS2 세션 기록: ~/.local/bin 에 바이너리 하나 내려받아 배치. 버전은 versions.tf 의
#    required_version(>= 1.6.0) 과 provider cloudflare/cloudflare(~> 4.40) 를 만족하면 된다.

# 1. 자격증명 — 레포 밖 홈 0600 파일에서만 읽는다. 값을 셸 히스토리에 남기지 않는다.
set -a; . ~/.colab-v2-staging.env; set +a
export TF_VAR_cloudflare_api_token="$CF_API_TOKEN"
export TF_VAR_cloudflare_account_id="$CF_ACCOUNT_ID"
export TF_VAR_tunnel_id="$CF_TUNNEL_ID"

# 2. 이 디렉터리에서 실행한다 (레포 안, state 는 없는 상태)
cd infra/staging/tunnel
terraform init

# 3. import — 기존 Cloudflare 터널 config 를 새 state 로 편입한다. 신규 생성이 아니다.
terraform import cloudflare_zero_trust_tunnel_cloudflared_config.staging \
  "$CF_ACCOUNT_ID/$CF_TUNNEL_ID"

# 4. plan — 사람이 읽고 판단한다.
terraform plan
```

### `plan` 결과를 읽는 법 — 여기가 절차의 핵심이자, 이번에 실측한 함정

`import` 직후 첫 `plan` 은 **문자 그대로 "No changes."가 아니다.** 실측(§4) 상 다음이 뜬다:

```
~ resource "cloudflare_zero_trust_tunnel_cloudflared_config" "staging" {
  ~ account_id = (sensitive value)   # 값 불변 — provider 가 최초 import 시 민감도 표시만 다시 계산
  ~ tunnel_id  = (sensitive value)   # 값 불변 — 위와 동일
  # (1 unchanged block hidden)
}
Plan: 0 to add, 1 to change, 0 to destroy.
```

이건 **실제 drift 가 아니다.** provider 가 import 로 얻은 상태에 sensitivity 메타데이터를
아직 붙이지 않은 상태라 최초 1회 이렇게 뜬다. `ingress_rule` 블록(`www→nginx:80` · catch-all
`404`) 은 **"unchanged block hidden"** 으로 — 여기가 진짜 판정 지점이다.

- **0 to add, 0 to destroy** 이고 바뀌는 속성이 `account_id`/`tunnel_id` 의 민감도 표시뿐이면
  → 정상. ingress 내용 자체는 레포 선언과 일치한다는 뜻이다.
- **ingress_rule 블록 안에서 실제 값(hostname·service)이 바뀌거나, `destroy`/`replace` 가
  보이면** → 중단하고 보고한다. 특히 `destroy`/`replace` 는 터널 자체 재생성 신호이고,
  그러면 `TUNNEL_TOKEN` 이 무효화돼 staging 이 죽는다(`README.md §4` 롤백 표와 동일 규칙).

문자 그대로 "No changes." 를 보려면 이 1회 `apply` 를 거쳐야 한다(민감도 표시만 갱신되고
실값은 안 바뀌므로 안전). **이 WU 의 리허설(§4)에서는 그 apply 를 실행하지 않았다** — 실물
터널을 대상으로 apply 하지 말라는 이번 세션 제약 때문이다. 즉 "완전 무결 복구"의 마지막
한 걸음(무해한 apply 1회)은 절차에 적혀 있으나 이번엔 시연하지 않았다 — 정직하게 이 문서에
남긴다.

```bash
# 5. (맨 호스트 실전 복구에서는 여기까지 간다 — 이번 리허설은 여기서 멈췄다)
terraform apply   # ingress 값 불변 확인 후. 민감도 표시만 정착시킨다.
curl -sS -o /dev/null -w '%{http_code}\n' -I https://www.colab-hydro.com/healthz  # 200
terraform plan    # 이제 문자 그대로 "No changes."
```

## 3. 레포에 없는 값 4개 — 어디서 오는가

| 값 | 레포에 있는가 | 어디서 오는가 |
|---|---|---|
| `CF_API_TOKEN` | 없음 | Cloudflare 대시보드 → My Profile → API Tokens → Custom token (`Account: Cloudflare Tunnel : Edit` 하나면 충분, `README.md §3`) |
| `CF_ACCOUNT_ID` | 없음 | Cloudflare 대시보드 Zero Trust → Networks → Tunnels, 또는 `cloudflared tunnel info` (읽기 전용) |
| `CF_TUNNEL_ID` | 없음 | 위와 동일 위치 |
| `CF_TUNNEL_TOKEN` | 없음(복구엔 불필요) | 커넥터 기동용 — `infra/staging/compose.yml` 이 쓴다. 이 WU 의 복구 대상이 아니다(이미 살아있는 컨테이너는 안 건드린다) |

넷 다 **레포 밖, 홈 디렉터리 0600 파일**에 산다 — 이 호스트에서는
`~/.colab-v2-staging.env`(절대경로는 이 표기까지만, 문서엔 `~` 로만 적는다).
CLAUDE.md §5 에 따라 이 문서에도 실제 절대경로는 적지 않는다. 새 호스트에서는 같은 이름의
파일을 같은 4줄(`CF_TUNNEL_TOKEN`·`CF_API_TOKEN`·`CF_ACCOUNT_ID`·`CF_TUNNEL_ID`) 로 새로
만들면 된다 — 값의 원천은 위 표, 토큰만 재발급이 필요할 수 있다(만료·회수 시).

## 4. 리허설 — 무엇을 어떻게 안전하게 검증했는가

**실물 파괴 없이 실행.** 순서:

1. 현재 상태 확인 — `www.colab-hydro.com/healthz` = 200. 실제 `terraform.tfstate` 로
   `terraform plan` → **"No changes."** (사전 확인).
2. 실 state 파일 2개(`terraform.tfstate`·`.backup`)를 스크래치 디렉터리로 **복사**(원본은
   그대로 둠 — 이동이 아니라 복사).
3. `.tf` 선언 파일 4개(`versions.tf`·`variables.tf`·`tunnel.tf`·`terraform.tfvars.example`)만
   별도 스크래치 디렉터리로 복사 — **state 파일도 `.terraform/` 도 가져가지 않음**. 이게
   "state 를 잃은 맨 호스트" 의 근사다.
4. 그 디렉터리에서 §2 의 순서(`init` → `import` → `plan`)를 **실제 토큰·계정 ID·터널 ID** 로
   실행. 이 값들이 이 호스트의 `~/.colab-v2-staging.env` 에 이미 있었기 때문에 가능했다
   (토큰 부재로 막힐 것을 예상했으나, 실측 결과 값이 이미 채워져 있었다).
5. 결과 — `import` 성공, `plan` = `0 to add, 1 to change, 0 to destroy`(민감도 표시 갱신뿐,
   §2 서술과 일치). **`apply` 는 실행하지 않았다** — 실물 터널·실물 state 를 대상으로 하는
   변경 명령이라 이번 세션 제약(`실물 상태를 바꾸지 않는다`)에 걸린다.
6. 리허설 종료 후 — 원본 `terraform.tfstate` 를 건드리지 않았으므로 복원 조치 자체가
   필요 없었다. `md5sum` 으로 리허설 전/후 원본 state 파일이 **바이트 단위로 동일**함을 확인.
   실 디렉터리에서 다시 `terraform plan` → **"No changes."** 재확인.
   `curl healthz` → **200** (리허설 전/후 동일).

**리허설이 증명한 것**: import 절차 자체는 동작한다. ingress 선언(`www→nginx:80` + catch-all
404)이 실제 Cloudflare 측 설정과 완전히 일치한다(`unchanged block hidden`).

**리허설이 증명하지 못한 것 — 정직하게 남긴다**:
- 마지막 apply 한 걸음(민감도 표시 정착 → 문자 그대로 "No changes.")은 실행하지 않았다.
  안전하다고 판단하는 근거(값 불변)는 §2 에 적었으나, **실행으로 확인한 사실은 아니다.**
- "맨 호스트" 를 완벽히 재현하지는 않았다 — 이 호스트에 이미 terraform 바이너리가 설치돼
  있었고, `~/.colab-v2-staging.env` 도 이미 채워져 있었다. 새 물리 호스트에서 §0(설치)과
  §3(자격증명 재발급/이전)까지 포함한 완전한 리허설은 이번에 하지 않았다.

## 5. 복구가 되돌리지 못하는 것

- **터널 자체의 정체성**(`tunnel_id`, `TUNNEL_TOKEN`) — 이건 복구 대상이 아니라 전제다.
  터널이 사라지면 이 절차로 복구할 수 없다 — 그건 IS2 범위 밖의 재해다.
- **state 파일에 박제된 리소스 메타데이터의 이력**(이전 `version=N` 계보 등) — import 는
  "지금 시점"만 편입한다. 과거 몇 번 바뀌었는지의 이력은 복구되지 않는다(애초에 대시보드
  쪽에만 있었고 레포가 정본이 된 이후에는 문제되지 않는다).
- **호스트에 있던 다른 어떤 상태도 아님** — 이 절차는 `infra/staging/tunnel/` 딱 하나의
  Terraform state 만 다룬다. IS3(백업/복원)이 다루는 애플리케이션 데이터·DB 는 별개다.

## 6. 이것이 임시형인 이유 — 다음 WU

이 문서는 **로컬 state + 문서화된 import 절차**라는 임시 형태다. 진짜 해법(원격 백엔드,
S3+DynamoDB lock 등)은 `WORK-UNITS.md` IS4 행이 이미 "원격 백엔드면 I0(AWS)" 라고 못박아
뒀다. AWS 계정이 없어 지금은 열 수 없을 뿐 — **닫힌 결정이 아니라 대기 중인 진입조건**이다.

- I0 이 열리면: `infra/staging/tunnel/` 에 `backend "s3" { ... }` 블록 추가 +
  `terraform init -migrate-state` 로 로컬 state 를 옮기는 것이 후속 WU (I1 트리 안에 배치).
- 그 전까지는 이 문서(§2)가 유일한 복구 경로다. **호스트가 바뀔 때마다 이 문서로 재현**한다.

## 7. 완료 오라클 판정

`WORK-UNITS.md` IS4 행의 오라클 — "state 를 잃은 상태에서 문서만 보고 복구 성공".

- **실행됐는가**: 예. `.tf` 선언만 가진 사본 디렉터리에서 `init → import → plan` 을 실제
  자격증명으로 완주했고, ingress 선언이 실물과 일치함(`unchanged block hidden`)을 확인했다.
- **완전한가**: 아니다. 마지막 apply 한 걸음(민감도 표시 정착)은 실행하지 않았고, 완전한
  "맨 호스트"(terraform 미설치 + 자격증명 없음) 조건까지는 재현하지 않았다.
- **판정**: 🟧 — 절차는 실증됐고 문서화됐으나, 위 두 지점이 남아 있어 "완전 복구 성공"을
  무조건 ✅ 로 부르지 않는다. 실물 staging 은 리허설 전/후 무중단(200 유지), 실 state 는
  바이트 단위로 무변경임을 확인했다.
