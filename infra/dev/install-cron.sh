#!/usr/bin/env bash
# EC2 cron 등록 — 백업(하루 1회) + 지연 정리 깨우기(하루 1회). 배포 계획서 §10-1·§10-3.
#
# **시각은 UTC 다**(cron 이 UTC 로 돈다). 19:00 UTC = 한국 04:00 —
# RDS 자동 백업 창(18:00~18:30 UTC)이 끝난 뒤, 유지 관리 창(화 19:30 UTC) 앞이다. 셋이 겹치지 않는다.
#
# **정리 잡이 왜 「깨우기」인가.** 이 레포의 만료 전송 정리는 **별도 잡이 아니라 지연 정리**다
# (`routes/upload_transfers.py::_reap_expired` — 원장이 아는 것만 지운다 · 버킷 스캔 금지).
# 그래서 등록할 크론 잡이 없다. 다만 **업로드가 한동안 없으면 그 정리가 아예 안 돈다** —
# 읽기 전용 op(`listIncompleteUploadTransfers`)를 하루 한 번 불러 그 자리를 지나가게 한다.
# 멀티파트 조각은 라이프사이클 `abort-incomplete-multipart-7d` 가 최후 백스톱이지만,
# **단일 PUT 으로 올라간 채 버려진 객체는 이 경로로만 치워진다**(전역 만료 규칙을 안 걸었으므로).
#
# 사용: sudo /opt/colab-v2/install-cron.sh
set -euo pipefail

APP=/opt/colab-v2
LOG=/var/log/colab-backup.log
CRON=/etc/cron.d/colab-dev

[ -x "$APP/backup.sh" ] || { echo "$APP/backup.sh 가 없다 — 먼저 올린다" >&2; exit 2; }
[ -r "$APP/reap-token" ] || { echo "$APP/reap-token 이 없다 — 심어 둔 주체 토큰 한 줄(0600)" >&2; exit 2; }

# ⚠ **Amazon Linux 2023 은 cron 을 기본으로 깔지 않는다** — `/etc/cron.d` 도 `crond` 도 없다
#    (2026-08-31 실측: 스크립트가 「No such file or directory」로 죽었다).
#    잡을 거는 스크립트가 제 발판을 스스로 챙긴다 — 안 그러면 「등록했다」고 말해 놓고 아무것도 안 돈다.
if [ ! -d /etc/cron.d ] || ! systemctl list-unit-files crond.service >/dev/null 2>&1; then
  echo "cronie 가 없다 — 설치한다"
  dnf install -y -q cronie >/dev/null
fi
systemctl enable --now crond

install -m 0644 /dev/null "$LOG" 2>/dev/null || true
chown ec2-user:ec2-user "$LOG"

cat > "$CRON" <<EOF
# colab-v2 dev — 시각은 UTC. 19:00 UTC = 한국 04:00 (배포 계획서 §10)
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

# ① DB 백업 → S3 _ops/backups/dev/  (실패하면 종료코드 1 + 로그에 RED)
#    **root 로 돈다** — 소유자 접속 문자열이 uid 10001 소유 0600 이라 ec2-user 로는 못 읽는다.
0 19 * * * root $APP/backup.sh >> $LOG 2>&1

# ② 만료 전송 지연 정리 깨우기 — 읽기 전용 op 하나를 부른다(부작용은 정리뿐)
20 19 * * * ec2-user curl -sS -o /dev/null -w '%{time_total}s %{http_code}\\n' -H "Authorization: Bearer \$(cat $APP/reap-token)" http://127.0.0.1:8000/api/v1/uploads/transfers/incomplete >> $LOG 2>&1
EOF
chmod 0644 "$CRON"

echo "등록했다: $CRON"
sed 's/^/   /' "$CRON"
echo
echo "로그: $LOG   (cron 은 UTC — 한국 시각은 +9)"
