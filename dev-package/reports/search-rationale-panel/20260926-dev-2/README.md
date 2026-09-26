# dev 501ef439 배포 뒤 검색 근거 사실 문구 재캡처 (2026-09-26)

- 대상: dev (`d31zgpff2091oh.cloudfront.net`) · 이전 배포 592ff4b7 → 이번 `501ef4398f42` (develop, PR #166~#171)
- 승인: Ted 2026-09-26 「dev 배포 다 머지해씀」 — dev 한정. reset·reseed·alembic downgrade·키 교체·`infra/**`·`ops/**` 변경 없음. `d3_search_evidence`(#169 승격 적용분) 무접촉.
- 사전 대조: `git diff --name-only 592ff4b7..501ef439 | grep -Ei 'migration|alembic|^infra/|/ops/'` = 0행.
- 계정: 운영자(무소속) 역할 · 전체 연구실 28건 범위.

## 배포 판정

| 항목 | 배포 전 | 배포 후 |
|---|---|---|
| deploy_doctor (EC2 1회 실행) | ✓ 15 · ✗ 0 · ─ 0 (트리 592ff4b7) | ✓ 15 · ✗ 0 · ─ 0 (트리 501ef439) |
| `CURRENT_FULL_SHA` | 592ff4b7693d… | 501ef4398f4252169b322b15bcb03f20ac7314f1 |
| `MAIN_SHA` | source_sha=6ac67e79bc96 candidate=592ff4b7693d ancestor=yes | source_sha=501ef4398f42 candidate=501ef4398f42 ancestor=yes |
| 컨테이너 4개 이미지 태그 | dev-592ff4b7693d | dev-501ef4398f42 (healthy) |
| 스키마 head | platform 0044 · ai 0011 | platform 0044 · ai 0011 (DB = 레포) |
| 사람 자료 표 계수 (BYPASSRLS `colab_backup`) | 계정 5 · 로그인 5 · 데이터셋 28 · 파일 571 · 업로드 96 · 프로젝트 4 · 계보 18 | 같음 |
| 웹 `index.html` sha256 (로컬 = 공개) | — | `ef220cab45546f6168e8a5d94f1dccaf4f18dc56b3f5ad0cb3ca1154b6a72e3b` · 공개 assets 95건 일치 · 번들 `assets/index-z0foCObm.js` |

- CI: `ci` run 36205742934 (attempt 1, push develop 501ef439) — green 14 · red(판정) 0 · red(준비) 0 · 해당 없음 1.
- 실행기: `scripts/deploy_release.py run` 계획 id `dev-verify-501ef439-20260926` — deploy 8단계(space → ship → tag → reposync → backup → up → web-build → deploy_web) · verify 3단계(state · web-hash · doctor) 전건 exit 0 · deployment=verified · notification=queued.

## 단정 결과 (응답 JSON · 화면 텍스트)

| 단정 | q1 pred_sample 앞 입력 | q2 강수 | q3 레이더 반사도 예측 |
|---|---|---|---|
| 카드 사실·rationale 에 「(출처」 0건 | 통과 (0) | 통과 (0) | 통과 (0) |
| term 사실에 「‘강우·강수’」 0건 (유일 낱말인 경우 제외) | 통과 (0) | 통과 (0) | 통과 (0) |
| 카드 문구에 「확인한 파일 근거」「온톨로지 연결 근거」「온톨로지」「계보」「못했어요」 0건 | 통과 (전부 0) | 통과 | 통과 |
| interpretation / degraded | llm / false | llm / false | llm / false |
| 결과 수 | 5 | 5 | 3 |

- 화면 텍스트의 「‘강우·강수’」 1건은 머리말 「주제 ‘강우·강수’로 좁혀 뒤졌어요」이고 카드 문구가 아니다.
- 상세 화면 `pred_sample` → 파일 관리 → `pred_sample.npy 검색 근거`: 설명서 이름 `01.level-data/01.precipitation/DATASETS.md · seq 5 pred_sample` · 절 또는 문단 `DATASETS.md#01.level-data/01.precipitation/DATASETS.md#seq-5` 표시 유지 (출처 label·locator). 편집 폼은 열기만 했고 저장하지 않았다.

## 전후 대조 — q1 「강우 예측 pred_sample.npy 파일의 바로 앞 입력 데이터셋」

전 = `origin/deploy/dev-592ff4b7:dev-package/reports/search-rationale-panel/20260926-dev/dev-search-response-llm.json` · 후 = `dev-search-response-llm.json`

| 카드 | 종류 | 전 (592ff4b7) | 후 (501ef439) |
|---|---|---|---|
| pred_sample | term | ‘강우’, ‘예측’, ‘pred_sample.npy’가 이름·주제·요약·포맷·변수에 맞았어요 | 같음 |
| pred_sample | evidence | pred_sample.npy에서 파일 역할(예측 결과) 조건이 맞았어요 (출처 01.level-data/01.precipitation/DATASETS.md · seq 5 pred_sample · DATASETS.md#01.level-data/01.precipitation/DATASETS.md#seq-5) | pred_sample.npy에서 파일 역할(예측 결과) 조건이 맞았어요 |
| HSR 레이더 반사도 원자료 | term | ‘강우’, ‘강우·강수’가 이름·주제·요약에 맞았어요 | ‘강우’가 이름·주제·요약에 맞았어요 |
| rn15 15분 누적강수 | term | ‘강우’, ‘강우·강수’가 이름·주제·요약에 맞았어요 | ‘강우’가 이름·주제·요약에 맞았어요 |
| hsr_sample | term | ‘강우’, ‘강우·강수’가 이름·주제·요약·확인한 파일 근거에 맞았어요 | ‘강우’가 이름·주제·요약에 맞았어요 |
| hsr_sample | linked | ‘pred_sample.npy’ 파일이 속한 자료의 바로 앞 단계 자료예요 | 같음 |
| rn15_sample | term | ‘강우’, ‘강우·강수’가 이름·주제·요약·확인한 파일 근거에 맞았어요 | ‘강우’가 이름·주제·요약에 맞았어요 |
| rn15_sample | linked | ‘pred_sample.npy’ 파일이 속한 자료의 바로 앞 단계 자료예요 | 같음 |

결과 순서·수(5건)·topic(강우·강수)·scope(전체 연구실 28건)는 전후 같다.

## 파일

| 파일 | 내용 |
|---|---|
| `dev-q1-light-1280.png` | q1 라이트 1280 전체 페이지 |
| `dev-q1-dark-390.png` | q1 다크 390 전체 페이지 |
| `dev-q2-light-1280.png` | q2 「강수」 라이트 1280 |
| `dev-q3-light-1280.png` | q3 「레이더 반사도로 강우를 예측한 모델 결과」 라이트 1280 |
| `dev-pred-sample-evidence-light-1280.png` | pred_sample 상세 · pred_sample.npy 검색 근거 (설명서 이름 · 절 또는 문단) |
| `dev-search-response-llm.json` | q1 `POST /api/v1/dataset-searches` 응답 (요청 헤더 제외) |
| `dev-queries.json` | q1~q3 카드별 rationaleFacts·rationale 과 단정 계수 |

## 남은 항목

- 「‘강우·강수’가 유일한 낱말」인 term 사실은 세 질문 모두에서 관측되지 않았다 — 예외 분기는 이번 캡처로 검증하지 못했다.
- dev 태그(`infra/dev/tag-release.sh dev`)는 사람이 부르는 단계로 남겨 두었다.
- 배포 완료 알림은 operator spool 에 queued 상태다.
