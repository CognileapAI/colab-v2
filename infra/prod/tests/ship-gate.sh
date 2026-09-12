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

new_fixture() { # $1=이름 → $TMP/$1/repo 에 prod 적재 스크립트 ＋ 공통 게이트 ＋ origin
  local root="$TMP/$1" work="$TMP/$1/repo"
  mkdir -p "$work/infra/prod" "$work/infra/_lib" "$work/dist"
  # `ship.sh` 는 `REPO="$HERE/../.."` 로 저장소를 잡는다 — 같은 상대 배치로 복사해야
  # 픽스처 저장소가 `$REPO` 가 되고 `infra/_lib/ship-gate.sh` 가 그 밑에서 읽힌다.
  cp "$REPO/infra/prod/ship.sh" "$work/infra/prod/ship.sh"
  cp "$REPO/infra/_lib/ship-gate.sh" "$work/infra/_lib/ship-gate.sh"
  for f in compose.yml up.sh backup.sh install-cron.sh; do : > "$work/infra/prod/$f"; done
  chmod +x "$work/infra/prod/ship.sh"
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

echo "── infra/prod/tests/ship-gate.sh — prod 반입 게이트 6 케이스"

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

echo "── 요약 — 통과 $PASS · 실패 $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
