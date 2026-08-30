// S-05 데이터셋 상세 — **미리보기(시각화) 구역** (WU-P3 · 격자 표현).
//
// 정본 = `E-03_데이터셋_상세/documents/Policy_데이터셋_상세.md`.
//  · `§1.3-1` 한 페이지 스크롤이다. **탭으로 콘텐츠를 숨기지 않는다** — 그래서 탭이 없다.
//  · `§1.3-5` 시각화는 한 번에 값 하나만 그린다. **보기는 전원, 편집은 권한자다.**
//  · `§8` 지도 표현 — **무엇으로 그릴지는 사람이 고르지 않는다.** 격자·경계·점의 판정은
//    포맷이 하고 viz-render 가 한다. 그래서 요청에 표현 종류를 싣지 않고, 전환 버튼도 없다
//    (목업의 격자·경계·점 버튼은 「세 표현을 검토하려고 둔 데모 장치」라고 정본이 적는다).
//  · `§8` **미리보기는 서버가 그린다** — 서버 왕복이라 **단계를 말해야 한다**
//    (파일 읽기 → 그리기 → 범례). 한 덩어리 「로딩 중」으로 두지 않는다.
//  · `§5`  시각화 구간 수 — 3~9 단계. **기본 6.**
//
// **이 구역이 짓지 않는 것** (범위를 늘리지 않는다 — `CLAUDE.md §5`)
//  · 팔레트·구간 수 컨트롤과 그에 따른 재렌더 = `V-1`(서버측) · `J-6`(선택 UI). 이 구역은
//    기본값으로 **한 번 그린다.** 보기 전용 화면에는 정본이 그 컨트롤을 애초에 두지 않는다(`§3.2`).
//  · 스크린샷 버튼 = `createScreenshot` 은 viz-render 에 서 있으나 **FE 도달 계약 표면이 없다**
//    (`fe-core.yaml` 에 중계 op 0건). 갈 곳 없는 버튼을 세우지 않는다 — 계약 개정 사안이다.
//  · 확대·타일 뷰 · 값 조회 · 겹쳐 보기 = 각각 정본 근거·완료 정의가 아직 없거나 다른 항목 소유.
import { useEffect, useMemo, useState } from 'react';
import {
  NotRenderableNotice,
  PartialFailureNotice,
  PreviewMap,
  RenderFailureNotice,
  RenderStageNotice,
} from '../preview/PreviewPanels';
import {
  NotRenderableError,
  PreviewGone,
  PreviewUnavailable,
  type PreviewSource,
  type RerenderInput,
} from '../preview/types';
import { usePreviewRender } from '../preview/usePreviewRender';
import '../preview/preview.css';
import { UNAVAILABLE_MESSAGE, apiDatasetPreviewSource } from './datasetPreviewSource';
import type { DatasetPreviewSource } from './types';

/** 정본 `§5` — 「3~9 단계. **기본 6**」. 화면이 다른 값을 고르지 않는다. */
export const DEFAULT_CLASS_COUNT = 6;

/** 렌더 시작 전 단계. 시작한 뒤는 `usePreviewRender` 가 상태를 맡는다. */
type StartState =
  | { phase: '시작하는 중' }
  | { phase: '시작함'; renderId: string }
  | { phase: '그릴 수 없음'; message: string; renderableFormats: string[] }
  | { phase: '만들 수 없음'; message: string };

export function DatasetPreviewSection(props: {
  datasetId: string;
  source?: DatasetPreviewSource | undefined;
  pollMs?: number | undefined;
}) {
  const source = useMemo(
    () => props.source ?? apiDatasetPreviewSource(),
    [props.source],
  );
  const [start, setStart] = useState<StartState>({ phase: '시작하는 중' });

  useEffect(() => {
    if (!props.datasetId) return;
    let alive = true;
    void (async () => {
      try {
        const list = await source.palettes();
        if (!alive) return;
        const palette = list[0]?.palette;
        // **빈 목록으로 렌더를 부르지 않는다** — 팔레트 키를 화면이 지어내면 그 순간
        // `RenderStyle.palette` 의 정본이 viz-render 에서 화면으로 옮겨 앉는다.
        if (!palette) {
          setStart({ phase: '만들 수 없음', message: UNAVAILABLE_MESSAGE });
          return;
        }
        const job = await source.create({
          datasetId: props.datasetId,
          palette,
          classCount: DEFAULT_CLASS_COUNT,
        });
        if (!alive) return;
        setStart({ phase: '시작함', renderId: job.renderId });
      } catch (e) {
        if (!alive) return;
        if (e instanceof NotRenderableError)
          setStart({
            phase: '그릴 수 없음',
            message: e.message,
            renderableFormats: e.renderableFormats,
          });
        else if (e instanceof PreviewGone)
          setStart({ phase: '만들 수 없음', message: UNAVAILABLE_MESSAGE });
        else
          setStart({
            phase: '만들 수 없음',
            message: e instanceof PreviewUnavailable ? e.message : UNAVAILABLE_MESSAGE,
          });
      }
    })();
    return () => {
      alive = false;
    };
  }, [source, props.datasetId]);

  // 렌더 경로 소비 규약(실패는 200+`failure` · 단계 · 부분 실패 · 만료)은 **한 자리에만 둔다** —
  // S-08 과 두 벌로 두면 두 화면의 판정이 갈린다.
  const relay: PreviewSource = useMemo(
    () => ({
      get: (renderId: string) => source.get(renderId),
      probeTile: (url: string) => source.probeTile(url),
      create: (input: RerenderInput) =>
        source.create({
          datasetId: props.datasetId,
          palette: input.palette,
          classCount: input.classCount,
        }),
    }),
    [source, props.datasetId],
  );

  return (
    <section className="dt-preview" data-testid="dataset-preview" aria-label="미리보기">
      <h2 className="pv-h2">미리보기</h2>

      {start.phase === '시작하는 중' ? <RenderStageNotice /> : null}

      {start.phase === '그릴 수 없음' ? (
        <NotRenderableNotice
          message={start.message}
          renderableFormats={start.renderableFormats}
        />
      ) : null}

      {start.phase === '만들 수 없음' ? <UnavailableNotice message={start.message} /> : null}

      {/* **렌더가 시작된 뒤에야 마운트한다.** `usePreviewRender` 는 `renderId` 를 마운트 시점에
          한 번 읽으므로(S-08 은 이어받은 id 를 들고 들어온다) 나중에 건네면 조회가 시작되지 않는다.
          공용 훅을 고치지 않고 **마운트 시점을 맞춘다** — S-08 의 소비 규약을 건드리지 않기 위해서다. */}
      {start.phase === '시작함' ? (
        <StartedPreview source={relay} renderId={start.renderId} pollMs={props.pollMs ?? 1000} />
      ) : null}
    </section>
  );
}

/** 정본 §8 「그리는 서버에 연결 못 함」 자리. 그릴 수 없는 것과 쓸 수 없는 것은 다르다. */
function UnavailableNotice(props: { message: string }) {
  return (
    <div className="pv-failure" data-testid="preview-unavailable" aria-live="assertive" role="alert">
      <p>{props.message}</p>
      <p className="pv-muted">다운로드·계보 확인은 그대로 할 수 있어요.</p>
    </div>
  );
}

function StartedPreview(props: { source: PreviewSource; renderId: string; pollMs: number }) {
  const { state } = usePreviewRender({
    source: props.source,
    renderId: props.renderId,
    pollMs: props.pollMs,
  });

  if (state.phase === '그리는 중')
    return state.stage ? <RenderStageNotice stage={state.stage} /> : <RenderStageNotice />;

  if (state.phase === '완료')
    return (
      <>
        {/* 부분 실패는 **오류가 아니다** — 지도를 그대로 그리고 무엇이 빠졌는지 말한다 */}
        {state.partialFailure ? <PartialFailureNotice partial={state.partialFailure} /> : null}
        <PreviewMap result={state.result} />
      </>
    );

  if (state.phase === '실패') return <RenderFailureNotice message={state.message} />;

  if (state.phase === '그릴 수 없음')
    return (
      <NotRenderableNotice message={state.message} renderableFormats={state.renderableFormats} />
    );

  if (state.phase === '만들 수 없음') return <UnavailableNotice message={state.message} />;

  if (state.phase === '만료됨') return <UnavailableNotice message={UNAVAILABLE_MESSAGE} />;

  return null;
}
