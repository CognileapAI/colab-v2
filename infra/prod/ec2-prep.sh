#!/usr/bin/env bash
# EC2 를 **앱이 뜰 수 있는 상태**로 만든다. 인스턴스를 만든 직후 한 번, 그 위에서 돌린다.
#
# 왜 스크립트로 남기나 —
#   `docs/DEPLOY.md §5-5` 는 「스왑 4 GB · Docker · compose 플러그인(수동) · postgresql16 ·
#   `/opt/colab-v2` · `/etc/colab`(700)」이라고만 적혀 있었다. **명령이 레포 어디에도 없었다.**
#   dev 때 손으로 친 것이 기록되지 않았고, 그래서 prod 를 세울 때 그 절만 보고는 못 세운다 —
#   §5 머리말이 스스로 정한 인수 시험(「이 절만 보고 세울 수 있는가」)을 그 절이 통과하지 못했다.
#
# 버전은 **dev 실물에서 읽어 왔다**(2026-09-06 · `ssh … docker compose version`):
#   compose **2.32.4**(수동 · 고정) · docker·psql·cronie 는 AL2023 저장소 최신
#   ⟹ prod 를 dev 와 같은 자리에 세운다. 지어낸 버전을 쓰지 않는다.
#   prod 실측(2026-09-06) — docker 25.0.16 · compose 2.32.4 · psql 16.15 · cronie 1.5.7
#
# 몇 번을 돌려도 같다(멱등). 이미 된 것은 건너뛰되 **건너뛴다고 말한다** — 조용히 넘어가면
# 「했다고 생각했는데 안 된」 자리가 생긴다.
#
# 쓰기:
#   scp -i <키> infra/prod/ec2-prep.sh ec2-user@<EIP>:/tmp/
#   ssh -i <키> ec2-user@<EIP> 'sudo bash /tmp/ec2-prep.sh'
set -euo pipefail

#: ⚠ **`docker compose` 플러그인은 AL2023 저장소에 없다.** `dnf install docker` 는 엔진만 준다.
#: 릴리스 바이너리를 `/usr/libexec/docker/cli-plugins/` 에 직접 놓는 수밖에 없다.
COMPOSE_VERSION="${COLAB_COMPOSE_VERSION:-v2.32.4}"
SWAP_GB="${COLAB_SWAP_GB:-4}"

[ "$(id -u)" -eq 0 ] || { echo "root 로 돌린다 — sudo bash $0" >&2; exit 1; }

say() { printf '\n── %s\n' "$*"; }
skip() { printf '   · %s — 이미 되어 있다. 건너뛴다\n' "$*"; }

# ── 1. 스왑 ──────────────────────────────────────────────────────────
#: prod 는 `t4g.medium` 4 GB 이고 컨테이너 넷의 상한 합이 3.2 GB 다 — 여유가 600 MB 뿐이라
#: **스왑이 없으면 호스트 전역 OOM 이 한 번에 온다.** dev 도 `/swapfile` 4 GB 를 fstab 에 올려 뒀다.
#: ⚠ dev 에서 실제로 난 OOM 4건은 **호스트가 아니라 컨테이너 상한**이었다(`compose.yml` 의 viz 주석).
#:   스왑은 그쪽을 막아 주지 않는다 — cgroup 상한은 스왑까지 합쳐 센다. 둘은 다른 장치다.
say "스왑 ${SWAP_GB}GB"
if swapon --show | grep -q '/swapfile'; then
  skip "/swapfile"
else
  dd if=/dev/zero of=/swapfile bs=1M count=$((SWAP_GB * 1024)) status=none
  chmod 600 /swapfile
  mkswap /swapfile >/dev/null
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo "   · 만들었다 · fstab 등재 — 재부팅 뒤에도 산다"
fi
swapon --show

# ── 2. 패키지 ────────────────────────────────────────────────────────
#: `postgresql16` 은 **클라이언트**다. 백업(`pg_dump`)과 부트스트랩(`psql`)이 쓴다.
#: ⚠ `pg_dump` 는 서버 버전(16) **이상**이어야 한다 — 낮으면 덤프를 거부한다.
#: `cronie` — AL2023 은 cron 을 기본으로 안 깐다. 없으면 `/etc/cron.d` 등재가
#: 「No such file or directory」로 죽고, **백업이 안 걸린 채 배포가 끝난다.**
say "패키지 — docker · postgresql16 · cronie"
dnf install -y -q docker postgresql16 cronie
systemctl enable --now docker
systemctl enable --now crond
usermod -aG docker ec2-user
#: ⚠ **`docker --version` 을 근거로 쓰지 않는다** — 그건 클라이언트 바이너리에 박힌 문자열이고
#: AL2023 패키지가 그것을 안 올린다. 2026-09-06 실측: rpm `25.0.16` · 서버 `25.0.16` ·
#: `docker --version` **`25.0.14`**. 보고가 실물과 다르면 그 보고는 근거가 못 된다.
echo "   · docker $(rpm -q --qf '%{VERSION}' docker) (서버 $(docker version --format '{{.Server.Version}}' 2>/dev/null || echo '?')) · psql $(psql --version | awk '{print $3}') · cronie ok"

# ── 3. compose 플러그인 (수동) ───────────────────────────────────────
say "docker compose 플러그인 ${COMPOSE_VERSION}"
PLUGIN=/usr/libexec/docker/cli-plugins/docker-compose
if [ -x "$PLUGIN" ] && [ "v$("$PLUGIN" version --short 2>/dev/null)" = "$COMPOSE_VERSION" ]; then
  skip "$COMPOSE_VERSION"
else
  install -d /usr/libexec/docker/cli-plugins
  #: **arm64 다.** x86 바이너리를 놓으면 `exec format error` 가 난다 —
  #: 그 오류는 이미지 아키텍처 문제와 메시지가 같아서 엉뚱한 곳을 뒤지게 된다.
  curl -fsSL -o "$PLUGIN.tmp" \
    "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-aarch64"
  chmod +x "$PLUGIN.tmp"
  mv "$PLUGIN.tmp" "$PLUGIN"
fi
docker compose version --short | sed 's/^/   · compose /'

# ── 4. 자리 ──────────────────────────────────────────────────────────
#: `/etc/colab` 은 **700** 이다. 시크릿 파일 7개가 여기 산다.
#: ⚠ 그 파일들의 소유자는 **uid 10001**(컨테이너 유저)이어야 한다. `root:root` 로 두면
#: 컨테이너가 못 읽어 **「계정이 없다」와 똑같은 401** 이 나온다 — dev 에서 실제로 겪었고
#: 원인을 찾는 데 가장 오래 걸린 자리다. 그 소유권은 시크릿을 놓을 때 준다(여기서는 디렉터리만).
say "자리 — /opt/colab-v2 · /etc/colab(700)"
install -d -m 755 -o root -g root /opt/colab-v2
install -d -m 700 -o root -g root /etc/colab
ls -ld /opt/colab-v2 /etc/colab | sed 's/^/   · /'

# ── 5. 확인 ──────────────────────────────────────────────────────────
say "확인"
fail=0
check() { if eval "$2" >/dev/null 2>&1; then echo "   ✓ $1"; else echo "   ✗ $1"; fail=$((fail+1)); fi; }
check "스왑이 켜져 있다"            "swapon --show | grep -q /swapfile"
check "스왑이 fstab 에 있다"        "grep -q '^/swapfile' /etc/fstab"
check "docker 가 돈다"              "systemctl is-active --quiet docker"
check "crond 가 돈다"               "systemctl is-active --quiet crond"
check "docker compose 가 있다"      "docker compose version"
check "pg_dump 가 16 이상이다"      "[ \"\$(pg_dump --version | awk '{print \$3}' | cut -d. -f1)\" -ge 16 ]"
check "/opt/colab-v2 가 있다"       "[ -d /opt/colab-v2 ]"
check "/etc/colab 이 700 이다"      "[ \"\$(stat -c %a /etc/colab)\" = 700 ]"
#: **IMDSv2 홉 제한 2** — 앱이 컨테이너 안에서 도니 한 번 더 건넌다. `1` 이면 컨테이너에서
#: 자격증명을 못 받아 S3 가 전량 실패한다. ⚠ 이건 **인스턴스 설정**이라 여기서 못 고친다 —
#: 콘솔에서 고치고 다시 돌린다. 조용히 넘어가면 배포 끝에 가서야 드러난다.
if TOK=$(curl -fsS -X PUT http://169.254.169.254/latest/api/token \
          -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' 2>/dev/null) \
   && curl -fsS -H "X-aws-ec2-metadata-token: $TOK" \
        http://169.254.169.254/latest/meta-data/iam/security-credentials/ >/dev/null 2>&1; then
  echo "   ✓ IMDSv2 로 인스턴스 역할이 보인다"
else
  echo "   ✗ IMDSv2 로 인스턴스 역할이 안 보인다 — 프로파일 미연결이거나 홉 제한이 2 가 아니다"
  fail=$((fail+1))
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "ec2-prep: 전부 통과 ─ 0"
else
  echo "::error::ec2-prep: ✗ ${fail}건 — 위 항목을 고치고 다시 돌린다"
  exit 1
fi
