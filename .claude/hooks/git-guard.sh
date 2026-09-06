#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# H3 — `PreToolUse` (matcher: Bash) · 스펙 `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` C절.
#
# 무엇을 해소하나 (F8 「병합 권한 잠금」 · D10 인접): `main` 은 오케스트레이터 한 자리에서만
#   움직인다는 규약이 문장으로만 있었다. 레인이 자기 브랜치에서 `main` 으로 밀거나, 강제 푸시로
#   남의 커밋을 덮거나, `gh pr merge` 로 게이트 밖에서 병합하는 경로가 열려 있었다.
#
# ⛔ **차단 대상은 명시 열거다 — 넓히지 않는다.** 스펙 C 의 H3 행 축자:
#   「⚠ **레인 첫 줄 `git merge --ff-only` 를 막으면 안 된다**(D6 해법). 차단 대상을 명시 열거로 좁힘 —
#     ⑴ main/master 로 push ⑵ `--force`/`-f` push ⑶ **HEAD 가 main/master 일 때의** `git merge`
#     ⑷ `gh pr merge` ⑸ `branch -D main`. 비-main 브랜치에서의 `merge --ff-only` 는 **허용**」
#
# ⭑ ⟨개정 2026-09-06 · P-J 설계 판정⟩ **⑶ 은 `--ff-only` 가 없을 때로 좁힌다.**
#   `main` 에서의 `git merge --ff-only <레인>` 은 오케스트레이터가 승인된 형태로 병합하는
#   **그 명령 자체**다(`rules §4-2` · `§2-1`). 그것까지 막으면 정상 경로마다 `COLAB_HOOKS=0` 을
#   붙이게 되고, 상시 무력화된 훅은 훅이 아니다. ff 가 아닌 병합(새 병합 커밋을 만드는 형태)은
#   **차단 유지** — 전수 green ＋ 〈N〉 재실측을 건너뛴 이력이 `main` 에 남는 자리가 거기다.
#   ／ 종전 ~~`main` 에서의 모든 `git merge` 차단~~(`11-merge-guards-verification.md` §2-1 ⑸).
#   허용(exit 0)이 정상인 것 — 비-main 브랜치의 `git merge --ff-only <x>` · `git push origin <기능브랜치>`
#   · `git fetch` · `git pull --rebase` · `git worktree …` · `git push origin --delete <기능브랜치>`
#   · git 이 아닌 모든 명령.
#
# ── PreToolUse 입력 스키마 (stdin · 문서 인용) ────────────────────────────────
#   https://code.claude.com/docs/en/hooks
#     {
#       "session_id": "abc123",
#       "prompt_id": "550e8400-e29b-41d4-a716-446655440000",
#       "transcript_path": "/home/user/.claude/projects/.../transcript.jsonl",
#       "cwd": "/home/user/my-project",
#       "permission_mode": "default",
#       "hook_event_name": "PreToolUse",
#       "tool_name": "Bash",
#       "tool_input": {
#         "command": "npm test",
#         "description": "Run test suite",
#         "timeout": 120000,
#         "run_in_background": false
#       },
#       "tool_use_id": "toolu_01ABC123..."
#     }
#   · `cwd` — "Current working directory when the hook is invoked"
#   · `tool_name`·`tool_input` — "The `tool_name`, `tool_input`, and `tool_use_id` fields are
#     event-specific."  ⇒ Bash 의 명령문은 `tool_input.command` 한 자리다.
#   · matcher — "PreToolUse … events have matchers that filter on tool name" ·
#     "`Bash` matches only the Bash tool". 그래서 이 훅은 Bash 호출에만 뜬다.
#
# ── 차단 규약 (문서 인용) ─────────────────────────────────────────────────────
#   exit 2 = "Blocks the tool call" · 그때 모델이 보는 문장은
#   "The blocking message is the reason from your JSON's blocking decision when it makes one,
#    and your stderr text otherwise."  ⇒ **stderr 한 줄이 곧 차단 사유다.**
#   exit 0 의 stderr 는 "goes to the debug log only, never the transcript, and Claude never sees it"
#   ⇒ 통과시킬 때는 아무것도 적지 않는다.
#   ⚠ **exit 1 은 통과다.** 판정을 못 하면 통과가 기본값이고, 그것이 의도다 — 파싱 실패가
#     모든 Bash 호출을 막으면 훅이 세션을 세운다. 이 훅은 보안 경계가 아니라 **마찰 장치**다.
#
# ⚠ 알려진 한계 (넓히지 않는 이유): 한 겹 감싼 형태(`bash -c "git push origin main"`,
#   `eval "$CMD"`)는 잡지 않는다. 잡으려고 문자열 어디에나 있는 `git` 을 세면 `echo`·문서 편집
#   같은 무해한 호출이 걸린다 — 오탐이 붙은 차단 훅은 곧 `COLAB_HOOKS=0` 상시화로 끝난다.
set -uo pipefail

payload=""
if [ ! -t 0 ]; then payload="$(cat 2>/dev/null || true)"; fi
[ -n "$payload" ] || exit 0

# ── 1. 입력 꺼내기 ────────────────────────────────────────────────────────────
# `command` 는 줄바꿈·따옴표를 담으므로 sed 로는 온전히 못 꺼낸다. python3 이 정본이고,
# 없으면 **통과**시킨다(판정 불가를 차단으로 세지 않는다).
command -v python3 >/dev/null 2>&1 || exit 0

read_fields() {
  printf '%s' "$payload" | python3 -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
if not isinstance(d,dict): sys.exit(0)
ti=d.get("tool_input") or {}
if not isinstance(ti,dict): ti={}
cmd=ti.get("command") or ""
# 명령문은 여러 줄일 수 있다 — 한 줄에 실어 보내려고 개행을 세퍼레이터로 바꾼다.
# (세그먼트 분리에서 개행은 어차피 `;` 과 같은 자리다.)
print(d.get("tool_name",""))
print(d.get("cwd",""))
print(str(cmd).replace("\r"," ").replace("\n"," ; "))
' 2>/dev/null
}

mapfile -t _f < <(read_fields)
TOOL="${_f[0]:-}"
CWD="${_f[1]:-}"
CMD="${_f[2]:-}"

[ "$TOOL" = "Bash" ] || exit 0
[ -n "$CMD" ] || exit 0
[ -n "$CWD" ] || CWD="$PWD"

# ── 2. 지금 어느 브랜치에 서 있나 ─────────────────────────────────────────────
# 워크트리 세션에서 `$CLAUDE_PROJECT_DIR` 은 **세션이 뜬 체크아웃**을 가리키고 움직이지 않는다.
# 판정 대상은 Claude 가 실제로 서 있는 자리이므로 입력의 `cwd` 를 쓴다
# (worktrees 문서: "`cwd` follows Claude … Read it when a hook needs the worktree path").
BRANCH="$(git -C "$CWD" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
on_main=0
case "$BRANCH" in main|master) on_main=1 ;; esac

# ── 3. 세그먼트로 가른다 ──────────────────────────────────────────────────────
# `a && b`, `a ; b`, `a | b` 를 각각 한 명령으로 본다. 구분자를 개행으로 바꾸고 줄 단위로 읽는다.
SEGS="$(printf '%s' "$CMD" | sed -e 's/&&/\n/g' -e 's/||/\n/g' -e 's/;/\n/g' -e 's/|/\n/g')"

is_main_ref() { # $1=refspec 토큰 — 목적지(dst)가 main/master 인가
  local t="$1" dst
  t="${t#+}"                       # `+main` 강제 갱신 표기
  case "$t" in *:*) dst="${t##*:}" ;; *) dst="$t" ;; esac
  dst="${dst#refs/heads/}"
  case "$dst" in main|master) return 0 ;; *) return 1 ;; esac
}

deny() { # $1=사유 한 줄 — stderr 한 줄이 그대로 차단 사유가 된다
  echo "⛔ 차단(H3 git-guard) — $1 · 이 자리는 오케스트레이터 몫이다(스펙 C H3). 정말 필요하면 COLAB_HOOKS=0 을 앞에 붙여 다시 부른다." >&2
  exit 2
}

while IFS= read -r seg; do
  # 앞머리 정리 — 공백·`env VAR=x`·`sudo`·`command`·`nohup`·`time` 은 넘기고 실행 파일부터 본다.
  # shellcheck disable=SC2086
  set -- $seg
  while [ $# -gt 0 ]; do
    case "$1" in
      *=*)                       shift ;;   # 앞머리 환경변수
      sudo|command|nohup|time|env) shift ;;
      *)                         break ;;
    esac
  done
  [ $# -gt 0 ] || continue

  exe="$1"; exe="${exe##*/}"     # `/usr/bin/git` → `git`
  shift

  # ── ⑷ gh pr merge — 게이트 밖 병합 경로 ────────────────────────────────────
  if [ "$exe" = "gh" ]; then
    if [ "${1:-}" = "pr" ] && [ "${2:-}" = "merge" ]; then
      deny "\`gh pr merge\` — PR 병합은 전수 게이트·〈N〉 재실측을 건너뛴다"
    fi
    continue
  fi

  [ "$exe" = "git" ] || continue

  # git 전역 옵션을 건너뛰고 서브커맨드를 찾는다 (`git -C <path> push …` 형태 포함).
  while [ $# -gt 0 ]; do
    case "$1" in
      -C|-c|--git-dir|--work-tree|--namespace|--exec-path) shift 2 || break ;;
      --git-dir=*|--work-tree=*|--namespace=*|--exec-path=*|-p|--paginate|--no-pager|--bare|--literal-pathspecs)
        shift ;;
      -*) shift ;;
      *)  break ;;
    esac
  done
  sub="${1:-}"; [ $# -gt 0 ] && shift

  case "$sub" in
    push)
      force=0; targets_main=0; npos=0
      for tok in "$@"; do
        case "$tok" in
          --force|-f|--force-with-lease|--force-with-lease=*|--force-if-includes) force=1 ;;
          --delete|-d) : ;;                       # 뒤따르는 브랜치 이름은 아래 positional 로 잡힌다
          -*) : ;;
          *)  npos=$((npos+1))
              # positional 1 은 원격 이름(`origin`)이다. 그것 자체가 main 이면 아래 단독 규칙이 받는다.
              if [ "$npos" -ge 2 ] && is_main_ref "$tok"; then targets_main=1; fi
              if [ "$npos" -eq 1 ] && is_main_ref "$tok"; then targets_main=1; fi
              ;;
        esac
      done
      # ⑵ 강제 푸시가 main/master 를 겨눈다
      if [ "$force" -eq 1 ] && [ "$targets_main" -eq 1 ]; then
        deny "main/master 로 강제 푸시(\`--force\`/\`-f\`/\`--force-with-lease\`) — 남의 커밋을 덮는다"
      fi
      # ⑴-a refspec 이 main/master 를 명시했다
      if [ "$targets_main" -eq 1 ]; then
        deny "main/master 로 push — \`main\` 은 오케스트레이터의 ff 병합으로만 움직인다"
      fi
      # ⑴-b refspec 이 없고 지금 서 있는 곳이 main/master 다(＝ 현재 브랜치가 그대로 나간다)
      if [ "$npos" -le 1 ] && [ "$on_main" -eq 1 ]; then
        if [ "$force" -eq 1 ]; then
          deny "현재 브랜치가 \`$BRANCH\` 인데 refspec 없는 강제 push — main/master 가 그대로 덮인다"
        fi
        deny "현재 브랜치가 \`$BRANCH\` 인데 refspec 없는 push — main/master 가 그대로 나간다"
      fi
      ;;
    merge)
      # ⑶ **HEAD 가 main/master 이고 `--ff-only` 가 없을 때** 막는다.
      #    · 비-main 브랜치의 `git merge --ff-only <통합브랜치>`(레인 첫 줄) — 통과.
      #    · main 에서의 `git merge --ff-only <레인>`(오케스트레이터의 승인된 병합) — **통과**
      #      (⭑ 개정 2026-09-06 · P-J. 종전에는 이것도 막혔다).
      #    · main 에서의 그 밖의 `git merge` — 차단. 새 병합 커밋이 게이트 밖에서 생긴다.
      ff_only=0
      for tok in "$@"; do
        case "$tok" in --ff-only) ff_only=1 ;; esac
      done
      if [ "$on_main" -eq 1 ] && [ "$ff_only" -eq 0 ]; then
        deny "현재 브랜치가 \`$BRANCH\` 인 상태의 \`git merge\`(--ff-only 없음) — main 은 전수 green ＋ 〈N〉 재실측 뒤 \`git merge --ff-only <레인>\` 로만 움직인다"
      fi
      ;;
    branch)
      del=0; hit=0
      for tok in "$@"; do
        case "$tok" in
          -D|-d|--delete) del=1 ;;
          -*) : ;;
          main|master|refs/heads/main|refs/heads/master) hit=1 ;;
        esac
      done
      if [ "$del" -eq 1 ] && [ "$hit" -eq 1 ]; then
        deny "\`git branch -D main|master\` — 기준 브랜치를 지운다"
      fi
      ;;
  esac
done <<< "$SEGS"

exit 0
