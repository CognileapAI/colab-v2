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

## 원격 검토와 반입 준비

- 문서 커밋 a4c257380d73f03c13c406988612ee1e59cdc9a1까지 feature/hsw0312_stage1_2 일반 push 완료. 원격 feature와 로컬 HEAD 일치. main은 변경하지 않았다.
- advisor go/no-go를 거쳐 draft PR https://github.com/CognileapAI/colab-v2/pull/13 생성. 자동 병합·리뷰어 지정 없음.
- CI https://github.com/CognileapAI/colab-v2/actions/runs/34549330140 실패(gate-selftest). 나머지 서비스 4종/프론트/계약/스키마/경계/계획 잡은 성공. 별도 compatibility https://github.com/CognileapAI/colab-v2/actions/runs/34549330209 성공. harness-eval의 성공 표시는 현행 명시 면제 모드이며 실제 Astra 행동 평가로 재사용하지 않는다.
- 로컬 Docker endpoint unix socket 확인 후, 배포 문서에 명시된 arm64 한정 QEMU 등록 완료. 다른 아키텍처 일괄 등록·기존 등록 제거·호스트/socket 마운트는 하지 않았다.
- a4c257380d73에서 build.sh 재실행 성공. core-api/pipeline-worker/viz-render/ai-service/migrator 5개 모두 arm64를 실제 inspect로 확인. `dist/colab-v2-dev-a4c257380d73.tar` 285M, sha 마커도 같은 값이다.
- 판정기 전달용은 dirty tree 복사가 아니라 동일 커밋의 git archive: `dist/stage12-doctor-a4c257380d73.tar.gz`, SHA256 `70d92629d17866832bf3b355c2cfc491cf7c2241f0b8e0658061af1472badfda`.
- 커밋 뒤 exec-bit 188개, generated 13개, contract-breaking 변경 0, work-item-consistency 불일치 0을 재확인했다.
- 다음: SSH 주소 확인 → 현재 dev 단일 doctor·백업·DB 권한/대기 행·디스크·직전 이미지 확인 → CI 결과와 최종 go/no-go → main fast-forward/push → ship/up/frontend → 같은 SHA의 전체 통합검증. 실제 dev 반입과 전체 통합검증은 미실행이다.

## CI 자가검사 결함 보완

- render-latency: 병렬도 0이 venv 부재에 가려 준비 실패로 끝났다. 존재하지 않는 Python 경로를 강제한 회귀시험에서 red 재현 후 입력 검사를 환경 검사 앞으로 이동, 13건 통과.
- ops-observability: 직접 실행하는 Python 2개의 Git 인덱스 모드가 100644였다. NTFS 로컬 실행과 CI가 달랐으며 ops_observability.py/alarm_runner.py를 100755로 기록한다.
- frontend-visual: CI에 agent-browser가 없는데 `_expect.sh`의 FAILURES가 최종 종료에 반영되지 않아 검사 실패를 green으로 표시했다. 공통 최종 판정에 배열 결함을 반영하고 정상/위반 기대와 미선언/준비 실패 조합 4건 추가. 2건 실패를 먼저 재현한 뒤 backup-cron-streak-selftest 20건 통과(실제 cron 설치·실행 아님).
- CI에는 검증된 agent-browser 0.27.0 및 Linux 브라우저 의존 설치를 추가했다. 정상/위반 HTML의 원격 실제 계측은 후속 CI에서 확인하며, 설치만으로 통과를 주장하지 않는다.
- readonly advisor: 전체 selftest 성공을 조건으로 feature 커밋/push 승인. main/배포 승인은 제외; SSH·백업·최종 go/no-go 경계 유지.
- 수정 후 단일 전체 selftest exit 0: 선언 25/실행 23/명시 면제 2, green 23/red 0. 면제는 별도 서비스 잡이 담당하는 stage2-markers-selftest와 service-tests-selftest이며 신규 면제는 없다. 로컬 Chromium 정상/위반 HTML의 실제 계측도 각각 green/red 기대대로 통과. 보고서 `reports/stage12-deploy-preflight/ci-selftest-fix/gate-summary.json`.
- 자가검사 로그의 artifact-ownership SQL 주석 heredoc에서 식별자 2개가 셸 명령 치환되어 command-not-found 경고가 남았다. 주석 외 SQL과 해당 19케이스 판정은 성공했으며, 이 실행을 무경고로 보고하지 않는다.
- 보완 커밋 `ab9491c7040bb919594e818393b5180e17cf0d3e` feature push 완료, 로컬/원격 SHA 일치. 후속 CI https://github.com/CognileapAI/colab-v2/actions/runs/34550271176 진행 중(성공 미확정). 커밋 뒤 대장 180건 불일치 0 재확인. ARM64 이미지 기준은 여전히 a4c257380d73이며 이번 변경은 CI/자가검사/운영 Python 실행 모드/문서다. 반입 전 최종 소스·doctor archive·이미지 기준을 다시 맞춘다.

## 세션 재개 — 접근과 PR 설명

- 지정 세션 `01a08b38-cbc1-7233-beba-35108150ccab` 기록과 현재 브랜치를 대조했다. 위 CI는 재조회 결과 completed/success이며 PR #13의 표시된 check 전부 pass다. harness-eval의 명시 면제는 실제 Astra 평가 성공이 아니다.
- 사용자의 재접속 요청 뒤 로컬 운영자 설정의 SSH 주소로 실제 접속 성공(aarch64). EC2 DescribeInstances는 여전히 UnauthorizedOperation이지만 SSH는 가능하다. 주소 재질문은 불필요했다.
- 현재 dev는 `09e2b9b2db1a`, 서비스 4개 healthy. 같은 기존 배포의 이미지·판정기 트리·state로 단일 deploy_doctor exit 0, 항목 15/실패 0/미검사 0을 확인했다. 새 Stage 1·2 배포 검증으로 세지 않는다.
- 디스크 여유 3.8GB, inode 사용 2%, 메모리 available 2895MB. 신규 Stage 2 처리 대상은 colab_backup 읽기 전용 조회에서 대기 업로드 0/파일 참조 0/대상 0바이트. 배포 직전에 다시 센다.
- 소유자 읽기 전용 조회: colab_owner의 public 신규 테이블에 colab_app SELECT/INSERT/UPDATE/DELETE 기본 권한 4종 존재. 마이그레이션 직후 새 테이블 실권한 확인은 별도다.
- 정본 backup.sh 성공: `2026-09-11T013622Z` platform 77894B/AI 5520B, S3 업로드 뒤 크기 대조 성공. 이번 실행으로 복원 시험까지 했다고 주장하지 않는다.
- 이전 배포의 compose/up.sh/dev.env/CURRENT_SHA/MAIN_SHA를 서버의 비공개 rollback 디렉터리에 보존했고, 이전 이미지 5개 불변 태그·arm64 존재를 확인했다. 새 0024를 모르는 옛 migrator로 up.sh를 실행하는 롤백은 피해야 하므로 앱만 되돌리는 절차와 호환성을 최종 검토한다.
- 사용자 추가 요청: PR #13에 이번 신규 개발 기능 목록을 쉬운 HTML로 포함한다. `docs/reviews/stage12-pr13.html`에서 기존 기능과 신규 구현, 로컬 검증과 dev 완료를 구분한다. HTML 추가 후 최종 소스·이미지·판정기 기준을 고정한다.
- HTML 검증: agent-browser로 Stage 1 2묶음/Stage 2 6묶음 표시, 모바일 키보드 Enter로 모두 보기 8묶음 복원, 390·1440px 가로 넘침 0, 외부 리소스 요청 0. 모바일에서 포인터 click이 상태를 바꾸지 않은 실행은 통과로 세지 않았고 키보드 경로를 확인했다. HTML·브라우저 캡처 PNG를 PR에 함께 연결한다. 제품 E2E 증거와 구분한다.
