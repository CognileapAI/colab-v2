#!/usr/bin/env bash
# `infra/dev/ship.sh` 반입 게이트 · `infra/dev/tag-release.sh` 셸 시험 (WU-D2).
#
# 픽스처 = 임시 `git init` 저장소 ＋ 로컬 bare `origin`. 실제 EC2 는 접촉하지 않는다 —
# `ssh`·`scp` 는 `PATH` 앞에 둔 가짜가 argv 를 로그에 적고 exit 0 한다(`ship.sh` 는
# 명령 배열을 env 로 바꿀 수 없으므로 `SSH=(echo)` 스파이가 성립하지 않는다).
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

# ── 픽스처 ──────────────────────────────────────────────────────────────────
# 가짜 ssh·scp — argv 를 로그에 적는다. `ship.sh` 가 이것을 부르면 「반입이 일어났다」는 뜻이다.
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

new_fixture() { # $1=이름 → $TMP/$1/repo 에 ship.sh 사본 ＋ origin 딸림, 표준출력 = 저장소 경로
  local root="$TMP/$1" work="$TMP/$1/repo"
  mkdir -p "$work/infra/dev" "$work/dist"
  # `ship.sh` 는 `REPO="$HERE/../.."` 로 저장소를 잡는다(`infra/dev/ship.sh:10`) —
  # 같은 상대 배치로 복사해야 픽스처 저장소가 `$REPO` 가 된다.
  cp "$REPO/infra/dev/ship.sh" "$work/infra/dev/ship.sh"
  cp "$REPO/infra/dev/tag-release.sh" "$work/infra/dev/tag-release.sh" 2>/dev/null || true
  cp "$REPO/infra/dev/compose.yml" "$REPO/infra/dev/up.sh" "$work/infra/dev/"
  chmod +x "$work/infra/dev/"*.sh
  git init -q -b main "$work"
  echo one > "$work/a.txt"
  git_q "$work" add -A >/dev/null
  git_q "$work" commit -qm "one" >/dev/null
  git init -q --bare "$root/origin.git"
  git_q "$work" remote add origin "$root/origin.git"
  git_q "$work" push -q origin main
  printf '%s' "$work"
}

dist_sha() { # $1=저장소 $2=sha — dist 에 sha 파일과 tar 를 심는다
  printf '%s\n' "$2" > "$1/dist/colab-v2-dev.sha"
  : > "$1/dist/colab-v2-dev-$2.tar"
}

run_ship() { # $1=저장소 → exit 코드는 $RC · 출력은 $OUT · ssh 로그는 $SSHLOG
  SSHLOG="$1/../ssh.log"; : > "$SSHLOG"
  OUT="$(cd "$1" && PATH="$TMP/bin:$PATH" COLAB_TEST_SSHLOG="$SSHLOG" \
        COLAB_DEV_SSH=ec2-user@example.invalid COLAB_DEV_KEY_FILE=/dev/null \
        bash "$1/infra/dev/ship.sh" 2>&1)"
  RC=$?
}

echo "── ship-gate.sh — 반입 게이트 6 케이스"

# ── ⓐ 비조상 sha → exit 65 · 가짜 ssh 호출 0 ────────────────────────────────
W="$(new_fixture a)"
echo two > "$W/b.txt"; git_q "$W" add -A >/dev/null; git_q "$W" commit -qm two >/dev/null
NONANC="$(git_q "$W" rev-parse --short=12 HEAD)"   # origin/main 에 push 하지 않았다 → 비조상
dist_sha "$W" "$NONANC"
run_ship "$W"
check "ⓐ 비조상" "exit" "$RC" 65
check "ⓐ 비조상" "ssh·scp 호출 수" "$(wc -l < "$SSHLOG" | tr -d ' ')" 0
has   "ⓐ 비조상" "사유 출력" "$OUT" "origin/main 조상이 아니다"

# ── ⓑ 조상 sha → exit 0 · ssh argv 에 MAIN_SHA 기록 ＋ ancestor=yes ─────────
W="$(new_fixture b)"
ANC="$(git_q "$W" rev-parse --short=12 HEAD)"
MAIN="$(git_q "$W" rev-parse --short=12 origin/main)"
dist_sha "$W" "$ANC"
run_ship "$W"
check "ⓑ 조상" "exit" "$RC" 0
LOG="$(cat "$SSHLOG")"
has "ⓑ 조상" "ssh argv 에 MAIN_SHA 기록" "$LOG" "/opt/colab-v2/MAIN_SHA"
has "ⓑ 조상" "printf 형식 축자" "$LOG" "main=%s candidate=%s ancestor=%s"
has "ⓑ 조상" "main= 값" "$LOG" "$MAIN"
has "ⓑ 조상" "candidate= 값(CURRENT_SHA 와 같은 문자열)" "$LOG" "$ANC"
has "ⓑ 조상" "세 값이 yes 로 실린다" "$LOG" " $MAIN $ANC yes"

# ── ⓒ origin 조회 실패 → exit 78 (준비) ────────────────────────────────────
W="$(new_fixture c)"
ANC="$(git_q "$W" rev-parse --short=12 HEAD)"
dist_sha "$W" "$ANC"
git_q "$W" remote set-url origin "$TMP/c/없는저장소.git"
run_ship "$W"
check "ⓒ origin 부재" "exit" "$RC" 78
check "ⓒ origin 부재" "ssh·scp 호출 수" "$(wc -l < "$SSHLOG" | tr -d ' ')" 0
has   "ⓒ origin 부재" "사유 출력" "$OUT" "origin 조회 실패"

# ── ⓓ 비조상 ＋ 우회 선언 → exit 0 · 출력 「우회 선언」 · ancestor=bypass ───
W="$(new_fixture d)"
echo two > "$W/b.txt"; git_q "$W" add -A >/dev/null; git_q "$W" commit -qm two >/dev/null
NONANC="$(git_q "$W" rev-parse --short=12 HEAD)"
dist_sha "$W" "$NONANC"
SSHLOG="$W/../ssh.log"; : > "$SSHLOG"
OUT="$(cd "$W" && PATH="$TMP/bin:$PATH" COLAB_TEST_SSHLOG="$SSHLOG" \
      COLAB_DEV_SSH=ec2-user@example.invalid COLAB_DEV_KEY_FILE=/dev/null \
      COLAB_SHIP_ALLOW_NONMAIN=1 bash "$W/infra/dev/ship.sh" 2>&1)"; RC=$?
check "ⓓ 우회 선언" "exit" "$RC" 0
has   "ⓓ 우회 선언" "출력에 선언이 남는다" "$OUT" "우회 선언"
has   "ⓓ 우회 선언" "ssh argv 에 ancestor=bypass" "$(cat "$SSHLOG")" " $NONANC bypass"

# ── ⓔ 같은 날 tag-release.sh dev 2회 → -1 · -2 ─────────────────────────────
W="$(new_fixture e)"
ANC="$(git_q "$W" rev-parse --short=12 HEAD)"
dist_sha "$W" "$ANC"
DAY="$(date +%Y%m%d)"
TAGOUT1="$(cd "$W" && bash "$W/infra/dev/tag-release.sh" dev 2>&1)"; T1=$?
TAGOUT2="$(cd "$W" && bash "$W/infra/dev/tag-release.sh" dev 2>&1)"; T2=$?
check "ⓔ 태그" "1회차 exit" "$T1" 0
check "ⓔ 태그" "2회차 exit" "$T2" 0
check "ⓔ 태그" "생성된 태그" "$(git_q "$W" tag -l "dev-$DAY-*" | sort | tr '\n' ' ')" "dev-$DAY-1 dev-$DAY-2 "
has   "ⓔ 태그" "push 는 사람이 한다 — 명령만 출력" "$TAGOUT2" "git push origin dev-$DAY-2"
check "ⓔ 태그" "원격에 push 하지 않았다" "$(git -C "$W/../origin.git" tag -l | wc -l | tr -d ' ')" 0
# 태그 대상은 로컬 dist 의 sha 다 — EC2 `CURRENT_SHA` 를 읽지 않는다(spec advisor ① 정정).
check "ⓔ 태그" "태그가 가리키는 sha" "$(git_q "$W" rev-parse --short=12 "dev-$DAY-1^{commit}")" "$ANC"
rm -f "$W/dist/colab-v2-dev.sha"
(cd "$W" && bash "$W/infra/dev/tag-release.sh" dev >/dev/null 2>&1); T3=$?
check "ⓔ 태그" "dist sha 부재 exit" "$T3" 65

# ── ⓕ staging 원장 행에 브랜치 필드 ────────────────────────────────────────
# `deploy.sh` 에 드라이런 모드가 없다(`grep -n 'DRY\|dry-run' infra/staging/deploy.sh` = 0건).
# 실배포 없이 잴 수 있는 것은 ⑴ 구문 ⑵ `ledger_append deploy` 세 줄 전부에 필드가 붙었는지다.
if bash -n "$REPO/infra/staging/deploy.sh" 2>/dev/null; then
  ok "ⓕ 원장 · deploy.sh 구문"
else
  bad "ⓕ 원장 · deploy.sh 구문" "bash -n 실패"
fi
LEDGER_N="$(grep -c 'ledger_append deploy ' "$REPO/infra/staging/deploy.sh")"
BRANCH_N="$(grep 'ledger_append deploy ' "$REPO/infra/staging/deploy.sh" | grep -c '브랜치=')"
check "ⓕ 원장" "ledger_append deploy 줄 수" "$LEDGER_N" 3
check "ⓕ 원장" "그중 브랜치= 가 붙은 줄" "$BRANCH_N" "$LEDGER_N"
has   "ⓕ 원장" "값은 현재 브랜치명" \
  "$(grep 'ledger_append deploy ' "$REPO/infra/staging/deploy.sh" | head -1)" 'branch --show-current'

echo "── 요약 — 통과 $PASS · 실패 $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
