# staging 터널의 ingress 정본.
#
# 터널은 원격 관리형(remotely-managed)이다. 커넥터는 TUNNEL_TOKEN 하나로만 인증하고
# ingress 는 Cloudflare 엣지에서 내려받는다. 로컬 config.yml 은 없고, 만들지도 않는다.
# 이 파일은 그 "엣지 쪽 정본"을 레포에서 밀어 넣기 위한 선언이다.
#
# 여기 선언되지 않은 규칙은 apply 시 사라진다.
# ssh.colab-hydro.com 규칙이 없는 것은 누락이 아니라 결정이다 — PLAN-SoT §9-㉜ (삭제 확정).

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "staging" {
  account_id = var.cloudflare_account_id
  tunnel_id  = var.tunnel_id

  config {
    ingress_rule {
      hostname = var.origin_hostname
      service  = var.origin_service
    }

    # catch-all — 마지막 규칙은 hostname 없이 와야 한다 (Cloudflare 요구사항).
    ingress_rule {
      service = "http_status:404"
    }
  }
}
