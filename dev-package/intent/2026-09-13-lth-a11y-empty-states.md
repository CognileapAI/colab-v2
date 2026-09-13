# Intent: 키보드 경로·제목 단계·빈 상태 문면 5건을 닫는다
메타 — 발의자: 이태헌 · 작성 2026-09-13 · 승인 미승인

## 문제
- 프로젝트 카드를 마우스로는 열 수 있고 키보드로는 열 수 없다(`D-2`).
- `/lab-settings` 에 그 화면의 대표 제목이 없고 3단계 제목부터 시작한다(`D-6`).
- 데이터셋이 0개인 프로젝트 상세의 소속 데이터셋 표가 제목 행만 보이고 안내가 없다(`I-6`).
- 「할 일 함」을 검증자가 띄어쓰기 오류로 읽었다(`D-7`).
- 로그인 실패 시 이메일까지 지워진다는 관측이 있다(`I-7`).

## 원한 결과 (proposed outcome)
- 검증 문장 ⑴ 프로젝트 카드가 키보드 탭으로 초점을 받고 Enter 로 상세 화면이 열리며 초점 표시가 보인다.
- 검증 문장 ⑵ `/lab-settings` 의 제목 단계가 1단계에서 시작하고 탭 본체 제목이 2단계다.
- 검증 문장 ⑶ 소속 데이터셋이 0건이면 표 대신 안내 문면과 연결 방법이 보이고, 0행에 좌우 이동 안내가 출력되지 않는다.
- 검증 문장 ⑷ 「할 일 함」 표기가 계약·정본·화면에서 한 이름으로 유지되고 그 사실을 기획자에게 회신한다.
- 검증 문장 ⑸ 로그인 실패 후 이메일 칸의 값이 유지된다 — 현재 코드가 이미 그 상태이므로 브라우저 관측 1건으로 닫는다.

## 영향 범위
- 사용자 / 화면: `/projects` 카드·표 · `/datasets` 표 · 프로젝트 상세 표 · `/lab-settings` · (`D-6` 전체안 채택 시) `/lab` · 로그인 화면.
- 서비스 · 스키마 · 계약: `frontend/src/components/project/ProjectCards.tsx` · `project.css` · `frontend/src/routes/LabSettingsPage.tsx` · `frontend/src/components/lab/LabInfoPanel.tsx` · `frontend/src/components/members/MemberPermissionGrid.tsx` · `frontend/src/components/project/ProjectDatasetTable.tsx`. core-api·`contracts/`·`db/` 변경 0.
- 계약 파괴 여부: 아니오

## 제약
- 카드 안에 또 하나의 클릭 대상을 세우지 않는다는 기존 규칙이 있다 — `frontend/src/components/project/ProjectCards.tsx` 앵커 `data-testid="card-cta"` 주석 축자 「카드 전체가 이미 클릭 대상이라 **그 안에 또 하나의 클릭 대상을 세우지 않는다**」 ⟹ 카드 전체를 대화형으로 만드는 방향이 그 규칙과 정합한다.
- 같은 패턴이 4자리다 — `ProjectCards`(`<article … onClick>`) · `frontend/src/components/project/ProjectTable.tsx`(`<tr … onClick={() => props.onOpen(row.projectId)}>`) · `frontend/src/components/catalog/CatalogTable.tsx`(앵커 `className={`clk${…}`}` ＋ `onClick`) · `ProjectDatasetTable`.
- 포커스 CSS 가 없다 — `frontend/src/components/project/project.css` 의 `.pcard` 선택자는 `.pcard {`·`.pcard[data-closed='true'] {` 둘뿐이고 `:focus-visible` 규칙이 없다.
- 접근성 검사 게이트가 없다 — `gates/run.sh` 에 `a11y`·`accessib` 0건. `CLAUDE.md §3-3` 이 「검사가 게이트에 없으면 그 자체가 결함」을 말한다(이 intent 범위 밖 · 후보).
- 「할 일 함」은 기획 정본 용어다 — `contracts/seams/fe-core.yaml` 앵커 `summary: 받은 접근 요청 (할 일 함 그룹)` · `dev-package/DOMAINS.md` 앵커 `활동 기록 타임라인 · 할 일 함 집계` · `dev-package/PERMISSION-PRINCIPLES.md` 앵커 `P-16. 권한 훅은 최소 단위에 건다.` · `dev-package/PLAN-SoT.md` 앵커 `〈281〉`. 「할 일함」·「할일함」·「할 일 목록」은 레포 전역 0건.
- 코드를 기획에 맞추는 방향이 기본이다(`.claude/rules/colab-rules.md §7`) ⟹ 표기 변경은 기획 정본 개정이 선행한다.
- 빈 상태 문면 기존 패턴 = 「…없어요」 ＋ 다음 행동 한 줄 — `frontend/src/components/catalog/CatalogTable.tsx:140` 의 `조건에 맞는 데이터가 없어요. 조건을 하나 풀어 보세요.` · `frontend/src/components/dashboard/DataMapCard.tsx:91` · `frontend/src/components/dashboard/TodoInbox.tsx:81`(`확인할 계보가 없어요.`).

## 설계트리 (grill-me 결과)
- Q1 `D-2` 를 카드만 고칠 것인가 → A 판정 대상이다. 사용자가 보는 것 = 키보드만 쓰는 사용자가 ⓐ 카드 보기에서는 상세로 들어가고 표 보기에서는 못 들어간다 ⓑ 네 자리 모두 들어간다.
  - Q1a 두 갈래의 대가 → A ⓐ 카드만(**S** · 같은 결함이 표 3자리에 남는다) ⓑ 패턴 4자리 전체(**M** · 행 전체를 대화형으로 만드는 방식을 한 번 정해 네 자리에 같이 적용한다).
  - Q1b 권고 → A **ⓑ** — 방식을 한 번 정하는 비용이 같고, ⓐ 는 같은 피드백을 표 보기에서 다시 받는다.
- Q2 `D-6` 의 범위 → A 판정 대상이다. `/lab` 도 같은 상태다(`frontend/src/routes/LabPage.tsx` 에 `<h1` 0건 · 카드 제목이 h2). h1 을 두는 화면은 4곳뿐이다(기준 = `grep -rn "<h1" frontend/src/routes` — `DatasetsPage`·`ProjectsPage`·`ProjectDetailPage`·`SearchResultsPage`).
  - Q2a 두 갈래의 대가 → A ⓐ `/lab-settings` 한 화면만(파일 3 · **S** · `/lab` 은 같은 상태로 남음) ⓑ 모든 화면에 대표 제목 규약을 세운다(파일 10+ · **M** · 글자 크기가 바뀌지 않는지 확인이 따른다).
  - Q2b 권고 → A **ⓑ 로 규약을 정하고 이번 회차는 ⓐ 범위로 집행**. 나머지 화면은 같은 항목의 후속.
  - Q2c 목업 지정 여부 → A h3 가 목업 지정인지 `[미확인]` — 해소 = `40 COLAB-기획/10_적용전/` 의 S-07 목업에서 해당 제목 태그 확인(읽기 전용 경로).
- Q3 `I-6` 의 문면 → A 기존 패턴에 맞춘다. 후보 축자 = 「연결된 데이터셋이 없어요. 데이터셋 상세에서 이 프로젝트를 고르면 여기에 보여요.」 크기 **S** · 0행에서 표와 좌우 이동 안내를 함께 감춘다.
- Q4 `D-7` 은 오탈자인가 → A 아니다. 사용자에게 보이는 자리 2건이 전부 목업 축자이고(`frontend/src/components/dashboard/TodoInbox.tsx` 앵커 `<h2>할 일 함</h2>` · `frontend/src/components/members/MemberPermissionGrid.tsx` 앵커 `승인 위임을 켜면 그 연구원의 할 일 함에 접근 요청이 들어오고`) 같은 표기가 계약·도메인·권한 원칙·정본 v1.4 에 전부 쓰였다.
  - Q4a 두 갈래의 대가 → A ⓐ 유지(작업 0 · 한 이름으로 일치한 상태 유지 · 검증자에게 「정한 용어」로 회신) ⓑ 변경(기획 정본 개정 ＋ 목업 패키지 재생성 ＋ 계약 설명 2건 ＋ 화면 2곳을 한 회차에 함께 움직인다 · 안 맞으면 `planning-freshness` 가 red).
  - Q4b 권고 → A **ⓐ 유지 ＋ 기획자 회신**. 바꿀 이유가 생기면 기획 정본에서 먼저 정한다.
- Q5 `I-7` 은 재현되는가 → A 코드에서 재현되지 않는다. `frontend/src/auth/LoginPage.tsx` 앵커 `if (response?.status === 401) {` 안은 `setPassword('');` 하나이고 `setAccountName('')` 호출은 레포에 없다. 로그인 op 은 전역 401 처리에서 제외된다(`frontend/src/api/client.ts` 앵커 `if (response.status === 401 && !isPublicSessionOp(request.url)) {`).
  - Q5a 그러면 무엇을 하는가 → A 코드 변경 0. 기획자에게 관측 1건을 요청한다 — 실패 직후 ⑴ DevTools Network 의 `POST /sessions` 상태 코드 ⑵ `#accountName` 의 `value` ⑶ `performance.getEntriesByType('navigation').length` ⑷ 비밀번호 관리 도구를 끈 상태의 재시도 결과.

## 미해결 질문
- `D-2` 범위 — ⓐ 카드만(**S**) ⓑ 클릭 대상 패턴 4자리 전체(**M**). **권고 = ⓑ**.
- `D-6` 범위 — ⓐ `/lab-settings` 만(**S**) ⓑ 전 화면 대표 제목 규약(**M**). **권고 = ⓑ 규약 확정 ＋ 이번 회차 ⓐ 집행**.
- `I-6` 문면 확정 — 후보 「연결된 데이터셋이 없어요. 데이터셋 상세에서 이 프로젝트를 고르면 여기에 보여요.」 **권고 = 후보 채택**(기존 「…없어요 ＋ 다음 행동」 패턴과 일치). 연결 방법 문장의 실제 경로 축자 `[미확인]`.
- `D-7` — **권고 = 현 표기 유지 ＋ 기획자에게 「정한 용어」로 회신**.
- `I-7` — **권고 = 코드 미수정 ＋ 기획자 관측 1건 요청**(Q5a 의 4항목).
- 접근성 검사 게이트 신설 여부 — 조사 B·C 가 `gates/` 에 해당 검사 0건을 확인. **권고 = 새 대장 항목 후보로만 등재**(이 intent 범위 밖).
- `/lab` 의 h1 부재를 같은 항목으로 묶는지 `[미확인]` — `D-6` 범위 판정에 종속.

## 범위 밖 (명시 제외)
- 접근성 검사 게이트(axe 류) 신설 — 별 항목 후보.
- `CatalogTable` 의 조건 없는 0건 빈 상태 문면(`state.hasConditions` 일 때만 출력 · `I-6` 과 별 자리).
- 「할 일 함」 표기 변경 및 그에 따른 기획 정본 개정·목업 패키지 재생성.
- 카드·표의 레이아웃·정보 구성 변경 — 이번 회차는 키보드 경로와 초점 표시만.
- `I-3` 취소선 `Verified` 표기(별 판정 · 조사 C 소관).

## 확인
- 프론티어 공집합 확인: [미확인]
- Ted 확인 문장(원문 그대로): "[미승인 — 확인 문장 없음]"
- 재개봉 금지: 아니오

## 참조
- 기획 원본: 검증 피드백 원문 `dev-package/reports/issues/2026-09-13-lth-review-1-raw.md`(D-2 · D-6 · D-7 · I-6 · I-7)
- 조사: `dev-package/reports/issues/2026-09-13-lth-survey-C.md`(D-2 · I-6) · `dev-package/reports/issues/2026-09-13-lth-survey-B.md`(D-6 · D-7) · `dev-package/reports/issues/2026-09-13-lth-survey-A.md`(I-7)
- 대장 항목: 접근성 등재분은 대비 계열뿐 — `dev-package/work-items.yaml` 앵커 `대비 3건(1·3·7)이 접근성 합격선`(`WU-A11`·`WU-B11`)
- 결정: `PLAN-SoT §9 〈281〉`(「할 일 함」 3그룹 · `Policy_역할과_권한` v1.4) · 새 결정 번호 〈N〉 은 병합 시 기입
