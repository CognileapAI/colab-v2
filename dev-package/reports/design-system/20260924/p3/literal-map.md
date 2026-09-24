# P3 색상 리터럴 인벤토리 — frontend/src/**/*.css (tokens.css 제외)

기준: HEAD 7967e001 (P1 병합 — tokens.css 가 유일한 :root). 파서: (job tmp) 원본 데이터: p3_results.json (같은 폴더). 주석은 줄번호를 보존하도록 개행 수를 맞춰 제거했다.

## 총계

- 검출 리터럴(직접+폴백) 총 72건: A 1 · B 3 · C 1 · D(죽은 폴백) 67
- 허용 키워드(transparent/inherit/currentColor) 사용 64건 — 리터럴 아님, 별도 집계
- 다크 컨텍스트(`prefers-color-scheme: dark` 또는 `[data-theme="dark"]`) 안의 리터럴: 0건 — 스캔 대상 컴포넌트 CSS 어디에도 다크 전용 블록이 없다(다크 분기는 tokens.css 안에만 있고 이번 스캔 범위에서 제외됨)

파일별 리터럴 상위 3 (키워드 제외, A+B+C+D 합):
1. components/search/search.css — 41건 (D 40, B 1)
2. components/upload/upload.css — 10건 (D 9, C 1)
3. shell/shell.css — 6건 (전부 D)
   (근접: components/detail/detail.css 4건 — D 3 · B 1)

## 분류 A — 같은 값 토큰 1개 → 치환

| file:line | selector | property(줄 첫 선언 기준) | literal | 같은 값 토큰 |
|---|---|---|---|---|
| components/project/project.css:334 | .pj-modal-back | background | rgb(15 20 28 / 45%) | --color-overlay |

## 분류 B — 같은 값 토큰 여러 개 → 뜻으로 고를 것

| file:line | selector | literal | 후보 토큰 |
|---|---|---|---|
| components/catalog/catalog.css:75 | .colmenu .cm-box (color 선언) | #fff | --color-white, --color-on-primary, --color-text-on-primary, --color-surface, --color-on-danger, --color-on-dark |
| components/detail/detail.css:159 | .detail-page .dt-edit .de-req (color 선언) | #fff | 위와 동일 6종 |
| components/search/search.css:113 | .search-page .vfilter .vsw::after (background 선언) | #fff | 위와 동일 6종 |

비고: 세 건 모두 흰 글자/흰 배경 용도이며 흰색 계열 토큰이 6개나 있어 자동 치환이 위험하다 — 각 용례(글자색 vs 표면색 vs on-danger 등)의 뜻을 보고 Ted 판정.

## 분류 C — 같은 값 토큰 없음 → Ted 판정

| file:line | selector | literal | 비고 |
|---|---|---|---|
| components/upload/upload.css:256 | .chip | background: #eef2f7 | 가장 가까운 후보는 --color-gray-100(#e8ecf2)·--color-surface-alt(#f4f7fb)이나 값이 다르다 — 새 토큰 또는 기존 토큰 값 변경 판정 필요 |

## 분류 D — 죽은 폴백(var(--x, literal) 인데 --x 가 정의됨 → 폴백 삭제) — 67건

전부 `var(--토큰명, <literal>)` 형태이며 P1 이후 해당 토큰이 tokens.css 에 전부 정의돼 있어 폴백 리터럴은 죽은 코드다. 파일별 건수:

- components/search/search.css 40
- components/upload/upload.css 9
- shell/shell.css 6
- components/detail/detail.css 3
- components/lineage/lineage.css 3
- components/dashboard/dashboard.css 2
- components/lab/lab.css 2
- components/preview/preview.css 2

전체 file:line | var(--토큰) | literal 목록:

```
dashboard/dashboard.css:125 | --accent-neutral | #5b7089
dashboard/dashboard.css:154 | --fg-danger | #a3222b
detail/detail.css:95 | --color-danger | #b42318
detail/detail.css:111 | --color-danger | #b42318
detail/detail.css:186 | --color-surface | #ffffff
lab/lab.css:13 | --color-danger | #b42318
lab/lab.css:40 | --color-surface | #fff
lineage/lineage.css:266 | --lin-over-ink | #5b6472
lineage/lineage.css:273 | --lin-over-ink | #5b6472
lineage/lineage.css:294 | --lin-over-ink | #5b6472
preview/preview.css:553 | --color-gray-500 | #697077
preview/preview.css:559 | --color-gray-400 | #848c94
search/search.css:10 | --color-border-control | #848c94
search/search.css:11 | --color-surface | #fff
search/search.css:15 | --color-primary-600 | #1f5eff
search/search.css:19 | --color-text-muted | #565c63
search/search.css:25 | --color-text-muted | #565c63
search/search.css:28 | --color-text-muted | #565c63
search/search.css:30 | --color-text-muted | #565c63
search/search.css:33 | --color-border | #dfe3e8
search/search.css:34 | --color-surface | #fff
search/search.css:38 | --color-text-muted | #565c63
search/search.css:39 | --color-warning-50 | #fff6ed
search/search.css:40 | --color-warning-50 | #fff6ed
search/search.css:50 | --color-border | #dde1e6
search/search.css:50 | --color-surface | #fff
search/search.css:50 | --color-text-body | #21272a
search/search.css:51 | --color-primary-600 | #0f62fe
search/search.css:52 | --color-text-muted | #565c63
search/search.css:56 | --color-border | #dfe3e8
search/search.css:57 | --color-surface | #fff
search/search.css:59 | --color-surface-alt | #f4f7fb
search/search.css:67 | --color-gray-100 | #e8ecf2
search/search.css:70 | --color-primary-600 | #1f5eff
search/search.css:75 | --color-text | #1b1f24
search/search.css:80 | --color-text-muted | #565c63
search/search.css:84 | --color-border | #dfe3e8
search/search.css:86 | --color-warning-50 | #fff6ed
search/search.css:86 | --color-warning-600 | #a85400
search/search.css:89 | --color-text-muted | #565c63
search/search.css:98 | --color-text-muted | #565c63
search/search.css:100 | --color-text-body | #21272a
search/search.css:104 | --color-border | #dfe3e8
search/search.css:105 | --color-surface | #fff
search/search.css:109 | --color-gray-200 | #d5dae0
search/search.css:115 | --color-success-600 | #1f8b4c (2건, 같은 줄)
search/search.css:116 | --color-success-600 | #1f8b4c
search/search.css:120 | --color-success-600 | #1f8b4c
search/search.css:125 | --color-success-50 | #e6f4ea
search/search.css:125 | --color-success-600 | #1f8b4c
search/search.css:128 | --color-success-600 | #1f8b4c
upload/upload.css:113 | --up-muted | #666
upload/upload.css:165 | --color-border-strong | #dfe3e8
upload/upload.css:166 | --color-primary-600 | #1369e9
upload/upload.css:282 | --color-surface | #fff
upload/upload.css:342 | --color-border | #e8ecf2
upload/upload.css:346 | --color-border | #e8ecf2
upload/upload.css:350 | --color-primary-600 | #1369e9
upload/upload.css:355 | --color-primary-600 | #1369e9
upload/upload.css:359 | --color-text-muted | #565c63
shell/shell.css:18 | --color-border | #dde1e6
shell/shell.css:20 | --color-surface | #fff
shell/shell.css:25 | --color-text-body | #21272a
shell/shell.css:28 | --color-border | #dde1e6
shell/shell.css:30 | --color-surface | #fff
shell/shell.css:31 | --color-text-body | #21272a
```

## 허용 키워드 사용 (리터럴 아님, 참고용) — 64건

- inherit 44건, transparent 20건, currentColor 0건
- 파일별: auth/login.css 4 · components/catalog/catalog.css 2 · components/common/variableTable.css 4 · components/detail/deletion.css 1 · components/detail/detail.css 6 · components/lab/lab.css 1 · components/lineage/lineage.css 1 · components/lineage/lineageGraph.css 2 · components/members/members.css 5 · components/project/project.css 6 · components/search/search.css 5 · components/upload/upload.css 10 · shell/design-system.css 8 · shell/shell.css 9

## 스캔 방법과 한계

1. tokens.css 를 주석 제거 후 파싱해 라이트 `:root` 블록과 `:root[data-theme="dark"]` 블록의 변수-값 표를 만들고, var() 별칭은 1단계 해석했다(라이트 90개·다크 41개 변수).
2. 나머지 CSS 파일에서 `var(--x, <literal>)` 폴백 안의 색상과, 선언문의 직접 색상 리터럴(hex/rgb/rgba/hsl/hsla)을 줄 단위로 찾았다. `var(...)` 안쪽은 직접 리터럴 집계에서 제외했다.
3. 같은 값 비교는 3자리 hex→6자리 정규화, rgb()→hex 정규화로 맞춘 뒤 라이트 토큰 표와 대조했다.
4. 한계: 한 줄에 선언이 여러 개(`a: 1; b: 2;`) 있으면 리포트의 property 컬럼이 그 줄의 첫 선언명을 가리켜 부정확할 수 있다 — A/B/C 5건은 실제 소스를 직접 대조해 property 를 손으로 바로잡았다. D 67건은 property 컬럼을 생략하고 var 이름으로만 표기했으므로 이 한계의 영향이 없다.
5. 다크 컨텍스트 판정은 선택자 문자열에 `prefers-color-scheme: dark` 또는 `data-theme=` 와 `dark` 가 함께 나타나는지로 봤다 — 이번 스캔 파일들에는 해당 선택자가 전혀 없었다.
