"""Read-only DOCX collection for review; extracts text, never verifies its claims."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree


def _inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('source outside reference root')
    return path


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_sources(root, roles, datasets):
    root = Path(root).resolve()
    sources, bindings = {}, []
    for annotation in roles:
        name = annotation['source_document']
        matches = [p for p in root.rglob('*.docx') if p.name == name]
        if len(matches) != 1:
            raise ValueError(f'missing or ambiguous source: {name}')
        path = _inside(root, matches[0].relative_to(root))
        relative = path.relative_to(root).as_posix()
        owners = [d for d in datasets if d['manifest_key'] == annotation['dataset_key']]
        files = [f for d in owners for f in d['files'] if f['file_name'] == annotation['file']]
        if len(owners) != 1 or len(files) != 1:
            raise ValueError(f'missing or ambiguous target: {annotation["dataset_key"]}/{annotation["file"]}')
        if relative not in sources:
            raw = path.read_bytes()
            import io
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                xml = ElementTree.fromstring(archive.read('word/document.xml'))
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs = []
            for index, paragraph in enumerate(xml.findall('.//w:p', ns), 1):
                text = ''.join(t.text or '' for t in paragraph.findall('.//w:t', ns))
                if text.strip():
                    paragraphs.append(dict(paragraph=index, text=text))
            sources[relative] = dict(path=relative, sha256=hashlib.sha256(raw).hexdigest(),
                                     paragraphs=paragraphs)
        bindings.append(dict(dataset_id=owners[0]['id'], file_id=files[0]['id'],
                             file_name=annotation['file'], source=relative,
                             annotation=annotation, status='previously-reviewed-research-annotation'))
    return dict(kind='source text collection; not product ingestion or semantic verification',
                automatically_verified=False, sources=list(sources.values()), bindings=bindings)


def verify_sources(root, report):
    changed = []
    for source in report['sources']:
        path = _inside(Path(root), source['path'])
        if not path.is_file() or _digest(path) != source['sha256']:
            changed.append(source['path'])
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-root', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path)
    mode.add_argument('--verify', type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    if args.verify:
        changed = verify_sources(args.reference_root, json.loads(args.verify.read_text()))
        print(json.dumps(dict(changed=changed), ensure_ascii=False))
        return int(bool(changed))
    role_path = here / 'file-role-evidence.json'
    snapshot_path = root / 'dev-package/reports/stage3-ai-search-plan/dev-data-snapshot.json'
    report = collect_sources(args.reference_root, json.loads(role_path.read_text())['evidence'],
                             json.loads(snapshot_path.read_text())['datasets'])
    report['input_hashes'] = {str(p.relative_to(root)): _digest(p)
                              for p in [role_path, snapshot_path, Path(__file__)]}
    with args.output.open('x') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(f"sources={len(report['sources'])}, bindings={len(report['bindings'])}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
