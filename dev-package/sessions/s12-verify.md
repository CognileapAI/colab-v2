# Stage 1·2 재검증 — 2026-09-10

## 현재 기준

HEAD/origin/main `712a33711f6a222ff7c1d431c4ecef0946508cca`, fetch 후 차이 0/0. 기존 승인문서 7파일은 보존했다. 최초 tracked diff hash는 자식 사양 참조, 미추적 결정문서도 lifecycle baseline에 포함한다.

SSH 읽기전용 실측: dev CURRENT_SHA `09e2b9b2db1a`, MAIN_SHA `main=09e2b9b2db1a candidate=09e2b9b2db1a ancestor=yes`; 서비스 4개 모두 11시간 기동 healthy. `git diff 09e2b9b HEAD -- frontend services contracts db infra` 0줄이다. 이는 배포 소스 대응 근거이며 제품 완료나 deploy_doctor 15/15의 새 실행이 아니다. 과거 2264 배포 기록만 보고 현재 배포를 미반영이라고 해석하면 틀린다.

## 재검증 행렬

각 완료 정의 원문은 `work-items.yaml` 해당 ID가 정본이다. 코드들은 현재 main에 포함된다. 이번 게이트 결과는 `reports/s12-verify/local/gate-summary.json`을 직접 읽는다; 표의 게이트명은 검증 대응이며 실행 성공을 미리 주장하지 않는다.

| 항목 | 완료 정의 요지·관련 게이트 | dev/최종 미충족 | 부모 판정 제안 |
|---|---|---|---|
| BF-7 | revoke tick 지연·DOM anchor·서버 렌더 유지; frontend-test | 실제 다운로드 완주 증상 미재현을 이번 dev에서 미실측 | open 유지 |
| BF-8 | 뿌리 padding·1200px·히어로 중복 제거·CSS 시험; frontend-test | 현재 dev 계산 스타일 미실측 | open 유지 |
| BF-9 | 원천→루트 null method edge·화살표2; core-api/frontend-test | 현재 dev 계보 화면 여정 미실측 | open 유지 |
| BF-11 | 정본 CSS 이름·공용 backrow·회귀0; frontend-test | 현재 dev 색상/레이아웃 확인 미실측 | open 유지 |
| BF-13 | 공통 토큰 드리프트 실패 fixture·충돌0·로컬 유지·화면회귀; frontend-test | BF-11 선행 및 현재 dev 화면 증거 대기 | partial 유지 |
| I3 | 15행 전체·자동 배포·롤백왕복·양성/음성·백업·게이트 | healthy4와 SHA만으로 자동완주/실제red·green/rollback을 입증 못함 | partial 유지, R-S2-OPS에 15조건 재대조 |
| BF-12 | stdout INFO·음성fixture·dev 첫주기·비밀미출력; viz-render | 최근12h 회수 로그 조회 일치줄0. dev TRIGGER_SPOOL env 미선언, 아래 결손 참조 | open 유지, TL-2 차단 |
| X-7 | core-api CI 실제green·비결정 fixture 원인·환경차이; core-api | 원격 조건 해소. 이번 로컬 게이트 결과 수용 필요 | 로컬green 뒤 done 후보 |
| WU-PREVIEW | 7종·실 GRIB/HDF decode·렌더 회귀; pipeline/viz/frontend | 해당 소스는 dev 포함되나 배포후7종 E2E 새 확인 부재 | partial 유지 |
| U-1 | S3 전송·원장·실측접수·재개; core-api/frontend | 제품승인 해소, 새 dev S3 전송/재개 검증 부재 | partial 유지 |
| F-3 | 목록·상대경로·티켓200·파일CRUD; core-api/frontend | 제품승인 해소, 새 dev 변경/재조회 검증 부재 | partial 유지 |

## X-7 원격 CI와 환경 차이

시험 수정 최종 커밋 `a3389bd`가 main에 포함된다. [main CI 34419117742](https://github.com/CognileapAI/colab-v2/actions/runs/34419117742/job/102690514011), SHA `89a28d9c0fd5d130bd88e158b69b803c590ebbd4`: core-api 의존설치·selftest·실제 시험 묶음 판정 step가 모두 success(시험 2026-09-09 23:57:23Z~2026-09-10 00:00:26Z). 최신 HEAD CI34473474058는 제품잡 skipped이므로 시험 성공에 불산입. CI검증 SHA부터 HEAD까지 core-api/계약/platform DB/CI설정 diff0.

원인은 `SELECT ... LIMIT 1`의 물리행순서 의존; 공개 DS_A1/잠김 DS_A2 고정 fixture로 수정했다(`20260908-product-local-verification.md`). 제품 권한 변경이나 시크릿 추가로 해결한 것이 아니다. 로컬은 WSL 기존 서비스 venv·test.env와 gate가 세우는 일회용 Postgres, CI는 Ubuntu/Python3.12·핀 의존 설치와 동일 gate/일회용 DB. 선택자 core-api `not e2e` 동일; CI 경로필터는 호출 여부만 결정한다.

## 새로 확인한 BF-12 진입 결손

dev 로그 최근12h에서 회수 관련 일치줄0은 실제 관측계수0을 뜻하지 않는다. `app/main.py`는 `app.state.triggers is not None`일 때만 ReclaimJob/TriggerDrainLoop를 만든다. `kernel/config.py`에서 COLAB_VIZ_TRIGGER_SPOOL 미선언은 None이며, dev 컨테이너 env의 해당 정확한 키 조회 결과 부재다. `infra/dev/compose.yml`에도 해당 키가 없다. 로깅만의 잔여라고 가정하지 말고 dev 트리거·저장소·회수 입력 경계를 R-S2-OPS에서 조사한다. 설정을 켜거나 운영 상태를 바꾸지 않았다. S3 mode에서 로컬 source_root가 원장 전체를 나타내는지도 검증 없이 회수 대상으로 삼지 않는다.

## 다음 독립 작업과 인계

- R-S1-STORAGE의 원장만 사용하는 실패안전 삭제/완료메타7일 구현과 실패시험은 시작 가능. 실제 삭제는 대상목록 승인까지 하지 않는다.
- R-S1-GATE-PERF은 이번 gate 로그 계수·시간을 baseline으로 소비한다.
- R-S2-OPS는 I3 자동화15조건·BF-12 배선·관측 결손을 조사/로컬 구현한다. 배포는 별도 실행 승인.
- TL-2 구현은 BF-12 dev 첫주기 관측까지 진입조건 미충족이다.
- 부모 대장: X-7은 새 로컬green 수용 뒤 done, evidence에 위 CI와 본 보고서 추가. 다른 10행 상태 유지, U-1/F-3 승인대기 문구는 복원하지 않는다. HANDOFF는 본 문서 링크 및 다음 독립 작업을 5줄 이내 반영한다.

## 실행 결과와 환경 복구

- 최초6종 단일task: exit1, green5/red(판정)1/red(준비)0. `verify-report`도 exit1 `gate failures remain`. 실제 원인은 viz venv의 `h5py` 부재이나 게이트가 수집오류를 판정실패로 분류한 값을 임의로78로 고치지 않는다.
- frontend 88파일/1186통과·실패0; core-api 1018통과/skip0/deselect6/failed0/errors0,162.8초; pipeline 268통과/skip0/deselect46/failed0/errors0,11.0초; 대장180건 불일치0; 계약3건 위반0.
- 정본 `services/viz-render/requirements.txt`는 h5py3.16.0을 선언했으나 기존 venv에 미설치였다. `python -m pip`도 pip모듈 부재로 실패해 설치하지 못했다. 기존 uv의 `pip --python services/viz-render/.venv/bin/python`으로 h5py3.16.0 1개만 추가했다(전역설치0·타패키지교체0·제품파일수정0).
- 복구 전용task `7437468635f84d1fbf7c1580a1de886d`, `reports/s12-verify/viz-recovery/gate-summary.json`: 단독 viz exit0, green1/red(판정)0/red(준비)0,387통과/skip0/deselect42/failed0/errors0,29.4초. 문서 수정 전에 `verify-report`와 lifecycle handoff 성공을 회수했다.
- 두 제품실행을 합쳐 단일6종green이라고 하지 않는다. 최초실패 보존, 복구검증별도. 나머지 제품게이트 반복0. X-7은 현재core-api green과 실제원격CI 성공·원인·환경차이 기록까지 충족하여 부모의 done 수용 대상으로 넘긴다.
- 결과 기록만 추가한 최종문서 task `d62240844b9f422ba82fb0c60ed6437a`의 보고서 `reports/s12-verify/docs-final/gate-summary.json`에서 최종 work-item-consistency/contract-lint 결과를 확인한다. 원래6게이트 task가 성공으로 바뀐 것은 아니다.

요청 대비: 조사 산출의 범위 초과0. 제품완료 미달은 표의 dev 여정·회수 첫주기·자동배포/rollback 증거이며, 조사 결과로 숨기지 않는다. 제품 코드·운영 데이터 변경0. 조사와 환경복구 인계 이후 부모가 독립 구현을 계속한다.
