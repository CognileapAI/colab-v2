# Stage 1·2 최종 구현 버전 dev 배포 실측

- 구현 SHA / origin/main / PR #18 merge: `30f5adf6774771c9ca34e2c3a0b92a0648b9cc76`.
- 같은 SHA CI `34577478051` completed/success. dormant-tests·harness-eval은 경로 조건 미실행이며 실행 통과로 세지 않는다.
- 이미지 tar SHA256 `c2c05b6255e6d5ff626da8e3302ed5e1bbf0f861a305ed4104667740a5a363e7`, 298704384 B. 로컬 checksum 전건 일치 뒤 ship exit0.
- fresh backup `2026-09-11T082022Z`: platform 104408 B / AI 5520 B, 두 객체 HEAD 크기 일치. backup exit0.
- up exit0, 두 migration chain 성공. 앱 기동 2026-09-11 08:35:50~51 UTC, 4개 healthy, restart0, pipeline/viz S3 모드.
- CURRENT_SHA `30f5adf67747`; MAIN_SHA `main=30f5adf67747 candidate=30f5adf67747 ancestor=yes`.
- 실제 core config ID `sha256:002b0cf2e76961de591f328f6a1aec039b9c214c51bcd324e87a59ea96bcfe9c`.
- 실제 pipeline config ID `sha256:4b44b93383619688af47ad09593ad5b45daa7ac53de3bb45479a8dd9fac3d33e`.
- 실제 viz config ID `sha256:af13ab7dc206155acff92076716fa725c09fae6bcc2b52ddbc3dc0e1973168ff`.
- 실제 AI config ID `sha256:4a68bbd3bdbb0e3d3b875d6294067e479f312de46dab46a3d84afbc71b62c62a`.
- 공개 index HTTP200 SHA256 `091bfb83b02cfdc07622701c27e22a189bd66f2ab60285ed85b6848bd074870b`, 고정 frontend dist와 일치. f8..30f5 frontend 차이0.
- doctor archive 원격 SHA256 `9115540c051909b57897a40b96163afe4997d5b6bb5580f1363b6840f1829f4f` 확인 후 `/opt/colab-repo` 반입. doctor file SHA256 `860770ca61e282ed5b5a36770109b82f67b1f0f2f87065508ba5f061ef48840f`, 후보와 일치.

## 검사 결과를 분리한다

1. 새 resident ops `deploy-verification.sh`, IMDS 앱 역할: exit1, **13/2/0**. 웹 버킷 HEAD/List 권한 403으로 ③ 웹 버킷과 그 결과를 읽는 ⑩ frontend가 red다. 공개 웹 응답은200이고 배포 파일 hash가 일치한다. 이 실패는 지우거나 부분 성공과 합산하지 않는다.
2. 기존 승인된 일회용 운영자 진단: 동일30f5 이미지·doctor·실제 dev를 대상으로 **단일 실행 exit0, 15/0/0**. 기존 로컬 운영자 프로필을 메모리→SSH stdin→일회용 진단 컨테이너에만 전달했다. 제품 컨테이너 환경·EC2 자격증명 파일 변경0. 원문 `.codex/artifacts/stage12-final-deploy/dev-doctor-30f5.log`.
3. resident `service-health.sh`: exit0, 네 서비스 HTTP200/unit 일치.
4. resident `backup-freshness.sh`: exit0, 기존 check_backups oracle green, 최신 백업 약0.3시간.

**I4 자동 deploy probe는 미완료다.** 운영자 진단15/0/0을 IMDS cron 결과로 바꾸지 않는다. 앱 역할의 권한을 확대하거나 검사 skip을 추가하지 않았다. 수신처·cron·외부 raise/clear도 미실행이다.

f8 rollback 이미지 보존. 실제 S3 회수 apply0, cron 설치0, 외부 전송0. 이후 최종 all 전후 두 실행 각61/0/0 및 TL2 실자료 분류 대조를 마쳤다. TL2 자동 연결·실제 정기 주기는 미완료다. 최신 판정은 [acceptance.md](acceptance.md), 전수 원본의 직접 검증과 보관 한계는 [verification.md](../stage12-final-gates/verification.md)를 따른다.
