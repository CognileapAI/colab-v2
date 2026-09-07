# Gate ② 수용 검토 — WU-B11 (p3-design-fix · 0a17d2e..8db3deb)

## 체크리스트
- ① CSS-only: `git diff --stat` = catalog/detail/lineageGraph/upload/shell `.css` 5 + `frontend/test/design-fix-20260908.test.ts` + 세션 노트 + `work-items.yaml`(status·evidence 2행). TSX·서버·`contracts/`·`tokens.css` 0. ✓
- ② 「main 과 동일」: 보고서·세션 노트에 해당 서술 0건. ✓
- ③ intent 대조 (R-B-4 §2-A 수용 기준 7 ↔ 시험 17):
  | 기준 | 시험 | 실측 |
  |---|---|---|
  | ⑥ 카드 그림자 0·팝오버 유지 | ㈎ 2 | `.catalog-page .card` box-shadow 0 · `.colmenu` `--shadow-lg` 유지 ✓ |
  | ⑦ 13px 미만 0건 | ㈏ 1 | grep `font-size:.*px` 최소 13 · `font:` 축약 0건 ✓ |
  | ⑧ 캡션 7곳 ≥13 | ㈐ 7 | 6곳 승격 + `.vizerr,.warn` 13 유지 ✓ · 「레이아웃 무붕괴」는 정적 추론만(jsdom 미계측) |
  | ⑨ 토큰 상이·바깥≥안쪽 | ㈑ 2 | `--color-border-strong` #dfe3e8 (L 낮음) vs `--color-border` #e8ecf2 → 컨테이너 진함 ✓ · 카탈로그 바깥=안쪽 동률(기준 문면 「같다」 허용) ✓ |
  | ⑩ 음수 2건 0·컨테이너 소유 | ㈒ 3 | 지목 2건 0 ✓ · 컨테이너 이관 **부분**(아래 미달) |
  | ⑪ display 0·미정의 토큰 0 | ㈓ 2 | 0·0 ✓ · 정의처 = `tokens.css` ∪ `detail.css :root`(`--color-gray-100`·`--color-primary-50/100` 은 detail.css 정의) |
  | FE 게이트 3 green | 기록 0670b0a | ✓ |

## For
- 판정표 「있음」 6건 전부 손댔고 「없음」 5·판정 대기 2·60건 일괄 승격·`.vizph` 무접촉 — 라운드 ⛔ 6항 준수.
- RED 15 → GREEN 17 선실측, 996 회귀 green, CSS 5파일·계약 0. 폐기 비용 > 잔여 수정 비용.
- ⑪ 액센트 치환은 목업 `:root` 레포 부재를 실측(find 0건)으로 뒷받침, 세션 노트에 근거 기재 — 기준 「둘 중 하나를 고르고 근거 기재」 충족.

## Against
- ⑩ 을 「닫혔다」로 보고했으나 라운드 §2-A 표가 지목한 `upload.css` 자식 `margin-top` 12곳 중 3곳(`:108·:113·:135`)만 이관. 잔여 9곳은 세션 노트 「하지 않은 것」에도 없다 — 판정된 범위의 누락을 보고에서 생략한 것이 핵심 결함. `CLAUDE.md §5` 「WU 부분 완료로 닫지 않는다」와 충돌.
- 「컨테이너 소유」 주석 2곳(`shell.css:57`·`upload.css:113`)이 실체보다 강함 — `.backrow` 는 여백을 받지 않았고 hover 상자만 비대칭이 됐다.

## Verdict
approve-with-changes — 항목별: ⑥⑦⑧⑨⑪ 승인 · ⑩ 은 「지목 음수 2건」만 승인, 컨테이너 이관은 이월 등재 없이는 수용 불가.

## Risks
1. `.up-card > .card-b` gap 12: `.up-note` 8→12 · `.toast`(`toast.css:12 margin:8px 0 0`) 8+12=20px — 실화면 간격 변화 미보고·미계측.
2. `.backlink` `padding-left 0`: 글자 위치 불변이나 hover/focus 테두리 좌 0/우 9 비대칭 — 키보드 포커스 시 노출.
3. `.aiflag` 중립 회색 + `.sp` primary-600: AI 표식이 `manflag`(primary-700 · primary-50)와 같은 색군 — 구분은 배경으로만 남음. 정책 「액센트 = AI 액션 전용」 복원은 목업 회수 뒤(기록됨).

## Missed
- ⑩ 잔여 `upload.css:147·150·159·166·168·170·191·234~237·243·251` — 범위 표 지목, 보고 부재.
- `detail.css:134 .dt-gridact margin:-8px` — `BasicInfoGrid` 직후 형제, 같은 컨테이너에서 lane 이 `:has(+ .filelist)` 규칙을 신설한 60행 위. 「판정 없이 고치지 않는다」 방어 가능(A11·R-B-4 모두 미지목) → 판정 대기 3건째로 등재해야 방어가 성립.
- `.dsec` 보류 판정: 정당 — 부모 `div[data-locked]` 무클래스, `[data-locked]{display:flex;gap:34px}` 는 머리·기본정보 사이에도 34px 삽입(B3·B10 구조 변경). 이월 경로 = `LockedContent.tsx` 에 클래스 부여(TSX WU).
- `lineageGraph.css:27` 주석 「코랄은 이 화면에서 계보의 AI 표식에만 쓴다」 — 코랄 0건이라 거짓.
- A11 ⑪ 표제 「미사용 규칙 4」 — R-B-4 범위 표·수용 기준 어디에도 열거 없음(라운드 파일 결함, 레인 책임 아님). 근거 필요 = A11 판정표 ⑪ 행의 「미사용 규칙 4」 실체.
- `.infogrid:has(+ .filelist)` — 로딩 중 형제가 무클래스 `div[data-testid=file-list-loading]` 이라 그 순간만 24px. 무시 가능, 기재.

## Fixes
- [병합 전 필수] 세션 노트 「하지 않은 것」＋ 〈N〉 ⑧축에 추가: ⑩ 컨테이너 이관 잔여 = `upload.css` 9곳 + `lineageGraph.css:7 .dsec`(TSX 필요) → 이월 항목(대장 신규 또는 R-C 후보) · `detail.css:134 .dt-gridact -8px` = 판정 대기 3건째. 이 등재 없이 `status: done` 금지.
- [병합 전 필수 · 택1] 위 등재 대신 `upload.css` 9곳 중 부모가 클래스 있는 자리는 이관 집행 + 시험 추가(RED 선실측). 부모 실체 미확인 → 집행 시 PreviewPanel/RegisterArea 컨테이너 클래스 증거 첨부.
- [선택] `shell.css:57` 주석을 사실로 교정(「음수 상쇄 제거 · hover 상자 좌측 padding 0」) · `lineageGraph.css:27` 주석 삭제 또는 「액센트 복원 전 중립」으로 교정.
- [선택] 세션 노트 ⑩ 행에 부수 간격 변화 기재: `.up-note` 8→12 · `.toast` 20px.
- [선택] `.colmenu`·`.tbl th` 등 `block()` indexOf 첫 일치 의존 — 선택자 앞에 `\n` 경계 추가로 오탐 방지.
