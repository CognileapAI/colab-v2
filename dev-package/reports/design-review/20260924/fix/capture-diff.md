# design-fix 20260924 · 최종 트리 캡처 대조

기준 `fix0924-base`(착수 HEAD `e8fc4e13`) 와 최종 통합 트리 `fix0924-final`(HEAD `407fbcab`) 의 `visual:diff` 엄격 대조 결과와, 바뀐 장면마다의 원인 항목 대응표.

## 1. 요약

- 캡처 **202장**(34장면 × 폭 3 × 테마 2, `gnb-more` 폭 2) · **바뀜 88장**(15장면) · **그대로 114장**(19장면 전부 ＋ `upload-classify` 375 2장).
- 엄격 차이 픽셀 합 3,314,549 · 보조(threshold 0.1) 855,575 · 크기 차이 6장(`detail` 768·1440 두 테마 높이 −22px · `primitives` 375 두 테마 +1px).
- `diff.mjs` 종료코드 **1**(차이 있음). 이번 대조는 의도된 시각 변경의 목록화가 목적이다 — 합격 판정(exit 0)이 아니다.
- **원인 불명 0건.** 바뀐 88장 전부를 아래 원인 항목으로 분해했다. 이동 보정 뒤 남는 잔차는 모두 이동한 요소 가장자리의 채널 1–2 단계 반올림 차이다(§5).
- 원인 항목이 캡처에 드러난 것: **값 18**(칩 테두리) · **#11**(칩 배경 — `primitives` `.chip--off` 만) · **#12**(`.btn-sm` 29px ＋ inline-flex · A4) · **#7**(자간 값이 바뀐 3곳) · **#9**(`.btn-primary:hover` primary-700 · 캡처 절차상 포인터가 남은 단추) · **A12**(`.search-page .chip` 테두리 단축형 삭제).

## 2. 실행

| 단계 | 명령(작업 디렉터리 `frontend/`) | 결과 |
|---|---|---|
| 캡처 | `npm run visual:capture -- --label fix0924-final` | `202 captures -> frontend/.visual/fix0924-final` · exit 0 · audit 다시 빌드(`built: true`) · parallel 2 · 2026-09-24T20:29:27Z – 20:37:35Z · `gitDirty` false · `browserArgs` = scenes.json 6개(`--disable-gpu` … `--disable-lcd-text`) |
| 대조 | `npm run visual:diff -- .visual/fix0924-base .visual/fix0924-final .visual/fix0924-report` | `202 captures · red 88 · strict px 3314549 · exit 1` |

- 명세 sha256 `20919450d75f…` 두 쪽 같음 → `--subset` 없이 엄격 대조(선례 `design-system/20260924/product-compare/README.md` 5).
- 기준: `frontend/.visual/fix0924-base` · HEAD `e8fc4e13` · 2026-09-24T15:19:25Z · 202장.
- 도구 보고 원본(캡처별 엄격·보조 px 표): `fix/capture/diff-report.md` · `diff-report.json`.
- 캡처 뒤 브라우저·preview 프로세스 잔존 0(`pgrep -af "agent-browser|vite preview|chrom"` 실측). 이 대조에서 직접 연 agent-browser 세션 0 — `capture.py` 가 제 세션을 닫는다.

## 3. 원인 항목 → 캡처에 드러난 자리

| 항목 | 변경 | 드러난 장면 | 드러난 요소 · 실측 |
|---|---|---|---|
| 값 18 | `.chip` `border-color: var(--color-border-strong)` | catalog · projects · project-detail · project-dialog · project-close · detail · members · search · search-degraded · pending · primitives | 칩 윤곽 1px 링만 바뀜. 라이트 `#e8ecf2`(232,236,242) → `#dfe3e8`(223,227,232) 픽셀 실측 · 칩 안쪽 픽셀 불변 |
| A12 | `.search-page .chip` 의 `border` 단축형 삭제 | search · search-degraded | 결과 행 「조각 n」 칩 테두리가 값 18 로 바뀜 |
| #11 | `.chip` 배경 `#eef2f7` → `--color-gray-100` | primitives | `.chip--off` 안쪽 채움. 라이트 `#eef2f7` → `#e8ecf2` · 다크 밝은 `#eef2f7` 바탕 → `#2b3745`. 제품 장면의 칩은 모두 제 배경 수식자를 가져 안쪽 픽셀 불변(테두리만 바뀜) |
| #12 · A4 | `.btn-sm` = `inline-flex` · `align-items:center` · 29px · padding 0 11px · `--text-caption` · 640px 이하 `min-height: 44px` | detail · settings · members · upload-classify · upload-metadata · upload-link · primitives | 768·1440: 단추 높이 40 → 29px(−11px) · 아래 내용이 11px 위로. 375: 높이 44px 유지 · 글자 13px·좌우 여백만 바뀜. 부수: 모달 본문 스크롤 높이·위치 변화(스크롤바 썸 · 내용 5–6px 이동) · `primitives` 375 첫 단추 줄 상자 1–2px 커짐 |
| #7 | 자간 토큰 — 값이 바뀐 곳만 드러남 | project-detail · detail · settings | `.project-detail .pd-head h1` −0.03em → −0.02em(`project.css:31`) · 상세 제목 −0.03em → −0.02em(`detail.css:15`) · `.settings-page h1` 「연구실 설정」 −0.023em → −0.02em(`members.css:20`). 제목 폭이 넓어짐 |
| #9 · 값 10 | `.btn-primary:where(:not(:disabled)):hover` = primary-700 | upload-metadata · upload-link | 장면 절차의 마지막 click(`[data-testid=reg-next]`) 자리에 포인터가 남아, 그 자리의 `btn-primary`(「다음 →」·「데이터셋 만들기 →」)가 hover 로 찍힘. 라이트 픽셀 `#1369e9`(19,105,233) → `#0f62e0`(15,98,224) 실측 |

## 4. 바뀐 장면 → 원인 항목 #

px = 캡처별 엄격 차이 픽셀(L 라이트 · D 다크). 15장면 88장 전부.

| 장면 | 바뀐 캡처(엄격 px) | 바뀐 요소 | 원인 항목 # |
|---|---|---|---|
| catalog | 6/6 · L/D 375 1948 · 768 2120 · 1440 2292 | 파일 행 칩 「아직 모름」「조각 n」「외 1」 · 잠긴 행 「잠김」 칩 테두리 | 값 18 |
| projects | 6/6 · 778–780 | 프로젝트 카드 유형 칩 「국가과제」「논문」 테두리 | 값 18 |
| project-detail | 6/6 · 375 6488 · 768 7384–7387 · 1440 7383–7386 | 제목 h1 자간(폭 증가) · 유형 칩 「국가과제」 · 연결 주소 「계보」 · 소속 데이터셋 「조각 4」 칩 테두리 | #7 · 값 18 |
| project-dialog | 6/6 · 375 170–172 · 768 408–414 · 1440 600–604 | 대화상자 안 「계보」 칩 · 뒤판 카드 유형 칩 테두리 | 값 18 |
| project-close | 6/6 · 375 170–171 · 768 500–504 · 1440 430–432 | 뒤판 카드 유형 칩 테두리(닫기 대화상자 자체는 불변) | 값 18 |
| detail | 6/6 · 375 6199–6205 · 768 365380–365541 · 1440 544034–544213 · 768·1440 높이 −22px | 제목 자간 · 헤더 칩 「강우·강수」 테두리 · 파일 카드 「파일 관리」「파일 추가」 `btn-sm` 40 → 29px(아래 전체 11px 위로) · 계보 「이후 수정됨」 칩 테두리 · 대표 그림 「그림 고르기」 `btn-sm`(아래 전체 22px 위로). 375 는 단추 높이 44px 유지 · 이동 없음 | #7 · #12 · 값 18 |
| settings | 6/6 · 375 1188–1196 · 768 21091–21129 · 1440 28290–28328 | h1 「연구실 설정」 자간 · 「정보 편집」 `btn-sm`(768·1440 카드 머리 낮아짐 → 정보 격자 위로 이동 · 375 글자·폭만) | #7 · #12 |
| members | 6/6 · 375 1303–1311 · 768 64460–64461 · 1440 87718–87742 | 「권한 편집」 `btn-sm`(768·1440 카드 머리 낮아짐 → 권한 표 전체 위로 이동) · 역할 칩 「교수 관리자」「연구원」 테두리 | #12 · 값 18 |
| search | 6/6 · 각 1052 | 결과 행 「조각 n」 칩 테두리 5곳 | 값 18 · A12 |
| search-degraded | 6/6 · 각 1052 | search 와 같은 칩 5곳 | 값 18 · A12 |
| pending | 6/6 · 각 206 | 「검토 대기」 칩(`chip--warning`) 테두리 | 값 18 |
| upload-classify | 4/6 · 768 62 · 1440 110107–118493 · 375 0 | 1440: 미리보기 패널 「짝 파일 없이 그려 보기」「미리보기 그리기」 `btn-sm`(짝 파일 단추가 안내 문장 옆으로 올라옴 · 패널 내용 위로) · 오른쪽 열은 스크롤바 썸만. 768: 스크롤바 썸 9×9px 만 | #12 |
| upload-metadata | 6/6 · 375 2652–2667 · 768 2475–2492 · 1440 56658–57299 | 전 폭: 「다음 →」 hover primary-700. 1440: 미리보기 패널 `btn-sm` 2개 · 패널 위치. 768: 스크롤바 썸 · 입력칸 위 모서리 11px(채널 ±1) | #9 · #12 |
| upload-link | 6/6 · 375 6430–6458 · 768 68344–68403 · 1440 187789–196490 | 「+ 가공 전 데이터 추가」 `btn-sm` · 미리보기 패널 `btn-sm` 2개 · 모달 본문 스크롤 위치(1440 내용 5px · 768 6px 아래로 — 스크롤 높이 감소) · 「데이터셋 만들기 →」 hover primary-700 · 375: 가공 전 데이터 추가 단추 글자·폭 ＋ hover | #12 · #9 |
| primitives | 6/6 · 375 44344–44610 · 768·1440 5143–5146 · 375 높이 +1px | `.btn-sm` 40 → 29px · 칩 6종 테두리 · `.chip--off` 채움(다크 밝은 바탕 해소) · 375: `.btn-sm` inline-flex·13px 로 첫 단추 줄 상자가 커져 아래 전체 1–2px 아래로 | #12 · #11 · 값 18 |

## 5. 이동 차이의 분해(원인 불명 0 의 근거)

- 방법: 차이 행 띠 추출 → 이동량을 가정해 후보 행 y 를 기준 행 y＋이동과 대조한 잔차 → 잔차 자리 확대 전후·diff 크롭 육안 확인 → 대표 픽셀 색값 실측. 스크립트는 저장소 밖 임시(`/tmp/fixdiff/`) — 산출물 아님.
- `detail-light-1440`: 파일 카드 뒤 11px 보정 → 잔차 = 「이후 수정됨」 칩 테두리 ＋ 「그림 고르기」 단추. 그 뒤 22px 보정 → 잔차 101px = 그림 고르기 단추 가장자리 ＋ 전폭 「다시 불러오기」 단추 아래 모서리 12px(채널 차 1). `detail-light-768` 도 같은 두 이동 · 22px 보정 뒤 잔차 131px(그림 고르기 단추 가장자리).
- `upload-link-light-1440` 오른쪽 열: 위쪽 −5px 보정 잔차 0 → 「+ 가공 전 데이터 추가」 단추 → 아래쪽 ＋6px 보정 잔차 0(단추 −11px 과 일치). `upload-link-light-768`: −6px(잔차 4px) · ＋5px 보정 뒤 채널 >2 잔차는 단추 자리와 하단 바(hover)뿐 · 입력칸 경계 줄은 채널 ≤2.
- `upload-metadata-light-768` 입력칸 모서리 11px: 채널 ±1. 같은 캡처에서 스크롤바 썸이 움직였다(스크롤 높이 변화 = #12 부수). 내용 정렬은 그대로라 스크롤 위치의 서브픽셀 변화에 따른 가장자리 반올림으로 본다(추정 · 채널 ±1 이라 시각 영향 0).
- `primitives-light-375`: 첫 단추 줄 아래 300–446 행은 −1px 보정 잔차 0 · 447 행 아래는 행마다 −1/−2px 보정으로 잔차 0(서브픽셀 이동의 행별 반올림). 남는 행 = 칩 줄(795–842 · 값 18·#11) ＋ 677–720 행 최대 20px/행(선택 상자 가장자리).
- 라이트·다크 짝 44쌍: 차이 띠(행·열 범위) 41쌍 일치 · 3쌍은 같은 요소 안에서 범위만 다르다(`settings`·`members` 375 「정보 편집」·「권한 편집」 단추 오른쪽 가장자리까지 · `upload-classify` 1440 미리보기 패널 윗단 7행). 짝별 엄격 px 차이 최대 8,701(`upload-link` 1440 · 다크 토큰 값 차이). 다크에만 있는 차이 자리 0.

## 6. 캡처에 드러나지 않은 항목(차이 0 과 정합)

| 항목 | 캡처 결과 | 사유 |
|---|---|---|
| #8 `--text-*` rem | 그대로인 19장면 114장(login · lab · empty · preview 등) 차이 0 · 바뀐 15장면의 차이도 전부 다른 항목으로 분해됨 | 뿌리 16px 에서 값 무변 — 차이 0 이 기대값 |
| #7 값 같은 5곳 · 값 9 | search 차이는 칩 5곳뿐 · login 0 | `search.css:7` · `dashboard.css:206` · `project.css:362` · `.brand` · `.page-head h1` 은 −0.02em 그대로 · `.login-brand` 리터럴 유지 |
| #7 `catalog.css:66` | 해당 요소 없음 | `.colmenu` 열 메뉴를 연 장면 없음 |
| #1 모달 전환 · 값 2 | upload 6장 차이 0 | 열린 끝 모양 동일. 캡처는 `FREEZE_CSS`(animation·transition 끔)로 찍는다 |
| #2 팝오버 · #4 · 값 21 | 해당 상태 없음 | 달력을 연 장면 · 파일 끌기 장면 없음 |
| #10 · 값 19 · WU-A1–A4 | 해당 상태 없음 | `.btn-strong` hover · `:active` 누름 상태를 만드는 장면 없음 |
| #14 z-index | account-admin 6장 차이 0 | `scenes.json` 의 account-admin 은 actions 0 — 계정 모달을 연 상태 없음 |
| #16 `.lvl-mismatch` | 해당 요소 없음 | catalog 차이는 전부 칩 테두리로 분해됨 |
| #17 `.de-req` | 해당 요소 없음 | 상세 편집 상태 장면 없음 |
| #13 · #15 · #19 | 코드 값 무변 | 주석만 |

## 7. 대표 전후 이미지

`fix/capture/` 에 12세트(`<캡처>.before.png` · `.after.png` · `.diff.png` · 36장).

| 캡처 | 보는 것 |
|---|---|
| `catalog-light-1440` | 값 18 — 표 안 칩 테두리 |
| `primitives-dark-1440` | #11 `.chip--off` 다크 채움 · 값 18 · #12 `.btn-sm` |
| `primitives-light-375` | #12 640px 이하 44px 하한 · inline-flex 로 아래 1–2px 이동 · 높이 +1px |
| `project-detail-light-1440` | #7 제목 자간 · 값 18 |
| `detail-light-1440` | #7 · #12 두 곳 · 높이 −22px |
| `settings-light-1440` | #7 h1 · #12 「정보 편집」 |
| `members-light-1440` | #12 「권한 편집」 → 표 이동 · 역할 칩 |
| `search-light-1440` | A12 · 값 18 |
| `pending-dark-1440` | 값 18 `chip--warning` 다크 |
| `upload-classify-light-1440` | #12 미리보기 패널 · 스크롤바 |
| `upload-metadata-light-375` | #9 포인터가 남은 「다음 →」 hover |
| `upload-link-light-1440` | #12 · 스크롤 위치 5px · #9 |

## 8. 남은 것

- 캡처 88장 차이는 모두 확정 값·항목의 의도된 변경이다. 수용 판정(advisor ③ · Ted)은 이 표와 `fix/capture/` 로 한다.
- 캡처가 닿지 않는 항목(§6)은 레인 보고서의 RTL·계산값·실브라우저 증거가 담당한다. 이 대조로 그 항목의 시각 결과를 보증하지 않는다.
- #9 hover 차이는 캡처 절차(click 뒤 포인터 잔류)의 산물이다. 다음 기준 캡처부터 이 두 장면은 hover 상태가 섞인 채로 비교된다.
