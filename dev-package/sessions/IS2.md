# WU-IS2 — 터널 라우팅을 레포로 끌어온다 (조사 + 제안, 미착수)

> **이 문서는 조사·제안이다. 실행은 하지 않았다.** Cloudflare 설정·cloudflared 컨테이너 어느 쪽도
> 건드리지 않았고, 확인 시점 `www.colab-hydro.com/healthz` 는 계속 200이었다.

---

## 1. 터널 모드 — 원격 관리형(remotely-managed), 실물로 재확인

증거:

- `infra/staging/compose.yml` — `cloudflared` 서비스의 커맨드는 `["tunnel", "--no-autoupdate", "run"]`뿐이다.
  로컬 `config.yml`도, `--config` 플래그도 없다. 인증은 `TUNNEL_TOKEN` 환경변수(토큰) 하나로만 이뤄진다.
- 로컬 ingress 파일이 컨테이너·레포 어디에도 없다. 볼륨 마운트도 `nginx.conf`·`html/`뿐 — cloudflared 쪽 설정 마운트가 없다.
- `docker logs colab_v2_staging_cloudflared`(읽기 전용 확인)에 다음 라인이 그대로 찍힌다.

  ```
  INF Updated to new configuration config="{\"ingress\":[
    {\"hostname\":\"www.colab-hydro.com\", \"service\":\"http://nginx:80\"},
    {\"hostname\":\"ssh.colab-hydro.com\", \"originRequest\":{}, \"service\":\"ssh://host.docker.internal:2222\"},
    {\"service\":\"http_status:404\"}
  ], \"warp-routing\":{\"enabled\":false}}" version=6
  ```

  `"Updated to new configuration"`은 **커넥터가 기동 시점에 Cloudflare 엣지에서 ingress를 내려받았다**는
  뜻이다(로컬 config.yml을 읽었다면 이 로그 문구·타이밍이 다르다 — remotely-managed 특유의 push 알림이다).
  `version=6` — 대시보드에서 이미 6번 개정된 설정이라는 뜻이고, 이 개정 이력 자체가 레포엔 없다.

결론: **remotely-managed(토큰 기반, ingress는 Cloudflare 쪽 정본)**. IS1 기록과 일치, 실물로 재확인 완료.

---

## 2. 소스 오브 트루스 옵션 3안 비교

### (a) 로컬 관리형(`config.yml` + credentials json)으로 전환

- **필요 자격증명**: 터널별 `credentials.json`(터널 ID의 개인키, 대시보드에서 재발급하거나
  `cloudflared tunnel token` → 자격 파일 변환 절차 필요). 지금 손에 있는 건 **연결 토큰뿐**이고
  credentials.json이 아니다 — 이것부터 새로 받아야 한다.
- **전환 중 깨지는 것**: 커맨드를 `tunnel --config /etc/cloudflared/config.yml run <이름|ID>`로 바꿔야 한다.
  `TUNNEL_TOKEN` 인증에서 `credentials-file` 인증으로 갈아타는 순간이 있어, **컨테이너 재기동 1회가 필연**이다
  (compose 특성상 완전 무중단 스위치가 안 된다 — 짧은 창이지만 롤백 전까지 530 위험 구간이 생긴다).
- **롤백**: 이전 compose(`TUNNEL_TOKEN` 방식)로 되돌리면 된다. 다만 대시보드가 "이 터널은 이제
  로컬 관리형"으로 인지할 수 있어(전환 시 대시보드가 원격 설정 UI를 잠그는 동작이 있음),
  완전한 원복이 항상 즉시 보장되진 않는다 — **부분적으로 비가역**.
- **무중단 검증**: 안 된다. 커넥터를 실제로 내렸다 올려야 확인된다.
- **레포 반영물**: `config.yml`(호스트명 → 서비스 매핑, 레포에 커밋 가능 — 비밀 없음) +
  `credentials.json`(비밀, 홈 `0600`에만).

### (b) 원격 관리형 유지 + Terraform `cloudflare_zero_trust_tunnel_cloudflared_config`로 ingress를 선언

- **필요 자격증명**: Cloudflare **API 토큰**(Zone:Read 불필요, Account: `Cloudflare Tunnel:Edit` 권한).
  터널 자체를 새로 만들지 않고 기존 터널 ID를 `data` 소스로 참조하거나 `import`로 편입.
- **전환 중 깨지는 것**: 이론상 없음 — Terraform이 대시보드와 **같은 API**로 같은 값을 밀어 넣을 뿐이다.
  `terraform plan`으로 현재 상태(www→nginx:80, ssh→host.docker.internal:2222, catch-all 404)와
  선언값이 일치하는지 **적용 전에 diff 없음을 먼저 확인**할 수 있다 — 이게 이 옵션의 핵심 강점.
- **롤백**: `terraform apply`로 이전 state 재적용, 또는 대시보드에서 수동으로 되돌려도 다음 `plan`이
  drift로 잡아준다. **완전 가역**.
- **무중단 검증**: 가능 — `plan`이 diff-only이므로 적용 전 안전 확인이 되고, 적용 자체도
  Cloudflare 엣지가 새 설정을 흡수하는 것이라 커넥터 재시작이 필요 없다(원격 관리형의 존재 이유).
- **레포 반영물**: `.tf` 파일(ingress 규칙 평문 — 비밀 없음) + API 토큰은 홈 `0600` env로 주입
  (`TF_VAR_cloudflare_api_token` 또는 `CLOUDFLARE_API_TOKEN`).
- **추가로 필요한 것**: 이 레포에 Terraform 자체가 없다(`find . -iname "*.tf"` 결과 0건).
  I1(토폴로지 IaC)이 어차피 Terraform을 들여올 예정이므로, IS2가 **그 Terraform 트리의 첫 조각**이
  될 수 있다 — 나쁘지 않은 선례.

### (c) 체크인된 선언 파일 + API 스크립트로 직접 적용

- **필요 자격증명**: (b)와 동일한 API 토큰. 다만 `plan`/`state` 개념이 없어 **적용 전 diff를
  스크립트가 직접 구현**해야 한다(현재 원격 설정을 GET → 로컬 파일과 비교 → 다르면 PUT).
- **전환 중 깨지는 것**: 없음(원격 관리형 그대로, API 호출 방식도 (b)와 동일 엔드포인트).
- **롤백**: 스크립트가 이전 JSON을 다시 PUT — 되지만, **state 파일이 없어 "지금 뭐가 적용된 상태인지"를
  레포가 스스로 증명 못 한다.** drift 감지도 매번 GET을 짜야 한다 — (b)가 공짜로 주는 것을 직접 구현.
- **무중단 검증**: 가능(GET 비교는 읽기 전용).
- **레포 반영물**: JSON/YAML 선언 파일 + `curl`/Python 스크립트.

---

## 3. 권장 — (b) Terraform 선언, 원격 관리형 유지

이유를 이 프로젝트 제약에 직접 묶는다.

1. **staging은 가역이어야 한다**(`CLAUDE.md`, `DEPLOY-CURRENT.md §10` "롤백이 되돌리기 한 번"). (a)는
   전환 자체가 컨테이너 재기동을 요구해 지금 살아 있는 200을 건드리는 유일한 옵션이다. (b)·(c)는
   **전환이라 부를 게 없다** — 기존 원격 관리형 구조를 그대로 두고 그 값만 레포에서 밀어 넣는다.
2. **비밀은 레포 밖 홈 0600 파일에 남는다**(`CLAUDE.md §3` 규칙 6·`infra/staging/README.md` 관행과 동형).
   (b)는 API 토큰 하나만 그 방식으로 넣으면 되고, 지금 쓰는 `CF_TUNNEL_TOKEN` 관행과 자연스럽게 병행된다.
   (a)는 `credentials.json`이라는 **새로운 종류의 비밀**을 추가로 관리해야 한다.
3. **게이트가 검증 가능해야 한다**(`CLAUDE.md §4`). (b)는 `terraform plan`이 "레포 선언 == 실제 상태"를
   기계적으로 증명한다 — 이게 정확히 이 WU의 완료 조건("레포에서 라우팅을 재적용해 동일 상태 재현")과
   맞아떨어진다. (c)는 같은 것을 손으로 다시 만들어야 해서 자체 버그 표면이 생긴다.
4. **I1이 어차피 Terraform을 들여온다.** IS2를 (b)로 하면 그 트리의 첫 리소스가 되어 나중에 새로 붙이는
   비용이 없다. (a)·(c)는 I1과 무관한 일회성 산출물이 된다.

무중단 검증(위험 없이 지금 바로 할 수 있는 것): `terraform plan`을 만들어 **적용하지 않고 diff만 확인** —
이 자체로 "레포 선언이 실제와 일치"를 증명할 수 있어, 이번 세션에서도 안전하게 시작할 수 있다.

---

## 4. 초안 산출물 — 다음 세션에서 `infra/staging/`(또는 `infra/cloudflare/`)에 배치할 것

**주의**: 아래는 초안이다. 실제 배치 전 대시보드의 정확한 `account_id`·터널 ID·zone ID를
`cloudflared tunnel info`(읽기 전용) 또는 대시보드에서 재확인해야 한다. 여기 값은 placeholder다.

```hcl
# infra/cloudflare/tunnel.tf (초안 — 아직 미배치)
#
# 원격 관리형 터널을 그대로 두고, ingress 규칙만 Terraform이 선언한다.
# 터널 자체(TUNNEL_TOKEN 발급)는 대시보드에서 이미 만들어진 것을 참조만 한다 — 재생성 아님.

terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
  # 값은 TF_VAR_cloudflare_api_token 환경변수로 주입한다. 레포에 값 없음.
}

variable "cloudflare_account_id" {
  type = string
  # placeholder — 대시보드에서 재확인 후 채운다.
  default = "<ACCOUNT_ID_PLACEHOLDER>"
}

variable "tunnel_id" {
  type = string
  # 커넥터 로그에서 확인된 실제 터널 ID.
  default = "39e9977b-875b-4cb4-8f42-a01c9e6f3cfc"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# 기존 터널을 새로 만들지 않고 참조만 한다.
data "cloudflare_zero_trust_tunnel_cloudflared" "staging" {
  account_id = var.cloudflare_account_id
  tunnel_id  = var.tunnel_id
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "staging" {
  account_id = var.cloudflare_account_id
  tunnel_id  = data.cloudflare_zero_trust_tunnel_cloudflared.staging.id

  config {
    ingress_rule {
      hostname = "www.colab-hydro.com"
      service  = "http://nginx:80"
    }

    # 블로커 #7 — ssh 규칙 존속 여부는 §5 결정 후 아래 블록 유지/삭제로 반영한다.
    # ingress_rule {
    #   hostname = "ssh.colab-hydro.com"
    #   service  = "ssh://host.docker.internal:2222"
    # }

    ingress_rule {
      service = "http_status:404"
    }
  }
}
```

### 적용 · 검증 · 롤백 명령 시퀀스 (다음 세션 실행용, 이번 세션엔 미실행)

```bash
# 0. 자격증명 — 레포 밖 홈 0600 파일에서만 로드
export TF_VAR_cloudflare_api_token=$(cat ~/.colab-v2-staging.env | grep CF_API_TOKEN | cut -d= -f2)

cd infra/cloudflare

# 1. 초기화
terraform init

# 2. import — 기존 터널 config를 state로 편입 (신규 생성 아님, 필수 1회)
terraform import cloudflare_zero_trust_tunnel_cloudflared_config.staging \
  "${TF_VAR_cloudflare_account_id}/${TF_VAR_tunnel_id}"

# 3. plan — 여기서 diff가 "no changes"면 레포 선언 == 실제 상태가 이미 증명된 것
terraform plan

# 4. apply — plan과 다른 경우에만, 사람이 diff를 읽고 승인 후
terraform apply

# 5. 검증 — staging은 절대 안 건드림, 헬스체크만
curl -s -o /dev/null -w '%{http_code}\n' https://www.colab-hydro.com/healthz   # 200 기대

# 6. 롤백 — 이전 state로 되돌리거나, 대시보드에서 직접 되돌린 뒤 plan으로 drift 없음 재확인
terraform apply -refresh-only   # 대시보드 수동 변경을 state에 흡수
# 또는
git checkout <이전 커밋> -- infra/cloudflare/tunnel.tf && terraform apply
```

---

## 5. 블로커 #7 — `ssh.colab-hydro.com` 규칙, Ted 결정 필요

커넥터 로그가 실물로 재확인해 준 사실: 이 규칙은 **오리진 없이 살아 있다**
(`"service":"ssh://host.docker.internal:2222"` — 2222 포트에 응답하는 것이 컨테이너·호스트 어디에도 없다).
IaC로 선언하는 순간 이 규칙을 **명시적으로 포함할지 뺄지 결정해야 한다** — "일단 놔둔다"는
IaC 선언에서는 존재할 수 없다(선언 안 하면 곧 삭제 의미가 된다).

| 선택 | 결과 | 대가 |
|---|---|---|
| **A. 규칙 삭제** | ingress에서 ssh 호스트명 제거. IaC 선언이 실제 필요와 일치. `ssh.colab-hydro.com`은 이후 404 catch-all로 떨어짐 | PoC 시절 SSH 관리 접근 경로가 완전히 사라진다. 되살리려면 새 오리진(2222 리스너)부터 다시 세워야 함 |
| **B. 규칙 유지 + staging 관리용 오리진을 실제로 붙인다** | `ssh.colab-hydro.com`이 다시 유효해짐 — WSL 호스트 SSH 접근용으로 쓸 수 있다 | 새로운 공개 노출면 하나가 늘어난다. `infra/staging/`에 sshd 컨테이너나 host 포트 2222 개방이 필요하고, 인증·방화벽 정책을 이 WU 범위에서 새로 정해야 함 — **범위 확대**(`CLAUDE.md §5` "범위 늘리기 금지"에 걸릴 수 있어 별도 WU로 쪼개는 편이 안전) |

**본 문서의 잠정 제안**: A(삭제)를 기본값으로 하되, 최종 결정은 Ted에게 넘긴다.
근거 — 오리진 없는 ingress 규칙은 이미 죽은 기능이고, B를 택하면 IS2 범위를 넘는 새 작업(별도 WU)이
필요해 이번 WU를 부분 완료로 닫게 된다(`CLAUDE.md §5` 금지 사항과 충돌).
