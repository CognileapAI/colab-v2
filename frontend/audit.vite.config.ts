import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../.codex/upload-preview-audit',
    emptyOutDir: false,
    assetsInlineLimit: 0,
    rollupOptions: {
      input: {
        upload: 'audit-upload.html',
        design: 'audit-design.html',
        preview: 'design-preview.html',
      },
    },
  },
});
