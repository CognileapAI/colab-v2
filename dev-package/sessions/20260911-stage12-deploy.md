# Stage 1·2 전체 구현 배포·통합검증

## 승인과 범위

- 사용자 요청: 「푸시 배포 한다음에 전체 통합검증하자」.
- 현재 eac2f0b는 내부 API 헤더 수정뿐이고 Stage 1·2 대부분이 미커밋임을 설명했다.
- 「관련 없는 변경은 제외하고 Stage 1·2 구현 전체를 커밋·푸시 → dev 배포 → 전체 통합검증」 범위 질문에 사용자 「어」로 승인했다.
- 배포 원천은 main, 대상은 기존 AWS dev다. prod, Terraform apply, 별도 데이터/S3/캐시 삭제, cron 설치와 외부 알람 통지는 포함하지 않는다.
- 새 원본 회수는 observe, S3 미리보기 회수는 관측 전용을 유지한다. 기존 만료 미완결 전송의 자동 정리 동작과 신규 회수 활성화를 구분한다.

## 실행 계획

- [x] 최신 origin/main 조회와 미커밋 변경 분류: origin/main 대비 HEAD 뒤 0/앞 1.
- [x] 마이그레이션·계약·생성물·서비스·프론트 사전 검사와 배포 안전성 독립 검토.
- [x] 관련 구현을 논리 단위로 커밋하고 코드 기준 SHA를 고정(아래 참조; 배포 이미지 생성은 별도).
- [x] 고정 소스의 arm64 이미지 5개와 프론트 빌드, 백업·롤백 대상 확인.
- [x] 최종 go/no-go 뒤 승인된 main 반영·push 및 dev 배포.
- [x] 동일 배포 SHA에서 deploy_doctor 전항목 단일 실행, 전체 게이트, 핵심 실제 사용자 여정 검증 실행(전체 통과 아님; 아래 잔여 참조).
- [x] 원격 CI·잔여 조건 확인 후 대장과 인계 갱신(미충족 항목 상태 유지).

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

## 최종 반입 전 판정

- PR HTML·PNG·기능 목록 반영 커밋 `9e3ff19f6d27306e0e359e8ff2d829f8f4a7452f`. PR #13 본문에 링크·Stage별 목록 존재를 되읽어 확인했다. 최종 CI `34551919730` completed/success, compatibility `34551919760` 성공.
- 같은 SHA 이미지 5개 arm64 확인, tar 285MB·SHA256 `8e84e69d4f15735583c7ce58805edf5a4c45003dcc00ef5bc8e89d4dfc0d38ee`. 동일 SHA git archive 판정기 SHA256 `34020e17f9431de52a769efd7425917adeaacadb0f9b8b44f1030f54d4761e87`.
- 프론트 재빌드 성공, index SHA256 `35cd00d9dc361cc95a3cf3b1282d17b4fb2de516a77f6ef862f9d41d2e55248c`. 기존 웹 버킷 파일을 로컬 rollback 사본에 내려받았으며 이전 index SHA256 `0fcb3cbfeb413e1dca6203910bd530eb0564c39ef78433aa9b8bbee6b5a3311d`.
- 이전 `09e2b9b2db1a`의 소스·시험을 git archive로 분리해 새 0024 선언 스키마의 일회용 DB에 연결했다. 업로드·등록·상세·연구실 경계·세션 시험 105 passed/실패 0/13.89초. 이는 이전 소스의 호환 시험이며 운영 DB 쓰기·운영 이미지 재기동 시험은 아니다. 임시 DB만 종료했다.
- 새 제약: uploads/ 613객체·4,740,251,471바이트가 현재 작업 상한 1GiB를 넘는다. S3 관측은 다운로드 전 총량 검사에서 ready=false로 멈추므로 회수 관측 완료는 불가능하다. 원본 부재나 정상 0건으로 해석하지 않는다. 대장 BF-12 open 유지, TL-2 선행 미충족 유지.
- 독립 최종 검토: CI 성공 뒤 dev 반입 가능, 회수 관측·Stage 전체 완료는 보류. 총량 초과 시 다운로드·삭제 없이 다음 재생성 주기를 계속하는 코드를 확인했다. 배포 뒤 실제 준비 실패 로그와 재생성 지속성을 검증한다. 상한 증가·원본 삭제·검사 제거·디스크 확장은 하지 않는다.
- 롤백은 보존한 이전 compose와 `COLAB_IMAGE_TAG=dev-09e2b9b2db1a`를 명시해 앱 4종만 `up -d --no-deps`로 되돌린다. 옛 migrator/up.sh를 실행하거나 DB를 downgrade하지 않는다. 웹은 보존한 정적 파일을 정본 deploy_web 경로로 복원한다.
- main fast-forward 전에 기존 CLAUDE.md의 끝줄 변경만 이름 붙인 stash로 잠시 보존했다. main을 같은 SHA로 fast-forward한 뒤 해당 stash만 복원한다. 다른 stash와 미추적 산출물은 보존한다.

## dev 배포와 실제 사용자 여정

- main을 `9e3ff19f6d27306e0e359e8ff2d829f8f4a7452f`로 fast-forward/push했다. PR #13은 같은 커밋으로 2026-09-11T01:51:45Z merged. 앞서 보존한 CLAUDE.md 변경은 해당 stash만 pop하여 복원했으며 기존 다른 stash는 유지했다.
- 정본 ship.sh → 동일 SHA 판정기 archive 반입 → platform migration → up.sh → deploy_web.py 순서로 성공. 이미지·archive 해시 대조 성공, 새 platform 테이블 3개에 앱 CRUD 4종 권한 확인. 권한 확인 직후 진단 SQL의 테이블명을 잘못 써 별도 조회가 exit 1이었으며, 실제 스키마는 후속 doctor가 확인했다.
- 웹 96파일/6,357,419바이트 게시, index는 마지막 업로드. 배포 후 단일 doctor exit 0, green 15/red 0/미검사 0. platform 0024·AI 0007, RLS 39테이블, 서비스 4개 healthy, main/배포 SHA 일치. 기존 배포의 사전 doctor와 구분한다.
- 로그: `.codex/artifacts/stage12-{ship,up,web}-9e3ff19.log`, `.codex/artifacts/stage12-deployed-doctor.log`. 서버 작업 여유 3.2GB. S3 관측은 실제 준비 실패 로그를 남겼다. 로그의 일반 오류 문구 자체가 용량 원인을 표시하지는 않으며, 사전 실측 총량이 1GiB 상한을 초과한 사실을 함께 기록한다.
- agent-browser로 dev에 로그인하고 실제 8×8 GeoTIFF(640바이트, EPSG:4326, 값 0~63) 업로드·분석·등록을 수행했다. 자료명 `TEST Stage12 20260911 9e3ff19 — 합성 8×8`, dataset `01M2732F9RE8XV9CSG46J240CX`. 실제 관측값이 아닌 검증용 합성 자료임을 설명에 표시했다. 자료는 삭제하지 않고 dev에 남겼다.
- 등록 후 미리보기 이미지 naturalWidth 1024 확인. 팔레트 다색-무지개/색 구간 3개로 변경한 뒤 이미지 주소 변경 및 렌더 완료를 확인했다. 같은 URL을 다시 열어 제목·설명·파일·미리보기와 로그인 상태 유지 확인. 목록의 지도 있음은 합성 자료 1행, 지도 없음은 해당 자료 제외 확인. 로그아웃 뒤 로그인 입력 화면 복귀 확인.
- 최초 ‘나만 보기’로 등록했을 때 만든 계정도 상세는 요약만 보이고 편집은 가능했다. 독립 코드 대조에서 이전 배포와 같은 접근 판정임을 확인했다: locked는 유효 grant가 필요하고 작성자 자동 grant가 없다. Stage 변경의 회귀로 단정하지 않으며, ‘나만 보기’ 문구와 기존 정책의 불일치 후보로 남긴다. 검증을 계속하기 위해 본 합성 자료만 ‘연구실 구성원 전체’로 편집·저장했다.
- S3 관측 준비 실패 이후에도 위 신규 미리보기와 팔레트 재생성이 성공했다. 초기 임시 화면의 순간적인 표시 시간, 격자 재사용·기본값 권한 등 전체 9개 수용 여정은 이번 확인 범위가 아니다.
- 브라우저의 offscreen click 무반응은 focus/Enter 뒤 실제 저장 결과로 확인했다. URL glob·존재하지 않는 화면 문구로 수행한 wait timeout 2건은 성공으로 세지 않았다. 초기 로그인 1회 실패는 자격 파일의 설명문을 계정값으로 읽은 시험 입력 오류이며 올바른 계정으로 재확인했다.
- 여정 캡처·비밀정보 없는 요약: `.codex/artifacts/stage12-dev-journey/`. 배포 후 단일 전체 게이트 결과와 후속 입력 보정은 아래에 분리 기록한다.

## 배포 후 전체 검사 — 첫 실행과 후속 확인

- 배포 SHA `9e3ff19f6d27306e0e359e8ff2d829f8f4a7452f`, `all -j 1`, 2026-09-11T01:55:11Z~02:20:02Z. 최종 exit 1, **green 54 / red(판정) 4 / red(준비) 2**. report `reports/stage12-deployed-all/gate-summary.json`과 개별 `.out/.rc/.span` 보존. 병렬 안전성 미선언 3종도 단독 실행했으며 결과에 포함했다. 작업 중 변경은 설명·기록 파일뿐이며 제품 코드는 배포 SHA와 같다.
- 서비스: core 1060·AI 138·viz 413·pipeline 275 passed, skipped/failed/errors 0, deselected 각각 6·26·42·50. frontend 94files/1204 passed/failed 0. pipeline 경고 22, viz 경고 1을 무경고로 표현하지 않는다. 대장 180건 불일치 0, 산문 파싱 대상 밖 9건은 안 본 자리로 유지한다.
- 최초 판정 실패 4종(schema-diff·autometa-loss·preview-tile-slot·artifact-ownership)은 기록된 예전 로컬 DB 주소에 연결하지 못했다. 실제 원인은 입력 연결이지만 게이트가 낸 exit 1과 판정 실패 계수는 바꾸지 않았다. 준비 실패 2종(frontend-visual·harness-eval)은 대상/실행 선언 누락이며 exit 78을 보존했다.
- 후속은 전체 재실행이 아닌 해당 6종의 단독 실행이다. `reports/stage12-deployed-supplement/`에 각각 기록했다. 홈 설정을 수정하지 않고 현재 로컬 staging DB의 주소만 실행 환경에서 보정했다(같은 DB·자격·읽기 전용 옵션·산출물 루트). 이 3종의 실물은 기존 `09e2b9b2db1a` 로컬 staging이며 새 AWS dev 데이터 검증으로 바꾸어 말하지 않는다.
- schema-diff: 새 일회용 platform/AI DB에 각각 upgrade head 후 선언=적용, **1/0/0**. 임시 DB 종료, 기존 staging/dev DB migration 아님. autometa-loss: 발행 6/반영 6/면제 0, **1/0/0**. preview-tile-slot: 발행 업로드 2/타일 146/사용 가능 146/면제 0, **1/0/0**.
- artifact-ownership: **0/1/0**. 로컬 staging 산출물 158벌 = 살아 있음 120/접수분만 0/고아 19/판정 불가 19. 대상 밖 지도 타일 146벌은 별도다. 고아 키의 미선언을 확인했으며 새 면제·보류 선언을 넣어 통과시키거나 산출물을 삭제하지 않았다. 전체 스냅숏은 로그가 가리키는 `/tmp/artifact-owner-Rabhx2/snapshot-20260911T022053Z.tsv`에 보존됐다.
- frontend-visual: dev 로그인 페이지 1건·라이트/다크 캡처 2장, 작은 글자 0/대비 실패 1, **0/1/0**. `button.login-submit` 3.41:1. 실제 DOM에서 disabled=true, 글자 rgb(255,255,255)/배경 rgb(132,140,148)/opacity 1 확인. 해당 로그인 JSX/CSS는 09e2~9e3 사이 diff 0이며 이번 회귀로 단정하지 않는다. 비활성 컨트롤에 대한 현행 검사 기준의 적용을 검토할 잔여로 남기고 허용 목록은 바꾸지 않았다.
- harness-eval: 현행 스크립트/CI의 승격 전 정책대로 명시 면제 **20과제 미실행**, **1/0/0**. 실제 Astra 행동 평가가 아니다. 이 면제를 포함한 후속 단독 6종은 **green 4 / 판정 실패 2 / 준비 실패 0**이며 최초 all의 54/4/2와 서로 다른 실행이다. 단일 전수 green이라고 합쳐 보고하지 않는다.

## 수용 대조와 인계

- 사용자 추가 산출물: PR #13에 신규 Stage 1 2묶음/Stage 2 6묶음 목록, 자체 실행 HTML, 다운로드 링크, 실제 HTML 캡처 PNG를 포함했다. 데스크톱·모바일 가로 넘침 0, Stage 필터·키보드 동작, 외부 리소스 0을 확인했다. 독립 문서 검토에서 필수 수정 없음. 처음 대기 문구는 실제 배포·검사 결과로 갱신한다.
- 배포 요청의 실행은 main push·dev 반입·단일 doctor·전체 검사·핵심 사용자 여정까지 수행했다. **미달:** 검사 2종 잔여, BF-12 관측 준비 실패와 TL-2 선행, J-1 나머지 dev 수용 여정, 기존 운영/검토 라운드의 완료 조건. 전체 Stage 완료로 닫지 않는다. **초과:** 사용자 추가 요청으로 승인된 ELI5 HTML/PNG 외 제품 구현 확대 0.
- 현재 대장 집계: stage1 done 53/비연기 미완 9/deferred 1, stage2 done 86/비연기 미완 8/deferred 2. 상태를 이번 배포만으로 done으로 올리지 않았다. 다음은 캐시 소유 판정·비활성 버튼 검사 적용 범위 확인, BF-12 제한 공간 내 전수 관측 보완, 나머지 J-1 dev 수용 및 운영 완료 조건이다. 원본 삭제·cron·외부 통지·prod·Terraform apply는 승인 범위 밖으로 유지한다.
- 문서 후속 커밋이 main을 전진해도 실행 제품은 `9e3ff19f6d27`이다. 설명 문서 변경만으로 이미지·앱을 재배포하지 않으며 기존 CLAUDE.md 사용자 변경과 다른 stash를 보존한다.
- 최종 기록 갱신 뒤 work-item-consistency 단독 exit 0/불일치 0을 확인했다(파싱 대상 밖 9건 유지). 독립 최종 검토는 문서 수용 approve이며 전체 검사 통과나 Stage 완료 승인이 아니다. PR 본문의 최초 전수와 후속 6종 결과·명시 면제·실패 2종을 그대로 유지한다.
