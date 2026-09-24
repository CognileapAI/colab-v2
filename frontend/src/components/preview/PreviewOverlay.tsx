/**
 * **도구 층** — 뷰포트 위에 고정되는 조작 한 겹 (`intent/2026-09-18-issue-120-preview-map-viewport.md`).
 *
 * 요구는 하나다 — **그림을 아무리 옮기고 키워도 도구의 화면 위치와 크기는 변하지 않는다.**
 * 종전에는 확대 줄·스크린샷·값 조회·커서 HUD 가 뷰포트의 **뒤 형제**로 문서 흐름에 쌓이고
 * 범례가 지도 행의 오른쪽 열이라, 4:3 틀 안쪽 스크롤 영역(`.pv-frame-in`)에 그림과 함께
 * 실려 같이 움직였다.
 *
 * 3층 구조를 지킨다 — 뷰포트(`position: relative` · `overflow: hidden`) / 층 묶음
 * (`.pv-layers` · **변환은 여기 하나**) / 도구 층(뷰포트의 **직계 자식이자 층 묶음의 형제**).
 * ⚠ **도구를 층 묶음 안에 넣지 않는다** — 넣는 순간 정본 §8 조건 ⑵(확대해도 범례가 바뀌지
 *   않는다)가 깨지고 도구가 그림과 함께 확대된다.
 * ⚠ **배치 규칙은 이 부품 한 곳에만 산다** — 네 화면(상세 · 업로드 인라인 · 확장보기 ·
 *   등록 전 미리보기)이 같은 JSX 순서를 복제하지 않는다(`PreviewSlot` 의 존치 규칙과 같은 원칙).
 * ⚠ **문면을 만들지 않는다** — 이 파일에 한국어 화면 글자는 없다. 버튼 이름·HUD·값 조회·
 *   범례 문구는 호출부가 이미 갖고 있는 정본 문면 그대로다.
 */
import type { MouseEvent, ReactNode } from 'react';
import './preview.css';

export interface PreviewOverlayProps {
  /** 우상단 — 범례. */
  topRight?: ReactNode;
  /** 우하단 — 확대·축소·기본 배율·스크린샷. */
  bottomRight?: ReactNode;
  /** 좌하단 — 커서 위경도 표시와 값 조회 패널. */
  bottomLeft?: ReactNode;
  testId?: string;
}

/**
 * **도구 층이 뷰포트 안으로 들어가면 버튼 클릭이 그림의 조작으로 샌다.**
 * 뷰포트는 `onClick`(값 조회) · `onPointerDown`(드래그 시작) · `onDoubleClick`(데이터 맞춤)을
 * 들고 있어서, 확대 버튼을 누르면 그 자리의 값을 조회하는 결함이 새로 생긴다. 규칙을
 * **부품 한 곳**에 둔다 — 뷰포트 핸들러 넷에 같은 target 검사를 흩지 않는다(우려 2 ⓐ).
 *
 * ⚠ 휠은 여기서 막지 못한다 — 훅이 뷰포트 노드에 **네이티브** 리스너로 걸어(검수 #24 ·
 *   `{ passive: false }`) React 의 `stopPropagation` 이 닿지 않는다. 그 갈래는 훅의 휠
 *   핸들러가 `event.target` 이 `.pv-overlay` 안이면 무시하는 것으로 막는다.
 */
function stop(e: MouseEvent<HTMLDivElement>) {
  e.stopPropagation();
}

export function PreviewOverlay(props: PreviewOverlayProps) {
  return (
    <div
      className="pv-overlay"
      data-testid={props.testId ?? 'preview-overlay'}
      onClick={stop}
      onPointerDown={stop}
      onDoubleClick={stop}
    >
      {/* 모서리 묶음은 **여백과 간격을 소유한다** — 도구 요소는 margin 을 지지 않는다.
          컨테이너의 `pointer-events: none` 덕에 빈 자리는 그림에 그대로 닿는다. */}
      {props.topRight ? <div className="pv-overlay-tr">{props.topRight}</div> : null}
      {props.bottomRight ? <div className="pv-overlay-br">{props.bottomRight}</div> : null}
      {props.bottomLeft ? <div className="pv-overlay-bl">{props.bottomLeft}</div> : null}
    </div>
  );
}
