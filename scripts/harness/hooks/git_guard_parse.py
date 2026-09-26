"""H3 git-guard — command parser and rule engine (called by `git-guard.sh`).

stdin  = the payload JSON already accepted by `lifecycle_contract.py validate-input --field command`.
stdout = JSON lines: line 1 `parsed` | `fallback <reason>`; one record per segment
         `{"seg":<n>,"dir":"<target checkout>","argv":[...],"opaque":<bool>}`; last line `{"end":<records>}`.
exit   = 0 parsed/allowed · 2 parsed/denied (one stderr line, written after the end marker) ·
         anything else = parser failure (git-guard.sh then runs its frozen bash rule engine).
Standard library only. The parser falls back only on input that `bash -n` also rejects
(unterminated quote, `$(`, `${`, backtick or `(`); an unterminated heredoc runs to end of input.
"""
import json
import os
import re
import subprocess
import sys

PROTECTED = ('main', 'master', 'develop', 'product')
LABEL = '보호 브랜치(main · master · develop · product)'
RESEED = re.compile(r'(^|[\s;&|(`])COLAB_RESEED_ACK_(NONEMPTY|BASIS)=')
PREFIX_WORDS = ('sudo', 'command', 'nohup', 'time', 'env')
RESERVED = ('!', '{', 'if', 'then', 'elif', 'else', 'do', 'while', 'until')
API_MERGE = re.compile(r'pulls/[0-9]+/merge/?(\?|$)')
BLANK = ' \t\r'
WORD_END = ' \t\r\n;&|()<>'


class ParseError(Exception):
    pass


class Word:
    __slots__ = ('text', 'opaque', 'quoted')

    def __init__(self, text, opaque=False, quoted=False):
        self.text, self.opaque, self.quoted = text, opaque, quoted

    def __repr__(self):
        return f'Word({self.text!r}, opaque={self.opaque})'


# ── scanners for nested constructs (return the index just past the construct) ──
def skip_single(s, i):
    j = s.find("'", i)
    if j < 0:
        raise ParseError('unterminated single quote')
    return j + 1


def skip_ansi(s, i):
    while i < len(s):
        if s[i] == '\\':
            i += 2
            continue
        if s[i] == "'":
            return i + 1
        i += 1
    raise ParseError("unterminated $'")


def skip_backtick(s, i):
    while i < len(s):
        if s[i] == '\\':
            i += 2
            continue
        if s[i] == '`':
            return i + 1
        i += 1
    raise ParseError('unterminated backtick')


def skip_group(s, i, open_ch, close_ch, depth=1):
    """Quote-aware nesting count from just after an opening `open_ch`."""
    n = len(s)
    while i < n:
        c = s[i]
        if c == '\\':
            i += 2
            continue
        if c == "'":
            i = skip_single(s, i + 1)
            continue
        if c == '"':
            i = lex_dquote(s, i + 1)[2]
            continue
        if c == '`':
            i = skip_backtick(s, i + 1)
            continue
        if c == '$' and s.startswith("$'", i):
            i = skip_ansi(s, i + 2)
            continue
        if c == '#' and open_ch == '(' and (i == 0 or s[i - 1] in ' \t\n;|&('):
            j = s.find('\n', i)
            i = n if j < 0 else j
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ParseError(f'unterminated {open_ch}')


def dollar(s, i):
    """At `s[i] == '$'`: return (raw text, opaque, next index)."""
    nxt = s[i + 1] if i + 1 < len(s) else ''
    if nxt == '(':
        j = skip_group(s, i + 2, '(', ')')
        return s[i:j], True, j
    if nxt == '{':
        j = skip_group(s, i + 2, '{', '}')
        return s[i:j], True, j
    if nxt.isalpha() or nxt == '_':
        j = i + 1
        while j < len(s) and (s[j].isalnum() or s[j] == '_'):
            j += 1
        return s[i:j], True, j
    if nxt and (nxt.isdigit() or nxt in '@*#?$!-'):
        return s[i:i + 2], True, i + 2
    return '$', False, i + 1


def lex_dquote(s, i):
    """From just after `"`: return (text, opaque, next index)."""
    buf, opaque, n = [], False, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            return ''.join(buf), opaque, i + 1
        if c == '\\' and i + 1 < n:
            if s[i + 1] in '$`"\\':
                buf.append(s[i + 1])
                i += 2
                continue
            if s[i + 1] == '\n':
                i += 2
                continue
        if c == '`':
            j = skip_backtick(s, i + 1)
            buf.append(s[i:j])
            opaque, i = True, j
            continue
        if c == '$':
            text, op, i = dollar(s, i)
            buf.append(text)
            opaque = opaque or op
            continue
        buf.append(c)
        i += 1
    raise ParseError('unterminated double quote')


def lex_word(s, i):
    buf, opaque, quoted, n = [], False, False, len(s)
    while i < n:
        c = s[i]
        if c in WORD_END:
            break
        if c == '\\':
            if i + 1 >= n:
                buf.append('\\')
                i += 1
                break
            if s[i + 1] != '\n':
                buf.append(s[i + 1])
                quoted = True
            i += 2
            continue
        if c == "'":
            j = skip_single(s, i + 1)
            buf.append(s[i + 1:j - 1])
            quoted, i = True, j
            continue
        if c == '"':
            text, op, i = lex_dquote(s, i + 1)
            buf.append(text)
            opaque, quoted = opaque or op, True
            continue
        if c == '`':
            j = skip_backtick(s, i + 1)
            buf.append(s[i:j])
            opaque, i = True, j
            continue
        if c == '$':
            if s.startswith("$'", i):
                j = skip_ansi(s, i + 2)
                buf.append(s[i + 2:j - 1])
                quoted, i = True, j
                continue
            if s.startswith('$"', i):
                text, op, i = lex_dquote(s, i + 2)
                buf.append(text)
                opaque, quoted = opaque or op, True
                continue
            text, op, i = dollar(s, i)
            buf.append(text)
            opaque = opaque or op
            continue
        buf.append(c)
        i += 1
    return Word(''.join(buf), opaque, quoted), i


def consume_heredocs(s, i, pending):
    """Skip heredoc bodies that start at `s[i]`. A missing terminator makes the body run to the end."""
    n = len(s)
    for delim, strip_tabs in pending:
        while True:
            if i >= n:
                return n
            j = s.find('\n', i)
            line = s[i:] if j < 0 else s[i:j]
            i = n if j < 0 else j + 1
            if (line.lstrip('\t') if strip_tabs else line) == delim:
                break
    return i


def lex(s):
    """Token stream: ('word', Word) · ('redir', op, takes_target) · ('op', ch)."""
    toks, pending, depth, i, n = [], [], 0, 0, len(s)
    while i < n:
        c = s[i]
        if c in BLANK:
            i += 1
            continue
        if c == '\\' and s.startswith('\\\n', i):
            i += 2
            continue
        if c == '\n':
            toks.append(('op', '\n'))
            i += 1
            if pending:
                i, pending = consume_heredocs(s, i, pending), []
            continue
        if c == '#':
            j = s.find('\n', i)
            i = n if j < 0 else j
            continue
        if s.startswith('((', i):
            j = skip_group(s, i + 2, '(', ')', depth=2)
            toks.append(('word', Word(s[i:j], opaque=True)))
            i = j
            continue
        if c in '<>' and s.startswith('(', i + 1):
            j = skip_group(s, i + 2, '(', ')')
            toks.append(('word', Word(s[i:j], opaque=True)))
            i = j
            continue
        if s.startswith('<<<', i):
            toks.append(('redir', '<<<', True))
            i += 3
            continue
        if s.startswith('<<', i):
            strip_tabs = s.startswith('<<-', i)
            i += 3 if strip_tabs else 2
            while i < n and s[i] in ' \t':
                i += 1
            delim, i = lex_word(s, i)
            if not delim.text and not delim.quoted:
                raise ParseError('missing heredoc delimiter')
            pending.append((delim.text, strip_tabs))
            continue
        if c in '<>' or s.startswith('&>', i):
            m = re.match(r'&>>|&>|>>|>\||>&|<&|<>|>|<', s[i:])
            toks.append(('redir', m.group(0), True))
            i += len(m.group(0))
            continue
        if c in ';&|()':
            if c == '(':
                depth += 1
            elif c == ')':
                depth = max(0, depth - 1)
            toks.append(('op', c))
            i += 1
            continue
        word, i = lex_word(s, i)
        if not word.quoted and not word.opaque and word.text.isdigit() and i < n and s[i] in '<>':
            continue  # fd number of a redirection (`2>&1`)
        toks.append(('word', word))
    if depth:
        raise ParseError('unterminated (')
    return toks


def parse(command):
    """Command string → list of segments (lists of Word), redirections and heredoc bodies removed."""
    segments, cur, drop = [], [], False
    for tok in lex(command):
        if tok[0] == 'word':
            if drop:
                drop = False
            else:
                cur.append(tok[1])
        elif tok[0] == 'redir':
            drop = tok[2]
        else:
            drop = False
            if cur:
                segments.append(cur)
                cur = []
    if cur:
        segments.append(cur)
    return segments


# ── target checkout ──
def strip_prefix(words):
    k = 0
    while k < len(words):
        t = words[k].text
        if '=' in t or t in PREFIX_WORDS or t in RESERVED:
            k += 1
            continue
        break
    return words[k:]


def resolve(base, word):
    if word is None or word.opaque or not word.text:
        return None
    p = word.text
    if p == '~' or p.startswith('~/'):
        p = os.path.expanduser('~') + p[1:]
    elif p.startswith('~'):
        return None
    if not os.path.isabs(p):
        p = os.path.join(base, p)
    return os.path.normpath(p)


def cd_target(args):
    k = 0
    while k < len(args) and args[k].text in ('-L', '-P', '-e', '-@', '-n', '--'):
        k += 1
    if k >= len(args) or args[k].text == '-' or args[k].text[:1] in '+-':
        return None
    return args[k]


def git_target(args, cur, origin):
    """git global options → (target dir, git dir or None, index of the subcommand)."""
    d, git_dir, work_tree, k = cur, None, None, 0
    while k < len(args):
        t = args[k].text
        val = args[k + 1] if k + 1 < len(args) else None
        if t == '-C':
            d = resolve(d, val) or origin
            k += 2
        elif t in ('--git-dir', '--work-tree'):
            path = resolve(d, val)
            if t == '--git-dir':
                git_dir = path
            else:
                work_tree = path
            k += 2
        elif t.startswith('--git-dir=') or t.startswith('--work-tree='):
            name, _, value = t.partition('=')
            path = resolve(d, Word(value, args[k].opaque))
            if name == '--git-dir':
                git_dir = path
            else:
                work_tree = path
            k += 1
        elif t in ('-c', '--namespace', '--exec-path'):
            k += 2
        elif t.startswith('-'):
            k += 1
        else:
            break
    return (work_tree or d), git_dir, k


def analyze(command, cwd):
    """Segments with their target checkout: [{seg, dir, argv, opaque, git_dir?}]."""
    records, cur = [], cwd
    for n, words in enumerate(parse(command), 1):
        rec = {'seg': n, 'dir': cur, 'argv': [w.text for w in words], 'opaque': any(w.opaque for w in words)}
        body = strip_prefix(words)
        exe = os.path.basename(body[0].text) if body else ''
        if exe in ('cd', 'pushd'):
            cur = resolve(cur, cd_target(body[1:])) or cwd
        elif exe == 'popd':
            cur = cwd
        elif exe == 'git':
            target, git_dir, _ = git_target(body[1:], cur, cwd)
            rec['dir'] = target
            if git_dir:
                rec['git_dir'] = git_dir
        rec['_body'] = body
        records.append(rec)
    return records


# ── rule engine ──
class Branches:
    def __init__(self):
        self.cache = {}

    def of(self, rec):
        key = (rec['dir'], rec.get('git_dir'))
        if key not in self.cache:
            cmd = (['git', '--git-dir=' + key[1]] if key[1] else ['git', '-C', key[0]])
            try:
                r = subprocess.run(cmd + ['rev-parse', '--abbrev-ref', 'HEAD'],
                                   capture_output=True, text=True, timeout=10)
                self.cache[key] = r.stdout.strip() if r.returncode == 0 else ''
            except Exception:
                self.cache[key] = ''
        return self.cache[key]


def dst_of(refspec):
    dst = refspec.split(':')[-1] if ':' in refspec else refspec
    return dst[len('refs/heads/'):] if dst.startswith('refs/heads/') else dst


def is_main_ref(refspec):
    return dst_of(refspec.lstrip('+')) in PROTECTED


def rule_gh(args):
    pos, method, k = [], 'GET', 0
    while k < len(args):
        t = args[k]
        if t in ('-R', '--repo', '--hostname', '-f', '-F', '--field', '--raw-field', '-H', '--header',
                 '-q', '--jq', '-t', '--template', '--input', '-p', '--preview', '--cache'):
            k += 2
            continue
        if t in ('-X', '--method'):
            if k + 1 < len(args):
                method = args[k + 1].upper()
            k += 2
            continue
        if t.startswith('--method='):
            method = t.split('=', 1)[1].upper()
        elif not t.startswith('-'):
            pos.append(t)
        k += 1
    if pos[:2] == ['pr', 'merge']:
        return '`gh pr merge` — PR 병합은 전수 게이트·〈N〉 재실측을 건너뛴다'
    if pos[:1] == ['api'] and len(pos) > 1 and method == 'PUT' and API_MERGE.search(pos[1]):
        return '`gh api -X PUT …/pulls/N/merge` — PR 병합은 전수 게이트·〈N〉 재실측을 건너뛴다'
    return None


def rule_push(args, branch, subagent):
    force = targets_main = targets_product = deleting = bulk = npos = 0
    k = 0
    while k < len(args):
        tok = args[k]
        k += 1
        if tok in ('-o', '--push-option', '--receive-pack', '--exec'):
            k += 1
        elif tok in ('--force', '-f', '--force-with-lease', '--force-if-includes') or tok.startswith('--force-with-lease='):
            force = 1
        elif tok in ('--delete', '-d'):
            deleting = 1
        elif tok in ('--all', '--mirror'):
            bulk = 1
        elif re.fullmatch(r'-[A-Za-z]+', tok):
            force = force or int('f' in tok)
            deleting = deleting or int('d' in tok)
        elif tok.startswith('-'):
            pass
        else:
            npos += 1
            refspec = tok[1:] if tok.startswith('+') else tok
            if tok.startswith('+'):
                force = 1
            if npos >= 2 and branch:
                parts = [branch if p in ('HEAD', '@') else p for p in refspec.split(':')]
                refspec = ':'.join(parts)
            if is_main_ref(refspec):
                targets_main = 1
            if dst_of(refspec) == 'product':
                targets_product = 1
            if tok.startswith(':'):
                deleting = 1
    on_main = branch in PROTECTED
    if targets_product or bulk or (npos <= 1 and branch == 'product'):
        return 'product 직접 push 및 전체 브랜치 push 금지 — develop PR을 사람이 병합한다'
    if deleting and targets_main:
        return f'{LABEL} 원격 삭제 금지'
    if force and targets_main:
        return f'{LABEL} 로 강제 푸시(`--force`/`-f`/`--force-with-lease`) — 남의 커밋을 덮는다'
    if npos <= 1 and on_main and force:
        return f'현재 브랜치가 `{branch}` 인데 refspec 없는 강제 push — {LABEL} 가 그대로 덮인다'
    if targets_main and subagent:
        return f'레인(서브에이전트)이 {LABEL} 로 push — 보호 브랜치는 오케스트레이터 한 자리에서만 움직인다(rules §2-1·§4-2)'
    if npos <= 1 and on_main and subagent:
        return f'레인(서브에이전트)이 `{branch}` 에서 refspec 없는 push — {LABEL} 가 그대로 나간다'
    return None


def rule_merge(args, branch):
    if branch == 'product':
        return 'product 로컬 병합 금지 — develop PR을 사람이 병합한다'
    if branch in PROTECTED and '--ff-only' not in args:
        return (f'현재 브랜치가 `{branch}` 인 상태의 `git merge`(--ff-only 없음) — 보호 브랜치는 전수 green ＋ '
                '〈N〉 재실측 뒤 `git merge --ff-only <레인>` 로만 움직인다')
    return None


def rule_pull(args, branch):
    bad = [t for t in args if t in ('--no-ff', '--no-rebase', '--rebase=false', '--ff=false')]
    if branch in PROTECTED and bad:
        return (f'현재 브랜치가 `{branch}` 인 상태의 `git pull {bad[0]}` — 병합 커밋이 게이트 밖에서 생긴다 · '
                '출구는 `git pull --ff-only` 또는 `git pull --rebase`')
    return None


def rule_branch(args):
    names = set(PROTECTED) | {'refs/heads/' + b for b in PROTECTED}
    if any(t in ('-D', '-d', '--delete') for t in args) and any(t in names for t in args if not t.startswith('-')):
        return f'`git branch -D` 로 {LABEL} 삭제 — 기준 브랜치를 지운다'
    return None


def judge(command, records, subagent, branches):
    flat = command.replace('\r', ' ').replace('\n', ' ; ')
    if RESEED.search(flat):
        return None, ('⛔ 차단(H3 git-guard ⑹) — COLAB_RESEED_ACK_NONEMPTY·COLAB_RESEED_ACK_BASIS 는 에이전트가 채우지 '
                      '않는다. 비어 있지 않은 dev 삭제는 사용자가 정지 게이트의 표별 계수를 보고 명시 GO 를 준 뒤 사용자 '
                      '터미널에서 넘긴다(.agents/rules/deploy.md 11번 증보). 훅을 비활성화하지 않는다.')
    for rec in records:
        body = rec['_body']
        if not body:
            continue
        exe = os.path.basename(body[0].text)
        args = [w.text for w in body[1:]]
        reason = None
        if exe == 'gh':
            reason = rule_gh(args)
        elif exe == 'git':
            k = git_target(body[1:], rec['dir'], rec['dir'])[2]
            sub, rest = (args[k], args[k + 1:]) if k < len(args) else ('', [])
            if sub == 'push':
                reason = rule_push(rest, branches.of(rec), subagent)
            elif sub == 'merge':
                reason = rule_merge(rest, branches.of(rec))
            elif sub == 'pull':
                reason = rule_pull(rest, branches.of(rec))
            elif sub == 'branch':
                reason = rule_branch(rest)
        if reason:
            return reason, None
    return None, None


def run(payload, out, err):
    tool = payload.get('tool_name') if isinstance(payload, dict) else None
    ti = payload.get('tool_input') if isinstance(payload, dict) else None
    command = ti.get('command') if isinstance(ti, dict) else None
    if tool != 'Bash' or not isinstance(command, str) or not command:
        out.write('parsed\n{"end":0}\n')
        return 0
    cwd = payload.get('cwd') if isinstance(payload.get('cwd'), str) else os.getcwd()
    try:
        records = analyze(command, cwd)
    except ParseError as exc:
        out.write(f'fallback {exc}\n')
        return 0
    lines = ['parsed']
    for rec in records:
        public = {key: rec[key] for key in ('seg', 'dir', 'argv', 'opaque', 'git_dir') if key in rec}
        lines.append(json.dumps(public, ensure_ascii=False, separators=(',', ':')))
    lines.append(json.dumps({'end': len(records)}, separators=(',', ':')))
    out.write('\n'.join(lines) + '\n')
    out.flush()
    reason, raw = judge(command, records, bool(payload.get('agent_id')), Branches())
    if raw:
        err.write(raw + '\n')
        return 2
    if reason:
        err.write(f'⛔ 차단(H3 git-guard) — {reason} · 이 자리는 오케스트레이터의 승인된 실행 경로로 인계한다. '
                  '훅을 비활성화하지 않는다.\n')
        return 2
    return 0


def main():
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            sys.stdout.write('fallback payload is not an object\n')
            return 0
        return run(payload, sys.stdout, sys.stderr)
    except RecursionError:
        sys.stdout.write('fallback nesting too deep\n')
        return 0
    except Exception:  # noqa: BLE001 — any crash is a parser failure; git-guard.sh falls back quietly
        return 3


if __name__ == '__main__':
    sys.exit(main())
