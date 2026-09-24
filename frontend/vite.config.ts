import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

declare const process: { env: Record<string, string | undefined> };

// P2a — jsdom 29 는 `@layer` 블록 안 규칙을 계산값에 넣지 않는다(파싱은 한다). test 모드에서만 stylesheet 로
// 실리는 CSS 의 `@layer a, b;` 문장을 지우고 `@layer x {` 껍질과 짝 `}` 만 벗긴다(내용·중첩 @media 그대로).
// `?raw` 원문과 제품 빌드는 건드리지 않는다. 그래서 vitest 는 층 순서를 검증하지 못한다 — 증거는 실브라우저 캡처.
export function stripLayerBlocks(css: string): string {
  let out = '';
  const shells: boolean[] = [];
  const upTo = (j: number, len: number) => (j < 0 ? css.length : j + len);
  for (let i = 0; i < css.length; ) {
    const skip = css.startsWith('/*', i) ? upTo(css.indexOf('*/', i + 2), 2)
      : css[i] === '"' || css[i] === "'" ? upTo(css.indexOf(css[i] as string, i + 1), 1) : 0;
    if (skip) { out += css.slice(i, skip); i = skip; continue; }
    const layer = /^@layer\b[^;{]*([;{])/.exec(css.slice(i, i + 256));
    if (layer) { if (layer[1] === '{') shells.push(true); i += layer[0].length; continue; }
    if (css[i] === '{') shells.push(false);
    if (css[i] === '}' && shells.pop()) { i++; continue; }
    out += css[i++];
  }
  return out;
}

// 정적 배포다 (frontend/README). SSR·서버 런타임을 두지 않는다.
export default defineConfig({
  plugins: [
    react(),
    { name: 'colab-test-layer-shim', enforce: 'pre', apply: (_config, env) => env.mode === 'test',
      transform: (code, id) => (/\.css($|\?)/.test(id) && !/[?&]raw\b/.test(id) ? stripLayerBlocks(code) : undefined) },
  ],
  // 로컬 개발 전용 프록시(PR #1) — staging 에선 nginx 가 같은 오리진의 /api 를 core-api 로 잇는다.
  // dev 서버가 그 자리를 대신한다. 빌드 산출물에는 아무 영향이 없다.
  server: {
    proxy: { '/api': `http://127.0.0.1:${process.env.COLAB_E2E_CORE_PORT ?? '8000'}` },
  },
  build: { outDir: 'dist', sourcemap: true },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
    include: ['test/**/*.test.tsx', 'test/**/*.test.ts'],
    // 카탈로그 헤더 고정·취소선을 **계산값**으로 재려면 그 규칙 파일이 실제로 실려야 한다.
    // vitest 기본값은 css 를 빈 것으로 stub 한다 — 그래서 종전 회차가 `[미확인]` 로 남겼다.
    // 버그 1·2·9 (레인 C) — 프로젝트 화면 뿌리 여백·상세 카드 면·GNB 아이콘 간격도 같은 이유로
    // 계산값이 필요해 project.css·shell.css 를 더한다. jsdom 이 못 재는 `var()` 배경·`gap` 은
    // 규칙 원문(`?raw`)으로 잰다 — 이 스텁은 `?raw` id 까지 빈 문자열로 만들므로 함께 허용한다.
    // (`node:fs` 는 쓰지 않는다 — `e01-apply-points.test.ts:14` 의 배포 불가 사고.)
    css: {
      include: [
        /catalog\.css(\?raw)?$/,
        /project\.css(\?raw)?$/,
        /shell\.css(\?raw)?$/,
        /tokens\.css(\?raw)?$/,
        // P2a — 층 순서 선언(styles.ts 첫 import). 위 껍질 제거 플러그인이 문장을 지우므로 계산값엔 영향 없다.
        /layers\.css(\?raw)?$/,
        // P2b — 원소 기본(`@layer base`)과 프리미티브(`@layer primitives`) — 옮긴 규칙이 계산값에 계속 실린다.
        /base\.css(\?raw)?$/,
        /primitives\.css(\?raw)?$/,
        /detail\.css\?raw$/,
        /dashboard\.css(\?raw)?$/,
        /search\.css(\?raw)?$/,
        // WU-A4 · PRD-28 — 등록 화면 2:3 과 짧은 값 3칸은 **선언**으로만 잴 수 있다
        // (jsdom 에 레이아웃 엔진이 없다). 규칙 원문을 `?raw` 로 읽는다.
        /upload\.css\?raw$/,
      ],
    },
  },
});
