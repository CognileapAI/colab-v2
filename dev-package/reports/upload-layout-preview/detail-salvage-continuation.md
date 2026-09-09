# 상세의 비지도 값 그림 보존 — 2026-09-09

## 원인과 변경

`usePreviewRender`가 200+실패 응답에서 message/code만 남기고 failure.details의 이미 구워진 그림 URL을 버렸다. 상세는 RenderFailureNotice만 표시하여 업로드에서 보던 BIN 값 그림이 등록 후 사라졌다.

- 기존 `upload/previewResult.ts::salvageOf`를 재사용한다. 별도 URL 해석기/새 API/계약/생성 타입을 만들지 않는다.
- 화면 상태 타입 PreviewState의 실패 가지에 기존 Salvage 타입의 값을 보존한다. 추가 타입 파일 없음.
- 상세는 기존 지도 실패 안내와 비지도 값 그림을 함께 표시한다. valuePreviewUrl 우선, 없으면 thumbnailUrl만 사용한다. URL 없으면 img를 만들지 않는다.
- 실패 상태를 완료로 바꾸지 않고, 지도 bounds/사이드카/좌표 HUD/줌/지도 클릭/값조회/지도 스크린샷 조작을 붙이지 않는다.
- 브라우저 이미지 로딩이 끝날 때까지 상태를 표시하고, 이미지 오류 후 같은 URL을 다시 불러오는 버튼을 제공한다. URL 변경 시 이미지 상태가 초기화된다.
- 파일 범위: `frontend/src/components/preview/usePreviewRender.ts`, `frontend/src/components/datasetpreview/DatasetPreviewSection.tsx`, 새 `frontend/test/dataset-preview-salvage.test.tsx`.

## 검증

- 신규3건: 값그림+지도실패 안내·지도조작 없음, 썸네일 단독·이미지오류 재시도, URL없는 실패에서 가짜 img 없음. RED2/기존행위1통과→GREEN3.
- 상세/줌/타일/스크린샷/업로드 격자 관련6파일 **80통과/0실패**. jsdom의 문서 navigation 미구현 안내3줄은 기존 스크린샷 시험에서 출력됐다.
- 타입 포함 최종 `npm run build` 종료0. 기존 큰 bundle 경고1건은 남음.
- 변경 전 사본 JSON stdin Edit/Write guard3종 실행. CSS 변경 없음.
- 실제 BIN 상세 브라우저 검증은 부모 통합 환경에서 수행한다. 합성 응답 회귀만으로 실제 이미지 표시 성공을 선언하지 않는다.

## 인계

- 표식 `dt-preview-salvage`, 이미지 `dt-preview-salvage-image`.
- 이미지 alt: 실제 값 그림 `데이터 값 미리보기`, 썸네일만 있을 때 `데이터 썸네일`.
- 이미지 오류 복구 버튼 `그림 다시 불러오기`.
- 미달: 부모의 실제 데이터 저장·상세·이미지 로드 검증 미실행. 초과0.
