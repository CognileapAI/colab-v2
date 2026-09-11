#!/usr/bin/env bash
# I4 dev 알람 스케줄을 실 cron/webhook 없이 검증한다.
set -uo pipefail

ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
INSTALL="$ROOT/infra/ops/install-schedule.sh"
RUN="$ROOT/infra/ops/run-scheduled.sh"
BACKUP="$ROOT/infra/ops/probes/backup-freshness.py"
BUNDLE="$ROOT/infra/ops/build-source-bundle.sh"
VERIFY_SOURCE="$ROOT/infra/ops/verify-source.sh"
VERIFY_REIMPORT="$ROOT/infra/ops/verify-reimport.sh"
DISPATCH="$ROOT/infra/ops/dispatch-current.sh"
FAILED=0; CHECKED=0
pass() { CHECKED=$((CHECKED+1)); echo "  ✓ $*"; }
fail() { CHECKED=$((CHECKED+1)); FAILED=$((FAILED+1)); echo "::error::ops-schedule-selftest red — $*"; }

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" 'colab ops schedule.XXXXXX')"
trap 'rm -rf "$TMP"' EXIT INT TERM
STATE="$TMP/state dir"; CRON_DIR="$TMP/cron.d"; CRON="$CRON_DIR/colab-ops"
mkdir -p "$STATE" "$CRON_DIR"
WEBHOOK="$TMP/webhook file"; printf 'https://alerts.invalid/hook\n' > "$WEBHOOK"; chmod 0600 "$WEBHOOK"
DEV_CRON="$CRON_DIR/colab-dev"
printf '# existing dev backup\n0 19 * * * root /opt/colab-v2/backup.sh\n' > "$DEV_CRON"
DEV_BEFORE="$(sha256sum "$DEV_CRON")"

run_install() {
  env COLAB_OPS_CRON_FILE="$CRON" COLAB_OPS_DEV_CRON_FILE="$DEV_CRON" \
    COLAB_OPS_STATE_DIR="$STATE" "$INSTALL" --env dev --webhook-file "$WEBHOOK" "$@" 2>&1
}

if [ ! -x "$INSTALL" ] || [ ! -x "$RUN" ] || [ ! -x "$BACKUP" ]; then
  fail "설치기·실행기·backup probe 실물이 모두 실행 가능해야 한다"
else
  pass "실행 파일 3종"
fi

for value in "relative" "$TMP/percent%file" "$TMP/line"$'\n'"file"; do
  OUT="$(env COLAB_OPS_CRON_FILE="$CRON" COLAB_OPS_DEV_CRON_FILE="$DEV_CRON" COLAB_OPS_STATE_DIR="$STATE" \
    "$INSTALL" --env dev --webhook-file "$value" install 2>&1)"; RC=$?
  [ "$RC" -eq 78 ] && [ ! -e "$CRON" ] && [[ "$OUT" == *'invalid=webhook-path'* ]] \
    || fail "cron 비안전 경로를 invalid-path 78로 거부하지 않았다"
done
pass "상대/%/개행 경로 거부"

for content in '' 'http://alerts.invalid/hook' $'https://alerts.invalid/a\nhttps://alerts.invalid/b'; do
  printf '%s' "$content" > "$WEBHOOK"; chmod 0600 "$WEBHOOK"
  OUT="$(run_install install)"; RC=$?
  [ "$RC" -eq 78 ] && [ ! -e "$CRON" ] || fail "잘못된 webhook 내용을 78로 거부하지 않았다"
done
printf 'https://alerts.invalid/hook\n' > "$WEBHOOK"
pass "webhook HTTPS 한 줄 검증"

QUOTE_WEBHOOK="$TMP/webhook'quoted file"; cp "$WEBHOOK" "$QUOTE_WEBHOOK"; chmod 0600 "$QUOTE_WEBHOOK"
OUT="$(env COLAB_OPS_CRON_FILE="$CRON" COLAB_OPS_DEV_CRON_FILE="$DEV_CRON" COLAB_OPS_STATE_DIR="$STATE" \
  "$INSTALL" --env dev --webhook-file "$QUOTE_WEBHOOK" install 2>&1)"; RC=$?
if [ "$RC" -eq 0 ] && python3 - "$CRON" "$QUOTE_WEBHOOK" <<'PY'
import shlex, sys
lines=[x for x in open(sys.argv[1]) if x.startswith("*/5")]
assert len(lines)==3
for line in lines:
    args=shlex.split(line.split(" root ", 1)[1])
    assert args[args.index("--webhook-file") + 1] == sys.argv[2]
PY
then
  pass "공백/apostrophe 경로 shell roundtrip"
else fail "공백/apostrophe 경로가 shell 명령으로 보존되지 않았다"; fi
rm -f "$CRON"

OUT="$(run_install install)"; RC=$?
if [ "$RC" -eq 0 ] && [ -f "$CRON" ] && grep -qF '*/5 * * * * root' "$CRON" \
    && grep -qF '/opt/colab-ops/bin/dispatch-current.sh' "$CRON" \
    && [ "$(sha256sum "$DEV_CRON")" = "$DEV_BEFORE" ]; then
  pass "dev cron 보존 + 5분 ops cron 설치"
else
  fail "설치 실패 또는 기존 colab-dev cron 변경 (exit $RC): $OUT"
fi

if run_install verify >/dev/null 2>&1; then pass "설치 뒤 verify"; else fail "verify가 설치 실물을 거부했다"; fi

OUT="$(run_install show)"
if [[ "$OUT" != *'alerts.invalid'* ]]; then pass "show가 webhook 내용을 출력하지 않음"; else fail "show가 webhook credential 내용을 출력했다"; fi

SNAPS="$(find "$STATE" -maxdepth 1 -name 'colab-ops.pre-*.bak' | wc -l)"
if [ "$SNAPS" -ge 1 ]; then pass "설치 전 snapshot"; else fail "설치 전 snapshot이 없다"; fi

if run_install remove >/dev/null 2>&1 && [ ! -e "$CRON" ] && [ "$(sha256sum "$DEV_CRON")" = "$DEV_BEFORE" ]; then
  pass "remove 후 전용 파일만 제거 + dev cron 보존"
else
  fail "remove가 전용 파일 밖을 바꿨다"
fi
run_install install >/dev/null 2>&1 || fail "remove 뒤 재설치 실패"

printf '# >>> colab-v2-dev-ops-alerts >>>\nbroken\n' > "$CRON"
BEFORE="$(sha256sum "$CRON")"; OUT="$(run_install install)"; RC=$?
if [ "$RC" -ne 0 ] && [ "$(sha256sum "$CRON")" = "$BEFORE" ]; then pass "오염 블록 fail-closed"; else fail "오염 블록을 덮어썼다"; fi

rm -f "$CRON"; BAD="$TMP/missing webhook"
OUT="$(env COLAB_OPS_CRON_FILE="$CRON" COLAB_OPS_DEV_CRON_FILE="$DEV_CRON" COLAB_OPS_STATE_DIR="$STATE" \
  "$INSTALL" --env dev --webhook-file "$BAD" install 2>&1)"; RC=$?
if [ "$RC" -eq 78 ] && [ ! -e "$CRON" ]; then pass "webhook 부재 준비 실패 78"; else fail "webhook 부재가 exit 78/무변경이 아니다: $RC"; fi

# run-scheduled의 고정 allowlist와 target별 상태/로그를 격리 복제본에서 확인한다.
OPS="$TMP/ops copy"; mkdir -p "$OPS/probes"
cp "$RUN" "$ROOT/infra/ops/alarm_runner.py" "$OPS/"
for target in deploy-verification service-health backup-freshness; do
  probe="$OPS/probes/$target.sh"
  printf '#!/usr/bin/env bash\nprintf "%%s\\n" "%s" >> "$COLAB_TEST_PROBE_MARK"\n' "$target" > "$probe"
  chmod +x "$probe"
done
MARK="$TMP/probe mark"
for target in deploy-verification service-health backup-freshness; do
  COLAB_TEST_PROBE_MARK="$MARK" COLAB_OPS_STATE_DIR="$STATE" \
    "$OPS/run-scheduled.sh" --env dev --target "$target" --webhook-file "$WEBHOOK" >/dev/null 2>&1 || true
done
if [ "$(sort -u "$MARK" 2>/dev/null | wc -l)" -eq 3 ] \
    && [ "$(find "$STATE" -name '*.state.json' | wc -l)" -eq 3 ] \
    && [ "$(find "$STATE" -name '*.log' | wc -l)" -eq 3 ]; then
  pass "3 probe allowlist + target별 state/log"
else
  fail "3 probe 또는 target별 state/log 배선이 다르다"
fi

if COLAB_OPS_STATE_DIR="$STATE" "$OPS/run-scheduled.sh" --env dev --target arbitrary \
    --webhook-file "$WEBHOOK" >/dev/null 2>&1; then fail "임의 target을 실행했다"; else pass "임의 target 거부"; fi

# 잠금 경합은 서비스 실패 횟수로 기록하면 오분류다.
mkdir -p "$STATE/locks"; exec 9>"$STATE/locks/service-health.lock"; flock -n 9
BEFORE_STATE="$(sha256sum "$STATE/service-health.state.json")"
OUT="$(COLAB_OPS_STATE_DIR="$STATE" "$OPS/run-scheduled.sh" --env dev --target service-health \
  --webhook-file "$WEBHOOK" 2>&1)"; RC=$?
AFTER_STATE="$(sha256sum "$STATE/service-health.state.json")"
if [ "$RC" -eq 75 ] && [ "$BEFORE_STATE" = "$AFTER_STATE" ] && [[ "$OUT" == *'already-running'* ]]; then
  pass "중첩은 준비 상태 75, service 실패 state 불변"
else
  fail "중첩을 서비스 실패로 오분류했다 (exit $RC): $OUT"
fi
exec 9>&-

# 기존 backup oracle에 대한 결합 계약. AWS에는 접촉하지 않는다.
CORE_PY="$ROOT/services/core-api/.venv/bin/python"
if [ -x "$CORE_PY" ] && "$CORE_PY" "$BACKUP" --self-check --repo "$ROOT" >/dev/null 2>&1; then
  pass "deploy_doctor.check_backups 결합 계약"
else
  fail "backup probe가 기존 check_backups와 결합되지 않았다"
fi

# 고정 커밋 archive만 bundle이 되고, manifest/source 교체를 함께 탐지한다.
FIXREPO="$TMP/git source"; mkdir -p "$FIXREPO/infra/ops" "$FIXREPO/services/core-api/ops" \
  "$FIXREPO/db/platform/versions" "$FIXREPO/db/ai/versions" "$FIXREPO/gates/tools" "$FIXREPO/gates/config"
printf '#!/usr/bin/env bash\necho A >> "$COLAB_TEST_DISPATCH_MARK"\n' > "$FIXREPO/infra/ops/run-scheduled.sh"; chmod +x "$FIXREPO/infra/ops/run-scheduled.sh"
printf 'doctor\n' > "$FIXREPO/services/core-api/ops/deploy_doctor.py"
printf 's3\n' > "$FIXREPO/services/core-api/ops/s3_doctor.py"
printf 'revision="p"\n' > "$FIXREPO/db/platform/versions/0001.py"; printf '[alembic]\nversion_table=x\n' > "$FIXREPO/db/platform/alembic.ini"
printf 'revision="a"\n' > "$FIXREPO/db/ai/versions/0001.py"; printf '[alembic]\nversion_table=x\n' > "$FIXREPO/db/ai/alembic.ini"
printf 'gate\n' > "$FIXREPO/gates/tools/rls_coverage.py"; printf 'allow\n' > "$FIXREPO/gates/config/rls-allowlist.toml"
git -C "$FIXREPO" init -q; git -C "$FIXREPO" add .; git -C "$FIXREPO" -c user.name=test -c user.email=test@example.invalid commit -qm base
FIXSHA="$(git -C "$FIXREPO" rev-parse HEAD)"; printf 'dirty\n' > "$FIXREPO/infra/ops/run-scheduled.sh"
OUTDIR="$TMP/bundle"
VROOT="$TMP/verify-root"; VSOURCE="$VROOT/versions/$FIXSHA"; mkdir -p "$VSOURCE"; chmod 0755 "$VROOT" "$VROOT/versions" "$VSOURCE"
if "$BUNDLE" --repo "$FIXREPO" --sha "$FIXSHA" --output "$OUTDIR" >/dev/null \
    && tar xzf "$OUTDIR/colab-ops-source-$FIXSHA.tar.gz" -C "$VSOURCE" \
    && cp "$OUTDIR/colab-ops-source-$FIXSHA.manifest" "$VSOURCE/OPS_SOURCE_MANIFEST" \
    && "$VERIFY_SOURCE" --source "$VSOURCE" --manifest "$VSOURCE/OPS_SOURCE_MANIFEST" --current-sha "$FIXSHA" >/dev/null; then
  pass "고정 commit archive/manifest 검증(working tree dirty 비유입)"
else fail "고정 commit source bundle 검증 실패"; fi
printf 'tamper\n' >> "$VSOURCE/infra/ops/run-scheduled.sh"
if "$VERIFY_SOURCE" --source "$VSOURCE" --manifest "$VSOURCE/OPS_SOURCE_MANIFEST" --current-sha "$FIXSHA" >/dev/null 2>&1; then
  fail "old/tampered source를 허용했다"
else pass "source 누락/변경 탐지"; fi
if "$VERIFY_SOURCE" --source "$VSOURCE" --manifest "$VSOURCE/OPS_SOURCE_MANIFEST" --current-sha deadbeef >/dev/null 2>&1; then
  fail "거짓 CURRENT_SHA를 허용했다"
else pass "manifest source_sha와 CURRENT_SHA 결합"; fi

# 고정 dispatcher는 cron을 바꾸지 않고 A→B→A trusted bundle을 선택한다.
TRUST="$TMP/trust"; mkdir -p "$TRUST/bin" "$TRUST/versions/$FIXSHA"; chmod 0755 "$TRUST" "$TRUST/bin" "$TRUST/versions"
tar xzf "$OUTDIR/colab-ops-source-$FIXSHA.tar.gz" -C "$TRUST/versions/$FIXSHA"; cp "$OUTDIR/colab-ops-source-$FIXSHA.manifest" "$TRUST/versions/$FIXSHA/OPS_SOURCE_MANIFEST"
printf '#!/usr/bin/env bash\necho B >> "$COLAB_TEST_DISPATCH_MARK"\n' > "$FIXREPO/infra/ops/run-scheduled.sh"; chmod +x "$FIXREPO/infra/ops/run-scheduled.sh"
git -C "$FIXREPO" add .; git -C "$FIXREPO" -c user.name=test -c user.email=test@example.invalid commit -qm B
BSHA="$(git -C "$FIXREPO" rev-parse HEAD)"; BOUT="$TMP/bundle-b"
"$BUNDLE" --repo "$FIXREPO" --sha "$BSHA" --output "$BOUT" >/dev/null; mkdir -p "$TRUST/versions/$BSHA"
tar xzf "$BOUT/colab-ops-source-$BSHA.tar.gz" -C "$TRUST/versions/$BSHA"; cp "$BOUT/colab-ops-source-$BSHA.manifest" "$TRUST/versions/$BSHA/OPS_SOURCE_MANIFEST"
cp "$DISPATCH" "$TRUST/bin/dispatch-current.sh" 2>/dev/null || true; cp "$VERIFY_SOURCE" "$TRUST/bin/verify-source.sh" 2>/dev/null || true
chmod +x "$TRUST/bin/dispatch-current.sh" "$TRUST/bin/verify-source.sh" 2>/dev/null || true
DMARK="$TMP/dispatch-mark"; DSTATE="$TMP/dispatch-state"; mkdir -p "$DSTATE"
for sha in "$FIXSHA" "$BSHA" "$FIXSHA"; do
  printf '%s\n' "$sha" > "$DSTATE/CURRENT_SHA"
  COLAB_OPS_TRUST_ROOT="$TRUST" COLAB_DEV_STATE="$DSTATE" COLAB_TEST_DISPATCH_MARK="$DMARK" \
    "$TRUST/bin/dispatch-current.sh" --env dev --target service-health --webhook-file "$WEBHOOK" >/dev/null 2>&1 || true
done
if [ "$(tr '\n' ' ' < "$DMARK" 2>/dev/null)" = 'A B A ' ]; then pass "고정 dispatcher A→B→rollback A"; else fail "고정 dispatcher 업그레이드/rollback 전환 실패"; fi

# 동일 SHA 재반입은 incoming manifest를 trusted 입력으로 쓰지 않는다.
INCOMING="$TMP/incoming.manifest"; cp "$TRUST/versions/$FIXSHA/OPS_SOURCE_MANIFEST" "$INCOMING"; chmod 0666 "$INCOMING"
BEFORE_RESIDENT="$(sha256sum "$TRUST/versions/$FIXSHA/OPS_SOURCE_MANIFEST")"
if "$VERIFY_REIMPORT" --source "$TRUST/versions/$FIXSHA" --incoming-manifest "$INCOMING" --current-sha "$FIXSHA" >/dev/null 2>&1 \
    && [ "$(sha256sum "$TRUST/versions/$FIXSHA/OPS_SOURCE_MANIFEST")" = "$BEFORE_RESIDENT" ]; then
  pass "동일 SHA 재반입: incoming 동일성만 비교 + resident manifest 검증"
else fail "동일 SHA 재반입이 trusted resident manifest로 검증되지 않았다"; fi
printf '# changed\n' >> "$INCOMING"
if "$VERIFY_REIMPORT" --source "$TRUST/versions/$FIXSHA" --incoming-manifest "$INCOMING" --current-sha "$FIXSHA" >/dev/null 2>&1; then
  fail "다른 incoming manifest로 기존 version을 덮어쓸 수 있다"
else pass "동일 SHA manifest 불일치 거부/덮어쓰기 0"; fi

chmod 0775 "$TRUST/versions"
if COLAB_OPS_TRUST_ROOT="$TRUST" COLAB_DEV_STATE="$DSTATE" "$TRUST/bin/dispatch-current.sh" --env dev --target service-health --webhook-file "$WEBHOOK" >/dev/null 2>&1; then
  fail "group-writable trust parent를 허용했다"
else pass "group/world-writable trust parent 거부"; fi
chmod 0755 "$TRUST/versions"; rm -rf "$TRUST/versions/$BSHA"; ln -s "$TRUST/versions/$FIXSHA" "$TRUST/versions/$BSHA"; printf '%s\n' "$BSHA" > "$DSTATE/CURRENT_SHA"
if COLAB_OPS_TRUST_ROOT="$TRUST" COLAB_DEV_STATE="$DSTATE" "$TRUST/bin/dispatch-current.sh" --env dev --target service-health --webhook-file "$WEBHOOK" >/dev/null 2>&1; then
  fail "symlink version 교체를 허용했다"
else pass "symlink source/manifest 거부"; fi
chmod 0770 "$TMP"; printf '%s\n' "$FIXSHA" > "$DSTATE/CURRENT_SHA"
if COLAB_OPS_TRUST_ROOT="$TRUST" COLAB_DEV_STATE="$DSTATE" "$TRUST/bin/dispatch-current.sh" --check >/dev/null 2>&1; then
  fail "trust root 위 writable 조상을 허용했다"
else pass "trust root 위 조상 owner/mode 검사"; fi
chmod 0700 "$TMP"

# docker CLI timeout 뒤에도 컨테이너 표식이 남지 않아야 한다.
FAKEBIN="$TMP/fake docker"; mkdir -p "$FAKEBIN"; MARKER="$TMP/container-running"
cat > "$FAKEBIN/docker" <<'DOCKER'
#!/usr/bin/env bash
case "$1" in
  image) exit 0 ;;
  run) touch "$COLAB_TEST_CONTAINER_MARKER"; sleep 20 ;;
  rm) rm -f "$COLAB_TEST_CONTAINER_MARKER"; exit 0 ;;
esac
DOCKER
chmod +x "$FAKEBIN/docker"; printf '%s\n' "$FIXSHA" > "$TMP/CURRENT_SHA"
OUT="$(PATH="$FAKEBIN:$PATH" COLAB_TEST_CONTAINER_MARKER="$MARKER" COLAB_DEV_STATE="$TMP" \
  COLAB_DEV_REPO="$ROOT" COLAB_OPS_DOCKER_TIMEOUT=1 timeout 5 "$ROOT/infra/ops/probes/deploy-verification.sh" 2>&1)"; RC=$?
if [ "$RC" -eq 124 ] && [ ! -e "$MARKER" ]; then pass "docker timeout 강제정리"; else fail "timeout 뒤 컨테이너가 남았다(exit $RC)"; fi

# alarm_runner가 probe shell을 죽여도 바깥 run-scheduled가 자기 고유 이름만 지운다.
cat > "$OPS/alarm_runner.py" <<'ALARM'
#!/usr/bin/env bash
while [ $# -gt 0 ] && [ "$1" != -- ]; do shift; done; shift
"$@" & child=$!; sleep 0.1; kill -9 "$child" 2>/dev/null; wait "$child" 2>/dev/null; exit 1
ALARM
cat > "$OPS/probes/deploy-verification.sh" <<'PROBE'
#!/usr/bin/env bash
docker run --name "$COLAB_OPS_CONTAINER_NAME"
PROBE
chmod +x "$OPS/alarm_runner.py" "$OPS/probes/deploy-verification.sh"
rm -f "$MARKER"
PATH="$FAKEBIN:$PATH" COLAB_TEST_CONTAINER_MARKER="$MARKER" COLAB_OPS_STATE_DIR="$STATE" \
  "$OPS/run-scheduled.sh" --env dev --target deploy-verification --webhook-file "$WEBHOOK" >/dev/null 2>&1 || true
if [ ! -e "$MARKER" ]; then pass "probe SIGKILL 뒤 바깥 wrapper 고유 container 정리"; else fail "probe SIGKILL 뒤 orphan container 표식"; fi

if [ "$FAILED" -ne 0 ]; then
  echo "ops-schedule-selftest RED — 검사 $CHECKED건 · 실패 $FAILED건"; exit 1
fi
echo "ops-schedule-selftest green — 검사 $CHECKED건 전건 기대대로"
