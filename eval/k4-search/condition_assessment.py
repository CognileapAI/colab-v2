"""Research evidence assessment: no confidence scores or inferred guarantees."""
import calendar
import datetime as dt
import re


def assess_conditions(query, facts):
    q = re.sub(r'\s+', '', query.lower())
    for month, name in enumerate(('일월','이월','삼월','사월','오월','유월','칠월','팔월','구월','시월','십일월','십이월'), 1):
        q = q.replace('년'+name, f'년{month}월')
    results = {}

    def add(key, status, evidence):
        results[key] = dict(status=status, evidence=evidence, source=facts.get('source'))

    if '결측' in q or '0%' in q:
        add('quality', 'unknown', '결측률 검증 보고서 없음')
    if '보간' in q and any(t in q for t in ('하지않', '안한', '없는')):
        known = facts.get('interpolated')
        add('interpolation', 'contradicted' if known is True else 'supported' if known is False else 'unknown',
            facts.get('interpolation_evidence', '보간 적용 여부 근거 문구 없음'))
    if '직접관측' in q:
        known = facts.get('direct_observation')
        add('direct_observation', 'contradicted' if known is False else 'unknown',
            facts.get('note', '직접 관측 근거 없음'))
    region = ('경기남부충청' if '경기' in q and '충청' in q else
              '제주' if '제주' in q else
              '대한민국시군구' if '시군구' in q else None)
    if region:
        add('region', 'supported' if region == facts.get('region') else 'unknown',
            facts.get('region') or '명시된 지역 근거 없음')
    cadence = ('weekly' if '주간' in q or '매주' in q else
               'daily' if '매일' in q or '일별' in q else
               'monthly' if '월평균' in q or '한달평균' in q else None)
    if cadence:
        actual = facts.get('cadence')
        add('cadence', 'unknown' if not actual else 'supported' if actual == cadence else 'contradicted',
            actual or '공통 시간 주기 근거 없음')
    date = re.search(r'(20\d{2})년(\d{1,2})월(?:(\d{1,2})일)?', q)
    if date:
        try:
            year, month = int(date[1]), int(date[2])
            start = dt.date(year, month, int(date[3]) if date[3] else 1).isoformat()
            end = start if date[3] else dt.date(year, month, calendar.monthrange(year, month)[1]).isoformat()
        except ValueError:
            add('period', 'unknown', '유효하지 않은 날짜')
        else:
            span = facts.get('coverage')
            status = ('unknown' if not span else 'supported' if span[0] <= start <= end <= span[1]
                      else 'contradicted' if end < span[0] or start > span[1] else 'unknown')
            add('period', status, span or '연속 기간 근거 없음')
    elif re.search(r'20\d{2}', q):
        add('period', 'unknown', facts.get('coverage') or '기간 근거 없음')
    return results
