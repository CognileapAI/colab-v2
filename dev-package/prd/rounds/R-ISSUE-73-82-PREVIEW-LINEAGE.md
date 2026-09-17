> spec: dev-package/prd/specs/2026-09-16-issue-73-82-preview-lineage.md
# 미리보기 선택칸과 계보 선언 구현 계획
> **For agentic workers:** 한 체크아웃 한 쓰기 주체. 기존 미커밋 #80/#76을 보존한다.

**Goal:** 긴 선택값 넘침을 고치고 부모 연결 중 선언을 숨기며 실제 GRIB 그림 대응을 확인한다.
**Architecture:** 기존 공용 선택칸과 계보 표시 조건을 재사용한다.
**Tech Stack:** React/TypeScript/CSS, vitest, agent-browser, Python viz-render.
**Spec:** 위 출처 spec.

## Global Constraints
- 2026-09-16 사용자 교정: "긴이름 화면넘칠경우 텍스트박스 사이즈를 넓히는건 UI 정책에 맞지않음". 선택칸은 기존 180px 기준에서 남은 공간으로 늘어나지 않는다. 공간 부족 시에만 줄고, 긴 텍스트는 말줄임하며 전체 값 펼침은 유지한다. 이전 flex-grow:1 수용을 이 조건으로 개정한다.
- 새 의존성·마이그레이션·계약 재정의 없음. 커밋/push/배포 없음.
- 원본 선택 ID·수동 대표그림·실제 오류 안내 유지.
- 과거 결과를 이번 실측으로 쓰지 않는다. 미실행/준비 실패를 성공으로 세지 않는다.

## 상태와 의존
- [x] 사용자 승인 및 두 intent 기록.
- [x] spec/계획 작성.
- [x] advisor 계획 검토. 극역 값 혼입·좌표/배열/sidecar 정합·범위 밖 입력 시험 조건 반영.
- [x] 한 구현 레인에서 RED→GREEN. 프런트 45건, 지도 warp 11건 대상 시험 통과(최종 통합 게이트는 runtime).
- [ ] 실제 GRIB 원본/렌더 재현과 화면 조작.
- [ ] 수용 검토와 최종 관련 게이트.
- [ ] runtime에 결과·미달/초과·로컬 PR 요약 인계.
- 최종 게이트 이후 제품 문서를 수정하지 않고 해당 task runtime을 최종 상태 원본으로 쓴다.

## Task 1: 공용 선택칸과 선언 표시
**Files:** `frontend/src/components/preview/PreviewPickRow.tsx`, `preview.css`, `frontend/src/components/lineage/LineageStep.tsx`, 해당 기존 `frontend/test/*preview*`, `lineage-unknown-20260907.test.tsx`.
**Interfaces:** 기존 props/선택 이벤트/lineage payload 그대로.
- [ ] 선언 시험을 `expect(screen.queryByTestId('lin-unknown')).not.toBeInTheDocument()`처럼 실제 DOM 숨김 조건으로 개정하되 정확한 testid는 기존 시험에서 확인한다. 해제 후 상태복원과 payload 생략도 검증한다.
- [ ] 긴 GRIB label 전체 확인 경로와 선택 원본값 보존 시험을 추가하고 실패를 확인한다.
- [ ] 최소 표시 조건과 공용 CSS만 수정한다. `min-width: 0; max-width: 100%`와 라벨 비줄바꿈을 기존 레이아웃에 맞게 적용한다.
- [ ] 관련 시험 GREEN 후 전체 frontend-test/typecheck를 최종 합류 트리에서 실행한다.
- [ ] 이전 비활성 표시 판정의 개정 링크를 원문 보존 방식으로 추가한다.

## Task 2: 실제 데이터·브라우저
- [ ] 기존 실제 업로드/렌더 러너를 재사용하고 surface.grib 원본 hash/변수/시점을 고정한다.
- [ ] 수정 전후 실제 폭을 재고 업로드·확장·상세 3화면을 1440/390px에서 확인한다.
- [ ] 지도/대표그림을 각각 원본 값·좌표 및 같은 render 선택값과 대조한다. 투영 차이만으로 실패 판정하지 않는다.
- [ ] 확정 부모 연결→선언 숨김→해제→기존 체크 복원→재연결→저장/재조회까지 검증한다.
- [ ] 서버 결함이 확인되면 원인과 기존 계약 내 최소 수정/회귀시험을 계획에 추가한다. 단순히 잘못된 그림끼리 맞추지 않는다.

## Task 3: 수용·인계
- [x] 실제 브라우저 수정 전 `before-2`에서 긴 선택칸 넘침과 85×1024 지도/파란 띠 재현. 최초 `before`는 30초 분석 대기 부족으로 중단했으며 결함 판정 근거 아님.
- [x] `after-1`에서 선택칸 두 폭·확장보기·변수/팔레트 변경·수동그림 보존 확인. 지도 극지방 가는 투명줄을 추가 발견. 연결 확정 버튼을 누락한 시나리오도 교정했으며 이 회차 전체 통과 아님.
- [x] 극지방 빈 줄: 등간격 북→남/서→동 위경도 격자는 기존 rasterio 역투영을 재사용, 다른 격자는 기존 경로 유지. NoData·범위 밖·비균등축 회귀 유지. 지도 cache 방법 토큰을 갱신해 기존 300초 캐시와 분리. 실제 메시지15 값 유효비 1.0(1003×1024) 확인.
- [x] `after-2`에서 극지방 빈 줄 제거 및 확정 연결/해제 선언 복원 확인. 등록에 필수 기간을 넣지 않은 시나리오를 교정했으며 전체 통과 아님. 좁은 native 선택창의 긴 값도 잘려 보여 공용 native details로 전체 값 펼침을 추가(마지막 관련 35건 통과); 최종 세 화면 실측은 다음 실행.
- [x] CSS 구현 문자열을 복제하던 신규 시험은 제거하고 실제 브라우저 폭/펼침 단언으로 대체. 기존 시험은 보존.
- [ ] `services/viz-render/src/colab_viz/domains/d7_visualization/preview.py`의 `warp_to_3857`을 실제 메시지15로 재현한다. 전지구 위도별 값 fixture가 과도한 y 범위/투명영역을 잡는 RED를 확인한다.
- [ ] 유효 위도 처리의 최소 수정 후 값/위치 대응·NoData·지역 격자·전체 범위 밖 오류·bbox/sidecar 정합 시험을 실행한다. bbox 숫자만 clamp하고 값 배열을 그대로 늘리지 않는다.
- [ ] viz-render 관련 단독 시험과 실파일 메시지15 전후 이미지를 기록한다. 프런트와 별도 계약 변경 없음.
- [ ] advisor: intent 미달/초과, 스키마 무변경, 실제 증거 대조.
- [ ] CSS 정적 검사·frontend-visual의 실제 대상/계수와 frontend-test/typecheck 결과 기록.
- [ ] 로컬 PR 요약과 남은 제약을 runtime 인계에 기록. 원격 게시하지 않는다.
