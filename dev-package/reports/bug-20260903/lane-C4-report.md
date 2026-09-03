# 레인 L-C4 — 버그 15 (데이터셋 설명문 `／` 줄 나눔 · A안)

## 좌표

- 브랜치 — `worktree-agent-aa39e80c78496402e`
- 워크트리 — `.claude/worktrees/agent-aa39e80c78496402e`
- 커밋 — `02738e4` (`02738e47e0b7ec4e1a8cbb1d870a0d6a2cc42bfc`) · 기반 `56eac76`
- 푸시·병합 없음. `main` 무접촉. `dev-package/`·`infra/staging/manifest-s2.json` 무접촉.

## RED 확인 (구현 전)

```
FAIL test/detail-summary-split.test.tsx > `／` 3개면 이끔 문장 1 + 목록 항목 3 이다
  TestingLibraryElementError: Unable to find an element by: [data-testid="dh-sum-lead"]
FAIL test/detail-summary-split.test.tsx > 구분자와 그 둘레 공백은 화면에 남지 않는다
  AssertionError: expected '저해상도(2 km) 자료를 …' not to contain '／'
Tests  2 failed | 3 passed (5)
```

- 통과한 3건은 「종전 그대로」를 지키는 가드다 — `／` 없는 설명 · 빈 설명 · 검색 카드 한 줄.
  이 셋은 구현 전에도 green 이 정상이고, 구현이 그것을 깨지 않았음을 뒤에서 증명한다.

## 변경 (3파일 · +43/-1 ＋ 신규 시험)

| 파일 | 내용 |
|---|---|
| `frontend/src/components/detail/DetailHeader.tsx` | `SUMMARY_SEPARATOR = '／'` ＋ `summarySegments()`(split → trim → 빈 조각 제거). 조각 2개 이상일 때만 `.dh-sum` 안을 `<p class="dh-sum-lead">` ＋ `<ul class="dh-sum-list">` 로 그린다. 1개면 종전 표현 그대로 |
| `frontend/src/components/detail/detail.css` | `.dh-sum-lead`·`.dh-sum-list`·`li` 촘촘한 여백 3줄 |
| `frontend/test/detail-summary-split.test.tsx` | 신규 5건 |

- `.dh-sum` 껍데기와 `data-testid="dh-sum"` 은 유지 — 기존 `detail.test.tsx:63`·`:160` 의 `toHaveTextContent` 가 그대로 통과한다.
- 미접촉 확인 — `PreviewPanels.tsx`·`DatasetPreviewSection.tsx`·`LineageSection.tsx`·`project.css`·`shell.css`·`vite.config.ts` 전부 diff 0.
- 저장·검색 무접촉 — 시드·DB·계약·`SearchHitCard` 손대지 않음.

## GREEN

- `npm test` (`vitest run`) — **37 파일 / 575건 전건 통과** (종전 대비 시험 5건 증가, 실패 0)
- `npm run typecheck` (`tsc --noEmit`) — 출력 없음, 오류 0

> 워크트리에 `node_modules` 가 없어 공유 체크아웃의 것을 심링크로 빌려 돌렸고 **실행 후 심링크는 지웠다.**
> 공유 체크아웃은 읽기만 했다.

## 되돌리는 법

- `git revert 02738e4` **한 번**이면 끝난다. 커밋 하나에 코드·CSS·시험이 모두 들어 있고 다른 파일에 갈래가 없다.

## 판정 대기 (Ted)

- 정본 `Policy_데이터셋_상세 §8` 은 이 자리를 「③ **한 줄** 요약」으로 못 박고 있다(`DetailHeader.tsx:2` 축자).
  여러 줄로 펼치는 것이 정본 위반인지는 **Ted 확인 대기**다. 코드는 승인 전제로 넣되 되돌리기 1회로 설계했다.
- 암묵 규약 하나가 생겼다 — 「`／` 는 구분자다」를 코드가 안다. 본문에 `／` 를 쓴 설명이 나중에 들어오면 오분할한다.
  현재 사용자 입력은 `RegisterArea` 300자 한 줄이라 해당 사례가 없다.
