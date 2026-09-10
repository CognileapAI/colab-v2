> spec: dev-package/prd/specs/product-finish.md
# 제품 개발 마감 실행 계획

**Goal:** 기존 기능의 남은 구현·검증을 완료하고 배포 가능한 결과를 만든다.
**Architecture:** 기존 서비스·계약·게이트 재사용. 제품 상태는 대장 한 곳에 유지한다.
**Tech Stack:** 기존 Python 서비스, TypeScript frontend, WSL gates, agent-browser.
**Spec:** `dev-package/prd/specs/product-finish.md`

## 전체 진행

- [x] 실제 main 이력과 최신 CI 잡 조회. 기록의 core-api 실패가 현재 성공임을 확인.
- [x] stage 1/2 미완료 대장 19행 조사. 구현 존재/검증 대기/결정 대기 분리(조사 노트 참조).
- [x] CI: 면제 eval의 불필요한 API 키 요구 제거, 러너 7건·게이트 4건·명시 면제 검증. 원격 CI는 미실행.
- [x] CI: 일회용 두 DB 실제 upgrade head 후 schema-diff green. 잔존 gatepg 컨테이너 0 확인.
- [x] 기획 원본은 로컬 필수 대조 유지, CI 합성 fixture 회귀로 분리. CI 원본 미실행 명시. 원본 중복·업로드 없음.
- [ ] 실제 제품 결함은 기존 완료 정의에 따라 실패 재현 → 수정 → 회귀.
  - [x] 기존 스크린샷·대시보드·CSS 토큰 회귀 3파일 41개 통과. 브라우저 동작은 별도.
  - [x] S3 보관 태그 조사: 구현이 아닌 문서 변경만 존재. 완료 전송 원장 보관 기간은 사용자 결정 대기.
- [x] 선정한 agent-browser 사용자 여정 실행(로그인·업로드·등록·렌더·재접속).
  - [x] 일회용 DB + 실제 core-api + 동일 HEAD frontend 로그인·오입력 거절·재접속·로그아웃 통과.
  - [x] 실행별 서버 marker 및 frontend proxy 확인, 브라우저 종료 실패 판정 보완 후 재통과.
  - [x] 실제 GeoTIFF 업로드·워커 처리·설명 누락 거절·등록·상세 reload 메타데이터 유지·로그아웃 통과. wrapper 종료 후 gatepg 잔존 0.
  - [x] 실제 viz-render 연결, 등록 전후가 아니라 등록 후·상세 reload 후 이미지 로드 확인. 저장 스크린샷 육안 확인.
- [x] X-7 로컬: 임의 LIMIT 1 제거, 공개202/잠김403 경계 검증. RED→관련10개 및 전체981개 GREEN. 원격CI 대기.
- [x] BF-13 로컬: 공통16개 값충돌0, 모든공통값 변이 및 세미콜론 생략 음성검사. 관련120개/최종4개 GREEN. 값·위치 유지.
- [x] 이번 변경 관련 로컬 게이트·타입·빌드 실행, 실패·준비·면제를 구분해 기록.
- [x] 코드 검토 지적 반영 및 루트 통합. 배포 성공은 별도 조건으로 유지.
- [x] dev a3389bd 배포 및 deploy_doctor 15/15·skip0 단일 실행 증거 확인.
- [ ] main CI에서 발견한 프로젝트 정렬 시험의 비동기 대기 수정 후 원격 CI 확인 및 릴리스 기록 확정.

2026-09-09 후속 당시 배포·CI 기록은 `dev-package/sessions/20260909-product-dev-release.md`에 복구했다. 2026-09-10 문서 동기화에서는 현재 배포를 다시 측정하지 않아 위 판정은 변경하지 않는다.

## 실행 규칙

개별 수정 후 전체 계획의 다음 실행 가능한 항목으로 계속한다.
제품 상태 대장은 증거와 완료 정의가 충족된 경우에만 갱신한다.
이전 Claude/Codex 전환 변경은 보존한다. 현재 쓰기 주체는 메인 하나이며 조사자는 지정 노트만 쓴다.
격리 구현 사본: `.codex/worktrees/product-finish`, 브랜치 `lane/product-finish`.
다른 하네스 작업 종료 후 제품 수정은 루트 `integration/r-product-finish`에도 반영했다.
루트에서 실제 전체 E2E(렌더 포함)를 다시 실행해 통과했고 일회용DB 잔존0을 확인했다.
현재 통합 결과·대장 정본은 루트이며, 격리 사본은 중간 검증용으로 보존한다.
PR #7을 main a3389bd로 반영하고 깨끗한 작업 사본에서 ARM64 이미지 5개와 웹을 빌드해 dev에 배포했다.
공통 절차: `.claude/skills/colab-v2-work/SKILL.md`, `writing-plans`, `executing-plans`.

## 검증 순서

1. 최신 CI 실패 로그를 출발 증거로 보존하고 수정 대상과 직접 연결한다.
2. CI eval: `eval/harness/tests/run-selftest.sh`, `gates/tools/harness-eval-selftest.sh`, 명시 면제 게이트.
3. DB: 일회용 두 DB에 실제 마이그레이션 적용·선언 비교, 실패 경로는 그대로 실패.
4. 제품 회귀와 E2E는 조사에서 확인한 환경·시나리오와 대상 코드 식별자를 먼저 기록한다.
5. 로컬 성공과 원격 CI·배포 성공을 별개로 보고한다.

## 현재 증거와 대기

- `dev-package/sessions/20260908-product-remaining-audit.md`: 대장 후보별 근거.
- `dev-package/sessions/20260908-product-e2e-environment.md`: 현재 확인된 앱은 운영 staging, 격리 앱 준비 필요.
- `dev-package/sessions/20260908-planning-ci-inputs.md`: 원본 31파일이 로컬에만 있음. 로컬 15블록·4항목 대조 통과.
- `dev-package/sessions/20260908-product-ci-review.md`: 리뷰 지적 이후 wrapper 홈 env 차단·입력 고정·슬롯 검증 반영.
- 연결·CI 정책·격리 환경·기획 판정부 테스트 23개 통과. 원격 CI, 실제 모델 eval, 제품 E2E는 이 결과에 포함하지 않는다.
- 기획 배치 선택은 중복 방지 요청에 맞춰 로컬 원본 검사를 기본으로 진행. 비공개 원본 저장소 선택 시 재조정.
- agent-browser로 현재 소스 Vite의 비인증 로그인 화면·빈 입력 제출 비활성 확인. 백엔드 로그인/저장 검증 아님.

## 후속 실측

- core-api 전체 게이트: 980 passed, 6 deselected(E2E 별도), 실패·skip 0.
- frontend 전체 게이트: 80파일 1,083개 통과.
- 이후 별도 실제 로그인 E2E는 `scripts/e2e-login.sh`로 통과. 합성 계정과 일회용 DB만 사용.
- `_pg.sh`의 no-command exec가 stderr를 영구 폐기하는 문제를 실패 재현 후 수정. `test_pg_stderr.py` 회귀 통과.
- E2E 두 리뷰 지적 반영, `20260908-e2e-login-review.md` 재검토 완료.
- 위 결과는 로컬 검증이며 원격 CI 및 dev 배포 완료 증거가 아니다.
- 격리 작업 사본 CI 정책·기획 판정부·DB 입력·stderr 회귀 10개 통과.

## 다음 묶음

2026-09-09 배포 실측: 서비스 4개 healthy, 웹 96파일 업로드, CloudFront index와 빌드 파일 동일.
사후 doctor 첫 실행은 EC2→CloudFront 연결 reset으로 14/15였으며, 전체 재실행은 15/15·실패0·생략0.
agent-browser로 배포 URL 로그인 화면과 빈 입력 제출 비활성을 확인했다. 이전 이미지 세대는 보존했다.
PR #7 CI는 성공했으나 main CI에서 프로젝트 보기 전환 시험이 비동기 정렬 완료 전에 순서를 읽는 문제가 발견됐다.
첫 행(p1)은 두 정렬에 공통이므로 전체 순서(12·8·5·3건)를 기다리도록 시험을 수정한다. 제품 실행 코드 변경은 없다.
PR #8의 첫 CI에서는 업로드 축척 시험이 팔레트 응답 전에 그리기를 눌러 실패했다. 두 업로드 시험은 팔레트 선택값 준비를 기다리도록 함께 수정한다.

1. S3 정리: 사용자에게 질문한 완료 전송 원장 보관 기간 확정 후, 원장이 아는 미등록 파일만 정리하는 구현·음성 회귀.
2. J-1: `20260908-j1-scope-map.md`의9건/8건 충돌 및 기존 F3 재사용 대응 정리. 묶음 전체 수용 조건을 유지하며 단독 완료로 보고하지 않는다.
3. Google IdP 및 배포 환경 검증은 대장 잔여로 유지. 이번 합성 계정 E2E는 Google 로그인 증거가 아니다.
4. 최종 제품 완료는 새 원격CI와 dev 배포·deploy_doctor15/15 증거를 얻은 뒤 판정한다.
