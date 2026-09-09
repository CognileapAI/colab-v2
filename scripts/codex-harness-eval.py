#!/usr/bin/env python3
"""Run the existing harness tasks and expect.sh against local Codex, without modifying fixtures.

Separate runner: Codex does not expose Claude's --max-budget-usd. This runner
requires an explicit per-run timeout and records usage, without claiming a USD cap.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def snapshot(root: Path, exclude: Path | None = None) -> dict:
    """Hash tracked and nonignored untracked bytes, including dirty/deleted files."""
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)
    names = set(git('ls-files', '-z', '--cached', '--others', '--exclude-standard').decode('utf-8').split('\0'))
    files = {}
    for name in sorted(names - {''}):
        path = root/name
        if exclude and path.resolve().is_relative_to(exclude.resolve()):
            continue
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    try:
        head = git('rev-parse', 'HEAD').decode().strip()
    except subprocess.CalledProcessError:
        head = None
    dirty = git('status', '--porcelain=v1', '-z').decode('utf-8')
    return {'head': head, 'dirty_status': dirty, 'files': files,
            'sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def runtime_model(raw: str, sessions: Path | None = None) -> dict:
    # JSONL records are LF-delimited; NEL/LS/PS may occur inside JSON strings.
    rows = [json.loads(line) for line in raw.split('\n') if line.strip()]
    ids = {r.get('thread_id') for r in rows if r.get('type') == 'thread.started' and r.get('thread_id')}
    if len(ids) != 1:
        raise ValueError('missing unique runtime thread ID; model unverified')
    thread_id = next(iter(ids))
    sessions = sessions or Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex')))/'sessions'
    for path in sessions.rglob(f'*{thread_id}*.jsonl'):
        events = [json.loads(line) for line in path.read_text(encoding='utf-8').split('\n') if line.strip()]
        if not any(e.get('type') == 'session_meta' and e.get('payload', {}).get('id') == thread_id for e in events):
            continue
        contexts = [e for e in events if e.get('type') == 'turn_context']
        models = sorted({e['payload']['model'] for e in contexts if isinstance(e.get('payload', {}).get('model'), str)})
        if models:
            return {'thread_id': thread_id, 'models': models, 'source': str(path),
                    'session_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'contexts': contexts}
    raise ValueError('matching runtime session turn_context model unavailable')


def run_task(task: Path, repeat: int, codex: str, timeout: int, output: Path) -> dict:
    row = {'task': task.name, 'repeat': repeat, 'status': 'readiness-failure'}
    prefix = output/f'{task.name}.{repeat}'
    start = time.monotonic()
    stdout, stderr = b'', b''
    try:
        if not (task/'fixture').is_dir() or not (task/'expect.sh').is_file():
            raise ValueError('fixture/ or expect.sh missing')
        prompt = (task/'task.md').read_bytes()
        row['task_sha256'] = hashlib.sha256(prompt).hexdigest()
        process = subprocess.run([codex, '-C', str(task/'fixture'), 'exec',
                                  '--sandbox', 'read-only', '--json', '-'],
                                 input=prompt, capture_output=True, timeout=timeout, cwd=task)
        stdout, stderr = process.stdout, process.stderr
        row['runtime_exit'] = process.returncode
        if process.returncode:
            raise ValueError(f'Codex exit {process.returncode}')
        raw = stdout.decode('utf-8')
        answer, row['usage'] = response(raw)
        Path(f'{prefix}.txt').write_text(answer, encoding='utf-8')
        row['model_evidence'] = runtime_model(raw)
        judge = judge_answer(task, answer)
        row.update(status=('green' if judge.returncode == 0 else
                           'judgment-failure' if judge.returncode == 1 else 'readiness-failure'),
                   judge_exit=judge.returncode,
                   evidence=(judge.stdout+judge.stderr).decode('utf-8', errors='replace'))
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b'', exc.stderr or b''
        row['error'] = f'timeout: {exc}'
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        row['error'] = str(exc)
    finally:
        Path(f'{prefix}.jsonl').write_bytes(stdout)
        Path(f'{prefix}.stderr').write_bytes(stderr)
        row['seconds'] = round(time.monotonic()-start, 2)
        Path(f'{prefix}.result.json').write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    return row


def judge_answer(task: Path, answer: str):
    command = (['wsl.exe', '--cd', str(task), '-e', 'bash', 'expect.sh']
               if sys.platform == 'win32' else ['bash', str(task/'expect.sh')])
    # Binary stdin preserves LF across native Windows -> WSL. Text mode
    # inserts CRLF and breaks the original judges' end anchors.
    return subprocess.run(command, input=answer.encode('utf-8'), capture_output=True,
                          cwd=task, timeout=30)


def response(raw: str) -> tuple[str, dict]:
    rows = [json.loads(line) for line in raw.split('\n') if line.strip()]
    if any(not isinstance(r, dict) for r in rows):
        raise ValueError('malformed Codex event')
    if any(r.get('type') == 'item.completed' and not isinstance(r.get('item'), dict) for r in rows):
        raise ValueError('malformed Codex item')
    if any(r.get('type') in ('error', 'turn.failed') for r in rows):
        raise ValueError('Codex error event')
    done = [r for r in rows if r.get('type') == 'turn.completed']
    messages = [r['item']['text'] for r in rows if r.get('type') == 'item.completed'
                and r.get('item', {}).get('type') == 'agent_message'
                and isinstance(r['item'].get('text'), str)]
    if len(done) != 1 or not messages or not messages[-1].strip():
        raise ValueError('missing completion or final agent message')
    return messages[-1], done[0].get('usage', {})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', required=True, help='Existing native Codex executable')
    parser.add_argument('--timeout', required=True, type=int)
    parser.add_argument('--only', action='append', required=True, help='H01 etc.; repeat for multiple tasks')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('timeout must be positive')
    tasks = sorted((ROOT / 'eval/harness').glob('H??-*'))
    selected = [p for p in tasks if p.name.split('-')[0] in args.only]
    if set(args.only) != {p.name.split('-')[0] for p in selected}:
        print('red(준비): unknown or missing task', file=sys.stderr)
        return 78
    # A new directory prevents results from earlier attempts being accepted.
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        version = subprocess.check_output([args.codex, '--version'], text=True, cwd=ROOT, timeout=30).strip()
        initial = snapshot(ROOT, args.output)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        failure = {'status': 'readiness-failure', 'error': str(exc), 'runs': []}
        (args.output/'summary.json').write_text(json.dumps(failure, ensure_ascii=False, indent=2), encoding='utf-8')
        return 78
    (args.output/'snapshot.before.json').write_text(json.dumps(initial, ensure_ascii=False, indent=2), encoding='utf-8')
    rows = []
    for task in selected:
        for repeat in (1, 2):
            row = run_task(task, repeat, args.codex, args.timeout, args.output)
            rows.append(row)
            # Keep console JSON safe on native Windows legacy code pages.
            # The preserved evidence files remain UTF-8 with original text.
            print(json.dumps(row, ensure_ascii=True), flush=True)
    final = snapshot(ROOT, args.output)
    (args.output/'snapshot.after.json').write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding='utf-8')
    snapshot_matches = initial['sha256'] == final['sha256'] and initial['head'] == final['head']
    report = {'schema': 'colab-codex-harness-eval/1', 'time': datetime.now(timezone.utc).isoformat(),
              'codex': args.codex, 'cli_version': version, 'head': initial['head'],
              'snapshot_sha256': initial['sha256'], 'snapshot_matches': snapshot_matches,
              'models': sorted({m for r in rows for m in r.get('model_evidence', {}).get('models', [])}),
              'timeout': args.timeout, 'usd_cap': 'unsupported', 'runs': rows}
    (args.output/'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    # Snapshot drift invalidates the evidence; stable mixed failures follow README's exit 1 priority.
    if not snapshot_matches:
        return 78
    if any(r['status'] == 'judgment-failure' for r in rows):
        return 1
    if any(r['status'] == 'readiness-failure' for r in rows):
        return 78
    return 0 if rows and all(r['status'] == 'green' for r in rows) else 1


if __name__ == '__main__':
    sys.exit(main())
