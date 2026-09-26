/**
 * **누르면 보이는 설명** (spec S-DEVICE-WIDTH-INPUT-20260926 V9 · 부록 C · 「레인 확정」 L3a 제약).
 *
 * 터치 기기에는 마우스 올림이 없어 `title` 에만 있던 설명이 보이지 않는다. 터치일 때만 부르는 쪽이
 * 짧은 라벨을 이 부품으로 감싼다 — 라벨이 설명 단추가 되고, 누르면 같은 자리 바로 뒤에 설명 글이 펼쳐진다
 * (우려 10ⓐ · 새 팝오버 0 · 펼침은 즉시). 마우스(판별 불가 포함)는 부르는 쪽이 원래 요소와 `title` 을 그대로 둔다.
 * - 단추: `type=button` · `aria-expanded` · `aria-controls` → 펼침 글 `id`. Enter · Space 는 단추 기본 동작이다.
 * - 누름은 행 전체 이동(표 행 `onClick`)으로 전달되지 않는다(`stopPropagation`).
 * - `as="node"` 는 계보 그래프 노드 자리다 — 상자 모양을 그대로 두고 누르는 역할(`role=button` · `tabIndex=0` ·
 *   Enter · Space)만 더한다. 글자 · 모양은 기존 보조 글자 토큰을 쓴다(`touchNote.css`).
 */
import { useId, useState, type KeyboardEvent, type MouseEvent, type ReactElement, type ReactNode } from 'react';
import './touchNote.css';

type DataAttrs = { [key: `data-${string}`]: string | undefined };

export function TouchNote(props: {
  /** 펼쳐 보일 설명 글(「새 문구안」 확정 문구 원문). */
  note: string;
  children: ReactNode;
  /** `node` = 계보 그래프 노드 상자(누르는 역할만 더함). 기본은 투명한 설명 단추. */
  as?: 'button' | 'node';
  className?: string;
  attrs?: DataAttrs;
}) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const toggle = (event: MouseEvent) => {
    event.stopPropagation();
    setOpen((v) => !v);
  };
  const trigger =
    props.as === 'node' ? (
      <div
        {...props.attrs}
        className={['touch-note-trigger', props.className].filter(Boolean).join(' ')}
        role="button"
        tabIndex={0}
        aria-expanded={open}
        aria-controls={id}
        onClick={toggle}
        onKeyDown={(event: KeyboardEvent) => {
          if (event.key !== 'Enter' && event.key !== ' ') return;
          event.preventDefault();
          event.stopPropagation();
          setOpen((v) => !v);
        }}
      >
        {props.children}
      </div>
    ) : (
      <button
        {...props.attrs}
        type="button"
        className={['touch-note-trigger touch-note-btn', props.className].filter(Boolean).join(' ')}
        aria-expanded={open}
        aria-controls={id}
        onClick={toggle}
      >
        {props.children}
      </button>
    );
  return (
    <>
      {trigger}
      <span id={id} className="touch-note-text" hidden={!open}>
        {props.note}
      </span>
    </>
  );
}

/**
 * 부르는 자리의 갈래 — 터치면 라벨을 설명 단추로 감싸고, 마우스(판별 불가 포함)거나 설명이 없으면 라벨을
 * 그대로 돌려준다(마우스 화면의 요소 · 배치 변화 0). 라벨의 `title` 은 부르는 쪽이 마우스일 때만 단다.
 */
export function TouchOrMouse(props: { mouse: boolean; note: string | undefined; children: ReactElement }) {
  return props.mouse || !props.note ? props.children : <TouchNote note={props.note}>{props.children}</TouchNote>;
}
