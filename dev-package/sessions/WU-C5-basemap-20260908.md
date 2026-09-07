# WU-C5 · 자립형 배경 지도 (레인 `rc-basemap` · 2026-09-08)

## 자산 출처
- Natural Earth 1:110m · GitHub 미러 `nvkelso/natural-earth-vector` **v5.1.2**(릴리스 태그로
  고정 · master `VERSION` 은 `5.2.0-pre`) · `geojson/ne_110m_coastline.geojson` ＋
  `geojson/ne_110m_admin_0_boundary_lines_land.geojson` · **Public Domain** · 2026-09-08.
- 도시·지명 자산 **반입 0**(판정 「도시 표기 없음」) · 지역 자르기 **0**(「다른 지역이 나올 수도 있다」).

## 크기 (실측 · `stat -c %s`)
해안선 139,907 → **96,757 B** · 국경 340,010 → **75,446 B** · 합계 479,917 → **172,203 B
(168.2 KB)**. 상한 500 KB(512,000 B) 대비 **33.6 %** · `du -sh` = 172 K. 시험이 매번 센다.
번들 실측(`vite build`) — `index.js` 493.66 → **662.18 kB**(+168.5 kB · 자산 크기 그대로) ·
gzip 145.96 → **203.23 kB**(+57.3 kB). 상한은 파일 크기 기준이라 판정 안이다.

## 간략화
원본 합계 468.7 KB 도 상한 안이지만 여백이 31 KB 뿐이라 **표현의 군더더기만** 덜었다
(`frontend/scripts/simplify-basemap.mjs`): ⑴ `properties`·`bbox`·`crs` 제거 ⑵ 좌표 소수점
**3자리** 반올림(≈110 m · 1:110m 원본 정밀도보다 곱다) ⑶ 연속 중복 점 제거 ⑷ 한 줄 JSON.
기하 삭제 **0**(feature 수 원본과 같다 · 해안선 134 · 국경 331). 확장자만 `.json`(Vite/TS
기본 JSON import) · 내용은 GeoJSON 그대로.

## 좌표 변환 공유
`preview/projection.ts` 가 **정본 한 자리**다. WU-C4 의 `pvLonOf`/`pvLatOf` 는 그
`lonAtFraction`/`latAtFraction` 을 감싸고, 배경은 같은 함수의 역(`lonFractionOf`/
`latFractionOf`)을 쓴다 — 두 벌이 되면 배경과 래스터가 어긋나고 그 어긋남은 화면에서만
보인다. 시험이 왕복(부산 앞바다 한 점)으로 두 방향을 함께 잰다.

## 배선 · 층 순서
층 묶음(`.pv-layers`) 맨 아래 → 배경 SVG → (C4 외곽선) → 래스터. 세 자리 = 상세
`PreviewPanels.PreviewMap` · 업로드 `upload/PreviewPanel` · 확장보기 오버레이(같은 파일).
`bounds` 없는 결과(②비지도형)에는 자리째 없다. 외부 요청 **0**(정적 import).

## 〈N〉 초안 (번호는 오케스트레이터가 붙인다)
〈N〉 POL-021 「타일 서버도 바탕 지도도 쓰지 않는다」 **부분 반전** — 레포에 반입한
자립형 벡터 배경(Natural Earth 1:110m 해안선＋국경 · 외부 요청 0 · 도시 표기 0)만 허용하고,
**타일 서버·외부 CDN·지도 라이브러리 금지는 그대로 유지**한다. PLAN-SoT ㉴ 「B-2 해안선
오버레이 미채택」도 함께 반전. 근거 = Ted 2026-09-08 「자립형 벡터 해안선 · POL-021 부분
반전」. ⛔ 원문 문단은 지우지 않고 덧붙인다.
