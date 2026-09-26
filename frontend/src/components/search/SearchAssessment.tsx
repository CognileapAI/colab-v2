import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import type { components } from '../../generated/fe-core';
import type { SearchAssessment, SearchContext } from './types';

const variables = { land_surface_temperature: '지표면 온도', air_temperature: '기온', precipitation: '강수량', wind_speed: '풍속', water_quality: '수질', particulate_matter: '미세먼지' };
const statistics = { instantaneous: '순간값', daily_mean: '일평균', daily_max: '일최고', daily_min: '일최저', monthly_mean: '월평균', monthly_mean_daily_max: '일최고값의 월평균', monthly_mean_daily_min: '일최저값의 월평균' };
const regions = { seoul: '서울', jeju: '제주', korean_peninsula: '한반도' };
const labels: Record<string,string> = { variable:'관측 변수',region:'지역',period:'기간',statistics:'통계값',nativeResolutionM:'원래 공간 해상도(m)',platform:'관측 기반',provider:'제공 기관',unit:'단위',representation:'자료 형태',cadence:'시간 간격',directObservation:'직접 관측',format:'파일 형식' };
const conditionLabels: Record<string,string> = { ...labels, maxResolutionM:'최대 공간 해상도(m)',maxCadenceSeconds:'주기',maxMissingRatePercent:'최대 결측률(%)',descriptionAll:'설명에 모두 포함',coverageYear:'관측 연도(겹치는 기간)',uploadedMonth:'플랫폼 등록 월',exactPeriod:'기준 파일과 동일한 기간' };

// 주기 상한(초) → 「1시간 이하」·「30분 이하」. 값은 등록 설명의 선언 주기와 비교한다(intent 2026-09-26-cadence-range-predicate).
function cadenceLimit(seconds: number): string {
  if (seconds % 3600 === 0) return `${seconds / 3600}시간 이하`;
  if (seconds % 60 === 0) return `${seconds / 60}분 이하`;
  return `${seconds}초 이하`;
}

function display(key: string, value: unknown): string {
  if (value == null) return '미확인';
  if (key === 'maxCadenceSeconds' && typeof value === 'number') return cadenceLimit(value);
  if (key === 'variable') return variables[value as keyof typeof variables] ?? String(value);
  if (key === 'region') return regions[value as keyof typeof regions] ?? String(value);
  if (key === 'statistics' && Array.isArray(value)) return value.map(v => statistics[v as keyof typeof statistics] ?? v).join(', ');
  if (key === 'period' && typeof value === 'object') {
    const period = value as { start?: unknown; end?: unknown };
    if (typeof period.start === 'string' && typeof period.end === 'string') return `${period.start} ~ ${period.end}`;
  }
  if (typeof value === 'object') return Object.values(value).join(' ~ ');
  if (typeof value === 'boolean') return value ? '예' : '아니요';
  const terms:Record<string,string> = {spatial:'공간자료',spatial_grid:'공간 격자',point_observations:'공간 좌표가 있는 점 관측',table:'표',array:'배열',satellite:'위성',ground:'지상',model:'모델',mixed:'혼합',daily:'일별',monthly:'월별',weekly:'주별','15min':'15분','5min':'5분','10min':'10분',hourly:'매시',yearly:'연 단위'};
  if (String(value) in terms) return terms[String(value)]!;
  return String(value);
}

export function AssessmentPanel({ assessment, onContext }: { assessment: SearchAssessment; onContext(context: SearchContext): void }) {
  return <section className="notice" aria-label="검색 조건과 근거" data-testid="search-assessment">
    <h2>{assessment.status === 'clarification' ? '먼저 확인할 내용이 있어요' : '조건과 근거로 찾았어요'}</h2>
    <p>{assessment.text}</p>
    <p>{assessment.scope} · {new Date(assessment.asOf).toLocaleDateString('ko-KR', { timeZone:'Asia/Seoul' })} 기준</p>
    <dl>{Object.entries(assessment.conditions).map(([key,value]) => <div key={key}><dt>{conditionLabels[key] ?? key}</dt><dd>{display(key,value)}</dd></div>)}</dl>
    {assessment.questions.length > 0 && <ul>{assessment.questions.map(q => <li key={q}>{q}</li>)}</ul>}
    {(assessment.intent === 'recommend' || assessment.intent === 'compare') && <ResearchForm onContext={onContext} />}
    {assessment.intent === 'reference_match' && <ReferenceForm onContext={onContext} />}
    {assessment.comparisons.map(item => <details key={item.datasetId}>
      <summary>{item.name} — {item.fileName ?? '등록 메타데이터'}의 비교 근거</summary>
      <dl>{Object.entries(labels).map(([key,label]) => <div key={key}><dt>{label}</dt><dd>{display(key,item.facts[key])}</dd></div>)}</dl>
      {item.source && <p>출처: {item.source.label} · {item.source.locator}</p>}
      <Link to={`/datasets/${item.datasetId}`}>자료 상세 보기</Link>
    </details>)}
  </section>;
}

function ResearchForm({ onContext }: { onContext(context: SearchContext): void }) {
  return <details><summary>연구 조건 입력·변경</summary>
    <form onSubmit={e => {
      e.preventDefault();
      const data = new FormData(e.currentTarget);
      if (String(data.get('start')) > String(data.get('end'))) {
        const end=e.currentTarget.elements.namedItem('end') as HTMLInputElement;
        end.setCustomValidity('종료일은 시작일 이후여야 합니다.'); end.reportValidity(); return;
      }
      const stats = data.getAll('statistics') as NonNullable<NonNullable<SearchContext['research']>['statistics']>;
      const resolution = String(data.get('resolution') ?? '');
      onContext({ research: { variable:data.get('variable') as keyof typeof variables,
        region:data.get('region') as keyof typeof regions,
        period:{ start:String(data.get('start')),end:String(data.get('end')) },
        ...(stats.length ? { statistics:stats } : {}), ...(resolution ? { maxResolutionM:Number(resolution) } : {}) } });
    }}>
      <p>이번 검색에 직접 지정한 조건을 사용합니다. 기온과 지표면 온도는 다른 변수입니다.</p>
      <p><label>관측 변수 <select name="variable" required defaultValue=""><option value="" disabled>선택</option>{Object.entries(variables).map(([v,l]) => <option key={v} value={v}>{l}</option>)}</select></label></p>
      <p><label>지역 <select name="region" required defaultValue=""><option value="" disabled>선택</option>{Object.entries(regions).map(([v,l]) => <option key={v} value={v}>{l}</option>)}</select></label></p>
      <p><label>시작일 <input type="date" name="start" required /></label> <label>종료일 <input type="date" name="end" required onChange={e => e.currentTarget.setCustomValidity('')} /></label></p>
      <fieldset><legend>필요한 통계값 (선택)</legend>{Object.entries(statistics).map(([v,l]) => <p key={v}><label><input type="checkbox" name="statistics" value={v} /> {l}</label></p>)}</fieldset>
      <p><label>최대 공간 해상도(m, 선택) <input type="number" name="resolution" min="0.001" step="any" /></label></p>
      <button type="submit">이 연구 조건으로 다시 찾기</button>
    </form>
  </details>;
}

function ReferenceForm({ onContext }: { onContext(context: SearchContext): void }) {
  const [datasets,setDatasets] = useState<components['schemas']['DatasetRow'][]>([]);
  const [files,setFiles] = useState<components['schemas']['DatasetFile'][]>([]);
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  return <div>
    <p>다운로드 완료 이력을 추측하지 않습니다. 비교 기준으로 사용할 자료와 파일을 선택해 주세요.</p>
    <button type="button" disabled={busy} onClick={async () => {
      setBusy(true); setError('');
      try { const r = await api.GET('/datasets'); if (!r.data) throw Error(); setDatasets(r.data.items as components['schemas']['DatasetRow'][]); }
      catch { setError('자료 목록을 불러오지 못했습니다. 다시 시도해 주세요.'); }
      finally { setBusy(false); }
    }}>기준 자료 목록 불러오기</button>
    {datasets.length > 0 && <p><label>기준 자료 <select defaultValue="" disabled={busy} onChange={async e => {
      const datasetId=e.target.value; setFiles([]); setBusy(true); setError('');
      try { const r=await api.GET('/datasets/{datasetId}/files',{params:{path:{datasetId}}}); if (!r.data) throw Error(); const rows=(r.data.items ?? []).filter(f => f.kind==='본체'); setFiles(rows); if (!rows.length) setError('선택할 수 있는 본체 파일이 없습니다.'); }
      catch { setError('파일을 열 수 없습니다. 접근 권한을 확인하거나 다른 자료를 선택해 주세요.'); }
      finally { setBusy(false); }
    }}><option value="" disabled>선택</option>{datasets.map(d => <option key={d.datasetId} value={d.datasetId}>{d.name}</option>)}</select></label></p>}
    {files.length > 0 && <p><label>기준 파일 <select defaultValue="" onChange={e => onContext({referenceFileId:e.target.value})}><option value="" disabled>선택</option>{files.map(f => <option key={f.fileId} value={f.fileId}>{f.fileName}</option>)}</select></label></p>}
    {error && <p role="alert">{error}</p>}
  </div>;
}
