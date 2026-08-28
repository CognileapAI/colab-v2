#!/usr/bin/env bash
# 판정기 fail-closed 증명 — **red fixture 로 판정기가 실제로 red 를 내는지 시험한다.**
#
# `IS3 §11` 방식 그대로 — **하나라도 green 이면 selftest 실패다.**
# 「전부 green」이 「전부 무력」과 구분되지 않는 상태를 만들지 않는다.
#
# 호스트 포트를 공개하지 않는다 — 픽스처 서버는 `127.0.0.1` 에만 붙는다(`I3 §5-6`·`§5-10`).
# 운영 스택을 건드리지 않는다 — HTTP 는 픽스처 서버, `docker` 는 PATH 껍데기로 갈아 끼운다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"; [ -n "${SRV:-}" ] && kill "$SRV" 2>/dev/null' EXIT
FAILED=0; N=0

want_red()   { N=$((N+1)); if "$@" >"$TMP/out" 2>&1; then echo "  FAIL  [$LABEL] green 이 나왔다 — 판정기가 무력하다"; sed 's/^/        /' "$TMP/out"; FAILED=$((FAILED+1)); else echo "  PASS  [$LABEL] red"; fi; }
want_green() { N=$((N+1)); if "$@" >"$TMP/out" 2>&1; then echo "  PASS  [$LABEL] green"; else echo "  FAIL  [$LABEL] red 가 나왔다 — 양성 대조군이 서지 않는다"; sed 's/^/        /' "$TMP/out"; FAILED=$((FAILED+1)); fi; }
grep_out()   { N=$((N+1)); if grep -qF "$2" "$TMP/out"; then echo "  PASS  [$1] 요약줄에 「$2」"; else echo "  FAIL  [$1] 요약줄이 「$2」를 말하지 않는다"; sed 's/^/        /' "$TMP/out"; FAILED=$((FAILED+1)); fi; }

# ── 픽스처 HTTP 서버 ────────────────────────────────────────────────────────
# MODE 로 세 얼굴을 만든다: green · dead(단위 하나가 503) · placeholder(전 경로 200 "ok").
start_srv() { # $1=MODE
  MODE="$1" python3 - "$TMP/port" <<'PY' &
import http.server, json, os, socketserver, sys
MODE = os.environ["MODE"]
UNITS = {"core-api", "pipeline-worker", "viz-render", "ai-service", "frontend"}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        p = self.path
        if MODE == "placeholder":
            # 자리표시 오리진 — **모든 경로에 200 을 준다.** 이것이 `I2 §3` 이 증명한 함정이다.
            body = b"ok\n"; self.send_response(200)
        elif p == "/healthz":
            body = b"ok\n"; self.send_response(200)
        elif p.startswith("/healthz/") and p[9:] in UNITS:
            u = p[9:]
            if MODE == "dead" and u == "viz-render":
                self.send_response(503); body = b"unavailable"
            else:
                self.send_response(200)
                body = json.dumps({"unit": u, "status": "alive", "implemented": True}).encode()
        else:
            self.send_response(404); body = b"nope"
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
srv = socketserver.TCPServer(("127.0.0.1", 0), H)   # 포트 0 = 커널이 고른다. 고정 포트를 열지 않는다.
open(sys.argv[1], "w").write(str(srv.server_address[1]))
srv.serve_forever()
PY
  SRV=$!
  for _ in $(seq 1 50); do [ -s "$TMP/port" ] && break; sleep 0.1; done
  [ -s "$TMP/port" ] || { echo "픽스처 서버가 뜨지 않았다 — selftest 실패"; exit 1; }
  PORT="$(cat "$TMP/port")"
}
stop_srv() { kill "$SRV" 2>/dev/null; wait "$SRV" 2>/dev/null; SRV=""; rm -f "$TMP/port"; }

V="$HERE/verify-deploy.sh"

echo "── F1 죽은 단위 하나 → red 여야 한다"
start_srv dead;        LABEL=F1; want_red "$V" --base "http://127.0.0.1:$PORT" --http-only; stop_srv

echo "── F2 자리표시 본문(전 경로 200 «ok») → red 여야 한다"
echo "     200 만 보는 판정기는 여기서 green 을 낸다. 그것이 이 픽스처가 잡는 결함이다."
start_srv placeholder; LABEL=F2; want_red "$V" --base "http://127.0.0.1:$PORT" --http-only; stop_srv

echo "── F3 양성 대조군(6종 전부 옳은 본문) → green 이어야 한다"
start_srv green;       LABEL=F3; want_green "$V" --base "http://127.0.0.1:$PORT" --http-only; stop_srv
# ⭑ 면제가 하나라도 있으면 요약줄이 **절대** 「SKIP 0」을 말해서는 안 된다.
#   green-by-skip 이 세상에 나오는 마지막 한 줄이 여기다.
N=$((N+1)); if grep -qF "SKIP 0" "$TMP/out"; then
  echo "  FAIL  [F3] 면제가 있는데 요약줄이 「SKIP 0」이라 말한다 — 건너뛴 건수를 숨긴다"; FAILED=$((FAILED+1))
else echo "  PASS  [F3] 면제가 있을 때 「SKIP 0」이라 말하지 않는다"; fi

echo "── F4 명시 면제는 통과하되 **건수를 드러낸다**"
start_srv green;       LABEL=F4; want_green "$V" --base "http://127.0.0.1:$PORT" --http-only; stop_srv
grep_out F4 "승인된 SKIP 1건"

echo "── F5 검사 대상 0건 → red 여야 한다 (없는 프로젝트 이름으로 컨테이너 검사)"
LABEL=F5; want_red env COLAB_COMPOSE_PROJECT=colab-v2-nonexistent-selftest "$V" --containers-only

echo "── F6 타깃 미지정 → 거부여야 한다 (기본값으로 떨어지지 않는다)"
LABEL=F6; want_red "$HERE/../pipeline/approval/target.sh" check
echo "── F7 prod 타깃 → 거부여야 한다 (조용한 no-op 금지)"
LABEL=F7; want_red "$HERE/../pipeline/approval/target.sh" check prod
echo "── F8 staging 타깃 → 통과여야 한다 (양성 대조군)"
LABEL=F8; want_green "$HERE/../pipeline/approval/target.sh" check staging

echo "── F9 승인 기록: 「무엇을 눈으로 봤는가」가 비면 거부"
LABEL=F9; want_red env COLAB_PIPELINE_STATE_DIR="$TMP/state" "$HERE/../pipeline/approval/approve.sh" Ted
echo "── F10 승인 기록: 승인자가 비면 거부"
LABEL=F10; want_red env COLAB_PIPELINE_STATE_DIR="$TMP/state" "$HERE/../pipeline/approval/approve.sh" "" "대시보드"
echo "── F11 승인 기록: 이름 한 낱말 + 본 것 → 통과 (양성 대조군)"
LABEL=F11; want_green env COLAB_PIPELINE_STATE_DIR="$TMP/state" "$HERE/../pipeline/approval/approve.sh" Ted "데이터셋 목록 화면"

echo "── F12 체인 판정: 한쪽 체인 미적용(빈 version 표) → red 여야 한다"
mkdir -p "$TMP/bin"
cat > "$TMP/bin/docker" <<'SH'
#!/usr/bin/env bash
# 픽스처 껍데기 — 운영 스택에 닿지 않는다. `colab_ai` 조회만 **빈 결과**를 낸다.
for a in "$@"; do case "$a" in -d) next=db ;; *) [ "${next:-}" = db ] && { DB="$a"; next=; } ;; esac; done
case "${DB:-}" in
  colab_platform) echo "0007_abcdef" ;;
  colab_ai)       : ;;                      # 빈 결과 = 체인 미적용
  *)              exit 1 ;;
esac
SH
chmod +x "$TMP/bin/docker"
LABEL=F12; want_red env PATH="$TMP/bin:$PATH" "$HERE/verify-chains.sh"
echo "── F13 체인 판정: 양쪽 다 head 있음 → green (양성 대조군)"
sed -i 's/  colab_ai)       : ;;.*/  colab_ai)       echo "0003_ffeedd" ;;/' "$TMP/bin/docker"
LABEL=F13; want_green env PATH="$TMP/bin:$PATH" "$HERE/verify-chains.sh"

echo
if [ "$FAILED" -ne 0 ]; then
  echo "verify selftest: RED (실패 ${FAILED}건 / ${N}건)"; exit 1
fi
echo "verify selftest: GREEN (${N}건 전부 기대대로 · red fixture 가 실제로 red 를 냈다)"
