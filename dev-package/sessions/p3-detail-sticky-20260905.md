# p3-detail-sticky — WU-A8 · 상세 구역 메뉴 sticky ＋ 활성 표시 (PRD-24 · 미결-9 ⓑ)

- 레인 `p3-detail-sticky` · 기점 `origin/integration/r-a` = `947bf1f` · 계약 0 · 마이그레이션 0 · staging 접촉 0.
- 범위는 **프론트 한 겹**이다. `contracts/`·서버·`components/upload/` 는 열지 않았다.

## 1. 무엇이 바뀌었나

| 파일 | 자리 | 내용 |
|---|---|---|
| `frontend/src/components/detail/SectionMenu.tsx` | 신설 96행 | 구역 메뉴. `DETAIL_SECTIONS` 3칸(계보 `#sec-lineage` · 미리보기 `#sec-preview` · 활용/접근 `#sec-usage`) · `IntersectionObserver` 스크롤 스파이 · 관측기가 없는 환경은 스크롤 위치 폴백 |
| `frontend/src/routes/DatasetDetailPage.tsx` | 16 · 185 | 메뉴를 본문 맨 위에 세운다(잠긴 본문에는 서지 않는다 — 가리킬 구역이 없다) |
| `frontend/src/routes/DatasetDetailPage.tsx` | 233 | 미리보기 앵커 `<div id="sec-preview">` — **감싸는 자리**에 둬서 `components/datasetpreview/` 를 건드리지 않았다 |
| `frontend/src/components/detail/detail.css` | 157~ | `.dsec-menu { position: sticky; top: 0; z-index: 5 }` ＋ `.dsec-menu-i.is-active` |
| `frontend/test/detail-section-menu.test.tsx` | 신설 189행 | 시험 7건 |

### 판단 두 가지

1. **구역은 늦게 온다.** 계보는 제 op 로 따로 읽어 뒤늦게 자리를 세운다. 처음 한 번만 훑는 감시는
   그 구역을 영영 놓쳤다 — `MutationObserver` 로 새로 뜬 앵커를 이어 붙인다(`SectionMenu.tsx:44-56`).
2. **탭이 아니다.** 메뉴는 앵커 이동과 「지금 어디」 표시만 한다. 어느 코드 줄도 구역을 숨기지 않고
   `role="tab"`·`tabpanel` 을 만들지 않는다 — 정본 `Policy_데이터셋_상세 §1.3-1` 무개정(미결-9 ⓑ).

## 2. 시험 — red 선실측 → green

`frontend/test/detail-section-menu.test.tsx` **7건**. 구현을 stash 한 상태에서 먼저 쟀다.

- **RED** — `6 failed | 1 passed (7)`(통과 1건 = 「탭 역할을 만들지 않았다」 · 공백 상태에서 참)
- **GREEN** — `7 passed (7)` · 연속 3회 같은 결과(들쭉날쭉 없음)

수용 기준 대응 —
- ㉮ `활용/접근` 클릭 뒤에도 메뉴가 같은 노드로 문서에 남는다 ＋ `detail.css` 원문이 `position: sticky`·`top:` 를 선언한다(jsdom 은 계산값을 주지 않아 규칙 원문을 잰다 — `project-css-tokens.test.ts` 선례).
- ㉯ 미리보기 구역 진입 시 `미리보기` 가 `aria-current="true"`·`data-active="true"`, 활성은 언제나 한 칸.
- ㉰ 세 구역 순회하며 매번 세 앵커가 DOM 에 남고 `hidden`·`aria-hidden` 이 없음을 단언 — §1.3-1 준수 증명.

## 3. 게이트

| 게이트 | 결과 |
|---|---|
| `frontend-typecheck` | **green** — `tsc --noEmit` 오류 0건 (첫 회 red 2건 — `JSX.Element` 네임스페이스 · 리터럴 union 좁힘. 둘 다 고쳐 재측정) |
| `frontend-test` | **green** — 43 파일 · **648 통과 · 0 실패** |

`frontend-fixture-reach` 는 §5 가 WU-A3 에만 건 게이트라 돌리지 않았다. `all` 은 병합 직전 몫이다.
회귀 방어선 `rev1-keep-regression`·`detail-edit` 는 위 648 안에서 통과했다(재시도 0회).

## 4. PLAN-SoT §9 초안 (〈N〉 = 병합 직전 `origin/main` 최대 ＋ 1 · 착수 시점 실측 최대 = 〈334〉)

```
| 〈N〉 | **R-A-3 FE 계층 — 상세 수정 진입점 신설 · 구역 메뉴 sticky(미결-9 ⓑ 최종형) · 종료 조건 개정** | **집행 (2026-09-05 · 워크트리 `p3-detail-sticky` · 병합 `<sha>` · 계약 개정 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음 ③근거 = PRD-14·20·22·23·24 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **해당 없음** · `contract-breaking` 출력 = `<축자 · 변경 0 확인>` ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요(㉮ 밖 · 계약 미접촉) ⑧이번에 세지 않은 축 = 대표 그림 저장 경로(WU-C2 별건) `[미측정]` |
```

## 5. 남는 것

- 기점 `947bf1f` 이후 `origin/integration/r-a` 가 **4 커밋 앞서 있다**(다른 레인 병합분). 이 레인은
  그 위에 얹히지 않았다 — 병합은 오케스트레이터의 ff-merge 몫이고, 겹치는 파일은 없다.
- `[미상]` 없음.
