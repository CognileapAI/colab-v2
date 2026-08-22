# infra/staging/tunnel — 터널 ingress 의 레포 측 정본 (WU-IS2)

## 1. 지금 터널은 어떤 모드인가

**원격 관리형(remotely-managed)** 이다. 실물 근거 두 가지:

- `../compose.yml` 의 `cloudflared` 커맨드는 `tunnel --no-autoupdate run` 뿐이다.
  `--config` 플래그도, 마운트된 설정 파일도 없다. 인증은 `TUNNEL_TOKEN` 환경변수 하나다.
- 커넥터 로그에 `Updated to new configuration ... version=6` 이 찍힌다 —
  기동 시점에 **Cloudflare 엣지에서 ingress 를 내려받았다**는 뜻이다.

즉 ingress 의 정본은 지금 Cloudflare 쪽에 있고, 레포엔 재현본이 없다. IS2 는 그 상태를 끝낸다.

## 2. 왜 로컬 `config.yml` 이 아니라 Terraform 인가

로컬 관리형으로 전환하려면 `credentials.json`(새 종류의 비밀)을 새로 받아야 하고,
`TUNNEL_TOKEN` 인증에서 `credentials-file` 인증으로 갈아타는 **컨테이너 재기동 1회가 필연**이다.
지금 살아 있는 200 을 끊는 유일한 선택지다. 게다가 대시보드가 터널을 로컬 관리형으로 잠그는
동작이 있어 원복이 항상 즉시 보장되지 않는다 — **부분적으로 비가역**.

Terraform 은 원격 관리형 구조를 그대로 두고 **대시보드와 같은 API 로 같은 값을 밀어 넣을 뿐**이다.

- 커넥터 재시작이 없다 (엣지가 새 설정을 흡수하고 push 한다).
- `terraform plan` 이 "레포 선언 == 실제 상태"를 **적용 전에** 기계적으로 증명한다.
  이게 IS2 의 완료 오라클과 정확히 같은 문장이다.
- 완전 가역 — 되돌리는 것도 apply 한 번.
- I1(토폴로지 IaC)이 어차피 Terraform 을 들여온다. 이 디렉터리가 그 트리의 첫 조각이다.

## 0. 상태 — 적용 완료 (2026-08-23)

`terraform plan` = **`No changes.`** 레포 선언이 실제 상태와 일치한다. **대시보드가 정본이 아니라 레포가 정본이고 대시보드가 그 산출이다.**

현재 ingress 는 둘뿐이다 — `www.colab-hydro.com → http://nginx:80` · catch-all `http_status:404`.

### `ssh.colab-hydro.com` 은 세 겹이었다

블로커 #7 을 "ingress 규칙 하나"로 진단했는데 얕았다. 지운 뒤에 나머지가 드러났다.

| 층 | 무엇이었나 | 어떻게 지웠나 |
|---|---|---|
| 라우팅 | 터널 ingress 규칙 | 선언에서 빼고 `apply` — 커넥터가 `version=7` 로 수신 |
| **인증** | Zero Trust **Access 애플리케이션** | ingress 를 지운 뒤 404 가 아니라 **302 Access 로그인**이 떴다. 아무 데도 안 가는 문에 자물쇠만 남은 상태 |
| **이름** | **DNS CNAME** (`ssh` → `<tunnel>.cfargotunnel.com`, proxied) | 이것 때문에 요청이 Cloudflare 까지 도달했다 |

**엣지에 만든 것은 라우팅·인증·이름 세 층에 흩어진다.** 하나만 지우고 끝났다고 보면 안 된다.

뒤의 둘은 API 로 바로 지우지 않았다. **임시 선언 → `import` → `plan` 확인(`0 add, 0 change, 2 destroy`) → `-target` destroy** 순서로 갔다. 무엇이 지워지는지 사람이 먼저 읽는 절차를 건너뛰지 않는다. 끝나고 임시 선언 파일은 지웠다 — 없는 것을 계속 선언해 둘 이유가 없다.

### 알려진 한계 — state 가 이 호스트에만 있다

`terraform.tfstate` 는 레포에 넣지 않는다(비밀이 들어간다). 지금은 **WSL 호스트 로컬에만** 있고, 호스트가 사라지면 `import` 로 다시 만들어야 한다. → **WU-IS4**.

terraform 은 `~/.local/bin` 에 사용자 수준으로 설치돼 있다(sudo·apt 저장소 불필요). 지우려면 그 파일 하나만 지우면 된다.

---

## 3. 선행 조건 — API 토큰

> 2026-08-23 발급 완료. 아래는 재발급·타 환경 구성용 기록이다.

Cloudflare 대시보드 → My Profile → API Tokens → Create Token → **Custom token**.

**최소 권한 — 아래 하나면 된다. 더 주지 않는다.**

| 종류 | 대상 | 권한 |
|---|---|---|
| Account | 이 터널이 속한 계정 | **Cloudflare Tunnel : Edit** |

Zone 권한은 필요 없다 (DNS 레코드는 이미 있고 건드리지 않는다).
Account Settings:Read 를 요구하는 화면이 나오면 그것까지만 추가한다.

만든 토큰과 ID 들은 **레포에 넣지 않는다.** 홈 디렉터리의 기존 파일에 줄을 덧붙인다
(권한 `0600` — `infra/staging/README.md` 의 `CF_TUNNEL_TOKEN` 과 같은 파일, 같은 관행):

```
CF_API_TOKEN=<값>
CF_ACCOUNT_ID=<값>
CF_TUNNEL_ID=<값>
```

`CF_ACCOUNT_ID` 와 `CF_TUNNEL_ID` 는 대시보드 Zero Trust → Networks → Tunnels 에서,
또는 읽기 전용인 `cloudflared tunnel info` 로 확인한다.

Terraform 이 이 호스트에 아직 설치돼 있지 않다 (`command -v terraform` → 없음).
apply 세션에서 먼저 설치해야 한다.

## 4. 순서 — import → plan → apply → 검증 → 롤백

```bash
# 0. 자격증명 주입 — 레포 밖 홈 0600 파일에서만 읽는다. 값을 셸 히스토리에 남기지 않는다.
set -a; . ~/.colab-v2-staging.env; set +a
export TF_VAR_cloudflare_api_token="$CF_API_TOKEN"
export TF_VAR_cloudflare_account_id="$CF_ACCOUNT_ID"
export TF_VAR_tunnel_id="$CF_TUNNEL_ID"

# (이 디렉터리에서 실행한다)
terraform init

# 1. import — 기존 터널 config 를 state 로 편입한다. 신규 생성이 아니다. 최초 1회.
terraform import cloudflare_zero_trust_tunnel_cloudflared_config.staging \
  "$CF_ACCOUNT_ID/$CF_TUNNEL_ID"

# 2. plan — 사람이 눈으로 읽고 승인하기 전엔 다음 단계로 넘어가지 않는다.
terraform plan
```

**plan 이 보여야 하는 것 — 이것과 다르면 멈추고 보고한다.**

- `~ update in-place` 리소스 **1개**, 그 안에서 `ssh.colab-hydro.com` ingress_rule 이 **사라지는 것**.
- `www.colab-hydro.com → http://nginx:80` 은 **변화 없음**.
- catch-all `http_status:404` 는 **변화 없음**(마지막 규칙 자리 유지).
- `destroy` 또는 `replace` 가 하나라도 보이면 **중단**. 터널 자체를 다시 만들려는 것이고,
  그러면 `TUNNEL_TOKEN` 이 무효가 되어 staging 이 죽는다.

```bash
# 3. apply — 위 조건을 만족한 plan 에 대해서만.
terraform apply

# 4. 검증 — 적용 직후 즉시.
curl -sS -o /dev/null -w '%{http_code}\n' -I https://www.colab-hydro.com/healthz   # 200 기대
curl -sS -o /dev/null -w '%{http_code}\n' -I https://ssh.colab-hydro.com/          # 404 기대 (규칙 삭제됨)

# 5. drift 재확인 — 완료 오라클. "레포 선언 == 실제 상태" 가 여기서 증명된다.
terraform plan    # "No changes." 여야 한다.
```

### 롤백 — 구체적으로

증상별로 다르다. 셋 중 하나를 고른다.

**(a) 200 이 깨졌다 — ingress 값이 틀렸다.** ssh 규칙을 되살릴 필요는 없다.
`tunnel.tf` 를 직전 커밋 상태로 되돌리고 다시 apply 한다. 커넥터 재시작 없이 엣지가 흡수한다.

```bash
git checkout HEAD~1 -- tunnel.tf
terraform apply
curl -sS -o /dev/null -w '%{http_code}\n' -I https://www.colab-hydro.com/healthz
```

**(b) 어쨌든 즉시 원상복구가 필요하다 — Terraform 을 거치지 않는 경로.**
대시보드 Zero Trust → Networks → Tunnels → 해당 터널 → Public Hostnames 에서
`www.colab-hydro.com → HTTP → nginx:80` 을 직접 확인·복원한다. 이건 항상 살아 있는 손잡이다.
복원 후 `terraform plan` 을 돌려 drift 를 확인하고, `terraform apply -refresh-only` 로 state 에 흡수한다.

**(c) 오리진 자체가 죽었다 (터널 설정 문제가 아니다).** 이건 IS1 의 롤백이다 —
`infra/staging/README.md` 의 `docker compose ... up -d` / `down` 한 쌍.

**(d) ssh 규칙이 다시 필요해졌다.** 되살리지 않는다. `PLAN-SoT §9-㉜` 이 삭제로 확정했고,
오리진을 새로 붙이는 것은 **범위 확대**라 별도 WU 다.

## 5. 아직 하지 않은 것 (2026-08-22 기준)

- **`terraform apply` 를 한 번도 실행하지 않았다.** `init`·`import`·`plan` 도 실행하지 않았다 —
  이 호스트에 Terraform 이 설치돼 있지 않고, API 토큰도 아직 없다.
- 따라서 Cloudflare 설정은 **지금 이 순간 아무것도 변경되지 않았다.**
  ssh 규칙은 여전히 엣지에 살아 있다. `www.colab-hydro.com/healthz` 는 계속 200 이다.
- 이 디렉터리는 **선언만 있는 상태**다. state 파일이 없고, 따라서 레포는 아직
  "지금 뭐가 적용된 상태인지"를 스스로 증명하지 못한다.

## 6. IS2 완료 오라클

> **레포에서 라우팅을 재적용해 동일 상태 재현** (`dev-package/WORK-UNITS.md` IS2 행)

기계적으로는 이것이다 — **apply 이후 `terraform plan` 이 "No changes." 를 내고,
동시에 `https://www.colab-hydro.com/healthz` 가 200 일 것.**
둘 중 하나라도 아니면 IS2 는 닫히지 않는다.
