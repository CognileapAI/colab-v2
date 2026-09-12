# 디자인 수정 검증

현재 상태: 승인된 로컬 수정 범위 완료. 필수 게이트 4개 green / 판정 실패 0 / 준비 실패 0.

- frontend-typecheck: 오류 0.
- frontend-test: 95파일, 1,209건 통과, 실패 0. 최종 실행은 VITEST_MAX_WORKERS=12이며 검사 대상을 줄이지 않았다.
- frontend-fixture-reach: 운영 진입점 도달 181개, 금지 fixture 모듈 도달 0.
- frontend-visual: 11페이지, 라이트/다크 선호 스크린샷 22장, 작은 글자/낮은 대비 0, 허용 목록 0.
- verify-report: 현재 파일 hash와 작업별 게이트 증거의 일치 확인.
- [화면 모음](gallery.html) · [게이트 원본](gate-summary.json) · [키보드 검증](keyboard.json) · [요청/취소/정보 편집 모달 검증](manual/dialog-checks.json).

최종 mobile 규칙 보완 후 14개 모바일 장면을 전부 재계측했다. 입력칸은 모두 16px 이상이다(manual/mobile-inputs.json).
태블릿/데스크톱에는 해당 max-width:640px 규칙이 적용되지 않으며, 정식 visual 게이트도 최종 소스로 다시 통과했다.
키보드 구현은 이 마지막 CSS 보완에서 변경하지 않았다.

## 변경과 수용 범위

| 검수 항목 | 수정 |
|---|---|
| D01–D03 글꼴·필터·홈 버튼 | native control 글꼴 상속, 필터 4개 한 묶음, 버튼 38px·명시적 여백, 읽기 글자 13px 이상 |
| D04–D06 모달·설정·기간 | 설정 페이지 여백, 모달 본문/하단 간격, 모바일 날짜 칸 min-width 보정 |
| D07–D09 그림 선택·로그인·레이어 | 파일 input은 시각적으로 숨기되 키보드 접근 유지, 로그인 grid 축소, 모달을 GNB 위로 배치 |
| D10·D16 키보드 | 연구실 정보 조회/편집, 프로젝트 생성/닫기, 접근 요청/승인 취소 6개 모달 포커스 순환·Escape·복귀. 저장 중 닫기 차단. 잠긴 행도 버튼으로 상세 진입 |
| D11–D15 읽기·상태 스타일 | 작은 본문 승격, 기존 회색 토큰으로 대비 개선, 승인·지도 안내·빈 상태·없는 페이지 스타일 보완 |
| D18–D20 공통 기준 | 수정한 화면의 중복 fallback 일부를 정본 토큰으로 연결, reduced-motion 전환 제거, 카드 그림자·음수 여백 보정 |
| D21·D24 좁은 화면 | 홈 지표 2열, 최근 기록 제목/메타데이터 재배치, 빈 안내 문장 줄바꿈 |

D17 전역 CSS 소유권 재편은 영향 범위가 커 제외했다. D18 나머지 fallback 참조 41회는 정의 누락으로 CSS가 무효인 상황이 아니며, 후속 구조 정리 후보로 남긴다.
D22·D23의 모든 실서비스 권한/업로드/미리보기 성공·실패 상태를 검증했다고 주장하지 않는다. D30 새 다크 테마는 구현하지 않았다.

## 증거 구분

- 화면은 현재 소스의 실제 React 컴포넌트 + 명시적 fixture 응답이다. 개발/운영 API 호출과 저장은 차단했다.
- 기존 라이브 감사 보고서와 사용자 첨부는 수정 전 근거다. 최종 근거는 이 디렉터리의 manual 및 frontend-visual이다.
- WSL 파일 감지가 최신 변경을 반영하지 않는 것을 확인해 소유한 로컬 Vite 서버만 재기동했다.
- served-css.json: 현재 로드된 스타일 16개 대조. 14개 원문 일치, 2개는 @import 확장·공백 정규화 후 일치(tokens.css 포함).
- 이전 시도에서 잘못 남은 캡처 이름이나 실패/중단 결과는 최종 합격으로 합산하지 않았다.
- 모달 테스트 RED 3건 → GREEN. 추가 중첩/제거된 트리거 사례 포함 5건 통과. 편집 모달은 브라우저에서 열린 채 Tab→BODY RED 확인 후 수정했다.
- 별도 브랜치 codex/design-style-repair. 커밋·push·배포 없음. 기존 다른 작업의 변경은 보존했다.

## 정적 계측

CSS의 13px 미만 선언 58 → 2(남은 2개는 정렬 화살표), 음수 margin 1 → 0.
미정의 변수 참조 64 → 41, 모두 기존 fallback이 있어 무효 선언은 아니다. 세부 결과는 css-audit.json/md.

## 최종 실제 화면

42개 장면(375/768/1440px)의 페이지 가로 넘침, 13px 미만 읽기 글자, 4.5 미만 대비 모두 0.
표/계보 그래프 내부의 의도된 가로 스크롤은 허용했다.

| 장면 | 너비 | 가로 넘침 | 작은 글자 | 낮은 대비 | 화면 |
|---|---:|---:|---:|---:|---|
| access-dialog-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/access-dialog-1440.png) |
| access-dialog-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/access-dialog-375.png) |
| access-dialog-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/access-dialog-768.png) |
| approval-dialog-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/approval-dialog-1440.png) |
| approval-dialog-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/approval-dialog-375.png) |
| approval-dialog-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/approval-dialog-768.png) |
| catalog-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/catalog-1440.png) |
| catalog-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/catalog-375.png) |
| catalog-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/catalog-768.png) |
| detail-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/detail-1440.png) |
| detail-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/detail-375.png) |
| detail-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/detail-768.png) |
| empty-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/empty-1440.png) |
| empty-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/empty-375.png) |
| empty-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/empty-768.png) |
| lab-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/lab-1440.png) |
| lab-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/lab-375.png) |
| lab-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/lab-768.png) |
| lab-dialog-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/lab-dialog-1440.png) |
| lab-dialog-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/lab-dialog-375.png) |
| lab-dialog-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/lab-dialog-768.png) |
| login-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/login-1440.png) |
| login-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/login-375.png) |
| login-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/login-768.png) |
| pending-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/pending-1440.png) |
| pending-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/pending-375.png) |
| pending-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/pending-768.png) |
| project-close-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/project-close-1440.png) |
| project-close-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/project-close-375.png) |
| project-close-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/project-close-768.png) |
| project-dialog-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/project-dialog-1440.png) |
| project-dialog-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/project-dialog-375.png) |
| project-dialog-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/project-dialog-768.png) |
| projects-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/projects-1440.png) |
| projects-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/projects-375.png) |
| projects-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/projects-768.png) |
| settings-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/settings-1440.png) |
| settings-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/settings-375.png) |
| settings-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/settings-768.png) |
| settings-dialog-1440 | 1440 | 0 | 0 | 0 | [PNG](manual/live/settings-dialog-1440.png) |
| settings-dialog-375 | 375 | 0 | 0 | 0 | [PNG](manual/live/settings-dialog-375.png) |
| settings-dialog-768 | 768 | 0 | 0 | 0 | [PNG](manual/live/settings-dialog-768.png) |

## 요청 대조와 인계

사용자가 승인한 폰트·누락 스타일·여백·모바일 잘림 및 검수표의 직접 결함 수정 범위에서 미달 0, 기능 범위 초과 0.
모바일 검색창과 로그인 입력 크기, 승인 메뉴 정렬, 정보 편집 모달은 같은 디자인/접근성 결함을 실제 검증 중 확인해 함께 보완했다.
D17의 구조 재편과 D18의 남은 fallback 통합은 사양에 명시한 제외/후속 후보다. 모든 서비스 상태의 라이브 E2E 합격이나 새 다크 테마 완성을 뜻하지 않는다.

독립 코드 검토에서 프로젝트 pending 색 덮어쓰기와 연구실 정보 편집 모달 누락을 지적받아 모두 수정했고, 두 파일 재검토 결과 approve였다.
프로젝트 카드의 기존 회귀 테스트가 box-shadow 선언을 기대한 문제는 테스트를 삭제하지 않고 `box-shadow: none`으로 무그림자 의도를 명시해 해소했다.

배포·push·제품 데이터 저장은 수행하지 않았다. 로컬 화면/fixture 근거이며, 정식 서비스에 배포된 상태로 보고하지 않는다.
보고서 커밋 조건의 적용 예외와 기존 변경 보존은 실행 계획에 기록했다. 최종 source 검증을 위한 임의 커밋은 만들지 않았다.
