import { useRef, useState } from 'react';
import { useAccount } from '../../permission/session';

/** J-2: 교수 전용이며 서버도 역할·격자 프로필을 다시 판정한다. */
export function DefaultGridButton(props: { datasetId: string; save: (datasetId: string) => Promise<void> }) {
  const account = useAccount();
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  if (account?.role !== '교수') return null;

  async function save() {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      await props.save(props.datasetId);
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : '기본 격자를 지정하지 못했어요. 다시 시도해 주세요.');
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return <div>
    <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => { void save(); }}>
      {busy ? '기본 격자 지정 중…' : '연구실 기본 격자로 지정'}
    </button>
    {error ? <p role="alert" className="warn">{error}</p> : null}
    {saved ? <p role="status">연구실 기본 격자로 지정했어요.</p> : null}
  </div>;
}
