# 온톨로지 삭제 차단

사용자 승인: “온톨로지 DB는 지워서는 안된다”, “기계쩍으로 차단하는 보호장치 있어야지”. 작업 branch codex/ontology-protection, 통합 대상 local-stage. main/DEV/운영 승격 없음.

- [x] 일회용 DB에서 현재 배포 역할의 삭제 허용을 실패 시험으로 재현.
- [x] colab_ai DB/public/D9 테이블 소유권을 NOLOGIN 보호 역할로 분리. 배포 역할 SELECT/INSERT/UPDATE만, 앱 SELECT만 허용.
- [x] 배포 bootstrap 반복 실행에도 보호 유지. 정상 seed upsert/버전 관리 지속성 검증.
- [x] 온톨로지 제자리 DROP 복원과 영구 저장소 대상 테스트 초기화 거부.
- [x] 일회용 실제 PostgreSQL 음성시험 및 관련 기존 검사·독립 리뷰.
- [x] 백업 후 ST 보호 적용, 내용 전후 hash/권한 실측, 결과 기록.

보호 해제용 환경변수/CLI 우회는 만들지 않는다. 보호 테이블의 DDL 변경은 기존 배포 자격으로 실패하도록 하고, 향후 명시적으로 검토한 관리 작업으로만 수행한다. 백업은 계속 가능해야 한다.
호스트 root/Docker 및 PostgreSQL superuser는 여전히 이 권한 경계를 해제할 수 있다. 해당 관리자 권한의 분리는 별도 보안 경계이며 이번 DB 권한 보호를 그 대체로 주장하지 않는다. PGDATA는 두 DB 공용 bind mount라 실제 파일 삭제 위험은 남는다.

## ST 적용과 검증 결과

- 초기 일회용 PostgreSQL RED: 50개 검사 중 20개 실패, 배포 역할의 삭제가 허용되는 결함을 실제 재현했다. 실제 ST에는 파괴 시험을 하지 않았다.
- 최종 일회용 삭제/복원거부/변조/권한상속/재배포 반복 검사 57건 전부 통과. 의도한 INSERT/UPDATE와 Alembic 버전 표 쓰기도 확인했다.
- 복원 자기검사 44건 전부 통과. AI 서비스 168건 전부 통과(skipped/deselected/failed/errors 0). 대장 일치 검사 통과.
- 중간 준비 실패: AI 실행기에 DB 주소가 없어 26개 setup error가 났다. 일회용 DB를 준비해 다시 실행했다. 첫 tmpfs 판정은 Docker의 Mounts에 tmpfs가 표시되지 않아 정상 일회용 DB를 거부했다. HostConfig.Tmpfs와 PGDATA 경로를 함께 검사하도록 수정 후 전체 AI 시험을 통과했다.
- 독립 리뷰에서 AWS 공유 bootstrap 회귀·필수 테이블 view 대체·상속 관리자 역할 우회를 지적했고 수정 후 ST 현재 head 적용 GO를 받았다.
- ST 적용 전/후 정상 백업 두 프로파일 모두 green: ai-20260913T160434.sql.gz, ai-20260913T160546.sql.gz. platform 백업도 함께 통과했다.
- 실제 ST 설치: pipeline 잠금 획득 후 ontology-protection.sql 적용, read-only checker ONTOLOGY_PROTECTED. 테이블 5개/103행의 정렬 JSON sha256이 전후 모두 일치했다. AI 컨테이너의 실제 앱 자격으로 GK2A→GK-2A 확장 성공.
- 소유권/ACL만 변경했으며 DB 행 수정·삭제, 스키마 구조 migration, 앱 재시작, AWS 배포는 하지 않았다.
- 원본 로그: `/tmp/colab-ontology-{red,green,restore,ai-tests-ready,backup-before,backup-after,ledger}.log`. 전후 hash는 사용자 캐시 `colab-ontology-protection/before.json`, `after.json`에 보존한다.

## 전체 요구의 남은 경계 — ONTO-PROTECT open

일반 배포/앱 자격의 삭제 차단은 ST에서 실제 적용됐다. 그러나 현재 에이전트 실행 계정은 Docker 그룹과 관리자 경로를 사용할 수 있다. postgres superuser 접속 또는 PGDATA 파일 직접 삭제까지 차단하려면 관리자 자격을 에이전트가 접근할 수 없는 별도 주체로 옮기고, 배포를 제한된 명령만 수행하는 서비스로 분리해야 한다. 그 접근권한 분리는 아직 수행하지 않았으며 전체 삭제불가 완료로 보고하지 않는다.

AWS 보호도 미적용이다. 공용 AWS bootstrap은 기존 경로를 유지하고 ST 정책을 자동 적용하지 않는다. 운영 승격 전에 별도 RDS 역할·소유권 정책 검증이 필요하다. UPDATE에 의한 내용 변경은 허용되고 백업으로 보완한다.
