"""Render immutable daily-report revisions from durable audit and collection facts."""
from __future__ import annotations
import collections
import copy
import datetime as dt
import hashlib
import json
import re
from zoneinfo import ZoneInfo
from .events import canonical, escape

KST = ZoneInfo('Asia/Seoul')
DETAIL_ACTIONS = {'dataset.deleted', 'project.deleted', 'permission.changed', 'access.approved', 'access.rejected'}
LABELS = {'upload.accepted': '업로드 접수', 'upload.registered': '등록', 'dataset.registered': '등록',
          'dataset.updated': '데이터 변경', 'dataset.deleted': '데이터 삭제', 'project.created': '프로젝트 생성',
          'project.deleted': '프로젝트 삭제', 'download.ticket_issued': '다운로드 요청/티켓 발급',
          'access.requested': '접근 요청', 'access.approved': '접근 승인', 'access.rejected': '접근 거절',
          'permission.changed': '권한 변경'}
ALIASES = {'데이터셋 등록': 'dataset.registered', '좌표계·격자 변경': 'dataset.updated',
           '격자 가져오기': 'dataset.updated', '본체 파일 변경': 'dataset.updated', '계보 확정': 'dataset.updated'}


def timestamp(value):
    result = dt.datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError('timezone-aware audit time required')
    return result


def _scope_rows(data, date, manifest):
    exclusions = manifest['test_exclusions']
    effective = timestamp(exclusions['effective_at'])
    start = dt.datetime.combine(dt.date.fromisoformat(date), dt.time(), KST)
    end = start + dt.timedelta(days=1)
    coverage = timestamp(manifest['coverage_started_at'])
    rows, excluded = [], 0
    for item in data['events'].values():
        row = copy.deepcopy(item['record'])
        occurred = timestamp(row['occurred_at'])
        if not start <= occurred < end or occurred < coverage:
            continue
        if occurred >= effective and (row['lab_id'] in exclusions['lab_ids'] or row['actor_id'] in exclusions['account_ids']):
            excluded += 1
            continue
        # D6 snapshots own project create/delete. D8's mirrored home-activity strings
        # are not separate operations and are deliberately not selected as a source.
        row['action'] = ALIASES.get(row['action'], row['action'])
        if row['action'] in LABELS:
            rows.append(row)
    rows.sort(key=lambda r: (timestamp(r['occurred_at']), r['source_id']))
    ranks = {'upload.accepted': 0, 'upload.registered': 1, 'dataset.registered': 2}
    uploads, selected = {}, []
    for row in rows:
        upload_id = row.get('upload_id')
        if row['action'].startswith('upload.'):
            upload_id = upload_id or row['target_id']
        if upload_id and row['action'] in ranks:
            key = (row['lab_id'], upload_id)
            if key not in uploads or ranks[row['action']] > ranks[uploads[key]['action']]:
                uploads[key] = row
        else:
            selected.append(row)
    selected.extend(uploads.values())
    selected.sort(key=lambda r: (timestamp(r['occurred_at']), r['source_id']))
    return selected, excluded


def _collection(data, manifest, date):
    collection = manifest.get('collection', data.get('collection'))
    if not isinstance(collection, dict):
        return {'status': 'missing', 'labs': [], 'sources': []}, False, '집계 불완전 · 수집 확인 없음'
    collection = copy.deepcopy(collection)
    day_start = dt.datetime.combine(dt.date.fromisoformat(date), dt.time(), KST)
    exclusions = manifest['test_exclusions']
    if day_start >= timestamp(exclusions['effective_at']) and isinstance(collection.get('labs'), list):
        collection['labs'] = [lab for lab in collection['labs'] if lab['id'] not in exclusions['lab_ids']]
        collection['sources'] = [source for source in collection.get('sources', []) if source.get('lab_id') not in exclusions['lab_ids']]
    if collection.get('status') == 'failed':
        return collection, False, '집계 불완전 · 전체 수집 실패'
    if collection.get('status') != 'complete':
        return collection, False, '집계 불완전 · 일부 원천 수집 실패'
    labs, sources = collection.get('labs'), collection.get('sources')
    if not isinstance(labs, list) or not isinstance(sources, list):
        return collection, False, '집계 불완전 · 수집 범위 확인 없음'
    try:
        observed = timestamp(collection['collected_at'])
        end = dt.datetime.combine(dt.date.fromisoformat(date) + dt.timedelta(days=1), dt.time(), KST)
        if observed < end:
            return collection, False, '집계 불완전 · 날짜 마감 이후 수집 확인 없음'
    except (KeyError, ValueError):
        return collection, False, '집계 불완전 · 수집 시각 확인 없음'
    if not labs:
        return collection, False, '대상 연구실 0개'
    required = manifest.get('sources', [])
    required = {s if isinstance(s, str) else s['id'] for s in required}
    if not required:
        return collection, False, '집계 불완전 · 보고 원천 미설정'
    facts = {(s['lab_id'], s['source']): s for s in sources}
    for lab in labs:
        for source in required:
            fact = facts.get((lab['id'], source))
            if not fact or fact.get('status') != 'complete' or fact.get('pending') != 0:
                return collection, False, '집계 불완전 · 미접수 또는 누락 원천 있음'
    if manifest.get('failed_sources'):
        return collection, False, '집계 불완전 · 일부 원천 수집 실패'
    return collection, True, ''


def _safe_value(value):
    if isinstance(value, dict):
        return {k: ('[비공개]' if str(k).lower() in {'password','token','secret','authorization','cookie','webhook'} else _safe_value(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_value(v) for v in value]
    if isinstance(value, str):
        return re.sub(r'https://hooks\.slack\.com/services/[^\s"<>]+', '[비공개 webhook]', value)
    return value


def _display(row, field):
    label = row.get(field + '_name')
    identity = row[field + '_id']
    return escape(_safe_value(f'{label} ({identity})' if label else f'{identity} (표시 이름 없음)'))


def _parts(date, environment, revision, lines, delayed=False):
    report_id = f'{environment}:{date}'
    correction = ' · 정정 보고' if revision > 1 else (' · 지연 보고' if delayed else '')
    base = f'CoLAB 운영 일일 보고 · {date} · {environment} · Asia/Seoul{correction}'
    body = '\n'.join(lines)
    total = 1
    while True:
        longest = f'{base}\nreport={report_id} · revision={revision} · {total}/{total}\n'
        capacity = 2940 - len(longest)
        if capacity < 1:
            raise ValueError('report header exceeds message size')
        needed = max(1, (len(body) + capacity - 1) // capacity)
        if needed == total:
            break
        total = needed
    result = []
    for index in range(total):
        prefix = f'{base}\nreport={report_id} · revision={revision} · {index + 1}/{total}\n'
        result.append({'schema': 'colab.operator-event/1', 'report_id': report_id, 'report_date': date,
                       'revision': revision, 'part': index + 1, 'total': total,
                       'text': prefix + body[index * capacity:(index + 1) * capacity]})
    return result


def event_id(part):
    return f"report:{part['report_id']}:r{part['revision']}:p{part['part']}"


def build(date: str, manifest: dict, archive) -> list[dict]:
    if manifest.get('usage') != 'live':
        return []
    if manifest['environment'] != 'dev':
        raise ValueError('only the declared live dev environment supplies activity reports')
    # Persist the exact rendered parts before returning anything to the publisher.
    with archive.transaction() as data:
        rows, excluded = _scope_rows(data, date, manifest)
        collection, collected, incomplete_label = _collection(data, manifest, date)
        lab_names = {lab['id']: lab.get('name') for lab in collection.get('labs', [])}
        account_names = {(a['lab_id'], a['id']): a.get('name') for a in collection.get('accounts', [])}
        for row in rows:
            row['actor_name'] = row.get('actor_name') or account_names.get((row['lab_id'], row['actor_id']))
            if not row.get('lab_name') and lab_names.get(row['lab_id']):
                row['lab_name'] = lab_names[row['lab_id']]
        facts = {k: v for k, v in collection.items() if k not in {'collected_at', 'snapshot_id'}}
        fingerprint = hashlib.sha256(canonical({'rows': rows, 'collection': facts, 'excluded': excluded,
            'coverage': manifest['coverage_started_at'], 'collected': collected, 'incomplete_label': incomplete_label, 'failed_sources': manifest.get('failed_sources', [])})).hexdigest()
        previous = data['reports'].get(date)
        if previous and previous.get('parts'):
            if previous['status'] != 'sent':
                if previous['fingerprint'] != fingerprint:
                    data['dirty'][date] = True
                return copy.deepcopy(previous['parts'])
            if previous['fingerprint'] == fingerprint:
                data['dirty'][date] = False
                return []
        revision = 1 if previous is None else previous['revision'] + 1
        state = incomplete_label if not collected else ('활동 없음' if not rows else '집계 완료')
        labs = {r['lab_id'] for r in rows}
        users = {(r['lab_id'], r['actor_id']) for r in rows}
        lines = [f'상태: {state}', f'연구실 {len(collection.get("labs", []))} · 활동 연구실 {len(labs)} · 사용자 {len(users)} · 활동 {len(rows)}']
        start = timestamp(manifest['coverage_started_at']).astimezone(KST)
        if start.date().isoformat() == date and start.time() != dt.time():
            lines.append('수집 시작 이후 기록만 포함한 부분 일자 · ' + start.isoformat())
        groups, display = {}, {}
        for row in rows:
            key = (row['lab_id'], row['actor_id'])
            groups.setdefault(key, collections.Counter())[row['action']] += 1
            display[key] = (_display(row, 'lab'), _display(row, 'actor'))
        for key, counts in sorted(groups.items()):
            lab, actor = display[key]
            detail = ', '.join(f'{LABELS[action]} {count}건' for action, count in sorted(counts.items()))
            lines.append(f'연구실 {lab} · 사용자 {actor}: {detail}')
        for row in rows:
            if row['action'] in DETAIL_ACTIONS:
                lines.append(f"{timestamp(row['occurred_at']).astimezone(KST).isoformat()} · 연구실 {_display(row, 'lab')} · "
                    f"행위자 {_display(row, 'actor')} · {LABELS[row['action']]} · 대상 {_display(row, 'target')} · "
                    f"전 {escape(json.dumps(_safe_value(row.get('before')), ensure_ascii=False))} · 후 {escape(json.dumps(_safe_value(row.get('after')), ensure_ascii=False))}")
        delayed = bool(manifest.get('run_at') and dt.date.fromisoformat(date) < timestamp(manifest['run_at']).astimezone(KST).date() - dt.timedelta(days=1))
        parts = _parts(date, manifest['environment'], revision, lines, delayed)
        history = copy.deepcopy(previous.get('history', [])) if previous else []
        if previous:
            history.append({k: v for k, v in previous.items() if k != 'history'})
        data['reports'][date] = {'fingerprint': fingerprint, 'revision': revision, 'status': 'generated',
            'complete': False, 'collection_complete': collected, 'parts': parts, 'event_ids': [event_id(p) for p in parts],
            'history': history, 'manifest': {'lab_count': len(collection.get('labs', [])), 'row_count': len(rows),
                'excluded_count': excluded, 'collection': collection}}
        data['dirty'][date] = False
        return copy.deepcopy(parts)
