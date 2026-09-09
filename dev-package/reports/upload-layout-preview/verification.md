# 업로드·상세 개선 검증 — 전체 intent 완료 판정

2026-09-09. `codex/upload-preview-finalfix`의 결과는 intent 10항목을 모두 충족한다. 승인된 대표 그림 저장·영구 오류 복구·계보 후보의 UTC일 기간/cursor·격자 설명 저장을 구현하고 실제 재조회까지 확인했다. **미달 0건, 초과 0건**이다. 배포 가능한 코드 상태이며 공유 main 병합·push·운영 배포·운영 S3 smoke는 실행하지 않았다.

## intent 1~10 대조

| # | 원하는 결과 | 최종 판정과 근거 |
|---|---|---|
| 1 | 기획 HTML의 모달·열·여백·카드·단계·상세 순서 | 620px 초기 모달과 단계별 장면, 좌우 등록 구조, 상세 정보 순서를 실제 화면으로 확인. `policy-map.md`, `screens/continuation/`, `browser/contract-expansion/finalfix-green3/contract/` |
| 2 | 파일 선택→전송·분석→등록 입력 장면 분리 | 빈 화면·분석 완료·분류·메타데이터·연결 장면을 같은 1440×1000 브라우저에서 확인. `browser/contract-expansion/finalfix-green3/contract/01-empty.png`~`07-connections.png` |
| 3 | 저장 상세의 파일·분류·기간·좌표·간격·원천·설명·변수 | HDF 등록·reload·편집 뒤 이름, 설명, 파일, 프로젝트, 변수, 날짜, 관측 간격, 원천, 격자 설명을 재조회. `browser/contract-expansion/finalfix-green3/contract/journey.json` |
| 4 | 실제 저장·프로젝트·계보·편집·다운로드 전체 흐름 | HDF 25단계에서 프로젝트 생성, 기간 후보 포함/제외·cursor, 계보 이동/수정/제거/재연결, 편집 지속, 원본 SHA256 일치를 확인. 기존 파일 묶음·ZIP 검증도 유지. `browser/contract-expansion/finalfix-green3/contract/journey.json`, `browser/partial/journey.json` |
| 5 | nc·tif·hdf·bin과 등록 포맷 실제 미리보기 | TIF 묶음·NC·HDF4·BIN 값·BIN 격자·NumPy·GRIB 제외 안내 7사례의 실제 결과를 구분해 기록. GRIB 제외를 미리보기 성공으로 계산하지 않음. `format-matrix.md`, `browser/index.md` |
| 6 | 업로드·확장·상세 그림과 지도 조작·부분 표시 | HDF 그림 decode, 확장보기, 상세 reload, 지도 확대·초기화·커서 위경도를 확인. 실제 TIF 부분 실패는 정상 그림과 누락 파일명을 함께 확인. `browser/contract-expansion/finalfix-green3/contract/journey.json`, `browser/partial/journey.json` |
| 7 | 전송·분석·렌더·이미지 표시 진행 안내 | 단계별 상태와 조회 재시도, 렌더 대기와 image load를 분리했고 관련 회귀와 실제 장면을 확인. `progress-cases.md`, `frontend-continuation.md` |
| 8 | 전송/분석/렌더/표시 상태별 행동 활성 조건 | 조기 등록 차단, 미리보기 실패와 등록 분리, 생성 중 입력 잠금, 415/413은 같은 그림 재시도를 막고 새 그림/자동 그림을 요구하며 일시 오류는 같은 ID 재시도를 유지함을 확인. `frontend-sol/verification.md`, `browser/contract-expansion/finalfix-green3/contract/07-recovery.png` |
| 9 | 느림·통신/서버/이미지/부분 실패·취소·재시도·늦은 응답 | 오류 복구와 오래된 응답 차단 회귀, 손상 TIF 부분 실패, 잘못된 PNG의 서버 이유와 새 그림을 통한 같은 ID 복구를 확인. `progress-cases.md`, `browser/partial/journey.json`, 확장 여정 `representativeRecoveryProof`·`datasetCreateProof` |
| 10 | 같은 장면 시각 대조와 정책65행 추적 | 1440×1000 장면별 캡처와 정책→rev2→구현→실행근거 대응표를 완성했고 정책23/27/37~38 확장까지 닫음. `policy-map.md`, `remaining-decisions.md` |

## 승인된 계약 확장

- 대표 그림: 본체와 분리된 저장·권한·조회 계약을 구현했다. 잘못된 PNG의 415 서버 이유를 표시하고 같은 파일 재시도를 막았다. 이때 데이터셋은 한 건(`01M22A1G6HJBSSN9SEKNS8XZTR`)이고 대표 그림은 0건이었다. 새 정상 PNG 선택 후 같은 ID에서 1건이 됐으며 상세 reload·교체·삭제 뒤 자동 그림 decode까지 확인했다.
- 계보 후보: 이름 OR 접근 가능한 본체 파일명 검색과 분류·주제·기간·가공단계 조건, 안정 cursor 페이지를 구현했다. 날짜 입력은 UTC일 시작·마지막 microsecond로 바꾼다. 브라우저에서 `a1-body.csv`로 DSA1을 찾고 기간 포함/제외·조건 초기화·cursor 25→29건, 계보 CRUD와 reload 지속성을 확인했다.
- 격자 설명: 사람 입력과 자동 분석값을 분리했다. 사람 설명을 우선·자동 `2400x2400`을 보조로 표시하고, 사람 입력 삭제 뒤 DB NULL과 자동값 복귀를 확인했다.
- 서버 `a50a861`과 frontend `71e6592`는 각각 Astra 수용 검토에서 승인됐다. finalfix 구현·실제 브라우저 커밋은 `6d1107c`다.

## 실제 브라우저 근거

agent-browser는 1440×1000, 일회용 PostgreSQL·로컬 원본/미리보기 저장소·worker·viz의 독립 환경에서 실행했다. HDF `MOD15A2H.A2019273.h27v05.061.2020313082826.hdf`는 9,731,088 B, SHA256 `ab7eda26634a5e2f13016acc7e1f8d0cd1daf3924bdbc58538b066b12c12e8a6`다. `browser/contract-expansion/finalfix-green3/contract/journey.json`의 25단계가 초기 620px, 계보 cursor 25→29와 기간 경계·초기화, invalid PNG 415 이유/같은 파일 차단→데이터셋1/그림0→새 그림 선택/같은 ID 그림1, 사람→자동 격자, custom image decode/reload/replace/delete, 원본 다운로드 해시를 기록한다. 앞선 세 실행은 native date 입력, cursor 버튼 활성화, 재연결 후보 페이지 문제로 각각 실패했고 `finalfix*` 디렉터리에 따로 보존했으며 통과로 계산하지 않았다. 운영 데이터와 공유 서버는 사용하지 않았다.

## 최종 게이트

- Astra `frontend-test`: **1,158/1,158**, 실패 0, exit0. `astra-final/frontend-test/gate-summary.json`.
- Astra `generated-up-to-date`: 등기부 **10건 일치**, 위반 0, exit0. `astra-final/generated/gate-summary.json`.
- Astra `service-tests-core-api`: **1,018/1,018**, 제외 6, 실패 0, exit0. 첫 실행은 이 사본의 venv 부재로 검사 0건·exit78이었고, 공유 기준의 고정 Python 경로로 다시 실행한 결과가 green이다. 두 보고서를 모두 보존했다.
- Astra `migration-drift`: **18/18**(platform 15+AI 3), 실패 0, exit0. 첫 실행은 Alembic 경로 미선언으로 검사 0건·exit78이었고, 공유 기준의 고정 Alembic을 명시한 재실행이 green이다. 두 보고서를 모두 보존했다.
- Astra `contract-lint`: seam **3건**, 룰 위반 0, green1/red(판정)0/red(준비)0, exit0. `astra-final/contract-lint/gate-summary.json`.
- 기존 범위 전수 근거도 유지한다: frontend1128/core989/pipeline-worker267/viz-render380, 실제 포맷7사례·부분실패, frontend 도달성174/금지0, 시각2페이지·13px미만0·대비미달0.

## 배포 상태와 한계

코드·계약·마이그레이션·브라우저 검증 기준으로 배포 가능한 상태다. 공유 main 병합, 원격 push, 운영 배포, 운영 S3에서의 실제 업로드/교체/삭제 smoke는 별도 조율 대상이며 미실행이다. GRIB은 기존 미지원 안내·등록·원본 다운로드 검증이며 새 지도 렌더러 지원을 뜻하지 않는다. 별칭과 모든 내부 구조를 무제한 지원한다고 주장하지 않는다.

## 이전 실행 이력

아래는 수정 전 발견과 중간 검증 이력이다. 당시의 미완료·준비 실패·수정 전 red는 보존하며, 현재 판정은 위의 통합 근거를 우선한다.

# 업로드 화면·미리보기 조사 및 진행 오류 보완 — 2026-09-09

## 당시 판정 범위
- 이 시점에는 전체 intent가 미완료였다. 이 실측은 원본/현 컴포넌트의 업로드 초기·분류 화면 비교, 원천 파일 렌더 서비스 시험, 진행 조회 오류 재현과 좁은 수정이었다.
- 화면 비교는 모의 응답을 넣은 실제 업로드 컴포넌트다. 실제 저장·서버 업로드 성공 증거가 아니다. 운영 서버·DB·큐·객체 저장소는 사용하지 않았다.
- 작업 사본의 전용 브랜치에서만 변경했다. 공유 원본·다른 세션 서버·배포를 변경하지 않았다.

## 화면 비교 — 모의 응답
- 창 크기: 1440 × 1000. rev2 원본을 agent-browser의 전용 세션으로 실행했다.
- 검수 진입점: `frontend/audit-upload.html`, `frontend/audit-upload.tsx`, `frontend/audit.vite.config.ts`. 기존 컴포넌트와 CSS를 그대로 가져온다. 네트워크 API를 호출하지 않으며 저장은 명시적으로 거절한다. 제품 빌드의 기본 진입점에는 포함하지 않는다.
- 처음 캡처에서 업로드 CSS 누락을 발견해 검수 진입점의 import를 바로잡고 다시 캡처했다. 아래 current 캡처는 CSS가 적용된 결과다.

| 장면 | 기획 | 실제 컴포넌트 | 확인된 차이 |
|---|---|---|---|
| 파일 선택 전 | `screens/reference-upload-empty.png` | `screens/current-upload-empty.png` | 기획은 중앙 파일 선택 모달, 현재는 전체 화면과 상단 드롭 카드. 파일 고르기 버튼·아이콘·안내 위치도 다름 |
| 분류 입력 | `screens/reference-upload-ready.png` | `screens/current-upload-classification.png` | 현재는 드롭 영역·파일 카드·분석 완료·등록 질문이 계속 공간을 차지해 좌우 입력을 아래로 밀어냄. 기획은 입력 장면 상단부터 미리보기/분류가 배치됨 |
| 분류 입력 세부 | 동일 | 동일 | 기획은 밑줄형 단계 내비·파일 배지, 현재는 둥근 단계 버튼·텍스트 파일명. 미리보기 상단에 대표 그림·팔레트·격자 안내 등 추가 조작이 쌓여 있음 |

- `screens/reference-upload-classification.png`는 기획의 그림 생성 중 상태다. `reference-upload-ready.png`는 이후 그림 표시 상태다. 실제 컴포넌트 캡처의 미리보기는 모의 응답상 아직 그리기 전이므로 그림 유무를 포맷 실패 증거로 쓰지 않는다.
- `policy-map.md`에 번호별 정책 65개를 추출했다. 당시 이 표의 전체 구현 검수는 미완료였으며 각 행은 미검증으로 남겼다. 이후 rev2 변경 대조와 상세/수정/확장/실패 화면을 추가 검증해 위 최종 판정에서 닫았다.

## 포맷 파서·렌더 — 실제 원천 파일
- `services/viz-render/tests/test_e2e_real.py` 실행: **10 passed, 0 skipped**, 17.22초. `formats.junit.xml`에 결과를 남겼다.
- 기존 viz Python 3.12 환경의 실행 파일·라이브러리를 재사용했고, 현재 사본의 소스를 `PYTHONPATH`로 지정했다. 원천은 읽고 시험용 임시 디렉터리로 복사하며 상시 서버나 DB를 사용하지 않는다.
- 시험 대상: GeoTIFF, NetCDF, Binary HSR, HDF4, NumPy 및 격자 유무·잘못된 격자·변수 생략·값 미리보기. PNG 생성뿐 아니라 불투명 픽셀·좌표 범위 등 기존 시험의 검증을 사용했다.
- **브라우저 업로드 → 분석 worker → 렌더 → 실제 표시의 전체 연결은 이 시험에 포함하지 않는다.** GRIB의 미리보기 지원도 포함하지 않는다.
- 경고 11건: JUnit 속성 형식 경고와 NetCDF 경로의 NumPy 바이너리 호환 가능성 경고. 시험 실패는 없으나 의존성 재현 시 확인할 환경 경고로 남긴다.
- 원천 파일 존재 확인: NetCDF 397,448 B / Binary gzip 1,259,571 B / GeoTIFF 24,577,705 B / HDF 파일 9,731,088 B / GRIB 149,514,336 B. 포맷 폴더는 `03 Reference-Data/02.File-format`. 모든 하위 구조 지원을 의미하지 않는다. 당시 파일 해시 목록과 브라우저 검수는 미작성 상태였고 이후 위 최종 근거로 보완했다.
- 당시와 현재 모두 GRIB은 reader에서 미리보기 제외된다. 제외 안내를 미리보기 성공으로 계산하지 않았고, 새 지도 렌더러 지원은 이번 범위에 포함하지 않았다.

## 진행 조회 오류 — 재현과 수정
1. 렌더 조회가 실패하면 오류 안내와 `그리는 중` 표시가 동시에 남았다. `progress-before.json`의 실패 단언으로 재현했다. 현재 오류가 있으면 이전 작업의 진행중 표시를 사용하지 않도록 수정했다.
2. 업로드 상태 조회가 한 번 끊기면 다음 조회가 예약되지 않았다. 복구 시험은 준비 상태에 도달하지 못해 실패했다. 상태 조회에 제한된 재시도(연속 세 번째 실패에서 자동 재시도 중단), 재연결 안내, 수동 재시도를 추가했다. 파일을 다시 전송하지 않는다. 업로드 삭제는 별도 안내하고 자동 재시도하지 않는다.
3. 재시도 중 기존 분석중 안내와 새 오류/복구 안내를 중복 표시하지 않는다. 성공 조회 시 오류를 지운다. 모달 정리 시 예약 타이머를 취소한다.

## 시험 근거
- `progress-before.json`: 보완 전 신규 두 시험 실패. 업로드 복구 시험은 기본 제한시간과 겹쳐 종료돼 후속 실행에서 관찰 대기를 3초로 조정했다. 코드의 조회 중단 경로도 직접 확인했다.
- `progress-focused.json`: 수정 후 신규 두 시험 + 기존 오래된 렌더 응답/화면 이탈 두 시험, **4 passed**.
- `progress-node22.json`: 업로드 기존 시험·기존 폴링 회귀·신규 복구 시험, **107 passed, 0 failed, 0 skipped**. Node 22.22.1 사용.
- `progress-final.json`: 검토 의견에 따라 연속 실패 한계·수동 재시도·삭제된 업로드·화면 이탈 후 늦은 오류 시험을 추가한 최종 실행. **110 passed, 0 failed, 0 skipped**, Node 22.22.1. 타입 검사와 변경 공백 검사도 통과했다.
- `progress-after.json`, `progress-node2419.json`: Windows Node 24 환경의 중간 실행 기록. 폼 데이터 파서에서 기존 두 시험이 실패했다. 첫 중간 실행은 미리보기 수정 전 소스가 로드돼 신규 시험도 실패했다. 이 기록을 최종 통과로 사용하지 않는다.
- 당시 frontend typecheck만 통과했고 사용자 흐름 전체 E2E, 전체 게이트, 최종 시각 검수는 미실행이었다. 이후 실행 결과는 위 최종 근거에 기록했다.

## 당시 남은 작업
- 후속 진행 보완: 새 파일 접수 시작 시 이전 uploadId/ready/rendered 초기화, 파일 구성 변경 시 PreviewPanel 재생성으로 이전 폴링/그림 격리. 렌더 요청 응답 대기와 실제 이미지 load 대기를 각각 표시하고 image error는 원인을 만료로 단정하지 않는다. 관련 기존+회귀 111건 통과(`progress-continuation.json`), 이후 추가한 요청/이미지 로드 시험을 포함한 복구 파일 8건 통과. 타입·공백 검사 통과. 아래 파일 교체 위험 중 이전 ready 유지 경로는 이 수정으로 해소했으며 전체 저장 흐름은 여전히 미검증이다.
- 2026-09-09 화면 1차 수정: 초기 중앙 모달·파일 고르기·아이콘, 등록 중 파일 관리 접기, 중복 등록 질문 제거, 밑줄 단계 탭/파일 배지. `screens/updated-upload-empty.png`, `screens/updated-upload-classification.png`를 1440×1000에서 직접 확인했다. 모의 응답을 쓰므로 저장·실제 미리보기 성공 증거가 아니다. 미리보기 조작부 배치·폼 카드·폰트·전체 폭 등 HTML 차이가 남는다.
- 화면 변경 후 `layout-tests.json`: 관련 시험 110 passed, 0 failed, 0 skipped. 타입 검사·빌드·공백 검사 통과. 대장 일관성 검사 통과(178개 항목, 불일치 0; 기존 비파싱 영역 9개는 검사 대상 제외로 보고됨).
- 정책 65개와 rev2의 전체 대조를 완료하고 업로드·상세 화면 구성을 재구성한다. 추가 기능의 배치는 기능 보존과 HTML 구성을 함께 만족하도록 구체화한다.
- 업로드에서 자동 미리보기 시작과 실제 이미지 로딩/실패 상태까지 연결한다. 현재 수정은 조회 오류 두 경로에 한정된다.
- 포맷별 실제 파일을 브라우저 흐름으로 검증하고 GRIB 지원, 확장자 별칭·내부 구조, 부분 파일 실패를 다룬다.
- 독립 DB·저장소·큐·worker가 모두 분리된 전체 시험 환경을 준비한 뒤 저장·편집·계보·다운로드를 검증한다.
- 당시 수용 검토에서 기존 파일 교체 시 새 전송 시작과 이전 uploadId/ready 상태의 수명이 겹칠 가능성을 추가로 발견했다. 이후 장면 수명 회귀로 재현·수정했고 최신 frontend 전수와 실제 여정으로 확인했다.

## 2026-09-09 재개 당시 진행 기록

- 이전 「조회 오류 두 경로에 한정」·「파일 교체 ready 위험 잔존」은 8855102 후속 수정 이전 서술이다. 재개 시 전체 초기화와 장면 수명을 새 회귀로 대조하며 과거 문장을 최신 판정으로 사용하지 않는다.
- 당시 원본620px compact를 분석완료→다음까지 유지하는 장면 경계·실제 입력 카드·상세 읽기순서·계보수정 UI를 보완 중이었다. 정책65행은 rev2/후속결정/구현/실행근거를 분리했다.
- TIF 실제 파일 브라우저: 업로드·worker분석·등록전그림·확장·등록·reload·편집·reload·원본 SHA256 일치. 화면 변경 통합 전 증거이며 최종 통합 후 새 실행한다.
- NC 등록전그림 성공 후 상세 reload에서 viz 연결 종료. 파일 판별·변수조회·값읽기·격자읽기 동시 실행 회귀가 자식프로세스 SIGSEGV(-11)로 실패해 원인을 재현했다.
- netCDF-C 프로세스 공유 상태 접근을 RLock으로 보호(중첩 판별 허용), 래스터 렌더 자체는 잠금 밖. 동일 회귀 80회 읽기·결과값 대조 1/1 통과. 당시 실제 NC 브라우저는 재실행 중이었고 이후 NC02 전체 흐름을 통과했다. 근거 파일 `native-io-red.log`와 `native-io-green.log`.
- 공식 근거: [Unidata netCDF FAQ — thread safety](https://docs.unidata.ucar.edu/netcdf-c/current/faq.html). C 기반 라이브러리의 동시 스레드 호출 안전성을 보장하지 않는다고 명시한다.
- 당시 대표그림 수동 교체 지속성은 기존 저장 API가 없어 포함 여부 사용자 결정 대기였다. 이후 사용자가 포함을 승인했고 위 계약 확장으로 구현·검증했다.

### 통합 중간 결과 — 완료 판정 아님

- NetCDF 실제 재실행 NC02: 등록 전/후 그림, 저장·reload·편집·reload·원본 SHA256 일치 통과. NetCDF native 접근 회귀1건 RED(SIGSEGV)→GREEN, 실제파일 포함 읽기/좌표50건 통과. viz 전체 게이트380실행/0skip/40deselected/0실패, exit0. e2e/perf 제외40건은 이 게이트 통과에 포함하지 않는다.
- UI1차+계보1차 통합. HDF02에서 자동그림·확장·프로젝트·계보·원천·기간없는 관측간격10분 보존 확인. parent 노드 화면이 실제 A강우원자료로 이동했으나 도구 URL glob대기 실패; 경로 직접대조로 시험 수정해 HDF03 실행.
- 통합 타입검사1차 실패: 새 관측간격시험의 optional base 접근 TS18048. UI 후속에서 수정, 통합 재검사 예정.
- BIN01은 실제 제품 실패: stage2 파이프라인이 격자없는 Binary를 업로드 실패로 처리해 값만 보기/등록이 막혔다. 화면에서도 서버분석 실패안내가 빠졌다. 각각 서버/화면 소유사본에서 회귀 재현 중.

당시 보존: frontend1128/core989/pipeline267/viz380 통과. 이 시점에는 단계 6의 기존 범위만 완료했고 계약 확장 세 항목은 미판정이었다. 이후 승인·구현·검증 결과는 위 최종 판정에 반영했으며, 중간 게이트 로그와 기점 이후 소스 SHA256도 같은 보고서 폴더에 보존했다.
