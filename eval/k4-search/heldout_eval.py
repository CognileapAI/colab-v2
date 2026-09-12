"""File retrieval + condition component checks; not an answer quality score."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
from structured_probe import search
from condition_assessment import assess_conditions


def files_match(case, result, keys):
    selected = {e['file'] for es in result.get('file_evidence', {}).values() for e in es}
    return set(case['required']) == {keys[i] for i in result['ids']} and selected == set(case['files'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    snapshot = root / 'dev-package/reports/stage3-ai-search-plan/dev-data-snapshot.json'
    datasets = json.loads(snapshot.read_text())['datasets']
    roles = json.loads((here / 'file-role-evidence.json').read_text())['evidence']
    facts = json.loads((here / 'condition-evidence.json').read_text())['datasets']
    cases = json.loads((here / 'heldout-cases.json').read_text())
    keys = {d['id']: d['manifest_key'] for d in datasets}
    results = []
    for case in cases:
        started = perf_counter()
        result = search(case['query'], datasets, evidence=roles)
        if case.get('files'):
            passed = files_match(case, result, keys)
        else:
            # Deliberately a component test: the oracle supplies a related
            # dataset, so this does NOT prove retrieval or generated reasoning.
            assessment = assess_conditions(case['query'], facts[case['related']])
            result['related_assessment'] = assessment
            passed = assessment.get(case['condition'], {}).get('status') == case['expected']
        results.append(dict(id=case['id'], passed=passed, result=result,
                            elapsed_ms=round((perf_counter() - started) * 1000, 3)))
    evidence = list(here.glob('*.py')) + list(here.glob('*.json')) + [snapshot]
    report = dict(kind='3 file-retrieval checks + 3 condition-component checks; not end-to-end answers',
                  results=results, model_calls=0,
                  hashes={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence})
    with Path(args.output).open('x') as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
    print(f"passed={sum(r['passed'] for r in results)}, failed={sum(not r['passed'] for r in results)}")
    return int(any(not r['passed'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
