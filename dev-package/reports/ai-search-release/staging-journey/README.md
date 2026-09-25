# AI 검색 ST 사용자 여정 — 2026-09-14

대상은 `local-stage`와 ST에 배포한 `a383510d7ded`이다. 기존 `ST검색검증20260913 합성 강우` 합성 픽스처만 사용했으며 새 운영 자료를 만들거나 삭제하지 않았다.

## 배포·보존 판정

- 배포 판정: 헬스/본문/컨테이너/호스트 노출 15/15 GREEN.
- migration: platform `0036_search_refresh_runtime`, AI `0007_merge_vocab_and_category`, 2/2 GREEN.
- 온톨로지 보호: DB·schema·D9 guardian 소유와 런타임 권한 GREEN.
- D9 보존: concept 49, edge 19, method term 13, place alias 4, topic synonym 18.
- 검색 refresh 계정·스케줄·worker 설정은 배선하지 않았다. 조건 판정 여정 구간의 core-api `POST /dataset-searches`는 200 두 건이고 ai-service `/searches`·모델 경로 요청은 0건이었다.
- 원본 운영 증거: `/home/ttlhi10/colab-v2-releases/pipeline.log`, `/home/ttlhi10/colab-v2-releases/release-ledger.tsv`, `.git/deploy-releases/st-b462b558aab74b139679c541c2ebcac0/state.json`.

## 실제 브라우저 여정

`agent-browser` 0.27.0의 격리 세션과 기존 ST 관리자 인증 레코드를 사용했다. API 직접 저장으로 우회하지 않았다.

1. 합성 TIFF의 검색 근거를 UI에서 확인 저장했다.
2. 새로고침 뒤 출처명, 절 위치, 서울, 강수량, 2025-01-01~2025-12-31, 공간 격자, tif, 월평균이 유지됨을 확인했다.
3. `서울 2025년 월평균 강수량 tif 추천`에서 명시적 연구 조건을 제출했다.
4. 합성 후보 1건, 비교 근거, `2025-01-01 ~ 2025-12-31`, 저장한 출처를 확인했다.
5. `자료 상세 보기`로 이동하고 상세 페이지를 새로고침해 동일 데이터셋 제목을 확인했다.

결과 화면은 [search-result.png](search-result.png), 상세 새로고침은 [detail-reload.png](detail-reload.png)에 보존한다.

첫 ST SHA `b8d53a74078f`에서는 비교 근거의 기간이 `end ~ start`로 표시됐다. 이 실행을 성공으로 덮지 않고, 실패 회귀 테스트→최소 수정→전체 frontend 1,406건/빌드 GREEN→`a383510d7ded` 재배포→동일 여정 GREEN 순서로 닫았다.

## main 승격 차단

최신 `origin/main` `6a4ac6c4`를 시험 병합한 트리는 `ba12eb074ea7773e09ca117d44eb4fdf6cfc0c73`이다. core-api 1,385건, viz-render 448건, 생성물 17건, 대장 230건, 기획 임베드 15건은 GREEN이지만 frontend는 123파일/1,443건 중 8파일/42건 RED였다. 판정 JSON은 `../main-refresh/frontend/gate-summary.json`에 보존한다.

실패 분포는 최신 main의 `dev-package/03-HANDOFF.md` `§4` 블로커 76과 같다. 등록 약 31건은 부모 0건의 기본 Lv0와 Lv0 출처 필수 규칙이 결합해 서버 등록 호출을 막고(`upload.test.tsx` 18, `register-steps` 4, `fe-small-rc8` 3, `interval-period` 2, `upload-form-rev2` 3, `upload-register-on-analysis-failure` 1), 나머지 11건은 제거된 `lin-confirm`을 main 시험이 요구한다(`lv-mismatch-reason-20260913` 3, `processing-level-default-20260913` 8). 이는 제품 판정 대기이며 검색 릴리스에서 시험을 고치거나 실패를 제외하지 않았다. 시험 병합을 중단했고 main/DEV는 NO-GO다.
