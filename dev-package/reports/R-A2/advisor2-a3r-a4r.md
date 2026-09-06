# Gate ② 수용 검토 — lane `p3-detail-edit2` (WU-A3R ＋ WU-A4R) · e01206c..87ca9df

## For
- A3R 완료 조건 ⑴⑵ 가 코드·시험 양쪽에서 성립 — `DatasetDetailPage.tsx:229-247`(편집 중 `dt-download` 미렌더) · `UsageSection.tsx:80`(`downloadHidden`) · `DatasetEditActions` 가 `dt-gridact` 행 안에 1건(`within(row)` 단언 ＋ `getAllByTestId` 길이 1).
- 재동기 결함 수정이 실물 결함 — 종전 `detail.detail.actions`(초기 조회값)를 읽던 3자리를 `shown.actions` 로 전환. 저장 응답은 계약상 `DatasetDetail`(`fe-core.yaml:968-972`) · `actions` required(`:3896-3899`) · 서버 PATCH 반환 = `dataset_detail()`(`catalog.py:778`, GET 과 동일 빌더 · `actions` 계산 `:922`). 형상 차이 없음.
- RED 3 → GREEN 실측 기록(⑴ 2건 · ⑵ 1건) · 회귀 18 ＋ 업로드 2 · 계약/서버/DB 0. 폐기 시 대가 = 재동기 결함이 통합 브랜치에 잔존.

## Against
- A4R 은 코드 delta 0 — 「green 으로 시작하는 시험은 오라클이 아니다」(CLAUDE.md §4) 문면상 이 WU 의 시험 2건은 오라클이 아니라 회귀 고정이다. 레인 없이 대장에서 「기점 충족」으로 닫는 것이 더 싼 경로였다.
- 배치 변경 하나에 4파일 리팩터(상태 상승). 다만 버튼이 폼 밖 두 자리(`dt-gridact` · 잠긴 상세의 폼 옆)에 서므로 두 렌더 지점이 한 상태를 봐야 하고, 더 작은 대안(포털·prop 전달)은 동일 복잡도. 반론 기각.
- 뒤집는 증거 = 실화면에서 `.de-act` 스타일이 `dt-gridact` 행 레이아웃을 깨뜨리는 스크린샷. jsdom 은 이를 못 본다.

## Verdict
- **approve** — A3R done. A4R done 처리 가능하되 대장 `note`/`evidence` 에 「라벨은 a32e580(WU-A4)에서 기점 충족 · 이 레인은 회귀 2건 고정 · RED 불가」 명기.

## Risks
1. 레인 `dev-package/reports/R-A2/p3-detail-edit2/gate-summary.json` 이 마지막 실행(`frontend-fixture-reach` 1건)만 보존 — typecheck·test 868 은 세션 노트 텍스트만 근거.
2. 잠긴 상세(`basicInfo` null)에서 편집 열기 → 버튼이 폼 옆(`DatasetDetailPage.tsx:204`)에 서는 분기는 시험 0건.
3. 저장 중(`saving`) 두 버튼 `disabled` 는 코드 존치이나 단언 부재(기존 공백 승계).

## Missed (intent 대조 열거)
- intent 항목 5 「편집 중 다운로드 숨김 · 저장 뒤 헤더 칩 재동기 · `좌표계 (선택)`」 — 미달 0.
- 초과 1(경미) = `FileList actions={shown.actions}`(`DatasetDetailPage.tsx:267`) — 라운드 문면(헤더 칩·공개 범위 설명) 밖 · 같은 결함군 · 레인이 자기 표시 §4 에 기재. 수용.
- (a) 공개 범위 설명 = R-A 에서 상수 `ACCESS_ORIGIN_NOTE` 이므로 「같은 값으로 다시 그려진다」의 검증 가능 범위는 표시 여부(`canDownload` 반전)까지. 값 칸 재동기는 R-B(WU-B3) 에서 재검증 필요 — 라운드 파일에 인계 한 줄.
- (c) 제외 목록 준수 실측 — 폼 입력 7칸(기존 시험 212행) · `edit-topic` 부재 · R-B 칸 미렌더(234행). 존치 6종 중 `DetailHeader.tsx`·`LockedNotice.tsx` diff 공집합.
- (e) 오라클 축소 근거 = PRD-28:699 「좌표계 칸 라벨이 `좌표계 (선택)` 이다 — **격자** · 변수 · 기간 시작 · 설명 · 원천 표기와 같은 패턴이고, **선택 항목인데** 보조 라벨이 없는 칸이 이 줄에 남아 있지 않다」 — 격자는 패턴 예시(보조 라벨 `자동`, `RegisterArea.tsx:67-72` `AutoField`)이며 선택 항목이 아니다. 축소 지지. 시험은 자동 칸 1건·`격자자동` 을 별도 단언해 대상 건수 0 이 아님을 보인다.
- (f) 취소 복원 = 기존 327행 시험(재열기 시 `BASE.name`) green · `open()` 이 `toDraft(patched ?? base)` 로 재파생 — 종전 `useState(() => toDraft(props.detail))` 과 동치. 오류 자리 = `detail-edit-error` 폼 내부 존치(303·316행 green). `base` 변경 시 draft·error·saving 초기화 추가 — 종전 언마운트 초기화와 동치.
- 세션 노트 주석 「P-12 와 같은 관례」 출처 미확인 — 판정 무관.

## Fixes
- [병합 전 필수] 통합 트리(병합 후 커밋)에서 `frontend-typecheck` · `frontend-test` · `work-item-consistency` 재실행 — 레인 summary 가 1 게이트만 보존.
- [병합 전 필수] `work-items.yaml` WU-A4R `note` 에 「라벨 기점 충족(a32e580 · WU-A4) · 본 레인 회귀 2건(`upload.test.tsx:869-894`) · RED 불가」 추가, status → done. WU-A3R status → done.
- [비차단] 라운드 파일 §2-⑤ 또는 WU-B3 인계에 「공개 범위 **값** 재동기 재검증(R-A 는 상수 문장만)」 1행.
- [비차단] 실화면 1회 — `dt-gridact` 행의 `취소`/`저장` 배치 · 잠긴 상세 편집 분기. 스크린샷을 `dev-package/reports/R-A2/p3-detail-edit2/` 에 첨부.
- [기록만] `GridAttachEntry` 편집 중 노출 — 라운드 문면은 다운로드만 지목. 판정 필요 시 Ted 묶음 질의에 적재.
