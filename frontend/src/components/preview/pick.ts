// WU-C3 — **500MB 조각 폴백 ＋ 파일·변수·시각 고르개**의 공용 자리.
//
// 축 ① 판정(`intent/2026-09-08-preview-slot.md`)이 요구하는 두 가지가 **한 파일**에 모인다:
//  ⑴ 413 `RENDER_TOO_LARGE` → files 조회 → 첫 renderable 조각 → `fileIds:[그것]` 재요청
//  ⑵ 세 고르개(파일·변수·시각)의 후보와 기본값 — 후보는 전부 **서버가 준 값**이다
//
// ⚠ **문면을 새로 짓지 않는다.** 이 파일의 유일한 한국어 화면 문장은 viz-render 의
//   `d7_visualization/failures.py TOO_LARGE_MESSAGE` **축자 복사**이고, 폴백 안내는 그
//   문장의 **둘째 문장을 잘라 쓴다**(`secondSentenceOf`). 조각 이름은 문장이 아니라 값이라
//   문장 옆에 값으로 선다 — 새 문장을 만들지 않기 위해서다.
// ⚠ 상한값·서버는 건드리지 않는다. FE 는 413 을 **해석만** 한다.
import type { Schemas } from '../../api/client';

/**
 * viz-render `d7_visualization/failures.py:54` **축자**. FE 가 파이썬 상수를 import 할 수
 * 없으므로 여기 한 자리에만 베껴 둔다 — 두 자리에 두면 판정이 갈린다.
 */
export const TOO_LARGE_MESSAGE = '미리보기는 500MB까지 그려요. 조각 하나를 골라 그려 보세요.';

/**
 * 문장 둘째 조각을 **자른다**(짓지 않는다). 마침표를 경계로 나누고 마침표를 되돌려 붙인다 —
 * 문장이 하나뿐이면 그 문장 자체가 답이다.
 */
export function secondSentenceOf(message: string): string {
  const parts = message
    .split('.')
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  const picked = parts.length >= 2 ? parts[1] : parts[0];
  return picked ? `${picked}.` : message;
}

/** 폴백 안내에 쓰는 문면. **`TOO_LARGE_MESSAGE` 의 둘째 문장 그대로다.** */
export const TOO_LARGE_SECOND_SENTENCE = secondSentenceOf(TOO_LARGE_MESSAGE);

/**
 * 413 `RENDER_TOO_LARGE` — **대상 조각의 크기 합이 렌더 상한을 넘었다**
 * (`core-viz.yaml` 413 · `renders.py:88,97`). 「만들 수 없음」과 다른 사실이라 따로 세운다:
 * 이것만이 **조각 하나로 다시 그릴 수 있다**는 뜻이다.
 */
export class RenderTooLarge extends Error {
  constructor(message: string = TOO_LARGE_MESSAGE) {
    super(message);
    this.name = 'RenderTooLarge';
  }
}

/** 응답 본문이 413 `RENDER_TOO_LARGE` 인가. **상태와 코드 둘 다 본다.** */
export function isRenderTooLarge(status: number, body: unknown): boolean {
  if (status !== 413) return false;
  if (typeof body !== 'object' || body === null) return true;
  const code = (body as { code?: unknown }).code;
  return code === undefined || code === 'RENDER_TOO_LARGE';
}

/**
 * 고르개에 서는 조각 하나. **계약 스키마가 아니다** — 등록 전(`UploadFileRef`)과
 * 등록 뒤(`DatasetFile`)가 다른 모양인데 고르개가 보는 사실은 셋뿐이라 화면 어휘로 좁힌다.
 *
 * ⓐ **`renderable` 의 출처 = `kind` 다.** 계약에 **조각별 renderable 플래그가 없다** —
 * `UploadStatus.renderable` 은 업로드 **한 건 전체**의 값이고 `UploadFileRef`·`DatasetFile`
 * 어느 쪽에도 조각별 값이 없다(생성물 실측 2026-09-08). 「그릴 수 있는 조각」의 유일한
 * 계약 근거는 **본체 조각인가**이다 — 기준 격자 파일은 그리는 대상이 아니다.
 */
export interface PreviewPiece {
  fileId: string;
  fileName: string;
  renderable: boolean;
}

export type UploadFileRef = Schemas['UploadFileRef'];
export type DatasetFile = Schemas['DatasetFile'];
export type TargetDescription = Schemas['TargetDescription'];
export type InstantRange = Schemas['InstantRange'];

/** 그릴 수 있는 조각의 종류. 기준 격자 파일은 **그리는 대상이 아니다**. */
const RENDERABLE_KIND = '본체';

export function pieceOfUploadFile(f: UploadFileRef): PreviewPiece {
  return { fileId: f.fileId, fileName: f.fileName, renderable: f.kind === RENDERABLE_KIND };
}

export function pieceOfDatasetFile(f: DatasetFile): PreviewPiece {
  return { fileId: f.fileId, fileName: f.fileName, renderable: f.kind === RENDERABLE_KIND };
}

export function renderablePieces(pieces: PreviewPiece[]): PreviewPiece[] {
  return pieces.filter((p) => p.renderable);
}

/** 첫 renderable 조각. **순서를 화면이 바꾸지 않는다** — 서버가 준 차례 그대로 첫 번째다. */
export function firstRenderable(pieces: PreviewPiece[]): PreviewPiece | undefined {
  return renderablePieces(pieces)[0];
}

/**
 * 시각 고르개의 후보.
 *
 * ⓐ **계약이 시각 목록을 주지 않는다** — `InstantRange` 는 `count`·`first`·`last` 셋이고
 * 「목록을 통째로 내리지 않는다」고 산문이 명시한다. 그래서 고를 수 있는 시각은
 * **처음과 마지막 둘**이다(같으면 하나). 자유 입력은 두지 않는다 — 화면이 없는 시각을
 * 지어내면 서버가 거절할 값을 사람에게 고르게 하는 것이 된다.
 */
export function instantChoicesOf(range: InstantRange | null | undefined): string[] {
  if (!range) return [];
  return range.first === range.last ? [range.first] : [range.first, range.last];
}

/** 사람이 고른 값. **URL 에 실리지 않는다**(판정 축자 — 컴포넌트 상태다). */
export interface PickSelection {
  fileId?: string | undefined;
  variable?: string | undefined;
  instant?: string | undefined;
}

/**
 * 고르개가 실제로 보여 주는 값 = 사람이 고른 값이 있으면 그것, 없으면 **describe 의 서버
 * 기본값**이다. 「아무것도 안 골랐을 때 무엇이 그려지는가」를 화면이 같은 사실로 말한다
 * (`TargetDescription` 산문 축자).
 */
export function shownVariable(
  sel: PickSelection,
  desc: TargetDescription | undefined,
): string {
  return sel.variable ?? desc?.default.variable ?? '';
}

export function shownInstant(sel: PickSelection, desc: TargetDescription | undefined): string {
  return sel.instant ?? desc?.default.instant ?? '';
}

/**
 * 조각 목록을 **한 번만 묻는다.** 고르개의 후보와 413 폴백이 같은 사실을 쓰는데 각자
 * 부르면 같은 화면이 같은 것을 두 번 묻는다 — 수용 기준의 「files 조회 **1회**」가 그 사실이다.
 * 첫 호출의 약속을 그대로 돌려주고, **실패하면 캐시를 버린다**(다음 시도가 다시 묻는다).
 */
export function onceFiles(
  load: () => Promise<PreviewPiece[]>,
): () => Promise<PreviewPiece[]> {
  let pending: Promise<PreviewPiece[]> | undefined;
  return () => {
    if (!pending) {
      pending = load().catch((e) => {
        pending = undefined;
        throw e;
      });
    }
    return pending;
  };
}

/**
 * ⑴ **폴백 한 자리.** 두 화면(업로드·상세)이 전부 이것을 지난다 —
 * 두 벌로 두면 「무엇을 조각으로 다시 그렸는가」의 판정이 갈린다
 * (`DatasetPreviewSection.tsx` 소비 규약 주석과 같은 규율).
 *
 * 413 이 아니면 **아무 일도 하지 않는다**. 413 이면 files 를 **한 번** 묻고 첫 renderable
 * 조각으로 다시 부른다. 폴백 자체가 실패하면(조각을 못 받았거나 renderable 이 없거나
 * 두 번째 요청도 실패) **처음 오류를 그대로 던진다** — 기존 실패 경로가 받는다.
 */
export async function createWithPieceFallback<J>(opts: {
  create: (fileIds?: string[]) => Promise<J>;
  files: (() => Promise<PreviewPiece[]>) | undefined;
}): Promise<{ job: J; piece?: PreviewPiece }> {
  try {
    return { job: await opts.create() };
  } catch (e) {
    if (!(e instanceof RenderTooLarge) || !opts.files) throw e;
    let piece: PreviewPiece | undefined;
    try {
      piece = firstRenderable(await opts.files());
    } catch {
      throw e;
    }
    if (!piece) throw e;
    // 두 번째 요청의 실패는 **폴백의 실패**다 — 그 오류를 그대로 올린다.
    const job = await opts.create([piece.fileId]);
    return { job, piece };
  }
}
