"""Typed search planning and evidence adjudication. No database or model side effects.

Vocabulary expansion cannot relax a hard constraint. A reviewed file is the unit
of conjunction; absent evidence never turns into a supported fact.
"""
from __future__ import annotations

import datetime as dt
import calendar
import re
from zoneinfo import ZoneInfo
from ..kernel import errors
from ..kernel.ids import Ulid

from ..kernel.region_scope import region_match
from ..kernel.search_semantics import SEMANTICS, SEMANTIC_VERSION

SEOUL = ZoneInfo('Asia/Seoul')


def validate_context(value):
    if value is None:
        return {}
    if not isinstance(value,dict) or set(value)-{'research','referenceFileId'}:
        raise errors.bad_request('context는 research 또는 referenceFileId만 받습니다.')
    if 'referenceFileId' in value and (not isinstance(value['referenceFileId'],str) or not Ulid.is_valid(value['referenceFileId'])):
        raise errors.bad_request('기준 파일 식별자가 올바르지 않습니다.')
    research = value.get('research')
    if 'research' in value:
        allowed = {'variable','region','period','statistics','maxResolutionM','maxMissingRatePercent'}
        if not isinstance(research,dict) or not research or set(research)-allowed:
            raise errors.bad_request('연구 조건 필드가 올바르지 않습니다.')
        for key,facet in [('variable','variables'),('region','regions')]:
            if key in research and (not isinstance(research[key],str) or research[key] not in SEMANTICS[facet]):
                raise errors.bad_request(f'연구 {key} 값이 지원하는 의미 식별자가 아닙니다.')
        if 'statistics' in research:
            stats = research['statistics']
            if not isinstance(stats,list) or not stats or any(not isinstance(s,str) or s not in SEMANTICS['statistics'] for s in stats) or len(stats)!=len(set(stats)):
                raise errors.bad_request('통계 유형이 올바르지 않습니다.')
        if 'maxResolutionM' in research:
            import math
            n = research['maxResolutionM']
            if isinstance(n,bool) or not isinstance(n,(float,int)) or not math.isfinite(n) or n<=0:
                raise errors.bad_request('최대 해상도는 양의 유한한 미터 값입니다.')
        if 'maxMissingRatePercent' in research:
            import math
            n = research['maxMissingRatePercent']
            if isinstance(n,bool) or not isinstance(n,(float,int)) or not math.isfinite(n) or not 0<=n<=100:
                raise errors.bad_request('최대 결측률은 0에서 100 사이의 백분율 값입니다.')
        if 'period' in research:
            span = research['period']
            try:
                if not isinstance(span,dict) or set(span)!={'start','end'}:
                    raise ValueError
                for date in span.values():
                    if not isinstance(date,str) or re.fullmatch(r'\d{4}-\d{2}-\d{2}',date) is None:
                        raise ValueError
                    dt.date.fromisoformat(date)
                if span['start']>span['end']:
                    raise ValueError
            except (ValueError,TypeError):
                raise errors.bad_request('연구 기간은 시작일 이하 종료일의 YYYY-MM-DD 값입니다.') from None
    return value


def compact(value):
    return re.sub(r'[\s_\-]+', '', str(value)).casefold()


def canonical(value, facet):
    value = compact(value)
    for key, aliases in SEMANTICS[facet].items():
        if value in {compact(key), *(compact(a) for a in aliases)}:
            return key
    return value


def mentions(query, facet):
    q = compact(query)
    return [key for key, aliases in SEMANTICS[facet].items()
            if any(compact(a) in q for a in aliases)]


def plan_query(query, *, now=None, context=None):
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(SEOUL)
    context = context or {}
    q = compact(query)
    intent = 'discover'
    if '같은기간' in q or '동일한기간' in q:
        intent = 'reference_match'
    elif '특성차이' in q or '비교' in q:
        intent = 'compare'
    elif '적합' in q or '추천' in q:
        intent = 'recommend'
    elif '제일선명' in q or '가장선명' in q or '가장높은해상도' in q:
        intent = 'finest'
    elif '이번달' in q and any(t in q for t in ('새로','올라','업로드','등록')):
        intent = 'latest'
    c, questions = {}, []
    variables = mentions(query, 'variables')
    reference_variable = None
    if intent == 'reference_match' and 'wind_speed' in variables:
        sources = [v for v in variables if v != 'wind_speed']
        reference_variable = sources[0] if len(sources)==1 else None
        variables = ['wind_speed']
    if len(variables) == 1:
        c['variable'] = variables[0]
    elif len(variables) > 1:
        questions.append('찾으려는 관측 변수를 하나 지정해 주세요. 지표면 온도와 기온은 서로 다른 변수입니다.')
    regions = mentions(query, 'regions')
    if len(regions) == 1:
        c['region'] = regions[0]
    elif len(regions) > 1:
        questions.append('검색할 지역을 하나 지정해 주세요.')
    formats = []
    # Parenthesized format examples describe representation, not hard format
    # filters: a georeferenced CSV may represent the same spatial data as NPY.
    format_query = re.sub(r'\([^)]*(?:예\s*[:：]|예를\s*들어)[^)]*\)', '', query)
    for fmt in ('npy','csv','netcdf','tif','hdf5'):
        if re.search(r'(?<![a-z])\.?'+fmt+r'(?![a-z])', format_query, re.I):
            formats.append(fmt)
    if len(formats)==1:
        c['format'] = formats[0]
    elif formats:
        questions.append('포맷을 하나 선택해 주세요. 여러 포맷의 포함·제외 조합은 아직 지원하지 않습니다.')
    if '공간자료' in q:
        c['representation'] = 'spatial'
    if '위성' in q:
        c['platform'] = 'satellite'
    if '영상' in q:
        c['representation'] = 'spatial_grid'
    if '관측' in q:
        c['directObservation'] = True
    if '환경부' in q:
        c['provider'] = '환경부'
    resolution = re.search(r'(\d+(?:\.\d+)?)\s*(km|m)\s*(?:이하|이내)',query,re.I)
    if resolution:
        c['maxResolutionM'] = float(resolution[1]) * (1000 if resolution[2].lower()=='km' else 1)
    if '설명' in q and ('둘다' in q or '모두' in q):
        words = re.findall(r"['\"‘’“”]([^'\"‘’“”]+)['\"‘’“”]", query)
        if len(words) >= 2:
            c['descriptionAll'] = words[:8]
            c.pop('variable',None)  # description words are literal predicates, not product variable claims
        else:
            questions.append('설명에 모두 포함되어야 할 단어를 따옴표로 표시해 주세요.')
    if '작년' in q or '지난해' in q:
        c['coverageYear'] = now.year - 1
    if intent == 'latest':
        c['uploadedMonth'] = now.strftime('%Y-%m')
    # Explicit periods and statistical operations remain distinct from freshness.
    years = re.findall(r'(?<!\d)((?:19|20)\d{2})년?',query)
    month = re.search(r'((?:19|20)\d{2})년\s*(\d{1,2})월',query)
    if len(re.findall(r'\d{1,2}월',query)) > 1:
        questions.append('여러 달에 걸친 기간은 연구 조건의 시작일·종료일로 확인해 주세요.')
    if month:
        year, number = map(int,month.groups())
        if 1 <= number <= 12:
            c['period'] = {'start':f'{year}-{number:02d}-01','end':f'{year}-{number:02d}-{calendar.monthrange(year,number)[1]}'}
        else:
            questions.append('관측 기간의 월을 확인해 주세요.')
    elif len(years)==1:
        c['coverageYear'] = int(years[0])
    elif len(years)==2 and int(years[0])<=int(years[1]):
        c['period'] = {'start':f'{years[0]}-01-01','end':f'{years[1]}-12-31'}
    elif years:
        questions.append('관측 기간의 시작과 끝을 확인해 주세요.')
    stats = []
    if '월평균' in q:
        if '최고' in q: stats.append('monthly_mean_daily_max')
        if '최저' in q: stats.append('monthly_mean_daily_min')
        if not stats: stats.append('monthly_mean')
    elif '일평균' in q:
        stats.append('daily_mean')
    elif '일별' in q or '일최고' in q or '일최저' in q:
        if '최고' in q: stats.append('daily_max')
        if '최저' in q: stats.append('daily_min')
        c['cadence'] = 'daily'
    if stats:
        c['statistics'] = stats
    if '월별' in q:
        c['cadence'] = 'monthly'
    if re.search(r'\d{1,2}일|\d{4}[./-]\d',query):
        questions.append('일 단위 기간은 연구 조건의 시작일·종료일로 명시해 주세요.')
    if intent in ('recommend','compare'):
        research = context.get('research')
        if not research:
            questions.append('연구에 필요한 관측 변수·지역·기간·통계값·최대 공간 해상도를 알려 주세요. 현재 연구 조건이 연결되어 있지 않습니다.')
        else:
            if not all(key in research for key in ('variable','region','period')):
                questions.append('추천 기준으로 관측 변수·지역·기간을 모두 지정해 주세요.')
            for key, value in research.items():
                if key in c and c[key] != value:
                    questions.append(f'질문의 {key} 조건과 연구 조건이 다릅니다. 어느 조건을 사용할지 확인해 주세요.')
                else:
                    c[key] = value
    if intent == 'reference_match' and not context.get('referenceFileId'):
        questions.append('어제 받은 기준 자료의 파일을 선택해 주세요. 다운로드 티켓 발급 이력은 수신 완료나 열람 기록과 다릅니다.')
    recognized = (intent in ('reference_match','latest','finest')
                  or intent in ('recommend','compare') and (bool(context.get('research')) or 'land_surface_temperature' in variables)
                  or bool((c.get('format') or c.get('representation')) and c.get('region')) or bool(c.get('descriptionAll'))
                  or bool(c.get('maxResolutionM')))
    return {'intent':intent, 'conditions':c, 'questions':questions, 'recognized':recognized,
            'asOf':now.isoformat(), 'semanticVersion':SEMANTIC_VERSION,'referenceVariable':reference_variable}


def _predicate(key, wanted, facts, metadata, row, *, expand_region=True):
    if key == 'descriptionAll':
        return all(word.lower() in (metadata.get('summary') or '').lower() for word in wanted)
    if key == 'uploadedMonth':
        value = metadata.get('created_at')
        if not value:
            return None
        stamp = dt.datetime.fromisoformat(value) if isinstance(value,str) else value
        return stamp.astimezone(SEOUL).strftime('%Y-%m') == wanted
    if key == 'format':
        # Extension proves the format requested here, but never spatial geometry.
        name = row.get('file_name','')
        value = facts.get('format') or (name.rsplit('.',1)[-1] if '.' in name else None)
        return None if value is None else str(value).casefold() == wanted.casefold()
    if key == 'coverageYear':
        span = facts.get('period')
        return None if not span else span['start'] <= f'{wanted}-12-31' and span['end'] >= f'{wanted}-01-01'
    if key == 'period':
        span = facts.get('period')
        return None if not span else span['start'] <= wanted['start'] and span['end'] >= wanted['end']
    if key == 'exactPeriod':
        return None if not facts.get('period') else facts['period'] == wanted
    if key == 'maxResolutionM':
        value = facts.get('nativeResolutionM')
        return None if value is None else value <= wanted
    if key == 'maxMissingRatePercent':
        # 데이터셋 단위 술어라 파일 사실이 아니라 후보 줄에서 읽는다 (`uploadedMonth` 와 같은 자리).
        # 자유 입력이 수치로 파싱되지 않은 자료는 근거가 없는 것이지 반증된 것이 아니다 → unknown.
        value = metadata.get('missing_rate_percent')
        return None if value is None else value <= wanted
    if key == 'statistics':
        value = facts.get('statistics')
        return None if value is None else set(wanted) <= set(value)
    if key == 'representation' and wanted == 'spatial':
        value = facts.get(key)
        return None if value is None else value in ('spatial_grid','point_observations')
    value = facts.get(key)
    if value is None:
        return None
    if key == 'region':
        # 직계 하위 한 단계까지(`kernel/region_scope.py` · SQL 후보와 같은 표). 부분 문자열로 넓히지 않는다.
        return region_match(wanted, value, expand=expand_region)[0]
    if key == 'variable':
        return canonical(value, 'variables') == wanted
    return value == wanted


def evaluate(plan, metadata, evidence):
    verdicts = []
    for row in evidence or [{}]:
        facts = row.get('facts',{})
        # reference_match 의 지역은 기준 파일의 지역 그대로다 — 「같은 지역」은 포함 관계가 아니다.
        expand = plan.get('intent') != 'reference_match'
        predicates = {key:_predicate(key,wanted,facts,metadata,row,expand_region=expand)
                      for key,wanted in plan['conditions'].items()}
        status = 'contradicted' if False in predicates.values() else 'unknown' if None in predicates.values() else 'supported'
        verdicts.append({'status':status,'checks':{k:'unknown' if v is None else 'supported' if v else 'contradicted' for k,v in predicates.items()},
                         'fileId':row.get('file_id'),'fileName':row.get('file_name'),
                         'facts':facts, 'source':row.get('source')})
    order = {'supported':0,'unknown':1,'contradicted':2}
    return min(verdicts,key=lambda v:(order[v['status']],v['facts'].get('nativeResolutionM',float('inf')),v['fileId'] or ''))


def respond(plan, matches, *, truncated):
    questions = plan['questions']
    if questions:
        status, message = 'clarification', '추천이나 조건 일치를 확정하기 전에 확인이 필요합니다.'
    elif truncated:
        status, message = 'partial', '후보 조회 한도에 도달했습니다. 지역·변수·기간 조건을 좁혀 주세요. 전체 건수나 최적 자료를 확정하지 않습니다.'
    else:
        status = 'answered'
        message = f"현재 접근 가능한 등록 자료에서 해석된 조건이 확인된 데이터셋은 {len(matches)}건입니다. 데이터셋마다 조건을 충족한 대표 파일을 표시합니다. 조건 근거가 없거나 오래된 자료는 포함하지 않습니다."
        if plan['intent'] in ('recommend','compare'):
            message += ' 명시한 연구 조건을 기준으로 비교했으며, 기록되지 않은 정확도나 연구 적합성은 보장하지 않습니다.'
            if len(matches)==1:
                message += f" 이 조건의 추천 후보는 ‘{matches[0]['name']}’입니다."
            elif len(matches)>1:
                message += ' 여러 자료가 조건을 충족하므로 확인된 정보만으로 하나를 최적이라고 단정하지 않습니다.'
        if plan['intent'] == 'finest' and matches:
            message += ' 확인된 원래 공간 해상도가 작은 순서입니다. 해상도는 자료의 종합 품질과 다릅니다.'
    return {'status':status,'text':message,'questions':questions,'intent':plan['intent'],
            'conditions':plan['conditions'],'asOf':plan['asOf'],'semanticVersion':plan['semanticVersion'],
            'scope':'현재 접근 가능한 플랫폼 등록 자료','candidateLimitReached':truncated,
            'comparisons':matches}
