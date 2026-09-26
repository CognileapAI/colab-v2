# 온톨로지 보강 회차 도구

새로 올라온 자료를 모아 빈칸·후보·사전에 없는 낱말을 뽑고, Ted 판정 페이지를 만들고, 초안 사실을 측정한다.
절차(언제 무엇을 판단하는지)의 정본은 `.agents/skills/ontology-round/SKILL.md` 다. 이 문서는 설치와 명령만 다룬다.

## 설정 — 누구나 한 번

```bash
bash dev-package/tools/ontology-round/setup.sh          # 없으면 만들고 점검
bash dev-package/tools/ontology-round/setup.sh --check  # 점검만
```

| 필요한 것 | 왜 | 없으면 |
|---|---|---|
| python3.12, `uv`(권장) 또는 venv | 분석·측정이 core-api 코드를 재사용한다 | setup 이 78 |
| `services/core-api/.venv` | 위와 같음 — setup 이 만든다 | setup 이 만든다 |
| docker | 측정용 일회용 postgres | 측정만 못 한다(setup 78) |
| 운영자 환경 래퍼 `~/.config/colab-platform/with-dev-env.sh` | dev 수집(읽기 전용 · SSH · 백업 롤) | dev 대신 `--database-url` 로 로컬 DB 회차만 가능 |

### dev 수집 자격

래퍼는 `COLAB_DEV_SSH`(ec2-user@<dev 주소>)와 `COLAB_DEV_KEY_FILE`(0600 키 파일)을 환경에 싣고 인자 명령을 실행하는
작은 셸이다. 값은 저장소에 두지 않는다. 받는 법은 운영 담당(Ted)에게 요청한다. 다른 경로면 `COLAB_DEV_ENV_WRAPPER` 로 지정한다.
수집은 dev 호스트의 `/etc/colab/backup-platform-db.url`(BYPASSRLS 백업 롤)로 **읽기 전용 트랜잭션**만 연다.

## 명령

```bash
bash dev-package/tools/ontology-round/round.sh init            # 지난 회차 이후 자료
bash dev-package/tools/ontology-round/round.sh init --all      # 처음이면 전체
bash dev-package/tools/ontology-round/round.sh init --database-url postgresql://…   # 로컬 DB
bash dev-package/tools/ontology-round/round.sh page <회차 폴더>                        # decisions.json → 판정 페이지
bash dev-package/tools/ontology-round/round.sh measure <회차 폴더> <payload.json>      # 일회용 DB 측정
```

회차 폴더 기본 자리는 `~/.local/state/colab/ontology-rounds/<YYYYMMDD-N>/`(`COLAB_ONTOLOGY_ROUND_HOME` 로 바꾼다).
레포 밖인 이유는 dev 자료 설명 원문이 들어 있어서다. PR 에 옮길 파일은 SKILL.md 6단계가 정한다.

| 파일 | 만드는 것 | 내용 |
|---|---|---|
| `datasets.json` | collect.py | 자료 이름·설명·등록 칸·확장자·근거 상태 (원문 — 레포에 넣지 않는다) |
| `analysis.json` · `summary.md` | analyze.py | 빈 칸 · 칸별 후보와 출처 · 사전에 없는 낱말 |
| `state.json` | round.sh | 수집 시각 — 다음 회차의 「지난 회차 이후」 기준 |
| `decisions.json` | 에이전트 | Ted 판정 결정 목록(형식은 page.py 머리말 · 예시 `decisions.example.json`) |
| `decision-page.html` | page.py | 판정 페이지(외부 자원 없음 · 로컬로 열거나 아티팩트로 올린다) |
| `measurement/` | round.sh measure | 초안 사실 규칙별·사실별 기여·역전 표 |

종료코드는 저장소 규약을 따른다 — 0 성공 · 1 판정 실패 · 78 준비 실패.
