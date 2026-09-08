# 레인 `rd-branching-doc` — WU-D1 (2026-09-08)

- 브랜치 `lane/wu-d1` · 기점 `origin/integration/r-d` `643436b`(지시문 기대값과 일치) · 제품 코드 0 · 계약 0 · 스키마 0 · 마이그레이션 0 · `frontend/` 0.

## 1. 전/후 (행 수 · `--numstat` 추가/삭제)

- `docs/BRANCHING.md` 부재 → **76** (신설) · `CLAUDE.md` 169 → **182** (`13 0`) · `dev-package/RESTART.md` 353 → **354** (`1 0`) · `infra/dev/README.md` 117 → **119** (`2 0` — 본문 1 ＋ 빈 줄 1).
- `git diff origin/integration/r-d --numstat -- CLAUDE.md dev-package/RESTART.md infra/dev/README.md` ⟹ **삭제 열 전건 0**.

## 2. 수용 기준 대조 (`R-D-1-branching.md §2 WU-D1` · `§5`)

| 기준 | 판정 | 근거 |
|---|---|---|
| 규칙 6 문면이 intent `## 원한 결과` 1~6 과 축자 일치(diff 0) | 충족 | §2-1 — RED 6행 결손·exit 1 → GREEN 출력 0행·exit 0 |
| `CLAUDE.md` `## 10.` 존재 | 충족 | `grep -c '^## 10\.' CLAUDE.md` = **1**(전 0) |
| `CLAUDE.md` §9 원문 삭제 0 · 두 README 삭제 0 | 충족 | numstat `13 0`·`1 0`·`2 0` |
| 브랜치 수명 표(기점·복귀·삭제 시점·누가) | 충족 | `docs/BRANCHING.md §2` 7행(`main`·`integration/r-N`·`lane/wu-*`·`plan/*`·`archive/*`·`dev-*`·`prod-*`) |
| 「하지 말 것」 ＋ 실측 예시 | 충족 | 같은 파일 §3 7행 · 출처 `WU-D4-branches-20260908.md` §1·§2·§7·§10 |
| 창 9 사례 한 문단 ＋ `〈378〉 ⑧` 링크 · `planning-freshness` green | 충족 | 같은 파일 §4 · 이 노트 §3 |

### 2-1. 문면 대조 한 줄 (행 번호 대신 내용 앵커)

```bash
diff <(sed -n '/^\*\*축 ① 규칙 6개\*\*/,/^\*\*축 ① 산출물\*\*/p' dev-package/intent/2026-09-08-r-d.md | grep -E '^[1-6]\. ') \
     <(sed -n '/<!-- rule6:begin -->/,/<!-- rule6:end -->/p' docs/BRANCHING.md | grep -E '^[1-6]\. ')
```

## 3. 게이트 (좁은 집합 3종 · 배출처 `dev-package/reports/R-D/rd-branching-doc`)

- 3종 전부 **green 1 / red(판정) 0 / red(준비) 0**. 요약줄 축자 —
  - `planning-freshness green — 임베드 블록 15개 전부 원본과 일치 · 적용 상태 4건 정합.`
  - `work-item-consistency: green — 대장과 산문의 불일치 0`
  - ``exec-bit green — `.sh` 144건 전부 인덱스 모드 100755 (100644 = 0건).``
- red 0 ⟹ 「어느 검사에 걸리는가」 판독 대상 없음. 배출처 JSON 은 `.gitignore` 대상이라 미커밋 · 1건씩 실행하며 같은 경로를 덮어쓴다.

## 4. 하지 않은 것

- `infra/dev/ship.sh`·`infra/staging/deploy.sh`·`services/core-api/ops/deploy_doctor.py` 무접촉.
- `work-items.yaml`·`03-HANDOFF.md`·`PLAN-SoT.md` 편집 0 · `eval/` 무접촉(병렬 레인 `lane/wu-d5` 영역) · 〈N〉 기입 0 · 병합 0 · push 0 · 브랜치 삭제 0.
- 실측 재수행 0 — 「하지 말 것」·창 9 수치는 `WU-D4-branches-20260908.md` 인용이다.

## 5. intent 대조 (`dev-package/intent/2026-09-08-r-d.md` 「원한 결과」 축 ①)

### 미달 3건 — 전부 다른 WU 소관(이 레인의 결손 아님)

1. `ship.sh` 앞단 게이트 ＋ `MAIN_SHA` 반입(규칙 1) — `WU-D2`. 실측 `grep -cE 'merge-base|MAIN_SHA|COLAB_SHIP_ALLOW_NONMAIN' infra/dev/ship.sh` = **0**.
2. staging 원장 `브랜치=` 필드(규칙 2) — `WU-D2`.
3. `deploy_doctor` 15번째 항목 — `WU-D3`. 실측 `deploy_doctor.py:62` `MARKS` **14자**.
- ⟹ 규칙 1·2·6(태그 도구)의 **집행**은 `WU-D2`·`WU-D3`, 이 레인 범위는 **문면 정본화**. `docs/BRANCHING.md §5` 가 「예정 동작 · 지금은 없다」로 명시한다.

### 기존 오라클로 충족 1건 (미달 아님)

- 규칙 5(한 라운드 = 한 체인 구간) — intent 산출물 목록에 신설 seam 요구 없음. 강제는 기존 `migration-single-head` ＋ drift 오라클(0007 선례)이 이미 한다.

### 초과 2건 (경미 · 되돌리지 않음)

1. 문면 대조 한 줄을 노트뿐 아니라 `docs/BRANCHING.md §1` 에도 실었다(라운드 요구는 「노트에 축자」). 남긴 이유 = 규칙 6 을 고칠 때 대조법을 문서 안에서 재현.
2. 「하지 말 것」 표에 intent 산출물 목록 밖 3행 — ⑸ `git push origin --tags` · ⑹ 태그 없이 브랜치 삭제 · ⑺ 열린 PR head 삭제. 근거 = `WU-D4-branches-20260908.md` §1·§2·§7·§10 실측.
- 둘 다 제품 동작 영향 0 · 계약 0.

## 6. 셀 수 없었던 것 · 후속

1. 규칙 6 축자 일치를 **기계가 잡지 않는다** — §2-1 은 손으로 돌리는 명령이고 `ALL_GATES`(`gates/run.sh`)·Dockerfile·배포 스크립트 어디에도 항목이 없다. ⟹ 후속 = 게이트 항목으로 승격(`CLAUDE.md §4`).
2. 「하지 말 것」 ⑺ 의 open PR 3건(#4·#5·#6)은 `WU-D4-branches-20260908.md` 작성 시점 값 · 이 레인은 GitHub 재조회 0.
3. `CLAUDE.md §10` 6줄과 `.claude/rules/deploy.md`·`docs/DEPLOY.md` 전문의 충돌 여부 — 두 파일 머리만 읽었고 전문 대조 미수행(`[미상]`).

## 7. advisor ② 반영 (2026-09-08 · 브랜치 `lane/wu-d1b`)

1. §4 창 9 서술 — 「`migrate-ai` 직전 STOP」 근거 0(R-C 배포 로그·`WU-C13` 노트에 STOP 기록 없음) ⟹ 「dev 사전 실측에서 `alembic_version_ai` 스탬프 `0006_topic_vocab_six` 가 `main` 에 없는 리비전으로 발견」 으로 교체. 출처 = `R-C-ROUND-20260908.md §9` 첫 항목 · `WU-C13-ai-merge-20260908.md` 머리 3줄.
2. §1 — 규칙 6 축자 블록은 무수정(diff 0 유지) · 블록 아래에 검사 자리 확정 1줄 추가(설계트리 Q2 = `ship.sh` 한 곳 ＋ `deploy_doctor` ⑮ · `up.sh`·`deploy.sh` 이중 검사 없음).
3. `CLAUDE.md §10` 마지막 줄 — 삭제 주체에 한정어 부착(정리 대상 = `WU-D4` 류 · 병합 경로 밖). 병합된 `lane/*`·`integration/*` 즉시 삭제(`colab-rules.md §2-1`)와의 충돌 해소.
4. §4 링크 — `〈378〉 ⑧` 앵커가 그 행에 두 개라 `R-C-ROUND-20260908.md §9` 병기.
5. §1 표제 — 「고치려면 intent 를 먼저 고친다」 → 「병합 뒤 정본 = 이 파일 · 개정은 새 intent ＋ 이 파일 동시」. intent 개정이 축자 검사를 영구 red 로 만드는 자리 제거.
6. 이 노트 §5 — 미달 4→**3**(규칙 5 는 기존 오라클로 충족) · 초과 1→**2**(§1 diff 한 줄 ＋ 「하지 말 것」 3행).
