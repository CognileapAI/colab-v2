# Stage 1·2 dev 최종 확인 — 2026-09-11

## 목적과 범위

- 사용자 목적: Stage 1·2의 `deferred` 제외 미완료를 0건으로 만든다.
- 이 레인: 이미 구현·배포된 BF-7/BF-8/BF-9/BF-11/BF-13/U-1/F-3을 완료 정의와 일대일로 dev에서 확인한다. 제품 코드·대장·DB DDL·배포·원본 삭제는 바꾸지 않는다.
- BF-12는 별도 격리 구현 레인이 진행 중이며, BF-12 dev 첫 주기 실로그가 서기 전 TL-2를 닫지 않는다.
- I-3/I-4의 실제 cron·판정 실패 유도·외부 통지는 기존 제외 작업이므로 구체 실행안과 승인 범위를 별도로 제시한다.

## 배포 기준과 공통 진단

- 로컬 및 `origin/main`: `a2fd7e8fd0d6c190182d9f59ffec72d8fe5a087c`.
- dev: `CURRENT_SHA=9e3ff19f6d27`, `MAIN_SHA=main=9e3ff19f6d27 candidate=9e3ff19f6d27 ancestor=yes`; 앱 컨테이너 4개 모두 healthy.
- 두 SHA의 제품 경로 차이는 `frontend/src/auth/login.css` 한 줄뿐이며 이 레인의 7개 항목 구현에는 차이가 없다.
- 새 baseline doctor: exit 0, **15 green / 0 판정 red / 0 준비 red**. 증거: `.codex/artifacts/stage12-final-verification/dev-doctor.log`.

## 완료 정의 수용 행렬

| 항목 | 완료 정의와 실제 확인 | 현재 판정 |
|---|---|---|
| BF-7 | dev 합성 dataset 미리보기에서 서버 `POST /api/v1/preview-screenshots` 200. 반환 PNG Blob 5,848바이트, 다운로드 앵커는 DOM 부착 상태로 클릭됐고 revoke는 클릭 약 4,000ms 뒤 발생 | dev 실증 충족. Firefox 재확인은 대장 note대로 별도 |
| BF-8 | S-01 계산값 padding 24/20/40/20px, max-width 1200px. hero 680px, hero 중심과 page content 중심 모두 632.5px로 이중 오프셋 0 | dev 실증 충족 |
| BF-9 | 기존 dev dataset `01M1SCCM…`에서 API 노드 3·edge 2. 원천→루트 edge의 `method=null`; 화면 `.lin-arw` 2개이며 원천 화살표 라벨 없음 | dev 실증 충족 |
| BF-11 | 토큰 정합·폐기 별칭 음성 fixture·공용 backlink 및 project/detail/catalog 회귀: 5파일 116시험 green. dev 상세 backlink 계산값은 `display:flex`, 색 `rgb(86,92,99)`, padding `3px 9px 3px 0`, radius 8px, 13px | 정적 완료 정의 충족. 다섯 색 변경 자리의 dev 실화면 전수 눈 확인은 미실행 |
| BF-13 | 세 raw CSS 공통 선언·값 동일·세미콜론 생략 음성·각 공통 토큰 변조 음성: 1파일 4시험 green | 구현 완료 정의 충족 |
| U-1 | 새 20MiB TEST 본체를 8MiB×2+4MiB, 3파트로 계획. part1 PUT 200 뒤 재조회 `uploadedParts=[1]`; 조기 완결 409. part2/3 PUT 200, 파일 완결 200/`올라감`, 전송 완결 201, 같은 ULID와 20,971,520B 접수 | dev 실증 충족 |
| F-3 | 합성 dataset 파일 목록 본체 640B. 단건 티켓·바이트 200, 640B SHA 원본 일치. 묶음 200, ZIP 832B/PK. TEST 파일 추가 201·경로 `TEST/folder/…` 정규화 및 재조회, 교체 200·크기/이름 갱신·경로 보존, 추가분 삭제 204·재조회 소멸, 마지막 원본 삭제 409·원본 존속 | dev 실증 충족 |

## BF-11 남은 의미 판정

- `--color-success-100: #cde9d6`는 기존 폴백 값에 이름을 붙인 화면 로컬 토큰이다. 저장소와 제공된 정본에서 이 값에 대응하는 다른 토큰 이름은 발견되지 않았다. 값 변경 없이 로컬에 둔 현재 구현은 BF-13의 「공통 토큰만 값 일치」 정책과 충돌하지 않는다.
- `preview.css`의 `.preview-page .backrow/.backlink`는 상세·프로젝트의 공용 규칙과 치수·색·hover가 다른 별개 화면 디자인이다. BF-11 완료 정의는 `detail.css`·`project.css` 두 사본의 공용화이며 preview 사본 통합을 요구하지 않는다.

## 실행 중 한계

- BF-7의 버튼 경로는 서버 응답·Blob·부착 클릭·지연 revoke까지 확인했지만, `agent-browser download` 명령은 30초 동안 지정 파일을 만들지 못했다. 브라우저 디스크의 실제 PNG 파일 signature·크기는 확인하지 못했으므로 이 한 조건을 미실행으로 남긴다.
- 선언 게이트 `frontend-test`·`frontend-typecheck`·`core-api-test`의 단일 task 실행은 부모의 즉시 인계 요청에 따라 frontend-test 실행 중 중단했다(exit 130). `gate-summary.json`은 생성되지 않았고 이를 green으로 세지 않는다. 독립 최신 좁은 시험은 BF-11 관련 116/116, BF-13 4/4이다.

## 독립 후속과 승인 경계

- BF-12 별도 구현·배포 결과 및 그 뒤 TL-2 실제 첫 바퀴 계수는 이 레인의 성공으로 대체하지 않는다.
- U-2 회수기 apply, IS-4 metadata-state apply, I-3 실제 cron 및 실패 유도, I-4 외부 알림은 실행 대상을 구체화한 뒤 별도 승인이 필요하다.
- F-3 기능 검증 중 삭제는 이 레인이 만든 `TEST` 자료에만 한정한다. 기존 사용자 자료와 S3 회수 apply는 건드리지 않는다.

## 전체 종료 실행 상태

- 사용자 요청은 Stage 1·2 비연기 미완료를 끝내는 것이다. 위 첫 검증 레인의 인계가 전체 종료는 아니다. 기존 `R-STAGE1-STAGE2-CLOSEOUT`과 각 항목 완료 정의를 유지한다.
- BF-12 스트리밍 보완은 독립 수용 검토 후 `f8ac7ee`로 통합했고 PR #15로 feature push했다. viz 418건·core 1062건·generated 13종은 별도 단독 실행 성공이며 부모가 보고서와 viz task 파일 hash를 확인했다. generated 최초 의존 부재 실패와 환경 보완 후 성공은 구분한다. main 반영·dev 배포·기본 3600초 첫 주기 확인은 아직 남는다.
- I4는 실제 dev 스케줄·probe 연결이 없어 별도 격리 구현 중이다. 첫 검토의 cron 경로·webhook 입력·컨테이너 timeout 정리·배포 소스 정합 결손을 보완한다. 실제 cron 설치와 외부 전송은 미실행이다.
- WU-PREVIEW·J-1은 별도 dev 사용자 여정 검증을 시작했다. BF-7 디스크 저장 미확인도 같은 미리보기 여정에서 확인한다. S3 릴리스 준비는 별도 사본에서 이미지·소스·복구 근거를 고정한다.
- 후속 순서: S3 배포와 첫 주기 → BF-12 수용 후 TL-2 구현·관측, 운영 실행 절차 보완과 구체 승인, G10 전후 계수 및 최종 단일 전체 검사, 항목별 대장 갱신. 중단된 첫 레인 task나 과거 전체 54/4/2를 전체 성공으로 바꾸지 않는다.

## 후속 실측 갱신 — 2026-09-11 15:52 KST

- 앞 절의 배포 대기는 해소: PR #15 main `f8ac7ee`와 실제 dev 태그 일치, 앱 4개 healthy, 새 단일 doctor 15/0/0. viz 기동 06:28:25 UTC이므로 첫 기본 3600초 주기 07:28:25 UTC 이후 관측 예정. BF-12와 TL-2는 아직 완료 아님.
- 운영 연결은 `6e6486d`로 통합, PR #16 검증 중. 첫 원격 selftest는 backup probe가 요구하는 core venv 부재로 22/1/0(실행 23, 명시 면제 2). `bbba58e`에서 CI 잡에 핀 의존 설치와 실제 doctor import 검증을 추가했다. 로컬 ops-observability-selftest 1/0/0, 원격 재실행은 별도 판정한다.
- WU-PREVIEW는 실제 업로드·미리보기·등록·새로고침 7종 성공/부분 0을 회수했다. GRIB1/2도 각각 신규 TEST로 확인했고 NetCDF는 f8에서 다시 열었다. 선택한 message/slice의 새로고침 지속성은 주장하지 않는다. 독립 수용 후 대장 반영 예정.
- J-1 기본 격자 재사용의 결함 후보는 철회했다. 도구 click 성공 응답에 실제 grid-reuse 요청이 없었고, focus+Enter 사용자 입력 후 POST 201과 지도 전환이 확인됐다. 초기 raw no-grid preview 응답을 재사용 결과로 잘못 연결했던 증거를 제외한다.
- IS4 `95119e8`의 보존 plan은 metadata-only 1건이지만 독립 검토에서 동시 실행·실패 로그 권한 결함으로 통합 기각됐다. 배타 잠금·원자적 한 번 실행 표식·umask와 음성 시험 보완 중. 실제 apply 0.
- G10의 동일 트리 전후 비교를 위해 내부 직렬 실행 제어와 worktree 보고서 EXDEV 보존 결함을 별도 사본에서 수정 중. 전체 검사 시작 전 실제 입력을 준비하며 과거 실행을 새 통합 결과로 재사용하지 않는다.
- 공식 대장 상태는 아직 Stage 1 완료 53/잔여 9/유예 1, Stage 2 완료 86/잔여 8/유예 2다. 위 구현·검증 진행은 대장 마감과 구분한다.

## 수용 갱신 — 2026-09-11

- BF-8·BF-9·WU-PREVIEW 3건을 독립 검토와 부모 증거 확인 뒤 done으로 갱신했다. dev f8과 CI 5a의 해당 제품 코드 차이 0; CI 34572152548에서 frontend 1204/core 1062/pipeline 275/viz 418 통과. CI 제외 core 6/pipeline 50/viz 42 및 dormant·harness 미실행은 최종 all과 구분한다.
- 증거 사본은 `reports/stage12-preview-acceptance/`에 보존했다. 비밀이 포함될 수 있는 raw HAR와 활성 gate-summary는 복사하지 않았다.
- 검토자의 BF-7·BF-11·BF-13 수용 제안은 부모가 보류했다. BF-7의 non-headless Chrome 조건, BF-11의 실제 다섯 사용 자리 계산 스타일 확인이 아직 남으며 BF-13은 BF-11 선행 조건을 따른다.
- J1의 8/9는 일부 동작을 전체 완료 조건으로 확대한 값이라 철회했다. B 격자 후보 제외/수동 재사용404, 판별 가능한 불일치 격자의 경고·계속·거리, 첫 미리보기 시점과 수렴 알림 1회가 추가 검증 대상이다. U-1/F-3는 명시된 최종 전종 게이트 대기다.
