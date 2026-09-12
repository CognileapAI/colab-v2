"""Normalize only declared CoLAB AWS scope; discard raw descriptions and entity data."""
from __future__ import annotations

import datetime as dt
import hashlib

from .events import make_event


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError('AWS update timestamp required')
    try:
        result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        # Health also documents RFC 822 timestamps in some event fields.
        from email.utils import parsedate_to_datetime
        result = parsedate_to_datetime(value)
    if result.tzinfo is None:
        raise ValueError('AWS timestamp must include timezone')
    return result.astimezone(dt.timezone.utc)


def normalize(raw: dict, manifest: dict) -> list[dict]:
    aws = manifest.get('aws', {})
    if {'account_id', 'regions', 'services', 'resources', 'alarms'} - aws.keys():
        raise ValueError('explicit AWS scope manifest required')
    if 'us-east-1' not in aws['regions']:
        raise ValueError('global Health event region must be declared')
    if raw.get('account') != aws['account_id']:
        raise ValueError('unexpected AWS account')
    if raw.get('region') not in aws['regions']:
        return []
    source, detail = raw.get('source'), raw.get('detail', {})
    if source == 'aws.health':
        service = detail.get('service')
        if service not in aws['services']:
            return []
        region = detail.get('eventRegion')
        if region not in set(aws['regions']) | {'global'}:
            return []
        category, status = detail.get('eventTypeCategory'), detail.get('statusCode')
        if category not in {'issue', 'scheduledChange'} or status not in {'open', 'upcoming', 'closed'}:
            return []
        entities = [e.get('entityValue') for e in detail.get('affectedEntities', [])]
        if detail.get('eventScopeCode') == 'PUBLIC':
            environments = {manifest['environment']}
        else:
            environments = {aws['resources'][e] for e in entities if e in aws['resources']}
        if not environments:
            return []
        occurred = _timestamp(detail['lastUpdatedTime'])
        identity = detail['eventArn']
        kind = 'aws.health.closed' if status == 'closed' else ('aws.health.scheduled' if category == 'scheduledChange' else 'aws.health.issue')
        severity = 'info' if status == 'closed' else ('warning' if category == 'scheduledChange' else 'critical')
        description = 'AWS 사건 종료 (앱 복구 확인과 별개)' if status == 'closed' else ('AWS 예정 변경' if category == 'scheduledChange' else 'AWS 장애')
        payload = {'kind': kind, 'target': service, 'status': description,
                   'aws_event_arn': identity, 'aws_region': region}
        if category == 'scheduledChange':
            payload['scheduled_at'] = _timestamp(detail['startTime']).isoformat()
    elif source == 'aws.cloudwatch':
        alarm = detail.get('alarmName')
        if alarm not in aws['alarms']:
            return []
        state = detail.get('state', {})
        value = state.get('value')
        if value not in {'ALARM', 'OK', 'INSUFFICIENT_DATA'}:
            return []
        previous = detail.get('previousState', {}).get('value')
        description = {'ALARM': 'AWS 자원 경보', 'INSUFFICIENT_DATA': '관측 불가',
                       'OK': 'AWS 경보 회복' if previous == 'ALARM' else 'AWS 정상 관측'}[value]
        environments = {aws['alarms'][alarm]}
        occurred = _timestamp(state['timestamp'])
        identity = 'cloudwatch:' + raw['account'] + ':' + raw['region'] + ':' + alarm
        status = value
        severity = 'critical' if value == 'ALARM' else ('warning' if value == 'INSUFFICIENT_DATA' else 'info')
        payload = {'kind': 'aws.alarm', 'target': alarm, 'status': description, 'aws_state': value}
    else:
        return []
    result = []
    for environment in sorted(environments):
        if environment not in {'dev', 'staging'}:
            raise ValueError('AWS resource environment is not mapped')
        key = '|'.join([identity, status, occurred.isoformat(), environment])
        result.append(make_event(source=source, environment=environment, severity=severity, channel='development',
            occurred_at=occurred, event_id='aws:' + hashlib.sha256(key.encode()).hexdigest(), payload=payload))
    return result
