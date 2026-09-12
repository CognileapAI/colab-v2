"""Negative evidence tests: never accept absent, stale or inconsistent reports."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile
import tomllib
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("bridge", Path(__file__).parents[1] / "agent-bridge.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class EnvironmentTests(unittest.TestCase):
    def test_non_login_tools_keep_control_flags_without_mutating_parent(self):
        with patch.dict(os.environ, {'PATH': '/usr/bin', 'COLAB_FIX_LANE': '1'}):
            env = bridge.tool_environment()
            self.assertIn(str(Path.home()/'.local/bin'), env['PATH'].split(os.pathsep))
            self.assertIn(str(Path.home()/'.npm-global/bin'), env['PATH'].split(os.pathsep))
            self.assertEqual(env['COLAB_FIX_LANE'], '1')
            self.assertEqual(os.environ['PATH'], '/usr/bin')


class AgentConfigurationTests(unittest.TestCase):
    def test_role_models_are_explicit_and_do_not_claim_parent_inheritance(self):
        expected = {
            'lane-worker': 'gpt-5.6-sol',
            'researcher': 'gpt-5.6-sol',
            'gate-runner': 'gpt-6-astra',
            'advisor': 'gpt-6-astra',
        }
        for role, model in expected.items():
            with self.subTest(role=role):
                config = tomllib.loads(
                    (bridge.ROOT/f'.codex/agents/{role}.toml').read_text(encoding='utf-8')
                )
                self.assertEqual(config.get('model'), model)
                instructions = config['developer_instructions'].lower()
                self.assertNotIn("inherit the parent's model", instructions)
                self.assertNotIn("inherit the parent's settings", instructions)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.report = {"schema": "colab-gate-summary/1", "tree": "abc",
                       "counts": {"green": 1, "red_판정": 0, "red_준비": 0},
                       "gates": [{"name": "contract-lint", "status": "green", "exit": 0}]}

    def test_valid_report(self):
        bridge.validate_report(self.report, ["contract-lint"], "abc")

    def test_rejects_missing_stale_and_malformed_evidence(self):
        mutations = [lambda d: d.clear(), lambda d: d.update(tree="old"),
                     lambda d: d.pop("counts"), lambda d: d.update(gates=[]),
                     lambda d: d["counts"].update(green=2),
                     lambda d: d["counts"].update(green=True),
                     lambda d: d["gates"][0].update(exit=1),
                     lambda d: d["gates"][0].update(state="red_준비"),
                     lambda d: d["gates"].append(copy.deepcopy(d["gates"][0]))]
        for mutate in mutations:
            data = copy.deepcopy(self.report)
            mutate(data)
            with self.subTest(data=data), self.assertRaises(ValueError):
                bridge.validate_report(data, ["contract-lint"], "abc")

    def test_unrelated_gate_does_not_prove_requested_gate(self):
        with self.assertRaises(ValueError):
            bridge.validate_report(self.report, ["frontend-test"], "abc")

    def test_readiness_failure_blocks_acceptance(self):
        self.report["counts"].update(green=0, red_준비=1)
        self.report["gates"][0].update(status="red_준비", exit=78)
        with self.assertRaises(ValueError):
            bridge.validate_report(self.report, ["contract-lint"], "abc")


class PatchTranslationTests(unittest.TestCase):
    def event(self, command):
        return {"hook_event_name": "PreToolUse", "cwd": str(bridge.ROOT),
                "tool_name": "apply_patch", "tool_input": {"command": command}}

    def test_all_targets_including_move_destination(self):
        patch = """*** Begin Patch
*** Add File: docs/a.md
+hello
*** Update File: frontend/src/old.ts
*** Move to: frontend/src/new.ts
@@
-old
+new
*** Delete File: frontend/test/example.test.ts
*** End Patch"""
        result = bridge.codex_payloads(self.event(patch))
        self.assertEqual([Path(x['tool_input']['file_path']).relative_to(bridge.ROOT).as_posix()
                          for x in result], ['docs/a.md', 'frontend/src/old.ts',
                                            'frontend/src/new.ts', 'frontend/test/example.test.ts'])

    def test_patch_provides_per_file_new_content_to_decision_guard(self):
        value = self.event('*** Begin Patch\n*** Update File: docs/other.md\n@@\n+unrelated\n*** Update File: dev-package/PLAN-SoT.md\n@@\n+| 〈9999999〉 | added decision |\n*** End Patch')
        payloads = bridge.codex_payloads(value)
        self.assertEqual(payloads[0]['tool_input']['new_string'], 'unrelated')
        self.assertEqual(payloads[1]['tool_input']['new_string'], '| 〈9999999〉 | added decision |')

    def test_escaping_move_rejected(self):
        with self.assertRaises(ValueError):
            bridge.codex_payloads(self.event('*** Begin Patch\n*** Update File: x\n*** Move to: ../x\n*** End Patch'))

    def test_empty_or_malformed_patch_rejected(self):
        for patch in ('', 'not a patch', '*** Begin Patch\n*** End Patch',
                      '*** Begin Patch\n*** Move to: x\n*** End Patch'):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                bridge.codex_payloads(self.event(patch))

    def test_added_header_text_is_not_an_edit(self):
        patch = '*** Begin Patch\n*** Add File: docs/example.md\n+*** Delete File: other\n*** End Patch'
        self.assertEqual(bridge.patch_paths(patch), ['docs/example.md'])


class LifecycleTests(unittest.TestCase):
    def event(self, name, **fields):
        return dict(cwd=str(bridge.ROOT), hook_event_name=name, **fields)

    @patch.object(bridge.subprocess, 'run')
    def test_stop_success_is_json_not_plain_text(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, 'H6 inspected\n', '')
        result = bridge.dispatch_event(self.event('SubagentStop', agent_type='researcher'))
        self.assertEqual(json.loads(json.dumps(result))['systemMessage'], 'H6 inspected')
        self.assertTrue(str(run.call_args.args[0][-1]).endswith('uncommitted-artifacts.sh'))

    @patch.object(bridge.subprocess, 'run')
    def test_stop_rejection_and_execution_error_do_not_pass(self, run):
        for rc in (1, 2, 78):
            run.return_value = subprocess.CompletedProcess([], rc, '', 'missing evidence')
            with self.subTest(rc=rc), self.assertRaises(ValueError):
                bridge.dispatch_event(self.event('SubagentStop', agent_type='lane-worker'))

    @patch.object(bridge.subprocess, 'run')
    def test_post_patch_css_feedback_reaches_context(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, '| CSS audit |', '')
        event = self.event('PostToolUse', tool_name='apply_patch', tool_input={
            'command': '*** Begin Patch\n*** Update File: frontend/src/shell/tokens.css\n@@\n-a\n+b\n*** End Patch'})
        result = bridge.dispatch_event(event)
        self.assertEqual(result['hookSpecificOutput']['hookEventName'], 'PostToolUse')
        self.assertIn('CSS audit', result['hookSpecificOutput']['additionalContext'])
        payload = json.loads(run.call_args.kwargs['input'])
        self.assertEqual(payload['tool_name'], 'Edit')
        self.assertTrue(payload['tool_input']['file_path'].endswith('tokens.css'))

    @patch.object(bridge.subprocess, 'run')
    def test_session_start_preserves_explicit_round_priority(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, 'mtime suggestion', '')
        result = bridge.dispatch_event(self.event('SessionStart', source='startup'))
        self.assertIn("user's selected round takes precedence", result['hookSpecificOutput']['additionalContext'])

    def test_missing_selector_and_unknown_event_rejected(self):
        for event in ('SubagentStop', 'SubagentStart', 'SessionStart', 'unknown'):
            with self.subTest(event=event), self.assertRaises(ValueError):
                bridge.dispatch_event(self.event(event))

    @patch.object(bridge.subprocess, 'run')
    def test_unrelated_role_does_not_run_lane_hook(self, run):
        self.assertEqual(bridge.dispatch_event(self.event('SubagentStop', agent_type='advisor')), {})
        run.assert_not_called()

    def test_all_source_skills_and_hook_matchers_are_checked(self):
        bridge.check()


@unittest.skipUnless(os.name == 'nt', 'native Windows launcher regression')
class WindowsLauncherTests(unittest.TestCase):
    def test_powershell5_closes_prompt_file_before_descendant_inherits_stdin(self):
        import time
        source = (bridge.ROOT/'scripts/dev.ps1').read_text(encoding='utf-8-sig')
        helper = source[source.index('function Invoke-LegacyNative('):source.index("if ($Tool -eq 'codex')")]
        for exit_code in (37, 0):
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory(prefix='colab descendant ') as directory:
                root = Path(directory)
                temporary = root/'temp'
                temporary.mkdir()
                child = root/'child.py'
                child.write_text(
                    "import subprocess,sys,pathlib\n"
                    "assert sys.stdin.buffer.read() == b'prompt\\r\\n'\n"
                    "subprocess.Popen([sys.executable,'-c',"
                    "'import time,pathlib,sys; time.sleep(3); pathlib.Path(sys.argv[1]).touch()',"
                    "str(pathlib.Path(__file__).with_suffix('.done'))],"
                    "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,"
                    "creationflags=subprocess.CREATE_NO_WINDOW)\n"
                    "print('stderr preserved',file=sys.stderr)\n"
                    "sys.exit(int(sys.argv[1]))\n", encoding='utf-8')
                harness = root/'harness.ps1'
                harness.write_text("$ErrorActionPreference='Stop'\n$hasPromptInput=$true\n$promptInput=@('prompt')\n"
                                   + helper + "\nexit (Invoke-LegacyNative (Get-Command python.exe).Source @($args[0],$args[1]))\n",
                                   encoding='utf-8-sig')
                try:
                    result = subprocess.run(['powershell','-NoProfile','-File',str(harness),str(child),str(exit_code)],
                                            cwd=root,env=dict(os.environ,TEMP=str(temporary),TMP=str(temporary)),
                                            capture_output=True,text=True,errors='replace',timeout=20)
                    self.assertFalse(child.with_suffix('.done').exists(), 'descendant must still be running')
                    self.assertEqual(result.returncode,exit_code,result.stdout+result.stderr)
                    self.assertIn('stderr preserved',result.stderr)
                    self.assertEqual(list(temporary.iterdir()), [])
                finally:
                    deadline = time.monotonic() + 10
                    while not child.with_suffix('.done').exists() and time.monotonic() < deadline:
                        time.sleep(0.1)

    def run_hook(self, cwd, payload, **controls):
        hooks = json.loads((bridge.ROOT/'.codex/hooks.json').read_text(encoding='utf-8'))
        command = hooks['hooks']['PreToolUse'][0]['hooks'][0]['commandWindows']
        env = dict(os.environ)
        for key in ('COLAB_HOOKS', 'COLAB_FIX_LANE', 'COLAB_ALLOW_TEST_EDIT'):
            env.pop(key, None)
        env.update(controls)
        return subprocess.run(['pwsh', '-NoProfile', '-Command', command],
                              cwd=cwd, input=json.dumps(dict(payload, cwd=str(cwd), hook_event_name='PreToolUse')),
                              capture_output=True, text=True, encoding='utf-8', env=env, timeout=60)

    def test_dev_entrypoint_transfers_control_environment_without_printing_values(self, shell="pwsh"):
        with tempfile.TemporaryDirectory(prefix='colab entry ') as directory:
            root = Path(directory)
            (root/'scripts').mkdir()
            (root/'scripts/dev.ps1').write_bytes((bridge.ROOT/'scripts/dev.ps1').read_bytes())
            (root/'scripts/agent-bridge.py').write_text(
                "import os,sys\n"
                "assert os.environ.get('COLAB_TASK_ID') == 'task-control-fixture'\n"
                "assert os.environ.get('COLAB_GATE_REPORT_DIR') == 'dev-package/reports/space path'\n"
                "assert os.environ.get('COLAB_FRONTEND_DIR') == 'frontend fixture'\n"
                "assert os.environ.get('COLAB_VISUAL_URLS') == 'http://127.0.0.1:5173/example'\n"
                "assert os.environ.get('COLAB_PLANNING_ROOT') == 'planning root fixture'\n"
                "assert os.environ.get('COLAB_PLANNING_HOME') == 'planning home fixture'\n"
                "assert 'COLAB_ALLOW_TEST_EDIT' not in os.environ\n"
                "assert sys.argv[1:] == ['run-tool','gate','--','contract-lint']\n"
                "print('controls verified without values')\n", encoding='utf-8')
            env = dict(os.environ, COLAB_TASK_ID='task-control-fixture',
                       COLAB_GATE_REPORT_DIR='dev-package/reports/space path',
                       COLAB_FRONTEND_DIR='frontend fixture', COLAB_VISUAL_URLS='http://127.0.0.1:5173/example',
                       COLAB_PLANNING_ROOT='planning root fixture', COLAB_PLANNING_HOME='planning home fixture')
            env.pop('COLAB_ALLOW_TEST_EDIT',None)
            result = subprocess.run([shell,'-NoProfile','-File',str(root/'scripts/dev.ps1'), 'gate', 'contract-lint'],
                                    cwd=root, env=env, text=True, capture_output=True, timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertNotIn('task-control-fixture', result.stdout)

    def test_powershell5_legacy_control_argument_preserves_json(self):
        self.test_dev_entrypoint_transfers_control_environment_without_printing_values(shell='powershell')

    def test_wsl_argument_envelope_preserves_literals_in_both_shells(self):
        arguments = ['batch', '{"text":"space value"}', 'el => el.textContent === "quoted"', '한글 공백']
        for shell in ('powershell', 'pwsh'):
            with self.subTest(shell=shell), tempfile.TemporaryDirectory(prefix='colab argv ') as directory:
                root = Path(directory)
                (root/'scripts').mkdir()
                (root/'scripts/dev.ps1').write_bytes((bridge.ROOT/'scripts/dev.ps1').read_bytes())
                expected = ['run-tool','browser','--',*arguments,'123']
                (root/'scripts/agent-bridge.py').write_text(
                    'import sys\nassert sys.argv[1:] == ' + repr(expected) + '\n', encoding='utf-8')
                # Enter through a PowerShell script to isolate the launcher boundary.
                literals = ','.join("'" + value.replace("'", "''") + "'" for value in arguments)
                harness = root/'harness.ps1'
                harness.write_text("$values = @(" + literals + ",123)\n& $PSScriptRoot/scripts/dev.ps1 browser @values\nexit $LASTEXITCODE\n", encoding='utf-8-sig')
                result = subprocess.run([shell,'-NoProfile','-File',str(harness)], cwd=root,
                                        text=True,capture_output=True,timeout=60)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_native_codex_arguments_preserved_in_both_shells(self):
        arguments = ['exec', '', 'space value', 'trailing slash\\', 'space slash\\', '{"text":"quoted"}', 'a\\\\"b', '한글']
        with tempfile.TemporaryDirectory(prefix='colab codex argv ') as directory:
            root = Path(directory)
            (root/'scripts').mkdir()
            (root/'scripts/dev.ps1').write_bytes((bridge.ROOT/'scripts/dev.ps1').read_bytes())
            compiler = root/'compile.ps1'
            compiler.write_text("Add-Type -TypeDefinition @'\n" +
                'using System; using System.Text; public class Probe { public static void Main(string[] args) { '
                'if (Array.IndexOf(args,"--version") >= 0) { Console.In.ReadToEnd(); Console.WriteLine("codex-cli 0.153.4"); return; } '
                'if(Array.IndexOf(args,"fail-probe") >= 0) { Console.Error.WriteLine("stderr preserved"); Environment.Exit(37); } foreach(string a in args) Console.WriteLine("ARG:"+Convert.ToBase64String(Encoding.UTF8.GetBytes(a))); if(Array.IndexOf(args,"-") >= 0) { var data = new System.IO.MemoryStream(); Console.OpenStandardInput().CopyTo(data); Console.WriteLine("STDIN:"+Convert.ToBase64String(data.ToArray())); } } }'
                + "\n'@ -OutputAssembly ($PSScriptRoot + '/codex.exe') -OutputType ConsoleApplication\n", encoding='utf-8-sig')
            compile_result = subprocess.run(['powershell','-NoProfile','-File',str(compiler)],cwd=root,text=True,capture_output=True)
            self.assertEqual(compile_result.returncode,0,compile_result.stderr)
            literals = ','.join("'" + value.replace("'", "''") + "'" for value in arguments)
            harness = root/'harness.ps1'
            harness.write_text(
                "function Get-Process { @() }\n"
                "function Get-ChildItem { [pscustomobject]@{ FullName=($PSScriptRoot + '/codex.exe'); LastWriteTimeUtc=[datetime]::UtcNow } }\n"
                "$values = @(" + literals + ")\nif ($args -contains 'failure') { $values += 'fail-probe' }\nif ($args -contains 'pipe') { $values += '-'; $text = if ($args -contains 'long') { [string][char]0xfeff + ('한글' * 40000) } else { '한글' }; $text, '', 'last line' | & $PSScriptRoot/scripts/dev.ps1 codex @values } else { & $PSScriptRoot/scripts/dev.ps1 codex @values }\nexit $LASTEXITCODE\n",encoding='utf-8-sig')
            import base64, hashlib
            for shell in ('powershell','pwsh'):
                with self.subTest(shell=shell):
                    result = subprocess.run([shell,'-NoProfile','-File',str(harness)],cwd=root,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=60)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    actual = [base64.b64decode(line[4:]).decode('utf-8') for line in result.stdout.splitlines() if line.startswith('ARG:')]
                    self.assertEqual(actual,['-C',str(root),*arguments])
                    piped = subprocess.run([shell,'-NoProfile','-File',str(harness),'pipe'],cwd=root,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=60)
                    self.assertEqual(piped.returncode,0,piped.stdout+piped.stderr)
                    payload = next(line[6:] for line in piped.stdout.splitlines() if line.startswith('STDIN:'))
                    self.assertEqual(base64.b64decode(payload), '한글\r\n\r\nlast line\r\n'.encode('utf-8'))
                    large = subprocess.run([shell,'-NoProfile','-File',str(harness),'pipe','long'],cwd=root,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=60)
                    self.assertEqual(large.returncode,0,large.stderr)
                    raw = base64.b64decode(next(line[6:] for line in large.stdout.splitlines() if line.startswith('STDIN:')))
                    expected_input = ('\ufeff' + '한글'*40000 + '\r\n\r\nlast line\r\n').encode('utf-8')
                    self.assertEqual(hashlib.sha256(raw).digest(),hashlib.sha256(expected_input).digest())
                    failed = subprocess.run([shell,'-NoProfile','-File',str(harness),'pipe','failure'],cwd=root,text=True,capture_output=True,timeout=60)
                    self.assertEqual(failed.returncode,37)
                    self.assertIn('stderr preserved',failed.stderr)

    def test_wsl_pipeline_preserves_utf8_without_bom_in_both_shells(self):
        with tempfile.TemporaryDirectory(prefix='colab stdin ') as directory:
            root = Path(directory)
            (root/'scripts').mkdir()
            (root/'scripts/dev.ps1').write_bytes((bridge.ROOT/'scripts/dev.ps1').read_bytes())
            (root/'scripts/agent-bridge.py').write_text('import sys; print(sys.stdin.buffer.read().hex())',encoding='utf-8')
            harness = root/'harness.ps1'
            harness.write_text("'한글', '', 'last line' | & $PSScriptRoot/scripts/dev.ps1 bridge doctor\nexit $LASTEXITCODE\n",encoding='utf-8-sig')
            for shell in ('powershell','pwsh'):
                with self.subTest(shell=shell):
                    result = subprocess.run([shell,'-NoProfile','-File',str(harness)],cwd=root,text=True,capture_output=True,timeout=60)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertEqual(bytes.fromhex(result.stdout.strip()), '한글\r\n\r\nlast line\r\n'.encode('utf-8'))
            import hashlib
            (root/'scripts/agent-bridge.py').write_text('import sys,hashlib; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())',encoding='utf-8')
            harness.write_text("$text = [string][char]0xfeff + ('한글' * 40000)\n$text, '', 'last line' | & $PSScriptRoot/scripts/dev.ps1 bridge doctor\nexit $LASTEXITCODE\n",encoding='utf-8-sig')
            expected_input = ('\ufeff' + '한글'*40000 + '\r\n\r\nlast line\r\n').encode('utf-8')
            for shell in ('powershell','pwsh'):
                large = subprocess.run([shell,'-NoProfile','-File',str(harness)],cwd=root,text=True,capture_output=True,timeout=60)
                self.assertEqual(large.returncode,0,large.stderr)
                self.assertEqual(large.stdout.strip(),hashlib.sha256(expected_input).hexdigest())
            harness.write_text("function Get-Command { $null }\n'한글' | & $PSScriptRoot/scripts/dev.ps1 bridge doctor\n",encoding='utf-8-sig')
            missing = subprocess.run(['powershell','-NoProfile','-File',str(harness)],cwd=root,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=60)
            self.assertNotEqual(missing.returncode,0)
            self.assertIn('Windows Python is required',missing.stderr)

    def test_codex_pipeline_prompt_reaches_only_selected_executable(self):
        with tempfile.TemporaryDirectory(prefix='colab prompt ') as directory:
            root = Path(directory)
            (root/'scripts').mkdir()
            (root/'scripts/dev.ps1').write_bytes((bridge.ROOT/'scripts/dev.ps1').read_bytes())
            fake = root/'fake-codex.ps1'
            fake.write_text(
                "if ($args -contains '--version') { $discard = @($input); Write-Output 'codex-cli 0.153.4'; exit 0 }\n"
                '$received = @($input) -join "`n"\n'
                'if ($received -ne "first line`n`nlast line") { Write-Error "prompt missing or changed"; exit 1 }\n'
                "Write-Output 'prompt preserved'; exit 0\n", encoding='utf-8')
            harness = root/'harness.ps1'
            harness.write_text(
                "$env:COLAB_FAKE_CANDIDATE = $args[0]\n"
                "function Get-Process { @() }\n"
                "function Get-ChildItem { [pscustomobject]@{ FullName=$env:COLAB_FAKE_CANDIDATE; LastWriteTimeUtc=[datetime]::UtcNow } }\n"
                "'first line', '', 'last line' | & $args[1] codex exec --json -\n",encoding='utf-8')
            result = subprocess.run(['pwsh','-NoProfile','-File',str(harness),str(fake),str(root/'scripts/dev.ps1')],
                                    cwd=root,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('prompt preserved',result.stdout)

    def test_subdirectory_safe_command_passes(self):
        result = self.run_hook(bridge.ROOT/'scripts', {'tool_name':'Bash', 'tool_input':{'command':'git status --short'}})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_native_fix_mode_and_exact_block_exit_survive_wsl(self):
        event = {'tool_name':'apply_patch', 'tool_input':{'command':
                 '*** Begin Patch\n*** Delete File: frontend/test/example.test.ts\n*** End Patch'}}
        result = self.run_hook(bridge.ROOT, event, COLAB_FIX_LANE='1')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('test-file-guard', result.stderr)

    def test_missing_git_root_is_block_not_launcher_error(self):
        with tempfile.TemporaryDirectory() as cwd:
            result = self.run_hook(cwd, {'tool_name':'Bash','tool_input':{'command':'git status'}})
        self.assertEqual(result.returncode, 2, result.stderr)


@unittest.skipIf(os.name == "nt", "hook integration runs in the existing WSL environment")
class HookIntegrationTests(unittest.TestCase):
    def run_stop_hook(self, cwd, payload):
        config = json.loads((bridge.ROOT/'.codex/hooks.json').read_text(encoding='utf-8'))
        command = config['hooks']['Stop'][0]['hooks'][0]['command']
        return subprocess.run(['bash', '-c', command], cwd=cwd, input=json.dumps(payload),
                              text=True, capture_output=True, timeout=60)

    def test_stop_launcher_is_noop_when_completion_module_is_absent(self):
        with tempfile.TemporaryDirectory(prefix='colab stop absent ') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            result = self.run_stop_hook(root, {'hook_event_name':'Stop', 'cwd':str(root),
                                               'session_id':'missing-module'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {})

    def test_registered_stop_launcher_runs_installed_completion_module(self):
        result = self.run_stop_hook(bridge.ROOT/'scripts',
                                    {'hook_event_name':'Stop', 'cwd':str(bridge.ROOT/'scripts'),
                                     'session_id':'ordinary-stop'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {})

    def test_stop_launchers_guard_missing_completion_module_after_reading_stdin(self):
        config = json.loads((bridge.ROOT/'.codex/hooks.json').read_text(encoding='utf-8'))
        hook = config['hooks']['Stop'][0]['hooks'][0]
        for key in ('command', 'commandWindows'):
            with self.subTest(key=key):
                self.assertIn('raw=sys.stdin.read()', hook[key])
                self.assertIn("scripts/slack_completion.py", hook[key])
                self.assertIn("print(\\'{}\\')", hook[key])

    def test_registered_linux_launcher_from_subdirectory(self):
        config = json.loads((bridge.ROOT/'.codex/hooks.json').read_text(encoding='utf-8'))
        command = config['hooks']['PreToolUse'][0]['hooks'][0]['command']
        for text, expected in (('git status --short', 0), ('git push --force origin main', 2)):
            data = {'cwd': str(bridge.ROOT/'scripts'), 'hook_event_name':'PreToolUse',
                    'tool_name':'Bash', 'tool_input':{'command':text}}
            result = subprocess.run(['bash','-c',command], cwd=bridge.ROOT/'scripts',
                                    input=json.dumps(data), text=True, capture_output=True, timeout=60)
            self.assertEqual(result.returncode, expected, result.stderr)

    def run_guard(self, *args, extra_env=None):
        env = dict(os.environ)
        for key in ("COLAB_HOOKS", "COLAB_FIX_LANE", "COLAB_ALLOW_TEST_EDIT"):
            env.pop(key, None)
        env.update(extra_env or {})
        return subprocess.run([sys.executable, str(bridge.ROOT / "scripts/agent-bridge.py"), *args],
                              env=env, capture_output=True, text=True, timeout=45)

    def test_safe_command_is_only_inspected(self):
        result = self.run_guard("guard-command", "--command", "git status --short")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NOT executed", result.stdout)

    def test_worker_main_push_is_rejected_without_execution(self):
        result = self.run_guard("guard-command", "--worker", "--command", "git push origin main")
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_fix_cannot_edit_test(self):
        result = self.run_guard("guard-edit", "--path", "frontend/test/example.test.ts",
                                extra_env={"COLAB_FIX_LANE": "1"})
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_outside_path_and_disabled_guard_rejected(self):
        self.assertEqual(self.run_guard("guard-edit", "--path", "../outside.md").returncode, 1)
        self.assertEqual(self.run_guard("guard-command", "--command", "git status",
                                        extra_env={"COLAB_HOOKS": "0"}).returncode, 1)

    def test_codex_patch_delete_hits_existing_fix_guard(self):
        event = {"cwd": str(bridge.ROOT), "hook_event_name": "PreToolUse", "tool_name": "apply_patch",
                 "tool_input": {"command": '*** Begin Patch\n*** Delete File: frontend/test/example.test.ts\n*** End Patch'}}
        env = dict(os.environ, COLAB_FIX_LANE='1', COLAB_HOOKS='1')
        env.pop('COLAB_ALLOW_TEST_EDIT', None)
        result = subprocess.run([sys.executable, str(bridge.ROOT / 'scripts/agent-bridge.py'), 'codex-event'],
                                input=json.dumps(event), text=True, capture_output=True, env=env, timeout=45)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('test-file-guard', result.stderr)

    def test_malformed_codex_event_is_blocked(self):
        result = subprocess.run([sys.executable, str(bridge.ROOT / 'scripts/agent-bridge.py'), 'codex-event'],
                                input='{}', text=True, capture_output=True, timeout=45)
        self.assertEqual(result.returncode, 2, result.stderr)


if __name__ == "__main__":
    unittest.main()
