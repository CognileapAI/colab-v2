import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { App } from './app/App';
// Pretendard 는 npm 패키지의 로컬 webfont 로만 싣는다 — 외부 CDN 에 의존하지 않는다.
// `--font-sans` 첫 자리(`Pretendard Variable`)가 실제로 붙는 자리다.
import 'pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css';
import './shell/shell.css';

const root = document.getElementById('root');
if (!root) throw new Error('#root 가 없다');

createRoot(root).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
