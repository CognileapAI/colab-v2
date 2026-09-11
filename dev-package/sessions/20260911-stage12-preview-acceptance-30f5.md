# Stage 1·2 U1/F3 최신 dev 30f5 smoke

- 대상: dev 공개 엣지, source `30f5adf6774771c9ca34e2c3a0b92a0648b9cc76`, 번들 `/assets/index-B1MJ4QbM.js`
- 시각: `2026-09-11T09:06:29.669Z` ~ `2026-09-11T09:08:18.160Z`
- 경계: 기존 A headed 세션의 브라우저 컨텍스트에서 실제 API와 S3 바이트를 호출했다. 이전 U1/F3 전체 UI E2E를 대체하지 않고 최신 배포 회귀 smoke로만 판정한다.

## U1

`TEST-stage12-u1-20MiB.nc` 20 MiB를 실제 멀티파트 3개로 접수했다. 첫 조각 PUT 200 뒤 조회한 `uploadedParts`는 `[1]`이었다. 이때 완료는 409였다. 2·3번 조각 PUT 200, 파일 완료 200, 전송 완료 201이었고 완료 응답의 업로드 ID는 `01M27VG19Z8NH79PJ5N698N85K`로 같았다. 완료 크기는 20,971,520 바이트다.

## F3

A 연구실 TEST 데이터셋 `01M27JXV7C2QASRJPJ5VZCS5V9`가 본체 1개뿐임을 먼저 확인했다. 묶음 다운로드는 10,788바이트 ZIP(`PK`)이고 SHA-256은 `29575619b4a465171fa728383e8ff4185cf5c2019a04c1725e7bfeafc45013ef`이다.

이번 시험 파일만 추가 201, 교체 200, 상대 경로 유지, 삭제 204와 목록 부재를 확인했다. 남은 원본 본체 삭제는 409로 거절됐고 이후 목록에도 그대로 남았다. B 연구실 후보 데이터와 기본 격자는 건드리지 않았다.

## 제한과 보존

U1의 완료된 TEST 전송은 유지했다. 서비스·자격증명 재적재 0회, 원본 파일 삭제 0건이다. Authorization과 서명 URL은 기록하지 않았다. 구조화 원값은 `dev-package/reports/stage12-preview-acceptance-30f5/u1-f3-smoke.json`에 있다.
