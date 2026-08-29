# 작업 브랜치 4종 `main` 병합 회차 — 명령·출력·시각

> **판정과 값의 정본 = `dev-package/PLAN-SoT.md §9 〈209〉`.** 이 파일은 원시 기록이고 값을 새로 세우지 않는다.
> 범위 = 로컬 병합만. **push · force-push · 공유 이력 rebase 0건.** 운영 스택 무접촉(읽기도 없음).

## 1. 시작 상태 (2026-08-29)

- `git log --oneline -1 main` = `d05171b` 「문서: X-5 판정 5건의 결정 브리프를 사후 등재한다」
- `git status` = 작업 브랜치 `work/pv1-cog-step` 체크아웃 · 추적 변경 0 · **미추적 2**
  (`dev-package/STAGE2-ROADMAP.md` · `dev-package/STAGE2-DECISION-BRIEF.md`)
- `git branch -a` = 로컬 6(`main` · `env/stage2-env-prereq` · `env/stage2-prereq` · `work/r1-restore-tails`
  · `work/s2-evalset-close` · `work/pv1-cog-step`) · 원격 1(`origin/main`)
- ⚠ `env/stage2-prereq` 는 이번 병합 대상이 **아니다**(지시 목록 밖). 손대지 않았다.

## 2. 게이트 기준선 (병합 전 · `main` = `d05171b`)

`./gates/run.sh all -j 6` — **green 25 · red 2**

| red | 사유 |
|---|---|
| `schema-diff` | `COLAB_APPLIED_DB_URL_PLATFORM`·`_AI` 미지정. **환경 부재이므로 red 로 센다 — 통과가 아니다.** |
| `work-item-consistency` | 불일치 **3건**(`㈓` conflict `S2b`·`R-1`·`S2`) |

## 3. 커밋 ①  미추적 산출물 등재 — `7861f10`

- `dev-package/STAGE2-ROADMAP.md`(152행) · `dev-package/STAGE2-DECISION-BRIEF.md`(335행)
- 내용 무수정. 이번 회차 산출물이 미추적으로 떠 있던 것을 레포에 고정한 것뿐이다.

## 4. 병합 4회 — 각 회차 직후 전 게이트 1회 완주

| # | 브랜치 | 병합 커밋 | 충돌 | green | red | `㈓` 불일치 |
|---|---|---|---|---|---|---|
| 1 | `env/stage2-env-prereq` (`d259a38`) | `a0ff650` | 없음 (ort · 4파일) | 25 | 2 | 3 |
| 2 | `work/r1-restore-tails` (`1b700be`) | `23e02bd` | 없음 (ort · 6파일) | 25 | 2 | **2** |
| 3 | `work/s2-evalset-close` (`3a7af7b`) | `6a15be5` | **`PLAN-SoT.md` 1자리** | **26** | **1** | **0** |
| 4 | `work/pv1-cog-step` (`e7e4f80`) | `1571a1c` | 없음 (ort · 1파일 신설) | 26 | 1 | 0 |

- 2회차에서 불일치가 3 → 2 로 준 것은 `R-1` 이 `conflict` → `partial` 로 갈렸기 때문이다.
- 3회차에서 `work-item-consistency` 가 **red → green** 으로 전이했다. **green 이 red 로 뒤집힌 게이트는 0건.**
- `work/r1-restore-tails` 는 `env/stage2-env-prereq`(`d259a38`)를 이미 품고 있어 2회차 차분이 자기 것만 남았다.

## 5. 충돌 하나 — `PLAN-SoT §9` 번호 충돌과 해소

**무엇이 부딪혔나**

- `main` 의 마지막 항목 번호 = `〈206〉`
- 두 브랜치가 서로를 못 본 채 각자 `〈206〉` 뒤에 **똑같이 `〈207〉`** 을 발급했다
  - `work/r1-restore-tails` — 「복원 절차의 잔여 세 꼬리」
  - `work/s2-evalset-close` — 「검색 평가셋 항목 둘을 산출물 완료로 닫는다」
- git 충돌 자리는 표 꼬리 **한 줄**(`<<<<<<<` 1묶음)

**어떻게 갈랐나**

1. **병합 순서가 앞인 쪽이 번호를 갖는다** — 복원 절차 회차가 `〈207〉` 유지.
2. 평가셋 회차를 **`〈208〉` 로 옮겼다.** 제목·본문·근거·실측값 **한 글자도 고치지 않았다.**
3. **항목은 하나도 지우지 않았다.** 두 항목 모두 표에 살아 있다(`〈207〉` · `〈208〉`).
4. **`〈208〉` 을 가리키던 참조 12자리를 함께 옮겼다** — 파일별 실측:
   - `dev-package/03-HANDOFF.md` — `S2` 행 1 · 진입조건 ⑴⑵ 2 · `§5` 확인표 6행 1 (계 4)
   - `dev-package/WORK-UNITS.md` — `§8.5` `S2`·`S2b` 2 · `§11` 초기데이터 줄 1 (계 3)
   - `dev-package/work-items.yaml` — `S2b` 2 · `S2` 1 · `K4` 2 · `P4` 2 (계 7)
   - `dev-package/sessions/S2-S2B-CLOSE-MEASURE.md` — 머리 1
   - **`〈207〉` 로 남긴 자리**(복원 절차 회차 소관) = `WORK-UNITS §10.3` 3 ·
     `sessions/R1-RESTORE-DRAFT.md` 4 · `sessions/R1-TAILS-EXEC.md` 1
5. **`〈208〉` 항목 안에 번호 개정 표시를 박았다** — 어디서 어디로 옮겼는지 · 왜 옮겼는지 ·
   내용 무수정이라는 것 · 참조를 함께 옮겼다는 것.

**남는 규율** — 번호 충돌은 브랜치가 각자 `§9` 꼬리에 붙어서 생긴다. **발급은 병합 시점에 다시 센다.**

## 6. 병합이 만든 상태 표기 모순과 그 정합

- **어긋난 자리** — 평가셋 회차는 자기 브랜치에서 「불일치 **3 → 1**(`R-1` 만 남는다)」로 적었다.
  같은 날 복원 절차 회차가 **`R-1` 을 `conflict` → `partial`** 로 갈랐고, 두 회차는 서로를 못 봤다.
- **병합 후 실측** = `㈓` conflict **0건** · `work-item-consistency` **green**.
- **고친 자리 3** (원문은 지우지 않고 취소선 ＋ 개정 표시):
  - `03-HANDOFF §1` 진입조건 ⑴⑵ — 「1 건(`R-1`)」 → **0 건**
  - `03-HANDOFF §5` 확인표 6행 — 기준값 `1` → **0**
  - `gates/README.md` `work-item-consistency` 행 — 「3 건」 → **0 건 · green**,
    함께 자란 계수도 재측(㈐ 67 → **70 행** · ㈏ 47 → **49 건**)
  - `PLAN-SoT §9 〈208〉` 「효과」 대목 — 「3 → 1」에 병합 후 실측 0 을 개정 표시로 붙였다
- **지운 것 0.** 뒤집힌 값은 취소선으로 남겼다.

## 7. 최종 상태

- `main` = `1571a1c`
- `./gates/run.sh all -j 6` — **green 26 · red 1**
- **red 1 = `schema-diff`** — `COLAB_APPLIED_DB_URL_PLATFORM`·`_AI` 미지정.
  **이 회차가 만든 red 가 아니다** — 시작 기준선에도 같은 red 였다.
  **푸는 법** = 체인마다 DB 를 세워 `db/<체인>/versions` 를 alembic `upgrade head` 한 뒤
  그 URL 을 체인별 변수로 넘긴다(`sessions/D3-db.md §3`). **게이트를 좁히지 않는다.**
- `work-item-consistency` **green**(불일치 0) — 이 회차 전이.
- push · force-push · 공유 이력 rebase **0건.** 운영 스택 접촉 **0건**(읽기 포함).
- 브랜치 삭제 **0건** — 병합원 4개는 그대로 남겼다(정리는 Ted 판정 자리).

## 8. 이번에 세지 않은 판단기준

- **`schema-diff` 의 두 체인 드리프트** — 적용 DB 를 세우지 않았다 → `[미확인]`.
- **서비스 시험 수**(core-api · frontend · ai-service · viz-render · pipeline-worker) —
  병합이 코드에 손대지 않아 돌리지 않았다 → `[미확인]`.
  ⚠ 다만 `env/stage2-env-prereq` 가 시험 env 배선과 일회용 사전 DB 부트스트랩을 들여왔으므로,
  **그 배선이 실제로 시험을 돌리는지는 이 회차가 재지 않았다.** 푸는 법 = ai-service 시험 1회 완주.
- **`〈207〉`·`〈208〉` 본문의 실측값 재검증** — 각 회차가 잰 값을 그대로 옮겼고 다시 재지 않았다.
