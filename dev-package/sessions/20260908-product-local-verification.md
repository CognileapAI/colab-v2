# 제품 마감 로컬 검증 — 2026-09-08

base `ccf76ec`. 격리 브랜치 `lane/product-finish`에서 구현·검증 후 다른 하네스 작업이 idle임을 확인하고 원래 체크아웃에 반영했다.
원래 체크아웃의 기존 수정은 보존했고 제품 대상 guard와 git apply --check를 통과했다. 커밋·push·배포는 하지 않았다.

## X-7 — 시험 대상 선택의 비결정성

원인은 제품 접근 정책이나 시크릿이 아니라 `SELECT id FROM d3_dataset LIMIT 1`이었다.
공개 DSA1과 잠긴 DSA2를 구분하지 않고 첫 행을 골랐으므로 DB 물리 순서가 바뀌면 같은 시험의 결과가 달랐다.
기존 재현 기록은 `sessions/p3-axes-schema-20260907.md` 86행과104행에 있다.
로컬·CI의 서로 다른 실행 이력/행 배치가 원인이며 시크릿 추가나 필터 축소로 해결하지 않았다.

- RED: 기존 임의 선택을 유지한 상태에서 공개202/잠김403 두 경우를 명시하면 잠김 case가202로 실패(1 failed,3 passed).
- 수정: 기존 conftest의 DS_A1/DS_A2를 직접 사용. 서비스 토큰 검사와 접근 거절은 유지.
- GREEN: 인증 중계+본체 접근 시험10개 통과.
- 전체 실제 일회용DB `service-tests-core-api`: 981 passed,6 deselected,skip/failed/errors0,166.76초.
- 기존 main CI34216692424가 green인 것은 수정 전 결과다. 수정 후 원격CI는 미실행이므로 X-7 최종 완료로 승격하지 않는다.

## BF-13 — 세 화면 토큰 드리프트

`catalog.css`·`detail.css`·`project.css`의 원문을 Vite `?raw`로 읽는다. `node:fs` 사용0.
정적 실측 공통 이름16개, 현재 값 충돌0개. 화면 CSS값과 토큰 위치는 변경하지 않았다.
셸이 쓰는 토큰만 올린다는 기존 `shell/tokens.css` 기준에 따라 화면 로컬을 유지한다.

- 원문/실제 선언/공통 선언이 비었으면 실패하도록 입력 검증.
- 각 공통 이름의 한쪽 값을 변이하면 그 이름의 불일치를 검출.
- 빈 검출 구현에서 변이 시험 실패를 재현한 뒤 비교 구현.
- 리뷰에서 유효한 마지막 선언의 세미콜론 생략 누락 발견. 해당 fixture RED(1fail/3pass) 후 파서 보완,4개 GREEN.
- 기존 프로젝트·상세·카탈로그와 토큰 시험7파일120개 통과(위 최종 음성 fixture 추가 전 실행). 최종 토큰4개 별도 통과.
- TypeScript `tsc --noEmit` 통과. CSS 시각 값·레이아웃 변경0.
- 대장 BF-11 선행 수용 및 최종 통합 검증과 별개로 로컬 구현 증거를 기록한다.

## E2E 및 CI 준비

- 실제 agent-browser 로그인·GeoTIFF 처리·등록·상세reload·이미지로드·로그아웃: `20260908-product-browser-e2e.md`.
- 전체 frontend 기존1083개 통과 후 이번 추가 검사와 관련120개/최종4개 통과.
- CI 준비 수정: 면제 eval의 API키 의존 제거, 러너7/게이트4 selftest 통과,20개 모델 과제 미실행을 명시.
- 실제 두 DB upgrade head + schema-diff 통과. 로컬 기획 원본15블록·applied4항목 대조 통과.
- 격리 CI 정책·DB 입력·기획 판정부·stderr 회귀10개 통과.
- `_pg.sh` slot획득이 stderr를 영구 폐기하던 문제를 실패 재현 후 수정.
- 루트 통합 후 Python 회귀38개 수집:35개 통과, Windows전용3개 WSL에서 skip. 연결 검사4역할/12스킬/9훅 green.
- 대장/03-HANDOFF의 BF-13 상태를 근거와 함께 동기화. work-item-consistency green(산문 불일치0, 기존 파싱대상밖9건은 출력에 명시).
- 원래 frontend `npm run build` 통과. 기존 크기 경고(JS bundle 약660kB)는 남아 있으며 빌드 실패가 아니다.

## 최종 완료까지 남은 조건

원격 CI, dev 배포 green 및 deploy_doctor15/15 단일실행 증거는 아직 없다.
S3 완료 전송 원장 보관 기간은 사용자 응답 대기. 기존 파일/등록 데이터셋 보관 기간과 구분한다.
J-1의9건/8건 범위 대응, Google IdP, TL-2의 배포 후 회수 관측 등은 대장에 남아 있다.
