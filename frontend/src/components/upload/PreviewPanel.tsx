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
import { PreviewExpandOverlay } from './PreviewExpandOverlay';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { GridOptions, PaletteOption, PreviewSource, RenderJob, RenderRequest, RenderResult } from './types';
import { GridUploadBlock, type GridActions } from './GridUploadBlock';
import { gridState, type GridRejectionInput } from './gridFlow';
import { colorRangeNotice, layerOf, layersOf, previewImageSrc, rangeKey, salvageOf } from './previewResult';
import { PreviewSlot, type PreviewSlotState } from '../preview/PreviewSlot';
import { BoundsOutline, PreviewZoomControls } from '../preview/PreviewZoomControls';
import { BasemapLayer } from '../preview/BasemapLayer';
import { useZoomPan } from '../preview/useZoomPan';
import { useStageRemaining } from '../preview/useStageRemaining';
import { PreviewPickRow } from '../preview/PreviewPickRow';
import {
  createWithPieceFallback,
  onceFiles,
  type PickSelection,
  type PreviewPiece,
  type TargetDescription,
} from '../preview/pick';

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
  options?: GridOptions;
  reuseBusy?: boolean;
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
  autoPreview?: boolean;
  /** 분석이 확인한 지도 지원 여부. 미확인 상태와 구분한다. */
  renderable?: boolean | undefined;
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
  onResult?: ((result: RenderResult) => void) | undefined;
  /** 대표 그림 실제 파일은 등록 수명과 함께 모달이 쥔다. */
  representativeFile?: File | null | undefined;
  onRepresentativeFileChange?: ((file: File | null) => void) | undefined;
  /** 데이터셋 생성 뒤에는 저장 복구에 필요한 대표 그림 고르개만 남긴다. */
  representativeOnly?: boolean | undefined;
  representativeDisabled?: boolean | undefined;
  /** 생성 요청 중 인스턴스와 선택 상태는 보존하고 모든 조작점만 감춘다. */
  interactionHidden?: boolean | undefined;
}) {
  const { source, uploadId } = props;
  const autoRequested = useRef<string | null>(null);
  /** ㈎ 확장보기가 열려 있나 (R-A′ 이관). 닫는 길은 `closeExpand` 하나다 — 갈래를 만들지 않는다. */
  const [expanded, setExpanded] = useState(false);
  const [palettes, setPalettes] = useState<PaletteOption[] | null>(null);
  const [palette, setPalette] = useState('');
  const [classCount, setClassCount] = useState(DEFAULT_CLASS_COUNT);
  const [job, setJob] = useState<RenderJob | null>(null);
  const remaining = useStageRemaining(job?.renderId, job?.stage, job?.status);
  const [requesting, setRequesting] = useState(false);
  const [loadedImage, setLoadedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tileExpired, setTileExpired] = useState(false);
  const [unreachable, setUnreachable] = useState(false);
  const [accepted, setAccepted] = useState(false);
  /** 모달이 쥔 File을 화면에 보이기 위한 주소. File 자체가 저장 경로로 올라간다. */
  const [pickedThumb, setPickedThumb] = useState<string | null>(null);
  const thumbInput = useRef<HTMLInputElement | null>(null);
  const polling = useRef(0);
  /**
   * 폴링 **세대**. 새로 그리기 시작할 때와 화면이 사라질 때 올라간다. 이미 날아간 조회는
   * 취소할 수 없으므로(계약에 취소가 없다) 돌아온 값을 **세대가 다르면 버린다** —
   * `clearTimeout` 만으로는 이미 응답을 기다리는 중인 조회를 막지 못해, 옛 렌더의 늦은
   * 응답이 새 렌더의 화면을 덮고 떠난 화면 뒤로 폴링이 다시 예약됐다.
   */
  const pollGen = useRef(0);
  // 색 범위가 **조용히** 바뀌지 않게, 앞서 본 잠정 범위를 들고 있는다 (`§D.4`)
  const seenRange = useRef<{ stage: string; key: string } | null>(null);
  // WU-C3 — 고르개 셋. **컴포넌트 상태다**(URL 미반영 · 판정 축자).
  const [pieces, setPieces] = useState<PreviewPiece[]>([]);
  const [description, setDescription] = useState<TargetDescription | undefined>(undefined);
  const [pick, setPick] = useState<PickSelection>({});
  const [fallbackPiece, setFallbackPiece] = useState<PreviewPiece | undefined>(undefined);
  // 고르개 후보와 413 폴백이 **같은 한 번의 조회**를 쓴다 (수용 기준 「files 조회 1회」).
  const loadFiles = useMemo(
    () => (source.files ? onceFiles(() => source.files!(uploadId ?? '')) : undefined),
    [source, uploadId],
  );

  // 후보는 **서버가 준 값뿐이다.** 못 받으면 자리는 서고 잠긴다 — 지어내지 않는다.
  useEffect(() => {
    if (!uploadId) return;
    let alive = true;
    void (async () => {
      try {
        const list = await loadFiles?.();
        if (alive && list) setPieces(list);
      } catch {
        /* 조각 목록이 없으면 파일 고르개가 잠긴다. 등록은 막지 않는다. */
      }
      try {
        const desc = await source.describe?.(uploadId);
        if (alive && desc) setDescription(desc);
      } catch {
        /* 변수·시각 후보가 없으면 그 둘이 잠긴다. 기본값은 서버가 고른다. */
      }
    })();
    return () => {
      alive = false;
    };
  }, [source, uploadId, loadFiles]);

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

  useEffect(
    () => () => {
      window.clearTimeout(polling.current);
      // 떠난 뒤 도착하는 응답을 버린다 — `clearTimeout` 은 **예약된** 다음 조회만 지운다.
      pollGen.current += 1;
    },
    [],
  );

  useEffect(() => {
    const file = props.representativeFile;
    if (!file) {
      setPickedThumb(null);
      if (thumbInput.current) thumbInput.current.value = '';
      return;
    }
    const url = URL.createObjectURL(file);
    setPickedThumb(url);
    return () => URL.revokeObjectURL(url);
  }, [props.representativeFile]);

  async function draw(withoutReferenceGrid: boolean, override?: PickSelection) {
    if (!uploadId || !palette) return;
    // **한 번에 하나만 그린다.** 회차를 올리는 순간 앞선 요청·조회의 응답은 전부 버려진다
    //  — 바꿔 그리기가 겹쳐 그리기가 되지 않는 자리다(`upload-preview-poll-20260903` 규약).
    const gen = ++pollGen.current;
    setRequesting(true);
    setJob(null);
    setLoadedImage(null);
    setError(null);
    setTileExpired(false);
    setUnreachable(false);
    setAccepted(false);
    const sel: PickSelection = { ...pick, ...(override ?? {}) };
    try {
      // ⑴ 500MB 폴백 — 413 이면 조각 목록을 묻고 첫 renderable 로 다시 부른다.
      const { job: started, piece } = await createWithPieceFallback({
        create: (fileIds) =>
          source.createRender({
            target: {
              uploadId,
              ...(fileIds ? { fileIds } : sel.fileId ? { fileIds: [sel.fileId] } : {}),
            },
            style: { palette, classCount },
            ...(sel.variable ? { variable: sel.variable } : {}),
            ...(sel.instant ? { instant: sel.instant } : {}),
            withoutReferenceGrid,
          } as RenderRequest),
        files: loadFiles,
      });
      if (pollGen.current !== gen) return;
      setRequesting(false);
      if (piece) setFallbackPiece(piece);
      setJob(started);
      props.onRender?.({ renderId: started.renderId, withoutReferenceGrid });
      poll(started.renderId, gen);
    } catch {
      if (pollGen.current !== gen) return;
      setRequesting(false);
      // 그리는 서버에 닿지 못했다 — **등록은 그대로 진행된다**(`§E.2-⑩`)
      setUnreachable(true);
      setError(UNAVAILABLE);
    }
  }

  // 등록 첫 장면에서는 사용자가 별도 실행을 찾지 않아도 참고 그림을 준비한다.
  // 같은 업로드의 재렌더는 명시적 버튼으로만 실행해 실패를 무한 반복하지 않는다.
  useEffect(() => {
    if (!props.autoPreview || !uploadId || !palette || autoRequested.current === uploadId) return;
    autoRequested.current = uploadId;
    void draw(false);
  }, [props.autoPreview, uploadId, palette]);

  function poll(renderId: string, gen: number) {
    window.clearTimeout(polling.current);
    polling.current = window.setTimeout(async () => {
      try {
        const next = await source.getRender(renderId);
        if (pollGen.current !== gen) return;
        setJob(next);
        if (next.status === '그리는 중') poll(renderId, gen);
      } catch {
        if (pollGen.current !== gen) return;
        setUnreachable(true);
        setError(UNAVAILABLE);
      }
    }, POLL_MS);
  }

  // 조회 실패 뒤 서버의 마지막 진행 상태를 현재 진행으로 표시하지 않는다.
  const drawing = (requesting || job?.status === '그리는 중') && !error;
  const done = job?.status === '완료';
  // **실패는 200 + `failure`** 다. HTTP 상태로 판정하지 않는다.
  const failure = job?.status === '실패' ? job.failure : undefined;
  const partial = job?.partialFailure;
  const result: RenderResult | undefined = done ? job?.result : undefined;
  useEffect(() => {
    if (result) props.onResult?.(result);
  }, [result, props.onResult]);
  // 실패해도 이미 구운 값 미리보기·썸네일이 있으면 **감추지 않는다**
  const salvage = salvageOf(failure);
  // **성공 경로의 ①②** (`〈88〉` 묶음 3). 이전에는 성공하면 오히려 사라지던 자리다.
  const layers = result ? layersOf(result) : null;

  // ⭑ ⟨WU-C4⟩ **업로드 화면도 상세와 같은 훅·같은 버튼을 쓴다**(판정 축자 「세 화면 공유」).
  //   확장보기는 **자기 층의 배율을 따로 쥔다** — 같은 상태를 두 층이 나눠 쓰면 뒤 층을
  //   확대해 둔 채로 앞 층이 열리는 자리가 생긴다. 훅은 **조건 밖**에서 둘 다 부른다.
  const mapBounds = result?.bounds;
  const zoom = useZoomPan({ bounds: mapBounds });
  const expandZoom = useZoomPan({ bounds: mapBounds });

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

  /**
   * 자리 선점 틀의 **안쪽** 상태 (WU-C1). 바깥 상자는 이 값과 무관하게 같은 치수다 —
   * 파일을 고른 장면2 진입 즉시 서고, 그리는 중에도 실패해도 접히지 않는다.
   */
  const slotState: PreviewSlotState = drawing
    ? 'drawing'
    : failure || error
      ? 'failed'
      : result
        ? 'done'
        : props.renderable === false ? 'failed' : 'idle';

  /**
   * 대표 그림이 화면에 무엇을 보이는가 (`WU-A10`).
   * 사람이 고른 그림이 있으면 그것, 없으면 **자동 생성된 미리보기 축소본**이 기본이다.
   * `pickedThumb` 는 모달이 보관한 File의 수명에 맞춰 만든 화면 주소다.
   */
  const autoThumb = layers?.thumbnailUrl ?? salvage?.thumbnailUrl ?? null;
  const thumbSrc = pickedThumb ?? autoThumb;

  function pickThumb(file: File | null): void {
    if (!file || props.representativeDisabled) return;
    props.onRepresentativeFileChange?.(file);
  }

  const representativePicker = (
    <div className="thumbrow" data-testid="up-thumb-block">
      <button
        type="button"
        className="th-slot"
        data-testid="up-thumb-pick"
        aria-label="대표 그림 바꾸기"
        disabled={props.representativeDisabled}
        onClick={() => thumbInput.current?.click()}
      >
        {thumbSrc ? (
          <img className="th-img" alt="" data-testid="up-thumb-img" src={thumbSrc} />
        ) : (
          <span className="th-ph" data-testid="up-thumb-empty" aria-hidden="true" />
        )}
      </button>
      <div className="th-txt">
        <span className="th-t">대표 그림(썸네일)</span>
        <span className="th-n" data-testid="up-thumb-nudge">
          눌러서 다른 그림으로 바꿀 수 있어요
        </span>
      </div>
      {props.representativeFile ? (
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={props.representativeDisabled}
          onClick={() => props.onRepresentativeFileChange?.(null)}
        >
          자동 그림 사용
        </button>
      ) : null}
      <input
        ref={thumbInput}
        className="th-in"
        type="file"
        disabled={props.representativeDisabled}
        accept="image/png,image/jpeg,image/webp"
        data-testid="up-thumb-input"
        onChange={(e) => pickThumb(e.target.files?.[0] ?? null)}
      />
    </div>
  );

  if (props.representativeOnly) {
    return (
      <section
        className="mapstage"
        data-testid="up-preview"
        data-mode="representative-recovery"
        hidden={props.interactionHidden}
        inert={props.interactionHidden ? true : undefined}
      >
        <div className="mapbar">
          <span className="mt">대표 그림 저장 마무리</span>
        </div>
        {representativePicker}
      </section>
    );
  }

  return (
    <section
      className="mapstage"
      data-testid="up-preview"
      hidden={props.interactionHidden}
      inert={props.interactionHidden ? true : undefined}
    >
      <div className="mapbar">
        <span className="mt">미리보기</span>
        {/* ㈎ 확장보기 (R-A′ 이관 · rev2 `openPvExpand()`) — 오버레이는 **업로드 모달 위**에
            서고 스스로 `data-esc-layer` 표식을 단다. 여는 자리는 미리보기 줄 하나다. */}
        <button
          type="button"
          className="btn btn-ghost btn-sm pvx-open"
          data-testid="pv-expand"
          aria-label="미리보기 크게 보기"
          onClick={() => setExpanded(true)}
        >
          ⤢
        </button>
      </div>

      {palettes !== null && palettes.length !== 3 ? (
        <p className="pv-failure" role="alert" data-testid="up-palette-issue">
          팔레트 목록이 예상한 3종과 달라요. 받은 목록을 표시하고 있어요.
        </p>
      ) : null}
      <details className="up-preview-options">
        <summary>미리보기 설정 · 대표 그림</summary>
      {/* 대표 그림은 자동 축소본이 기본이고, 고르면 등록 뒤 사용자 그림으로 별도 저장한다. */}
      {representativePicker}

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

      </details>

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

      {/* ⬛ 자리 선점 틀 — **파일을 고른 순간 이미 서 있다**(축 ① · 4:3 · 네 상태 치수 불변).
          안쪽만 idle(`.vizph`) → drawing(3단계) → done(그림) | failed(`.vizerr` · salvage)로 갈린다. */}
      <PreviewSlot state={slotState} testId="up-preview-slot">
      {/* ⑵ 고르개 셋 — 파일·변수·시각. **틀 안 컨트롤 줄이고 두 화면이 같은 컴포넌트를 쓴다.**
          한 번에 값 하나만 바뀌고, 바꾸는 즉시 **바꿔 그리기**가 돈다. */}
      <PreviewPickRow
        idPrefix="up"
        pieces={pieces}
        description={description}
        selection={pick}
        disabled={drawing}
        fallbackPiece={fallbackPiece}
        onPick={(next) => {
          setPick((prev) => ({ ...prev, ...next }));
          if (uploadId) void draw(false, next);
        }}
      />
      {/* 진행을 **단계로** 말한다. `stage` 는 `그리는 중` 일 때만 있다 */}
      {drawing && (
        <div className="vizload" role="status" aria-live="polite" data-testid="up-preview-stage">
          <span className="spin" aria-hidden="true" />
          <span>{requesting ? '미리보기 요청 중' : job?.stage ?? '지도 그리는 중'}…</span>
          {remaining !== null ? <span data-testid="up-preview-eta">이 단계 약 {Math.ceil(remaining / 1000)}초 남음</span> : null}
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
          {previewImageSrc(result) && loadedImage !== previewImageSrc(result) && !tileExpired && (
            <div className="vizload" role="status" aria-live="polite" data-testid="up-preview-image-loading">
              <span className="spin" aria-hidden="true" />그림 불러오는 중…
            </div>
          )}
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
            <div
              className="pv-viewport"
              data-testid="up-preview-viewport"
              ref={zoom.viewportRef}
              onMouseDown={zoom.onMouseDown}
              /* 더블클릭 = 데이터 경계에 맞춤(여백 0). 상세와 같은 규칙이다. */
              onDoubleClick={zoom.fitToData}
              data-zoomable="true"
            >
              <div
                className="pv-layers"
                data-testid="up-preview-layers"
                data-zoom-scale={String(zoom.scale)}
                data-zoom-base-scale={String(zoom.baseScale)}
                {...(zoom.rungKm !== undefined ? { 'data-scale-rung-km': String(zoom.rungKm) } : {})}
                style={{
                  transform: `translate(${zoom.x}px, ${zoom.y}px) scale(${zoom.scale})`,
                  transformOrigin: '0 0',
                }}
              >
                {/* ⭑ ⟨WU-C5⟩ 자립형 벡터 배경 — 래스터 아래 · 경계 있을 때만(외부 요청 0) */}
                {mapBounds ? <BasemapLayer bounds={mapBounds} /> : null}
                {zoom.showBoundsOutline ? <BoundsOutline /> : null}
                <img
                  className="tile pv-tile"
                  alt="미리보기"
                  /* 계약이 `oneOf` 라 갈래마다 다른 자리다 — 단일 이미지(stage 1)와 타일(stage 2) */
                  data-testid={result.imageUrl ? 'up-preview-image' : 'up-preview-tile'}
                  data-preview-variable={result.legend.variable ?? ''}
                  src={previewImageSrc(result)}
                  onLoad={(event) => {
                    zoom.onImageLoad(event);
                    setLoadedImage(previewImageSrc(result) ?? null);
                  }}
                  onError={() => setTileExpired(true)}
                />
              </div>
            </div>
          ) : null}
          {/* 확대/축소 줄 — 상세·확장보기와 **같은 컴포넌트**다(사용자 스토리 7) */}
          <PreviewZoomControls zoom={zoom} testId="up-preview-zoom" />
          {tileExpired && (
            <div className="vizerr" role="alert" aria-live="assertive" data-testid="up-preview-expired">
              그림을 불러오지 못했어요. 미리보기를 다시 그려 주세요.
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

      {!job && !error && (
        <div className="vizph">
          {props.renderable === false ? (
            <div data-testid="up-preview-unsupported" role="status">
              <div className="pt">지도로 그릴 수 없는 파일이에요</div>
              <div className="pd">파일은 그대로 등록할 수 있어요. 미리보기 설정을 열어 직접 그리기를 시도할 수도 있어요.</div>
            </div>
          ) : (
            <>
              <div className="pt">아직 그리지 않았어요</div>
              <div className="pd">미리보기 설정을 열어 팔레트와 구간 수를 고르고 미리보기 그리기를 눌러 주세요.</div>
            </>
          )}
        </div>
      )}
      </PreviewSlot>

      {/* 「미리보기를 보려면 격자를 올리세요」 — 문구와 상태는 `gridFlow.ts` 가 소유한다 */}
      {grid && (gridBlock || grid.options) ? (
        <GridUploadBlock
          state={gridBlock}
          transfer={grid.transfer ?? null}
          {...(grid.options ? { options: grid.options } : {})}
          reuseBusy={grid.reuseBusy ?? false}
          actions={{
            onPickGrid: grid.onPickGrid,
            onSkipGrid: grid.onSkipGrid,
            ...(grid.onReuseGrid ? { onReuseGrid: grid.onReuseGrid } : {}),
            ...(grid.onCancel ? { onCancel: grid.onCancel } : {}),
            onAccept: () => {
              setAccepted(true);
              grid.onAccept?.();
            },
            ...(grid.onFlipAxes ? { onFlipAxes: grid.onFlipAxes } : {}),
          }}
        />
      ) : null}

      {/* ㈎ 확장보기 오버레이 — 배경 클릭·× 가 **같은 한 함수**를 탄다(A9R 규율).
          ⚠ 업로드 모달의 `requestClose` 를 부르지 않는다 — Esc 우선순위가 「확장보기 →
             … → 업로드」라 위 층이 먼저 닫힌다. 위 층이 아래 층을 닫으면 그 순서가 뒤집힌다. */}
      {expanded && (
        <PreviewExpandOverlay title="미리보기" requestClose={() => setExpanded(false)}>
          {result?.imageUrl ? (
            <>
              <div
                className="pv-viewport"
                data-testid="pv-expand-viewport"
                ref={expandZoom.viewportRef}
                onMouseDown={expandZoom.onMouseDown}
                onDoubleClick={expandZoom.fitToData}
                data-zoomable="true"
              >
                <div
                  className="pv-layers"
                  data-testid="pv-expand-layers"
                  data-zoom-scale={String(expandZoom.scale)}
                  data-zoom-base-scale={String(expandZoom.baseScale)}
                  {...(expandZoom.rungKm !== undefined
                    ? { 'data-scale-rung-km': String(expandZoom.rungKm) }
                    : {})}
                  style={{
                    transform: `translate(${expandZoom.x}px, ${expandZoom.y}px) scale(${expandZoom.scale})`,
                    transformOrigin: '0 0',
                  }}
                >
                  {mapBounds ? <BasemapLayer bounds={mapBounds} /> : null}
                  {expandZoom.showBoundsOutline ? <BoundsOutline /> : null}
                  <img
                    className="pvx-img pv-tile"
                    alt=""
                    data-testid="pv-expand-image"
                    src={result.imageUrl}
                    onLoad={expandZoom.onImageLoad}
                  />
                </div>
              </div>
              <PreviewZoomControls zoom={expandZoom} testId="pv-expand-zoom" />
            </>
          ) : (
            <p className="muted" data-testid="pv-expand-empty">
              아직 그리지 않았어요
            </p>
          )}
        </PreviewExpandOverlay>
      )}
    </section>
  );
}
