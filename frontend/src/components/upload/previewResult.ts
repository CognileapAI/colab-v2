// 렌더 결과를 **화면 어휘로** 옮기는 자리 — `PLAN-SoT §9-〈74〉`(미리보기 3층)·`〈85〉`.
//
// 계약이 `oneOf` 로 갈라 놓은 것을 화면이 그대로 읽는다.
//  · `imageUrl` ＋ 경계·사이드카 → **③지도형**
//  · `imageUrl` 만            → **②비지도형. 경계가 없는 것이 정상이고 이것은 완료다**
//  · `tileUrlTemplate`        → stage 2 확대 뷰의 갈래. stage 1 은 내지 않지만 **읽을 수는 있다**
//
// ⭑ **⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 3⟩ 그 자리가 열렸다.**
// 이전 판의 주석은 「①썸네일은 완료 응답에 자리가 없다 — 실패 봉투로만 온다」였고
// **그것이 사실이었다.** viz-render 가 ①②를 항상 함께 굽는데 성공 응답에는 `imageUrl`
// 한 자리뿐이라, ③이 있으면 ②가 ③이 없으면 ①이 버려졌다 — 즉 **렌더가 성공할수록
// 썸네일이 안 보였다**(스윕 `A-1`). 이제 `thumbnailUrl`·`valuePreviewUrl` 이 계약에 있다.
// `salvageOf`(실패 봉투 경로)는 **지우지 않는다** — 실패해도 구워진 층은 여전히 남는다.
import type { RenderResult } from './types';

/** 화면이 사람에게 말하는 층 이름. **번호를 쓰지 않는다.** */
export type PreviewLayerName = '값 미리보기' | '지도형 미리보기';

export function layerOf(result: RenderResult): PreviewLayerName {
  return result.bounds || result.sidecarUrl || result.tileUrlTemplate
    ? '지도형 미리보기'
    : '값 미리보기';
}

export interface PreviewLayers {
  /** ①썸네일 128 px WEBP. 없으면 자리째 없다 — **URL 을 지어내지 않는다.** */
  thumbnailUrl?: string;
  /** ②비지도형 1024 px PNG. */
  valuePreviewUrl?: string;
  /** 주 화면에 그릴 한 장 — ③이 있으면 ③, 없으면 ②다. */
  mainImageUrl?: string;
}

/**
 * 성공 결과가 실어 온 **세 층**을 화면 어휘로 옮긴다 (`〈88〉` 묶음 3).
 * 「무엇을 주 화면에 그릴 것인가」(`imageUrl`)와 「어떤 층들이 함께 구워졌는가」는
 * 다른 질문이고, 계약이 그 둘을 갈라 놓았다.
 */
export function layersOf(result: RenderResult): PreviewLayers {
  const r = result as RenderResult & { thumbnailUrl?: string; valuePreviewUrl?: string };
  const out: PreviewLayers = {};
  if (r.thumbnailUrl) out.thumbnailUrl = r.thumbnailUrl;
  if (r.valuePreviewUrl) out.valuePreviewUrl = r.valuePreviewUrl;
  const main = previewImageSrc(result);
  if (main) out.mainImageUrl = main;
  return out;
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
