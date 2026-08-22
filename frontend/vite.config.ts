import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// 정적 배포다 (frontend/README). SSR·서버 런타임을 두지 않는다.
export default defineConfig({
  plugins: [react()],
  build: { outDir: 'dist', sourcemap: true },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
    include: ['test/**/*.test.tsx', 'test/**/*.test.ts'],
  },
});
