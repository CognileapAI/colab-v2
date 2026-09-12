# R-BUGFIX-260912 — GitHub 이슈 댓글 최종본 (DRAFT · 미게시)

- 대상 12건 · 레포 `CognileapAI/colab-v2`. 원 초안 = `dev-package/reports/bugfix-260912/closing-draft.md §6`.
- 게시 시점 = **`main` ff 뒤**. 게시 여부·닫기 판정은 Ted. 이 세션은 `gh issue comment` 를 실행하지 않았다.
- sha 는 이 브랜치 실측(`git log --oneline 10a3fb8..HEAD -- frontend/` · `git log --oneline 6afa776..1a38131` · `git log --oneline 1a38131..f98d09de`)으로 확정한 8자리다.
- `#11` 은 **닫지 않는다**(등재 안내 댓글).

---

## 1. 커밋 대조 (실측)

| 이슈 | 반영 커밋 | 커밋 제목 |
|---|---|---|
| `#24` | `1a381310` · `67e25399` | 분석 중 다음 버튼 비활성 사유 고지와 동작 중 표시 추가 / 확장보기에 고르개 줄 신설 · 선택 상태 공유 · 「그리는 중」 표시 (Ted 판정 ⑥·⑧) |
| `#25` | `ccaf27f6` · `a841d7a1` · `67e25399` | L3b ① 미리보기 4:3 틀에 「틀 위 줄」 자리 신설 / L3b ② 데이터셋 상세 고르개 이동 / L3b ③ 확장보기 고르개 |
| `#26` | `6afa776a` · `c9e95eb2` | 64×64 축소본을 접히는 설정 자리로 / L3b ⑤ 축소본 중복 방지 |
| `#27` | `bf02a0c8` | L3b ④ `#27`·`#28` 확대 줄의 접힘·가림 해소 |
| `#28` | `bf02a0c8` | 같은 커밋(한 단계로 처리) |
| `#29` | `67e25399` | L3b ③ 확장보기 고르개 줄 신설(판정 ⑥) — 결함 자체는 재현 안 됨 |
| `#30` | `4572fd48` | 버그개선 회차 마감 원장 — `LV-5` 대장 등재(Ted 유지 판정 기록 `c088dd1c`) |
| `#31` | `bb3e77d8` | 등록 카드 기간 안내를 달력 버튼 뒤로 이동 |
| `#32` | `cef275a0` | 메인 배너 접수 완료 행에 폐기 버튼 추가 |
| `#33` | `b8b4e7e2` | 배너 재개 식별자를 업로드 모달까지 배선 |
| `#34` | `aa26db94` | 닫기 확인에 세 번째 선택지 추가 |
| `#11` | `4572fd48` | 같은 커밋 — `PA-T` 대장 등재 |

- L3b 단계 순번(시간순) = ① `ccaf27f6` ② `a841d7a1` ③ `67e25399` ④ `bf02a0c8` ⑤ `c9e95eb2` ⑥ `f98d09de`(R-C-2 문면 개정 · 이슈 댓글 인용 대상 아님).
- 초안 `§0` 의 `9f925219`·`75a053ea`(실측·판정 확정)는 문서 커밋이라 댓글 sha 로 쓰지 않는다 — 실측 근거는 파일 경로로 인용한다.

---

## 2. 게시 명령 (사람 실행 · `main` ff 뒤)

```bash
gh issue comment 24 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/24.md
gh issue comment 25 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/25.md
gh issue comment 26 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/26.md
gh issue comment 27 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/27.md
gh issue comment 28 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/28.md
gh issue comment 29 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/29.md
gh issue comment 30 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/30.md
gh issue comment 31 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/31.md
gh issue comment 32 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/32.md
gh issue comment 33 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/33.md
gh issue comment 34 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/34.md
gh issue comment 11 -R CognileapAI/colab-v2 --body-file dev-package/reports/bugfix-260912/issue-comments/11.md
```

- 실행 자리 = 레포 루트(상대 경로 그대로). 워크트리에서 돌리면 그 워크트리 루트.
- 닫기는 별도 판정이다 — `gh issue close` 는 이 목록에 없다. `#11` 은 닫지 않는다.

---

## 3. 미확인

| 항목 | 상태 | 해소 |
|---|---|---|
| staging 태그 `cbb9ff1406c5`(`#29` 인용) | 초안 `§6` 인용값 그대로 · 이 세션 미검증 | `dev-package/reports/issues/2026-09-12-measure-L4.md` §4-1 실물 |
| `#24` 실측 수치(141조각 · 39.8/41.5초 · 69.8/73.2초) | 초안 `§6` 인용값 그대로 · 이 세션 미검증 | 같은 파일 |
| `#30` 14행 계수 | 초안 `§6` 인용값 그대로 · 이 세션 미검증 | 같은 파일 §4-2 |
