# R-C-3 · 검증 계층 ＋ R-C 종료 검증 — WU-C12 — spec: `dev-package/prd/specs/R-C.md` (출처 intent `dev-package/intent/2026-09-08-r-c.md` 우산 · `dev-package/intent/2026-09-08-preview-slot.md` 축 ①)

> ⛔ **착수 조건 = Ted 가 intent 2건을 커밋(승인) ＋ 21차 승인 문장 기입. 그 전에는 이 파일로 세션을 열지 않는다.** 이 파일은 R-C-1·R-C-2 의 11 WU 가 전부 `done` 인 뒤에 연다.
> 이 파일 하나로 세션을 시작한다. 라운드 = **R-C** · 계층 = **검증** · WU **1건**(C12) ＋ **라운드 종료 검증 · 병합 · 등재**. 세 파일 중 마지막이다.
> 통합 브랜치 `integration/r-c` · 워크트리 `.claude/worktrees/r-c` · 기점 = `main` tip(해시 박지 않음). 계약 21차(㉮ 전망 · R-C-1 집행) · 마이그레이션 2 전망(＋ `db/ai` 1) · 이 파일 자체는 계약 0 · 마이그레이션 0.
> spec 우선(`prd/specs/README.md`).

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.** `dev-package/03-HANDOFF.md` · `dev-package/PLAN-SoT.md` · `dev-package/work-items.yaml` · `dev-package/WORK-UNITS.md`

- **허용된 접근은 아래 세 줄뿐이다.**
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-C1' dev-package/work-items.yaml`(C1~C12 각각)
  3. 게이트 이름 확인 — `grep -n -A18 '^ALL_GATES=(' gates/run.sh`
- `03-HANDOFF.md` · `CLAUDE.md` · `RESTART.md` 는 머리 부분만. 정본 = spec ＋ intent 2건 ＋ 이 파일. 디자인 판정표 `dev-package/sessions/p3-design-audit-20260905.md`(46행)는 **통째로 읽는다**(재실측 기준선).
- 레인 세션 노트 11건(`dev-package/sessions/rc-*-<YYYYMMDD>.md`)은 **각 ≤60행** — 통째로 읽어 취합한다.
- `path:line` 은 R-C-1·R-C-2 뒤 트리에서 **다시 잰다**. 못 재면 `[미상]`.

### 세션 시작
```bash
cd "<작업공간>/30 CoLAB-v2" && claude --add-dir "../40 COLAB-기획"
git -C .claude/worktrees/r-c rev-parse HEAD && git -C .claude/worktrees/r-c status --porcelain   # 0행
for w in C1 C2 C3 C4 C5 C6 C7 C8 C9 C10 C11; do grep -A2 "^  - id: WU-$w$" dev-package/work-items.yaml | grep status; done   # 11 done
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전 재실측
```
- 에이전트 역할 — `advisor`(fable · ②·③ go/no-go) · `lane-worker`(opus) · `gate-runner`(haiku · `all -j 1` 실행·계수 회수).

---

## 1. 확정 결정 — 다시 열지 않는다

- 2026-09-05 확정 16 · 2026-09-06 확정 12 · 2026-09-08 R-B 61건 · 2026-09-08 축 ① 16 판정 · 우산 intent Q1~Q7 — 축자는 `R-C-1-contract-db.md §1`·`R-C-2-frontend.md §1`. **재개봉 0.**
- 이 파일이 잰다: **틀 4:3** · **상세 좌우** · **500MB 조각 폴백** · **파일·변수·시각 선택** · **사다리 스냅** · **NE 배경 ≤500KB** · **POL-021 부분 반전 〈N〉(원문 무삭제)** · **21차 첨가 6건 ㉮(`contract-breaking` 축자)** · **head 1(`0021`)** · **Lv 4자리 통일** · **게이트 `migration-drift` 오라클 11** · **변수명 UNIQUE 0**(판정 A) · **한반도 고정 프레임 0**(Ted 철회).
- 다르게 구현된 것을 찾으면 **고치지 말고 보고한다** — 이 파일은 검증이지 재작업 자리가 아니다.

---

## 2. 범위 — WU 1건 ＋ 라운드 종료 검증

### §A · WU-C12 · R-C 종료 검증 (디자인 재실측 ＋ 전수 게이트 ＋ intent 대조) — 계층 검증 · 크기 M · 레인 `rc-verify`

- **의존** — WU-C1~C11 전부 `done`. 계약 0 · 스키마 0 · 마이그레이션 0. ⛔ 21차 해제를 **쓰지 않는다**.
- **할 일** ⑴ 디자인 검수 재실측 — `p3-design-audit-20260905.md` 11항 ＋ R-B §5-45~49 5항을 R-C 뒤 CSS 에서 **grep 계측**으로 다시 잰다(있음/없음/`[미상]`) ⑵ 전수 게이트 `bash gates/run.sh all -j 1` **한 번의 실행**(다른 레인 정지) ⑶ intent 대조 — `preview-slot.md ## 원한 결과` 1~10 ＋ `r-c.md ## 원한 결과` 축 ② 4묶음을 **미달·초과** 로 열거(advisor ②) ⑷ 축 ② 19건 소유 대조표 — §6 각 항목 → WU → 커밋 → 수용 기준 통과 여부(변수명 UNIQUE = 「판정 A 로 종결 · 미착수」 명시 · 배포 창 실측 3건 = 「R-C 밖」 명시) ⑸ 경계·회귀 증명 ⑹ 병합·등재(§B).
- **수용 기준** — 재실측표 16항 전부 판정값 있음(`[미상]` 0) · `all -j 1` green / red(판정) 0 / red(준비) 0 · 미달·초과 열거표 존재(0건이어도 「0건」 을 적는다) · 소유 대조표 19행.
- **좁은 게이트** — `work-item-consistency` · `planning-freshness` · `exec-bit`(자산·스크립트 비트) → 전수 `all -j 1`.

### §B · R-C 라운드 종료 검증 — 이 파일이 라운드의 마지막이다

- **경계 증명 3건** — `cross-tenant 음성 0건`(C7 `0020`·`0021` · RLS 무변) · `state='잠김' ∧ 유효 grant ≥1` 행 **어느 시점에도 0건**(C7 · R-B 유지) · 미리보기 네트워크 요청 = 자기 origin 뿐(C5 · 외부 0).
- **회귀 증명 4건** — `processingLevel` 열쇠 값 종전과 동일(C9 · 사람 값은 별 열쇠) · 비지도형 미리보기 종전과 동일(C4) · 장면1 = 드롭존만(C1 · PRD-260905:385) · 변수 검색·자동완성 종전과 동일(C7 트리거 전환).
- **절차 검증 5항** — §5 에 적는다.
- **배포 창 인계 4건**(R-C 밖 · 명시 인계) — `0020` 중복 이름 건수 · `0021` 대상 행 실측(판정 20) · 0019 백필 손실(35) · 판정식 전환 행(40) ＋ `COLAB_VIZ_WORK_MAX_BYTES` 배포값 기록.

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 워크트리 레인
- 레인 `rc-verify` 하나. 코드 수정은 **재실측이 드러낸 결함의 보고**까지다 — 고치려면 소유 WU 를 재개봉하지 말고 **R-D 후보로 등재**한다.

### ㉯ 착수 전 — 대장
- 11 WU `done` 확인(세션 시작 블록) · `WU-C12` `open` → 완료 시 `done` ＋ `evidence`.

### ㉰ 계약 동결 해제 — **이 파일은 계약을 열지 않는다**
- 21차 집행은 R-C-1 WU-C10 에서 끝났다. 여기서는 **승인 커밋 → `contracts/` 첫 수정** 순서를 `git log` 로 증명한다.

### ㉱ 결정 번호 〈N〉 — 병합 직전 재실측 · 3행
```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 이 값 ＋ 1 부터
```
- 착수 시점 참고값 = **〈374〉**(2026-09-08 · 근거 아님). `PLAN-SoT §9` 행에는 **`intent:`·`spec:` 두 필드**를 함께 적는다(`〈369〉`-㉱ · `renumber-decisions.sh` 대조). ⛔ HANDOFF 에 값을 적지 않는다.

```
| 〈N〉 | **R-C 집행 — 미리보기 5건(틀 4:3 · 상세 좌우 · 500MB 조각 폴백 · 파일·변수·시각 선택 · 사다리＋배경) ＋ R-B 후속(게이트 승격 3종 · 서버·FE 소형 · Lv 통일 · CSS 잔여) 12 WU** | **집행 (2026-MM-DD · 통합 `integration/r-c` · 병합 `<sha>`).** ①회차 = **21차**(직전 20차 = R-B) ②값 = `describe` 조회 · `processingLevelUserSet`(노드·`ProjectDatasetRow`) · `DataMap.byCategory` · `declareLineageUnknown`·`updateLineageParentMethod` · `parentProcessingLevel` ③근거 = intent 축 ① 16 판정 ＋ R-B §5 판정 A(9·14·16·19·20·23·24·27·28·31·33·36·41·42·43·45~49) ④가·파 판정 = `<㉮/㉯ 실측>` · `contract-breaking` 출력 = `<축자>` ⑤소비자 = `<n>` 건 · 측정법 = `grep -rn 'describe\|processingLevelUserSet\|byCategory\|declareLineageUnknown\|updateLineageParentMethod\|parentProcessingLevel' contracts/ services/ frontend/src` ⑥마이그레이션 = **2건 · head 1개**(`0020`·`0021` · 앞 head `0019_rb7_search_index_m10`) ＋ `db/ai` `0004` ⑦승인 = Ted · `<일자>` · 원문 `<축자>` ⑧이번에 세지 않은 축 = 배포 창 실측 4건(0020 중복 · 0021 대상 행 · 0019 백필 · 판정식 전환) `[미측정]` · intent: `dev-package/intent/2026-09-08-r-c.md` · spec: `dev-package/prd/specs/R-C.md` |
| 〈N+1〉 | **POL-021 「타일 서버도 바탕 지도도 쓰지 않는다」 부분 반전 ＋ ㉴ 「B-2 해안선 오버레이 미채택」 반전 — 자립형 벡터 배경(레포 반입 · 외부 요청 0)만 허용 · 타일 서버·CDN 금지 유지** | **반전 (Ted 2026-09-08 · 원문 「자립형 벡터 해안선 · POL-021 부분 반전」).** ⛔ `PLAN-SoT.md:591`·`WORK-UNITS.md:425`·`CLAUDE.md:19` 원문을 지우지 않는다 — 덧붙인다. 자산 = `frontend/src/assets/basemap/`(NE 1:110m · `<KB 실측>`) · intent: `dev-package/intent/2026-09-08-preview-slot.md` · spec: `dev-package/prd/specs/R-C.md` |
| 〈N+2〉 | **계약 동결 해제 21차 — 첨가 6건 · 등급 `<실측>` · R-C-C21-REQUEST** | **집행 (Ted 승인 `<일자>` · `dev-package/sessions/R-C-C21-REQUEST-<날짜>.md`).** ①~⑧ 은 〈N〉 과 같다 · 승인 커밋 `<sha>` 이 `contracts/` 첫 수정 `<sha>` 보다 앞선다(`git log` 축자) · intent: `dev-package/intent/2026-09-08-r-c.md` · spec: `dev-package/prd/specs/R-C.md` |
```
- 세 행이 한 회차에서 나오면 순서는 21차(승인) → POL-021 반전 → R-C 집행 이 시간순이다 — 번호는 **시간순**으로 붙인다.

### ㉲ 게이트 — 전수 1회
```bash
COLAB_GATE_REPORT_DIR=dev-package/reports/R-C/all bash gates/run.sh all -j 1   # 다른 레인 정지 · 한 워크트리에 한 벌
```
- 판정 = **한 번의 실행**으로 red(판정) 0 ＋ red(준비) 0. 두 실행에 걸친 계수는 판정이 아니다. 마지막 커밋 뒤 한 번 더.
- 병합 트리가 이미 판정된 트리와 같으면 `main` 전수를 다시 돌리지 않는다 — 트리 해시로 갈음(`〈333〉` 선례).

### ㉳ 커밋 문면
```
검증 R-C-3 라운드 종료 검증 (WU-C12)

- 재실측 16항 · all -j 1 green <n>/<n> · 미달 <n> 초과 <n> · 소유 대조 19행
- 계약 0 · 스키마 0 · 마이그레이션 0 · 〈N〉·〈N+1〉·〈N+2〉 등재(병합 직전 실측)
```

### ㉴ 금지
- ⛔ `main` 직접 push(ff 한 줄만) · ⛔ `contracts/` · ⛔ 마이그레이션 · ⛔ staging DB 직접 쓰기 · ⛔ `done` WU 재개봉 · ⛔ 결함을 이 레인에서 고치기(R-D 등재).
- ⛔ 〈N〉 예약 · ⛔ POL-021·`〈194〉`·`〈276〉` 원문 삭제 · ⛔ HANDOFF 본문 직접 수정(5줄만 넘긴다) · ⛔ `40 COLAB-기획/` 수정 · ⛔ 절대경로.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| 재실측표 | `dev-package/sessions/rc-verify-<YYYYMMDD>.md` — 디자인 11＋5 항 · 경계 3 · 회귀 4 · 절차 5 · 소유 대조 19행 · 미달·초과 열거 — **≤ 80행** |
| 게이트 요약 | `dev-package/reports/R-C/all/gate-summary.json`(미추적) |
| 라운드 마감 | `dev-package/sessions/R-C-ROUND-<YYYYMMDD>.md` — WU 지도 · advisor ② 12건 · 후속(R-D 후보) · 배포 창 인계 4건 |
| 원장 | `PLAN-SoT §9` **3행**(㉱ 문안 · 시간순) |
| 대장 | `work-items.yaml` — `WU-C12` `done` ＋ `evidence` · 12/12 |
| 환류 | `python3 dev-package/tools/planning-applied.py --sync` → `--sync --apply` → `bash gates/run.sh planning-freshness` · `prd/README.md` 상태표 |
| 승인 흔적 | intent 2건 커밋 sha · `R-C-C21-REQUEST` 승인 블록 · 21차 승인 커밋 → `contracts/` 첫 수정 순서(`git log` 축자) |

**HANDOFF 갱신문(오케스트레이터가 붙인다 · 5줄 이하)**
```
최종 갱신 2026-MM-DD — R-C 12 WU(C1~C12) 전건 done · integration/r-c <sha> → main ff 한 줄 · 등재 〈N〉(R-C 집행)·〈N+1〉(POL-021 부분 반전)·〈N+2〉(21차)
게이트 = 전수 all -j 1 한 번의 실행 green <n> / red(판정) 0 / red(준비) 0(트리 <sha> · dev-package/reports/R-C/all/) · 신설 migration-drift(오라클 11)
계약 21차 첨가 6 · 등급 <실측> · 마이그레이션 0020·0021 head 1 ＋ db/ai 0004 — 어느 환경에도 미적용 · 배포 0(다음 배포 창 = R-B 5건 ＋ R-C 3건 ＋ 실측 4건)
근거 = dev-package/sessions/R-C-ROUND-<YYYYMMDD>.md · spec dev-package/prd/specs/R-C.md
다음 = 배포 창(실측 4건 → 마이그레이션 8건 → deploy_doctor) · R-D intent(재실측 결함 · 22차 후보)
```

---

## 5. 완료 판정

- **WU-C12** — 재실측 16항 판정값(`[미상]` 0) · `all -j 1` green(판정 red 0 · 준비 red 0 · 다른 레인 0) · 미달·초과 열거표 · 소유 대조 19행(UNIQUE = 판정 A 종결 · 배포 창 3건 = 밖).
- **경계 증명 3건** · **회귀 증명 4건** — §B 축자.
- **절차 검증 5항**
  1. **intent 2건이 Ted 커밋으로 승인**돼 있다(sha) — 초안 상태로 레인이 돌지 않았다.
  2. **21차 승인이 `contracts/` 첫 수정보다 먼저** 있었음이 커밋 순서로 보인다.
  3. **〈N〉·〈N+1〉·〈N+2〉 가 병합 직전 실측값**이다(예약값 아님 · `intent:`·`spec:` 필드 포함).
  4. **POL-021 반전이 원문을 지우지 않고** 덧붙여져 있다(3자리).
  5. **마이그레이션 head 1개** — 착수 시점 실측 head = `0019_rb7_search_index_m10` · R-C 가 `0020`→`0021` 을 잇는다 · `db/ai` 별 체인 `0004`.
- **병합** — `integration/r-c` → `main` **ff 한 줄** ＋ `prd/README.md` 상태표 ＋ `planning-freshness` green.
- 라운드 완료는 **위 전부**다. 부분 완료로 WU 를 닫지 않는다.

### 다음 파일
없다 — R-C 의 마지막 파일이다. 다음 = 배포 창(`docs/DEPLOY.md` · 실측 4건 선행) → R-D intent(grill-me).
