"""Bounded metadata candidates for typed search, under the caller's RLS scope.

No raw files, source bodies or model payloads are loaded. Predicates are bound
parameters; a cap is reported by the application and never presented as a total.
"""
from sqlalchemy import text
import json
import re
from ..kernel.search_semantics import SEMANTICS

LIMIT = 200


def _percentage(value):
    """백분율 인자를 0~100 의 수로 못박는다. bool 은 수가 아니다.

    호출자가 검증했다고 믿지 않는다 — 이 함수는 HTTP 밖(오라클·도구)에서도 불린다.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
        raise ValueError('maxMissingRatePercent must be a number in 0..100')
    if not 0 <= value <= 100:
        raise ValueError('maxMissingRatePercent must be a number in 0..100')
    return float(value)


def candidates(session, conditions, *, verified_ids=None):
    where = ['d.deleted_at IS NULL']
    params = {'limit':LIMIT+1}
    if verified_ids is not None:
        where.append('d.id::text IN (SELECT jsonb_array_elements_text(CAST(:verified_ids AS jsonb)))')
        params['verified_ids'] = json.dumps(verified_ids)
    for index, word in enumerate(conditions.get('descriptionAll',[])):
        where.append(f"position(:word{index} in lower(coalesce(dd.summary,''))) > 0")
        params[f'word{index}'] = word.casefold()
    if conditions.get('uploadedMonth'):
        where.append("to_char(d.uploaded_at AT TIME ZONE 'Asia/Seoul','YYYY-MM')=:month")
        params['month'] = conditions['uploadedMonth']
    if 'maxMissingRatePercent' in conditions:
        # 결측률은 파일이 아니라 데이터셋의 **대표 변수** 사실이라 file_checks 가 아닌 여기 산다.
        # 읽는 칸은 원본에서 파생된 수치(`0043`)다 — facts 사본이 아니므로 등록·수정이 그 자리에
        # 반영된다. 파싱 불가·미기재는 NULL 이라 EXISTS 가 서지 않고 조용히 넓어지지 않는다.
        params['missing_rate'] = _percentage(conditions['maxMissingRatePercent'])
        where.append('''EXISTS (SELECT 1 FROM d3_dataset_variable v
            WHERE v.dataset_id=d.id AND v.is_representative
              AND v.missing_rate_percent <= :missing_rate)''')
    # Apply hard predicates before LIMIT. Unrelated recent uploads must not crowd
    # an older matching product out of the candidate window. One EXISTS means
    # every requested property belongs to the same current reviewed file.
    file_checks = []
    for index,(key,value) in enumerate(conditions.items()):
        arg = f'v{index}'
        params[arg] = value
        if key in ('descriptionAll','uploadedMonth','maxMissingRatePercent'):
            params.pop(arg)
            continue
        if key in ('variable','region'):
            facet = 'variables' if key=='variable' else 'regions'
            aliases = [value,*SEMANTICS[facet].get(value,[])]
            params[arg] = json.dumps([re.sub(r'[\s_\-]+','',v).casefold() for v in aliases])
            file_checks.append(f"regexp_replace(lower(e.facts->>'{key}'),'[[:space:]_-]+','','g') IN (SELECT jsonb_array_elements_text(CAST(:{arg} AS jsonb)))")
        elif key == 'format':
            file_checks.append(f"lower(coalesce(e.facts->>'format',substring(f.file_name from '[^.]+$')))=:{arg}")
        elif key == 'representation' and value == 'spatial':
            file_checks.append("e.facts->>'representation' IN ('spatial_grid','point_observations')")
            params.pop(arg)
        elif key == 'maxResolutionM':
            file_checks.append(f"CASE WHEN jsonb_typeof(e.facts->'nativeResolutionM')='number' THEN (e.facts->>'nativeResolutionM')::numeric <= :{arg} ELSE false END")
        elif key == 'coverageYear':
            params[arg] = str(value)
            file_checks.append(f"e.facts->'period'->>'start' <= :{arg} || '-12-31' AND e.facts->'period'->>'end' >= :{arg} || '-01-01'")
        elif key == 'period':
            params[arg] = value['start']; params[arg+'end'] = value['end']
            file_checks.append(f"e.facts->'period'->>'start' <= :{arg} AND e.facts->'period'->>'end' >= :{arg}end")
        elif key == 'exactPeriod':
            params[arg] = json.dumps(value)
            file_checks.append(f"e.facts->'period'=CAST(:{arg} AS jsonb)")
        elif key == 'statistics':
            params[arg] = json.dumps(value)
            file_checks.append(f"e.facts->'statistics' @> CAST(:{arg} AS jsonb)")
        elif key in ('platform','provider','representation','cadence','directObservation'):
            params[arg] = json.dumps(value)
            file_checks.append(f"e.facts->'{key}'=CAST(:{arg} AS jsonb)")
        else:
            # Unknown predicate cannot broaden search silently.
            raise ValueError('unsupported typed predicate')
    evidence_query = '''SELECT e.facts,e.file_id,f.file_name,e.source_label,e.source_locator,e.source_sha256,e.revision,e.file_revision
            FROM d3_search_evidence e JOIN d3_file f
            ON f.id=e.file_id AND f.dataset_id=e.dataset_id AND f.lab_id=e.lab_id
            WHERE e.dataset_id=d.id AND e.status='reviewed' AND e.file_revision=f.content_revision
              AND f.kind='본체' AND ('''+') AND ('.join(file_checks or ['true'])+''')
            ORDER BY CASE WHEN jsonb_typeof(e.facts->'nativeResolutionM')='number'
                      THEN (e.facts->>'nativeResolutionM')::numeric END NULLS LAST,e.file_id LIMIT 1'''
    # 대표 변수의 파생 결측률을 후보 줄에 함께 싣는다 — 판정부(`client_search._predicate`)가
    # 데이터셋 단위 술어를 `descriptionAll`·`uploadedMonth` 와 같은 자리에서 되읽기 위해서다.
    # 이 값은 응답 항목에 실리지 않는다(`routes/catalog.py` 는 verdict 와 `_compose` 만 쓴다).
    rows = session.execute(text('''SELECT d.id dataset_id,dd.name,dd.summary,
        d.uploaded_at created_at,d.last_modified_at,
        (SELECT v.missing_rate_percent FROM d3_dataset_variable v
          WHERE v.dataset_id=d.id AND v.is_representative) missing_rate_percent,
        ev.* FROM d3_dataset d
        JOIN d3_dataset_description dd ON dd.dataset_id=d.id
        JOIN LATERAL ('''+evidence_query+''') ev ON true
        WHERE '''+' AND '.join(where)+''' ORDER BY d.uploaded_at DESC,d.id LIMIT :limit'''),params).mappings().all()
    out = []
    for row in rows[:LIMIT]:
        out.append({'dataset_id':row['dataset_id'],'name':row['name'],'summary':row['summary'],
                    'created_at':row['created_at'],
                    'missing_rate_percent':(None if row['missing_rate_percent'] is None
                                            else float(row['missing_rate_percent'])),
                    'evidence':{
                        'file_id':row['file_id'],'file_name':row['file_name'],'facts':row['facts'],
                        'source':{'label':row['source_label'],'locator':row['source_locator'],'sha256':row['source_sha256']}},
                    'receipt':{'file_id':row['file_id'],'revision':row['revision'],'file_revision':row['file_revision'],
                               'modified':row['last_modified_at'].isoformat()}})
    return out, len(rows)>LIMIT


def current_receipts(session, receipts):
    if not receipts:
        return set()
    # Last bounded recheck after composition: READ COMMITTED must not publish
    # evidence which was replaced or lost body access between the two reads.
    return set(session.execute(text('''SELECT f.id FROM
        jsonb_to_recordset(CAST(:receipts AS jsonb)) AS r(file_id text,revision integer,file_revision integer,modified timestamptz)
        JOIN d3_file f ON f.id::text=r.file_id AND f.content_revision=r.file_revision
        JOIN d3_search_evidence e ON e.file_id=f.id AND e.revision=r.revision AND e.status='reviewed'
           AND e.file_revision=f.content_revision
        JOIN d3_dataset d ON d.id=f.dataset_id AND d.deleted_at IS NULL AND d.last_modified_at=r.modified
        '''),{'receipts':json.dumps(receipts)}).scalars())


def reference(session, file_id):
    # File RLS enforces current body access, in addition to dataset visibility.
    return session.execute(text('''SELECT f.dataset_id,f.file_name,e.facts FROM d3_file f
        JOIN d3_dataset d ON d.id=f.dataset_id
        LEFT JOIN d3_search_evidence e ON e.file_id=f.id AND e.dataset_id=f.dataset_id
          AND e.status='reviewed' AND e.file_revision=f.content_revision
        WHERE f.id=:id AND f.kind='본체' AND d.deleted_at IS NULL'''), {'id':file_id}).mappings().first()
