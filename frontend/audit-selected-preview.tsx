// Local browser fixture only. No production API calls or persisted data changes.
import './src/shell/styles';
import tileUrl from './audit-tile.svg?url';
import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { DatasetPreviewSection } from './src/components/datasetpreview/DatasetPreviewSection';
import type { DatasetPreviewSource, DatasetRenderInput } from './src/components/datasetpreview/types';
import type { RenderJob } from './src/components/preview/types';

const query = new URLSearchParams(location.search);
const calls: DatasetRenderInput[] = [];
const descriptions: Array<string | undefined> = [];
const timings: unknown[] = [];
const lookups: string[] = [];
window.addEventListener('colab-preview-timing', (event) => timings.push((event as CustomEvent).detail));
let finished = false;
const legend = { palette: 'viridis', variable: 'rain', unit: 'mm', classes: [{ color: '#21918c', min: 0, max: 5 }] };
const source: DatasetPreviewSource = {
  files: async () => [
    { fileId: 'file-a', fileName: '강수_첫째.nc', renderable: query.get('unsupported') !== '1' },
    { fileId: 'file-b', fileName: '강수_둘째.nc', renderable: query.get('unsupported') !== '1' },
  ],
  describe: async (fileId?: string) => {
    descriptions.push(fileId);
    return { variables: ['rain', 'temperature'], instants: { count: 2, first: '2023-05-01T00:00:00Z', last: '2023-05-02T00:00:00Z' }, default: { variable: 'rain', instant: '2023-05-01T00:00:00Z' } };
  },
  palettes: async () => [{ palette: 'viridis', label: '비리디스' }],
  create: async (input) => {
    calls.push(structuredClone(input));
    finished = false;
    if (query.get('lost') === '1') throw new Error('Local fixture: create response lost');
    return { renderId: `local-${calls.length}`, status: '그리는 중', stage: '지도 그리는 중' };
  },
  get: async (renderId): Promise<RenderJob> => {
    lookups.push(renderId);
    if (query.get('pollError') === '1' && lookups.length === 1) throw new Error('Local fixture: poll response lost');
    if (!finished) return { renderId, status: '그리는 중', stage: '지도 그리는 중' };
    if (query.get('failure') === '1') return { renderId, status: '실패', failure: { code: 'RENDER_TIMEOUT', message: '로컬 검증용 시간 초과 응답입니다.' } };
    return query.get('tiles') === '1'
      ? { renderId, status: '완료', result: { tileUrlTemplate: '/audit-tile.svg?z={z}&x={x}&y={y}', sidecarUrl: '/local-fixture-sidecar', bounds: { west: 126.5, south: 34.8, east: 129.6, north: 37.2 }, legend } }
      : { renderId, status: '완료', result: { imageUrl: tileUrl, legend } };
  },
  probeTile: async () => 'ok',
  mapGeometry: async () => ({ width: 512, height: 512 }),
  screenshot: async () => { throw new Error('Local fixture: screenshot service is unavailable'); },
  lookupValue: async () => { throw new Error('Local fixture: value service is unavailable'); },
};

Object.assign(window, { previewAudit: { calls, descriptions, timings, lookups } });
function Audit() {
  const [, refresh] = useState(0);
  return <main className="detail-page">
    <h1>선택 미리보기 로컬 검증</h1>
    <p>실제 API를 호출하지 않는 검증 화면입니다.</p>
    <button type="button" data-testid="audit-finish" onClick={() => { finished = true; refresh((n) => n + 1); }}>작업 완료 응답 보내기</button>
    <DatasetPreviewSection datasetId="local-dataset" source={source} pollMs={100} />
  </main>;
}
createRoot(document.getElementById('root')!).render(<Audit />);
