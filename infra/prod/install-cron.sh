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
# ⭑ **⟨증보 2026-09-13⟩ 이 스크립트가 prod 의 크론 **전부**를 건다 — 넷이다.**
#   ① DB 백업 ② 만료 전송 지연 정리 깨우기 ③ 소유권 장부 스냅샷(매시 17분) ④ 운영자 알림 런타임.
#   ③④ 는 종전에 **레포 밖**에 있었다 — ③ 은 세션 문서의 heredoc, ④ 는 `dev|staging` 만 받는
#   설치기. 한 자리에 모으는 이유는 「걸었다고 말해 놓고 안 도는」 자리를 없애기 위해서다.
#   멱등이다(같은 내용이면 다시 써도 같다). **필요한 파일이 없으면 exit 2** — 조용히 건너뛰지 않는다.
#
# 사용: sudo COLAB_ENV=prod COLAB_BACKUP_BUCKET=… \
#            COLAB_OWNERSHIP_COMPOSE_PROJECT=… COLAB_OWNERSHIP_CORE_IMAGE=… COLAB_OWNERSHIP_VIZ_GID=… \
#            COLAB_NOTIFICATION_CONFIG=/etc/colab/operator-runtime.env COLAB_NOTIFICATION_ROOT=/opt/colab-ops/versions/<sha> \
#            /opt/colab-v2/install-cron.sh
set -euo pipefail

# ⚠ **벌 이름을 인자로 받는다** (2026-09-06 · `〈400〉`-㉳-⑴·⑶).
#    종전에는 `colab-dev` 가 파일명에 박혀 있어 prod 에서 같은 파일을 덮어썼고,
#    크론 줄이 `backup.sh` 를 **env 없이** 불러 그 스크립트의 dev 기본값이 이겼다.
#    이제 **크론이 값을 싣고** `backup.sh` 는 값이 없으면 뜨지 않는다(양쪽에서 막는다).
ENVNAME="${COLAB_ENV:?COLAB_ENV 가 필요하다 — dev|prod. 기본값을 두지 않는다}"
BUCKET="${COLAB_BACKUP_BUCKET:?COLAB_BACKUP_BUCKET 가 필요하다 — 그 벌의 데이터 버킷}"
APP=/opt/colab-v2
LOG=/var/log/colab-backup.log
CRON="/etc/cron.d/colab-$ENVNAME"

[ -x "$APP/backup.sh" ] || { echo "$APP/backup.sh 가 없다 — 먼저 올린다" >&2; exit 2; }
[ -r "$APP/reap-token" ] || { echo "$APP/reap-token 이 없다 — 심어 둔 주체 토큰 한 줄(0600)" >&2; exit 2; }

# ── ③ 소유권 장부 스냅샷 · ④ 운영자 알림 — 입력을 **먼저 전부** 검사한다 ──────────────
# 반쯤 걸린 상태로 끝나지 않게 한다. 하나라도 없으면 크론 파일을 한 줄도 쓰지 않고 exit 2 다.
OWNERSHIP_SH="$APP/publish-ownership-hourly.sh"
OWNERSHIP_CRON=/etc/cron.d/colab-ownership-snapshot
OWNERSHIP_LOG="/var/log/colab-v2-$ENVNAME-ownership.log"
OWNERSHIP_URL_FILE="${COLAB_OWNERSHIP_DB_URL_FILE:-/etc/colab/ownership-platform-db.url}"
: "${COLAB_OWNERSHIP_COMPOSE_PROJECT:?COLAB_OWNERSHIP_COMPOSE_PROJECT 가 필요하다 — docker compose ls 로 잰 값}"
: "${COLAB_OWNERSHIP_CORE_IMAGE:?COLAB_OWNERSHIP_CORE_IMAGE 가 필요하다 — colab-v2/core-api:prod-<sha>}"
: "${COLAB_OWNERSHIP_VIZ_GID:?COLAB_OWNERSHIP_VIZ_GID 가 필요하다 — viz 컨테이너의 실제 gid}"
case "$COLAB_OWNERSHIP_VIZ_GID" in ''|*[!0-9]*) echo 'COLAB_OWNERSHIP_VIZ_GID 는 숫자다' >&2; exit 2 ;; esac
[ -x "$OWNERSHIP_SH" ] || { echo "$OWNERSHIP_SH 가 없다 — ship.sh 가 싣는다" >&2; exit 2; }
[ -r "$OWNERSHIP_URL_FILE" ] || { echo "$OWNERSHIP_URL_FILE 이 없다 — colab_backup 롤 접속 문자열(root 0600)" >&2; exit 2; }

# ④ 는 세 상태다(`CLAUDE.md` 게이트 규율과 같은 모양) — 선언되면 건다 · `COLAB_NOTIFICATION_SKIP=1` 로 **명시**
#    면제하면 건수를 드러낸 채 넘어간다 · 아무 말도 없으면 exit 2. 면제가 필요한 실물 = 알림 런타임이 기대는
#    AWS 자원(SQS 큐 2 · Secrets Manager 웹훅 ARN 2 · CloudWatch 알람)이 아직 dev 에만 있는 벌(2026-09-13 prod).
NOTIFY_SKIP="${COLAB_NOTIFICATION_SKIP:-0}"
case "$NOTIFY_SKIP" in 0|1) ;; *) echo 'COLAB_NOTIFICATION_SKIP 은 0 또는 1 이다' >&2; exit 2 ;; esac
NOTIFY_CONFIG="${COLAB_NOTIFICATION_CONFIG:-/etc/colab/operator-runtime.env}"
if [ "$NOTIFY_SKIP" = 0 ]; then
  : "${COLAB_NOTIFICATION_ROOT:?COLAB_NOTIFICATION_ROOT 가 필요하다 — 검증된 ops 소스 번들 루트 /opt/colab-ops/versions/<sha> (면제는 COLAB_NOTIFICATION_SKIP=1 로만)}"
  NOTIFY_INSTALLER="$COLAB_NOTIFICATION_ROOT/infra/notifications/install-runtime-cron.sh"
  [ -r "$NOTIFY_CONFIG" ] || { echo "$NOTIFY_CONFIG 가 없다 — 운영자 런타임 설정(root 0600 · README §4-c)" >&2; exit 2; }
  [ -r "$NOTIFY_INSTALLER" ] || { echo "$NOTIFY_INSTALLER 가 없다 — ops 소스 번들이 반입되지 않았다" >&2; exit 2; }
fi

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

# ① DB 백업 → S3 _ops/backups/$ENVNAME/  (실패하면 종료코드 1 + 로그에 RED)
#    **root 로 돈다** — 소유자 접속 문자열이 uid 10001 소유 0600 이라 ec2-user 로는 못 읽는다.
0 19 * * * root COLAB_BACKUP_BUCKET=$BUCKET COLAB_BACKUP_ENV=$ENVNAME $APP/backup.sh >> $LOG 2>&1

# ② 만료 전송 지연 정리 깨우기 — 읽기 전용 op 하나를 부른다(부작용은 정리뿐)
20 19 * * * ec2-user curl -sS -o /dev/null -w '%{time_total}s %{http_code}\\n' -H "Authorization: Bearer \$(cat $APP/reap-token)" http://127.0.0.1:8000/api/v1/uploads/transfers/incomplete >> $LOG 2>&1
EOF
chmod 0644 "$CRON"

# ── ③ 소유권 장부 스냅샷 — 매시 17분 ────────────────────────────────────────────
# 왜 17분인가 — 정각을 피한다(백업·정리·다른 호스트의 크론이 정각에 몰린다). dev 와 같은 값이다.
# 값은 **크론이 싣는다** — 래퍼가 기본값을 갖지 않으므로(`publish-ownership-hourly.sh` 의 `:?`)
# 여기서 빠뜨리면 매시 exit 78 로 죽고 로그에 남는다. 조용히 옛 스냅샷이 남지 않는다.
install -m 0644 /dev/null "$OWNERSHIP_LOG" 2>/dev/null || true
cat > "$OWNERSHIP_CRON" <<EOF
# colab-v2 $ENVNAME 소유권 장부 스냅샷 — 시각은 UTC. viz 는 이 파일을 읽기만 한다.
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

17 * * * * root COLAB_OWNERSHIP_COMPOSE_PROJECT=$COLAB_OWNERSHIP_COMPOSE_PROJECT COLAB_OWNERSHIP_CORE_IMAGE=$COLAB_OWNERSHIP_CORE_IMAGE COLAB_OWNERSHIP_DB_URL_FILE=$OWNERSHIP_URL_FILE COLAB_OWNERSHIP_VIZ_GID=$COLAB_OWNERSHIP_VIZ_GID $OWNERSHIP_SH >> $OWNERSHIP_LOG 2>&1
EOF
chmod 0644 "$OWNERSHIP_CRON"

# ── ④ 운영자 알림 런타임 — 설치기 자신이 멱등이고 드리프트를 거절한다 ──────────────
# ⛔ 여기서 cron 줄을 손으로 쓰지 않는다. 일정 정본은 `install-runtime-cron.sh` 안의 `expected()` 이고,
#    그것이 `verify` 로 자기 출력과 설치본을 대조한다 — 두 벌을 두면 대조가 무의미해진다.
if [ "$NOTIFY_SKIP" = 0 ]; then
  bash "$NOTIFY_INSTALLER" --environment "$ENVNAME" --config "$NOTIFY_CONFIG" install
else
  echo "④ 운영자 알림 cron: 명시 면제(COLAB_NOTIFICATION_SKIP=1) — 걸지 않은 잡 1종(export·spool·retry·probe). 면제 근거를 배포 기록에 적는다"
fi

echo "등록했다: $CRON"
sed 's/^/   /' "$CRON"
echo "등록했다: $OWNERSHIP_CRON"
sed 's/^/   /' "$OWNERSHIP_CRON"
echo
echo "로그: $LOG · $OWNERSHIP_LOG   (cron 은 UTC — 한국 시각은 +9)"
[ "$NOTIFY_SKIP" = 1 ] || echo "운영자 알림 cron: /etc/cron.d/colab-operator-notifications (install-runtime-cron.sh 가 관리)"
