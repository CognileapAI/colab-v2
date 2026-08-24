// 미리보기 한 건의 상태 기계. **렌더 경로 소비 규약이 전부 여기에 모인다.**
//
//  · 실패는 `200 + failure` 다 — HTTP 오류가 아니다
//  · `stage` 는 `그리는 중` 일 때만 있고, 값은 정본 3문구 그대로다
//  · `partialFailure` 는 실패가 아니다 — `완료` 로 남고 읽힌 조각으로 그린다
//  · 415 는 「등록할 수 없음」이 아니다 — 그릴 수 있는 형식을 함께 말한다
//  · 만료는 만료라고 말한다 (조회 404 · 타일 401 둘 다)
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  NotRenderableError,
  PreviewGone,
  PreviewUnavailable,
  type PartialFailure,
  type PreviewSource,
  type RenderResult,
  type RenderStage,
  type RerenderInput,
} from './types';
import { tileUrl } from './tiles';

/** 만료 문구는 정본 §8.1 수명 행·§9 마지막 행 그대로다. 여기서 새로 쓰지 않는다. */
export const EXPIRED_MESSAGE = '이 파일은 더 이상 없어요. 다시 올려 주세요.';

export type PreviewState =
  | { phase: '이어받은 미리보기 없음' }
  | { phase: '그리는 중'; stage?: RenderStage }
  | { phase: '완료'; result: RenderResult; partialFailure?: PartialFailure }
  | { phase: '실패'; code: string; message: string }
  | { phase: '그릴 수 없음'; message: string; renderableFormats: string[] }
  | { phase: '만료됨' }
  | { phase: '만들 수 없음'; message: string };

export interface UsePreviewRenderInput {
  source: PreviewSource;
  renderId: string | undefined;
  pollMs: number;
}

export function usePreviewRender({ source, renderId, pollMs }: UsePreviewRenderInput): {
  state: PreviewState;
  rerender: (input: RerenderInput) => void;
} {
  // 다시 그리기가 **같은 renderId** 를 돌려줄 수도 있으므로 회차를 함께 센다 —
  // id 만 보면 그 경우에 조회가 다시 시작되지 않고 화면이 `그리는 중` 에 멈춘다
  const [current, setCurrent] = useState<{ id: string; nonce: number } | undefined>(
    renderId ? { id: renderId, nonce: 0 } : undefined,
  );
  const [state, setState] = useState<PreviewState>(
    renderId ? { phase: '그리는 중' } : { phase: '이어받은 미리보기 없음' },
  );
  const probed = useRef<string | null>(null);

  useEffect(() => {
    if (!current) return;
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const step = async () => {
      try {
        const job = await source.get(current.id);
        if (!alive) return;
        if (job.status === '그리는 중') {
          // 단계를 한 덩어리 「로딩 중」으로 접지 않는다 — 멈춘 것인지 구분되지 않는다
          setState(job.stage ? { phase: '그리는 중', stage: job.stage } : { phase: '그리는 중' });
          timer = setTimeout(step, pollMs);
          return;
        }
        if (job.status === '실패') {
          // 문구는 서버(정본)가 준 것을 그대로 쓴다. 화면이 다시 지어내지 않는다
          setState({
            phase: '실패',
            code: job.failure?.code ?? '',
            message: job.failure?.message ?? '',
          });
          return;
        }
        if (!job.result) {
          setState({ phase: '만들 수 없음', message: '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.' });
          return;
        }
        setState({
          phase: '완료',
          result: job.result,
          // 부분 실패는 **완료** 안에 담긴다 — 오류 자리로 보내지 않는다
          ...(job.partialFailure ? { partialFailure: job.partialFailure } : {}),
        });
        // 타일 한 장을 찔러 본다. 401 이면 서명이 죽은 것이고 그것은 **만료**다.
        // ⚠ **타일 갈래일 때만이다** — stage 1 의 단일 이미지 결과에는 템플릿이 없고,
        // 없는 것을 찔러 「만료」로 단정하지 않는다 (`〈85〉` 로 갈래가 둘이 됐다).
        const url = job.result.tileUrlTemplate
          ? tileUrl(job.result.tileUrlTemplate, 0, 0, 0)
          : undefined;
        if (url && probed.current !== url) {
          probed.current = url;
          const tile = await source.probeTile(url);
          if (alive && tile === 'expired') setState({ phase: '만료됨' });
        }
      } catch (e) {
        if (!alive) return;
        if (e instanceof PreviewGone) setState({ phase: '만료됨' });
        else if (e instanceof NotRenderableError)
          setState({
            phase: '그릴 수 없음',
            message: e.message,
            renderableFormats: e.renderableFormats,
          });
        else if (e instanceof PreviewUnavailable)
          setState({ phase: '만들 수 없음', message: e.message });
        else
          setState({
            phase: '만들 수 없음',
            message: '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.',
          });
      }
    };

    void step();
    return () => {
      alive = false;
      if (timer) clearTimeout(timer);
    };
  }, [source, current, pollMs]);

  const rerender = useCallback(
    (input: RerenderInput) => {
      setState({ phase: '그리는 중' });
      probed.current = null;
      source
        .create(input)
        .then((job) => setCurrent((prev) => ({ id: job.renderId, nonce: (prev?.nonce ?? 0) + 1 })))
        .catch((e) => {
          if (e instanceof PreviewGone) setState({ phase: '만료됨' });
          else if (e instanceof NotRenderableError)
            setState({
              phase: '그릴 수 없음',
              message: e.message,
              renderableFormats: e.renderableFormats,
            });
          else
            setState({
              phase: '만들 수 없음',
              message:
                e instanceof PreviewUnavailable
                  ? e.message
                  : '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.',
            });
        });
    },
    [source],
  );

  return { state, rerender };
}
