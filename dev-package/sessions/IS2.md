# WU-IS2 — 터널 라우팅을 레포로 끌어온다

> **상태: 선언 완료 · 적용 전.** 이번 세션에서도 Cloudflare 설정·cloudflared 컨테이너 어느 쪽도
> 건드리지 않았다. 확인 시점 `www.colab-hydro.com/healthz` = **200**.
> 남은 것은 `terraform apply` 한 번과 그 검증이며, **Ted 가 API 토큰을 만들어 주기 전까지 진행 불가**다.

---

## 1. 설계 근거 (유지)

### 터널 모드 — 원격 관리형, 실물 확인

- `infra/staging/compose.yml` 의 `cloudflared` 커맨드는 `tunnel --no-autoupdate run` 뿐 —
  `--config` 도, 마운트된 설정 파일도 없다. 인증은 `TUNNEL_TOKEN` 환경변수 하나.
- 커넥터 로그: `Updated to new configuration ... version=6` — 기동 시 **엣지에서 ingress 를 내려받았다**.
  로컬 config.yml 을 읽었다면 이 문구·타이밍이 다르다. `version=6` = 대시보드에서 이미 6번 개정됐고
  그 이력이 레포엔 없다.

확인된 실제 ingress 3건: `www.colab-hydro.com → http://nginx:80` ·
`ssh.colab-hydro.com → ssh://host.docker.internal:2222` · catch-all `http_status:404`.

### 3안 비교 결론 — (b) Terraform 선언, 원격 관리형 유지

| 안 | 전환 중 중단 | 롤백 | 적용 전 diff 증명 |
|---|---|---|---|
| (a) 로컬 관리형 `config.yml` + credentials.json | **컨테이너 재기동 필연** | 부분적 비가역(대시보드가 원격 UI 를 잠금) | 불가 |
| **(b) Terraform** | **없음** (엣지가 흡수·push) | 완전 가역 | **`terraform plan`** |
| (c) 선언 파일 + API 스크립트 | 없음 | 가능하나 state 없음 | 직접 구현해야 함 |

채택 이유를 프로젝트 제약에 직접 묶으면:

1. **staging 은 가역이어야 한다.** (a)만 살아 있는 200 을 끊는다.
2. **비밀은 레포 밖 홈 0600 파일에 남는다.** (b)는 API 토큰 하나면 되고 기존
   `CF_TUNNEL_TOKEN` 관행과 같은 파일에 얹힌다. (a)는 `credentials.json` 이라는 새 종류의 비밀을 늘린다.
3. **완료 조건이 기계로 증명돼야 한다.** `terraform plan` 의 "No changes." 가 곧
   "레포에서 라우팅을 재적용해 동일 상태 재현" 이다. (c)는 같은 걸 손으로 다시 만들어 버그 표면을 만든다.
4. **I1 이 어차피 Terraform 을 들여온다.** IS2 가 그 트리의 첫 조각이 된다.

### ssh 규칙 — 결정 완료

`PLAN-SoT §9-㉜` 으로 **삭제 확정**. 오리진이 존재하지 않는 죽은 규칙이고, 살리는 쪽은
새 노출면을 만드는 범위 확대라 별도 WU 다. 선언에서 빠져 있으므로 apply 시 사라진다 —
**누락이 아니라 이 WU 의 유일한 실제 변경분**이다.

---

## 2. 지금 레포에 들어간 것

`infra/staging/tunnel/` (신규):

| 파일 | 내용 |
|---|---|
| `versions.tf` | `required_version >= 1.6.0`, provider `cloudflare/cloudflare ~> 4.40` 핀, provider 블록 |
| `variables.tf` | `cloudflare_api_token` · `cloudflare_account_id` · `tunnel_id` — 전부 `sensitive`, **default 없음**. 호스트명·오리진만 default 보유 |
| `tunnel.tf` | `cloudflare_zero_trust_tunnel_cloudflared_config.staging` — ingress 2건(www → nginx:80, catch-all 404). ssh 규칙 없음 |
| `terraform.tfvars.example` | placeholder 뿐. 실값은 `TF_VAR_*` 환경변수로 주입 |
| `.gitignore` | `*.tfvars` · `.terraform/` · `*.tfstate*` · `*.tfplan` 차단. `git check-ignore` 로 검증 완료 (example 만 통과) |
| `README.md` | 모드 근거 · 토큰 권한 · import→plan→apply→검증→롤백 전 시퀀스 · 미완 사항 · 완료 오라클 |

`infra/staging/README.md` 를 `tunnel/` 로 연결하도록 갱신했다.
**비밀·계정 ID·터널 ID 는 어느 레포 파일에도 적히지 않았다.** 절대경로도 없다.

`terraform` 은 이 호스트에 **설치돼 있지 않다**(`command -v terraform` → 없음).
따라서 `init`/`validate`/`fmt` 도 실행하지 못했다 — 선언은 아직 파서로 검증되지 않은 상태다.

---

## 3. 남은 것

1. Terraform 설치 (apply 세션에서).
2. `terraform init` → `validate`/`fmt` (여기서 문법·provider 스키마가 처음 검증된다).
3. `terraform import cloudflare_zero_trust_tunnel_cloudflared_config.staging "<account_id>/<tunnel_id>"`.
4. `terraform plan` — **`~ update in-place` 1개, ssh ingress_rule 삭제만** 이어야 한다.
   `destroy`/`replace` 가 보이면 중단(터널 재생성 = `TUNNEL_TOKEN` 무효 = staging 사망).
5. `terraform apply` → `curl` healthz **200** 확인 → `terraform plan` 이 **"No changes."**
6. `03-HANDOFF.md` IS2 행 갱신.

명령 전문과 롤백 (a)~(d) 는 `infra/staging/tunnel/README.md §4`.

---

## 4. 블로킹 선행 조건 — Ted 가 만들어야 할 것

**Cloudflare API 토큰 1개.** 대시보드 → My Profile → API Tokens → Create Token → Custom token.

최소 권한 — 이것 하나면 된다:

| 종류 | 대상 | 권한 |
|---|---|---|
| Account | 터널이 속한 계정 | **Cloudflare Tunnel : Edit** |

Zone 권한 불필요(DNS 는 건드리지 않는다). 화면이 요구하면 `Account Settings : Read` 까지만 추가.

토큰과 함께 **account ID · tunnel ID** 도 필요하다. 셋 다 홈의 기존 0600 파일
`~/.colab-v2-staging.env` 에 줄로 추가한다 — 레포엔 넣지 않는다:

```
CF_API_TOKEN=<값>
CF_ACCOUNT_ID=<값>
CF_TUNNEL_ID=<값>
```

이 셋이 오기 전까지 IS2 는 진행할 수 없다.

---

## 5. 완료 오라클

> 레포에서 라우팅을 재적용해 동일 상태 재현 (`WORK-UNITS.md` IS2 행)

기계적 판정 = **apply 후 `terraform plan` 이 "No changes." 이고, 동시에
`https://www.colab-hydro.com/healthz` 가 200.** 둘 중 하나라도 아니면 닫지 않는다.
