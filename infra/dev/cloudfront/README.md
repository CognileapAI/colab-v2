# CloudFront — dev 배포 1개 · 오리진 3 · 동작 3 (`PLAN-SoT §9 〈178〉-㉮`)

도메인 없이 기본 주소(`https://<id>.cloudfront.net`)로 HTTPS 를 얻는다. HTTPS 가 없으면 브라우저의
`crypto.subtle`·디렉터리 선택이 보안 컨텍스트 밖이라 이어올리기가 조용히 죽는다.

| 동작(경로) | 오리진 | 캐시 · 전달 | 함수 |
|---|---|---|---|
| 기본 `*` | **A** 웹 버킷 `colab-platform-web-dev` (OAC) | 캐시 켬 · `assets/*` 는 객체의 `Cache-Control: immutable`, `index.html` 은 `no-cache`(`deploy_web.py` 가 헤더를 준다) | `spa-rewrite.js` viewer-request |
| `/api/*` | **B** EC2 탄력적 IP `:8000` HTTP | **캐시 끔** · 모든 헤더·쿠키·쿼리 전달 · 전 메서드 허용 · 응답 타임아웃 60 s | 없음 |
| `/previews/*` | **C** 데이터 버킷 `colab-platform-data-dev` (OAC, `previews/*` 만 허용 — `iam/bucket-policy-data.json`) | 캐시 켬(객체 `max-age=300`) | 없음 |

- HTTP → HTTPS 리디렉션. 사용자 지정 오류 응답은 **쓰지 않는다**(SPA 폴백은 함수).
- 배포가 생기면 `<DISTRIBUTION_ARN>`·`<DISTRIBUTION_DOMAIN>` 을 `iam/bucket-policy-*.json`·`iam/cors-data.json` 에 채워 붙여넣는다.
- 판정 = `deploy_doctor` 진입·라우팅 항목: `GET /` 200 html · `GET /api/v1/me` **401 JSON**(HTML 200 이면 SPA 로 샜다) · `GET /previews/__probe` 비-HTML.
