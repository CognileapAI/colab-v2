// 타일 모자이크의 셈 — **웹 메르카토르 `z/x/y` 역변환 하나뿐이다.**
//
// 서버가 내는 타일은 표준 XYZ 다(`services/viz-render/.../tiles.py` — 「필요한 것은 웹
// 메르카토르 역변환 공식 하나뿐」). 화면 쪽도 같은 셈만 한다 — **지도 라이브러리를
// 끌어오지 않는다.** 층 겹치기·기저 지도·좌표 표시가 없으므로 위젯이 할 일이 없고,
// 있는 것을 쓰면 이 화면이 지도 편집기가 된다(정본 §8 겹쳐 보기 행의 이유와 같다).
//
// **여기서 정하지 않는 것** — 한계 배율. 그것은 **데이터가 가진 해상도**에서 오고
// (정본 v2.6 §8 조건 ⑷) 사이드카가 말한다. 이 파일은 배율을 받아 레벨을 고를 뿐이다.

/** XYZ 타일 한 변. 서버와 같은 값이어야 한다 (`tiles.py TILE_SIZE`). */
export const TILE_SIZE = 256;

export interface Bounds {
  west: number;
  south: number;
  east: number;
  north: number;
}

export interface TilePiece {
  z: number;
  x: number;
  y: number;
  /** 층 묶음(배율 1 기준) 안에서의 자리와 크기 — 퍼센트가 아니라 픽셀이다. */
  left: number;
  top: number;
  width: number;
  height: number;
}

/** 경도 → 세계 x (0~1). */
export function worldX(lon: number): number {
  return (lon + 180) / 360;
}

/** 위도 → 세계 y (0~1 · 북이 0). */
export function worldY(lat: number): number {
  const φ = (Math.max(-85.05112878, Math.min(85.05112878, lat)) * Math.PI) / 180;
  return (1 - Math.log(Math.tan(φ) + 1 / Math.cos(φ)) / Math.PI) / 2;
}

/**
 * 기본 레벨 — **배율 1 에서 타일 한 장이 화면 픽셀과 대략 1:1 이 되는 레벨.**
 * 더 낮게 잡으면 처음부터 뭉개져 보이고, 더 높게 잡으면 처음부터 조각을 과하게 받는다.
 */
export function baseLevel(bounds: Bounds, boxWidth: number): number {
  const spanX = Math.max(worldX(bounds.east) - worldX(bounds.west), 1e-12);
  if (!(boxWidth > 0)) return 0;
  return Math.max(0, Math.round(Math.log2(boxWidth / (TILE_SIZE * spanX))));
}

/**
 * 지금 배율에 맞는 레벨. **배율이 두 배가 되면 레벨이 하나 오른다** —
 * 정본 §8 「그 배율에 맞는 촘촘함으로 바꿔 끼운다」가 이 문장이다.
 * `maxScale` 은 데이터가 가진 해상도에서 온 한계이고, 레벨도 거기서 멈춘다(조건 ⑷).
 */
export function levelFor(base: number, scale: number, maxScale: number): number {
  const step = Math.round(Math.log2(Math.max(scale, 1)));
  const cap = Math.ceil(Math.log2(Math.max(maxScale, 1)));
  return base + Math.max(0, Math.min(step, cap));
}

/**
 * 지금 보이는 자리를 덮는 조각들. **보이지 않는 조각은 만들지 않는다** — 한계 배율에서
 * 전체를 다 세우면 조각이 수백 장이 되고, 그때 확대가 「기다리는 일」이 된다(정본 §8).
 *
 * `view` 는 층 묶음에 걸린 변환이다(`translate(x,y) scale(s)` · 원점 0 0).
 */
export function visibleTiles(
  bounds: Bounds,
  box: { width: number; height: number },
  level: number,
  view: { scale: number; x: number; y: number },
): TilePiece[] {
  if (!(box.width > 0) || !(box.height > 0)) return [];
  const wx0 = worldX(bounds.west);
  const wx1 = worldX(bounds.east);
  const wy0 = worldY(bounds.north);
  const wy1 = worldY(bounds.south);
  const spanX = Math.max(wx1 - wx0, 1e-12);
  const spanY = Math.max(wy1 - wy0, 1e-12);
  const n = 2 ** level;

  // 층 묶음 좌표 ↔ 세계 좌표
  const tileW = (box.width / spanX) / n;
  const tileH = (box.height / spanY) / n;

  // 화면에 실제로 보이는 층 묶음 좌표 구간 (변환의 역이다)
  const s = Math.max(view.scale, 1e-9);
  const left = (0 - view.x) / s;
  const top = (0 - view.y) / s;
  const right = (box.width - view.x) / s;
  const bottom = (box.height - view.y) / s;

  const i0 = Math.max(Math.floor(wx0 * n), Math.floor(wx0 * n + left / tileW));
  const i1 = Math.min(Math.ceil(wx1 * n) - 1, Math.floor(wx0 * n + (right - 1e-9) / tileW));
  const j0 = Math.max(Math.floor(wy0 * n), Math.floor(wy0 * n + top / tileH));
  const j1 = Math.min(Math.ceil(wy1 * n) - 1, Math.floor(wy0 * n + (bottom - 1e-9) / tileH));

  const out: TilePiece[] = [];
  for (let j = j0; j <= j1; j += 1) {
    for (let i = i0; i <= i1; i += 1) {
      if (i < 0 || j < 0 || i >= n || j >= n) continue;
      out.push({
        z: level,
        x: i,
        y: j,
        left: (i / n - wx0) * (box.width / spanX),
        top: (j / n - wy0) * (box.height / spanY),
        width: tileW,
        height: tileH,
      });
    }
  }
  return out;
}
