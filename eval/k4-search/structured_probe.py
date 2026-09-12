"""Offline candidate probe; no LLM, database mutation, or full semantic verdict.

Uses only snapshot descriptions, filenames and direct parent edges. Heuristics
are experimental; unverified facets must never be presented as satisfied.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from condition_assessment import assess_conditions


def search(query, datasets, *, evidence=()):
    q = query.lower()
    months = ['일월', '이월', '삼월', '사월', '오월', '유월',
              '칠월', '팔월', '구월', '시월', '십일월', '십이월']
    for number, name in sorted(enumerate(months, 1), key=lambda item: -len(item[1])):
        q = re.sub(r'(?<=년)\s*' + name, f' {number}월', q)
    by_id = {d['id']: d for d in datasets}
    unverified = []
    # Evidence is absent for quality claims and native measurement resolution.
    if '결측' in q or '0%' in q:
        unverified.append('quality')
    if '직접 관측' in q or re.search(r'\d+\s*(?:m|km)', q):
        unverified.append('native_resolution')
    if any(t in q for t in ('경기', '충청', '제주', '우리나라', '대한민국')):
        unverified.append('geographic_coverage')
    if any(t in q for t in ('주간', '매주', '매일', '15분', '4주', '4weeks')):
        unverified.append('temporal_granularity')
    if '말고' in q:
        unverified.append('file_exclusion')
    owners = [d for d in datasets if any(f['file_name'].lower() in q for f in d['files'])]
    if owners and any(t in q for t in ('원자료', '바로 앞', '입력 데이터셋')):
        edges = [p for d in owners for p in d['parents'] if p['parent_dataset_id'] in by_id]
        return dict(ids=list(dict.fromkeys(p['parent_dataset_id'] for p in edges)),
                    relation=edges, unverified=unverified, strategy='exact-file/direct-parent')

    topic_patterns = [('식생·NDVI', r'식생|ndvi|푸른|녹색도'),
                      ('강우·강수', r'강수|강우|레이더'), ('가뭄', r'가뭄|spei|spi')]
    topics = [topic for topic, pattern in topic_patterns if re.search(pattern, q)]
    if len(topics) > 1:
        return dict(ids=[], unverified=unverified + ['multiple_topics'], strategy='unsupported')
    positive = re.sub(r'(?:^|[.!?])[^.!?]*(?:빼줘|제외해)[.!?]?', ' ', q)
    positive = re.sub(r'[^.!?]*?제외하고', ' ', positive)
    model = bool(re.search(r'u[- ]?net', positive))
    auxiliary = any(t in positive for t in ('보조', '지형', '토지피복'))
    validation = any(t in positive for t in ('검증', '비교에 쓴')) and 'quality' not in unverified
    prediction = any(t in positive for t in ('예측', '추정'))
    monthly = any(t in q for t in ('월평균', '한 달 평균'))
    crop = 'wgs84' in q or '잘라' in q
    month = re.search(r'(20\d{2})년\s*(\d{1,2})월', q)
    if month:
        wanted_month = f'{month[1]}{int(month[2]):02d}'
        unverified.append('continuous_temporal_coverage')
    else:
        wanted_month = None
        if re.search(r'\d{4}', q):
            unverified.append('period')
    day = re.search(r'20\d{2}년\s*\d{1,2}월\s*(\d{1,2})일', q)
    wanted_date = wanted_month + f'{int(day[1]):02d}' if day and wanted_month else wanted_month
    if not (topics or owners):
        return dict(ids=[], unverified=unverified + ['unsupported_query'], strategy='facets')

    found = []
    file_evidence = {}
    for d in datasets:
        if topics and not all(d['topic'] == topic for topic in topics):
            continue
        text = (d['name'] + ' ' + d['summary']).lower()
        files = ' '.join(f['file_name'].lower() for f in d['files'])
        names = {f['file_name'] for f in d['files']}
        sourced = [e for e in evidence if e['dataset_key'] == d.get('manifest_key')
                   and e['file'] in names and e.get('source_document')]
        excluded = re.search(r'\b(spi|spei)\s*말고', q)
        if excluded:
            sourced = [e for e in sourced if e.get('variable', '').lower() != excluded[1]]
        # An input's model relationship comes from its child's actual edge.
        model_children = [child for child in datasets if
                          re.search(r'u[- ]?net', child['summary'].lower()) and
                          any(p['parent_dataset_id'] == d['id'] for p in child['parents'])]
        own_model = bool(re.search(r'u[- ]?net', text))
        if model and not (own_model or ((auxiliary or validation) and model_children)):
            continue
        # Mentioning prediction in an input description is not an output role.
        predicted = own_model and any(f['file_name'].lower().startswith(('pred_', 'prediction_')) for f in d['files'])
        if predicted and prediction:
            annotated = {e['file'] for e in sourced}
            sourced += [dict(file=f['file_name'], role='prediction', source_document='registered summary and filename',
                             scope='prediction filename; no performance guarantee') for f in d['files']
                        if f['file_name'] not in annotated and f['file_name'].lower().startswith(('pred_', 'prediction_'))
                        and (not wanted_date or wanted_date in f['file_name'])]
        aux = '보조입력' in text and not predicted
        # A child's mention of validation does not identify which parent/file
        # provided it. Require local evidence; missing roles stay unresolved.
        valid = ('검증자료' in text and not predicted) or any(e['role'] == 'validation' for e in sourced)
        if auxiliary and not aux:
            continue
        if prediction or validation:
            if not ((prediction and predicted) or (validation and valid)):
                continue
        if monthly and not (('월 평균' in text or '월평균' in text) and not predicted and not aux):
            continue
        if crop and not ('wgs84' in text and ('crop' in text or '영역 추출' in text)):
            continue
        if wanted_date and wanted_date not in files:
            continue
        found.append(d['id'])
        if sourced:
            roles = set()
            if prediction:
                roles.add('prediction')
            if validation:
                roles.add('validation')
            if auxiliary:
                roles.add('auxiliary_input')
            file_evidence[d['id']] = [e for e in sourced if not roles or e['role'] in roles]
    if (re.search(r'\b(spi|spei)\s*말고', q) and 'file_exclusion' in unverified
            and found and all(file_evidence.get(i) for i in found)):
        unverified.remove('file_exclusion')
    return dict(ids=found, unverified=unverified, strategy='facets', file_evidence=file_evidence)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    cases_path = Path(__file__).with_name('golden-cases.json')
    suite = json.loads(cases_path.read_text())
    snapshot_path = root / suite['snapshot']
    datasets = json.loads(snapshot_path.read_text())['datasets']
    extras_path = Path(__file__).with_name('structured-extra-cases.json')
    extras = json.loads(extras_path.read_text())
    evidence_path = Path(__file__).with_name('file-role-evidence.json')
    annotations = json.loads(evidence_path.read_text())['evidence']
    conditions_path = Path(__file__).with_name('condition-evidence.json')
    conditions = json.loads(conditions_path.read_text())
    key_id = {d['manifest_key']: d['id'] for d in datasets}
    cases = suite['cases'] + [dict(c, required=[key_id[k] for k in c['required']],
                                scope=list(key_id.values())) for c in extras]
    results = []
    for case in cases:
        result = search(case['query'], [d for d in datasets if d['id'] in case['scope']],
                        evidence=annotations)
        result['conditions'] = {
            d['id']: assess_conditions(case['query'], conditions['datasets'].get(d['manifest_key'], {}))
            for d in datasets if d['id'] in result['ids']}
        result['candidate_status'] = {
            id: ('related_condition_mismatch' if any(c['status'] == 'contradicted' for c in checks.values())
                 else 'candidate_conditions_incomplete') for id, checks in result['conditions'].items()}
        passed = (set(case['required']) <= set(result['ids']) if case['mode'] == 'retrieval'
                  else not result['ids'] if case['mode'] == 'empty' else None)
        results.append(dict(id=case['id'], query=case['query'], **result,
                            inclusion=passed, semantic='unassessed'))
    evidence = [Path(__file__), Path(__file__).with_name('test_structured_probe.py'),
                cases_path, extras_path, snapshot_path, evidence_path, conditions_path,
                Path(__file__).with_name('condition_assessment.py'),
                Path(__file__).with_name('test_condition_assessment.py')]
    report = dict(model_calls=0, kind='offline candidate experiment; not production quality',
                  hashes={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence},
                  results=results)
    with Path(args.output).open('x') as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
    for group in (results[:12], results[12:]):
        print({str(v): sum(r['inclusion'] is v for r in group) for v in (True, False, None)})
    return int(any(r['inclusion'] is False for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
