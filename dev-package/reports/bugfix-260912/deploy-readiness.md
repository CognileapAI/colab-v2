# dev 배포 준비도 실물 대조 (읽기 전용 · DRAFT · 미승인)

근거 = `dev-package/reports/bugfix-260912/deploy-checklist.md` · `.claude/rules/deploy.md` ·
`docs/DEPLOY.md` · `dev-package/RESTART.md` · `infra/dev/README.md`. 이 세션은 파일 편집 0 ·
커밋 0 · 원격 행위 0. 표는 이 워크트리에서 2026-09-12 실측.

| 단계 | 필요한 것 | 실물 존재 | 근거 |
|---|---|---|---|
| main ff push | Ted 승인 | 해당없음(사람 판단) | `docs/BRANCHING.md §2` |
| SSH 키 | `~/.config/colab-platform/dev-key.pem` | 예 | `-rw-------` 1674바이트, 2026-09-05 |
| EC2 `dev.env` | `/opt/colab-v2/dev.env` | 미확인 | EC2 미접촉 |
| `deploy_release.py` | 실행 가능 여부 | 예 | `--help` 정상 출력(`run/staging/status`) |
| `gh auth status` | 로그인 | 예 | 계정 `sungwooHa`, 스코프 `repo`·`workflow` |
| AWS 자격 | `aws sts get-caller-identity` | 아니오 | `NoCredentials` 에러 |
| EC2 SSH 접속 | 호스트 별칭 | 미확인 | 문서상 리터럴 `ec2-user@<EIP>`뿐, `~/.ssh/config`에 별칭 없음, EIP 자체 미확인 |
| `tag-release.sh dev` | 스크립트·요구값 | 예 | 존재, 실행 시 `main` 조상 검사(비조상 exit 65)·태그 중복 exit 65 |
| `deploy_doctor` 15항목 | 단일 실행 명령 | 예(명령만) | 체크리스트 §2-5 축자 명령, EC2 위 전용 |
| core-api venv | `.venv/bin/python` | 심볼릭만 | `/usr/bin/python3` 링크, `-e .` 설치 여부 미확인 |
| `release.json` 계획 | 레포 밖 고정 파일 | 아니오 | `~/colab-deploy/r-bugfix-260912/release.json` 없음 |
| `/tmp/op.env` | 임시 운영자 키 | 아니오(정상) | 실행 직후 삭제 규약 |

## 에이전트가 바로 실행 가능한 단계

- 로컬 조상 확인(`git merge-base --is-ancestor`)·결정 번호 재실측(`max-decision.sh`)
- `deploy_release.py --check`로 계획 JSON 검증(계획이 작성된 뒤, dry-run 한정)
- 배포 계획 JSON 초안 작성(레포 밖 저장은 사람이 검토 후 고정)

## 사람 개입 필요

- `main` ff push(Ted 승인, 비가역)
- `COLAB_DEV_SSH`/`COLAB_DEV_KEY_FILE` 설정과 실제 EC2 접속(이 호스트에 AWS 자격 없음)
- `/tmp/op.env` 준비·`deploy_doctor` EC2 위 실행
- `git push origin dev-20260912-2`, `git push origin --delete integration/r-bugfix-260912`(비가역)
- staging 재빌드 승인(`approve.sh Ted "..."` — 승인자 이름 리터럴 필요)
- `gh issue comment` 12건 게시(외부 공개)

## staging을 `main` 기준으로 재빌드하는 명령

근거 = `dev-package/RESTART.md ②-0`.

```
infra/staging/pipeline/approval/approve.sh Ted "<무엇을 눈으로 봤는가>"
infra/staging/deploy.sh --target staging
```

승인자 이름이 비어 있으면 스크립트가 exit 64로 거부한다. staging은 예외적으로
`integration/*` HEAD를 굽는 경로이므로(`docs/BRANCHING.md` 규칙 1·2), `main` ff 이후
실행하면 그 시점의 `main` 커밋을 굽는다.
