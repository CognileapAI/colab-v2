import { useEffect, useRef, useState } from 'react';
import { PermissionGate } from '../../permission/PermissionGate';
import type {
  RepresentativeImageMetadata,
  RepresentativeImageSource,
} from './representativeImageSource';

export function RepresentativeImageSection(props: {
  datasetId: string;
  metadata?: RepresentativeImageMetadata | undefined;
  source: RepresentativeImageSource;
  bodyAccessible: boolean;
}) {
  const [custom, setCustom] = useState(props.metadata?.custom ?? false);
  const [url, setUrl] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const generation = useRef(0);
  const lifecycle = useRef(0);
  const currentUrl = useRef<string | null>(null);

  function replaceUrl(next: string | null) {
    if (currentUrl.current && currentUrl.current !== next) URL.revokeObjectURL(currentUrl.current);
    currentUrl.current = next;
    setUrl(next);
  }

  async function load(): Promise<'loaded' | 'failed' | 'stale'> {
    const gen = ++generation.current;
    setError(null);
    try {
      const blob = await props.source.get(props.datasetId);
      if (gen !== generation.current) return 'stale';
      replaceUrl(URL.createObjectURL(blob));
      setCustom(true);
      return 'loaded';
    } catch (cause) {
      if (gen !== generation.current) return 'stale';
      setError(cause instanceof Error ? cause.message : '대표 그림을 불러오지 못했어요.');
      return 'failed';
    }
  }

  useEffect(() => {
    lifecycle.current += 1;
    generation.current += 1;
    replaceUrl(null);
    setCustom(props.metadata?.custom ?? false);
    setFile(null);
    setBusy(false);
    setError(null);
    if (props.metadata?.custom && props.bodyAccessible) void load();
    return () => {
      lifecycle.current += 1;
      generation.current += 1;
      if (currentUrl.current) URL.revokeObjectURL(currentUrl.current);
      currentUrl.current = null;
    };
  }, [props.datasetId, props.metadata?.custom, props.bodyAccessible, props.source]);

  async function save() {
    if (!file || busy) return;
    const life = lifecycle.current;
    setBusy(true);
    setError(null);
    try {
      const metadata = await props.source.put(props.datasetId, file);
      if (life !== lifecycle.current) return;
      setCustom(metadata.custom);
      setFile(null);
      if ((await load()) === 'failed') {
        setError('대표 그림은 저장했지만 새 그림을 불러오지 못했어요. 다시 불러와 주세요.');
      }
    } catch (cause) {
      if (life === lifecycle.current) {
        setError(cause instanceof Error ? cause.message : '대표 그림을 저장하지 못했어요.');
      }
    } finally {
      if (life === lifecycle.current) setBusy(false);
    }
  }

  async function remove() {
    if (busy) return;
    const life = lifecycle.current;
    setBusy(true);
    setError(null);
    try {
      await props.source.remove(props.datasetId);
      if (life !== lifecycle.current) return;
      generation.current += 1;
      replaceUrl(null);
      setCustom(false);
      setFile(null);
    } catch (cause) {
      if (life === lifecycle.current) {
        setError(cause instanceof Error ? cause.message : '대표 그림을 지우지 못했어요.');
      }
    } finally {
      if (life === lifecycle.current) setBusy(false);
    }
  }

  return (
    <section className="dt-representative" data-testid="detail-representative" aria-label="대표 그림">
      <div className="dt-representative-head">
        <h2>대표 그림</h2>
        <span className="muted">사용자 그림이 없으면 아래 자동 미리보기를 사용해요.</span>
      </div>
      {custom && url ? <img className="dt-representative-image" src={url} alt="사용자 대표 그림" /> : null}
      {custom && !url && !error ? <p role="status">대표 그림을 불러오는 중이에요…</p> : null}
      {error ? <p className="de-err" role="alert">{error}</p> : null}
      {custom && error && !file ? (
        <button type="button" className="btn btn-secondary btn-sm" disabled={busy} onClick={() => void load()}>
          대표 그림 다시 불러오기
        </button>
      ) : null}
      <PermissionGate requires="업로드·편집">
        <div className="dt-representative-actions">
            <label className="btn btn-secondary btn-sm">
              그림 고르기
              <input
                className="th-in"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                data-testid="detail-representative-input"
                onChange={(event) => {
                  setFile(event.target.files?.[0] ?? null);
                  setError(null);
                }}
              />
            </label>
            {file ? (
              <button type="button" className="btn btn-primary btn-sm" disabled={busy} onClick={() => void save()}>
                {error ? '대표 그림 다시 저장' : '대표 그림 저장'}
              </button>
            ) : null}
            {custom ? (
              <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => void remove()}>
                자동 그림 사용
              </button>
            ) : null}
        </div>
      </PermissionGate>
    </section>
  );
}
