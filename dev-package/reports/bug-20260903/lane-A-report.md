# Lane A 검증 보고 — 계보 그래프 빈 칸·고아 화살표 제거 (버그 3·5·7)

## 위치
- 브랜치: `worktree-agent-afd5e5a90f1790ac1`
- 워크트리: `.claude/worktrees/agent-afd5e5a90f1790ac1`
- 커밋: `4d01d28c38eeee775d194037454f8ef5de76d392`
- `git status --porcelain` 결과 없음 — 워크트리 클린, 미커밋 변경 없음

## 근본 원인
가로축이 「노드 종류 = 고정 4칸」을 전제해, 종류가 없는 칸도 DOM·폭(178px)을 그대로 들고 있었다.
레일 화살표도 인접 칸에 노드가 있는지와 무관하게 항상 출력됐다. 그 결과:
- 버그 5: 루트 Lv0 왼쪽에 빈 칸 2개 + 화살표 2개
- 버그 3: 잎 Lv1 오른쪽에 화살표 1개(갈 곳 없음)
- 버그 7: 원천 옆에 「→ 빈 칸 →」

## 변경 파일 (+179/−36, 3파일)
- `frontend/src/components/lineage/LineageSection.tsx` (+56/−31 상당)
  - `shown = cols.filter(nodes.length > 0)` 로 노드 있는 칸만 렌더. `data-col` 값(칸 번호)은 유지해 §8 축 순서 보존
  - 화살표는 **선 칸과 선 칸 사이**에만 배치. 건너뛴 레일의 가공 방식 라벨은 그 한 칸에 모아 실어 값 보존
  - 원천은 대응 edge가 없어(core-api) 라벨 없는 화살표로 남김 — 의도된 동작으로 명시, 버그 아님
- `frontend/src/components/lineage/lineageGraph.css` (+2/−1)
  - `.lin-axis`: `min-width: 820px` (4칸 전제 고정값) → `width: max-content; min-width: 100%;` 로 변경. 칸 수 가변에 대응
- `frontend/test/lineage-graph.test.tsx` (+133/−0 상당)
  - 기존 4칸 고정 단언(`cols.length === 4`)을 「칸 수는 0보다 크고, `data-col`은 오름차순·중복 없음」으로 완화 (§8은 순서만 규정, 빈칸 유지는 미규정)
  - 신규 픽스처 3종: 루트+자식(버그5), 잎+부모(버그3), 원천+루트+자식(버그7)
  - 각 픽스처에서 렌더된 칸 번호(`renderedCols`)와 화살표 개수(`arrowCount`)를 검증
    - 루트: `[2,3]`, 화살표 1개
    - 잎: `[1,2]`, 화살표 1개
    - 원천: `[0,2,3]`, 화살표 2개, 첫 레일엔 라벨 없이 `→`만
  - 공통 불변식 테스트: 렌더된 모든 칸은 노드 ≥1, 화살표 개수 = 렌더 칸 수 − 1, 칸 번호 오름차순

## 테스트 결과
- `npx vitest run` (frontend): **Test Files 36 passed (36) / Tests 575 passed (575)**, 실패 없음
- 실행 로그에 `Not implemented: navigation to another Document` 경고 3건 — jsdom의 통상적 미구현 경고, 테스트 실패 아님

## 타입체크
- `npm run typecheck` (`tsc --noEmit`): 출력 없음, 종료 클린 — 통과

## 보류 사항
- 원천→루트 edge를 core-api가 아직 내려주지 않는 문제는 이번 커밋의 스코프 밖. 프론트는 이를 「라벨 없는 화살표」로 명시적으로 수용했고, 코드 주석(`routes/lineage.py` 참조)에 그 사실을 남겼다 — 별도 TODO/FIXME 마커는 없음, 백엔드 후속 작업 여부는 이 커밋만으로는 판단 불가
