// S-04 「바로 미리보기」 — 정본 §8 미리보기 그리기 · §9 그리기 실패 4종.
//
// **서버가 그린다.** 진행은 정본 문구 세 값 그대로 말한다:
//   `파일 읽는 중…` → `지도 그리는 중…` → `범례 만드는 중…`
// 한 덩어리 「로딩 중」으로 두지 않는다 — 멈춘 것인지 구분되지 않는다.
// 안내는 `aria-live=polite`, 오류는 `assertive` (§8).
//
// 소비 규칙 (`sessions/P2-viz-report.md §13` · 부록 A)
//   ⑴ 실패는 4xx 가 아니라 **200 + `failure`** 다.
//   ⑵ `stage` 는 `그리는 중` 일 때만 있다.
//   ⑶ `partialFailure` 는 `status` 를 `실패` 로 만들지 않는다 — 읽힌 조각으로 그리고 `완료` 다.
//   ⑷ `tileUrlTemplate` 은 **불투명 문자열**이다(`〈68〉` 단명 서명 포함). `{z}`·`{x}`·`{y}` 만 치환한다.
//   ⑸ 만료된 렌더의 타일은 **401** 로 온다 — 권한 문제가 아니라 만료로 다룬다.
import { useEffect, useMemo, useRef, useState } from 'react';
import type { PaletteOption, PreviewSource, RenderJob, RenderResult } from './types';
import { GridUploadBlock, type GridActions } from './GridUploadBlock';
import { gridState, type GridRejectionInput } from './gridFlow';
import { colorRangeNotice, layerOf, layersOf, previewImageSrc, rangeKey, salvageOf } from './previewResult';

/** 정본 §9 「그리는 서버에 연결 못 함」. 코드가 없을 때 쓰는 기본 문구. */
const UNAVAILABLE = '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.';
/** 렌더 진행 확인 간격. 서버 왕복이 수 초~수십 초라 정본이 「단계로 말한다」고 했다. */
const POLL_MS = 250;
/** 구간 수 3~9 · 기본 6 (`Policy_데이터셋_상세 §5` · 계약 `RenderStyle.classCount`). */
const DEFAULT_CLASS_COUNT = 6;

/**
 * 입력칸의 글자를 구간 수로 읽는다. **빈 칸·숫자가 아닌 것은 값이 아니라 없음**이라
 * 기본값으로 되돌린다 — `Number('')` 이 0 이라 종전에는 칸을 비우는 순간 계약 밖의 0 이
 * 다음 그리기에 실려 나갔다.
 */
export function classCountOf(raw: string): number {
  const n = Number(raw);
  return raw.trim() === '' || !Number.isFinite(n) ? DEFAULT_CLASS_COUNT : n;
}

/** 격자 흐름이 바깥(모달)에서 받는 사실 + 바깥으로 돌려주는 행동 (`§E.1-㈎`). */
export interface GridFlowProps extends GridActions {
  /** 사람이 「건너뛰기」를 골랐다 (`§E.2-⑨`). **기본 경로다.** */
  skipped?: boolean;
  /** 격자 파일이 실제로 붙어 있는가. */
  hasGrid?: boolean;
  /** 전송 진행 — 바이트가 실제로 세어질 때만 온다. 없으면 퍼센트를 쓰지 않는다. */
  transfer?: { sentBytes: number; totalBytes: number } | null;
  /** 워커의 축 판정을 기다린다 (`§E.3b` — 확정 또는 거절로 끝나야 `ready`). */
  verifying?: boolean;
  /**
   * ⟨`〈88〉` 묶음 7⟩ **워커가 거절한 격자의 사유**(`UploadStatus.gridRejections`).
   * 렌더가 아직 없는 등록 전 구간에서 ⑥⑦⑧ 거절 상태를 세우는 근거다 —
   * 이전에는 이 자리에 근거가 없어 화면이 viz-render 의 실패 문장을 인용했다.
   */
  gridRejection?: GridRejectionInput | null;
}

export function PreviewPanel(props: {
  source: PreviewSource;
  uploadId: string | null;
  /** 기준 격자 파일이 붙어 있는가. 없으면 정본 §9 안내 + `짝 파일 없이 그려 보기`. */
  hasReferenceGrid: boolean;
  /** 격자 업로드 흐름. 없으면 블록을 열지 않는다 — 화면이 사라지는 것이 아니라 안 열린다. */
  grid?: GridFlowProps | undefined;
  /**
   * 그리기를 **시작한 사실**을 바깥(S-04 모달)에 알린다.
   * 「보기만 할게요」로 S-08 에 갈 때 그 화면이 **다시 그리지 않고 이어서 보게** 하려면
   * `renderId` 가 모달 손에 있어야 한다 (정본 §8.1 미리보기 — 「그대로 이어서 보여준다」).
   * 짝 파일 없이 그렸는지도 **여기서만 아는 사실**이라 함께 넘긴다.
   */
  onRender?: ((info: { renderId: string; withoutReferenceGrid: boolean }) => void) | undefined;
}) {
  const { source, uploadId } = props;
  const [palettes, setPalettes] = useState<PaletteOption[] | null>(null);
  const [palette, setPalette] = useState('');
  const [classCount, setClassCount] = useState(DEFAULT_CLASS_COUNT);
  const [job, setJob] = useState<RenderJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tileExpired, setTileExpired] = useState(false);
  const [unreachable, setUnreachable] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const polling = useRef(0);
  // 색 범위가 **조용히** 바뀌지 않게, 앞서 본 잠정 범위를 들고 있는다 (`§D.4`)
  const seenRange = useRef<{ stage: string; key: string } | null>(null);

  // 팔레트 값의 **유일한 출처는 서버**다. 화면이 목록을 지어내지 않는다.
  useEffect(() => {
    let alive = true;
    void source
      .palettes()
      .then((list) => {
        if (!alive) return;
        setPalettes(list);
        setPalette((cur) => cur || list[0]?.palette || '');
      })
      .catch(() => {
        if (!alive) return;
        // 팔레트가 없으면 그릴 수 없다. **그릴 수 없는 것과 등록할 수 없는 것은 다르다** —
        // 알리기만 하고 등록 경로는 그대로 둔다 (§9 기준 격자 파일 없음 항과 같은 태도).
        setPalettes([]);
        setError(UNAVAILABLE);
      });
    return () => {
      alive = false;
    };
  }, [source]);

  useEffect(() => () => window.clearTimeout(polling.current), []);

  async function draw(withoutReferenceGrid: boolean) {
    if (!uploadId || !palette) return;
    setError(null);
    setTileExpired(false);
    setUnreachable(false);
    setAccepted(false);
    try {
      const started = await source.createRender({
        target: { uploadId },
        style: { palette, classCount },
        withoutReferenceGrid,
      });
      setJob(started);
      props.onRender?.({ renderId: started.renderId, withoutReferenceGrid });
      poll(started.renderId);
    } catch {
      // 그리는 서버에 닿지 못했다 — **등록은 그대로 진행된다**(`§E.2-⑩`)
      setUnreachable(true);
      setError(UNAVAILABLE);
    }
  }

  function poll(renderId: string) {
    window.clearTimeout(polling.current);
    polling.current = window.setTimeout(async () => {
      try {
        const next = await source.getRender(renderId);
        setJob(next);
        if (next.status === '그리는 중') poll(renderId);
      } catch {
        setUnreachable(true);
        setError(UNAVAILABLE);
      }
    }, POLL_MS);
  }

  const drawing = job?.status === '그리는 중';
  const done = job?.status === '완료';
  // **실패는 200 + `failure`** 다. HTTP 상태로 판정하지 않는다.
  const failure = job?.status === '실패' ? job.failure : undefined;
  const partial = job?.partialFailure;
  const result: RenderResult | undefined = done ? job?.result : undefined;
  // 실패해도 이미 구운 값 미리보기·썸네일이 있으면 **감추지 않는다**
  const salvage = salvageOf(failure);
  // **성공 경로의 ①②** (`〈88〉` 묶음 3). 이전에는 성공하면 오히려 사라지던 자리다.
  const layers = result ? layersOf(result) : null;

  // 색 범위 — **조용히 바뀌지 않는다.** 앞서 본 범위와 견줘 바뀜을 한 번 말한다 (`§D.4`)
  const stage = result?.colorRangeStage ?? salvage?.colorRangeStage;
  const changed = useMemo(() => {
    if (!result || !stage) return false;
    const key = rangeKey(result);
    const seen = seenRange.current;
    const moved = Boolean(seen && seen.stage === '잠정' && stage === '확정' && seen.key !== key);
    seenRange.current = { stage, key };
    return moved;
  }, [result, stage]);
  const notice = colorRangeNotice(stage, changed);

  const grid = props.grid;
  const gs = grid
    ? gridState({
        hasGrid: grid.hasGrid ?? props.hasReferenceGrid,
        skipped: grid.skipped ?? false,
        transfer: grid.transfer ?? null,
        verifying: grid.verifying ?? false,
        drawing,
        result: result ?? null,
        failure: failure ?? null,
        // **구조화된 거절이 먼저다** (`〈88〉` 묶음 2) — 화면은 서버 문장을 가르지 않는다.
        // 렌더의 판정(`RenderJob.gridRejection`)이 있으면 그것이 최신이고, 없으면
        // 워커의 판정(`UploadStatus.gridRejections` — 등록 전 구간)이 선다.
        gridRejection: job?.gridRejection ?? grid.gridRejection ?? null,
        unreachable,
      })
    : null;
  // 「맞습니다」를 누른 뒤에는 확인을 다시 청하지 않는다 — 물어 놓고 또 묻지 않는다
  const gridBlock = gs && !(accepted && gs.name === '위치 확인') ? gs : null;

  return (
    <section className="mapstage" data-testid="up-preview">
      <div className="mapbar">
        <span className="mt">미리보기</span>
      </div>

      {/* 컨트롤은 팔레트와 구간 수 **둘뿐**이다 — 표현 종류는 사람이 고르지 않는다(계약). */}
      <div className="vizsetup">
        <label className="vs-f">
          <span>팔레트</span>
          <select
            className="sel"
            data-testid="up-style-palette"
            value={palette}
            onChange={(e) => setPalette(e.target.value)}
          >
            {(palettes ?? []).map((p) => (
              <option key={p.palette} value={p.palette}>
                {p.label}
              </option>
            ))}
          </select>
        </label>
        <label className="vs-f">
          <span>구간 수</span>
          <input
            className="inp"
            type="number"
            min={3}
            max={9}
            data-testid="up-style-classcount"
            value={classCount}
            /* 빈 칸은 **0 이 아니다** — 지우는 중일 뿐이다. `Number('')` 은 0 이고 그 0 이
               그대로 `RenderStyle.classCount`(3~9)로 나가 서버가 거절한다. 값이 없으면
               기본값으로 둔다 (`CODE-REVIEW-20260903` 부록 · 화면 소결함). */
            onChange={(e) => setClassCount(classCountOf(e.target.value))}
          />
        </label>
        <div className="vs-act">
          {uploadId && (
            <button
              type="button"
              className="btn btn-strong btn-sm"
              data-testid="up-preview-draw"
              onClick={() => void draw(false)}
            >
              미리보기 그리기
            </button>
          )}
        </div>
      </div>

      {/* 기준 격자 파일 없음 — 미리보기가 안 된다고 알리되 **등록은 막지 않는다** (§8·§9) */}
      {!props.hasReferenceGrid && (
        <div className="companion" data-testid="up-nogrid">
          <span className="cw">위경도를 담은 짝 파일이 없어요.</span>
          <span className="cw">파일 안에 위경도가 들어 있으면 그려져요. 등록은 막지 않아요.</span>
          {uploadId && (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              data-testid="up-preview-without-grid"
              onClick={() => void draw(true)}
            >
              짝 파일 없이 그려 보기
            </button>
          )}
        </div>
      )}

      {/* 진행을 **단계로** 말한다. `stage` 는 `그리는 중` 일 때만 있다 */}
      {drawing && (
        <div className="vizload" role="status" aria-live="polite" data-testid="up-preview-stage">
          <span className="spin" aria-hidden="true" />
          <span>{job?.stage ?? ''}…</span>
        </div>
      )}

      {(failure || error) && (
        <div className="vizerr" role="alert" aria-live="assertive" data-testid="up-preview-error">
          {failure?.message ?? error ?? UNAVAILABLE}
        </div>
      )}

      {/* 부분 실패는 실패가 아니다 — 읽힌 조각으로 그리고 안내만 붙인다 (§9) */}
      {partial && (
        <div className="vizpartial" data-testid="up-preview-partial">
          조각 {partial.totalParts}개 중 {partial.totalParts - partial.renderedParts}개를 읽지
          못했어요. 읽은 {partial.renderedParts}개로 그릴 수 있어요.
          <span className="names">{partial.missingParts.map((m) => m.fileName).join(' · ')}</span>
        </div>
      )}

      {/* 그림 한 장. **②비지도형은 경계가 없는 것이 정상이고 그것도 완료다**(`〈85〉`) —
          여기서 오류 자리로 보내지 않는다. 배지가 좌표의 출처를 화면이 말하게 한다(`K-4`) */}
      {result && (
        <div className="mapcanvas" data-testid="up-preview-map">
          <div className="pv-badges">
            {result.precisionBadge ? (
              <span className="chip" data-testid="up-preview-badge">
                {result.precisionBadge}
              </span>
            ) : null}
            <span className="chip chip--neutral" data-testid="up-preview-layer">
              {layerOf(result)}
            </span>
          </div>
          {/* ①썸네일 — **성공 응답에도 실린다**(`〈88〉` 묶음 3). 없으면 자리째 없다 */}
          {layers?.thumbnailUrl ? (
            <img
              className="thumb"
              alt=""
              data-testid="up-preview-thumb"
              src={layers.thumbnailUrl}
            />
          ) : null}
          {previewImageSrc(result) ? (
            <img
              className="tile"
              alt="미리보기"
              /* 계약이 `oneOf` 라 갈래마다 다른 자리다 — 단일 이미지(stage 1)와 타일(stage 2) */
              data-testid={result.imageUrl ? 'up-preview-image' : 'up-preview-tile'}
              src={previewImageSrc(result)}
              onError={() => setTileExpired(true)}
            />
          ) : null}
          {tileExpired && (
            <div className="vizerr" role="alert" aria-live="assertive" data-testid="up-preview-expired">
              타일 주소의 수명이 다했어요. 미리보기를 다시 그려 주세요.
            </div>
          )}
        </div>
      )}

      {/* 실패했어도 **이미 구운 값 미리보기·썸네일은 남는다** — 있는 것을 감추지 않는다 */}
      {!result && salvage && (
        <div className="mapcanvas" data-testid="up-preview-salvage">
          {salvage.precisionBadge ? (
            <span className="chip" data-testid="up-preview-badge">
              {salvage.precisionBadge}
            </span>
          ) : null}
          {salvage.thumbnailUrl ? (
            <img className="thumb" alt="" data-testid="up-preview-thumb" src={salvage.thumbnailUrl} />
          ) : null}
          {salvage.valuePreviewUrl ? (
            <img
              className="tile"
              alt="값 미리보기"
              data-testid="up-preview-image"
              src={salvage.valuePreviewUrl}
            />
          ) : null}
        </div>
      )}

      {/* 색 범위 단계 — **잠정을 잠정이라 말한다.** 조용히 바뀌지 않는다 (`§D.4`) */}
      {notice ? (
        <div className="vizstage" data-testid="up-preview-colorstage" aria-live="polite">
          <span className="chip chip--neutral">{notice.stage}</span>
          {notice.message ? <span className="cw">{notice.message}</span> : null}
        </div>
      ) : null}

      {/* 「미리보기를 보려면 격자를 올리세요」 — 문구와 상태는 `gridFlow.ts` 가 소유한다 */}
      {grid && gridBlock ? (
        <GridUploadBlock
          state={gridBlock}
          transfer={grid.transfer ?? null}
          actions={{
            onPickGrid: grid.onPickGrid,
            onSkipGrid: grid.onSkipGrid,
            ...(grid.onCancel ? { onCancel: grid.onCancel } : {}),
            onAccept: () => {
              setAccepted(true);
              grid.onAccept?.();
            },
            ...(grid.onFlipAxes ? { onFlipAxes: grid.onFlipAxes } : {}),
          }}
        />
      ) : null}

      {!job && !error && (
        <div className="vizph">
          <div className="pt">아직 그리지 않았어요</div>
          <div className="pd">위에서 팔레트와 구간 수를 고르고 미리보기 그리기를 눌러 주세요.</div>
        </div>
      )}
    </section>
  );
}
