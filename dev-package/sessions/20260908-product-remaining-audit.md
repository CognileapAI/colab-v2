# 제품 개발 잔여 조사 — 2026-09-08

읽기 전용 조사. 기준 HEAD `ccf76ec`. 상태 변경·시험 실행·CI 조회·운영 접촉·배포·데이터 쓰기 0회. 본 파일만 산출. 기록된 과거 통과는 오늘 통과로 계산하지 않았다.

## 계수와 판단

- YAML items 행 단위: 총 177행. stage1 done53/open8/partial2, stage2 done84/open7/partial2/deferred1. 현재 stage1/2 실행 후보는 open/partial 19행이며, 개별 기능 수가 아니다.
- after_stage2 open15행, out_of_scope deferred4/done1행. C3·C4 묶음 중복 행 및 J-1 다기능 묶음 때문에 행 수를 개발 기능 수로 바꿔 말하지 않는다.
- [권고] 최신 실패 CI(schema/planning/harness) 준비 결손 보수 및 이미 main에 있는 수정의 완료 증거 대조 → 사용자 핵심 여정 검증 → 실제 미구현 → 운영 마감 → 성능·보관 순서. 자동으로 모든 보류 범위를 다시 열지 않는다.
- 대장의 main 미병합 서술(BF7/8 등)은 현재 main 파일/이력과 어긋난다. 상태 done으로 단정하지 않고 구현 존재와 수용/배포 증거를 구분한다.

## 현재 단계 후보별 분류

### IS4 — terraform state 보관
- P2 · stage2/partial · 구현 있음·복구 검증 남음
- 기존 완료 정의 요약: terraform state 상실 조건에서 문서만으로 복구.
- 정본: `dev-package/work-items.yaml:304` (해당 completion_def 전체가 기준).
- 근거: `infra/staging/tunnel/README.md §5-1; dev-package/sessions/WINDOW-20260903-F2.md §6`.
- 판단/잔여: 대장은 맨몸 호스트 조건만 미완. 최신 실제 복구/plan 미실행.

### I3 — 배포 자동화
- P2 · stage2/partial · 구현 있음·운영 검증/트리거 남음
- 기존 완료 정의 요약: 파이프라인 완주·상세15행.
- 정본: `dev-package/work-items.yaml:345` (해당 completion_def 전체가 기준).
- 근거: `dev-package/sessions/I3.md §6; dev-package/work-items.yaml I3`.
- 판단/잔여: 대장 최신 재계수 닫힘11/열림1/부분3. 자동 트리거, 판정 red 로그, 단일 전수 gate, 전후 health 실측 잔여. 이번 운영 접촉 없음.

### I4 — 운영 준비 (추적·알람·복구 리허설)
- P2 · stage2/open · 구현 필요 후보·I3 선행
- 기존 완료 정의 요약: 회차 복원 결과 재사용+추적·로그·알람·레지던시 기록.
- 정본: `dev-package/work-items.yaml:358` (해당 completion_def 전체가 기준).
- 근거: `infra/README.md; dev-package/work-items.yaml I4`.
- 판단/잔여: services/infra/contracts 코드설정에서 opentelemetry/trace_id/alertmanager/prometheus/residency 검색 히트0. 동의어 전수/외부 환경 미확인. WAL은 prod 별도.

### TL-2 — 구판 미리보기 산출물 회수 — 지도 타일 회수 루프의 소유 판정에 등급을 더한다
- P2 · stage2/open · 선행 검증 대기·구현 필요 후보
- 기존 완료 정의 요약: 판정불가/원천원장부재 관측 등급·실패시험·기존19벌 대조·삭제 별도go·한바퀴 실측.
- 정본: `dev-package/work-items.yaml:987` (해당 completion_def 전체가 기준).
- 근거: `dev-package/work-items.yaml TL-2/BF-12`.
- 판단/잔여: BF-12 완료 전 착수 보류 기록. TL-2 문구 staging과 BF-12 최신 dev 판정처 불일치 조정 필요.

### J-1 — 편의 기능 묶음
- P2 · stage2/open · 범위 미판정·대장/근거 충돌
- 기존 완료 정의 요약: 확정 completion_def_draft의 편의 기능 9건 통과.
- 정본: `dev-package/work-items.yaml:1058` (해당 completion_def 전체가 기준).
- 근거: `dev-package/sessions/S1-PLAN-REFOUND.md:1001,1009-1018; dev-package/work-items.yaml J-1`.
- 판단/잔여: 대장은 9건, 참조 정본 J-10은 F-3 승격으로 묶음 9→8이라고 적음. 개별 기능 최신 R-B/R-C 구현 중복 대조 전 묶음 구현 중지/보고. 옛 문구 612m는 최신 대장에서 고정값 아님.

### PA-G — 구글 IdP 어댑터
- P2 · stage2/open · 구현 필요
- 기존 완료 정의 요약: Google 단일 어댑터·비밀번호 경로/파일 폐기·admin/음성시험·PA 재통과·배포.
- 정본: `dev-package/work-items.yaml:1374` (해당 completion_def 전체가 기준).
- 근거: `services/core-api/src/colab_core/kernel/authn.py:36,179,187`.
- 판단/잔여: 현 authn은 planted-password. IdP 설정/전환 사용자 영향 검토 필요. 자격정보 출력/수정 없음.

### CR-2 — 코드리뷰 회차 후속 — Ted 판정 5건 ＋ 배포 뒤 재굽기·소유 재실측 ＋ CI 인프라 red 둘
- P2 · stage2/open · 복합 항목·최신 대조 필요
- 기존 완료 정의 요약: 계약/로그인 제한/재굽기/수명·비밀·DLQ/CI 각각 판정 및 집행.
- 정본: `dev-package/work-items.yaml:1938` (해당 completion_def 전체가 기준).
- 근거: `dev-package/sessions/CODE-REVIEW-20260903-PLAN.md §5-5; dev-package/sessions/R-D-ROUND-20260908.md:69`.
- 판단/잔여: 최근 R-B/R-C 계약 변경이 있어 옛 요구 전부 재구현 금지. 현재 planning CI 결손은 최신 R-D에도 기록. 원자 항목별 폐쇄 증거 대조 필요.

### BF-7 — 스크린샷 버튼 — 객체 URL 같은 tick 회수·앵커 미부착 경합 (하드닝 · 크롬 취소 증상 미재현)
- P1 · stage1/open · 구현 있음·검증/대장 정리
- 기존 완료 정의 요약: 객체 URL 지연 회수·앵커 부착, 실패 시험, 다운로드 완주, 서버 렌더 무변경.
- 정본: `dev-package/work-items.yaml:2183` (해당 completion_def 전체가 기준).
- 근거: `frontend/src/components/datasetpreview/ScreenshotButton.tsx:27,94; frontend/test/dataset-preview-screenshot.test.tsx`.
- 판단/잔여: 현 main에 4000ms 지연 코드 있음. 대장 main 미병합 문구 낡음. 현 트리 테스트 및 agent-browser 다운로드 재검증 필요.

### BF-8 — `LabPage`(S-01) 뿌리 규칙 부재 — 화면 뿌리가 자기 여백을 갖는 관례의 결손
- P1 · stage1/open · 구현 있음·검증/대장 정리
- 기존 완료 정의 요약: 뿌리 여백·최대폭 1200px, 히어로 이중 여백 방지, CSS 로드 시험.
- 정본: `dev-package/work-items.yaml:2219` (해당 completion_def 전체가 기준).
- 근거: `frontend/src/components/dashboard/dashboard.css:9; frontend/test/dashboard.test.tsx`.
- 판단/잔여: 현 main에 규칙 있음. git log는 42638fc/89f0357 확인. 대장 main 미병합 문구 낡음.

### BF-9 — core-api 계보 그래프 — 원천 → 루트 edge 부재 (프론트는 라벨 없는 화살표로 수용)
- P1 · stage1/open · 구현 있음·검증/대장 정리
- 기존 완료 정의 요약: 원천→루트 edge·method null, FE 화살표 유지, 응답 시험, 계약 델타 기록.
- 정본: `dev-package/work-items.yaml:2253` (해당 completion_def 전체가 기준).
- 근거: `services/core-api/src/colab_core/app/routes/lineage.py:99,111,151`.
- 판단/잔여: 현 main source_edges 및 nullable parent 구현 확인. 현 트리 시험 미실행.

### BF-10 — 바탕지도 대안 — 격자선·눈금 옵션 (POL-021 준수 · Ted 6 · 접수 B-2)
- P2 · stage1/open · 미판정·구현 필요 후보
- 기존 완료 정의 요약: EPSG4326 격자선/눈금 토글·기본off·PNG 불일치 판정·bbox 시험.
- 정본: `dev-package/work-items.yaml:2287` (해당 completion_def 전체가 기준).
- 근거: `dev-package/work-items.yaml BF-10`.
- 판단/잔여: 대장 evidence null. graticule/gridLines 검색에서 구현 미발견이나 동의어 포함 전수 분석 아님. 화면/PNG 정책 선결.

### BF-11 — `project.css` 미정의 토큰(`--line`·`--fg-muted`·`--surface`·`--fg`) → `tokens.css` 정본 치환 ＋ backlink 공용화
- P1 · stage1/open · 구현 있음·검증/대장 정리
- 기존 완료 정의 요약: 참조 토큰 정의 시험·정본 치환·backlink 공용화·화면 회귀.
- 정본: `dev-package/work-items.yaml:2307` (해당 completion_def 전체가 기준).
- 근거: `frontend/test/project-css-tokens.test.ts; dev-package/reports/bf-11/lane-report.md`.
- 판단/잔여: 테스트 파일 현재 존재 및 대장 구현 근거 확인. 현 브라우저 색상/정본 이름 판정 미확인.

### BF-12 — 지도 타일 회수 루프 「관측 전용의 관측이 안 된다」 — 앱 로그 설정 부재로 INFO 요약이 버려진다
- P1 · stage2/open · 구현 있음·배포 관측 남음
- 기존 완료 정의 요약: stdout INFO·실패 시험·dev 첫 회수 바퀴 로그·비밀 미출력.
- 정본: `dev-package/work-items.yaml:2344` (해당 completion_def 전체가 기준).
- 근거: `services/viz-render/src/colab_viz/kernel/logging_setup.py; dev-package/work-items.yaml BF-12`.
- 판단/잔여: 현 main 로깅 파일 있음. dev 실제 한 바퀴 및 삭제0은 이번 조사 미측정.

### BF-13 — 화면 CSS 세 파일이 같은 `--color-*` 토큰을 각자 `:root` 에 다시 적는다 — 값 일치를 재는 것이 0건
- P2 · stage1/open · 구현 필요 후보
- 기존 완료 정의 요약: CSS 중복 변수 값 비교 음성 시험·갈린 값 판정·공통 토큰 위치 판정·회귀.
- 정본: `dev-package/work-items.yaml:2371` (해당 completion_def 전체가 기준).
- 근거: `frontend/test/project-css-tokens.test.ts; dev-package/work-items.yaml BF-13`.
- 판단/잔여: 기존 시험은 project 단일 파일 범위. 세 CSS 값 드리프트 실제 개수 미측정. 임의 값 통합 금지.

### U-1 — 업로드 S3 직행 + 중단 재개
- P1 · stage1/partial · 구현 근거 있음·승인/검증 남음
- 기존 완료 정의 요약: S3 저장 분기·프리사인드 전송·재개·실물 확인 뒤 접수.
- 정본: `dev-package/work-items.yaml:2401` (해당 completion_def 전체가 기준).
- 근거: `dev-package/sessions/F2-PR.md; dev-package/work-items.yaml U-1`.
- 판단/잔여: 대장은 실버킷 증거와 8차 해제 판정 대기 기록. 최신 승인 이력 대조 전 닫지 않음.

### U-2 — S3 고아 바이트 정리
- P1 · stage1/open · main 구현 필요·기존 archive 구현 비교 먼저
- 기존 완료 정의 요약: S3 삭제 성공 후 행 정리·삭제 실패 재시도·등록 보호·원장 키만·고아 판별 음성 시험.
- 정본: `dev-package/work-items.yaml:2414` (해당 completion_def 전체가 기준).
- 근거: `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:662; dev-package/sessions/R-D-ROUND-20260908.md:57`.
- 판단/잔여: 현 expire는 DELETE FROM d5_upload만 실행. archive/feature/rtf400_upload_reaper 태그 5c1458e 실재. 기존 구현 재검토 우선, 복사/병합 안 함. 완결 전송 보관 기간 판정 필요.

### F-3 — 파일 관리 — 목록·폴더 구조·다운로드·본체 변경
- P1 · stage1/partial · 구현 근거 있음·승인/검증 남음
- 기존 완료 정의 요약: 파일 목록/크기·상대 경로·티켓/바이트/ZIP 다운로드·본체 변경.
- 정본: `dev-package/work-items.yaml:2427` (해당 completion_def 전체가 기준).
- 근거: `dev-package/sessions/F2.md; dev-package/work-items.yaml F-3`.
- 판단/잔여: 대장은 구현/실호출과 9차 해제 판정 대기 기록. U-1 선행. 실물 모든 경로 미검증.

### G10 — 단독 선언 게이트 8개 안의 시험 병렬화 — 전수 시간의 대부분이 그 여덟에 있다
- P3 · stage1/open · 구현 필요 후보
- 기존 완료 정의 요약: 게이트 내부 병렬화·자가시험·동일 시험 계수·동일 트리 시간 비교.
- 정본: `dev-package/work-items.yaml:2466` (해당 completion_def 전체가 기준).
- 근거: `gates/config/parallelism.toml; dev-package/reports/window-8a/lane-report.md`.
- 판단/잔여: 속도 개선이며 기능 완주 차단과 분리. serial 선언 완화 금지. 이번 시간 미측정.

### X-7 — main CI core-api 시험 red 1건 해소 — test_viz_service_credential.py:85 403≠202 (a31111f 이래 · R-D advisor ③ 발견)
- P1 · stage2/open · 최신 CI 성공 확인·과거 원인/대장 정리
- 기존 완료 정의 요약: main CI core-api green·원인 분류·로컬/CI 환경 차이 기록.
- 정본: `dev-package/work-items.yaml:3139` (해당 completion_def 전체가 기준).
- 근거: `dev-package/sessions/R-D-ROUND-20260908.md:69`.
- 판단/잔여: 초판 판단 개정: 메인이 CI 34216692424, head ccf76ec를 직접 조회하여 core-api success를 확인했다. 현재 실패로 재사용하지 않는다. 과거 원인/로컬 차이 기록이라는 나머지 완료 정의 확인 후 대장 정리 후보다.

## 분리하는 범위

- R2 · after_stage2/open · v1 레포 5종 archive · 정본 `dev-package/work-items.yaml:42`.
- C1 · after_stage2/open · 5 repo 푸시 확인 · 정본 `dev-package/work-items.yaml:185`.
- C2 · after_stage2/open · v1 이관 (`20 CoLAB-v1`) · 정본 `dev-package/work-items.yaml:198`.
- C3 · after_stage2/open · PoC 지식 추출 `HARVEST.md` · 정본 `dev-package/work-items.yaml:211`.
- C4 · after_stage2/open · v1 방법론 추출 `METHOD.md` · 정본 `dev-package/work-items.yaml:224`.
- C3·C4 · after_stage2/open · 지식·방법론 추출 (`WORK-UNITS §10` 에서 한 행으로 묶인 항목) · 정본 `dev-package/work-items.yaml:237`.
- I0 · out_of_scope/deferred · AWS 계정·결제·리전·예산 알람 · 정본 `dev-package/work-items.yaml:250`.
- I1 · out_of_scope/deferred · 토폴로지 + IaC (`plan` 까지) · 정본 `dev-package/work-items.yaml:317`.
- I5 · out_of_scope/deferred · prod 전환 · 정본 `dev-package/work-items.yaml:371`.
- G1b · after_stage2/open · E-04 · E-02 목업·화면 최신성 · 정본 `dev-package/work-items.yaml:399`.
- DP-1 · after_stage2/open · 데이터 프로세스 — 사용자가 원하는 형태로 가공하고 결과를 새 데이터셋으로 저장한다 · 정본 `dev-package/work-items.yaml:669`.
- T-1 · after_stage2/open · `ts_config` 한국어 재작성 · 정본 `dev-package/work-items.yaml:788`.
- P4 · after_stage2/open · 검색 히어로(S-01) · 검색 결과(S-06) · 정본 `dev-package/work-items.yaml:1218`.
- K3 · after_stage2/open · 계보 제안 서비스 · 정본 `dev-package/work-items.yaml:1309`.
- K4 · after_stage2/open · 자연어 검색 서비스 · 정본 `dev-package/work-items.yaml:1322`.
- K5 · after_stage2/open · 제안 원장 · 정본 `dev-package/work-items.yaml:1335`.
- 2단-격자전용-실패3건-처분 · stage2/deferred · 실패로 굳은 격자 전용 업로드 3건의 처분 (`〈120〉` 3건) · 정본 `dev-package/work-items.yaml:1517`.
- LV-3 · after_stage2/open · 「CoLAB에서 가공됨」 표식 — 레벨 표시 옆 작은 표식 ＋ 계보 그래프 노드 구분 · 정본 `dev-package/work-items.yaml:1658`.
- LV-4 · after_stage2/open · 계보 관계를 지울 때 부모 이름을 상수로 복사해 남긴다 (링크는 없다) · 정본 `dev-package/work-items.yaml:1697`.
- VZ-1 · out_of_scope/deferred · 2D 시각화의 경계·점 표현 — 범위 밖 (벡터 원천 0건) · 정본 `dev-package/work-items.yaml:1727`.

## 미측정·후속

- 현재 실행 서버/승인된 테스트 계정/데이터셋, 실제 브라우저 여정, 현 CI 결과, 현재 gate 결과는 미측정. 메인이 해당 조사·실행 결과와 취합해야 한다.
- J-1 범위 및 TL-2 판정 환경 불일치는 문서 대조 후 대장부터 정정할 후보. 본 조사에서 판정/수정하지 않았다.
- archive upload-reaper 태그는 존재만 확인. 현재 트리 대비 패치/테스트/대장 번호 충돌은 다음 비교가 필요하다.
- 커밋은 메인의 단일 쓰기/검토 흐름에 맡긴다.

## 최신 CI 정정 — 메인 직접 실측 전달

메인 조회 CI `34216692424`, HEAD `ccf76ec`: core-api success, schema/planning/harness failure. 조사자가 직접 API를 호출한 결과가 아니라 메인의 직접 조회 증거를 전달받아 반영한 값이다. 초판의 core-api 재현 최우선 권고를 철회한다.
