/**
 * ⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 1·2·3⟩ — 화면이 **문장을 가르지 않는다.**
 *
 * 무엇이 닫히는가 (스윕 `C-1`·`A-1`)
 *  ⑴ `REFERENCE_GRID_MISSING` 한 코드가 사다리 1·2·3단을 전부 싣고 왔고, 화면이 서버의
 *     한국어 문장을 **정규식으로** 갈랐다. 복합 문장에서 **먼저 맞는 정규식이 이겨**
 *     실제로 오분류했고, 두 서비스가 같은 문장의 **인자 순서를 반대로** 써서 화면이
 *     두 형상을 맞바꿔 말했다. **에러는 안 났다.**
 *  ⑵ ①썸네일이 성공 응답에 실릴 자리가 없어 **실패 봉투로만** 화면에 닿았다 —
 *     즉 **렌더가 성공할수록 썸네일이 안 보였다.**
 */
import { describe, expect, it } from 'vitest';
import { gridState } from '../src/components/upload/gridFlow';
import { layersOf } from '../src/components/upload/previewResult';
import type { RenderResult } from '../src/components/upload/types';

const LEGEND = { palette: 'viridis', classes: [{ color: '#440154', min: 0, max: 5 }] };

describe('§E.2 거절 3상태 — 구조화된 필드로 가른다', () => {
  it('형상 불일치: 사유와 숫자 형상을 그대로 읽는다', () => {
    const s = gridState({
      hasGrid: true,
      failure: { code: 'REFERENCE_GRID_MISSING' },
      gridRejection: {
        reason: '형상 불일치',
        shapes: { dataShape: [2881, 2305], gridShape: [1024, 1024] },
      },
    } as never);
    expect(s?.name).toBe('형상 불일치');
    expect(s?.shapes).toEqual({ data: '2881 × 2305', grid: '1024 × 1024' });
  });

  it('짝 불일치: 위도·경도 형상을 각자 자기 이름으로 읽는다', () => {
    const s = gridState({
      hasGrid: true,
      failure: { code: 'REFERENCE_GRID_MISSING' },
      gridRejection: {
        reason: '짝 불일치',
        shapes: { latShape: [8, 8], lonShape: [10, 10] },
      },
    } as never);
    expect(s?.name).toBe('짝 불일치');
    expect(s?.shapes).toEqual({ lat: '8 × 8', lon: '10 × 10' });
  });

  it('축 판별 실패: 사유만으로 선다', () => {
    const s = gridState({
      hasGrid: true,
      failure: { code: 'REFERENCE_GRID_MISSING' },
      gridRejection: { reason: '축 판별 실패' },
    } as never);
    expect(s?.name).toBe('축 판별 실패');
  });

  it('⚠ 복합 문장이 와도 구조화된 사유가 이긴다 — 정규식 순서가 뒤집지 않는다', () => {
    // 서버 문장에는 아랫단 사유가 괄호로 딸려 온다. 옛 화면은 그 안쪽을 먼저 맞혔다.
    const s = gridState({
      hasGrid: true,
      failure: {
        code: 'REFERENCE_GRID_MISSING',
        details: {
          detail:
            '격자 형상이 데이터와 안 맞는다: 데이터 (8, 8) vs 격자 (10, 10) ' +
            '(축을 판별하지 못했다(a/b): 두 배열 모두 값이 ±90 안에 있어)',
        },
      },
      gridRejection: { reason: '형상 불일치', shapes: { dataShape: [8, 8], gridShape: [10, 10] } },
    } as never);
    expect(s?.name).toBe('형상 불일치');
  });

  it('⚠ 두 서비스의 인자 순서가 달라도 형상이 뒤바뀌지 않는다 — 이름으로 읽기 때문이다', () => {
    // viz-render 는 「데이터 … vs 격자 …」, pipeline-worker 는 「격자 … vs 데이터 …」로 쓴다.
    // 문장 순서로 채우면 화면이 두 형상을 맞바꿔 말한다. 이름 붙은 필드는 그럴 수 없다.
    const s = gridState({
      hasGrid: true,
      failure: { code: 'REFERENCE_GRID_MISSING' },
      gridRejection: {
        reason: '형상 불일치',
        // 순서를 일부러 뒤집어 넣는다 — 결과는 같아야 한다
        shapes: { gridShape: [10, 10], dataShape: [8, 8] },
      },
    } as never);
    expect(s?.shapes).toEqual({ data: '8 × 8', grid: '10 × 10' });
  });

  it('격자를 안 올렸는데 거절 필드도 없으면 「좌표 없음」이다 — 거절이 아니라 보류다', () => {
    const s = gridState({
      hasGrid: false,
      failure: { code: 'REFERENCE_GRID_MISSING', details: { detail: '기준 격자 디렉터리가 없다' } },
    } as never);
    expect(s?.name).toBe('좌표 없음');
  });
});

describe('§〈88〉 묶음 3 — 성공 응답이 세 층을 다 말한다', () => {
  it('지도형 성공에서 ①②③이 모두 읽힌다', () => {
    const result = {
      imageUrl: 'https://viz.example/p/map.png',
      thumbnailUrl: 'https://viz.example/p/thumb.webp',
      valuePreviewUrl: 'https://viz.example/p/detail.png',
      sidecarUrl: 'https://viz.example/p/box.json',
      bounds: { west: 124, south: 33, east: 132, north: 39 },
      legend: LEGEND,
    } as unknown as RenderResult;
    expect(layersOf(result)).toEqual({
      thumbnailUrl: 'https://viz.example/p/thumb.webp',
      valuePreviewUrl: 'https://viz.example/p/detail.png',
      mainImageUrl: 'https://viz.example/p/map.png',
    });
  });

  it('비지도형 성공에서도 ①썸네일이 살아 있다 — 성공할수록 안 보이던 자리다', () => {
    const result = {
      imageUrl: 'https://viz.example/p/detail.png',
      thumbnailUrl: 'https://viz.example/p/thumb.webp',
      valuePreviewUrl: 'https://viz.example/p/detail.png',
      legend: LEGEND,
    } as unknown as RenderResult;
    expect(layersOf(result).thumbnailUrl).toBe('https://viz.example/p/thumb.webp');
  });

  it('썸네일이 없는 결과에서 URL 을 지어내지 않는다', () => {
    const result = {
      imageUrl: 'https://viz.example/p/detail.png',
      legend: LEGEND,
    } as unknown as RenderResult;
    expect(layersOf(result).thumbnailUrl).toBeUndefined();
  });
});

// ───────────────────────────────────────────────────────────────────────────
// `격자 전송 중` 은 **격자가 있을 때만** 성립한다
//
// `transfer` 는 본체+격자 전체 바이트라, 격자가 없는데도 이 상태가 서면
// 화면이 「격자 파일을 받는 중입니다」라고 **틀린 말**을 한다.
describe('§E.2 격자 전송 중 — 격자가 없으면 그 상태가 아니다', () => {
  it('격자가 있으면 전송 중이다', () => {
    const s = gridState({ hasGrid: true, transfer: { sentBytes: 1, totalBytes: 2 } } as never);
    expect(s?.name).toBe('격자 전송 중');
  });

  it('격자가 없으면 전송 중이라고 말하지 않는다', () => {
    const s = gridState({ hasGrid: false, transfer: { sentBytes: 1, totalBytes: 2 } } as never);
    expect(s?.name).not.toBe('격자 전송 중');
  });
});
