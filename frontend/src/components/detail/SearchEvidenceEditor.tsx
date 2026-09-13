import { useEffect, useMemo, useRef, useState } from 'react';
import { useWorkProtection } from '../../auth/useWorkProtection';
import { useHasPermission } from '../../permission/PermissionGate';
import type {
  SearchEvidenceFacts,
  SearchEvidenceItem,
  SearchEvidenceSource,
  SearchEvidenceWrite,
} from './searchEvidenceSource';
import { SearchEvidenceRequestError } from './searchEvidenceSource';

const ROLE_OPTIONS = [
  ['model_input', '학습 입력'],
  ['auxiliary_input', '보조 입력'],
  ['validation', '검증'],
  ['prediction', '예측'],
  ['index', '지수'],
  ['documentation', '설명서'],
  ['analysis_code', '분석 코드'],
] as const;

type TriState = '' | 'yes' | 'no';
type FormState = {
  typed: SearchEvidenceFacts;
  roles: SearchEvidenceFacts['roles'];
  periodStart: string;
  periodEnd: string;
  region: string;
  cadence: '' | NonNullable<SearchEvidenceFacts['cadence']>;
  model: string;
  variable: string;
  directObservation: TriState;
  nativeResolutionM: string;
  interpolated: TriState;
  label: string;
  locator: string;
  text: string;
};

function formFrom(item: SearchEvidenceItem): FormState {
  const evidence = item.evidence;
  return {
    typed: Object.fromEntries(Object.entries(evidence?.facts ?? {}).filter(([key]) => ['representation','platform','format','provider','unit','statistics'].includes(key))),
    roles: evidence?.facts.roles ?? [],
    periodStart: evidence?.facts.period?.start ?? '',
    periodEnd: evidence?.facts.period?.end ?? '',
    region: evidence?.facts.region ?? '',
    cadence: evidence?.facts.cadence ?? '',
    model: evidence?.facts.model ?? '',
    variable: evidence?.facts.variable ?? '',
    directObservation: evidence?.facts.directObservation === undefined ? '' : evidence.facts.directObservation ? 'yes' : 'no',
    nativeResolutionM: evidence?.facts.nativeResolutionM?.toString() ?? '',
    interpolated: evidence?.facts.interpolated === undefined ? '' : evidence.facts.interpolated ? 'yes' : 'no',
    label: evidence?.source.label ?? '',
    locator: evidence?.source.locator ?? '',
    text: evidence?.source.text ?? '',
  };
}

function factsFrom(form: FormState): SearchEvidenceFacts {
  const facts: SearchEvidenceFacts = { ...form.typed };
  if (form.roles?.length) facts.roles = form.roles;
  if (form.periodStart && form.periodEnd) facts.period = { start: form.periodStart, end: form.periodEnd };
  if (form.region.trim()) facts.region = form.region.trim();
  if (form.cadence) facts.cadence = form.cadence;
  if (form.model.trim()) facts.model = form.model.trim();
  if (form.variable.trim()) facts.variable = form.variable.trim();
  if (form.directObservation) facts.directObservation = form.directObservation === 'yes';
  if (form.nativeResolutionM) facts.nativeResolutionM = Number(form.nativeResolutionM);
  if (form.interpolated) facts.interpolated = form.interpolated === 'yes';
  return facts;
}

function statusLabel(status: 'draft' | 'reviewed' | 'stale') {
  if (status === 'draft') return '초안';
  if (status === 'reviewed') return '확인됨';
  return '재확인 필요';
}

function roleLabel(role: NonNullable<SearchEvidenceFacts['roles']>[number]) {
  return ROLE_OPTIONS.find(([value]) => value === role)?.[1] ?? role;
}

export function SearchEvidenceEditor(props: {
  datasetId: string;
  fileId: string;
  fileName: string;
  source: SearchEvidenceSource;
  onClose: () => void;
  onDirtyChange?: (dirty: boolean) => void;
}) {
  const [item, setItem] = useState<SearchEvidenceItem | null>(null);
  const [form, setForm] = useState<FormState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const [confirmAction, setConfirmAction] = useState<'close' | 'reload' | null>(null);
  const loadGeneration = useRef(0);
  const canEdit = useHasPermission('업로드·편집');
  const initial = useMemo(() => item ? JSON.stringify(formFrom(item)) : '', [item]);
  const dirty = form !== null && JSON.stringify(form) !== initial;

  useEffect(() => {
    props.onDirtyChange?.(dirty);
    return () => props.onDirtyChange?.(false);
  }, [dirty, props.onDirtyChange]);

  useWorkProtection(`search-evidence:${props.datasetId}:${props.fileId}`, {
    dirty,
    inFlight: saving,
    discard: () => { if (item) setForm(formFrom(item)); },
  });

  async function load() {
    const generation = ++loadGeneration.current;
    setLoading(true);
    setError(null);
    try {
      const result = await props.source.list(props.datasetId);
      const next = result.items.find((candidate) => candidate.fileId === props.fileId);
      if (!next) throw new Error('이 파일은 더 이상 없어요.');
      if (generation === loadGeneration.current) {
        setItem(next);
        setForm(formFrom(next));
        setConflict(false);
      }
    } catch (caught) {
      if (generation === loadGeneration.current) {
        setError(caught instanceof Error ? caught.message : '검색 근거를 불러오지 못했습니다.');
      }
    } finally {
      if (generation === loadGeneration.current) setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    return () => { loadGeneration.current += 1; };
  }, [props.datasetId, props.fileId, props.source]);

  function request(action: 'close' | 'reload') {
    if (dirty) {
      setConfirmAction(action);
      return;
    }
    if (action === 'close') props.onClose();
    else void load();
  }

  function discardAndContinue() {
    const action = confirmAction;
    setConfirmAction(null);
    if (action === 'close') props.onClose();
    if (action === 'reload') void load();
  }

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => current ? { ...current, [key]: value } : current);
  }

  function toggleRole(role: NonNullable<SearchEvidenceFacts['roles']>[number]) {
    if (!form) return;
    const roles = form.roles ?? [];
    set('roles', roles.includes(role) ? roles.filter((candidate) => candidate !== role) : [...roles, role]);
  }

  function setTyped<K extends keyof SearchEvidenceFacts>(key: K, value: SearchEvidenceFacts[K]) {
    if (!form) return;
    const next = { ...form.typed };
    if (value === undefined || value === '' || Array.isArray(value) && value.length === 0) delete next[key];
    else next[key] = value;
    set('typed', next);
  }

  async function save(status: SearchEvidenceWrite['status']) {
    if (!item || !form) return;
    setSaving(true);
    setError(null);
    setConflict(false);
    try {
      await props.source.save(props.datasetId, props.fileId, {
        expectedRevision: item.evidence?.revision ?? 0,
        expectedFileRevision: item.fileRevision,
        facts: factsFrom(form),
        source: { label: form.label.trim(), locator: form.locator.trim(), text: form.text.trim() },
        status,
      });
      await load();
    } catch (caught) {
      const isConflict = (caught instanceof SearchEvidenceRequestError && caught.status === 409)
        || (typeof Response !== 'undefined' && caught instanceof Response && caught.status === 409);
      setConflict(isConflict);
      setError(isConflict ? '다른 변경이 먼저 저장되었습니다. 작성 중인 내용은 그대로 보존했습니다.'
        : caught instanceof Error ? caught.message : '검색 근거를 저장하지 못했습니다.');
    } finally {
      setSaving(false);
    }
  }

  const facts = form ? factsFrom(form) : {};
  const hasFact = Object.keys(facts).length > 0;
  const validSource = Boolean(form?.label.trim() && form.locator.trim() && form.text.trim());
  const periodValid = !form || (!form.periodStart && !form.periodEnd) || Boolean(form.periodStart && form.periodEnd);
  const resolutionValid = !form?.nativeResolutionM || Number(form.nativeResolutionM) > 0;
  const canSave = Boolean(hasFact && validSource && periodValid && resolutionValid && !saving && !loading);

  return (
    <section className="dt-edit" aria-label={`${props.fileName} 검색 근거`}>
      <div className="dt-files-head">
        <strong>{props.fileName} 검색 근거</strong>
        <button type="button" className="btn btn-sm" onClick={() => request('close')} disabled={saving}>닫기</button>
      </div>
      {loading ? <p role="status" aria-live="polite">검색 근거를 불러오는 중입니다.</p> : null}
      {error ? (
        <div className="dt-files-error" role="alert">
          <p>{error}</p>
          {conflict ? <button type="button" className="btn btn-sm" onClick={() => request('reload')}>서버 값 다시 불러오기</button> : null}
          {!conflict ? <button type="button" className="btn btn-sm" onClick={() => request('reload')}>다시 시도</button> : null}
        </div>
      ) : null}
      {confirmAction ? (
        <div className="de-act de-confirm" role="alertdialog" aria-label="작성 중인 검색 근거 처리">
          <p className="de-confirm-msg">작성 중인 내용이 있습니다. 이 내용을 버릴까요?</p>
          <button type="button" className="btn btn-sm" onClick={discardAndContinue}>작성 내용 버리기</button>
          <button type="button" className="btn btn-sm" onClick={() => setConfirmAction(null)}>계속 작성</button>
        </div>
      ) : null}
      {item && form && !canEdit ? (
        <div className="de-grid">
          {item.evidence ? (
            <>
              <p role="status">상태: {statusLabel(item.evidence.status)}{item.evidence.status === 'stale' ? ' — 파일 내용이 바뀌어 재확인이 필요합니다.' : ''}</p>
              <dl>
                <dt>파일 역할</dt><dd>{item.evidence.facts.roles?.map(roleLabel).join(', ') || '미상'}</dd>
                <dt>기간</dt><dd>{item.evidence.facts.period ? `${item.evidence.facts.period.start} ~ ${item.evidence.facts.period.end}` : '미상'}</dd>
                <dt>지역</dt><dd>{item.evidence.facts.region ?? '미상'}</dd>
                <dt>주기</dt><dd>{item.evidence.facts.cadence ?? '미상'}</dd>
                <dt>모델</dt><dd>{item.evidence.facts.model ?? '미상'}</dd>
                <dt>변수</dt><dd>{item.evidence.facts.variable ?? '미상'}</dd>
                <dt>자료 형태</dt><dd>{item.evidence.facts.representation ?? '미상'}</dd>
                <dt>관측 기반</dt><dd>{item.evidence.facts.platform ?? '미상'}</dd>
                <dt>제공 기관</dt><dd>{item.evidence.facts.provider ?? '미상'}</dd>
                <dt>단위</dt><dd>{item.evidence.facts.unit ?? '미상'}</dd>
                <dt>통계 유형</dt><dd>{item.evidence.facts.statistics?.join(', ') || '미상'}</dd>
                <dt>직접 관측</dt><dd>{item.evidence.facts.directObservation === undefined ? '미상' : item.evidence.facts.directObservation ? '예' : '아니요'}</dd>
                <dt>원 관측 해상도</dt><dd>{item.evidence.facts.nativeResolutionM === undefined ? '미상' : `${item.evidence.facts.nativeResolutionM} m`}</dd>
                <dt>보간</dt><dd>{item.evidence.facts.interpolated === undefined ? '미상' : item.evidence.facts.interpolated ? '예' : '아니요'}</dd>
                <dt>설명서 이름</dt><dd>{item.evidence.source.label}</dd>
                <dt>절 또는 문단</dt><dd>{item.evidence.source.locator}</dd>
                <dt>원문 발췌</dt><dd>{item.evidence.source.text}</dd>
              </dl>
            </>
          ) : <p className="fieldnote">저장된 검색 근거가 없습니다.</p>}
        </div>
      ) : null}
      {item && form && canEdit ? (
        <form className="de-grid" aria-label={`${props.fileName} 검색 근거`} onSubmit={(event) => event.preventDefault()}>
          {item.evidence ? (
            <p role="status" aria-live="polite">
              상태: {statusLabel(item.evidence.status)}
              {item.evidence.status === 'stale' ? ' — 파일 내용이 바뀌어 재확인이 필요합니다.' : ''}
            </p>
          ) : <p className="fieldnote">저장된 검색 근거가 없습니다.</p>}
          <fieldset>
            <legend>파일 역할 (여러 개 선택 가능)</legend>
            {ROLE_OPTIONS.map(([value, label]) => (
              <label key={value}>
                <input type="checkbox" checked={form.roles?.includes(value) ?? false} onChange={() => toggleRole(value)} />
                {label}
              </label>
            ))}
          </fieldset>
          <div className="de-row"><label className="de-k" htmlFor={`se-label-${props.fileId}`}>설명서 이름</label><input className="de-v" id={`se-label-${props.fileId}`} maxLength={200} required value={form.label} onChange={(e) => set('label', e.target.value)} /></div>
          <div className="de-row"><label className="de-k" htmlFor={`se-locator-${props.fileId}`}>절 또는 문단</label><input className="de-v" id={`se-locator-${props.fileId}`} maxLength={300} required value={form.locator} onChange={(e) => set('locator', e.target.value)} /></div>
          <div className="de-row"><label className="de-k" htmlFor={`se-text-${props.fileId}`}>원문 발췌</label><textarea className="de-v" id={`se-text-${props.fileId}`} maxLength={20000} required value={form.text} onChange={(e) => set('text', e.target.value)} /></div>
          <div className="de-row"><label className="de-k" htmlFor={`se-start-${props.fileId}`}>기간 시작</label><input className="de-v" id={`se-start-${props.fileId}`} type="date" value={form.periodStart} onChange={(e) => set('periodStart', e.target.value)} /></div>
          <div className="de-row"><label className="de-k" htmlFor={`se-end-${props.fileId}`}>기간 끝</label><input className="de-v" id={`se-end-${props.fileId}`} type="date" value={form.periodEnd} onChange={(e) => set('periodEnd', e.target.value)} /></div>
          {!periodValid ? <p role="alert">기간은 시작과 끝을 함께 입력해 주세요.</p> : null}
          <div className="de-row"><label className="de-k" htmlFor={`se-region-${props.fileId}`}>지역</label><input className="de-v" id={`se-region-${props.fileId}`} maxLength={500} value={form.region} onChange={(e) => set('region', e.target.value)} /></div>
          <div className="de-row"><label className="de-k" htmlFor={`se-cadence-${props.fileId}`}>주기</label><select className="de-v" id={`se-cadence-${props.fileId}`} value={form.cadence} onChange={(e) => set('cadence', e.target.value as FormState['cadence'])}><option value="">미상</option><option value="15min">15분</option><option value="daily">매일</option><option value="weekly">매주</option><option value="monthly">매월</option></select></div>
          <div className="de-row"><label className="de-k" htmlFor={`se-model-${props.fileId}`}>모델</label><input className="de-v" id={`se-model-${props.fileId}`} maxLength={500} value={form.model} onChange={(e) => set('model', e.target.value)} /></div>
          <div className="de-row"><label className="de-k" htmlFor={`se-variable-${props.fileId}`}>변수</label><input className="de-v" id={`se-variable-${props.fileId}`} maxLength={500} value={form.variable} onChange={(e) => set('variable', e.target.value)} /></div>
          <p className="fieldnote">지표면 온도와 기온은 다릅니다. 파일 형식만으로 공간자료 여부를 판단하지 말고 출처를 확인해 주세요.</p>
          {([
            ['representation','자료 형태',[['spatial_grid','공간 격자'],['point_observations','공간 좌표가 있는 점 관측'],['table','표'],['array','배열']]],
            ['platform','관측 기반',[['satellite','위성'],['ground','지상'],['model','모델'],['mixed','혼합']]],
            ['format','파일 형식',[['npy','NPY'],['csv','CSV'],['netcdf','NetCDF'],['tif','TIFF'],['hdf5','HDF5']]],
          ] as const).map(([key,label,options]) => <div className="de-row" key={key}><label className="de-k" htmlFor={`se-${key}-${props.fileId}`}>{label}</label><select className="de-v" id={`se-${key}-${props.fileId}`} value={form.typed[key] ?? ''} onChange={e => setTyped(key,e.target.value as SearchEvidenceFacts[typeof key])}><option value="">미상</option>{options.map(([v,l]) => <option key={v} value={v}>{l}</option>)}</select></div>)}
          {([['provider','제공 기관',200],['unit','단위',100]] as const).map(([key,label,max]) => <div className="de-row" key={key}><label className="de-k" htmlFor={`se-${key}-${props.fileId}`}>{label}</label><input className="de-v" id={`se-${key}-${props.fileId}`} maxLength={max} value={form.typed[key] ?? ''} onChange={e => setTyped(key,e.target.value)} /></div>)}
          <fieldset><legend>통계 유형</legend>{([
            ['instantaneous','순간값'],['daily_mean','일평균'],['daily_max','일최고'],['daily_min','일최저'],['monthly_mean','월평균'],['monthly_mean_daily_max','일최고값의 월평균'],['monthly_mean_daily_min','일최저값의 월평균'],
          ] as const).map(([value,label]) => <label key={value}><input type="checkbox" checked={form.typed.statistics?.includes(value) ?? false} onChange={() => {
            const values=form.typed.statistics ?? [];
            setTyped('statistics',values.includes(value) ? values.filter(v => v!==value) : [...values,value]);
          }} />{label}</label>)}</fieldset>
          <div className="de-row"><label className="de-k" htmlFor={`se-observed-${props.fileId}`}>직접 관측</label><select className="de-v" id={`se-observed-${props.fileId}`} value={form.directObservation} onChange={(e) => set('directObservation', e.target.value as TriState)}><option value="">미상</option><option value="yes">예</option><option value="no">아니요</option></select></div>
          <div className="de-row"><label className="de-k" htmlFor={`se-resolution-${props.fileId}`}>원 관측 해상도 (m)</label><input className="de-v" id={`se-resolution-${props.fileId}`} type="number" min="0.000001" step="any" value={form.nativeResolutionM} onChange={(e) => set('nativeResolutionM', e.target.value)} /></div>
          {!resolutionValid ? <p role="alert">원 관측 해상도는 0보다 큰 값으로 입력해 주세요.</p> : null}
          <div className="de-row"><label className="de-k" htmlFor={`se-interpolated-${props.fileId}`}>보간</label><select className="de-v" id={`se-interpolated-${props.fileId}`} value={form.interpolated} onChange={(e) => set('interpolated', e.target.value as TriState)}><option value="">미상</option><option value="yes">예</option><option value="no">아니요</option></select></div>
          {!hasFact ? <p className="fieldnote">파일 역할 또는 적용 범위 사실을 하나 이상 입력해 주세요.</p> : null}
          <div className="de-act">
            <button type="button" className="btn btn-sm" disabled={!canSave} onClick={() => void save('draft')}>초안 저장</button>
            <button type="button" className="btn btn-primary btn-sm" disabled={!canSave} onClick={() => void save('reviewed')}>확인하고 저장</button>
          </div>
        </form>
      ) : null}
    </section>
  );
}
