# 로컬 화면 검수

`frontend`에서 `npm ci`, `npm run audit:build`, `npm run audit:preview -- --port 4187` 순서로 실행한다.
빌드 설정은 `audit.vite.config.ts` 하나이며 결과는 `.codex/upload-preview-audit`에 생성된다.

- `/design-preview.html`: 대표 화면·테마·너비 선택. 화면은 `/audit-design.html?design=calm&theme=dark&scene=catalog` 꼴(GNB 없는 화면)로 연다
- `/audit-design.html?design=full&theme=dark&scene=catalog`: 현재 공통 스타일의 모의 화면
- `/audit-design.html?design=full&scene=preview-done`: 로컬 예시 지도
- `/audit-design.html?design=full&scene=primitives`(`&theme=dark`): 프리미티브 갤러리 — `primitives.css` 6계열(btn · field · chip · card · table · modal)의 기본 · 수식자 · disabled 정적 상태. 제품 컴포넌트를 쓰지 않는다(`docs/design-system.md` ③·⑧)
- `/audit-upload.html?theme=dark`: 모의 업로드 화면

검수 화면은 모의 응답을 사용하며 저장 API를 호출하지 않는다. 실제 저장·조회 E2E를 대신하지 않는다.
검수용 코드와 정적 예시 이미지는 일반 제품 빌드 진입점에서 분리돼 있다.
