/**
 * **자립형 벡터 배경 지도** (WU-C5 · 축 ①-⑤b · Ted 2026-09-08 판정).
 *
 * 왜 있는가 — 사다리가 데이터 경계에 맞춰 축척을 세우면(WU-C4) 화면에는 값만 남고
 * **그 값이 지구 어디인지**가 사라진다. 해안선과 국경 두 줄이 그 자리를 답한다.
 *
 * ⛔ **타일 서버 0 · 외부 CDN 0 · 지도 라이브러리 0** — POL-021 「타일 서버도 바탕 지도도
 *   쓰지 않는다」의 **부분 반전**이다. 반전된 것은 「레포 안에 든 벡터 배경」 하나뿐이고,
 *   외부로 나가는 요청은 여전히 금지다. 그래서 자산은 `fetch` 가 아니라 **정적 import**로
 *   들어온다 — 번들에 굳으면 런타임에 나갈 길이 없다.
 * ⛔ **도시 표기 0** — 자산이 해안선·국경 두 장뿐이라 표기할 점이 아예 없다.
 * ⛔ 좌표 변환을 여기서 다시 쓰지 않는다 — 정본은 `projection.ts` 이고 커서 역산
 *   (`pvLonOf`/`pvLatOf`)이 같은 함수의 역을 쓴다. 두 벌이 되면 배경과 래스터가 어긋난다.
 *
 * 어디에 서는가 — 층 묶음(`.pv-layers`) **맨 아래**, 래스터 밑이다. 층 묶음의 좌표계에서
 * 데이터 경계는 곧 층 전체이므로(WU-C4 `BoundsOutline` 과 같은 근거) 이 SVG 는 층을 가득
 * 채우고, 이동·배율은 층에 걸린 같은 `transform` 이 함께 옮긴다(정본 §8 조건 ⑸).
 * 경계 밖으로 나간 선은 `viewBox` 가 잘라 낸다 — 한반도 프레임으로 **자르지 않는다**.
 */
import { useMemo } from 'react';
import coastline from '../../assets/basemap/ne_110m_coastline.json';
import boundaries from '../../assets/basemap/ne_110m_admin_0_boundary_lines_land.json';
import { lonFractionOf, latFractionOf } from './projection';
import type { GeoBounds } from './scaleLadder';
import './preview.css';

/** `viewBox` 한 변. 비율은 `preserveAspectRatio="none"` 이 죽이므로 값 자체는 눈금일 뿐이다. */
const VB = 1000;

interface LineFeatureCollection {
  features: { geometry: { type: string; coordinates: number[][] | number[][][] } }[];
}

function ringsOf(geometry: { type: string; coordinates: number[][] | number[][][] }): number[][][] {
  return geometry.type === 'MultiLineString'
    ? (geometry.coordinates as number[][][])
    : [geometry.coordinates as number[][]];
}

/**
 * GeoJSON → SVG `d`. **경계를 벗어난 조각도 그린다** — 잘라 내면 옆 나라가 사라지고,
 * Ted 판정(「다른 지역이 나올 수도 있다」)이 지키려던 것이 바로 그 옆 나라다.
 */
export function basemapPathData(fc: LineFeatureCollection, bounds: GeoBounds): string {
  const parts: string[] = [];
  for (const f of fc.features) {
    for (const ring of ringsOf(f.geometry)) {
      let d = '';
      for (let i = 0; i < ring.length; i += 1) {
        const pt = ring[i];
        if (!pt) continue;
        const x = (lonFractionOf(pt[0] as number, bounds) * VB).toFixed(1);
        const y = (latFractionOf(pt[1] as number, bounds) * VB).toFixed(1);
        d += `${i === 0 ? 'M' : 'L'}${x} ${y}`;
      }
      if (d) parts.push(d);
    }
  }
  return parts.join('');
}

export function BasemapLayer(props: { bounds: GeoBounds }) {
  const { bounds } = props;
  const coast = useMemo(() => basemapPathData(coastline as LineFeatureCollection, bounds), [bounds]);
  const border = useMemo(() => basemapPathData(boundaries as LineFeatureCollection, bounds), [bounds]);
  return (
    <svg
      className="pv-basemap"
      data-testid="pv-basemap"
      viewBox={`0 0 ${VB} ${VB}`}
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
    >
      {/* 해안선이 한 단 진하다 — 물과 뭍의 경계가 행정 경계보다 먼저 읽혀야 한다. */}
      <path className="pv-basemap-coast" data-testid="pv-basemap-coastline" d={coast} />
      <path className="pv-basemap-border" data-testid="pv-basemap-boundary" d={border} />
    </svg>
  );
}
