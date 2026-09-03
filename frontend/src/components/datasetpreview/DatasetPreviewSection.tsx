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
//  · 겹쳐 보기 = 정본 근거·완료 정의가 아직 없거나 다른 항목 소유.
//    ⭑ ⟨개정 2026-09-03 · `PLAN-SoT §9 〈294〉` · 15차 해제⟩ **값 조회는 이제 이 구역이 짓는다** —
//    정본 §8 이 조회 자리를 **등록된 데이터셋 · 좌표 있는 자료 · 본체를 볼 수 있는 사람**에만
//    세우고, 그 셋이 전부 이 자리에서 성립한다(`ValueLookupPanel`). ／ 이전 표기 ~~값 조회 ·~~
//    ⭑ ⟨개정 2026-08-31 · Ted 판정 ⑩ · `PLAN-SoT §9 〈238〉`⟩ **타일 뷰는 이제 이 구역이 짓는다** —
//    지도 화면을 타일 방식으로 전환했다(`03-HANDOFF §4` `#48`). ／ 이전 표기 ~~타일 뷰 ·~~
//
// **이 구역이 새로 짓는 것 둘** (화면 레인 · `PLAN-SoT §9 〈231〉`·`〈232〉` 뒤)
//  · **확대(줌)** — 정본 `§8` 「확대(줌) — 왜 넣는가, 무엇이 되면 된 것인가」 조건 여섯.
//    변환은 **이미 그린 결과 위에서만** 일어난다(조건 ⑶ 렌더 재요청 0) · 상태를 저장하지
//    않는다(조건 ⑹) · 한계는 **데이터가 가진 해상도**다(조건 ⑷ · `useZoomPan`).
//  · **스크린샷** — 중계 op `createPreviewScreenshot`(11차 동결 해제 `〈231〉`)에 닿는다.
//    정본 `§6` 이 **편집 권한자 컨트롤**로 두므로 보기 전용에는 자리째 없다(`§3.2`).
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
import { useZoomPan } from '../preview/useZoomPan';
import { ScreenshotButton } from './ScreenshotButton';
import { ValueLookupPanel, useValueLookup } from './ValueLookupPanel';
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
  /**
   * ⭑ ⟨버그 14⟩ **이 구역이 어느 데이터의 것인지 스스로 말한다.** 계보 줄이 제목처럼
   * 읽혀 스크롤 위치에 따라 무엇을 보고 있는지 알 수 없던 결함(recon-B §5)의 최소 수정 —
   * 상세가 **이미 들고 있는 값**(`detail.detail.name`·`fileName`)을 머리에 낸다.
   * 새 API·계약을 만들지 않는다.
   */
  datasetName?: string | undefined;
  fileName?: string | null | undefined;
  /**
   * ⭑ ⟨버그 13 · Ted 판정⟩ 「상세에서 원본 픽셀 크기를 알 수 있게 해 달라」.
   * 상세가 **이미 읽어 온** `basicInfo.grid`(격자 간격/해상도) 하나만 받는다 — 원본 배열
   * 크기(폭×높이)는 렌더가 완료돼야 사이드카에서 나오므로 `StartedPreview` 가 스스로 잰다.
   */
  gridResolution?: string | null | undefined;
}) {
  const source = useMemo(
    () => props.source ?? apiDatasetPreviewSource(props.datasetId),
    [props.source, props.datasetId],
  );
  const [start, setStart] = useState<StartState>({ phase: '시작하는 중' });
  // 렌더가 완료된 뒤 사이드카가 알려주는 원본 배열 크기. 그때까지 · 못 읽으면 `undefined` —
  // 확대 한계(`useZoomPan`)가 이미 같은 사이드카를 쓰는 것과 같은 규칙이다(조건 ⑷).
  const [nativeSize, setNativeSize] = useState<{ width: number; height: number } | undefined>(
    undefined,
  );

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
      <h2 className="pv-h2">
        미리보기{props.datasetName ? ` — ${props.datasetName}` : ''}
      </h2>
      {props.fileName ? (
        <p className="pv-muted" data-testid="preview-target-file">
          {props.fileName}
        </p>
      ) : null}
      {formatSourceGrid(props.gridResolution, nativeSize) ? (
        <p className="pv-muted" data-testid="preview-source-grid">
          {formatSourceGrid(props.gridResolution, nativeSize)}
        </p>
      ) : null}

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
        <StartedPreview
          source={relay}
          datasetSource={source}
          renderId={start.renderId}
          pollMs={props.pollMs ?? 1000}
          onNativeSize={setNativeSize}
        />
      ) : null}
    </section>
  );
}

/**
 * ⭑ ⟨버그 13 · Ted 판정⟩ 격자 간격/해상도와 원본 배열 크기를 한 캡션으로 잇는다.
 * **둘 다 선택 값이다** — 어느 한쪽이 없으면 그 조각만 뺀다. 둘 다 없으면 `undefined`
 * 를 돌려주고 호출부가 자리째 뺀다(없는 값을 지어내지 않는다).
 */
function formatSourceGrid(
  grid: string | null | undefined,
  size: { width: number; height: number } | undefined,
): string | undefined {
  const parts: string[] = [];
  if (grid) parts.push(`격자 ${grid}`);
  if (size) parts.push(`${size.width} × ${size.height}`);
  return parts.length > 0 ? parts.join(' · ') : undefined;
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

function StartedPreview(props: {
  source: PreviewSource;
  datasetSource: DatasetPreviewSource;
  renderId: string;
  pollMs: number;
  /** ⭑ ⟨버그 13⟩ 사이드카가 읽어 준 원본 배열 크기를 머리 캡션(부모)에 올려 준다. */
  onNativeSize?: ((size: { width: number; height: number }) => void) | undefined;
}) {
  const { state } = usePreviewRender({
    source: props.source,
    renderId: props.renderId,
    pollMs: props.pollMs,
  });
  // **훅은 조건 밖에서 부른다** — 렌더가 어느 단계든 같은 순서로 불려야 한다.
  const zoom = useZoomPan();
  // 값 조회 (`〈294〉`). **렌더를 다시 시작하지 않는다**(완료 정의 ⑵).
  const value = useValueLookup(props.datasetSource);

  // **원본 해상도를 한 번만 묻는다** (정본 v2.6 §8 조건 ⑷ · `〈238〉`).
  // 타일 표면에는 잴 그림 한 장이 없어 사이드카가 그 값을 말한다. **확대 조작은 이
  // 경로를 다시 타지 않는다** — 의존이 결과 한 건의 사이드카 주소 하나다(조건 ⑶).
  const done = state.phase === '완료' ? state.result : undefined;
  const sidecarUrl = done?.tileUrlTemplate ? done.sidecarUrl : undefined;
  const { datasetSource } = props;
  const { onNativeWidth } = zoom;
  const { onNativeSize } = props;
  useEffect(() => {
    if (!sidecarUrl) return;
    let alive = true;
    void (async () => {
      const geom = await datasetSource.mapGeometry(sidecarUrl);
      // **못 읽으면 아무것도 하지 않는다** — 한계를 지어내지 않는다.
      if (alive && geom) {
        onNativeWidth(geom.width);
        // ⭑ ⟨버그 13⟩ 같은 사이드카 응답의 `height` 도 마저 써 준다 — 새 왕복이 아니다.
        onNativeSize?.(geom);
      }
    })();
    return () => {
      alive = false;
    };
  }, [datasetSource, sidecarUrl, onNativeWidth, onNativeSize]);

  if (state.phase === '그리는 중')
    return state.stage ? <RenderStageNotice stage={state.stage} /> : <RenderStageNotice />;

  if (state.phase === '완료')
    return (
      <>
        {/* 부분 실패는 **오류가 아니다** — 지도를 그대로 그리고 무엇이 빠졌는지 말한다 */}
        {state.partialFailure ? <PartialFailureNotice partial={state.partialFailure} /> : null}
        <PreviewMap
          result={state.result}
          zoom={zoom}
          /* **좌표가 없는 결과에는 자리째 없다**(완료 정의 ⑹) — `bounds` 가 그 판정이다 */
          onPickPoint={state.result.bounds ? value.pick : undefined}
          valuePanel={state.result.bounds ? <ValueLookupPanel state={value.state} /> : null}
          actions={
            <ScreenshotButton
              source={props.datasetSource}
              renderId={props.renderId}
              result={state.result}
              zoom={zoom}
            />
          }
        />
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
