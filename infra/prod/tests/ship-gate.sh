#!/usr/bin/env bash
# `infra/prod/ship.sh` 반입 게이트 셸 시험 (2026-09-12 · 규칙 1·6).
#
# dev 판(`infra/dev/tests/ship-gate.sh`)과 **같은 픽스처 규약**이다 — 임시 `git init` 저장소 ＋
# 로컬 bare `origin`, `PATH` 앞에 둔 가짜 `ssh`·`scp` 가 argv 를 로그에 적고 exit 0 한다.
# 실제 EC2 는 접촉하지 않는다.
#
# prod 가 dev 와 다른 자리는 하나다 — **`prod-YYYYMMDD` 태그 검사**(규칙 6). 조상 검사에는
# 선언 우회(`COLAB_SHIP_ALLOW_NONMAIN=1`)가 있고 **태그 검사에는 없다.** ⓔ 가 그 차이를 잰다.
# 규약 = `gates/tools/*-selftest.sh` 와 같다 — exit 0 green · exit 1 red(판정) · exit 78 red(준비).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"

PASS=0; FAIL=0
ok()   { PASS=$((PASS + 1)); printf '  ✓ %s\n' "$1"; }
bad()  { FAIL=$((FAIL + 1)); printf '  ✗ %s — %s\n' "$1" "$2"; }
check(){ # $1=이름 $2=조건설명 $3=실제 $4=기대
  if [ "$3" = "$4" ]; then ok "$1 · $2 = $3"; else bad "$1 · $2" "기대 $4 · 실제 $3"; fi
}
has()  { # $1=이름 $2=설명 $3=건초더미 $4=바늘
  case "$3" in *"$4"*) ok "$1 · $2" ;; *) bad "$1 · $2" "「$4」가 없다" ;; esac
}

command -v git >/dev/null || { echo "::gate-readiness-failure:: git 이 없다"; exit 78; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/bin"
for cmd in ssh scp; do
  cat > "$TMP/bin/$cmd" <<EOF
#!/usr/bin/env bash
printf '%s %s\n' "$cmd" "\$*" >> "\$COLAB_TEST_SSHLOG"
exit 0
EOF
  chmod +x "$TMP/bin/$cmd"
done

git_q() { git -c user.email=t@t -c user.name=t -c commit.gpgsign=false -C "$1" "${@:2}"; }

# `build-source-bundle.sh` 가 커밋에 있어야 한다고 요구하는 경로들(그 파일의 `PATHS` 배열 축자).
# 하나라도 없으면 번들이 exit 1 이므로, 픽스처는 **빈 자리표라도 전부 커밋해 둔다**.
OPS_BUNDLE_PATHS=(infra/__init__.py infra/ops infra/notifications
                  services/core-api/ops services/core-api/src
                  services/core-api/pyproject.toml services/core-api/requirements.in
                  services/core-api/requirements.txt db/platform db/ai
                  gates/tools/rls_coverage.py gates/config/rls-allowlist.toml)
# 레포 tar 가 `/opt/colab-repo` 로 싣는 경로들(`infra/prod/ship.sh` 의 `REPO_SYNC_PATHS` 축자).
REPO_SYNC_PATHS=(db gates services/core-api/ops infra contracts)

new_fixture() { # $1=이름 → $TMP/$1/repo 에 prod 적재 스크립트 ＋ 공통 게이트 ＋ origin
  local root="$TMP/$1" work="$TMP/$1/repo" p
  mkdir -p "$work/infra/prod" "$work/infra/_lib" "$work/dist"
  # `ship.sh` 는 `REPO="$HERE/../.."` 로 저장소를 잡는다 — 같은 상대 배치로 복사해야
  # 픽스처 저장소가 `$REPO` 가 되고 `infra/_lib/ship-gate.sh` 가 그 밑에서 읽힌다.
  cp "$REPO/infra/prod/ship.sh" "$work/infra/prod/ship.sh"
  cp "$REPO/infra/_lib/ship-gate.sh" "$work/infra/_lib/ship-gate.sh"
  cp "$REPO/infra/_lib/ops-bundle.sh" "$work/infra/_lib/ops-bundle.sh"
  mkdir -p "$work/infra/ops"
  cp "$REPO/infra/ops/build-source-bundle.sh" "$work/infra/ops/build-source-bundle.sh"
  chmod +x "$work/infra/ops/build-source-bundle.sh"
  for f in compose.yml up.sh backup.sh install-cron.sh deploy-doctor.sh; do : > "$work/infra/prod/$f"; done
  chmod +x "$work/infra/prod/ship.sh"
  # 번들이 요구하는 자리표 ＋ 레포 tar 가 싣는 자리 — **디렉터리는 파일 하나를 넣어야 git 이 담는다.**
  for p in "${OPS_BUNDLE_PATHS[@]}" "${REPO_SYNC_PATHS[@]}"; do
    case "$p" in
      *.py|*.toml|*.in|*.txt) mkdir -p "$work/$(dirname "$p")"; : > "$work/$p" ;;
      *) mkdir -p "$work/$p"; : > "$work/$p/.keep" ;;
    esac
  done
  git init -q -b main "$work"
  echo one > "$work/a.txt"
  git_q "$work" add -A >/dev/null
  git_q "$work" commit -qm "one" >/dev/null
  git init -q --bare "$root/origin.git"
  git_q "$work" remote add origin "$root/origin.git"
  git_q "$work" push -q origin main
  printf '%s' "$work"
}

dist_sha() { # $1=저장소 $2=sha
  printf '%s\n' "$2" > "$1/dist/colab-v2-prod.sha"
  : > "$1/dist/colab-v2-prod-$2.tar"
}

run_ship() { # $1=저장소 $2..=추가 env → $RC · $OUT · $SSHLOG
  local w="$1"; shift
  SSHLOG="$w/../ssh.log"; : > "$SSHLOG"
  OUT="$(cd "$w" && PATH="$TMP/bin:$PATH" COLAB_TEST_SSHLOG="$SSHLOG" \
        COLAB_PROD_SSH=ec2-user@example.invalid COLAB_PROD_KEY_FILE=/dev/null \
        env "$@" bash "$w/infra/prod/ship.sh" 2>&1)"
  RC=$?
}

TAGDAY="prod-$(date +%Y%m%d)"

echo "── infra/prod/tests/ship-gate.sh — prod 반입 게이트 6 케이스 ＋ 반입 단계 2 케이스"

# ── ⓐ 비조상 sha → exit 65 · 반입 0회 ───────────────────────────────────────
W="$(new_fixture a)"
echo two > "$W/b.txt"; git_q "$W" add -A >/dev/null; git_q "$W" commit -qm two >/dev/null
NONANC="$(git_q "$W" rev-parse --short=12 HEAD)"
git_q "$W" tag "$TAGDAY" >/dev/null          # 태그가 있어도 조상이 아니면 거절이다
dist_sha "$W" "$NONANC"
run_ship "$W" COLAB_SHIP_UNUSED=1
check "ⓐ 비조상" "exit" "$RC" 65
check "ⓐ 비조상" "ssh·scp 호출 수" "$(wc -l < "$SSHLOG" | tr -d ' ')" 0
has   "ⓐ 비조상" "사유 출력" "$OUT" "origin/main 조상이 아니다"

# ── ⓑ 조상인데 prod 태그가 없다 → exit 65 · 반입 0회 (규칙 6) ───────────────
W="$(new_fixture b)"
ANC="$(git_q "$W" rev-parse --short=12 HEAD)"
dist_sha "$W" "$ANC"
run_ship "$W" COLAB_SHIP_UNUSED=1
check "ⓑ 태그 부재" "exit" "$RC" 65
check "ⓑ 태그 부재" "ssh·scp 호출 수" "$(wc -l < "$SSHLOG" | tr -d ' ')" 0
has   "ⓑ 태그 부재" "사유 출력" "$OUT" "prod 태그가 없다"
has   "ⓑ 태그 부재" "규칙 6 을 가리킨다" "$OUT" "prod-YYYYMMDD"

# ── ⓒ 조상 ＋ prod 태그 → exit 0 · MAIN_SHA 한 줄 · ancestor=yes ────────────
W="$(new_fixture c)"
ANC="$(git_q "$W" rev-parse --short=12 HEAD)"
MAIN="$(git_q "$W" rev-parse --short=12 origin/main)"
git_q "$W" tag "$TAGDAY" >/dev/null
dist_sha "$W" "$ANC"
run_ship "$W" COLAB_SHIP_UNUSED=1
check "ⓒ 통과" "exit" "$RC" 0
LOG="$(cat "$SSHLOG")"
has "ⓒ 통과" "태그 확인 출력" "$OUT" "prod 태그 확인: $TAGDAY"
has "ⓒ 통과" "ssh argv 에 MAIN_SHA 기록" "$LOG" "/opt/colab-v2/MAIN_SHA"
has "ⓒ 통과" "printf 형식 축자" "$LOG" "main=%s candidate=%s ancestor=%s"
has "ⓒ 통과" "세 값이 yes 로 실린다" "$LOG" " $MAIN $ANC yes"

# ── ⓓ 비조상 ＋ 우회 선언 ＋ 태그 → exit 0 · ancestor=bypass ────────────────
W="$(new_fixture d)"
echo two > "$W/b.txt"; git_q "$W" add -A >/dev/null; git_q "$W" commit -qm two >/dev/null
NONANC="$(git_q "$W" rev-parse --short=12 HEAD)"
git_q "$W" tag "$TAGDAY" >/dev/null
dist_sha "$W" "$NONANC"
run_ship "$W" COLAB_SHIP_ALLOW_NONMAIN=1
check "ⓓ 우회 선언" "exit" "$RC" 0
has   "ⓓ 우회 선언" "출력에 선언이 남는다" "$OUT" "우회 선언"
has   "ⓓ 우회 선언" "ssh argv 에 ancestor=bypass" "$(cat "$SSHLOG")" " $NONANC bypass"

# ── ⓔ 태그 검사에는 우회가 없다 — 조상 ＋ 태그 부재 ＋ 우회 선언 → 여전히 65 ─
W="$(new_fixture e)"
ANC="$(git_q "$W" rev-parse --short=12 HEAD)"
dist_sha "$W" "$ANC"
run_ship "$W" COLAB_SHIP_ALLOW_NONMAIN=1
check "ⓔ 태그 우회 불가" "exit" "$RC" 65
check "ⓔ 태그 우회 불가" "ssh·scp 호출 수" "$(wc -l < "$SSHLOG" | tr -d ' ')" 0
has   "ⓔ 태그 우회 불가" "우회가 없다고 말한다" "$OUT" "우회 선언이 없다"

# ── ⓕ origin 조회 실패 → exit 78 (준비) ────────────────────────────────────
W="$(new_fixture f)"
ANC="$(git_q "$W" rev-parse --short=12 HEAD)"
git_q "$W" tag "$TAGDAY" >/dev/null
dist_sha "$W" "$ANC"
git_q "$W" remote set-url origin "$TMP/f/없는저장소.git"
run_ship "$W" COLAB_SHIP_UNUSED=1
check "ⓕ origin 부재" "exit" "$RC" 78
check "ⓕ origin 부재" "ssh·scp 호출 수" "$(wc -l < "$SSHLOG" | tr -d ' ')" 0
has   "ⓕ origin 부재" "사유 출력" "$OUT" "origin 조회 실패"

# ── ⓖ 통과 회차의 **반입 단계** — deploy-doctor · 레포 tar · ops 번들 · prod.env ─────
# 왜 여기서 재나 — 이 넷은 전부 「빠뜨려도 ship.sh 가 exit 0 을 낸다」는 모양이었다.
# `deploy_doctor` ⑥ 이 낡은 `/opt/colab-repo` 를 정답표로 삼아 조용히 틀리고(dev 실측 2회),
# `prod.env` 의 `COLAB_IMAGE_TAG` 를 손으로 안 고치면 **옛 이미지로 마이그레이션이 돈다**.
W="$(new_fixture g)"
ANC="$(git_q "$W" rev-parse --short=12 HEAD)"
git_q "$W" tag "$TAGDAY" >/dev/null
dist_sha "$W" "$ANC"
run_ship "$W" COLAB_SHIP_UNUSED=1
check "ⓖ 반입 단계" "exit" "$RC" 0
LOG="$(cat "$SSHLOG")"
has "ⓖ 반입 단계" "deploy-doctor.sh 를 싣는다" "$LOG" "infra/prod/deploy-doctor.sh"
has "ⓖ 반입 단계" "레포 tar 를 싣는다" "$LOG" "colab-repo-$ANC.tgz"
has "ⓖ 반입 단계" "/opt/colab-repo 에 --overwrite 로 푼다" "$LOG" "-C /opt/colab-repo --overwrite"
has "ⓖ 반입 단계" "ops 번들 tar 를 싣는다" "$LOG" "colab-ops-source-$ANC.tar.gz"
has "ⓖ 반입 단계" "ops 번들 manifest 를 싣는다" "$LOG" "colab-ops-source-$ANC.manifest"
has "ⓖ 반입 단계" "ops 버전 자리" "$LOG" "/opt/colab-ops/versions/$ANC"
has "ⓖ 반입 단계" "소스 검증기를 심는다" "$LOG" "/opt/colab-ops/bin/verify-source.sh"
has "ⓖ 반입 단계" "재반입 검증 갈래" "$LOG" "verify-reimport.sh"
has "ⓖ 반입 단계" "prod.env 갱신 스크립트를 싣는다" "$LOG" "set-image-tag.sh"
has "ⓖ 반입 단계" "갱신 인자가 불변 태그다" "$LOG" "set-image-tag.sh prod-$ANC"
has "ⓖ 반입 단계" "다음 단계를 말한다" "$OUT" "up.sh"
# 레포 tar 는 **실제 파일 존재**로 만든다 — P3 는 `infra/prod` 가 미추적인 워크트리에서 돈다.
REPO_TGZ="$W/dist/colab-repo-$ANC.tgz"
if [ -f "$REPO_TGZ" ]; then
  ok "ⓖ 반입 단계 · 레포 tar 가 dist 에 생겼다"
  TARLIST="$(tar tzf "$REPO_TGZ")"
  for p in "${REPO_SYNC_PATHS[@]}"; do
    has "ⓖ 반입 단계" "레포 tar 에 $p" "$TARLIST" "$p"
  done
else
  bad "ⓖ 반입 단계 · 레포 tar 가 dist 에 생겼다" "$REPO_TGZ 가 없다"
fi
# `prod.env` 갱신은 **원격 스크립트 파일**이다 — heredoc 으로 원격 셸에 본문을 흘리지 않는다.
SETTER="$W/dist/set-image-tag.sh"
if [ -f "$SETTER" ]; then
  ok "ⓖ 반입 단계 · prod.env 갱신 스크립트가 dist 에 생겼다"
  SETTXT="$(cat "$SETTER")"
  has "ⓖ 반입 단계" "갱신 대상이 prod.env" "$SETTXT" "/opt/colab-v2/prod.env"
  has "ⓖ 반입 단계" "옛 줄을 걷어낸다" "$SETTXT" "COLAB_IMAGE_TAG="
  has "ⓖ 반입 단계" "모드 0600 을 유지한다" "$SETTXT" "chmod 0600"
  case "$SETTXT" in *"<<"*) bad "ⓖ 반입 단계 · heredoc 금지" "본문에 << 가 있다" ;; *) ok "ⓖ 반입 단계 · heredoc 금지" ;; esac
else
  bad "ⓖ 반입 단계 · prod.env 갱신 스크립트가 dist 에 생겼다" "$SETTER 가 없다"
fi

# ── ⓗ 레포 tar 대상이 빠지면 **거절** — 조용히 적게 싣지 않는다 ───────────────
# `git ls-files` 가 아니라 **실제 파일 존재**로 판정한다(P3 의 미추적 배치를 살리는 자리).
W="$(new_fixture h)"
ANC="$(git_q "$W" rev-parse --short=12 HEAD)"
git_q "$W" tag "$TAGDAY" >/dev/null
dist_sha "$W" "$ANC"
rm -rf "$W/contracts"
run_ship "$W" COLAB_SHIP_UNUSED=1
check "ⓗ 레포 tar 결손" "exit" "$RC" 2
has   "ⓗ 레포 tar 결손" "사유 출력" "$OUT" "contracts"

echo "── 요약 — 통과 $PASS · 실패 $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
