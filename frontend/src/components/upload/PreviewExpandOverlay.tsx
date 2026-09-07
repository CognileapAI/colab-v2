// ㈎ 미리보기 확장보기 오버레이 (R-A′ 이관 · rev2 `pvExpandBack` · PRD-39 ⑭).
//
// 지키는 것
//  - **닫기는 `requestClose` 를 경유한다** — 바깥이 넘긴 그 함수 하나만 부른다. 직접 close 를
//    두면 × 버튼·배경·Esc 의 판정식이 갈리고, 그때 한쪽만 고쳐지는 날이 온다(A9R 규율).
//  - **열려 있는 동안 `data-esc-layer="확장보기"` 표식을 스스로 단다** — 업로드 모달의
//    Esc 처리(`UploadModal` 의 `ESC_LAYER_ATTR` 검사)가 이 층 위에서 Esc 를 삼키지 않는다.
//    층 목록을 모달에 적어 두 벌로 만들지 않는다.
//  - **mousedown 과 click 을 가른다**(A9R `downOnBackdrop` 패턴) — 안쪽에서 눌러 배경에서 뗀
//    드래그(텍스트·지도 끌기)는 click.target 이 배경이 되어 확인 없이 닫히던 자리다.
//  - **Esc 는 이 층이 스스로 받는다**(⟨advisor ② · F2⟩) — 배경·×·Esc 세 갈래가 같은
//    `requestClose` 한 곳으로 모인다. 표식이 떠 있어 업로드 모달은 물러나 있으므로,
//    이 층이 Esc 를 안 받으면 Esc 가 아무 일도 하지 않는다(A9R 규율의 빠진 갈래였다).
//  - **내부 클릭은 무동작이다.**
import { useCallback, useRef, type ReactNode } from 'react';
import { ESC_LAYER_ATTR, useEscLayer } from './escLayer';

export function PreviewExpandOverlay(props: {
  title: string;
  /** 닫기 — **`requestClose` 를 그대로 받는다.** 여기서 다른 경로를 만들지 않는다. */
  requestClose: () => void;
  children: ReactNode;
}) {
  const downOnBackdrop = useRef(false);
  const { requestClose } = props;
  useEscLayer(useCallback(() => requestClose(), [requestClose]));
  return (
    <div
      className="modal-back pvx-back"
      data-testid="pv-expand-overlay"
      {...{ [ESC_LAYER_ATTR]: '확장보기' }}
      onMouseDown={(e) => {
        downOnBackdrop.current = e.target === e.currentTarget;
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && downOnBackdrop.current) props.requestClose();
      }}
    >
      <div
        className="modal pvx"
        role="dialog"
        aria-modal="true"
        aria-label={props.title}
        data-testid="pv-expand-body"
      >
        <div className="modal-h">
          <h3>{props.title}</h3>
          <button
            type="button"
            className="x"
            data-testid="pv-expand-close"
            aria-label="확장보기 닫기"
            onClick={props.requestClose}
          >
            ×
          </button>
        </div>
        <div className="modal-b pvx-b">{props.children}</div>
      </div>
    </div>
  );
}
