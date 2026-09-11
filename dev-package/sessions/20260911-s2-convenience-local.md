# Stage 2 편의 기능 — 로컬 구현 검증

대상: HEAD `712a33711f6a222ff7c1d431c4ecef0946508cca` 위 미커밋 작업 트리.
사양/계획: `prd/specs/s2-convenience.md`, `prd/rounds/R-S2-CONVENIENCE.md`.
Google 로그인 제외와 Stage 3 백오피스 계정 추가 우선순위는 유지한다.

## 구현 범위

- 0024 migration: 업로드/데이터셋 격자 프로필, 연구실 기본 격자, 임시 접수 멱등 ID.
- 같은 연구실·같은 형상 격자 후보, 명시적 복제, 교수 전용 기본 지정. 등록 시 활동 1행이며 계보를 만들지 않는다.
- 형식/해시 불일치 비차단 안내, 실제 경계·화소 차이 거리, 예상 영역 네 값, 지도 상태 배지·필터.
- 서버 팔레트와 3~9 구간 조작, 실제 완료 표본 중앙값 ETA, 첫 본체 임시 미리보기와 최종 결과 수렴.
- 폴더 경로 보존·서버 축 판별은 기존 구현을 사용한다. 수용 근거 재대조는 계획에서 추적한다.

## 새 실패 재현과 보완

1. 같은 영역이라도 화소 크기가 다른 격자를 거리 0으로 표시하던 문제: 거리 계산 시험 RED → 2 passed.
2. 격자 복사 중 등록 다음 단계가 열리던 문제: UI 시험 RED → 복사/등록 잠금 구현.
3. 선택 변경 뒤 이전 격자 복사 오류가 새 업로드에 나타나던 문제: 완료된 새 후보 화면에서 RED → 접수 세대별 응답 폐기.
4. 팔레트 목록 개수가 잘못돼도 업로드 화면이 알리지 않던 문제: RED → 받은 목록은 유지하고 오류 안내.
5. 본체 좌표가 있어 외부 격자를 쓰지 않을 때 예상 영역이 외부 격자를 가리키던 문제: 실제 GeoTIFF RED → 본체/COG 좌표 우선.
6. 임시 비지도형 → 최종 지도형을 영역 변화로 알리지 않던 문제: RED → 미관측/좌표 없음/실제 경계를 구별. 재렌더 뒤에도 수렴 알림 한 자리 유지.
7. 등록 전 숨김 클래스가 임시 미리보기까지 감추던 문제: 실제 upload CSS를 적용한 가시성 시험 RED → 임시/최종 수렴 미리보기에서는 숨김 클래스를 해제, 업로드 집중 16 passed.
8. 로컬 격자 복사 도중 쓰기 실패가 나면 불완전한 목적지 파일이 남던 문제: 1 failed/28 passed RED → 실패한 목적지도 정리 대상으로 잡아 29 passed. 원본 바이트 보존 확인. 실제 사용자 파일 삭제는 수행하지 않았다.

## 검증 결과

- Core 서비스: 1,059 passed, skipped 0, deselected 6, 56.12초.
- 불완전 복사 정리 보완 후 최신 Core 서비스: 1,060 passed, skipped 0, deselected 6, 52.92초.
- Pipeline 서비스: 273 passed, skipped 0, deselected 50, 8.02초. 기존 라이브러리·NaN 경고 23건.
- 동일 바이트 타일 재사용 시험 보강 후 최신 Pipeline 서비스: 274 passed, skipped 0, deselected 50, 7.41초, 경고 22건.
- Pipeline 격자 프로필/타일 재사용 집중: 실자료 3갈래 포함 13 passed, 경고 1건. 최초 실행은 원천 환경 선언 누락으로 3 failed/10 passed였고, 정본 시험 환경을 읽은 재실행에서 13 passed. 실패를 생략하지 않는다.
- Viz 실제 RenderResult 경계: 외부 격자/본체 좌표 우선 두 갈래 2 passed. 프로필 시험과 같은 입력 좌표에서 `(124,31,128,34)` 네 값 일치.
- Frontend 업로드 집중: 16 passed. 앞선 격자·스타일·ETA 집중 21 passed. 마지막 타입 게이트 오류 0.
- 최초 전체 frontend: 1,199 passed/1 failed, 94파일, 775.93초. 실행 중 추가된 잠금 RED 시험을 수집했으며 이후 집중 GREEN.
- 후속 전체 frontend: 94파일, 1,204 passed, 실패 0. 이 실행 시작 뒤 추가한 실제 CSS 가시성 보완은 업로드 집중 16 passed 및 격리 브라우저로 별도 검증했다. 전체 최종 트리 증거는 Stage 1·2 전수에서 갱신한다.
- 가시성 보완 후 frontend-typecheck 재실행: src/test 오류 0, exit 0.
- 0024 drift, 계약·생성물·DB outbox 집중은 앞선 실행에서 통과했으며 최종 경계 게이트를 다시 대조한다.

## 실제 브라우저

`agent-browser` doctor: 9 pass/0 warn/0 fail. URL `http://127.0.0.1:43173`, 일회용 DB/연구원/로컬 저장소.
기존 `scripts/e2e-login.sh --upload`로 실제 GeoTIFF 업로드·분석·등록, 설명 누락 거절,
새로고침 후 이름/설명/파일명/미리보기 유지, 로그인 거절·성공·재접속·로그아웃을 확인했다.
테스트 앱·브라우저·DB·임시 파일은 runner가 정리했다. 기존 staging 스택 변경 0.

확장 `scripts/s2-grid-journey.py`는 직접 격자 → 재사용 → 실제 DB digest/영역/활동/계보 → 목록 필터를 검사한다.
최초 실행은 Python 경로의 symlink를 해석해 venv 밖 인터프리터가 선택되면서 numpy 부재로 준비되지 못했다.
인터프리터 경로를 venv 안에 유지하도록 시험 runner를 고쳤다. 이후 등록 입력 단계 진입 전 숨겨진 후보를 기다리던 순서와 한글 aria-label을 JSON Unicode escape로 CSS에 전달하던 선택자 오류를 수정했다. 후보 DB 프로필은 정상이며 후보 누락 제품 결함으로 판정하지 않는다.

최종 실행 exit 0: 직접 격자 등록, 기존 격자 가져오기·등록, 두 데이터셋 새로고침 후 이미지 표시,
실제 DB의 동일 digest/좌표 `(124,31,128,34)`/지도 상태, 재사용 활동 정확히 1건·계보 edge 0건,
카탈로그 지도 상태 필터 포함/제외, 로그인·세션·로그아웃 모두 통과했다.
증거: `.codex/artifacts/s2-grid-journey-20260911/journey.json`, `candidate-screen.txt`, `dataset-1.png`, `dataset-2.png`.
이전 실패를 최종 성공에 산입하지 않는다. 실제 S3 첫 파일 전송 E2E는 이 로컬 여정에 포함하지 않았다.

## 남은 조건과 승인

- 최종 트리의 전체 frontend와 계약/DB/import/planning 경계 및 서비스 전수 판정.
- Stage 1·2 전체 검증, 운영 회차의 실제 배포·무인 trigger·알람·회수 관측.
- main push, staging/dev 배포, Terraform 원격 apply, 실제 S3/캐시 삭제는 아직 실행하지 않았다.
- 로컬 구현과 배포 완료를 구분한다. staging green 전까지 J-1은 partial이다.
