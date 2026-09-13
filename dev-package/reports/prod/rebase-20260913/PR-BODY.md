## 무엇을

`feature/rtf400_deploy_prod` 를 최신 `origin/main`(`aa8bee98`) 위로 리베이스하고, prod 를
**`main` 규율 안으로 들여놓는 장치**를 마저 넣었다. 커밋 **22**(기존 18 ＋ 신규 4).

- **A. 반입 도구 결함 정정** — 태그 sha 파일 · 판정 레포 동기화 · ops 소스 번들 · `prod.env` 이미지 태그.
- **B. compose·부트스트랩을 dev 현재판에 맞춤** — 소유권 장부 · 계정 관리 롤 · Stage 2 · 롤 부트스트랩 2단계.
- **C. 운영 기능 prod 이식** — 소유권 스냅샷 매시 발행 · 운영자 알림 런타임.
- **D. 결정 번호 재발급** `〈383〉` → `〈395〉`.

⛔ 이 PR 은 **코드·문서만** 바꾼다. AWS·EC2·RDS·S3 무접촉이고 prod 에 아무것도 적용하지 않았다.

## 왜

`main` 은 **유일한 배포 원천**이고, 그 규율을 집행하는 장치가 dev 에만 있었다. 앞선 회차가
반입 게이트(조상 ＋ `prod-*` 태그)를 prod 에 넣었고, 이번 회차는 **그 게이트를 통과한 뒤에
벌어지는 일들**을 메운다. 이번에 고친 넷은 전부 같은 모양이었다 —

> **빠뜨려도 `ship.sh` 가 exit 0 을 내고, 걸리는 검사가 하나도 없다.**

- 판정 레포(`/opt/colab-repo`)가 낡으면 `deploy_doctor` ⑥ 이 **옛 alembic head 를 정답표로 삼아
  조용히 틀린다.** dev 에서 **2회** 실측했다(`r-login-backoffice/task5/deploy-3-verify.md`).
- `prod.env` 의 `COLAB_IMAGE_TAG` 를 안 고치면 **옛 migrator 이미지로 마이그레이션이 돈다.**
- `deploy-doctor.sh` 를 안 밀면 판정 진입점 자체가 EC2 에 없다.
- `tag-release.sh prod` 가 **dev 의 sha 파일**을 읽었다 — prod 만 빌드한 회차는 태그를 못 찍거나
  dev 의 sha 에 prod 태그가 붙었다.

## 태그 주체 — 규칙 문면과 이번 회차의 차이 (Ted 통보 필요)

`docs/BRANCHING.md` 규칙 6 과 `infra/_lib/ship-gate.sh` 의 주석은 **태그 주체를 Ted** 로 적는다.
이번 prod 배포 회차는 **사용자가 로컬에서 `prod-20260913` 을 찍고 push 는 하지 않는** 방식으로
진행할 계획이다(사용자 결정 2026-09-13). 반입 게이트 ②는 **로컬 태그로 통과한다**(원격 미조회 ·
우회 변수 없음)이므로 기술적으로는 성립하지만, **문면과 실제 주체가 다르다**는 사실을 여기 적는다.
문면을 고칠지 이번만 예외로 둘지는 Ted 판정 자리다.

## 운영 기능 둘 — 이번에 레포 안으로 들어왔다

| 기능 | 종전 자리 | 이번 자리 |
|---|---|---|
| 소유권 장부 스냅샷(매시 17분) | **세션 문서의 heredoc** | `infra/prod/publish-ownership-hourly.sh` ＋ `install-cron.sh` |
| 운영자 알림 런타임 | 설치기가 `dev\|staging` 만 수용 | **`prod` 수용**(갈래 = 연결 dev·prod / relay staging) |

`infra/prod/install-cron.sh` 가 prod 크론 **넷 전부**를 건다(백업 · 지연 정리 깨우기 · 소유권 스냅샷 ·
운영자 알림). 입력을 먼저 전부 검사해 하나라도 없으면 크론을 **한 줄도 쓰지 않고 exit 2** 다.

## 배포 전 선행 조건 (이 PR 이 해결하지 않는 것)

1. **백업 먼저** — `backup.sh` 1회 ＋ `_ops/backups/prod/` 객체 확인.
2. **마이그레이션** platform 19건(0013~0031) ＋ ai 3건(0006 형제 둘 ＋ 0007 merge).
   ⚠ `0020` 은 `d6_project (lab_id,name)` 중복이 있으면 실패한다 — 사전에 센다.
3. **롤 두 벌** — `db-bootstrap.sh account-admin` · `operator`(이번 PR 이 스크립트로 넣었다).
4. **시크릿 파일 4개 추가** — `account-admin-database.url`(uid 10001) ·
   `operator-database.url` · `ownership-platform-db.url` · `ops-slack-webhook.url`(셋 다 root).
   표는 `infra/prod/README.md §4-b`.
5. **`prod.env` 키 3개 추가** — `COLAB_VIZ_OWNERSHIP_SNAPSHOT_OWNER_UID` · `_GROUP_GID` · `_MAX_AGE_SECONDS`.
6. **`main` 재빌드 ＋ `prod-YYYYMMDD` 태그.** 지금 도는 `prod-3922d01750d0` 은 규칙 6 이전 판이라
   `MAIN_SHA` 가 없고 ⑮ 가 ✗ 다. ⛔ 손으로 `MAIN_SHA` 를 만들어 지우지 않는다 — 그것은
   반입 게이트를 거쳤다는 **거짓 증거**다.

## 검증

선언 12건 · **한 번의 실행** ·
배출처 `dev-package/reports/prod/rebase-20260913/gates` —

```
── 계 : green 12 / red(판정) 0 / red(준비) 0     (exit 0)
```

- green 12 — `exec-bit` · `db-boundary` · `work-item-consistency` · `contract-lint` ·
  `contract-breaking`(기준 `origin/main` · 파괴적 변경 **0**) · `generated-up-to-date` ·
  셀프테스트 6종(`artifact-ownership` · `autometa-loss` · `boundary` · `db-boundary` · `event` · `preview-tile-slot`).
- ⚠ `event-selftest` 는 처음 red 였고 원인은 **이 워크트리에 `gates/tools/node/node_modules` 가 없던 것**이다
  (게이트는 도구 확보 실패를 일부러 red 로 센다). `npm ci` 뒤 green. 검사는 줄이지 않았다.
- **선언 밖 `planning-freshness` red 5** — 원인은 레포 밖이다(기획 원본 폴더가 이 호스트에 없다).
- 시험 — `test_deploy_doctor.py` **34 passed** · `infra/prod/tests/ship-gate.sh` **48/0**(종전 21) ·
  `infra/dev/tests/ship-gate.sh` **36/0**(종전 통과 18 · 실패 8 — 픽스처가 `infra/ops` 를 안 심어
  `ship.sh` 가 exit 127 이었고, **어느 게이트도 CI 도 그 시험을 돌리지 않아** 보이지 않았다).
- `scripts/tests/test_operator_runtime_cron.py` 는 9 중 3 실패 — 셋 다 staging relay 갈래이고
  원인은 macOS 에 `flock` 이 없고 BSD `stat` 이 `-c` 를 모르는 것이다(리눅스 CI·EC2 무관).
- `service-tests`·`all` 은 이 회차에서 돌리지 않았다.

## 배포 실측

*(자리만 — prod 재배포 뒤 채운다: 태그 · sha · `deploy_doctor --env prod` 15/15 한 번의 실행 ·
마이그레이션 19＋3 · healthz 4 · cron 4 · 브라우저 한 바퀴)*

## 후속 (이 PR 밖)

1. `infra/{dev,prod}/tests/ship-gate.sh` **게이트 승격** — 지금은 어느 게이트·CI 잡도 돌지 않는다.
2. `event-lint`·`event-selftest`·`planning-freshness` 의 **외부 입력 부재를 준비 red(78)로 가름**.
3. `test_operator_runtime_cron.py`·`test_deploy_release.py` 의 **GNU 의존**(`flock`·`stat -c`).
4. `infra/dev/ship.sh` 에도 **판정 레포 동기화 ＋ `dev.env` 태그 갱신**(이번엔 prod 만 넣었다).
5. `work-items.yaml` 병합 드라이버를 **venv 파이썬**으로 워크트리마다 걸기.
6. `〈395〉` 는 임시 — **병합 직전 재실측**(규칙 4-1).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01E843FPmKzSLnStzS9YCx97
