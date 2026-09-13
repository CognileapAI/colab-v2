# local-stage 전환과 ST 배포

승인: [환경 브랜치 intent](../intent/2026-09-13-environment-branches.md).

- [x] 기존 검색 수정 보존, local-stage 브랜치 생성(main 7446eb7d 기점).
- [x] 브랜치 정본과 CLAUDE 진입점 갱신.
- [x] 실제 ST cron에 COLAB_PIPELINE_BRANCH=local-stage 명시. 다른 cron 항목 보존·재조회 확인.
- [ ] 변경 커밋·origin/local-stage 반영.
- [ ] 백업·migration 0032·ST 배포 및 health/chain 검증.
- [ ] 배포 결과·후속 기록.

전환 전 ST 실물은 이미지 7446eb7dd428, 자동배포 worktree는 staging/auto-deploy 브랜치의 clean 7446eb7d였다. 과거 ST 실측 당시 acf2532f와 시점이 다르다.
검색 제품 변경은 이전 core1220 및 RLS/스키마 검증을 유지하며 이번에는 배포·전략 문서만 추가한다. main·DEV·운영 배포는 수행하지 않는다.

후속: PR 최초 릴리스 전 production 생성, AWS 운영 배포 원천 검사·동일 산출물 승격·브랜치 보호 설정을 준비해야 한다. 운영 환경 구축은 이번 범위 밖이다.
