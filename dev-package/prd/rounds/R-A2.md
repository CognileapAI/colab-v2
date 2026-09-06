# R-A2 · rev2 증분 5 WU — spec: `dev-package/prd/specs/R-A2.md` (출처 intent `dev-package/intent/2026-09-06-r-a2.md`)

> 이 파일 하나로 세션을 시작한다. 라운드 = **R-A′** · 통합 브랜치 `integration/r-a2` · 워크트리 `.claude/worktrees/r-a2` · 기점 `27733ba`(= `origin/main`).
> **계약 0 · 스키마 0 · 마이그레이션 0.** 계약 동결 해제 회차를 쓰지 않는다.
> 어긋나면 **spec 이 이 파일보다 우선한다**(`prd/specs/README.md`).

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.** `dev-package/03-HANDOFF.md` · `dev-package/PLAN-SoT.md` · `dev-package/work-items.yaml` · `dev-package/WORK-UNITS.md`

- 허용된 접근은 세 줄뿐이다.
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-A13R' dev-package/work-items.yaml`
  3. 게이트 이름 확인 — `grep -n -A18 '^ALL_GATES=(' gates/run.sh` (`ALL_GATES` 배열)
- 요구사항 정본은 이 파일과 `dev-package/prd/PRD-260905-적용전기획.md`(2026-09-06 판본 · PRD-41~45 포함) 다. 더 필요하면 **해당 `#### PRD-xx` 절만** 읽는다.
- 코드 파일은 고칠 때만 연다. 현황 정찰·grep 스윕·다수 파일 읽기는 `researcher` 에 위임하고 결론만 회수한다.
- 못 읽으면 `[미상]` 이고 실패다. 지어내지 않는다.

### 세션 시작

```bash
cd "<작업공간>/30 CoLAB-v2" && claude --add-dir "../40 COLAB-기획"
# /context 의 Memory files 에 .claude/rules/colab-rules.md 가 뜨는지 확인한다
git -C .claude/worktrees/r-a2 rev-parse HEAD        # 현재 HEAD 를 읽는다(값을 미리 적지 않는다)
git -C .claude/worktrees/r-a2 status --porcelain    # 0행
```

- 기점은 `origin/main` **`27733ba` 이상**이다. 현재 HEAD 는 준비 커밋이 쌓이면서 바뀌므로 **문서에 특정 해시를 박아 두지 않는다** — `git rev-parse HEAD` 로 읽고, 기점 포함 여부는 `git merge-base --is-ancestor 27733ba HEAD` 로 판정한다.

- 에이전트 역할 — `advisor`(fable · 계획 검토 ① · 수용 검토 ②) · `lane-worker`(opus · `isolation: "worktree"`) · `researcher`(sonnet · 조사) · `gate-runner`(haiku · 게이트 실행·계수 회수).
- 의존성(워크트리 `node_modules` · 서비스 `.venv`)은 H2 `worktree-setup.sh` 가 스폰마다 건다. 손으로 `npm ci`·`uv venv` 를 치지 않는다.
- 시험 환경은 `gates/run.sh` 가 스스로 `~/.colab-v2-test.env` 를 source 한다. `set -a; . …; set +a` 관용구는 불요다.

---

## 1. 확정 결정 — 다시 열지 않는다 (28건 · 종결 2건)

다르게 구현할 사유를 찾으면 **고치지 말고 보고한다.**

- 2026-09-05 확정 16 — 미결-1 · 2 · 3 · 4 · 5 · 6 · 7 · 9 · 11 · 12 · 13 · 14 · 15 · 16 · 17 · 18
- 2026-09-06 확정 12 — 미결-r2-1(기간 종료 비움 허용 · 저장은 `period_end = period_start`) · r2-2(닫기 문면 3종 ＋ `계속하기`) · r2-3(연관 = 한 표 ＋ 유형 열) · 판정-1(존치 규칙 ⓐ) · 판정-2(달력 팝오버 ⓑ · **담는 WU 만 B3 로 이관**) · III-A(미결-17 종결 · 변수 표 5열) · III-B(`좌표계 (선택)`) · III-C · III-D · III-E · III-F(미결-1·4·6·11 유지 · 재판정 종결) · III-G(통보문 상단 상자)
- 종결 2(판정 아님) — 미결-8(해소) · 미결-10(WU-A11 실측)
- **존치 규칙 축자(판정-1 ⓐ)** — 「목업이 그리지 않았다는 사실은 걷으라는 지시가 아니다. 걷는 것은 Ted 가 항목별로 따로 판정한다.」
  존치 6종 = 기준 격자 파일 흐름(`upload/gridFlow.ts:38-83` · `UploadModal.tsx:566-593` · `FileDropCard.tsx:10,36-49`) · AI 계보 제안(`lineage/LineageStep.tsx:505-520` · `LineageSection.tsx:141-158`) · 2단 등록 게이트(`UploadModal.tsx:605-635`) · 이어올리기 배너(`UploadModal.tsx:467-511`) · 승인·검증 층(`DetailHeader.tsx:72,81-85` · `detail/LockedNotice.tsx`) · 값 조회(`datasetpreview/ValueLookupPanel.tsx`). **회귀 시험도 철거하지 않는다.**
- 기획자 회신 의존 **0건.**

---

## 2. 범위 — WU 5건 (순서 고정)

> PRD 축자 원천 = `dev-package/prd/PRD-260905-적용전기획.md`. 완료 조건은 `개발계획서_다음라운드_260906.md §1` 축자다.

### ① WU-A13R — 공통 토스트 ＋ 문면 21행 (PRD-32 · PRD-43 · 크기 M · 선행 없음)

- PRD 자리 — `PRD-260905-적용전기획.md:759`(PRD-32) · `:994`(PRD-43 · 문면 21행 표)
- 변경 — **프론트**: 공통 토스트 컴포넌트 1개 ＋ 문면 21행(각 문면은 그 자리를 담는 WU 가 호출). 확장자가 섞이면 첫 종류만 남기고 토스트 축자 `확장자가 다른 파일은 뺐어요. 한 번에 한 종류만 묶어요`. 비교는 소문자 기준(`.NC` = `.nc`).
- 변경 — **서버**: 한 업로드의 조각 확장자가 2종 이상이면 400. 화면 차단이 유일한 방어선이 되지 않게 한다.
- 변경 — **계약·DB**: 없음.
- 기존 데이터 — 조각 확장자 2종 이상인 데이터셋을 **센다. 고치지 않고 지우거나 쪼개지 않는다.**
- 완료 조건(축자) — 「21행이 전부 코드에 있고 하드코드 중복 0건(한 곳에서 온다) · 토스트가 스스로 사라지고 포커스를 뺏지 않는다 · `F-11`·`D-13` 의 건수가 보간값이다 · `D-07` 축약 표기가 `2025-06 ~ 09` 다」
- 좁은 게이트 — `service-tests-core-api` · `frontend-typecheck` · `frontend-test`

### ② WU-A12R — PRD-39 「없음」 잔여 5건 ＋ 커서 위경도 HUD (PRD-39 · 크기 S 6건 · 선행 A13R)

- PRD 자리 — `PRD-260905-적용전기획.md:884`
- 이번 라운드 몫 6건 — ① 파일 분석 3단계 표시 ＋ 완료 전 `다음` 비활성 · ② 모달 전역 드롭 수신 · ③ 파일 빼기 즉시 반영 ＋ 초기화 고지(`파일을 뺐어요. 입력하던 내용은 사라져요`) · ⑩ 접근 구역 출처 문장(`업로드할 때 정한 값이에요 · 올린 사람과 연구실 설정 권한자가 바꿀 수 있어요.`) · ⑫ 행동 줄 바닥 고정 ＋ 할 일 안내 3문면 · **HUD**
- HUD 축자 — 「`mousemove` 핸들러 1개 ＋ 역산 함수 2개(`pvLatOf`/`pvLonOf`) ＋ 문면 2종(`커서를 지도 위로` · `지도 밖`) · 서버 왕복 0」. **값 조회를 대체하지 않고 병존한다 — 역산값(HUD)과 셀값(값 조회)의 출처를 라벨로 갈라 적는다.**
- 회귀 — `있음` 4건(⑦ ⑧ ⑪ ⑬) ＋ 참고 ⑼ 각각에 회귀 시험 1건이 green.
- 변경 — 계약·서버·DB 없음. **판정 없이 고치지 않는다.**
- 좁은 게이트 — `frontend-typecheck` · `frontend-test`

### ③ WU-A7R — 한 표 ＋ 유형 열 ＋ 이름 중복 검사 (PRD-23 · PRD-42 · 크기 S · 선행 A13R)

- PRD 자리 — `PRD-260905-적용전기획.md:588`(PRD-23 개정본) · `:979`(PRD-42)
- 변경 — **프론트**: ③ 연결 단계의 연관 영역을 **표 한 장**으로 그린다. 열 = `유형` · `이름` · `해제`. 유형 배지는 **저장값 `kind`** 에서 읽는다(이름 문자열 정규식 판정 금지 · 값 집합 `ProjectFormModal.tsx:18` `['국가과제','논문']`). **0건이면 표 자체를 숨긴다.** `+ 새 프로젝트 만들기` 는 영역 맨 아래 **한 곳**.
- 변경 — **서버**: 같은 연구실 안에서 이름이 겹치면 거절(유형이 달라도 겹침). 문면 `같은 이름의 프로젝트가 이미 있어요. 목록에서 골라 주세요`.
- ⚠ **빈 이름 문면은 고치지 않는다** — `이름을 적어 주세요. 나중에 찾을 때 쓰는 유일한 이름이에요.` 가 정본이다.
- 기존 데이터 — 이미 겹치는 행은 **지우거나 고치지 않는다.** 신규 생성만 막는다.
- 완료 조건(축자) — 「같은 연구실 안에서 이름이 겹치면 유형이 달라도 거절하고 … 다른 연구실의 같은 이름은 성공한다」 ＋ 「표 한 장에 행을 쌓고 열이 `유형 · 이름 · 해제` 이며, 유형 배지가 저장값 `kind` 에서 오고, 연관 0건이면 표가 화면에 없다」
- 좁은 게이트 — `frontend-typecheck` · `frontend-test` · `service-tests-core-api`

### ④ WU-A9R — 닫기 문면 3종 ＋ 배경 클릭 닫기 ＋ 손댐 판정 (PRD-14 · 34 · 44 · 크기 S · 선행 A13R · A12R)

- PRD 자리 — `PRD-260905-적용전기획.md:405`(PRD-14) · `:793`(PRD-34) · `:1034`(PRD-44)
- 문면 3갈래 — 파일만(사람 입력 0 · 확정 계보 0) = 올린 파일이 취소된다 · 입력 있음(≥1 · 계보 0) = 적은 내용이 사라진다 · 입력＋계보(≥1 · ≥1) = 적은 내용과 **연결한 계보 N 건**이 사라진다(건수 보간). 제목 `업로드를 닫을까요?` 유지. 버튼 = `계속하기` · `닫고 나가기`.
- **축자 확정 시점** — 세 문면과 `계속하기` 의 최종 축자는 착수 시 `10_적용전/업로드_계보_260905_rev2_이태헌.html` 에서 그대로 뜬다. **개발 세션이 새로 짓지 않는다.** 못 뜨면 `[미상]` 으로 멈춘다.
- 손댐 판정 추가분 2건 — 담은 **프로젝트 건수** · **대표 그림 교체 여부**. 나머지는 PRD-14 그대로(자동 채움값 `Lv2`·`연구실 구성원 전체`·확장자·용량은 세지 않는다).
- 배경 클릭 — 업로드 모달·확장보기 오버레이의 어두운 배경을 누르면 닫히고 **닫기 확인을 그대로 탄다.** 모달 내부 클릭은 닫지 않는다. 함께 받는 것 = PRD-39 ⑭ Esc 우선순위(확장보기 → 찾기 → 계보 수정 → 닫기 확인 → 업로드).
- 좁은 게이트 — `frontend-typecheck` · `frontend-test`

### ⑤ WU-A3R ＋ WU-A4R — 편집 중 다운로드 숨김·칩 재동기 ＋ `좌표계 (선택)` (PRD-22 · PRD-28 · 크기 S · 선행 A12R)

- PRD 자리 — `PRD-260905-적용전기획.md:573`(PRD-22) · `:693`(PRD-28)
- WU-A3R 각주 2 — ⑴ **편집 중에는 다운로드가 숨고 `취소`/`저장` 이 그 자리에 온다.** ⑵ **저장 뒤 헤더 칩과 공개 범위 설명이 같은 값으로 다시 그려진다.**
- WU-A4R — 등록 화면 좌표계 칸 보조 라벨을 `좌표계 (선택)` 로 한다(III-B ⓐ · 코드가 이미 `변수 (선택)`·`기간 시작 (선택)` 패턴을 쓴다).
- **R-B 가 더하는 필드(분류·유형·가공 단계·변수 표·공개 범위·관측 간격·기간 최소 단위·Lv0 2칸)는 그리지 않는다.** `topic` 은 읽기 전용 유지.
- 좁은 게이트 — `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach`

### 이 라운드에 없는 것 (R-B `WU-B3` 이관)

- WU-A6 기간 달력 팝오버(판정-2 ⓑ · 판정 무변 · 담는 WU 만 이동) · PRD-39 ⑤ 확장보기 오버레이(M) · 등록 3단계 재편 · 모달 2장면 구조 · 종료 비움 조립(PRD-40).
- 계약 개정 · 스키마 · 마이그레이션 전부(M-1~M-5 · M-8 · M-10).

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 레인 — WU 하나에 워크트리 하나 · 직렬

- 레인 이름 = `p3-toast-copy`(A13R) · `p3-rev2-build`(A12R) · `p3-project-table`(A7R) · `p3-close-copy`(A9R) · `p3-detail-edit2`(A3R ＋ A4R).
- 스폰 = `Agent(subagent_type: "lane-worker", isolation: "worktree")`. **병렬 0** — 5 WU 가 같은 업로드 화면 파일을 공유한다.
- 레인 첫 줄 = `git merge --ff-only integration/r-a2`. 끝나면 `integration/r-a2` 로 **ff-merge**, 그 뒤 워크트리·로컬/원격 브랜치 3종을 정리한다.

### ㉯ 착수 전 — 대장 등재가 먼저다

- 신규 id 규칙 = **기존 `done` 항목 id ＋ 접미 `R`**(rev2 증분). `done` 항목을 다시 열지 않는다. 각 항목은 `depends_on` 으로 부모를 잇고 `sources` 에 이 파일과 PRD id 를 적는다.
- 이 라운드 6건은 이미 `dev-package/work-items.yaml` 에 `status: open` 으로 서 있다 — 착수 시 그 항목의 status 를 `in_progress` 로 바꾸고 `evidence` 에 세션 노트 경로를 적는다.
- 판정 = `bash gates/run.sh work-item-consistency` green.

### ㉰ 계약 동결 해제 — **쓰지 않는다**

⛔ 이 라운드의 6건은 `contracts/` 를 건드리지 않는다. 없는 열쇠가 필요하다고 판단되면 **고치지 말고 보고한다** — R-B 의 몫이다.

### ㉱ 결정 번호 〈N〉 — 예약하지 않는다

```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전에 다시 잰다
```

착수 시점 참고값 = **〈371〉**(2026-09-06 실측 · 근거 아님). **병합 직전 `origin/main` 최대 ＋ 1.** H5 가 그 값을 판정한다.
`PLAN-SoT §9` 행에는 **`intent:`·`spec:` 두 필드를 함께 적는다**(`〈369〉`-㉱ · `renumber-decisions.sh` 가 실존 파일인지 대조한다).

```
| 〈N〉 | **R-A′ rev2 증분 5 WU — 공통 토스트 21행 · PRD-39 잔여 ＋ HUD · 연관 한 표 ＋ 중복 검사 · 닫기 문면 3종 · 상세 편집 각주** | **집행 (2026-MM-DD · 통합 `integration/r-a2` · 병합 `<sha>` · 계약 개정 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = 해당 없음(계약 미개방) ②값 = 없음 ③근거 = PRD-14·22·23·28·32·34·39·42·43·44 ④`contract-breaking` 출력 = `<축자 · 변경 0 확인>` ⑤소비자 = 해당 없음 ⑥마이그레이션 = 0건 ⑦승인 = 불요 ⑧이번에 세지 않은 축 = A6 달력 팝오버·PRD-39 ⑤(WU-B3) `[미측정]` · intent: `dev-package/intent/2026-09-06-r-a2.md` · spec: `dev-package/prd/specs/R-A2.md` |
```

### ㉲ 게이트 — 작업 중엔 단독, 라운드 끝엔 전수 1회

```bash
# 레인 안 (단독 게이트만 하나씩 · 배출처를 준다)
COLAB_GATE_REPORT_DIR=dev-package/reports/R-A2/<레인> bash gates/run.sh <좁은 게이트>
# 라운드 끝 (다른 레인 정지 상태 · 한 워크트리에 한 벌)
bash gates/run.sh all -j 4
```

- 판정 = **한 번의 실행으로 red(판정) 0 ＋ red(준비) 0.** 두 실행에 걸친 계수는 판정이 아니다.
- 레인 종료 검사(H7) — `gate-summary.json` 존재 ＋ `counts.red_판정 == 0` ＋ `commit`/`tree` 대조. **마지막 커밋 뒤에 게이트를 한 번 더 돌린다.**
- ⛔ 게이트를 끄거나 검사 대상을 줄이지 않는다. **구현 전 red 를 눈으로 확인한다.**

### ㉳ 커밋 문면

```
FE R-A′ <WU 제목> (WU-A__R)

- <바뀐 자리 1~3줄 · 문면 축자는 원문에서 떴다는 사실 포함>
- 계약 0 · 스키마 0 · 마이그레이션 0
- RED 선실측 → GREEN: <시험 파일>:<건수>
```

### ㉴ 금지

- ⛔ `main` 직접 push · ⛔ `contracts/` 수정 · ⛔ 마이그레이션 추가 · ⛔ staging DB 직접 쓰기.
- ⛔ 존치 6종 제거(컴포넌트·훅·서버 경로·회귀 시험) · ⛔ HUD 로 값 조회 대체.
- ⛔ PRD-34 문면을 개발 세션이 작성 · ⛔ PRD-42 빈 이름 문면 수정 · ⛔ PRD-32 기존 행 수정·분할.
- ⛔ A6 달력 팝오버·확장보기 오버레이 착수(WU-B3) · ⛔ `40 COLAB-기획/` 문서 수정 · ⛔ 문서·주석에 절대경로.
- ⛔ 이 세션이 `03-HANDOFF.md` 본문을 직접 고치기 — §4 의 5줄을 오케스트레이터에 넘긴다.

---

## 4. 산출물 · 세션 노트 · HANDOFF 5줄

| 자리 | 무엇 |
|---|---|
| 레인 세션 노트 | `dev-package/sessions/<레인>-<YYYYMMDD>.md` — 실측 계수·red→green 근거 |
| 게이트 요약 | `dev-package/reports/R-A2/<레인>/gate-summary.json`(미추적 · 커밋하지 않는다) |
| 라운드 마감 | `dev-package/sessions/R-A2-ROUND-<YYYYMMDD>.md` |
| 원장 | `PLAN-SoT §9` 한 행(㉱ 문안 · `intent:`·`spec:` 포함) |
| 하네스 관찰 | `dev-package/reports/harness/2026-09-06/` — `lane-worker` 자율 블록 관찰(§0-5 잔여 #9) · 에이전트 4종 스폰 실측 |

**HANDOFF 5줄(오케스트레이터가 붙인다 · 값은 `PLAN-SoT §9` 와 세션 노트에)**

```
최종 갱신 2026-MM-DD — R-A′ 5 WU 병합 완료(통합 `integration/r-a2` → `main` ff 한 줄 · 등재 〈N〉)
게이트 = 전수 `all -j 4` 한 번의 실행 red(판정) 0 ＋ red(준비) 0
계약 0 · 스키마 0 · 마이그레이션 0 — 배포 창 8-b 와 병행, 서로 막지 않는다
근거 = `dev-package/sessions/R-A2-ROUND-<YYYYMMDD>.md` · spec `dev-package/prd/specs/R-A2.md`
다음 = R-B 착수(`integration/r-b` · 기점 = `integration/r-a2` tip · 계약 해제 1회차 필요)
```

---

## 5. 완료 판정

| 단계 | 무엇을 | 합격선 |
|---|---|---|
| WU 착수 전 | 대장 등재·상태 전이 | `bash gates/run.sh work-item-consistency` green |
| 구현 전 | 실패 시험 | **red 를 눈으로 확인한다** |
| 구현 후 | §2 의 좁은 게이트 | 해당 게이트만 단독 green ＋ `gate-summary.json` 배출 |
| 레인 종료 | H7 | `counts.red_판정 == 0` ＋ `commit`/`tree` 대조 통과 |
| 레인 종료 | advisor ② | revision 체인 · 「main 과 동일」 금지 · **intent `원한 결과` 미달·초과 열거** |
| 라운드 끝 | 전 게이트 | `bash gates/run.sh all -j 4` · 한 번의 실행 · red(판정) 0 ＋ red(준비) 0 |
| 라운드 끝 | 병합 | `integration/r-a2` → `main` **ff 한 줄** ＋ 〈N〉 재실측 등재 ＋ `prd/README.md` 상태표 갱신 |
| 라운드 끝 | 환류 | `python3 dev-package/tools/planning-applied.py --sync` → `--sync --apply` → `bash gates/run.sh planning-freshness` |

| 라운드 끝 · 후속 | `main` 병합 뒤 `integration/w9-dev-deploy` | 〈372〉~〈375〉 **재실측**(이 라운드가 〈N〉 을 먹어 번호가 밀린다 · `renumber-decisions.sh`) ＋ `exec-bit` **선측**(실행비트 `100644` 역행 여부를 ff 전에 본다) |

- 라운드 완료는 **위 8행 전부**다. 부분 완료로 WU 를 닫지 않는다.
- 병합 트리가 이미 판정된 트리와 같으면 `main` 전수를 다시 돌리지 않는다 — 트리 해시로 갈음한다(`〈333〉` 선례).
