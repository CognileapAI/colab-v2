# DR-2 — dev EC2 `/opt/colab-repo` 트리 동기화 (tar-sync 3줄)

- 실행 2026-09-13 · 성격 = **원격 상태 변경 1건(레포 트리 덮어쓰기)** · 배포 0 · DB 쓰기 0 · S3 쓰기 0 · compose 0.
- 근거 절차 = `infra/dev/README.md` 「⟨선행 단계 · 실측 2026-09-06 · `〈361〉`-㉯⟩」 축자 3줄 · 정찰 `dev-package/reports/r-dev-reset/dev-access-recon.md §1`·`§4`.
- 접속 자격 = 운영자 env 파일(레포 밖)의 `COLAB_DEV_SSH`·`COLAB_DEV_KEY_FILE`. 값은 이 문서·로그·argv 에 미기재.

## 1. 원본 트리

| 항목 | 값 |
|---|---|
| `git fetch origin` 후 `origin/main` | `aa8bee981ff584f0175a88158bc00e38f7bdcc37` |
| 반입 대상 경로 | `db` · `gates` · `services/core-api/ops` · `infra` |
| 생성 방법 | `git archive origin/main -- <위 4경로> \| gzip`(체크아웃 0 · 작업 트리 미사용) |
| 아카이브 규모 | 항목 635건 · 815,638 바이트 |
| dev 실행 sha `6ff0eecd2cba` ↔ `origin/main` 의 위 4경로 diff | **0건**(`git diff --stat` 공백) — 동기화 내용물은 배포 sha 와 동일 |
| `6ff0eecd2cba` 는 `origin/main` 의 조상 | 예(`git merge-base --is-ancestor`) |

## 2. 원격 명령 (값 가림)

```bash
scp -q -o BatchMode=yes -i "$COLAB_DEV_KEY_FILE" <로컬 tgz> "$COLAB_DEV_SSH":/tmp/repo.tgz
ssh -o BatchMode=yes -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" 'sudo tar xzf /tmp/repo.tgz -C /opt/colab-repo --overwrite'
ssh -o BatchMode=yes -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" 'ls /opt/colab-repo/db/platform/versions | tail -3; md5sum /opt/colab-repo/services/core-api/ops/deploy_doctor.py'
ssh -o BatchMode=yes -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" 'sudo bash /opt/colab-repo/infra/ops/probes/deploy-verification.sh'
```

- 전 4명령 exit 0. 재시도 0 · 부분 실행 합산 0 · `--allow-skip` 미사용.
- ⛔ 미실행 = compose·`up.sh`·`ship.sh`·마이그레이션·DB 쓰기·S3 쓰기.

## 3. 동기화 후 원격 실측

| 항목 | 종전 | 지금 |
|---|---|---|
| `/opt/colab-repo/db/platform/versions` 최신 | `0030_merge_operator_audit_and_backoffice.py` | **`0031_search_evidence.py`** |
| `deploy_doctor.py` md5 (개발 기계 ↔ EC2) | 일치 `a2d5651512ff786f0a71eeb36e51ed9c` | 일치(무변) |

## 4. `deploy_doctor` 1회 실행 결과

- 실행 경로 = EC2 `sudo bash /opt/colab-repo/infra/ops/probes/deploy-verification.sh` · **한 번의 실행** · exit 0.
- 요약줄 축자 — **`항목 15 — ✓ 15 · ✗ 0 · ─ 0`** · `전 항목 통과 (─ 0 — 15 항목이 실제로 돌았다)`.
- **⑥ 스키마 head (platform) = ✓** — `0031_search_evidence (DB = 레포)`. 종전 유일한 ✗ 가 해소됐다.
- ⑦ ai head `0007_merge_vocab_and_category (DB = 레포)` ✓ · ⑮ 실행 sha `6ff0eecd2cba ∈ main` ✓.
- ✗ 항목 없음.

## 5. 판정·잔여

- 진입조건 ㄹ(`deploy_doctor` ⑥ ✗)는 **해소**. 정찰 `§5` 차단표의 3번이 닫힌다.
- ⚠ 이 15/15 는 **현재 실행 sha `6ff0eecd2cba` 기준 1회 실측**이고, `main` 병합·재배포가 일어나면 다시 재야 한다.
- 구조적 원인은 미해소 — `ship.sh` 가 같은 회차에 `/opt/colab-repo` 를 밀지 않는다(정찰 `§6-1`). 배포마다 ⑥ 이 재발할 수 있다.
- 원격 `/tmp/repo.tgz` 잔존(절차 문서에 삭제 단계 없음).
