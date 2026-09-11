# Stage 1·2 재검증 사양

승인 출처: `sessions/20260910-stage12-decisions.md`, 부모 사양 `stage1-stage2-closeout.md`, 사용자 2026-09-10 계획대로 개발 완수 지시.

## 원한 결과

기존 구현 9건(BF-7/8/9/11/13, I3, BF-12, X-7, WU-PREVIEW)과 승인된 U-1/F-3의 코드·현재 시험·원격 CI·dev 실물을 대조하여 재개발을 방지한다. 조사 완료와 각 제품 항목 완료는 별개다.

## 기준과 경계

- 기준 HEAD와 fetch된 origin/main: `712a33711f6a222ff7c1d431c4ecef0946508cca`, 차이 0/0.
- 승인결정 기존 변경 7파일을 보존한다. clean 작업트리 전제는 이 승인 baseline으로 구체화한다. tracked diff SHA256 `e775d30a8f3eb31faabba80b3389f5ab5ad1fb6ecc5a6a6e1679385cecf4dbf2`; 미추적 결정문서까지 lifecycle baseline이 내용 hash로 보존한다.
- 제품 코드·계약·마이그레이션을 수정하지 않는다. 상태 대장 편집은 부모 한 명이 수행한다.
- 운영 접촉은 SSH 상태·로그 조회만. 배포·push·삭제·로그인/계정 쓰기 E2E는 수행하지 않는다.
- 로컬 green만으로 dev 완료를 선언하지 않는다. CI step skip도 green 시험이 아니다.
- 회수 루프 첫 주기 실물 부재는 BF-12와 종속 TL-2를 막는다. 저장소·시험 효율·관측의 독립 로컬 구현은 계속할 수 있다.

## 수용 기준

1. 11행 각각 기존 완료 정의, main 포함, 관련 시험, dev 확인과 정확한 잔여조건을 `sessions/s12-verify.md`에 기록한다.
2. frontend-test, service-tests-core-api, service-tests-viz-render, service-tests-pipeline-worker, work-item-consistency, contract-lint를 한 lifecycle task로 순차 실행한다. 종료코드 0/1/78과 세 계수를 보고서에 남긴다.
3. 원격 core-api CI는 job 명칭뿐 아니라 실제 시험 step 성공을 확인한다. 로컬과 CI 환경·필터 차이를 설명한다.
4. 대장 done 후보와 유지 사유를 부모에게 전달한다. dev 15/15를 이번에 실행하지 않으면 새 실측으로 주장하지 않는다.
5. 결과 보고서가 미충족 조건을 드러내면 조사는 완료될 수 있으나 제품 완료 판정은 보류한다.
