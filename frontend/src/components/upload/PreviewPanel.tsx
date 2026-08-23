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
import { useEffect, useRef, useState } from 'react';
import type { PaletteOption, PreviewSource, RenderJob } from './types';

/** 정본 §9 「그리는 서버에 연결 못 함」. 코드가 없을 때 쓰는 기본 문구. */
const UNAVAILABLE = '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.';
/** 렌더 진행 확인 간격. 서버 왕복이 수 초~수십 초라 정본이 「단계로 말한다」고 했다. */
const POLL_MS = 250;
/** 구간 수 3~9 · 기본 6 (`Policy_데이터셋_상세 §5` · 계약 `RenderStyle.classCount`). */
const DEFAULT_CLASS_COUNT = 6;

export function PreviewPanel(props: {
  source: PreviewSource;
  uploadId: string | null;
  /** 기준 격자 파일이 붙어 있는가. 없으면 정본 §9 안내 + `짝 파일 없이 그려 보기`. */
  hasReferenceGrid: boolean;
}) {
  const { source, uploadId } = props;
  const [palettes, setPalettes] = useState<PaletteOption[] | null>(null);
  const [palette, setPalette] = useState('');
  const [classCount, setClassCount] = useState(DEFAULT_CLASS_COUNT);
  const [job, setJob] = useState<RenderJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tileExpired, setTileExpired] = useState(false);
  const polling = useRef(0);

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
    try {
      const started = await source.createRender({
        target: { uploadId },
        style: { palette, classCount },
        withoutReferenceGrid,
      });
      setJob(started);
      poll(started.renderId);
    } catch {
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
        setError(UNAVAILABLE);
      }
    }, POLL_MS);
  }

  const drawing = job?.status === '그리는 중';
  const done = job?.status === '완료';
  // **실패는 200 + `failure`** 다. HTTP 상태로 판정하지 않는다.
  const failure = job?.status === '실패' ? job.failure : undefined;
  const partial = job?.partialFailure;
  const result = done ? job?.result : undefined;

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
            onChange={(e) => setClassCount(Number(e.target.value))}
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

      {result && (
        <div className="mapcanvas" data-testid="up-preview-map">
          {/* `tileUrlTemplate` 을 **그대로** 쓴다. 질의부를 떼거나 다시 조립하면 서명이 깨진다 */}
          <img
            className="tile"
            alt="미리보기 타일"
            data-testid="up-preview-tile"
            src={result.tileUrlTemplate.split('{z}').join('0').split('{x}').join('0').split('{y}').join('0')}
            onError={() => setTileExpired(true)}
          />
          {tileExpired && (
            <div className="vizerr" role="alert" aria-live="assertive" data-testid="up-preview-expired">
              타일 주소의 수명이 다했어요. 미리보기를 다시 그려 주세요.
            </div>
          )}
        </div>
      )}

      {!job && !error && (
        <div className="vizph">
          <div className="pt">아직 그리지 않았어요</div>
          <div className="pd">위에서 팔레트와 구간 수를 고르고 미리보기 그리기를 눌러 주세요.</div>
        </div>
      )}
    </section>
  );
}
