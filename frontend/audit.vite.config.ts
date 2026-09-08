import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../.codex/upload-preview-audit',
    emptyOutDir: false,
    rollupOptions: { input: fileURLToPath(new URL('./audit-upload.html', import.meta.url)) },
  },
});
