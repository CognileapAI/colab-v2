# X5-403-VERIFY — `updateDataset` · `updateProject` 403 집행의 red/green 증명

- 대상 브랜치: `x5-403-enforce` (`d571e57` · `origin/main` 위로 리베이스됨)
- 워크트리: `.claude/worktrees/x5-403`
- 측정 시점: 2026-08-28
- 측정자: 검증 서브에이전트 (커밋·푸시·amend 없음)

---

## 1. 검증 대상

| 항목 | 실물 |
|---|---|
| 생산 코드 ㉠ | `services/core-api/src/colab_core/app/routes/catalog.py` `update_dataset` — `from .ingestion import _require_upload_edit` 지연 import 후 `_require_upload_edit(db, subject)` |
| 생산 코드 ㉡ | `services/core-api/src/colab_core/app/routes/project.py` `update_project` — `if not _can_manage(db, subject): raise errors.forbidden(...)` |
| 시험 ㉠ | `services/core-api/tests/test_dataset_update.py::test_editing_a_dataset_needs_the_upload_edit_switch` |
| 시험 ㉡ | `services/core-api/tests/test_lab_and_project_update.py::test_editing_a_project_needs_the_switch` |

두 시험 모두 `sql` 픽스처로 `d2_permission_switch` 의 해당 스위치를 `false` 로 내린 뒤
`PATCH` 를 부르고 `403` 을 요구한다. `conftest.py` 의 `_RESTORE` 마지막 문장이
`업로드·편집`·`프로젝트 생성` 두 스위치를 매 시험 뒤 `true` 로 되돌린다 —
스위치 훼손이 다음 시험으로 새지 않는다.

---

## 2. 시험 환경 — 일회용 인스턴스

`dev-package/RESTART.md §2-④` 절차 그대로.

- `docker run -d --rm --name x5403_pg --tmpfs /var/lib/postgresql/data:rw,size=512m -e PGDATA=/var/lib/postgresql/data/pg ... postgres:16-alpine`
- **호스트 포트 미공개** — 컨테이너 IP 로만 붙는다
- 스키마·앱 롤·시드는 `services/core-api/tests/fixtures/setup-db.sh` (`CONTAINER=x5403_pg`)
- 접속 URL 은 `0600` 임시 파일로만 넘겼고 **출력·문서 어디에도 값을 남기지 않았다**
- 환경변수: `COLAB_CORE_TEST_DATABASE_URL` · `COLAB_CORE_TEST_SUBJECTS_FILE`(`tests/fixtures/subjects.json`)

### 운영 스택 접촉 — 없음

- `colab_v2_staging_*` 8개 컨테이너에 대해 **정지·재기동·재생성·`down`·`DELETE`/`UPDATE`/DDL 어느 것도 하지 않았다**
- `docker ps` 로 이름만 조회했다(읽기)
- 파괴 플래그 사용 없음. 우회한 거부도 없음

---

## 3. 전체 스위트 (수정 그대로)

```
455 passed in 42.04s
```

- 통과 **455** · 실패 **0** · skip **0** · error **0**
- 단위: `services/core-api` 디렉터리에서 `python -m pytest -q` 1회, 위 일회용 DB 기준

---

## 4. red 픽스처 증명

생산 코드 두 훅만 되돌렸다(`git show HEAD -- <두 src 파일> | git apply -R`).
**시험 파일은 손대지 않았다.**

```
 M services/core-api/src/colab_core/app/routes/catalog.py
 M services/core-api/src/colab_core/app/routes/project.py
```

두 시험만 재실행한 결과:

```
>       assert r.status_code == 403, "스위치 없는 사람이 데이터셋 정보를 고쳤다"
E       AssertionError: 스위치 없는 사람이 데이터셋 정보를 고쳤다
E       assert 200 == 403
E        +  where 200 = <Response [200 OK]>.status_code
tests/test_dataset_update.py:161: AssertionError
```

```
>       assert r.status_code == 403, "스위치 없는 사람이 프로젝트 정보를 고쳤다"
E       AssertionError: 스위치 없는 사람이 프로젝트 정보를 고쳤다
E       assert 200 == 403
E        +  where 200 = <Response [200 OK]>.status_code
tests/test_lab_and_project_update.py:159: AssertionError
```

```
FAILED tests/test_dataset_update.py::test_editing_a_dataset_needs_the_upload_edit_switch
FAILED tests/test_lab_and_project_update.py::test_editing_a_project_needs_the_switch
2 failed in 4.41s
```

- 기대 `403` · 실측 `200` — **두 시험 다 생산 코드 훅에 실제로 매달려 있다.** 통과용 장식이 아니다.
- 훅을 지우면 스위치 없는 계정이 데이터셋 요약과 프로젝트 이름을 실제로 고친다(응답 200).

복원:

```
git checkout -- services/core-api/src/colab_core/app/routes/catalog.py \
                services/core-api/src/colab_core/app/routes/project.py
```

- 복원 뒤 `git status --short` **출력 없음**(clean)
- 복원 뒤 두 시험 재실행 — `2 passed in 2.96s`
- 브랜치 상태: `## x5-403-enforce...origin/x5-403-enforce [ahead 12, behind 1]` — 커밋·푸시·amend 없음

---

## 5. 게이트 6종

`frontend` 에서 `npm ci` 선행(0 vulnerabilities).

| 게이트 | 판정 | 요약줄 |
|---|---|---|
| `contract-lint` | green | `contract-lint green — seam 3건, 룰 위반 0.` |
| `contract-breaking` | green | `contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.` |
| `seam-consistency` | green | `seam-consistency green — G-e 336건 · G-b 7건 · ㉠ 0건 · ㉡ 18건.` (의도적 이월 4건 명시 — 단계 4'·4''·4'''·10) |
| `import-boundary` | green | `Contracts: 8 kept, 0 broken.` / `import-boundary green — 계약 전부 통과.` |
| `banned-import` | green | `banned-import green — .py 113건, 금지 import 0.` |
| `generated-up-to-date` | green | `generated-up-to-date green — 등기부 4건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.` |

6종 전부 실제로 돌았다. 도구 부재로 못 돈 게이트 **0건**.

`seam-consistency` 의 「㉠ 0건」은 신설 검사 대상이 0이라는 뜻이고 게이트 자신이
「기준선이 곧 현재」로 설명한다 — 이번 변경이 seam 을 건드리지 않았으므로 예상된 값이다.

---

## 6. 이번에 세지 않은 것

- **`[미확인]` — 프런트엔드 쪽 회귀**: `frontend` 테스트·빌드는 이 회차의 범위 밖이라 돌리지 않았다.
  풀려면 `cd frontend && npm test` (또는 해당 게이트) 를 돌린다.
- **`[미확인]` — staging 실물에서의 403 동작**: 운영 스택 무접촉 원칙에 따라 배포본으로는 확인하지 않았다.
  풀려면 배포 후 `PATCH /api/v1/datasets/{id}` · `PATCH /api/v1/projects/{id}` 를
  스위치 꺼진 주체로 불러 403 을 본다.
- **red 증명의 범위**: 두 생산 훅만 되돌렸다. 헬퍼(`_require_upload_edit` · `_can_manage`) 자체의
  red 증명은 형제 op 시험이 이미 담당하는 자리라 이번에 다시 세지 않았다.

## 7. 정리

- 일회용 컨테이너 `x5403_pg` 는 `--rm` 으로 떴다. 검증 종료와 함께 제거.
- 작업 트리 clean. 커밋·푸시·amend 없음.
