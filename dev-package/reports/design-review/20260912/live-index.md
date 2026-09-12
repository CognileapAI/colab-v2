# 실제 화면 확인 범위

대상: 기존 검수용 로그인 프로필이 가리키는 개발 서비스 https://d31zgpff2091oh.cloudfront.net. 사용자에게 별도 주소를 문의했고 회신 전 기존 개발 환경을 사용했다. 소스맵에 포함된 TS/TSX 158/158 내용이 현재 작업 사본과 같음을 대조했다. 서버 Git SHA를 검증했다는 의미는 아니다.

수동 캡처 37회 중 의도한 화면에 도달한 증거 35회. 상세 진입 실패로 카탈로그에 남은 2회는 제외했다. 별도 공식 게이트는 4개 URL × light/dark 스크린샷 8장이다.

| 캡처 | 화면/실제 상태 | 폭 | 문서 scrollWidth | <13px 원시 요소 | 대비<4.5 원시 요소 | 이미지 |
|---|---|---:|---:|---:|---:|---|
| lab-desktop | S-01 | 1440 | 1440 | 21 | 0 | [화면](live/lab-desktop.png) |
| lab-mobile | S-01 | 375 | 375 | 21 | 0 | [화면](live/lab-mobile.png) |
| catalog-desktop | S-03 | 1440 | 1440 | 60 | 20 | [화면](live/catalog-desktop.png) |
| catalog-mobile | S-03 | 375 | 375 | 60 | 20 | [화면](live/catalog-mobile.png) |
| projects-desktop | S-02 | 1440 | 1440 | 6 | 3 | [화면](live/projects-desktop.png) |
| projects-mobile | S-02 | 375 | 375 | 6 | 3 | [화면](live/projects-mobile.png) |
| project-create-mobile | S-02 | 375 | 375 | 15 | 6 | [화면](live/project-create-mobile.png) |
| project-create-desktop | S-02 | 1440 | 1440 | 15 | 6 | [화면](live/project-create-desktop.png) |
| projects-table-desktop | S-02 | 1440 | 1440 | 1 | 0 | [화면](live/projects-table-desktop.png) |
| project-detail-desktop | S-02b | 1440 | 1440 | 3 | 0 | [화면](live/project-detail-desktop.png) |
| project-detail-mobile | S-02b | 375 | 375 | 3 | 0 | [화면](live/project-detail-mobile.png) |
| settings-desktop | S-07 | 1440 | 1440 | 8 | 0 | [화면](live/settings-desktop.png) |
| settings-mobile | S-07 | 375 | 375 | 8 | 0 | [화면](live/settings-mobile.png) |
| members-mobile | S-07 · 탭 진입만/권한표 미표시 | 375 | 375 | 0 | 0 | [화면](live/members-mobile.png) |
| members-desktop | S-07 · 탭 진입만/권한표 미표시 | 1440 | 1440 | 0 | 0 | [화면](live/members-desktop.png) |
| lab-info-desktop | S-01 | 1440 | 1440 | 29 | 0 | [화면](live/lab-info-desktop.png) |
| lab-info-mobile | S-01 | 375 | 375 | 29 | 0 | [화면](live/lab-info-mobile.png) |
| upload-empty-desktop | S-01 | 1440 | 1440 | 21 | 0 | [화면](live/upload-empty-desktop.png) |
| upload-empty-mobile | S-01 | 375 | 375 | 21 | 0 | [화면](live/upload-empty-mobile.png) |
| dataset-detail-desktop | 대상 도달 실패: 실제 카탈로그 | 1440 | 1425 | 60 | 20 | [화면](live/dataset-detail-desktop.png) |
| dataset-detail-mobile | 대상 도달 실패: 실제 카탈로그 | 375 | 375 | 60 | 20 | [화면](live/dataset-detail-mobile.png) |
| dataset-detail-verified-desktop | S-05 | 1440 | 1440 | 0 | 0 | [화면](live/dataset-detail-verified-desktop.png) |
| dataset-detail-verified-mobile | S-05 | 375 | 382 | 0 | 0 | [화면](live/dataset-detail-verified-mobile.png) |
| dataset-edit-mobile | S-05 | 375 | 382 | 0 | 0 | [화면](live/dataset-edit-mobile.png) |
| dataset-edit-desktop | S-05 | 1440 | 1440 | 0 | 0 | [화면](live/dataset-edit-desktop.png) |
| lineage-editor-desktop | S-05 | 1440 | 1440 | 0 | 0 | [화면](live/lineage-editor-desktop.png) |
| lineage-editor-mobile | S-05 | 375 | 382 | 0 | 0 | [화면](live/lineage-editor-mobile.png) |
| login-desktop | 로그인 | 1440 | 1440 | 0 | 0 | [화면](live/login-desktop.png) |
| login-mobile | 로그인 | 375 | 384 | 0 | 0 | [화면](live/login-mobile.png) |
| search-desktop | S-06 | 1440 | 1440 | 22 | 0 | [화면](live/search-desktop.png) |
| search-mobile | S-06 | 375 | 375 | 22 | 0 | [화면](live/search-mobile.png) |
| notfound-desktop | not-found | 1440 | 1440 | 0 | 0 | [화면](live/notfound-desktop.png) |
| notfound-mobile | not-found | 375 | 375 | 0 | 0 | [화면](live/notfound-mobile.png) |
| preview-expired-desktop | S-08 · 이어받은 미리보기 없음(만료 아님) | 1440 | 1440 | 0 | 3 | [화면](live/preview-expired-desktop.png) |
| preview-expired-mobile | S-08 · 이어받은 미리보기 없음(만료 아님) | 375 | 375 | 0 | 3 | [화면](live/preview-expired-mobile.png) |
| catalog-filtered-desktop | S-03 | 1440 | 1440 | 16 | 4 | [화면](live/catalog-filtered-desktop.png) |
| catalog-filtered-mobile | S-03 | 375 | 375 | 16 | 4 | [화면](live/catalog-filtered-mobile.png) |

## 데이터/상태 경계

- 저장·삭제·등록·승인·업로드 제출·권한 변경 조작0. 화면 진입과 modal 열기/닫기, tab/filter/view 변경을 수행했다. 앱이 조회 시 남기는 최근 열어봄 브라우저 기록과 로그인 세션은 발생한다.
- 상세 화면은 진입 시 DatasetPreviewSection.tsx:143 및 datasetPreviewSource.ts:93에서 자동 POST /previews를 요청한다. 따라서 백엔드 요청 전체가 읽기 전용이거나 새 렌더0이었다고 주장하지 않는다. 서버의 캐시 재사용/새 렌더 작업 수는 미계측이다.
- 모든 화면을 매번 실제 URL/data-screen과 대조했다. 멤버 탭 빈 본문은 멤버 UI 합격이 아니다.
- 업로드 초기 상태는 파일을 고르지 않고 확인. 기존 HDF5 상세의 preview를 읽었고 팔레트/구간 변경으로 렌더 요청하지 않았다.
- preview-expired라는 파일명의 두 캡처는 실제로 이어받은 정보 없음 상태이다. 실제 TTL 만료 상태 검증으로 재사용하지 않는다.
- live_probe는 배경 overlay 뒤 요소와 표 내부 가로스크롤 요소도 수집한다. 여러 상태·폭의 원시 수를 합산해 독립 결함 수로 보고하지 않는다.
- light/dark media는 공식 게이트에서 측정. reduce=true에서도 셸 transition이 남는 값은 reduced-motion.json.
- 375px 기본 폭과 1440px 데스크톱을 확인했다. 768px·200% 확대·실제 iOS Safari·모든 긴 문자열과 권한별 상태는 미측정이다.

## 공식 frontend-visual 게이트

4 URL(lab/datasets/projects/lab-settings), 실제 exit1. green0 / red(판정)1 / red(준비)0. 13px 미만95회 / 대비4.5 미만23회 / 스크린샷8장 / 허용 접두사0. 독립 결함 수가 아니라 4페이지의 반복 요소 포함 관측이다. 게이트 기준을 완화하거나 허용 목록을 늘리지 않았다.
근거: gate/gate-summary.json, gate/frontend-visual/index.md. 관련 검사는 이번 감사의 결함을 확인한 것이며 제품 수정 검증 성공이 아니다.

## 검사 준비/실행 오류와 처리

- 정적 감사 첫 실행은 출력 폴더가 없어 실패. 폴더 생성 후 정상 재실행했다.
- 로그인 캡처 기록기가 data-screen 없는 페이지를 처리하지 못해 실패. 감사 도구의 optional field 처리를 고쳐 재실행했다. 제품 코드는 바꾸지 않았다.
- 처음 상세 행 클릭은 모바일 넓은 표의 클릭 위치 때문에 카탈로그에 남았다. 두 캡처를 실패로 보존하고 데스크톱의 이름 셀 클릭 후 S-05 도달을 확인해 다시 측정했다.
- 검색 URL의 셸 특수문자와 지원하지 않는 focus subaction은 실제 페이지 변경 전에 실패. 올바른 인자/CLI focus 명령으로 재실행했다.
