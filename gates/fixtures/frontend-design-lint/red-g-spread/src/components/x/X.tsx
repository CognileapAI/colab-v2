// 화면 픽스처(P3) — 펼침 속성 안의 `style` 키도 g 로 판정한다: 비변수 키는 red, 변수 대입만은 v.
import type { CSSProperties } from 'react';

export function X({ on, x }: { on: boolean; x: number }) {
  return (
    <div className="x-page">
      <div {...(on ? { 'data-on': 'true', style: { transform: `translate(${x}px, 0)` } } : {})} />
      <div {...(on ? { style: { '--x-shift': `${x}px` } as CSSProperties } : {})} />
    </div>
  );
}
