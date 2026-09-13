> ⛔ **낡았다 — 이 회차의 문서는 `dev-package/reports/prod/rebase-20260913/PR-BODY.md` 다.**
> 기준 `main` 이 `a8a1653` → `aa8bee98` 로 옮겨졌고 커밋도 13 → 22 로 늘었다.
> 아래는 2026-09-12 시점의 기록이고 그대로 둔다(고치지 않는다).

## 무엇을

`feature/rtf400_deploy_prod` 를 최신 `origin/main`(`a8a1653`) 위로 리베이스하고, 그 사이 `main` 에 들어온
**새 배포 규약**(브랜치 정본 `docs/BRANCHING.md` 규칙 6 · 반입 게이트 · `deploy_doctor` 15번째 항목)을
**prod 쪽에도 같은 모양으로** 넣었다.

- 커밋 **13 유지**(내용 유지 · sha 변경) ＋ 규약 반영 커밋.
- prod 스택 자체(S3·VPC·RDS·EC2·CloudFront·백업 cron)는 이미 이 브랜치가 세운 것이고, 이 PR 이
  더하는 것은 **그 prod 를 `main` 규율 안으로 들여놓는 장치**다.

## 왜

`main` 은 **유일한 배포 원천**이다. 그 규칙을 집행하는 장치가 지금까지 **dev 에만** 있었다 —
`infra/dev/ship.sh` 는 `main` 조상이 아닌 커밋을 거절하고 `/opt/colab-v2/MAIN_SHA` 를 남기는데,
`infra/prod/ship.sh` 에는 그런 검사가 **한 줄도 없었다.** 규칙이 dev 에서만 지켜지면 같은 사고가
prod 에서 다시 난다(dev 에서 실제로 났다 — `main` 밖 커밋이 실렸고 그 마이그레이션이 dev 에만 남았다).

## prod 실물 현황 (2026-09-12 실측)

| 항목 | 값 |
|---|---|
| 진입 주소 | `https://d1aje00ns2hjsl.cloudfront.net` (CloudFront · 무료 플랜 · WAF **감시 모드**) |
| 실행 이미지 | `prod-3922d01750d0` — **이 브랜치의 중간 커밋에서 빌드**한 것이고 `main` 에서 나온 것이 아니다 |
| `prod-*` 태그 | **0건** |
| `/opt/colab-v2/MAIN_SHA` | **없음** ⟹ `deploy_doctor` ⑮ 는 지금 **✗**(「파일 없음」) |
| DB 스키마 (platform) | `0012_merge_lv1_and_transfer` — `main` head `0027_operator_audit` 까지 **15건 미적용** |
| DB 스키마 (ai) | `0005_k2b_concept_graph_seed` — `main` head `0007_merge_topic_vocab_and_rc7_category` 까지 **3건 미적용** |
| 이전 판정 | 브랜치 판 `deploy-doctor.sh`(14 항목) 1회 = ✓14 ✗0 ─0 (2026-09-06) |

## 규칙 1·6 정합 경로 — 무엇을 넣었나

1. **반입 게이트를 한 벌로 뽑았다** — 신규 `infra/_lib/ship-gate.sh`.
   dev·prod 두 `ship.sh` 가 **같은 함수**를 부른다(복사본 둘은 한쪽만 고쳐져 갈린다).
   - 후보 sha ∈ `origin/main` 아님 → **exit 65** · `origin` 조회 실패 → **exit 78** ·
     선언 우회 `COLAB_SHIP_ALLOW_NONMAIN=1` → 통과하되 `ancestor=bypass` 가 기록에 남고 ⑮ 가 ✗ 로 잡는다.
2. **prod 에만 태그 검사를 더했다**(규칙 6) — 후보 sha 에 `prod-*` 태그가 없으면 **exit 65**.
   ⛔ **이 검사에는 우회 변수가 없다.** 태그 주체는 Ted 다.
3. **`MAIN_SHA` 를 prod 에서도 적는다** — `main=… candidate=… ancestor=…` 한 줄(dev 와 동일 형식).
4. **`infra/prod/deploy-doctor.sh` 가 `-v /opt/colab-v2:/state:ro` 를 넘긴다** — 그래야 ⑮ 가 읽는다.
   머리말도 「14 항목」→「15 항목」. 마운트가 없으면 ⑮ 는 영원히 ✗ 다.
5. **문서를 실물에 맞췄다** — `docs/DEPLOY.md` 의 「prod 는 아직 없다」 3계열을 dev·prod 2벌 현황으로
   고치고 `§5-9`(태그에서만 배포)·`§5-10`(마이그레이션 격차)을 신설. `.claude/rules/deploy.md` 는
   **한 줄만**(「지금 서 있는 것은 dev 하나」 → 「dev·prod 둘」) — 「깨뜨리면 안 되는 것」 11항목은 무변.

## 배포 전 선행 조건 (이 PR 이 해결하지 않는 것)

이 PR 은 **코드·문서만** 바꾼다. AWS·EC2·RDS 무접촉이고 prod 에 아무것도 적용하지 않았다.

1. **백업 먼저** — `backup.sh` 1회 ＋ `_ops/backups/prod/` 객체 확인. 마이그레이션 15건을 반쯤
   적용한 prod 는 되돌릴 자리가 없다.
2. **마이그레이션 18건**(platform 15 ＋ ai 3). ai 는 `0006` 형제 둘 ＋ merge 라 적용 순서 drift 오라클이 붙는다.
3. **롤 `account-admin`·`operator` 를 prod 에 만든다** — prod RDS 는 P6-c 시점의 롤 4 벌이다.
4. **신설 설정값을 `/etc/colab` 에 파일 단위로** 배치(디렉터리째 마운트 금지).
5. **`main` 재빌드 ＋ `prod-YYYYMMDD` 태그** — 지금 도는 이미지는 규칙 6 이전 판이라, 손으로
   `MAIN_SHA` 를 만들어 ⑮ 를 지우지 않는다(그것은 반입 게이트를 거쳤다는 거짓 증거다).

## Ted 판정이 필요한 것

| # | 항목 | 두 갈래의 대가 |
|---|---|---|
| 1 | **prod 태그 정책** — `prod-YYYYMMDD` 를 언제 찍는가(dev 배포 창 몇 회를 green 으로 넘긴 뒤인가) | 회수를 크게 잡으면 prod 가 오래 낡고, 작게 잡으면 태그가 dev 와 다를 바 없어진다 |
| 2 | **관리자 역할** — `account-admin`·`operator` 를 prod 에 누구 계정으로 만드는가 | 운영자 1명으로 시작하면 부재 시 잠기고, 여럿이면 경계가 넓어진다 |
| 3 | **WAF 차단 모드 전환** — 지금은 감시 모드다 | 지금 켜면 `/api/*` 정상 요청이 오탐으로 막혀도 앱 버그처럼 보인다. 켜지 않으면 막는 것이 없다 |
| 4 | **결정 번호** — `main` 의 `〈372〉`(R-A′ rev2 병합)와 충돌해 이 브랜치 쪽을 **`〈395〉` 으로 재발급**했다(22 파일 · 47곳 · 현 `main` 최대 `〈382〉` ＋1) | 번호는 병합 직전 다시 재는 것이 규칙이므로 `〈395〉` 도 임시다 — 병합 시점에 재실측하면 된다 |

## 검증

선언 12건 · 한 번의 실행 —
`COLAB_GATE_REPORT_DIR=dev-package/reports/prod/rebase-20260912 bash gates/run.sh task`

```
── 계 : green 12 / red(판정) 0 / red(준비) 0     (exit 0)
```

- green 12 — `exec-bit` · `db-boundary` · `work-item-consistency` · `contract-lint` ·
  `contract-breaking`(기준 `origin/main` · **파괴적 변경 0**) · `generated-up-to-date` ·
  셀프테스트 6종(`artifact-ownership` · `autometa-loss` · `boundary` · `db-boundary` · `event` · `preview-tile-slot`).
- **선언 밖 1건 = `planning-freshness` red 5건** — 숨기지 않고 따로 돌려 로그를 남겼다.
  원인은 레포 밖이다: 기획 원본 폴더 `40 COLAB-기획` 가 **이 호스트에 존재하지 않는다**(홈 전체 탐색 0건).
  이 브랜치는 그 판정기·매니페스트를 건드리지 않았다. CI 에서는 해당 입력이 있으면 정상 판정된다.
- 시험 — `services/core-api/tests/test_deploy_doctor.py` **34 passed**(prod 6건 신규 · red 선행 5건 확인) ·
  신규 `infra/prod/tests/ship-gate.sh` **21/0**(red 선행 통과 2·실패 19 확인).
- `service-tests`·`all` 은 이 회차에서 돌리지 않았다.

## 후속 (이 PR 밖)

1. `infra/dev/tests/ship-gate.sh`·`infra/prod/tests/ship-gate.sh` 를 **게이트로 승격** — 지금은 어느 게이트·CI 잡도 돌지 않는다.
2. `planning-freshness` 의 「외부 폴더 부재」를 준비 red(78)로 가름.
3. `event-lint` 의 의존 부재를 exit 78 ＋ `::gate-readiness-failure::` 로(지금은 판정 red 로 계수된다).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01E843FPmKzSLnStzS9YCx97
