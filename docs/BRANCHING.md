# BRANCHING — 브랜치·태그 수명 정본

> 요지 6줄과 이 파일 링크는 `CLAUDE.md §10`. 배포 절차 정본은 `docs/DEPLOY.md`, 규약은 `.claude/rules/deploy.md`.
> 이 문서는 **어느 브랜치가 어디서 나고 어디로 돌아가며 언제 사라지는가**만 정한다. 배포 값·자원 목록은 여기 두지 않는다.
> 출처 = `dev-package/intent/2026-09-08-r-d.md` 「원한 결과」 축 ① · spec `dev-package/prd/specs/R-D.md` · 실측 `dev-package/sessions/WU-D4-branches-20260908.md`.

---

## 1. 현재 정책 — develop 개발 원천·product 운영 원천

승인 근거: `dev-package/intent/2026-09-15-develop-product-deployment.md`.
실행 계획: `dev-package/prd/rounds/R-DEVELOP-PRODUCT.md`.
2026-09-15 정책 개정이며 **원격 전환·운영 배포 완료 기록이 아니다**. 전환 실측은 `dev-package/reports/develop-product/transition-inventory.md`로 확인한다.

<!-- rule6:begin -->
1. 기본 브랜치 `develop`이 dev 배포 원천이며 `product`가 운영 배포 원천이다. 후보 SHA는 대상 환경의 원격 원천 브랜치에 포함되어야 한다. 이름이 없는 경우 main으로 되돌아가지 않는다.
2. staging은 `integration/*`의 리허설 환경이다. 원장에 브랜치 이름을 함께 기록한다.
3. `integration/r-N`은 develop tip에서 시작하고 develop으로 ff-only 통합한 뒤 삭제한다. main에서 develop으로 실제 전환되기 전 준비 작업은 현재 main tip을 기준으로 한다.
4. `lane/wu-*`는 integration에서 시작하고 rebase＋ff로 복귀한다. product에는 같은 저장소 develop의 PR만 사람이 직접 merge commit으로 병합한다. 직접 push·force push·삭제·자동 병합과 봇 우회를 허용하지 않는다.
5. 마이그레이션은 한 라운드 = 한 체인 구간이다. 형제가 생기면 merge revision과 두 적용 순서 drift 검증이 필요하다.
6. 릴리스는 태그로 식별한다. dev는 `dev-YYYYMMDD-N`, 운영은 `prod-*` 태그와 실제 product 병합 SHA를 결속한다. 사람의 PR 병합 후 배포하며 추가 배포 승인 단계는 없다.
<!-- rule6:end -->

- 반입 검사는 공통 ship gate, 사후 대조는 deploy doctor가 담당한다. dev/prod 호출부가 기준 ref를 고정하고 환경변수로 임의 원천을 허용하지 않는다.
- PR의 head/base SHA와 초기화 manifest digest는 병합 전에 검증한다. 실제 merge SHA는 병합 뒤 부모 관계·승인 입력을 대조하여 실행 기록과 결속한다.
- product 기준점 생성 자체는 배포가 아니다. 첫 PR 병합 전 자동 배포 진입점·보호 규칙·영속 기록·대상 검증이 준비되어야 한다.
- 최초 운영 reseed는 첫 배포 PR에 명시한 대상에서만 1회 실행한다. 이후 일반 배포와 재시도로 초기화를 반복하지 않는다. 실패 시 점검 상태에서 사람이 재개를 결정한다.
- 구현 중인 검사와 실제 원격 보호 설정의 상태는 구분한다. 이 문서 자체는 GitHub 설정을 변경하거나 배포를 실행하지 않는다.

## 2. 브랜치·태그 수명 표

| 이름 | 기점 | 복귀·반영 방식 | 삭제 시점 | 책임 |
|---|---|---|---|---|
| `develop` | 기존 main을 rename | 개발 통합 도착점·기본 브랜치 | 영구 | 사람/오케스트레이터의 승인된 통합 |
| `product` | 전환 계획의 검토된 기준점 | 동일 저장소 develop PR의 사람 직접 merge commit | 영구 | 사람 병합, 배포 자동 실행 |
| `integration/r-N` | develop tip | develop으로 ff-only | 통합 뒤 | 오케스트레이터 |
| `lane/wu-*` | integration | rebase＋ff | 통합 뒤 | 구현 레인, 통합은 오케스트레이터 |
| `lane/product-source`·`lane/product-release` | 이번 integration | 변경 검토 후 integration으로 회수 | 통합 뒤 | 이번 라운드 격리 구현 |
| `plan/*` | develop tip | 문서를 integration에 반영 | 라운드 통합 뒤 | 오케스트레이터 |
| `archive/*` 태그 | 보존 대상 tip | 배포 대상 아님 | 영구 | 개별 보존 승인 범위 |
| `dev-YYYYMMDD-N` 태그 | 실제 dev 적용 SHA | 검증·원장과 연결 | 영구 | 승인된 릴리스 흐름 |
| `prod-*` 태그 | 실제 product 병합 SHA | 검증·원장과 연결 | 영구 | 사람 병합으로 시작된 릴리스 흐름 |

- 새 브랜치 접두어는 이 표에 먼저 기록한다. 기술적 worktree 브랜치와 별도의 제품 배포 원천을 혼동하지 않는다.
- 강제 push와 태그 일괄 push는 사용하지 않는다. product 승격을 squash/rebase로 바꿔 공통 이력을 끊지 않는다.

## 3. 하지 말 것

- 다른 저장소의 develop 또는 feature 브랜치를 product에 직접 반영하기.
- 사람 병합 없이 운영을 배포하거나 자동 병합 봇에 보호 규칙 우회 권한 주기.
- 원격 ref 부재를 main fallback이나 비조상 허용 변수로 해결하기.
- 최초 초기화의 실행 기록 조회 실패를 미실행으로 간주하기.
- 계정 비밀번호·운영 비밀을 PR·문서·커밋에 기록하기.
- 이후 절의 과거 main 배포 근거를 새 develop/product 실측으로 재사용하기.

## 4. 창 9 사례 — 규칙 1 이 없던 자리에서 난 것

2026-09-06 창 9 는 `main` 밖 레인 sha `20b3715`(`integration/w9-dev-deploy`)를 dev 에 반입했고, 그 브랜치의 ai 마이그레이션 `0006_topic_vocab_six` 가 **dev 에만 적용된 채** 남았다. R-C 배포 창의 **dev 사전 실측에서 `alembic_version_ai` 스탬프 `0006_topic_vocab_six` 가 `main` 에 없는 리비전으로 발견**됐고(레포 체인에는 형제 `0006_rc7_synonym_category` 가 있었다 · STOP·중단 기록 0), Ted 판정 ⓐ 뒤 `WU-C13` 이 그 두 파일(`db/ai/versions/0006_topic_vocab_six.py` · `db/ai/seed/topic_synonym_six.sql`)을 파일 단위로 흡수하고 `0007_merge_vocab_and_category`(부모 둘 ＋ 두 적용 순서 drift 오라클)로 닫았다. **흡수되지 않고 `main` 에 동등물이 0 인 것**은 넷이다 — dev 트리거 스풀 배선(`infra/dev/compose.yml` 의 `COLAB_WORKER_EVENT_SPOOL`·`COLAB_VIZ_TRIGGER_SPOOL`·`viz-events` 볼륨 ＋ `infra/dev/README.md` 규약 8줄) · `infra/staging/manifest-refdata.json` 의 `sourceLabel` 4값 · 창 9 원장 6행 · `dev-package/reports/window-9/` 실행 로그 20파일. 반입 게이트가 있었으면 `20b3715` 는 dev 에 실리지 못했고, 이 넷은 `main` 을 통과하며 흡수 여부가 그때 갈렸을 것이다. 상세 = `PLAN-SoT §9 〈378〉 ⑧` · `dev-package/sessions/R-C-ROUND-20260908.md` §9 · `dev-package/sessions/WU-D4-branches-20260908.md` §2.

---

## 5. staging 예외와 긴급 우회 — 집행 자리 = `ship.sh` ＋ `deploy_doctor` ⑮

- **staging 예외(규칙 2)** — staging 은 `integration/*` HEAD 를 굽는다. 리허설이므로 조상 검사의 대상이 아니고, 대신 **원장 행에 브랜치 이름**을 같이 적는다(`infra/staging/deploy.sh` 의 `ledger_append` 비고 끝 `브랜치=`). staging 에서 완료 판정을 하지 않는다(`CLAUDE.md §0` 완료 조건).
- **긴급 우회** — 반입 게이트를 넘겨야 하는 날은 `COLAB_SHIP_ALLOW_NONMAIN=1` 을 선언한다. 거절 대신 통과하되 ⑴ 출력에 「비조상 반입 · 우회 선언」 한 줄 ⑵ EC2 `MAIN_SHA` 파일에 `ancestor=bypass` ⑶ `deploy_doctor` 15번째 항목이 그 값을 ✗ 로 판정 — 셋이 함께 남는다. 조용한 우회만 막고 선언된 우회는 허용한다.
- ⭑ **⟨개정 2026-09-08 · WU-D2·D3 병합⟩ 위 두 문단은 구현된 동작이다** ／ 종전 ~~「현재 트리에는 반입 게이트도 우회 경로도 없다 · `deploy_doctor` 도 14항목이다 · 예정 동작이다」~~ — `infra/dev/ship.sh` 가 `dist/colab-v2-dev.sha` 를 읽은 직후 `origin/main` 을 fetch 해 조상 검사를 하고, EC2 `/opt/colab-v2/MAIN_SHA` 에 `main=<12자리> candidate=<12자리> ancestor=yes|no|bypass` 한 줄을 적는다. `deploy_doctor` 는 **15항목**이고 ⑮ 가 `CURRENT_SHA`·`MAIN_SHA` 를 대조한다.
- 손으로 재던 한 줄(`git merge-base --is-ancestor <sha> origin/main`)은 `ship.sh` 게이트가 대신한다 — 반입 전 확인용으로 남겨 두되 반입의 조건은 게이트 쪽이다. 태그는 `infra/dev/tag-release.sh`(`dev-YYYYMMDD-N` · `prod-YYYYMMDD`).
