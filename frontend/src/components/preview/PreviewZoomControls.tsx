/**
 * **세 화면이 함께 쓰는 확대/축소 줄** (축 ①-⑤a · 판정 축자 「세 화면 공유 `useZoomPan`/`.pv-zoom`」).
 *
 * 상세(`PreviewMap`)·업로드(`PreviewPanel`)·확장보기(`PreviewExpandOverlay`) 셋이 **같은
 * 컴포넌트 하나**를 쓴다 — 마크업이 갈리면 화면마다 다른 조작을 배우게 된다(사용자 스토리 7).
 *
 * ⚠ **문면을 새로 만들지 않는다** — 「확대」·「축소」·「기본 배율로」·「원본 해상도까지 봤어요」는
 *   종전 `PreviewPanels.ZoomControls` 원문 그대로 옮겨 온 것이다(신설 0).
 * ⚠ **한계 판정은 훅이 쥔다**(`zoom.atLimit` · 정본 §8 조건 ⑷) — 여기서 수치를 만들지 않는다.
 * ⭑ ⟨휴대폰·패드 대응 20260926 · V11⟩ **터치 기기에서만** 3단추 줄 바깥 같은 모서리에 「데이터에
 *   맞춤」 단추 하나를 더한다(더블클릭 맞춤의 누름 대안 · 문구 6 확정). 3단추 줄 고정 시험 때문에
 *   줄 안에는 넣지 않고 Fragment 로 나란히 낸다. 마우스 · 판별 불가에서는 지금과 한 글자도 같다.
 */
import type { ZoomPan } from './useZoomPan';
import { useInputMode } from '../common/useInputMode';
import './preview.css';

/** 터치 문구 — 더블클릭 「데이터에 맞춤」의 누름 대안(spec 「새 문구안」 · 확정). */
export const FIT_TO_DATA_LABEL = '데이터에 맞춤';

export function PreviewZoomControls(props: { zoom: ZoomPan; testId?: string }) {
  const { zoom } = props;
  const touch = useInputMode() === 'touch';
  return (
    <>
      {/* 맞춤 단추를 확대 줄 **앞**(모서리 위쪽)에 둔다 — 좁은 지도에서 줄이 지도 가운데까지
          올라가 그림 누름(값 조회)을 받아 버리지 않게 한다. */}
      {touch ? (
        <div className="pv-fit">
          <button type="button" onClick={zoom.fitToData}>
            {FIT_TO_DATA_LABEL}
          </button>
        </div>
      ) : null}
      <div className="pv-zoom" data-testid={props.testId ?? 'preview-zoom'}>
        {/* ⭑ ⟨버그 8⟩ **한계에 닿은 확대는 눌리지 않는다.** 「고장인가」와 「여기가 끝인가」를
            화면이 가려 주지 않던 자리다. 아래 한계 안내와 **같은 사실 하나**를 말한다. */}
        <button type="button" onClick={zoom.zoomIn} disabled={zoom.atLimit} aria-disabled={zoom.atLimit}>
          확대
        </button>
        <button type="button" onClick={zoom.zoomOut}>
          축소
        </button>
        <button type="button" onClick={zoom.reset}>
          기본 배율로
        </button>
        {zoom.atLimit ? (
          <p className="pv-muted" data-testid="zoom-limit" aria-live="polite">
            원본 해상도까지 봤어요
          </p>
        ) : null}
      </div>
    </>
  );
}

/**
 * **「지금 어디를 보고 있는지」 외곽선** (판정 축자 「작은 유역 = 배경 위 bounds 외곽선」).
 *
 * 층 묶음(`.pv-layers`)의 좌표계에서 **데이터 경계는 곧 층 전체**다 — 그래서 사각형은
 * 층을 가득 채우는 상자 하나이고, 이동·배율은 층에 걸린 같은 `transform` 이 함께 옮긴다
 * (정본 §8 조건 ⑸ 「모든 층에 함께」).
 *
 * ⚠ **지도 자산을 여기서 들이지 않는다** — 해안선·국경은 WU-C5 소유다. 이 사각형은
 *   배경 없이도 서고, 배경이 오면 그 위에 그대로 얹힌다.
 */
export function BoundsOutline() {
  return (
    <div
      className="pv-bounds-outline"
      data-testid="preview-bounds-outline"
      aria-hidden="true"
    />
  );
}
