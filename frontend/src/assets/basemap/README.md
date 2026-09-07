# 배경 지도 자산 — Natural Earth 1:110m (WU-C5 · 축 ①-⑤b)

미리보기 배경(`components/preview/BasemapLayer.tsx`)이 **정적 import** 로 읽는 벡터 두 장.
런타임에 나가는 요청은 없다 — 타일 서버 0 · 외부 CDN 0 · 지도 라이브러리 0
(POL-021 **부분 반전**: 레포 안에 든 벡터 배경만 허용 · 외부 요청 금지는 유지).

## 출처

| 항목 | 값 |
|---|---|
| 원본 | Natural Earth — `nvkelso/natural-earth-vector` (GitHub 미러) |
| 버전 | **v5.1.2** (릴리스 태그 · 저장소 `VERSION` 은 master 기준 `5.2.0-pre`) |
| 원본 주소 | `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_110m_coastline.geojson`<br>`https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_110m_admin_0_boundary_lines_land.geojson` |
| 내려받은 날 | 2026-09-08 |
| 라이선스 | **Public Domain** (Natural Earth — "no permission needed", 저작권 주장 없음) |

도시·지명 자산은 **가져오지 않았다**(판정 「도시 표기 없음」).
지역을 잘라 내지도 않았다 — 전 지구가 그대로 들어 있다(판정 「다른 지역이 나올 수도 있다」).

## 크기 (실측 · `stat -c %s`)

| 파일 | 원본 | 반입본 |
|---|---:|---:|
| `ne_110m_coastline.json` | 139,907 B | **96,757 B** |
| `ne_110m_admin_0_boundary_lines_land.json` | 340,010 B | **75,446 B** |
| 합계 | 479,917 B | **172,203 B (168.2 KB)** |

상한 500 KB(512,000 B) 대비 **33.6 %**. 시험(`frontend/test/basemap-layer.test.tsx`)이 매번 센다.

## 간략화 절차

원본은 합계 468.7 KB 로 상한 안이지만 여백이 31 KB 뿐이라, **좌표는 그대로 두고 표현의
군더더기만** 덜어 냈다. 스크립트 = `frontend/scripts/simplify-basemap.mjs`.

```
node frontend/scripts/simplify-basemap.mjs <원본.geojson> <출력.json>
```

1. `properties` · `bbox` · `crs` 제거 — 선을 긋는 데 쓰지 않는 필드.
2. 좌표를 소수점 **3자리**로 반올림(≈ 110 m). 1:110m 원본의 실제 정밀도보다 곱다.
3. 반올림 뒤 **연속 중복 점** 제거. 점이 2개 미만이 된 조각은 버린다.
4. 들여쓰기 없는 한 줄 JSON.

기하는 하나도 버리지 않았다 — feature 수 = 해안선 **134** · 국경 **331**(원본과 같다).
확장자만 `.json` 이다(Vite/TS 의 기본 JSON import 를 쓰려고). 내용은 GeoJSON
`FeatureCollection` 그대로다.
