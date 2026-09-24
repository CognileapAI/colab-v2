// 화면 픽스처(P3) — 인라인 style 은 CSS 변수 대입만(`--` 로 시작하는 키)이면 green 이다.
import type { CSSProperties } from 'react';

export function X({ width, height }: { width: string; height: string }) {
  return (
    <div className="x-page" data-note="style={{ width }} 는 문자열 안이라 세지 않는다">
      <span style={{ '--x-w': width } as CSSProperties} />
      <span style={{ ['--x-h']: height } as CSSProperties} />
    </div>
  );
}
