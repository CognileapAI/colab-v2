// 렌더 결과를 **화면 어휘로** 옮기는 자리 — `PLAN-SoT §9-〈74〉`(미리보기 3층)·`〈85〉`.
//
// 계약이 `oneOf` 로 갈라 놓은 것을 화면이 그대로 읽는다.
//  · `imageUrl` ＋ 경계·사이드카 → **③지도형**
//  · `imageUrl` 만            → **②비지도형. 경계가 없는 것이 정상이고 이것은 완료다**
//  · `tileUrlTemplate`        → stage 2 확대 뷰의 갈래. stage 1 은 내지 않지만 **읽을 수는 있다**
//
// ⚠ **①썸네일은 완료 응답에 자리가 없다** — `RenderResult` 에 썸네일 URL 필드가 없고,
// viz-render 는 실패 봉투의 `details.thumbnailUrl` 로만 그 자리를 말한다. 그래서 화면은
// 실패했을 때에 한해 그 URL 을 살려 쓴다. **없는 필드를 지어내지 않는다**(`DR-9`).
import type { RenderResult } from './types';

/** 화면이 사람에게 말하는 층 이름. **번호를 쓰지 않는다.** */
export type PreviewLayerName = '값 미리보기' | '지도형 미리보기';

export function layerOf(result: RenderResult): PreviewLayerName {
  return result.bounds || result.sidecarUrl || result.tileUrlTemplate
    ? '지도형 미리보기'
    : '값 미리보기';
}

/** `{z}`·`{x}`·`{y}` **셋만** 바꾼다 — 서명이 실려 있어 다시 조립하면 깨진다(`〈68〉`). */
function tileSrc(template: string): string {
  return template.split('{z}').join('0').split('{x}').join('0').split('{y}').join('0');
}

/** 그릴 이미지 한 장. **없으면 `undefined`** — 빈 `src` 를 만들지 않는다. */
export function previewImageSrc(result: RenderResult): string | undefined {
  if (result.imageUrl) return result.imageUrl;
  if (result.tileUrlTemplate) return tileSrc(result.tileUrlTemplate);
  return undefined;
}

export interface Salvage {
  thumbnailUrl?: string;
  valuePreviewUrl?: string;
  precisionBadge?: string;
  colorRangeStage?: string;
}

/**
 * 실패했지만 **이미 구운 ①②가 있으면** 그 자리를 읽는다 (`jobs.py:_failure`).
 * 있는 것을 감추면 화면이 「아무것도 못 그렸다」고 거짓말한다.
 */
export function salvageOf(failure: { details?: unknown } | null | undefined): Salvage | null {
  const d = failure?.details;
  if (typeof d !== 'object' || d === null) return null;
  const o = d as Record<string, unknown>;
  const pick = (k: string) => (typeof o[k] === 'string' ? (o[k] as string) : undefined);
  const out: Salvage = {};
  const thumb = pick('thumbnailUrl');
  const value = pick('valuePreviewUrl');
  const badge = pick('precisionBadge');
  const stage = pick('colorRangeStage');
  if (thumb) out.thumbnailUrl = thumb;
  if (value) out.valuePreviewUrl = value;
  if (badge) out.precisionBadge = badge;
  if (stage) out.colorRangeStage = stage;
  return out.thumbnailUrl || out.valuePreviewUrl ? out : null;
}

/** 범례가 실제로 덮는 값 범위. 같은 범위면 색도 같다 — 바뀜 판정의 근거다. */
export function rangeKey(result: RenderResult): string {
  const cs = (result.legend?.classes ?? []) as Array<Record<string, unknown>>;
  if (cs.length === 0) return '';
  const first = cs[0] ?? {};
  const last = cs[cs.length - 1] ?? {};
  const num = (v: unknown) => (typeof v === 'number' ? String(v) : '');
  return `${num(first['min'] ?? first['from'])}~${num(last['max'] ?? last['to'])}`;
}

export interface ColorRangeNotice {
  stage: string;
  message: string;
}

/**
 * 잠정 색 범위를 **정직하게** 말한다 (`§D.4`).
 *  · 등록 전(`잠정`) — **미리** 알린다. 「등록하면 색이 달라질 수 있습니다」
 *  · 확정으로 바뀌고 범위가 실제로 달라졌으면 — **한 번** 말한다
 *  · 확정인데 범위가 그대로면 — 아무 말도 하지 않는다. 없는 변화를 알리지 않는다
 */
export function colorRangeNotice(
  stage: string | undefined,
  changed: boolean,
): ColorRangeNotice | null {
  if (!stage) return null;
  if (stage === '잠정')
    return { stage, message: '지금 색 범위는 잠정입니다 — 등록하면 색이 달라질 수 있습니다.' };
  if (stage === '확정' && changed)
    return { stage, message: '등록하면서 색 범위가 달라졌습니다. 같은 값도 색이 다르게 보입니다.' };
  return { stage, message: '' };
}
