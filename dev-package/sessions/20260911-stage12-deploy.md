# Stage 1·2 전체 구현 배포·통합검증

## 승인과 범위

- 사용자 요청: 「푸시 배포 한다음에 전체 통합검증하자」.
- 현재 eac2f0b는 내부 API 헤더 수정뿐이고 Stage 1·2 대부분이 미커밋임을 설명했다.
- 「관련 없는 변경은 제외하고 Stage 1·2 구현 전체를 커밋·푸시 → dev 배포 → 전체 통합검증」 범위 질문에 사용자 「어」로 승인했다.
- 배포 원천은 main, 대상은 기존 AWS dev다. prod, Terraform apply, 별도 데이터/S3/캐시 삭제, cron 설치와 외부 알람 통지는 포함하지 않는다.
- 새 원본 회수는 observe, S3 미리보기 회수는 관측 전용을 유지한다. 기존 만료 미완결 전송의 자동 정리 동작과 신규 회수 활성화를 구분한다.

## 실행 계획

- [x] 최신 origin/main 조회와 미커밋 변경 분류: origin/main 대비 HEAD 뒤 0/앞 1.
- [ ] 마이그레이션·계약·생성물·서비스·프론트 사전 검사와 배포 안전성 독립 검토.
- [x] 관련 구현을 논리 단위로 커밋하고 코드 기준 SHA를 고정(아래 참조; 배포 이미지 생성은 별도).
- [ ] 고정 소스의 arm64 이미지 5개와 프론트 빌드, 백업·롤백 대상 확인.
- [ ] 최종 go/no-go 뒤 승인된 main 반영·push 및 dev 배포.
- [ ] 동일 배포 SHA에서 deploy_doctor 전항목 단일 실행, 전체 게이트, 실제 사용자 여정 검증.
- [ ] 원격 CI·잔여 조건 확인 후 대장과 인계 갱신.

전체 통합검증은 사용자 요청대로 배포 뒤 수행한다. 사전 검사는 배포 실패·스키마 손상을 막는 관련 검사이며 전체 완료 판정이 아니다.
배포 및 검증이 끝나기 전에는 Stage 1·2 완료를 선언하지 않는다.

## 사전 실측과 보완

- migration-single-head: platform 28개/단일 head 0024, AI 8개/단일 head 0007.
- 최초 schema-diff는 설정된 시험 DB 연결 실패로 exit 1(러너 분류: 판정 실패). 실제 원인은 사라진 시험 DB 주소이며, 운영 DB로 대체하지 않는다. 별도 일회용 DB에서 재검증한다.
- 계약 lint 3건, HEAD 대비 breaking 0, 생성물 13개 일치, 프론트 타입 오류 0.
- core 1060 passed/skip 0/deselect 6, pipeline 274/0/50, viz 413/0/42, AI 138/0/26. pipeline 서비스 실행 뒤 아래 회귀시험을 추가했으므로 최종 서비스 재실행이 필요하다.
- 독립 검토에서 dev Stage 2 미선언 발견. 배포 설정을 실제 IngestionService에 적용해 NumPy 파일의 프로필 누락 1 failed를 재현했다. Stage 2 on과 공유 미리보기 경로를 선언한 뒤 동일 시험 1 passed(2.43초).
- 스위치 활성화로 기존 완료/실패/등록 행을 강제 재처리하지 않는다. 기존 미완료 대기 행은 새 파이프라인으로 처리되므로 반입 전 대기 계수와 디스크 여유를 확인한다.
- AWS 로컬 운영자와 colab-dev 프로필 모두 EC2 주소 조회 UnauthorizedOperation. 키 파일은 있으나 현재 SSH 주소가 확인되지 않아 사용자에게 요청했다. 권한 확대·네트워크 설정 변경은 하지 않는다.
- 예비 advisor 판정은 즉시 배포 reject: 고정 소스/빌드/백업/실제 env/단일 doctor 근거가 필요하다. Stage 2 설정 보완 권고는 수용했으나 최종 배포 승인 판정과 구분한다.
- 프론트 최신 전체 시험: 94 files, 1204 passed, 실패 0. `npm --prefix frontend run build` 성공(198 modules); JS 청크 500kB 초과 경고 1건은 남아 있다.
- 격리 schema-diff 첫 재시도는 SQLAlchemy 전용 URL scheme을 pg_dump에 전달해 exit 1. libpq 호환 URL로 시험 입력을 교정한 별도 실행에서 platform/AI 모두 upgrade head 후 선언=적용, exit 0. 게이트 판정부·비교 범위는 변경하지 않았다. 시험용 DB 컨테이너만 runner가 정리했으며 제품 데이터는 삭제하지 않았다.
- 위 결과 경로: `reports/stage12-deploy-preflight/`. 최초 연결 실패, 격리 입력 오류와 최종 성공은 서로 다른 보고서 디렉터리로 보존한다.
- 0024 drift 재실행: head green/0023 red/downgrade red 기대 판정과 0023 shape 복원 모두 통과. 실제 운영 downgrade는 수행하지 않았다.
- 최종 워커 서비스, import 경계 8/8, 금지 import 163파일/위반 0, DB 경계 376대상/위반 0, service selftest, ops 관측/자가시험, 대장 180건/불일치 0 통과. 대장 파싱 대상 밖 9건은 전수 확인으로 주장하지 않는다.

## 로컬 커밋과 빌드

- e735ee2: 시험 병렬화(19파일).
- 32af585: 서비스 추적·운영 관측(31파일).
- 5d9ab3cfb1f1cd2bdd8275fe5fb073835ba541ba: 계약과 소비자를 포함한 기능 통합·dev Stage 2 설정(82파일).
- 위 코드 기준에서 services/frontend/contracts/db/infra/gates와 격자 여정 스크립트의 잔여 tracked/untracked 변경 0을 확인했다. `.codex/artifacts`는 커밋 대상에서 제외하고 그대로 보존했다.
- 최초 ARM64 빌드 실패: core-api의 RUN에서 `exec format error`, exit 1. buildx 지원은 amd64뿐이며 ARM QEMU 등록이 없다. `infra/dev/README.md` 진단표의 등록 절차를 별도 검토한다. 이 실패 실행을 이미지 5개 생성 성공으로 세지 않으며 기존 dist 산출물을 현재 빌드로 반입하지 않는다.
- 프론트 산출물 SHA256: index `35cd00d9dc361cc95a3cf3b1282d17b4fb2de516a77f6ef862f9d41d2e55248c`, JS `74d99942b4540c836fd52b069586a6509ab3859a4141da6f1eaaf821d805c5f4`, CSS `50da61bf6fe3375d1714c97f96fdfb018e68063a42f3a89acf37cb307771a7bb`.
