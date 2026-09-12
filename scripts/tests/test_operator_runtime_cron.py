import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'infra/notifications/run-runtime-job.sh'
INSTALLER = ROOT / 'infra/notifications/install-runtime-cron.sh'


class RuntimeCronTests(unittest.TestCase):
    def config(self, root, environment):
        fake = root / 'python'
        fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$COLAB_TEST_CALLS"\ncase "$*" in *"infra.notifications.cli probe"*) exit "${COLAB_TEST_PROBE_RC:-0}";; esac\n')
        fake.chmod(0o700)
        manifest = root / 'manifest.json'; manifest.write_text('{}')
        key = root / 'relay-key'; key.write_text('not-a-real-key'); key.chmod(0o600)
        config = root / 'runtime.env'
        config.write_text(
            f"COLAB_NOTIFICATION_ENVIRONMENT={environment}\n"
            f"COLAB_NOTIFICATION_ROOT={ROOT}\n"
            f"COLAB_NOTIFICATION_PYTHON={fake}\n"
            f"COLAB_OPERATOR_MANIFEST={manifest}\n"
            f"COLAB_OPERATOR_SPOOL={root / 'spool'}\n"
            f"COLAB_OPERATOR_STATE={root / 'state'}\n"
            f"COLAB_TEST_CALLS={root / 'calls'}\n"
            "COLAB_TEST_SECRET=must-not-be-printed\n"
            "COLAB_STAGE_SSH_TARGET=dev-host\n"
            f"COLAB_STAGE_SSH_KEY={key}\n"
            f"COLAB_STAGE_REMOTE_WRAPPER={RUNNER}\n"
            "COLAB_STAGE_REMOTE_CONFIG=/etc/colab/operator-runtime.env\n"
        )
        config.chmod(0o600)
        return config

    def invoke(self, *args, env=None):
        return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)

    def test_dev_wrapper_loads_private_config_without_printing_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config = self.config(root, 'dev')
            for job in ('export', 'probe-service-health', 'daily', 'spool', 'retry', 'receive'):
                result = self.invoke(RUNNER, '--config', config, job)
                self.assertEqual(result.returncode, 0, (job, result.stderr))
                self.assertNotIn('must-not-be-printed', result.stdout + result.stderr)
            calls = (root / 'calls').read_text()
            self.assertIn('operator_audit_export.py sync', calls)
            self.assertIn('probe --manifest', calls)
            self.assertIn('daily --manifest', calls)
            self.assertIn('drain-spool --profile connected', calls)
            self.assertIn('publish-pending --manifest', calls)
            self.assertIn('relay receive', calls)

    def test_stage_probe_records_completion_time_then_relays_spool(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config = self.config(root, 'staging')
            result = self.invoke(RUNNER, '--config', config, 'probe-backup-freshness')
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = (root / 'calls').read_text().splitlines()
            self.assertEqual(len(calls), 3)
            self.assertIn('cli probe', calls[0])
            self.assertIn('--profile relay', calls[0])
            self.assertIn('relay heartbeat', calls[1])
            self.assertIn('--observed-at ', calls[1])
            self.assertIn('relay send', calls[2])
            self.assertNotIn('must-not-be-printed', result.stdout + result.stderr)

    def test_installer_is_deterministic_idempotent_and_refuses_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config = self.config(root, 'dev'); cron = root / 'cron'
            env = dict(os.environ, COLAB_NOTIFICATION_CRON_FILE=str(cron))
            rendered = self.invoke(INSTALLER, '--environment', 'dev', '--config', config, 'render', env=env)
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            daily = next(line for line in rendered.stdout.splitlines() if line.endswith(' daily'))
            self.assertTrue(daily.startswith('*/5 * * * * root'))
            self.assertNotIn('0-59/5 23', rendered.stdout)
            self.assertEqual(rendered.stdout.count('probe-'), 3)
            first = self.invoke(INSTALLER, '--environment', 'dev', '--config', config, 'install', env=env)
            second = self.invoke(INSTALLER, '--environment', 'dev', '--config', config, 'install', env=env)
            self.assertEqual((first.returncode, second.returncode), (0, 0))
            installed = cron.read_text(); cron.write_text(installed + '# drift\n')
            rejected = self.invoke(INSTALLER, '--environment', 'dev', '--config', config, 'install', env=env)
            self.assertEqual(rejected.returncode, 1)
            self.assertEqual(cron.read_text(), installed + '# drift\n')
            self.assertNotIn('must-not-be-printed', rendered.stdout + first.stdout + second.stdout + rejected.stderr)

    def test_stage_schedule_contains_only_probe_and_ssh_relay_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config = self.config(root, 'staging'); cron = root / 'cron'
            env = dict(os.environ, COLAB_NOTIFICATION_CRON_FILE=str(cron))
            result = self.invoke(INSTALLER, '--environment', 'staging', '--config', config, 'render', env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count('probe-'), 3)
            self.assertIn('stage-relay', result.stdout)
            self.assertNotIn(' export', result.stdout)
            self.assertNotIn(' daily', result.stdout)
            self.assertNotIn(' connected', result.stdout)

    def test_stage_unobservable_probe_does_not_send_heartbeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config = self.config(root, 'staging')
            env = dict(os.environ, COLAB_TEST_PROBE_RC='75')
            result = self.invoke(RUNNER, '--config', config, 'probe-service-health', env=env)
            self.assertEqual(result.returncode, 75)
            calls = (root / 'calls').read_text().splitlines()
            self.assertEqual(len(calls), 2)
            self.assertIn('cli probe', calls[0])
            self.assertIn('relay send', calls[1])
            self.assertNotIn('relay heartbeat', '\n'.join(calls))

    def test_relay_probe_profile_accepts_connected_manifest_without_local_channels(self):
        import json
        from infra.notifications import cli
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {
                'schema': 'colab.operator-manifest/1', 'environment': 'staging', 'usage': 'rehearsal',
                'channels': {
                    'development': 'arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:dev',
                    'activity': 'arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:activity',
                },
                'coverage_started_at': '2026-09-12T00:00:00+00:00',
                'test_exclusions': {'lab_ids': [], 'account_ids': [], 'effective_at': '2026-09-12T00:00:00+00:00'},
                'sources': ['d2', 'd3', 'd5', 'd6', 'd8'],
                'probes': [{'target': 'service-health', 'command': ['/bin/true'], 'timeout': 2}],
                'aws': {'account_id': '123456789012', 'regions': ['ap-northeast-2', 'us-east-1'],
                        'services': ['EC2'], 'resources': {'i-stage': 'staging'},
                        'alarms': {'stage-status': 'staging'}},
            }
            path = root / 'manifest.json'; path.write_text(json.dumps(manifest))
            code = cli.main(['probe', '--manifest', str(path), '--profile', 'relay',
                             '--target', 'service-health', '--state', str(root / 'state.json'),
                             '--spool', str(root / 'spool')])
            self.assertEqual(code, 0)


if __name__ == '__main__':
    unittest.main()
