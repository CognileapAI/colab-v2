// GNB 「더보기」 — 좁은 폭에서 상단 기능의 **이름을 글자로** 되돌리는 자리.
//
// 왜 생겼나 (이태헌 1차 검증 `I-9` · 카드 ③ ⓒ):
//   반응형 사다리는 좁아질수록 라벨부터 접고 아이콘만 남긴다(`shell.css` 「GNB 반응형 사다리」).
//   그 결과 390px 에서 업로드·계정 관리·연구실 설정이 **그림으로만** 남아, 처음 보는 사람이
//   무엇인지 알 수 없었다. 목록 안에서는 그림과 이름을 함께 낸다.
//
// 담는 것 = **기능 진입 셋**뿐이다. 아바타(내 계정) 메뉴는 카드 ② 판정대로 만들지 않는다.
// 항목이 하나도 없으면 이 부품을 세우지 않는다 — 여는 것이 비어 있는 자리를 새로 만들지 않는다.
import { useCallback, useRef, useState, type ReactNode } from 'react';

export function GnbMoreMenu(props: {
  /** 목록 항목. `close` 는 **화면을 옮기는 항목**만 부른다(아래 주석 참조). */
  children: (close: () => void) => ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // 닫을 때 초점을 「더보기」로 돌려준다 — 키보드만 쓰는 사람이 문서 처음으로 튕기지 않게.
  const close = useCallback(() => {
    triggerRef.current?.focus();
    setOpen(false);
  }, []);

  return (
    <div
      className="gnb-more-wrap"
      onKeyDown={(e) => {
        if (e.key !== 'Escape' || !open) return;
        e.stopPropagation();
        close();
      }}
    >
      <button
        ref={triggerRef}
        type="button"
        className="gnb-more"
        data-testid="gnb-more"
        aria-label="더보기"
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {/* 인라인 SVG 만 쓴다 — 아이콘 라이브러리를 들이지 않는다(`Gnb.tsx` 와 같은 규율). */}
        <svg
          className="ico"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="5" cy="12" r="1.4" />
          <circle cx="12" cy="12" r="1.4" />
          <circle cx="19" cy="12" r="1.4" />
        </svg>
      </button>
      {open ? (
        <div className="gnb-more-list" data-testid="gnb-more-list">
          {/* ⚠ **업로드 항목은 이 목록을 닫지 않는다.** 모달의 열림 상태는 `UploadEntry` 안에
              있고, 목록을 닫으면 그 컴포넌트가 언마운트되어 모달이 열리자마자 사라진다.
              업로드 모달은 전체 화면(`position: fixed`)이라 목록을 가리고, 모달을 닫으면
              누르던 자리로 돌아온다. 화면을 옮기는 두 항목만 `close` 를 부른다. */}
          {props.children(close)}
        </div>
      ) : null}
    </div>
  );
}
