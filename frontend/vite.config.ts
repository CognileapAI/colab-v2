import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// 정적 배포다 (frontend/README). SSR·서버 런타임을 두지 않는다.
export default defineConfig({
  plugins: [react()],
  // 로컬 개발 전용 — staging 에선 nginx 가 같은 오리진의 /api 를 core-api 로 잇는다.
  // dev 서버가 그 자리를 대신한다. 빌드 산출물에는 아무 영향이 없다.
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  build: { outDir: 'dist', sourcemap: true },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
    include: ['test/**/*.test.tsx', 'test/**/*.test.ts'],
  },
});
