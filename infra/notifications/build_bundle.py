"""Build a deterministic Lambda archive with explicitly pinned SDK dependencies."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import zipfile

FILES = ('__init__.py', 'events.py', 'delivery.py', 'aws_events.py', 'aws_store.py', 'handlers.py',
         'archive.py', 'digest.py', 'jobs.py', 'http_sender.py', 'producers.py')
PACKAGES = ('boto3', 'botocore', 'jmespath', 's3transfer', 'urllib3', 'dateutil', 'six.py')


def build(source: Path, output: Path, vendor: Path | None = None) -> str:
    if vendor is None or not vendor.is_dir():
        raise ValueError('pinned dependency vendor directory is required')
    requirements = {}
    for line in (source / 'requirements.txt').read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            name, version = line.split('==')
            requirements[name.lower().replace('_', '-')] = version
    installed = {d.metadata['Name'].lower().replace('_', '-'): d.version
                 for d in importlib.metadata.distributions(path=[str(vendor)])}
    if any(installed.get(name) != version for name, version in requirements.items()):
        raise ValueError('vendor dependencies do not match pinned requirements')
    entries = {'notifications/' + name: (source / name).read_bytes() for name in FILES}
    for package in PACKAGES:
        root = vendor / package
        if not root.exists():
            raise ValueError('required dependency package is absent')
        candidates = [root] if root.is_file() else root.rglob('*')
        for path in candidates:
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                entries[path.relative_to(vendor).as_posix()] = path.read_bytes()
    hashes = {name: hashlib.sha256(body).hexdigest() for name, body in sorted(entries.items())}
    entries['bundle-manifest.json'] = json.dumps({'dependencies': requirements, 'files': hashes}, sort_keys=True).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for name, body in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, body)
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default=str(Path(__file__).parent))
    parser.add_argument('--vendor', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    print(build(Path(args.source), Path(args.output), Path(args.vendor)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
