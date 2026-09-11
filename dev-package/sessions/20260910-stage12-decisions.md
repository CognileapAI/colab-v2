# Stage 1·2 범위 확정과 Stage 3 우선순위 — 2026-09-10

## 사용자 원문

> 1. 권고대로 하고 해결했으니 빼자.(a)  -> b 안은 github 이슈작성 (신규)
> 2. a 안으로가자
> 3. a 안으로가자
> 4. a 로 가자
> 5. a로 하자  - b안은 github 이슈로 작성(신규)
> 6. 로그인은 만들지 않고 github 이슈로 작성 (신규)
> 7. a안
>
> 구글로그인은 빼고 우리가 백오피스화면을 만들어서 메일 계정을 직접 추가해주려고 한다. 이건 stage3의 최우선 개발로 하자

## 확정값과 반영

- Q1: 기존 해안선·국경 배경과 커서 좌표 수용. BF-10 격자선 자체는 미구현 deferred, Stage 1·2 필수 범위 제외. 화면+PNG 동일 격자선·눈금 후속 [#10](https://github.com/CognileapAI/colab-v2/issues/10).
- Q2: 완료 전송 메타 원장 completed_at 기준 7일 보관. 원본 파일 TTL이 아니며 등록 업로드 보존. 실제 삭제는 대상 목록 확인 후 별도 승인.
- Q3: S3 직접 전송·72시간 재개·접수 완료 처리, 파일 목록·폴더·200 다운로드 티켓·본체 관리·본체 변경 시 수정 시각 갱신의 현행 제품 계약 승인. U-1/F-3의 승인 대기는 해소하되 최신 시험·dev 배포 확인 전 partial 유지.
- Q4: core-viz 연구실·계정 경계 헤더 필수, 경계 부재 HTTP 400, ScreenshotRequest.layers 최대 8의 실측 계약 가산 승인. 과거 오류 코드 일괄 추가 승인 아님.
- Q5: dev 현행 로그인 제한(자격/클라이언트 각각 5회/15분, 성공 시 초기화, 프로세스 메모리) 수용. 배포 후 전달 IP·여섯 번째 실패 429 재검증. 공유 제한은 다중 서버·prod 전에 해결할 후속 [#11](https://github.com/CognileapAI/colab-v2/issues/11).
- Q6: Google 로그인 이번 개발 제외, PA-G deferred 및 종전 자동 개시 기한 해제. 후속 [#12](https://github.com/CognileapAI/colab-v2/issues/12), 실행 일정 미정. 기존 로그인·비밀번호 발급 경로 제거는 승인 범위가 아님.
- Stage 3: BO-1 운영자 백오피스에서 이메일 식별 서비스 계정을 직접 추가하는 기능 최우선. 메일함 생성 요구로 확대하지 않음. 계정 발급 방식·권한·연구실 소속·기존 계정 처리와 최종 완료 정의는 별도 설계 대상.
- Q7: 로컬 구현·시험·문서화 연속 진행. main push·staging/dev 배포·실제 데이터/S3/캐시 삭제는 각각 구체적인 결과·대상 제시 뒤 실행 직전 승인.

## 계획·검증 범위

- 정본: `dev-package/work-items.yaml`; 실행 순서 `dev-package/prd/rounds/R-STAGE1-STAGE2-CLOSEOUT.md`; 사양 `dev-package/prd/specs/stage1-stage2-closeout.md`.
- 이번 산출은 사용자 결정 기록·계획·대장 반영이다. 제품 코드 구현·시험·배포 완료를 주장하지 않는다.
- BF-10·PA-G 상태만 open→deferred; 기존 완료 138건 유지. Stage 1 비연기 미완 9/연기 1, Stage 2 비연기 미완 9/연기 2. after_stage2는 BO-1 추가로 16건.
- 자식 라운드의 구체적 실행 사양·실패 시험은 착수 단계에서 작성한다. 전체 상세 사양 완성 주장은 하지 않는다.
- 다음: R-S12-VERIFY에서 재검증 9건과 U-1/F-3 시험·dev 배포 증거 대조. Stage 3 미확정 상세는 Stage 1·2 차단 조건이 아니다.
- 문서 관련 게이트 보고 경로: `dev-package/reports/stage12-decisions/docs/gate-summary.json` (실제 판정·계수는 보고서 참조).

## PLAN-SoT 등재 인계

새 결정 번호를 이 작업자가 예약하지 않는다. 부모 오케스트레이터가 병합 직전 정본 최대 번호를 확인해 본 사용자 원문과 위 확정값을 가리키는 등재문을 추가한다. 이번 문서 반영 자체는 커밋·main push·배포 승인이 아니다.
