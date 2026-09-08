# 레인 `rd-branch-sweep` — WU-D4 (2026-09-08)

- 브랜치 `lane/wu-d4` · 기점 `origin/integration/r-d` `785ed88`(지시문 기대값과 일치) · 기준 `main` `18c0228` · 산출 = `dev-package/sessions/WU-D4-branches-20260908.md`(표 11행 ＋ 상세 ＋ 집행 명령) ＋ 이 노트.

## 1. 전/후 계수 (시험 seam · 축자)

| 계수 | 전 | 후 |
|---|---|---|
| `git branch -a \| wc -l` | 21 | 21 |
| `git ls-remote --heads origin \| wc -l` | 12 | 12 |
| `git tag -l 'archive/*' \| wc -l` | 0 | 10 |

- 브랜치 계수 무변 = 삭제 0 건의 직접 증거. `archive/*` 10건 목록은 표 §1 마지막 열 · `gh-pages` 는 보류라 태그 제외.

## 2. 수용 기준 대조 (`R-D-1-branching.md §2 WU-D4` · `§5`)

| 기준 | 판정 | 근거 |
|---|---|---|
| 표에 브랜치 11건 전행 | 충족 | 표 §1 = 판정 대상 11행 ＋ 판정 밖 4행 각주 |
| 조상/밖 커밋/동등물 열 공란 0(`[미상]` 허용) | 충족 | 12열 × 11행 전부 값 기재 · `[미상]` 은 §8 에 5건 열거 |
| 즉시 삭제분에 `archive/*` 태그 선재 | 충족 | `archive/integration/r-a2` · `archive/integration/r-b` |
| 레인 종료 시 원격 삭제·push 0건 | 충족 | 원격 계수 12 무변 · 이 레인의 push 호출 0 |
| Ted 한 줄 없음 ⟹ 창 9 계열·원격 5 무삭제 | 충족 | 5건 전부 `git ls-remote` 에 잔존 |
| `gh-pages` 용도 확인 · 좁은 게이트 3종 | 충족 | `gh api …/pages` 응답 축자(표 §7) — 가동 중 Pages 원천 · 게이트는 §4 |

## 3. 하지 않은 것

- 브랜치 삭제 **0**(로컬·원격) · `git push` **0**(태그·브랜치·삭제 전부).
- `dev-package/work-items.yaml` · `03-HANDOFF.md` · `PLAN-SoT.md` 편집 **0** · `main` 접촉 0 · 병합 0 · 리베이스 0 · 〈N〉 기입 0.
- 근거 = spec 우려 11(원격 삭제·태그 push 는 비가역 원격 행위) ＋ advisor ① 조건 ⑵(게이트 ③ 뒤 오케스트레이터 집행).

## 4. 게이트 (좁은 집합 3종 · 배출처 `dev-package/reports/R-D/rd-branch-sweep`)

| 게이트 | 요약줄 | 3계수 |
|---|---|---|
| `exec-bit` | `exec-bit green — .sh 144건 전부 인덱스 모드 100755 (100644 = 0건).` | green 1 / red(판정) 0 / red(준비) 0 |
| `work-item-consistency` | `work-item-consistency: green — 대장과 산문의 불일치 0` | green 1 / red(판정) 0 / red(준비) 0 |
| `planning-freshness` | `planning-freshness green — 임베드 블록 15개 전부 원본과 일치 · 적용 상태 4건 정합.` | green 1 / red(판정) 0 / red(준비) 0 |

- red **0** ⟹ `origin/integration/r-d` 대조 불요. `work-item-consistency` 관측 1건(㈔ 건너뛴 번호 〈290〉)은 게이트 docstring 이 「red 가 아니다」로 명시한 항목.
- 배출처 = `dev-package/reports/R-D/rd-branch-sweep/gate-summary.json`(스키마 `colab-gate-summary/1` · `.gitignore` 대상이라 미커밋). 별도 로그 파일 없음 — `gates/run.sh` 는 1건씩 실행하며 같은 경로를 덮어쓰므로 마지막 실행분이 남는다.

## 5. intent 대조 (`dev-package/intent/2026-09-08-r-d.md` 규칙 3·4)

- 축자 = 규칙 3 「… `main` 으로는 ff-only 한 줄. **병합 뒤 브랜치 삭제**.」 · 규칙 4 「`lane/wu-*` 는 … rebase＋ff 로 돌아온다. **통합에 얹힌 즉시 삭제**.」

### 미달 3건 (셋 다 「오케스트레이터 유예」 · 조사 미달은 아니다 · advisor ② 2026-09-08 정정: 2→3)

1. 규칙 3 「병합 뒤 브랜치 삭제」 미집행 — `integration/r-a2`·`integration/r-b` 는 조상·밖 커밋 0 으로 조건 충족이나 로컬·원격 잔존. 막는 것 = advisor ① 조건 ⑵ ＋ spec 우려 11(레인 산출을 표 ＋ 로컬 태그까지로 한정).
2. 규칙 4 「통합에 얹힌 즉시 삭제」 미집행 — 대상은 `lane/wu-d4` 자신. 막는 것 = 병합 미수행(얹는 주체가 오케스트레이터).
3. spec 우려 6 「원격까지 태그」·라운드 ⑵ 원격 태그 push 미집행 — `archive/*` 10 건은 로컬만(원격 0). 막는 것 = advisor ① 조건 ⑵(원격 push 는 게이트 ③ 뒤 오케스트레이터 · 개별 push · `--tags` 금지).

### 초과 0건

- 표·태그·게이트·이 노트 외 산출 없음. 제품 코드 0 · 계약 0 · 스키마 0 · 마이그레이션 0 · `frontend/` 0.
- 표 §9 후속 3건은 **기록만** — 고치지 않았고 대장에도 올리지 않았다(등재는 오케스트레이터 몫).

## 6. 지시문과 어긋난 실측 1건 — `gh-pages`

- 기대 = 「Ted 한 줄 뒤 삭제 · 단 용도 확인 전 무접촉」 / 실측 = GitHub Pages **가동 중**이고 원천 브랜치가 `gh-pages`(`"status":"built"` · `"source":{"branch":"gh-pages"}` · `https://cognileapai.github.io/colab-v2/`).
- ⟹ 권고를 **보류**로 바꾸고 태그도 만들지 않았다. 삭제 대상으로 두려면 Pages 설정 해제가 선행이고 이 라운드 범위 밖이다.
