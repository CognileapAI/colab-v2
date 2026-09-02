// HSR 격자 업로드 흐름의 **상태 기계와 문구** — `S1-PLAN-REFOUND §E.2`·`§E.3`.
//
// 이 파일이 지키는 것 넷 (`§E.0`)
//  1. **등록은 미리보기에 인질이 아니다.** 어느 상태도 등록을 막는 신호를 내지 않는다.
//  2. **패널은 사라지지 않는다** — 이 블록은 패널 **안**에서 열리고 닫힌다.
//  3. **좌표를 지어내지 않는다** — 격자가 없으면 보류이고, 여기서 합성하지 않는다.
//  4. **사용자에게 축을 묻지 않는다** — 서버가 판별하고, 화면은 보여주고 뒤집기만 준다.
//
// ⚠ **문구를 여기서 새로 만들지 않았다.** 아래 표는 `§E.2` 「화면 문구 (한국어 확정안)」
// 열을 그대로 옮긴 것이다. 고치려면 `S1-PLAN-REFOUND` 를 먼저 고친다 (`CLAUDE.md §5`).
import type { RenderResult } from './types';

/** `§E.2` 의 열한 상태. **화면에는 번호를 쓰지 않는다** — 이름으로 부른다. */
export type GridStateName =
  | '좌표 없음'
  | '격자 전송 중'
  | '격자 확인 중'
  | '지도에 얹는 중'
  | '위치 확인'
  | '형상 불일치'
  | '축 판별 실패'
  | '짝 불일치'
  | '건너뜀'
  | '렌더 서버 불가'
  | '경계 위생 실패';

export interface GridCopy {
  title: string;
  body: string;
  /** 진행 표시의 성격 — `퍼센트` 는 **전송 구간에만** 정직하다 (`§D.7`). */
  progress?: '퍼센트' | '불확정';
  /** 이 상태가 등록을 막는가. **전부 false 다.** 필드를 둔 이유는 시험이 그것을 읽기 위해서다. */
  blocksRegistration?: false;
}

/** `§E.2` 표 그대로. `{}` 자리는 서버가 준 실측값으로 채운다 — 화면이 지어내지 않는다. */
export const GRID_COPY: Record<GridStateName, GridCopy> = {
  '좌표 없음': {
    title: '이 파일은 좌표를 자체적으로 갖고 있지 않습니다.',
    body: '값과 형상은 아래에 그대로 보입니다. 지도 위 위치를 보려면 위경도 격자 파일이 필요합니다.',
  },
  '격자 전송 중': {
    title: '격자 파일을 받는 중입니다.',
    body: '',
    progress: '퍼센트',
  },
  '격자 확인 중': {
    title: '격자가 이 파일의 것인지 확인하는 중입니다.',
    body: '',
    progress: '불확정',
  },
  '지도에 얹는 중': {
    title: '격자를 확인했습니다. 지도에 얹는 중입니다.',
    body: '',
    progress: '불확정',
  },
  '위치 확인': {
    title: '이 위치가 맞습니까?',
    body: '위도·경도를 서버가 판별했습니다. 지도가 엉뚱하면 두 파일이 바뀐 것입니다.',
  },
  '형상 불일치': {
    title: '이 격자는 이 파일의 것이 아닙니다.',
    body: '이 파일은 {데이터} 이고, 올리신 격자는 {격자} 입니다.',
  },
  '축 판별 실패': {
    title: '어느 쪽이 위도이고 어느 쪽이 경도인지 판정하지 못했습니다.',
    body: '두 파일 모두 값이 ±90 안에 있어 구분할 수 없습니다. 파일을 확인해 주세요.',
  },
  '짝 불일치': {
    title: '위도 파일과 경도 파일의 크기가 서로 다릅니다.',
    body: '{위도} / {경도}. 한 쌍이 아닙니다.',
  },
  '건너뜀': {
    title: '지도 없이 등록합니다.',
    body: '나중에 데이터셋 상세에서 격자를 올리면 지도형 미리보기만 새로 만들어집니다. 값 미리보기와 계보는 그대로 유지됩니다.',
  },
  '렌더 서버 불가': {
    title: '미리보기를 만드는 서버에 닿지 못했습니다.',
    body: '등록은 그대로 진행할 수 있습니다.',
  },
  '경계 위생 실패': {
    title: '격자를 적용했지만 결과 위치가 한반도 밖으로 나왔습니다. 지도형을 만들지 않았습니다.',
    body: '',
  },
};

/** viz-render 가 내는 실패 코드 (`d7_visualization/failures.py`). 화면은 코드로 가른다. */
export const FAILURE_CODE = {
  NO_GRID: 'REFERENCE_GRID_MISSING',
  BOUNDS: 'MAP_BOUNDS_IMPLAUSIBLE',
  UNREACHABLE: 'RENDER_SERVER_UNREACHABLE',
} as const;

/** 계약이 정한 배지 3값 (`GridPrecisionBadge`). **문자열을 여기서 다시 만들지 않는다.** */
export const BADGE_NO_GRID = '격자 없음 — 지도형 보류';
export const BADGE_ATTACHED = '동봉 격자 적용';

/**
 * ⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 2⟩ 서버가 준 **구조화된** 거절.
 * 계약 `core-viz.yaml#GridRejection` 이고 `UploadStatus.gridRejections` 도 같은 값 집합이다.
 */
export interface GridRejectionInput {
  reason?: string;
  shapes?: {
    dataShape?: number[];
    gridShape?: number[];
    latShape?: number[];
    lonShape?: number[];
  };
  fileName?: string;
}

export interface GridStateInput {
  /** 격자 파일을 실제로 올렸는가. 안 올렸으면 거절이 아니라 **아직 없음**이다. */
  hasGrid?: boolean;
  skipped?: boolean;
  /** 전송 진행 — **바이트가 실제로 세어질 때만** 채운다. 없으면 퍼센트를 쓰지 않는다. */
  transfer?: { sentBytes: number; totalBytes: number } | null;
  /** 접수는 됐고 워커의 축 판정을 기다린다 (`§E.3b` — 확정 또는 거절로 끝나야 ready). */
  verifying?: boolean;
  /** 격자가 확정된 뒤의 렌더 진행. */
  drawing?: boolean;
  result?: RenderResult | null;
  failure?: { code?: string; message?: string; details?: unknown } | null;
  /** 렌더 서버에 닿지 못했다 (`§E.2-⑩` — `test_preview_relay.py:169` 의 화면 판). */
  unreachable?: boolean;
  /**
   * **거절 사유의 정본 자리** (`〈88〉` 묶음 2). 이것이 있으면 서버 문장을 보지 않는다.
   * 없으면 문장으로 가르는 옛 경로가 선다 — 아직 안 고친 서버가 있을 수 있으므로 지우지 않지만,
   * **새 사실을 만들지는 않는다.**
   */
  gridRejection?: GridRejectionInput | null;
}

export interface GridStateShapes {
  data?: string;
  grid?: string;
  lat?: string;
  lon?: string;
}

export interface GridStateResult {
  name: GridStateName;
  shapes?: GridStateShapes;
  /** 분류가 안 되는 거절일 때 **서버가 준 문장을 그대로** 싣는다 — 화면이 지어내지 않는다. */
  serverDetail?: string;
}

function detailOf(failure: GridStateInput['failure']): string {
  const d = failure?.details;
  if (typeof d !== 'object' || d === null) return '';
  const v = (d as { detail?: unknown }).detail;
  return typeof v === 'string' ? v : '';
}

/** `(2881, 2305)` → `2881 × 2305`. **숫자를 만들지 않는다** — 서버 문장에 있는 것만 옮긴다. */
function shapeText(raw: string): string {
  return raw
    .replace(/[()]/g, '')
    .split(',')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .join(' × ');
}

const SHAPE = /\(([0-9,\s]+)\)/g;

/** `[2881, 2305]` → `2881 × 2305`. **숫자를 만들지 않는다.** 빈 배열이면 자리째 없다. */
function shapeOf(dims?: number[]): string | undefined {
  if (!dims || dims.length === 0) return undefined;
  return dims.join(' × ');
}

/**
 * ⟨`〈88〉` 묶음 2⟩ **구조화된 거절을 그대로 읽는다** — 문장을 가르지 않는다.
 *
 * ⚠ 형상을 **이름으로** 읽는 것이 핵심이다. 옛 경로는 문장에서 나온 괄호를 **순서대로**
 * `{데이터}`·`{격자}` 에 채웠는데, viz-render 는 「데이터 … vs 격자 …」로 쓰고
 * pipeline-worker 는 「격자 … vs 데이터 …」로 써서 **두 형상이 맞바뀌었다.**
 * 화면이 「이 파일은 격자의 형상이고, 올리신 격자는 본체의 형상입니다」라고 말했고
 * **거짓말인데 에러가 안 났다** (스윕 `C-1`⑵).
 */
export function fromGridRejection(rejection: GridRejectionInput): GridStateResult | null {
  const name = rejection.reason;
  if (name !== '형상 불일치' && name !== '축 판별 실패' && name !== '짝 불일치') return null;
  const src = rejection.shapes ?? {};
  const shapes: GridStateShapes = {};
  const data = shapeOf(src.dataShape);
  const grid = shapeOf(src.gridShape);
  const lat = shapeOf(src.latShape);
  const lon = shapeOf(src.lonShape);
  if (data) shapes.data = data;
  if (grid) shapes.grid = grid;
  if (lat) shapes.lat = lat;
  if (lon) shapes.lon = lon;
  return Object.keys(shapes).length > 0 ? { name, shapes } : { name };
}

/**
 * 거절 사유를 `§E.2` 의 상태로 가른다.
 *
 * ⚠ **이 함수는 이제 대비책이다** — `〈88〉` 묶음 2 가 `gridRejection` 을 열었고 화면은
 * 그쪽을 먼저 읽는다. 여기 남긴 이유는 **아직 그 필드를 안 채우는 응답이 올 수 있어서**이고,
 * 새 사실을 만들지는 않는다. 아래 경고는 **이 대비 경로에 대한 것**으로 그대로 참이다.
 *
 * ⚠ **가르는 근거가 서버 문장뿐이다.** `REFERENCE_GRID_MISSING` 한 코드가 사다리
 * 1·2·3단을 모두 싣고 오고, 계약에는 그것을 나눌 필드가 없다 (`ErrorEnvelope.details` 는
 * 자유 객체이고 viz-render 가 `detail` 한 줄만 넣는다). 그래서 **문장으로 가르되,
 * 못 가른 것은 서버 문장을 그대로 보여 준다** — 억지로 한 상태에 밀어 넣지 않는다.
 */
export function classifyGridRejection(detail: string, hasGrid: boolean): GridStateResult {
  if (/축을 판별하지 못했다/.test(detail)) return { name: '축 판별 실패' };
  if (/형상 불일치|짝이 아니다/.test(detail)) {
    const found = [...detail.matchAll(SHAPE)].map((m) => shapeText(m[1] ?? ''));
    const lat = found[0];
    const lon = found[1];
    return {
      name: '짝 불일치',
      ...(lat && lon ? { shapes: { lat, lon } } : {}),
      serverDetail: detail,
    };
  }
  if (/격자 형상이 데이터와 안 맞는다/.test(detail)) {
    const found = [...detail.matchAll(SHAPE)].map((m) => shapeText(m[1] ?? ''));
    const data = found[0];
    const grid = found[1];
    return {
      name: '형상 불일치',
      ...(data && grid ? { shapes: { data, grid } } : {}),
      serverDetail: detail,
    };
  }
  // 격자를 안 올렸는데 「격자가 없다」는 거절이 아니라 **아직 없음**이다 (`§5.5` 보류).
  if (!hasGrid) return { name: '좌표 없음' };
  return { name: '형상 불일치', serverDetail: detail };
}

/**
 * 지금 격자 블록이 무엇을 말해야 하는가. **null 이면 블록을 열지 않는다** —
 * 파일 안에 좌표가 있어 지도형이 이미 성립한 경우다(`투영 계산 격자`).
 *
 * 순서가 곧 `§E` 다: 닿지 못함 → 실패 → 전송 → 확인 → 렌더 → 결과.
 */
export function gridState(input: GridStateInput): GridStateResult | null {
  const hasGrid = input.hasGrid ?? false;
  if (input.unreachable) return { name: '렌더 서버 불가' };
  if (input.failure?.code === FAILURE_CODE.BOUNDS) return { name: '경계 위생 실패' };
  if (input.failure?.code === FAILURE_CODE.UNREACHABLE) return { name: '렌더 서버 불가' };
  if (input.gridRejection) {
    // **구조화된 사유가 이긴다** (`〈88〉` 묶음 2). 문장은 보지 않는다.
    const structured = fromGridRejection(input.gridRejection);
    if (structured) return structured;
  }
  if (input.failure?.code === FAILURE_CODE.NO_GRID) {
    return classifyGridRejection(detailOf(input.failure), hasGrid);
  }
  // ⚠ **`hasGrid` 를 함께 본다.** `transfer` 는 본체+격자 **전체 바이트**라, 격자가 없는데
  // 이 상태가 서면 화면이 「격자 파일을 받는 중입니다」라고 **틀린 말**을 한다
  // (`§E.2` 「처리 중이 아닌 것을 처리 중처럼 말하지 않는다」). 침묵보다 나쁘다.
  if (hasGrid && input.transfer) return { name: '격자 전송 중' };
  if (input.verifying) return { name: '격자 확인 중' };
  if (hasGrid && input.drawing) return { name: '지도에 얹는 중' };
  if (input.result) {
    if (input.result.precisionBadge === BADGE_ATTACHED) return { name: '위치 확인' };
    if (input.result.precisionBadge === BADGE_NO_GRID)
      return input.skipped ? { name: '건너뜀' } : { name: '좌표 없음' };
    return null; // `투영 계산 격자` — 파일이 스스로 좌표를 말했다. 청할 것이 없다
  }
  if (input.skipped) return { name: '건너뜀' };
  return null;
}

/** `{데이터}`·`{격자}`·`{위도}`·`{경도}` 를 실측값으로 채운다. 값이 없으면 자리째 뺀다. */
export function fillBody(name: GridStateName, shapes?: GridStateShapes): string {
  const body = GRID_COPY[name].body;
  if (!shapes) return body.includes('{') ? '' : body;
  const filled = body
    .replace('{데이터}', shapes.data ?? '')
    .replace('{격자}', shapes.grid ?? '')
    .replace('{위도}', shapes.lat ?? '')
    .replace('{경도}', shapes.lon ?? '');
  return filled.includes('{') ? '' : filled;
}
