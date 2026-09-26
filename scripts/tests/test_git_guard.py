"""H3 git-guard — 공백 경로 `-C` · 대상 checkout · heredoc/인용 · argv 형태 · 폴백.

spec `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-20260925.md` §4.1 (V1–V6 · A1 ⑴–⑸).
hook 수준 시험은 `.claude/hooks/git-guard.sh` shim 을 직접 부른다(bridge 는 cwd 를 ROOT 로 고정한다).
"""
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / '.claude/hooks/git-guard.sh'
PARSER = ROOT / 'scripts/harness/hooks/git_guard_parse.py'
DENY = '⛔ 차단(H3 git-guard)'
FALLBACK = 'git-guard: parser fallback:'
END = re.compile(r'^\{"end":([0-9]+)\}$')


def load_parser():
    if not PARSER.is_file():
        raise AssertionError(f'parser module missing: {PARSER}')
    spec = importlib.util.spec_from_file_location('git_guard_parse_under_test', PARSER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hook_env():
    env = dict(os.environ)
    for key in ('COLAB_HOOKS', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'):
        env.pop(key, None)
    return env


def payload(command, cwd, agent=False):
    data = {'session_id': 'test', 'transcript_path': '/dev/null', 'cwd': str(cwd),
            'hook_event_name': 'PreToolUse', 'tool_name': 'Bash',
            'tool_input': {'command': command}, 'tool_use_id': 't1'}
    if agent:
        data.update(agent_id='agent-x', agent_type='lane-worker')
    return data


def run_hook(command, cwd, agent=False, hook=HOOK):
    return subprocess.run(['bash', str(hook)], input=json.dumps(payload(command, cwd, agent)),
                          text=True, capture_output=True, env=hook_env(), timeout=60)


def bash_n(command):
    return subprocess.run(['bash', '-n'], input=command, text=True, capture_output=True).returncode


@unittest.skipIf(os.name == 'nt', 'Bash hook integration requires WSL')
class GitGuardFixture(unittest.TestCase):
    """공백 포함 경로의 저장소 — 메인 checkout = feature · 두 번째 checkout(`dev co`) = develop."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        base = Path(cls._tmp.name) / 'co lab'
        cls.repo = base / 'repo'
        cls.devco = base / 'dev co'
        cls.repo.mkdir(parents=True)
        git = ['git', '-C', str(cls.repo)]
        env = hook_env()
        subprocess.run(git + ['init', '-q', '-b', 'feature'], check=True, env=env)
        subprocess.run(git + ['-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                              'commit', '-q', '--allow-empty', '-m', 'init'], check=True, env=env)
        subprocess.run(git + ['branch', 'develop'], check=True, env=env)
        subprocess.run(git + ['worktree', 'add', '-q', str(cls.devco), 'develop'], check=True, env=env)
        for path, branch in ((cls.repo, 'feature'), (cls.devco, 'develop')):
            actual = subprocess.run(['git', '-C', str(path), 'rev-parse', '--abbrev-ref', 'HEAD'],
                                    text=True, capture_output=True, check=True, env=env).stdout.strip()
            if actual != branch:
                raise AssertionError(f'fixture branch {path}: {actual} != {branch}')

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def expect(self, cases, cwd, hook=HOOK):
        for command, agent, expected in cases:
            with self.subTest(command=command, agent=agent, cwd=str(cwd)):
                result = run_hook(command, cwd, agent, hook)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertNotIn(FALLBACK, result.stderr)
                if expected == 2:
                    self.assertIn(DENY, result.stderr)
                else:
                    self.assertEqual(result.stderr, '')


class SpacedCheckoutTests(GitGuardFixture):
    """V1 — 공백 경로 `-C "<…>"`·`-C '<…>'` 에서도 규칙 ⑴–⑸·product 가 걸린다."""

    def test_rules_hold_through_quoted_spaced_dash_c(self):
        for quote in ('"', "'"):
            d = f'{quote}{self.devco}{quote}'
            self.expect([
                (f'git -C {d} push --force origin develop', False, 2),
                (f'git -C {d} branch -D develop', False, 2),
                (f'git -C {d} push origin develop', True, 2),
                (f'git -C {d} push origin main', True, 2),
                (f'git -C {d} merge feature', False, 2),
                (f'git -C {d} push origin product', False, 2),
            ], self.devco)

    def test_allowed_forms_pass_silently(self):
        r = f'"{self.repo}"'
        self.expect([
            (f'git -C {r} push origin feature', False, 0),
            (f'git -C {r} merge --ff-only develop', False, 0),
            (f'git -C {r} pull --rebase', False, 0),
            (f'git -C {r} worktree add ../wt2 -b other', False, 0),
            (f'git -C {r} push origin --delete feature', False, 0),
            ('git push origin feature', True, 0),
            ('git merge --ff-only develop', True, 0),
        ], self.repo)


class TargetCheckoutTests(GitGuardFixture):
    """V2 — 판정 branch = 명령이 실제로 겨누는 checkout(payload cwd 가 아니다)."""

    def test_target_checkout_decides_branch(self):
        d, r = f'"{self.devco}"', f'"{self.repo}"'
        self.expect([
            (f'git -C {d} merge feature', False, 2),
            (f'cd {d} && git merge feature', False, 2),
            (f'cd {d} && git push', True, 2),
            (f'git -C {r} merge feature', False, 0),
            (f'cd {r} && git merge feature', False, 0),
            (f'cd {r} && git push', True, 0),
            (f'git --git-dir={d}/.git --work-tree={d} merge feature', False, 2),
            (f'git --git-dir {d}/.git --work-tree {d} merge feature', False, 2),
            (f'pushd {d} && git merge feature', False, 2),
            (f'( cd {d} && git merge feature )', False, 2),
        ], self.repo)

    def test_real_git_dir_path_also_resolves(self):
        git_dir = subprocess.run(['git', '-C', str(self.devco), 'rev-parse', '--absolute-git-dir'],
                                 text=True, capture_output=True, check=True, env=hook_env()).stdout.strip()
        self.expect([(f'git --git-dir="{git_dir}" --work-tree="{self.devco}" merge feature', False, 2)],
                    self.repo)


class QuotedTextTests(GitGuardFixture):
    """V3 — heredoc 본문(종결·미종결)·인용 인자 안 문구는 명령이 아니다."""

    def test_text_inside_heredoc_and_quotes_is_not_a_command(self):
        self.expect([
            ("cat > note.md <<'EOF'\ngit merge --no-ff x\ngh pr merge 1\ngit push --force origin develop\nEOF", False, 0),
            ("cat > note.md <<'EOF'\ngit push --force origin develop\n", False, 0),
            ('grep -E "git merge|gh pr merge" f', False, 0),
            ('git commit -m "gh pr merge note; git push -f origin develop"', False, 0),
            ('git commit -m "제목\n\nCo-Authored-By: X <x@y>"', False, 0),
            ('python3 - <<EOF\nprint("git merge --no-ff x; gh pr merge 2")\nEOF', False, 0),
            ("cat<<EOF\ngit merge --no-ff x\nEOF", False, 0),
            ("cat <<-EOF\n\tgit merge --no-ff x\n\tEOF\ngit status", False, 0),
        ], self.devco)

    def test_command_before_unterminated_heredoc_is_still_parsed(self):
        self.expect([(f'git -C "{self.devco}" push -f origin develop <<EOF', False, 2),
                     ("cat <<'EOF'\nbody\nEOF\ngit merge --no-ff feature", False, 2)], self.devco)


class ArgvFormTests(GitGuardFixture):
    """V4 — 기존 열거 ⑴–⑸ 의 다른 argv 형태."""

    def test_gh_global_flags_and_api_merge(self):
        self.expect([
            ('gh -R o/r pr merge 1', False, 2),
            ('gh --repo o/r pr merge', False, 2),
            ('gh --repo=o/r pr merge 3', False, 2),
            ('gh api -X PUT repos/o/r/pulls/1/merge', False, 2),
            ('gh api --method put repos/o/r/pulls/1/merge/', False, 2),
            ("gh api -X PUT 'repos/o/r/pulls/1/merge?x=1'", False, 2),
            ('gh api --method=PUT /repos/o/r/pulls/12/merge', False, 2),
            ('gh api repos/o/r/pulls/1/merge', False, 0),
            ('gh api -X GET repos/o/r/pulls/1/merge', False, 0),
            ('gh api -X PUT repos/o/r/pulls/1/requested_reviewers', False, 0),
            ('gh pr view 1', False, 0),
        ], self.repo)

    def test_bundled_force_and_head_refspec(self):
        self.expect([
            ('git push -fu origin develop', False, 2),
            ('git push -uf origin develop', False, 2),
            ('git push origin HEAD', True, 2),
            ('git push origin @', True, 2),
            ('git push origin HEAD:develop', True, 2),
            ('git push origin HEAD', False, 0),
            ('git push origin +HEAD', False, 2),
            ('git push -o ci.skip origin feature', False, 0),
        ], self.devco)
        self.expect([('git push origin HEAD', True, 0), ('git push -u origin HEAD', True, 0)], self.repo)

    def test_non_ff_pull_on_protected_branch(self):
        self.expect([
            ('git pull --no-ff origin develop', False, 2),
            ('git pull --no-rebase', False, 2),
            ('git pull --rebase=false', False, 2),
            ('git pull --ff=false', False, 2),
            ('git pull', False, 0),
            ('git pull --ff-only', False, 0),
            ('git pull --rebase', False, 0),
        ], self.devco)
        self.expect([('git pull --no-ff', False, 0)], self.repo)


class FallbackTests(GitGuardFixture):
    """V5 — 해석기 폴백은 `bash -n` 거부 입력과 해석기 결함에서만 · crash 0 · stderr 1줄."""

    FALLBACK_INPUTS = (('git push --force origin develop "x', 2),
                       ('echo "unterminated', 0),
                       ('echo $(git status', 0))

    def test_fallback_inputs_are_exactly_bash_syntax_errors(self):
        parser = load_parser()
        for command, expected in self.FALLBACK_INPUTS:
            with self.subTest(command=command):
                self.assertNotEqual(bash_n(command), 0)
                with self.assertRaises(parser.ParseError):
                    parser.parse(command)
                result = run_hook(command, self.devco)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(result.stderr.count(FALLBACK), 1, result.stderr)
        # 미종결 heredoc 은 bash 가 받아들이므로 fallback fixture 가 될 수 없다.
        unterminated = "cat > note.md <<'EOF'\ngit push --force origin develop\n"
        self.assertEqual(bash_n(unterminated), 0)
        parser.parse(unterminated)

    def test_parser_falls_back_only_where_bash_rejects(self):
        parser = load_parser()
        corpus = [
            'git status', "cat > n <<'EOF'\nx\nEOF", 'echo $((1<<2))', 'echo $(echo ")")',
            'case x in a) git status;; esac', 'if git merge x; then :; fi', 'a=1 b=2 git status',
            'echo `date`', "echo $'a\\'b'", 'echo ${X:-y}', 'cat <(git log) >(wc)', '(( x = 1 << 2 ))',
        ]
        for command in corpus:
            with self.subTest(command=command):
                try:
                    parser.parse(command)
                except parser.ParseError:
                    self.assertNotEqual(bash_n(command), 0, command)
                else:
                    self.assertEqual(bash_n(command), 0, command)


@unittest.skipIf(os.name == 'nt', 'Bash hook integration requires WSL')
class FaultInjectionTests(unittest.TestCase):
    """V5 — hook 폴더 tempdir 복사본의 해석기를 망가뜨려도 폴백(현행 규칙) · crash 0."""

    STUBS = {
        'a-missing': None,
        'b-exit3': 'import sys\nsys.exit(3)\n',
        'c-first-line-only': 'print("parsed")\n',
        'd-record-then-exit3': ('import sys\nprint("parsed")\n'
                                'print(\'{"seg":1,"dir":"/","argv":["git"],"opaque":false}\')\n'
                                'sys.stdout.flush()\nsys.exit(3)\n'),
        'e-wrong-record': 'print("parsed")\nprint(\'{"x":1}\')\nprint(\'{"end":1}\')\n',
        'f-no-end-marker': ('print("parsed")\n'
                            'print(\'{"seg":1,"dir":"/","argv":["git","status"],"opaque":false}\')\n'),
    }

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'copy root'
        ignore = shutil.ignore_patterns('__pycache__')
        shutil.copytree(ROOT / 'scripts/harness', self.root / 'scripts/harness', ignore=ignore)
        shutil.copytree(ROOT / '.claude/hooks', self.root / '.claude/hooks', ignore=ignore)
        self.work = Path(self.tmp.name) / 'work'
        subprocess.run(['git', 'init', '-q', '-b', 'develop', str(self.work)], check=True, env=hook_env())

    def test_broken_parser_falls_back_to_current_rules(self):
        parser = self.root / 'scripts/harness/hooks/git_guard_parse.py'
        hook = self.root / '.claude/hooks/git-guard.sh'
        self.assertTrue(parser.is_file(), 'parser must exist before it can be broken')
        for name, stub in self.STUBS.items():
            if stub is None:
                parser.unlink(missing_ok=True)
            else:
                parser.write_text(stub, encoding='utf-8')
            for command, expected in (('git push --force origin develop', 2), ('git status', 0)):
                with self.subTest(stub=name, command=command):
                    result = run_hook(command, self.work, hook=hook)
                    self.assertEqual(result.returncode, expected, result.stderr)
                    self.assertEqual(result.stderr.count(FALLBACK), 1, result.stderr)
                    self.assertNotIn('hook readiness failure', result.stderr)
                    self.assertNotIn('Traceback', result.stderr)
                    if expected == 2:
                        self.assertIn(DENY, result.stderr)


@unittest.skipIf(os.name == 'nt', 'Bash hook integration requires WSL')
class CorpusTests(GitGuardFixture):
    """실사용 corpus — `set -u` unbound(exit 1 = fail-open) 방지 · stderr 빈 문자열."""

    def test_everyday_commands_pass_silently(self):
        self.expect([
            ('git status', False, 0),
            ('git log --oneline -5', False, 0),
            ("git commit -F - <<'EOF'\n제목\n\n본문 git push --force origin develop\nEOF", False, 0),
            ('gh pr view 1', False, 0),
            ('git diff --stat', False, 0),
            ('ls -la | head -3 && echo done', False, 0),
        ], self.devco)

    def test_hook_script_is_valid_bash(self):
        result = subprocess.run(['bash', '-n', str(ROOT / 'scripts/harness/hooks/git-guard.sh')],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class ParserUnitTests(unittest.TestCase):
    """해석기 import 단위 시험 — tokenizer · 대상 dir · JSON lines · rev-parse 지연 평가."""

    @classmethod
    def setUpClass(cls):
        cls.p = load_parser()

    def argv(self, command):
        return [[w.text for w in seg] for seg in self.p.parse(command)]

    def dirs(self, command, cwd='/base'):
        return [(rec['argv'][0], rec['dir']) for rec in self.p.analyze(command, cwd)]

    def test_heredoc_bodies_are_excluded(self):
        self.assertEqual(self.argv("cat > n <<'EOF'\ngit merge x\nEOF\ngit status"),
                         [['cat'], ['git', 'status']])
        self.assertEqual(self.argv('cat <<EOF\ngit push -f origin develop\n'), [['cat']])
        self.assertEqual(self.argv('cat<<EOF\ngit merge x\nEOF'), [['cat']])
        self.assertEqual(self.argv('echo $((1<<2))\ngit status'), [['echo', '$((1<<2))'], ['git', 'status']])
        self.assertEqual(self.argv('cat <<< "git merge x" && git status'), [['cat'], ['git', 'status']])

    def test_quoted_operators_do_not_split(self):
        self.assertEqual(self.argv('echo "a|b;c\nd" && git status'), [['echo', 'a|b;c\nd'], ['git', 'status']])
        self.assertEqual(self.argv("echo 'x && y' | wc -l"), [['echo', 'x && y'], ['wc', '-l']])

    def test_redirections_are_removed(self):
        self.assertEqual(self.argv('git status > out.txt 2>&1'), [['git', 'status']])
        self.assertEqual(self.argv('git status &>log; cat<in'), [['git', 'status'], ['cat']])
        self.assertEqual(self.argv('>out git push origin x'), [['git', 'push', 'origin', 'x']])

    def test_command_substitution_is_one_opaque_token(self):
        segs = self.p.parse('echo $(echo ")") done')
        self.assertEqual([w.text for w in segs[0]], ['echo', '$(echo ")")', 'done'])
        self.assertEqual([w.opaque for w in segs[0]], [False, True, False])

    def test_target_dir_resolution(self):
        home = os.path.expanduser('~')
        self.assertEqual(self.dirs('git -C a -C b status'), [('git', '/base/a/b')])
        self.assertEqual(self.dirs('cd sub && git status'), [('cd', '/base'), ('git', '/base/sub')])
        self.assertEqual(self.dirs('cd ~/x && git status')[1], ('git', home + '/x'))
        self.assertEqual(self.dirs('git -C "$X" status'), [('git', '/base')])
        self.assertEqual(self.dirs('cd $X && git status')[1], ('git', '/base'))
        self.assertEqual(self.dirs('cd /o && cd - && git status')[2], ('git', '/base'))
        self.assertEqual(self.dirs('git --work-tree=/w status'), [('git', '/w')])

    def run_main(self, command, cwd='/base'):
        out, err = io.StringIO(), io.StringIO()
        rc = self.p.run(payload(command, cwd), out, err)
        return rc, out.getvalue().splitlines(), err.getvalue()

    def test_records_are_json_lines_with_end_marker(self):
        rc, lines, err = self.run_main('git commit -m "제목\n\nCo-Authored-By: X <x@y>" && git status')
        self.assertEqual((rc, err), (0, ''))
        self.assertEqual(lines[0], 'parsed')
        match = END.match(lines[-1])
        self.assertIsNotNone(match, lines)
        records = lines[1:-1]
        self.assertEqual(int(match.group(1)), len(records))
        self.assertTrue(all(line.startswith('{"seg":') for line in records), records)
        first = json.loads(records[0])
        self.assertEqual(first['argv'][:3], ['git', 'commit', '-m'])
        self.assertIn('\n\nCo-Authored-By', first['argv'][3])

    def test_parse_failure_prints_fallback_line(self):
        rc, lines, err = self.run_main('echo "open')
        self.assertEqual(rc, 0)
        self.assertTrue(lines[0].startswith('fallback '), lines)

    def test_rev_parse_runs_only_for_branch_rules_once_per_dir(self):
        def fake(args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout='feature\n', stderr='')
        for command, expected in (('git status', 0), ('git log --oneline -5', 0), ('gh pr view 1', 0),
                                  ('git push', 1), ('git push && git merge --ff-only x', 1),
                                  ('git push && git -C other push', 2)):
            with self.subTest(command=command), mock.patch.object(self.p.subprocess, 'run', side_effect=fake) as run:
                rc, _, _ = self.run_main(command, cwd=str(ROOT))
                self.assertEqual(rc, 0)
                calls = [c for c in run.call_args_list if 'rev-parse' in c.args[0]]
                self.assertEqual(len(calls), expected, run.call_args_list)


if __name__ == '__main__':
    unittest.main()
