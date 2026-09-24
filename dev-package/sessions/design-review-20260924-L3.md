# design-review 20260924 — L3 (upload / lineage / project / lab / members / approval, STATIC only)

Tree: dc05531c (develop 7acd0fce + css_audit). Mode = AUDIT. CSS/TSX 0건 수정.
Files: frontend/src/components/upload/**, components/lineage/**(lineage.css·lineageGraph.css·TSX), components/project/**, components/lab/**, components/members/**, components/approval/**
Axes: p3 11-item baseline · AA 4.5:1(light/dark) · font>=13px · undefined token · neg margin · card shadow(popover ok) · border 2-layer · container-owned spacing · local-token ⓐ/ⓑ

## 1. 판정표

| # | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|
| 1 | 정적 | 카드 그림자 (7파일 전수) | 없음 | `approval.css:4`·`lab.css:42`·`lineage.css:299,343`·`project.css:270,345,592`·`upload.css:654` 모두 `box-shadow: none` 명시. `upload.css:486` `.dr-pop`(달력 팝오버) `var(--shadow-lg)`은 팝오버 허용 대상. `upload.css:467` `.dr-field[aria-expanded]` `0 0 0 3px …-100`은 포커스 링이지 카드 그림자가 아니다 | — |
| 2 | 정적 | 13px 미만 글자 | 없음 | css_audit 7파일 전 파일 `<13px` 열 0 | — |
| 3 | 정적 | 음수 여백 | 없음 | css_audit 7파일 전 파일 `neg margin` 열 0. `margin:` 리터럴 수동 재확인(`grep -n "margin.*-[0-9]"`)에서도 실제 음수 여백 0건(매치는 `--space-*` 변수 이름 오탐) | — |
| 4 | 정적 | 미정의 토큰 | 없음 | css_audit 7파일 전 파일 `undefined token` 열 0 | — |
| 5 | 정적 | 파일 내 토큰 정의(ⓐ/ⓑ) | 없음 | css_audit 7파일 전 파일 `local token def` 열 0. `--[a-zA-Z]` 정의 재검색 0건 — ⓐ/ⓑ 판단 대상 자체가 없다 | — |
| 6 | 정적 | `lineageGraph.css` 계보 그래프 라벨 13px / 여백 소유 / 죽은 스타일(p3 ⑦⑧⑩⑪ 잔존분) | 없음 | 파일 전체 재확인 — 13px 미만 0건(전부 `13px` 이상), `margin-top:34px` 자식 소유 규칙은 컨테이너(`detail.css` `.dt-secs` gap)로 이관됐다는 주석(`:13-14`)과 실제로 자식 margin-top 선언 0건, 미정의 토큰(`--color-accent-*` 등) 0건 — WU-C11(`:8-12`)이 `detail.css :root` 로 토큰 선언을 옮겼다 | — |
| 7 | Ted 판정 | ⑦-2 `.lin .chip--warning` 색 | 변경 | `lineage.css`에는 `.lin .chip--warning` 전용 규칙이 없다(`.lin .chip`은 폭·패딩만, `:231`). 전역 `.chip--warning`(`primitives.css:66`) 이 `background: var(--color-warning-50); color: var(--color-warning-600);`를 이미 선언한다 — docs `⑦-2`가 적은 「선언이 없어 기본 모양」과 현재 렌더가 다르다. `docs/design-system.md` 갱신 필요(코드는 이미 값을 가짐) | Ted 판정 |
| 8 | Ted 판정 | ⑦-2 `.pcard` 초점 간격 2px | 잔존 | `project.css:119-121` `.pcard:focus-visible { outline: 2px solid var(--color-primary-600); }` — `outline-offset` 선언 없음. docs가 적은 「선언이 없어 기본 모양」과 일치, 아직 미해결 | Ted 판정 |
| 9 | Ted 판정 | ⑦-8 `lineage.css` 안내 줄 색(`.lin-over-why`·`.lin-unknown-why` 등) | 잔존 | `lineage.css:152-166` 주석은 「안내 줄 `#5b6472` on `#f7f8fa` = 5.63:1」이라 적지만, 실제 `.lin-over-why`(`:227`)·`.lin-unknown-why`(`:269`)는 `color: var(--color-warning-600)`(주황, `#a85400`) 렌더다. `#5b6472`는 `--color-text-muted`(`tokens.css:68` `#565c63`)와도 정확히 일치하지 않는 구값 — 주석과 렌더 둘 다 낡았을 가능성. docs 선택지(회색 토큰으로 / 주석을 렌더에 맞춤)대로 Ted 판정 필요 | Ted 판정 |
| 10 | 정적 | 접근성 대비(대표 표본, 손계산) | 없음 | `--color-danger #a3222b` on 흰 배경(`.ar-error`·`.labinfo-error`) light **7.45:1**, dark `--color-danger #ffadb6` on `--color-surface #1a222c` **9.10:1**. `--color-warning-600 #a85400` on 흰 배경(`.pj-ds .lin-none`) **5.34:1**. `lineage.css` 자체 주석의 `.lin-conflict` 계열 5.00:1(사유 문구)·2.91:1(비활성 컨트롤·4.5 대상 아님, `:157-165` 설계 의도)도 WCAG 상대휘도로 재계산해 일치 확인. css_audit `contrast<4.5` 열 7파일 전부 0(같은 규칙 안 색쌍) | — |
| 11 | 정적 | 보더 2층 토큰 분리 | 없음 | `upload.css`·`project.css`·`members.css`·`lab.css`·`lineageGraph.css`의 `border` 선언 재검토 — 컨테이너 외곽선과 내부 구분선이 같은 토큰을 역전해 쓰는 중첩 쌍을 발견하지 못했다(단일 보더 컴포넌트가 대부분). `20260905` 판정 9의 결함 자리(`detail.css`·`catalog.css`)는 이 레인 파일 밖 | — |
| 12 | 실화면 | apple-design 축(`:active`·모션·reduced-motion) | — | 이번 레인 축 아님(L4a/L4b) | 담당 외 |

## 2. 이월 재판정 (`design-review-20260912.md` → `findings.md` D-rows, 이 레인 파일)

| 이전 id | 원문 | 현재 판정 | 근거 |
|---|---|---|---|
| D06 | 프로젝트 생성 모바일 날짜 입력 잘림(`project.css:351,376,417`) | [미상] | 정적으로 폭 계산 불가 — 실화면 계측 필요(라이브 스택 다운, 이번 회차 확인 못함). 인용 행 번호는 파일이 늘어나 현재와 다르므로 정적 재확인은 불가 | 실화면 계측 |
| D07 | 대표 그림 파일 선택기 스타일 적용 조건 불일치(`upload.css:400`) | [미상] | `RepresentativeImageSection.tsx`는 이 레인 파일(`components/upload/**`) 밖 TSX다. `upload.css` 쪽 `.thumbrow` 정의는 여전히 존재하나 조건 매칭 재현은 실화면 필요 | 실화면 계측 |
| D09 | 프로젝트 모달이 GNB 아래 표시(z-index) | 해소 | `project.css:333` `.pj-modal-back { z-index: 200 }` > `shell.css:106` GNB `z-index: 100`. 역전이 정정됐다 | — |
| D10 | 모달 키보드 포커스가 배경으로 빠짐(`ProjectFormModal.tsx`) | [미상] | 코드 레벨 포커스 트랩 로직은 TSX 검사가 필요해 정적 CSS 감사 밖 — 이번 레인은 CSS 축만 확인했다. 재판정하려면 TSX 포커스 관리 로직 확인이 별도로 필요 | 실화면 계측 |
| D11 | 13px 미만 다수(`project.css`·`lineage.css` 포함) | 해소 | 이 레인 7파일 css_audit `<13px` 열 전부 0(§1 행2) | — |
| D12 | 상태/보조 글자 대비 미달(`project.css:528` 구행) | 해소 | 인용 행은 현재 `.pj-closebody`로 옮겨져 있어 원 대상과 다르다. §1 행10 손계산 대표 표본에서 이 레인 파일 내 대비 미달 0건 재확인 | — |
| D13 | 승인 UI 개별 스타일 누락(`ar-*`·`vc-*`·`modal-act`·`dh-more`·`btn-danger`) | 해소 | 현재 `approval.css`(19줄 전체)에 `.ar-pending`·`.ar-reason`·`.vc-reason`·`.ar-error`·`.modal-act`·`.dh-more`·`.dh-menu`·`.approval-dialog .btn-danger` 전부 정의돼 있다 | — |
| D14 | 업로드 미리보기·빈 상태 스타일 누락(`mapbar`·`mt`·`mapempty`·`err`·`pj-empty`·`pd-closedbar`·`pd-linkempty`) | 변경 | `upload.css:627-631` `.mapbar`·`.mt`·`.mapempty` 정의됨. `project.css:568` `.pj-empty` 정의됨. `pd-closedbar`·`pd-linkempty`는 여전히 미정의이나 소비처(`ProjectDetailPage.tsx`)가 `frontend/src/routes/`에 있어 이 레인 파일(`components/project/**`) 밖 — 레인 경계 밖 잔존으로 별도 표기만 한다 | Ted 판정(범위 조정) |
| D17 | 전역 control/card/modal 이름 중복(`upload.css`·`members.css`·`project.css` 등) | 잔존 | 구조 설계 후보로 D-row 자체가 「모든 화면 결함으로 세지 않는다」고 명시 — `docs/design-system.md ⑦-12`(별 계열 이름 합치기) 판정 대기와 같은 항목. 재판정 대상 아님, 그대로 계류 | Ted 판정(⑦-12로 이관) |
| D19 | reduced-motion 분기 없이 셸 transition 유지 — 업로드는 분기 3개 보유 | 담당 외 | 모션 축은 L4a/L4b. `upload.css`는 이미 `reduced-motion` 분기 3곳 보유(원문에도 명시)만 재확인 | 담당 외 |
| D20 | 카드 그림자·음수 여백 잔존(`project.css:243,436`·`members.css:5`) | 해소 | 인용 행은 파일 구조 변경으로 현재 내용과 다르다. §1 행1(카드 그림자)·행3(음수 여백) 전수 재확인에서 이 레인 7파일 모두 0건 | — |
| D22 | 멤버 권한표·승인 취소·잠긴 데이터 요청 최종 외형 | [미상] | 권한별 실화면 계측 필요 — 이번 회차도 라이브 스택 다운으로 확인 못함 | 실화면 계측 |
| D23 | 업로드 처리·오류·등록 상태 전수 외형 | [미상] | 데이터 상태별 실화면 계측 필요 — 이번 회차도 확인 못함 | 실화면 계측 |

## 3. 소계

- 있음: 0 · 없음: 8(§1 행1-6,10,11) · [미상]: 1(§1 행12는 담당 외로 미상 아님) · 이월 [미상] 4건(D06·D07·D10·D22·D23 중 실화면 5건 — D10 포함 시 5건)
- Ted 판정: 4건(§1 행7·8·9, D14 범위조정 1) · 즉시 수정 후보: 0건
- 이월: 해소 5건(D09·D11·D12·D13·D20) · 변경 1건(D14) · 잔존 1건(D17, 담당외 이관) · [미상] 5건(D06·D07·D10·D22·D23)

## 4. Ted 판정 후보

- **`.lin .chip--warning` 색**(§1-7): 현재 코드는 이미 `--color-warning-600` 색을 렌더한다. ⓐ `docs/design-system.md ⑦-2` 행을 「해소」로 갱신(문서만 수정, 코드 무변경) / ⓑ 그대로 판정 대기 유지(문서 오차를 별건으로 취급). **권고 ⓐ** — 코드가 이미 값을 가지므로 문서만 현재 렌더에 맞춘다.
- **`.pcard` 초점 간격 2px**(§1-8): ⓐ `.pcard:focus-visible`에 `outline-offset: 2px` 추가(시각 변경 — outline이 카드 밖으로 2px 떨어져 보임) / ⓑ 그대로(현재도 `outline: 2px solid`가 이미 보이는 상태라 시급하지 않음). **권고 ⓑ** — outline 자체는 이미 있어 접근성 결함은 아니고, 간격 추가는 순수 미관 판단.
- **`lineage.css` 안내 줄 주석-렌더 불일치**(§1-9): ⓐ 렌더대로 주황(`--color-warning-600`)을 유지하고 주석 문구를 수정(문서·주석만 변경, 코드 무변경) / ⓑ 주석이 뜻한 회색 토큰(`--color-text-muted`)으로 실제 렌더를 바꾼다(대비값 재계산 필요 — 위 경고 문맥과의 시각 일관성이 깨질 수 있다). **권고 ⓐ** — 현재 주황 렌더가 「확인 필요」 경고 의미와 시각적으로 일치하고 대비도 5.00:1로 이미 합격이다.
- **D14 `pd-closedbar`/`pd-linkempty` 미정의**: `components/project/**` 밖 `frontend/src/routes/ProjectDetailPage.tsx`가 소비한다. 이 레인 분할 범위(`components/project/**`)를 벗어나 있어 L2 또는 별도 레인이 재확인해야 한다.

## 5. css_audit 오탐

- (없음) — 이 레인 파일 7종의 모든 행을 소스에서 재확인했고, 도구가 보고한 값(카드 그림자 `none` 계열)이 실제와 일치했다. 오탐 0건.

## 6. 이번에 세지 않은 축

- apple-design 인터랙션 축(`:active` 피드백·`transition` 중단 가능성·`reduced-motion` 분기·`letter-spacing`·`backdrop-filter`) — L4a/L4b 담당.
- 실화면 필요 항목 5건(D06·D07·D10·D22·D23) — 라이브 스택 다운으로 이번 회차 미계측.
- `pd-closedbar`/`pd-linkempty`(§4 D14) — 소비 TSX가 이 레인 파일 범위(`components/project/**`) 밖.
