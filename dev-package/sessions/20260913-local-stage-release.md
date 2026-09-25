# local-stage 전환과 ST 배포

승인: [환경 브랜치 intent](../intent/2026-09-13-environment-branches.md).

- [x] 기존 검색 수정 보존, local-stage 브랜치 생성(main 7446eb7d 기점).
- [x] 브랜치 정본과 CLAUDE 진입점 갱신.
- [x] 실제 ST cron에 COLAB_PIPELINE_BRANCH=local-stage 명시. 다른 cron 항목 보존·재조회 확인.
- [x] 변경 커밋·origin/local-stage 반영.
- [x] 백업·migration 0032·ST 배포 및 health/chain 검증.
- [x] 배포 결과·후속 기록.

전환 전 ST 실물은 이미지 7446eb7dd428, 자동배포 worktree는 staging/auto-deploy 브랜치의 clean 7446eb7d였다. 과거 ST 실측 당시 acf2532f와 시점이 다르다.
검색 제품 변경은 이전 core1220 및 RLS/스키마 검증을 유지하며 이번에는 배포·전략 문서만 추가한다. main·DEV·운영 배포는 수행하지 않는다.

후속: PR 최초 릴리스 전 production 생성, AWS 운영 배포 원천 검사·동일 산출물 승격·브랜치 보호 설정을 준비해야 한다. 운영 환경 구축은 이번 범위 밖이다.

## 배포 결과

- 검색 수정 `75cd069b`, 전략 문서 `761aefac98b8`를 origin/local-stage에 push했다. 배포 직전 clean 및 HEAD=origin/local-stage 일치를 확인했다.
- 배포 실행 id `st-e1989fca77b74cb19ad1c262fb5392a6`: deployment=verified, deploy/verify=passed, exit 0. 이미지 5종은 `761aefac98b8`이다.
- 사전 백업 platform/ai 두 프로파일 green. platform `0032_private_owner_access`, ai `0007_merge_vocab_and_category`. 배포 판정 15건·체인 2건 모두 통과, SKIP 0.
- 실제 브라우저: 기존 합성 dataset `01M2BF9P79K1APP13JZAZE3J61`을 UI로 나만 보기 저장 후 새로고침. accessState=잠김, bodyAccessible/canDownload=true. 근거 GET 200·reviewed revision1 유지, 다운로드 ticket/바이트 GET 200·430bytes 확인.
- 같은 UI에서 `ST검색검증20260913 검증용 결측률 0%` 검색 → 15건 중 대상 1건, 품질 미확인 설명 유지, 결과 클릭 시 동일 상세 이동. 과거 12건 확대 현상 해소. 이번에는 근거 내용 재편집·저장은 반복하지 않았다.
- 실제 Sonnet 및 ST 타 계정 거부 여정은 이번에 미실행. 비소유자/타 연구실 거부는 앞선 core1220 회귀 근거다. K4 전체 품질 완료로 선언하지 않는다.
- 외부 알림은 송신하지 않았다. 별도 비연결 로컬 spool에 queued 상태로 보존했다. 운영 relay 기본 spool을 사용하지 않았다.
- 로그: `/tmp/colab-local-stage-deploy.log`. 실행기 상세: `.git/deploy-releases/st-e1989fca77b74cb19ad1c262fb5392a6/`. 브라우저 증거: 사용자 캐시 `colab-local-stage-release/`의 browser-plan.json, private-owner-check.json, search-quality.png.
- 자동배포는 전환 중 잠시 정지했다. 기존 pipeline 잠금 비점유 확인 후 직접 배포했고, 마지막 기록 커밋까지 전용 배포 worktree를 fast-forward한 뒤 local-stage source/비연결 spool을 명시해 재개한다. 다음 새 커밋부터 local-stage를 감시한다.

## 배포 도구 후속

현재는 실제 cron 환경 선언으로 원천을 고정했다. 기존 스크립트의 기본값(main), public deploy의 브랜치 강제 검사, schedule installer의 환경 보존은 아직 수정하지 않았다. 재설치 때 반드시 local-stage 환경 선언을 보존해야 한다. 이를 포함한 환경별 원천 강제와 PR 운영 배포 준비는 다음 구현 작업이며 현재 강제 완료로 주장하지 않는다.
