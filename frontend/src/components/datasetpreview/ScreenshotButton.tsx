// S-05 데이터셋 상세 — **스크린샷** 컨트롤 (WU-P3 · 화면 레인).
//
// 정본 `Policy_데이터셋_상세` v2.5.
//  · `§8` 스크린샷 행 「지금 장면을 PNG로 저장. **설정을 저장하지 않으므로 남길 장면은 여기서
//    뽑는다.** **확대한 자리와 배율도 "지금 장면"에 포함된다」
//  · `§6`  `업로드·편집` 켜짐 = 시각화 편집·**스크린샷**·계보 수정 → **편집 권한자 컨트롤이다**
//  · `§3.2` 보기 전용에는 이 컨트롤이 **자리째 없다** — 비활성 버튼을 두지 않는다(P-12).
//
// **그리는 일은 한 줄도 하지 않는다** — 층과 보고 있는 자리를 중계 op 에 넘기고 받은 PNG 를
// 그대로 내려 준다. 화면이 캔버스로 다시 그리면 서버가 그린 그림과 다른 것이 저장된다.
import { useState } from 'react';
import { PermissionGate } from '../../permission/PermissionGate';
import type { ZoomPan } from '../preview/useZoomPan';
import { UNAVAILABLE_MESSAGE } from './datasetPreviewSource';
import type { DatasetPreviewSource, ScreenshotRequest } from './types';
import type { RenderResult } from '../preview/types';

/** 소수점 이하를 끝없이 늘리지 않는다. 경계는 WGS84 경위도이고 6자리면 미터 아래다. */
function round6(v: number): number {
  return Math.round(v * 1e6) / 1e6;
}

/**
 * 지금 보고 있는 자리의 경계. **그림 전체 경계 안에서 확대·이동한 만큼만 잘라 낸다** —
 * 없는 자리를 만들어 내지 않는다. 배율 1 · 이동 0 이면 결과의 경계 그대로다.
 */
export function visibleBounds(
  bounds: { west: number; south: number; east: number; north: number },
  f: { x0: number; y0: number; x1: number; y1: number },
) {
  const lon = bounds.east - bounds.west;
  const lat = bounds.north - bounds.south;
  return {
    west: round6(bounds.west + lon * f.x0),
    east: round6(bounds.west + lon * f.x1),
    north: round6(bounds.north - lat * f.y0),
    south: round6(bounds.north - lat * f.y1),
  };
}

export function ScreenshotButton(props: {
  source: DatasetPreviewSource;
  renderId: string;
  result: RenderResult;
  zoom: ZoomPan;
}) {
  const [failure, setFailure] = useState<string | null>(null);
  const { result, zoom } = props;
  const bounds = result.bounds;
  const size = zoom.viewportSize();

  // **계약이 요구하는 값이 없으면 버튼을 세우지 않는다** — `ScreenshotRequest.viewport` 는
  // 경계가 필수이고, ②비지도형 결과에는 경계가 없는 것이 정상이다(`〈85〉`).
  // 갈 곳 없는 버튼도, 지어낸 좌표도 만들지 않는다.
  if (!bounds) return null;

  async function take() {
    if (!bounds) return;
    setFailure(null);
    const viewport = size ?? { width: 1024, height: 1024 };
    const request: ScreenshotRequest = {
      // 이 데이터 층 하나다. 겹쳐 보기는 이 구역이 아직 짓지 않았다 — 맨 아래 층은 불투명도 1.
      layers: [{ renderId: props.renderId, opacity: 1 }],
      viewport: {
        width: viewport.width,
        height: viewport.height,
        bounds: visibleBounds(bounds, zoom.visibleFraction()),
      },
    };
    try {
      const png = await props.source.screenshot(request);
      const url = URL.createObjectURL(png);
      const a = document.createElement('a');
      a.href = url;
      a.download = `preview-${props.renderId}.png`;
      // **문서에 붙여 놓고 누른다** — 떠 있는 앵커는 브라우저에 따라 클릭이 먹지 않는다.
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      // **같은 tick 에서 거두지 않는다** — 크롬은 클릭이 돌아온 뒤 별도 태스크에서 `blob:` 을
      // 읽는다. 그 전에 `revokeObjectURL` 을 부르면 자리가 사라져 내려받기가 **취소**된다.
      // 그렇다고 흘려 두지도 않는다 — 다음 태스크에서 앵커와 함께 거둔다.
      setTimeout(() => {
        a.remove();
        URL.revokeObjectURL(url);
      }, 0);
    } catch (e) {
      setFailure(e instanceof Error && e.message ? e.message : UNAVAILABLE_MESSAGE);
    }
  }

  return (
    <PermissionGate requires="업로드·편집">
      <div className="pv-shot">
        <button type="button" onClick={() => void take()}>
          스크린샷
        </button>
        {failure ? (
          <p className="pv-failure" data-testid="screenshot-failure" aria-live="assertive" role="alert">
            {failure}
          </p>
        ) : null}
      </div>
    </PermissionGate>
  );
}
