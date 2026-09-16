> spec: dev-package/prd/specs/admin-role-scope.md
# 관리자 역할·연구실 범위 구현 계획

**Goal:** 시스템 관리자 전체 권한·교수 자기 연구실 전체 관리·정확한 권한 안내를 기존 데이터 보존 조건으로 구현한다.
**Architecture:** 기존 인증 주체·연구실 스코프·RLS·접근 Port를 재사용한다. 기존 객체는 서버에서 대상 연구실을 확인하고 신규 생성만 연구실을 선택한다.
**Tech Stack:** Python/FastAPI/SQLAlchemy/PostgreSQL/Alembic, React/TypeScript/OpenAPI.
**Spec:** `dev-package/prd/specs/admin-role-scope.md`.

## 제약과 실행
- intent 승인: 2026-09-16 「고고」. 배포·원격 계정 변경·커밋·PR 게시 없음.
- 단일 쓰기 주체. 자동 격리 도구가 없는 세션에서는 같은 사본의 쓰기 작업을 직렬로 수행하며 부모는 작업자 집행 중 읽기/검토만 한다.
- 기존 데이터·연구실 소속·계보·일반 구성원 제한 유지. 실제 운영 데이터 시험 금지.
- 모든 구현은 관련 실패 시험부터 시작한다. 검증 결과는 task runtime 또는 명시 실행 로그에 기록한다.

## 1. 승인·설계
- [x] intent 승인과 정책 답변 기록.
- [x] spec·계획 작성.
- [x] advisor 계획 검토: 권한 회수 후 기존 티켓/미리보기 작업 재인가 누락 지적을 spec과 시험 범위에 반영.

## 2. 서버 권한·대상 연구실
파일: `services/core-api/src/colab_core/app/deps.py`, `kernel/scope.py`, `domains/d2_access.py`, `app/routes/identity.py`, 대상별 기존 라우트/Port, `db/platform/schema.sql`, 새 platform migration, `contracts/seams/fe-core.yaml`.
- [x] 관리자 타 연구실 변경/교수 비공개 관리/일반 사용자 위조 거절 RED 확인 후 구현.
- [x] 기존 객체의 대상 연구실을 확인하는 요청 스코프와 신규 생성 선택 계약 구현. 실제 actor 유지.
- [x] 관리자 permission/action 및 교수 body_access, RLS 본체 정책 일치.
- [x] 미리보기 생성/조회/값조회/스크린샷과 다운로드 티켓에 대상 스코프 유지, 소비 시 권한 재검사.
- [x] 소속 없는 관리자 생성·소속 관리자 타 연구실·잘못된 대상·다른 연구실 참조 거절 시험 GREEN.

## 3. 화면·조회 실패
파일: `frontend/src/permission/`, `shell/Gnb.tsx`, `routes/DatasetDetailPage.tsx`, `components/datasetpreview/`, `components/upload/`, `components/project/`, 계정 관리 화면, 관련 `frontend/test/`.
- [x] describe 403→안내→재시도 성공과 관리자/교수 역할 표시·신규 대상 연구실 선택 시험 RED.
- [x] 읽기 전용 가정을 제거하고 서버 권한으로 관리 동작 표시. 교수 표기는 교수 관리자로 변경.
- [x] 시스템 관리자 신규등록에만 연구실 선택. 작업 문맥은 모달/요청에 결속하고 다른 탭·연구실로 새지 않게 함.
- [x] 미리보기 실패 상태/재시도 및 공개 범위 관리자 접근 안내 구현.
- [x] 프런트 전체 시험·타입 검사 GREEN.

## 4. 기존 계정 전환 준비
파일: 기존 계정 관리 kernel/ops와 해당 시험, 로컬 사용자용 적용 설명.
- [x] 실제 동작을 수행하지 않는 목록 준비와 입력 오류·목록 중첩·마지막 관리자 보호 시험 RED.
- [x] 목록에 결속한 교수 겸직 권한 회수와 세션 무효화·멱등성 구현, 격리 DB에서 GREEN.
- [x] 교수 역할·데이터·소속 유지 검증. 실제 DEV 적용은 미실행. 사용자 절차: `docs/development/admin-role-transition.md`.

## 5. 통합·검증·인계
- [x] 계약 생성기로 타입 갱신 및 계약 게이트.
- [x] 서비스·프런트·스키마·RLS·관련 정합 게이트, 실제 계수 회수.
- [x] 로컬 격리 환경 agent-browser: 관리자 기존자료 미리보기/수정→재조회, 신규자료 연구실 선택, 교수 비공개 관리, 일반계정 거절.
- [x] advisor 수용 검토 및 intent 항목별 미달·초과 대조.
- [x] 로컬 PR 요약·계정 전환/배포 절차·검증 제한 인계. 배포 완료를 주장하지 않음.

## 현재 상태
- 서버 인계: core 1360/1360 통과, skip 0·deselect 6, 종료 0; 핵심 14건 저병렬 통과, viz 관련 19건 통과. 로그 `/tmp/admin-core-handoff.log`, `/tmp/admin-final-focused4.log`, `/tmp/admin-viz-focused.log`. 서버 작업자의 쓰기 종료를 확인했다. 전체 통합 검증은 후속 변경 뒤 새로 실행한다.
- advisor 중간 검토의 교차 연구실 격자/구성원 참조 누락을 보완했다. 대상 확정 뒤 전역 SELECT를 끄는 구조로 추가 보완하고 재검증했다.
- 계정 전환과 후속 서버 보완 인계: core 1381/1381 통과, skip 0·deselect 6, 종료 0; 핵심 21건 직렬 통과. 로그 `/tmp/operator-transition-core-gate.log`, `/tmp/operator-transition-final-serial.log`. 실제 관리자 생성과 전환의 잠금 공유·중간 실패 전체 롤백·멱등 적용을 확인했다.
- advisor가 발견한 외랩 관리자 계정 INNER JOIN에 따른 등록/계보 조회 누락은 실DB에서 RED를 확인하고 LEFT JOIN·원본 actor ID 보존으로 보완했다. 무소속/타랩 관리자 등록 뒤 대상 교수 재조회·계보 재조회가 통과했다. advisor 재검토 승인. 옛 정책 시험 주석도 갱신했다.
- 프런트·브라우저 구현 완료. 후속 검토에서 미등록 미리보기 403 안내 누락을 발견해 5개 RED→GREEN 시험으로 보완했다. 계약 승인 인용 누락과 viz 응답의 새 target 필드를 반영한 시험도 보완했다. 부모의 최종 변경 부분 게이트 재실행과 배포 빌드까지 완료했다. DEV 전환·배포·커밋은 하지 않았다.
- DEV 테스트 계정 인증은 앞선 조사에서 실패했다. 실사용 검증은 새로 준비한 격리 로컬 환경으로 수행한다.


## 최종 수용 근거 (2026-09-17)
- 부모 직접 재실행: core-api 1381/1381, skip 0·deselect 6; migration-drift platform 25 + AI 3 = 28/28; schema-diff 양 체인 일치; migration-single-head·rls-coverage·rls-effect·rls-effect-selftest·import-boundary·banned-import·work-item-consistency 통과. 각 게이트 종료 0, green 1 / 판정실패 0 / 준비실패 0. 각각 독립 실행이며 하나의 task 실행으로 합산하지 않는다.
- RLS selftest 23개: 교수 예외 제거·시스템 예외 제거·모든 사용자 확대 변형을 각각 거절한다. 작업자 저병렬 2와 부모 실행에서 확인했다.
- 부모의 최종 변경 후 직접 재실행: 프런트 1538/1538·타입 오류 0·생성물 13개 일치·계약 lint/breaking/seam-consistency 통과·viz 542/542(skip 0·deselect 42). 프런트 배포 빌드 종료 0. 번들 크기 500kB 초과 경고와 viz NumPy deprecation 경고는 남아 있으나 실패는 없다.
- 실제 브라우저: `/tmp/admin-role-browser/admin-journey.json`, `/tmp/admin-role-browser/journey.json`, `/tmp/admin-role-browser-run.log`. B 연구실 선택→GeoTIFF 업로드→닫기/새로고침/등록 재개→등록→미리보기 이미지→수정/재조회, 관리자 회수 후 옛 세션 거절/재로그인, 교수 비공개 관리, 일반 본문/다운로드 거절 모두 종료 0. 부모가 결과 JSON과 미리보기/거절 화면을 직접 확인했다.
- 브라우저 이후 변경은 기존 미등록 미리보기 오류 문구·계약 산문/생성 타입 주석·viz 응답 시험이다. 403 다섯 경로는 HTTP source 회귀시험으로 검증했다. 브라우저 당시 계약 hash와 최종 계약 hash가 같다고 주장하지 않는다.
- 일반 구성원은 기존 업로드/편집 권한에 따라 비공개 자료의 메타데이터 편집이 가능하다. 이번 변경은 본문·미리보기·다운로드 제한을 유지하며 이 기존 정책을 새로 축소하지 않았다.
- advisor 수용: 대상 연구실 결속·자료 보존·계정 전환 잠금/롤백·RLS 오라클·최종 403 보완 승인. 검토 범위의 미달·초과 없음.
- 로컬 PR 본문·사용자 게시 절차: `docs/development/admin-role-scope-pr.md`. 실제 계정 전환 절차: `docs/development/admin-role-transition.md`.

## intent 항목별 대조
| proposed outcome 순서 | 구현·검증 근거 |
|---|---|
| 1. 시스템 관리자 전체 권한 | 서버 대상 범위·권한 스위치·본문 RLS·관리자 API 회귀시험, 타 연구실 브라우저 여정 |
| 2. 교수 관리자 자기 연구실 전체 관리 | professor manager 정책·본문 RLS·자기/타 연구실 API 시험, 비공개 수정 브라우저 |
| 3. 기존 교수 자격만 회수 | 전환 도구가 operator 자격만 회수; 역할·소속·비밀번호·자료 보존 시험. 실환경 적용은 사용자 단계 |
| 4. 실제 목록·세션·멱등·최소 관리자 | list/prepare/apply, snapshot 대조·옛 세션 거절·재실행·마지막 관리자 시험 |
| 5. 유지/회수 근거·중첩/불명확 거절 | 모든 현재 operator 정확한 분류·이유 필수·목록 오류 거절 시험 |
| 6. 두 관리자 표시와 원본 분리 | 계정/구성원 화면 표기, 교수 role과 service_operator 별도 유지 |
| 7. 기존 객체 실제 연구실·행위자 | 서버 객체 해석·target scope·감사 actor, 외랩 등록 뒤 교수 재조회/계보 시험 |
| 8. 신규 생성 연구실 선택·저장 | 모달 지역 상태·서버 헤더 검증·재개 labId; B 연구실 저장/새로고침 브라우저 |
| 9. 읽기 전용 가정 제거·계층 일치 | 화면 권한 gate·서버·RLS·viz target 일치, 관련 전체 시험 |
| 10. 권한 오류 구분·재시도 | describe 오류/재시도 및 HTTP403 다섯 경로 시험, 일반 구성원 잠김 화면 |
| 11. 기존 자료 보존 | populated 0032→0033→0032 전체 데이터 dump 동일, 연결·소속·actor 회귀시험; DEV 적용은 사용자 단계 |
| 12. 일반 구성원 제한·관리자 접근 고지 | ordinary 경계·현재 권한 재검사·공개 범위 안내 시험, 브라우저 본문 거절 |
| 13. 무소속/소속 관리자·브라우저 | 두 관리자 API/컴포넌트 시험, 소속 관리자 실제 브라우저 여정 |
| 14. 교수 범위·전환 후 세션·자료 | 교수 자기/타 연구실·계정 관리 거절 시험, 전환 DB 시험과 브라우저 재로그인 |

승인된 **구현·로컬 검증·사용자 배포 준비 범위**의 미달 0건·초과 0건.
실제 DEV 적용과 원래 NetCDF 재검증은 사용자 배포 뒤 진입조건이며, 구현 완료를 적용 완료로 해석하지 않는다.
실제 S3 이어올리기는 이번 로컬 브라우저 증거에 포함되지 않는다. 원본 미리보기 이슈 #42는 닫지 않았다.

최종 개별 게이트 17종은 각각 종료 0·green 1 / 판정실패 0 / 준비실패 0이다. 원시 로그·개별 JSON·브라우저 증거·최종 변경 파일 SHA256은 로컬 Git common 디렉터리의 `colab-local-evidence/admin-role-scope-20260917/`에 보존한다. 원시 게이트 JSON의 HEAD tree는 미커밋 내용 hash가 아니며, 별도 `source-sha256.json`이 최종 파일 내용을 기록한다. 이 폴더는 로컬 증거이며 커밋/원격 게시 산출물이 아니다.
