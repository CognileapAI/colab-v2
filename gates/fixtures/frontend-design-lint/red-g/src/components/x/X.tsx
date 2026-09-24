// 화면 픽스처(P3) — 인라인 g: 색 · px · 축약형은 red, 변수 대입만인 것은 세지 않는다(v).
import type { CSSProperties } from 'react';

export function X({ width, color }: { width: string; color: string }) {
  return (
    <div className="x-page">
      <span style={{ background: color }} />
      <span style={{ marginTop: 16 }} />
      <span style={{ width }} />
      <span style={{ '--x-w': width } as CSSProperties} />
    </div>
  );
}
