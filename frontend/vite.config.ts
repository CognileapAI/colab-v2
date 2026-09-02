import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// 정적 배포다 (frontend/README). SSR·서버 런타임을 두지 않는다.
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // 시험 회차에서만 레포 안 문서 자리를 읽기 허용한다. `?raw` 는 vite 의 `server.fs.allow`
  // 밖 파일을 **Denied ID** 로 거절한다 — E-01 적용 지점 시험이 초안 md 를 읽어야 하는데
  // 그 자리가 frontend/ 밖이라 거절됐다. 개발 서버(mode !== 'test')는 넓히지 않는다.
  server: mode === 'test' ? { fs: { allow: ['.', '../dev-package/sessions'] } } : {},
  build: { outDir: 'dist', sourcemap: true },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
    include: ['test/**/*.test.tsx', 'test/**/*.test.ts'],
    // 카탈로그 헤더 고정·취소선을 **계산값**으로 재려면 그 규칙 파일이 실제로 실려야 한다.
    // vitest 기본값은 css 를 빈 것으로 stub 한다 — 그래서 종전 회차가 `[미확인]` 로 남겼다.
    // 이 파일 하나만 싣는다(전역 확장 아님).
    css: { include: [/catalog\.css$/] },
  },
}));
