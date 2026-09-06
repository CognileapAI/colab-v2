# `dev-package/tools/`

| 도구 | 무엇을 하나 |
|---|---|
| `check-package-freshness.py` | 게이트 `planning-freshness` — 기획 정본 패키지 HTML 의 임베드 md ↔ 원본 md 일치 |
| `merge-work-items.py` | `dev-package/work-items.yaml` 전용 3-way 병합 드라이버 (D4 · `rules/colab-rules.md §4-2`) |

## `merge-work-items.py` — 한 번만 걸어 두는 설정

`.gitattributes` 는 **드라이버 이름**만 선언한다(`dev-package/work-items.yaml merge=work-items`).
실행할 명령은 **로컬 설정**이 준다 — 레포 파일이 명령을 지정할 수 있으면 클론이 곧 코드 실행이라
git 이 그렇게 설계돼 있다. 체크아웃마다 한 번:

```
git config merge.work-items.driver "python3 dev-package/tools/merge-work-items.py %O %A %B"
git config merge.work-items.name   "work-items.yaml 덧붙임 병합"
```

- 레인 워크트리는 `.claude/hooks/worktree-setup.sh`(H2)가 스폰 시점에 자동으로 건다.
- 설정이 없으면 git 은 **조용히 기본 텍스트 병합**으로 돌아간다. 종전처럼 충돌 표식이 남을 뿐이고
  잘못 병합되지 않는다 — 미설정이 새 위험을 만들지 않는다.
- 걸렸는지 확인 = `git config --get merge.work-items.driver`

### 무엇을 자동으로 풀고 무엇을 사람에게 넘기나

| 상황 | 결과 |
|---|---|
| 양쪽이 각자 새 WU 블록을 **끝에 덧붙였다** | 자동 병합. 상대 신규 블록이 뒤에 붙는다 |
| 한쪽만 어떤 WU 를 고쳤다 | 고친 쪽을 취한다 |
| 상대가 지운 WU 를 우리는 안 건드렸다 | 삭제를 따른다 |
| **같은 WU 를 양쪽이 다르게 고쳤다** | **충돌** — 표준 충돌 표식을 남긴다 |
| 머리말(주석·`items:`)을 양쪽이 다르게 고쳤다 | **충돌** |
| 결과가 YAML 로 파싱 안 됨 · id 중복 · id 없는 항목 | **충돌** |

⚠ 드라이버는 「덧붙임은 충돌이 아니다」 하나만 안다. 의심스러운 자리는 전부 exit 1 로 물러선다 —
조용히 한쪽을 고르면 갈렸다는 사실이 사라진다. 병합 뒤에는 게이트 한 번:
`./gates/run.sh work-item-consistency`.

### 자기 증명

`bash dev-package/tools/merge-work-items-selftest.sh` 가 픽스처 6종(양쪽 덧붙임 · 한쪽 수정 ·
한쪽 삭제 · 같은 WU 상충 · id 중복 · 머리말 상충)으로 「자동 병합이 되는 자리」와 「충돌로 물러서는
자리」를 둘 다 보인다. 실물 대장(572 KB · 140항목)에 대한 소요도 함께 잰다(스펙 K 미검증 1).
