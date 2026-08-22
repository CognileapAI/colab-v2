# 값은 이 레포에 두지 않는다. 홈 디렉터리 0600 파일에서 환경변수로 주입한다.
# (CLAUDE.md §3 — 비밀은 레포 밖, infra/staging/README.md 의 .colab-v2-staging.env 관행과 동형)

variable "cloudflare_api_token" {
  description = "Cloudflare API 토큰. Account > Cloudflare Tunnel:Edit 권한만 있으면 된다."
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "터널이 속한 Cloudflare 계정 ID."
  type        = string
  sensitive   = true
}

variable "tunnel_id" {
  description = "staging 터널의 ID. 기존 터널을 참조만 한다 — 새로 만들지 않는다."
  type        = string
  sensitive   = true
}

variable "origin_hostname" {
  description = "터널이 공개하는 호스트명."
  type        = string
  default     = "www.colab-hydro.com"
}

variable "origin_service" {
  description = "오리진 주소. compose 의 서비스 이름 nginx 에 고정돼 있다."
  type        = string
  default     = "http://nginx:80"
}
