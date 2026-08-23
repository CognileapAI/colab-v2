/**
 * S-08 미등록 파일 미리보기 — 정본 `Policy_업로드와_계보_확정 §8.1` 전 행.
 *
 * **이 화면은 사실을 하나도 만들지 않는다** (§7.1 · `P2.md §2-27`) — D3 카탈로그에 행이
 * 생기지 않고, 계보·검색·프로젝트 어느 읽기에도 비치지 않는다. 여기서 하는 일은 셋뿐이다:
 * 이어받은 미리보기를 **조회**하고, 표현을 바꾸면 **다시 그리고**, 등록으로 가는 **길을 낸다.**
 *
 * **미리보기의 이어짐이 이 화면의 요점이다** (§8.1 미리보기 행 — 「업로드 모달에서 그린
 * 미리보기를 그대로 이어서 보여준다」). 그래서 S-08 은 도착하자마자 다시 그리지 않고,
 * S-04 가 넘긴 `renderId` 를 **조회**한다.
 */
import { useMemo, useState } from 'react';
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  BasicInfoPanel,
  EmptySlots,
  ExpiredNotice,
  NotRenderableNotice,
  PartialFailureNotice,
  PreviewMap,
  RenderFailureNotice,
  RenderStageNotice,
  VolatileNotice,
} from '../components/preview/PreviewPanels';
import { DEFAULT_CLASS_COUNT, PreviewControls } from '../components/preview/PreviewControls';
import {
  RENDER_QUERY_KEY,
  REGISTER_FROM_PREVIEW_STATE_KEY,
  readPreviewHandoff,
} from '../components/preview/handoff';
import { apiPreviewSource } from '../components/preview/previewSource';
import { EXPIRED_MESSAGE, usePreviewRender } from '../components/preview/usePreviewRender';
import type { PreviewSource } from '../components/preview/types';
import '../components/preview/preview.css';

/** 나가기는 헤더 밖 제 줄에 하나만 둔다 — 상세(S-05)와 같은 규약이다. */
const BACK = { label: '데이터셋 목록', to: '/datasets' };

export function UnregisteredPreviewPage(props: { source?: PreviewSource; pollMs?: number } = {}) {
  const { uploadId = '' } = useParams();
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();

  // 주소가 이어짐의 실물이고, 라우터 state 는 헤더에서 읽은 값을 함께 나른다
  const handoff = useMemo(() => readPreviewHandoff(location.state), [location.state]);
  const renderId = params.get(RENDER_QUERY_KEY) ?? handoff?.renderId;

  const source = useMemo(() => props.source ?? apiPreviewSource(), [props.source]);
  const { state, rerender } = usePreviewRender({
    source,
    renderId: renderId ?? undefined,
    pollMs: props.pollMs ?? 1000,
  });

  const [classCount, setClassCount] = useState(DEFAULT_CLASS_COUNT);

  const palette = state.phase === '완료' ? state.result.legend.palette : null;
  const variable = state.phase === '완료' ? state.result.legend.variable : undefined;

  // 헤더에서 읽은 값만 세운다. 렌더가 **실제로 그린 값**의 이름은 범례가 알려 준다
  const basicInfo = {
    ...(handoff?.basicInfo ?? {}),
    ...(variable ? { variable } : {}),
  };

  const onClassCount = (n: number) => {
    setClassCount(n);
    if (!palette) return; // 팔레트 키 없이는 다시 그릴 수 없다 — 억지로 값을 고르지 않는다
    rerender({
      uploadId,
      palette,
      classCount: n,
      withoutReferenceGrid: handoff?.withoutReferenceGrid ?? false,
    });
  };

  /** §7.2 「모달을 다시 열고 등록 단계까지 펼친다」 — 모달은 `P2-fe-upload` 소유라 열쇠만 건넨다. */
  const onRegister = () => {
    navigate(BACK.to, {
      state: { [REGISTER_FROM_PREVIEW_STATE_KEY]: { uploadId, ...(renderId ? { renderId } : {}) } },
    });
  };

  return (
    <div className="preview-page" data-screen="S-08">
      <div className="backrow" data-testid="backrow">
        {/* §8.1 나가기 — 파일을 버리고 목록으로 돌아간다 */}
        <Link className="backlink" to={BACK.to}>
          <span className="bl-a">←</span>
          <span className="bl-n">{BACK.label}</span>
        </Link>
      </div>

      <VolatileNotice onRegister={onRegister} />

      <BasicInfoPanel basicInfo={basicInfo} />

      <section className="pv-preview" aria-label="미리보기">
        <h2 className="pv-h2">미리보기</h2>

        {state.phase === '이어받은 미리보기 없음' ? (
          <p className="pv-muted" data-testid="preview-none">
            이 화면으로 이어진 미리보기가 없어요. 업로드에서 다시 열어 주세요.
          </p>
        ) : null}

        {state.phase === '그리는 중' ? (
          <RenderStageNotice {...(state.stage ? { stage: state.stage } : {})} />
        ) : null}

        {state.phase === '실패' ? <RenderFailureNotice message={state.message} /> : null}

        {state.phase === '그릴 수 없음' ? (
          <NotRenderableNotice message={state.message} renderableFormats={state.renderableFormats} />
        ) : null}

        {state.phase === '만들 수 없음' ? <RenderFailureNotice message={state.message} /> : null}

        {state.phase === '만료됨' ? <ExpiredNotice message={EXPIRED_MESSAGE} /> : null}

        {state.phase === '완료' ? (
          <>
            {/* 부분 실패는 **완료** 안에서 말한다 — 미리보기를 통째로 막지 않는다 (§9) */}
            {state.partialFailure ? <PartialFailureNotice partial={state.partialFailure} /> : null}
            <PreviewMap result={state.result} />
          </>
        ) : null}

        {state.phase === '완료' || state.phase === '그리는 중' ? (
          <PreviewControls
            classCount={classCount}
            onClassCount={onClassCount}
            disabled={state.phase !== '완료'}
          />
        ) : null}
      </section>

      <EmptySlots />
    </div>
  );
}
