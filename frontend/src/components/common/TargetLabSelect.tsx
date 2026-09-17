import { useEffect, useState } from 'react';
import { api, type Schemas } from '../../api/client';

export function TargetLabSelect(props: { value: string; onChange(value: string): void; disabled?: boolean | undefined }) {
  const [labs, setLabs] = useState<Schemas['AccountOptions']['labs']>([]);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let alive = true;
    setError('');
    void api.GET('/admin/account-options').then(({ data }) => {
      if (!data) throw new Error('연구실 목록을 불러오지 못했어요.');
      if (alive) setLabs(data.labs);
    }).catch(() => { if (alive) setError('연구실 목록을 불러오지 못했어요.'); });
    return () => { alive = false; };
  }, [attempt]);
  return <div className="pj-row">
    <label>대상 연구실<select className="pj-inp" aria-label="대상 연구실" value={props.value}
      disabled={props.disabled} onChange={event => props.onChange(event.target.value)}>
      <option value="">연구실을 선택해 주세요</option>
      {labs.map(lab => <option key={lab.labId} value={lab.labId}>{lab.name}</option>)}
    </select></label>
    {error ? <p role="alert">{error} <button type="button" className="btn" onClick={() => setAttempt(n => n + 1)}>다시 불러오기</button></p> : null}
  </div>;
}
