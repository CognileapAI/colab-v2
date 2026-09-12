# 스타일 정의와 파일 커버리지

기준: 현재 작업 사본 HEAD c329c32. CSS 16개, TSX 82개를 전수 대상으로 삼았다. 라이브에서 모든 조건 분기를 실행했다는 의미는 아니다.

## CSS import 도달성

| 파일 | main에서 도달 | 직접 import 주체 |
|---|---|---|
| `frontend/src/auth/login.css` | 예 | `frontend/src/auth/LoginPage.tsx` |
| `frontend/src/components/catalog/catalog.css` | 예 | `frontend/src/routes/DatasetsPage.tsx` |
| `frontend/src/components/common/toast.css` | 예 | `frontend/src/components/common/Toast.tsx` |
| `frontend/src/components/common/variableTable.css` | 예 | `frontend/src/components/common/VariableTable.tsx` |
| `frontend/src/components/dashboard/dashboard.css` | 예 | `frontend/src/routes/LabPage.tsx` |
| `frontend/src/components/detail/detail.css` | 예 | `frontend/src/routes/DatasetDetailPage.tsx` |
| `frontend/src/components/lab/lab.css` | 예 | `frontend/src/components/lab/LabInfoPanel.tsx` |
| `frontend/src/components/lineage/lineage.css` | 예 | `frontend/src/components/lineage/LineageFixModal.tsx` · `frontend/src/components/lineage/LineageStep.tsx` |
| `frontend/src/components/lineage/lineageGraph.css` | 예 | `frontend/src/components/lineage/LineageSection.tsx` |
| `frontend/src/components/members/members.css` | 예 | `frontend/src/components/members/MemberPermissionGrid.tsx` |
| `frontend/src/components/preview/preview.css` | 예 | `frontend/src/components/datasetpreview/DatasetPreviewSection.tsx` · `frontend/src/components/preview/BasemapLayer.tsx` · `frontend/src/components/preview/PreviewSlot.tsx` · `frontend/src/components/preview/PreviewZoomControls.tsx` · `frontend/src/routes/UnregisteredPreviewPage.tsx` |
| `frontend/src/components/project/project.css` | 예 | `frontend/src/routes/ProjectDetailPage.tsx` · `frontend/src/routes/ProjectsPage.tsx` |
| `frontend/src/components/search/search.css` | 예 | `frontend/src/routes/LabPage.tsx` · `frontend/src/routes/SearchResultsPage.tsx` |
| `frontend/src/components/upload/upload.css` | 예 | `frontend/src/components/upload/GridAttachEntry.tsx` · `frontend/src/components/upload/UnfinishedUploads.tsx` · `frontend/src/components/upload/UploadEntry.tsx` |
| `frontend/src/shell/shell.css` | 예 | `frontend/src/main.tsx` |
| `frontend/src/shell/tokens.css` | 예 | `frontend/src/components/members/members.css` · `frontend/src/shell/shell.css` |

`shell.css`의 CSS `@import`도 추적했다. `tokens.css`가 미연결이라는 초기 기계 후보는 JS import만 추적해 생긴 오탐으로 폐기했다. 모든 라우트가 정적으로 import되므로 타 화면의 전역 CSS도 최초 화면부터 도달한다. 도달한다고 해당 DOM에 맞는다는 보장은 없다.

## TSX 담당과 전수 확인

| 파일 | 검토 담당 |
|---|---|
| `frontend/src/app/App.tsx` | L1 |
| `frontend/src/app/routes.tsx` | L1 |
| `frontend/src/auth/AuthGate.tsx` | L1 |
| `frontend/src/auth/LoginPage.tsx` | L1 |
| `frontend/src/components/approval/AccessRequestPanel.tsx` | L3 |
| `frontend/src/components/approval/VerificationAction.tsx` | L3 |
| `frontend/src/components/approval/VerifiedBadge.tsx` | L3 |
| `frontend/src/components/catalog/AppliedConditions.tsx` | L2 |
| `frontend/src/components/catalog/AxisFilterBar.tsx` | L2 |
| `frontend/src/components/catalog/CatalogTable.tsx` | L2 |
| `frontend/src/components/catalog/ColumnMenu.tsx` | L2 |
| `frontend/src/components/common/LoadFailure.tsx` | L1 |
| `frontend/src/components/common/Toast.tsx` | L1 |
| `frontend/src/components/common/VariableTable.tsx` | L1 |
| `frontend/src/components/dashboard/DataMapCard.tsx` | L1 |
| `frontend/src/components/dashboard/EmptyLabOnboarding.tsx` | L1 |
| `frontend/src/components/dashboard/LabInfoModal.tsx` | L1 |
| `frontend/src/components/dashboard/RecentActivity.tsx` | L1 |
| `frontend/src/components/dashboard/SummaryTiles.tsx` | L1 |
| `frontend/src/components/dashboard/TodoInbox.tsx` | L1 |
| `frontend/src/components/datasetpreview/DatasetPreviewSection.tsx` | L2 |
| `frontend/src/components/datasetpreview/ScreenshotButton.tsx` | L2 |
| `frontend/src/components/datasetpreview/ValueLookupPanel.tsx` | L2 |
| `frontend/src/components/detail/BasicInfoGrid.tsx` | L2 |
| `frontend/src/components/detail/DatasetEditEntry.tsx` | L2 |
| `frontend/src/components/detail/DatasetEditForm.tsx` | L2 |
| `frontend/src/components/detail/DefaultGridButton.tsx` | L2 |
| `frontend/src/components/detail/DetailHeader.tsx` | L2 |
| `frontend/src/components/detail/FileList.tsx` | L2 |
| `frontend/src/components/detail/LockedNotice.tsx` | L2 |
| `frontend/src/components/detail/PieceList.tsx` | L2 |
| `frontend/src/components/detail/RepresentativeImageSection.tsx` | L2 |
| `frontend/src/components/detail/SectionMenu.tsx` | L2 |
| `frontend/src/components/detail/UsageSection.tsx` | L2 |
| `frontend/src/components/lab/LabInfoGrid.tsx` | L3 |
| `frontend/src/components/lab/LabInfoPanel.tsx` | L3 |
| `frontend/src/components/lineage/LineageFixModal.tsx` | L3 |
| `frontend/src/components/lineage/LineageSection.tsx` | L3 |
| `frontend/src/components/lineage/LineageStep.tsx` | L3 |
| `frontend/src/components/lineage/ParentPicker.tsx` | L3 |
| `frontend/src/components/members/MemberPermissionGrid.tsx` | L3 |
| `frontend/src/components/preview/BasemapLayer.tsx` | L2 |
| `frontend/src/components/preview/PreviewControls.tsx` | L2 |
| `frontend/src/components/preview/PreviewPanels.tsx` | L2 |
| `frontend/src/components/preview/PreviewPickRow.tsx` | L2 |
| `frontend/src/components/preview/PreviewSlot.tsx` | L2 |
| `frontend/src/components/preview/PreviewZoomControls.tsx` | L2 |
| `frontend/src/components/project/ProjectCards.tsx` | L3 |
| `frontend/src/components/project/ProjectCloseModal.tsx` | L3 |
| `frontend/src/components/project/ProjectDatasetTable.tsx` | L3 |
| `frontend/src/components/project/ProjectFormModal.tsx` | L3 |
| `frontend/src/components/project/ProjectTable.tsx` | L3 |
| `frontend/src/components/project/ProjectToolbar.tsx` | L3 |
| `frontend/src/components/search/SearchHero.tsx` | L2 |
| `frontend/src/components/search/SearchHitCard.tsx` | L2 |
| `frontend/src/components/upload/FileDropCard.tsx` | L3 |
| `frontend/src/components/upload/GridAttachEntry.tsx` | L3 |
| `frontend/src/components/upload/GridUploadBlock.tsx` | L3 |
| `frontend/src/components/upload/PeriodCalendarPopover.tsx` | L3 |
| `frontend/src/components/upload/PreviewExpandOverlay.tsx` | L3 |
| `frontend/src/components/upload/PreviewPanel.tsx` | L3 |
| `frontend/src/components/upload/RegisterArea.tsx` | L3 |
| `frontend/src/components/upload/UnfinishedUploads.tsx` | L3 |
| `frontend/src/components/upload/UploadEntry.tsx` | L3 |
| `frontend/src/components/upload/UploadModal.tsx` | L3 |
| `frontend/src/main.tsx` | L1 |
| `frontend/src/permission/LockedContent.tsx` | L1 |
| `frontend/src/permission/PermissionGate.tsx` | L1 |
| `frontend/src/permission/session.tsx` | L1 |
| `frontend/src/placeholders/LockIndicatorSlot.tsx` | L1 |
| `frontend/src/placeholders/VerifiedBadgeSlot.tsx` | L1 |
| `frontend/src/routes/DatasetDetailPage.tsx` | L2 |
| `frontend/src/routes/DatasetsPage.tsx` | L2 |
| `frontend/src/routes/LabPage.tsx` | L1 |
| `frontend/src/routes/LabSettingsPage.tsx` | L3 |
| `frontend/src/routes/NotFoundPage.tsx` | L1 |
| `frontend/src/routes/ProjectDetailPage.tsx` | L3 |
| `frontend/src/routes/ProjectsPage.tsx` | L3 |
| `frontend/src/routes/SearchResultsPage.tsx` | L2 |
| `frontend/src/routes/UnregisteredPreviewPage.tsx` | L2 |
| `frontend/src/shell/AppLayout.tsx` | L1 |
| `frontend/src/shell/Gnb.tsx` | L1 |

TS/타입·서비스 보조 파일은 import 및 동작 근거로 참조했다. 연구자의 총 읽기 파일 수는 이 TSX 82개와 단위가 달라 합산하지 않는다.

## CSS 정의가 없는 정적 클래스 이름 전수

65종 / 마크업 사용 136곳. 아래는 **클래스명 직접 정의 부재 목록**이며 65개의 결함 목록이 아니다. 조상·태그 선택자, 의미/시험용 hook, 기본 클래스가 대신 스타일을 제공할 수 있다.

| 이름 | 사용 수 | 소유 파일·행 |
|---|---:|---|
| `ar-error` | 3 | `frontend/src/components/approval/AccessRequestPanel.tsx:73` · `frontend/src/components/approval/VerificationAction.tsx:127` · `frontend/src/components/approval/VerificationAction.tsx:150` |
| `ar-pending` | 1 | `frontend/src/components/approval/AccessRequestPanel.tsx:30` |
| `ar-pending-note` | 1 | `frontend/src/components/approval/AccessRequestPanel.tsx:32` |
| `ar-reason` | 1 | `frontend/src/components/approval/AccessRequestPanel.tsx:64` |
| `axis-bar` | 1 | `frontend/src/components/catalog/AxisFilterBar.tsx:21` |
| `axis-k` | 2 | `frontend/src/components/catalog/AxisFilterBar.tsx:26` · `frontend/src/routes/DatasetsPage.tsx:111` |
| `axis-pick` | 2 | `frontend/src/components/catalog/AxisFilterBar.tsx:25` · `frontend/src/routes/DatasetsPage.tsx:110` |
| `btn-danger` | 1 | `frontend/src/components/approval/VerificationAction.tsx:132` |
| `btn-secondary` | 42 | `frontend/src/components/approval/VerificationAction.tsx:50` · `frontend/src/components/datasetpreview/DatasetPreviewSection.tsx:467` · `frontend/src/components/detail/DatasetEditEntry.tsx:13` · `frontend/src/components/detail/DatasetEditForm.tsx:185` · `frontend/src/components/detail/DatasetEditForm.tsx:239` · `frontend/src/components/detail/DatasetEditForm.tsx:262` · `frontend/src/components/detail/DefaultGridButton.tsx:30` · `frontend/src/components/detail/RepresentativeImageSection.tsx:165` · `frontend/src/components/detail/RepresentativeImageSection.tsx:171` · `frontend/src/components/lab/LabInfoPanel.tsx:116` · `frontend/src/components/lab/LabInfoPanel.tsx:233` · `frontend/src/components/lineage/LineageFixModal.tsx:174` · `frontend/src/components/lineage/LineageSection.tsx:223` · `frontend/src/components/lineage/LineageSection.tsx:224` · `frontend/src/components/lineage/LineageSection.tsx:225` · `frontend/src/components/lineage/LineageSection.tsx:298` · `frontend/src/components/lineage/LineageStep.tsx:334` · `frontend/src/components/lineage/LineageStep.tsx:482` · `frontend/src/components/lineage/LineageStep.tsx:619` · `frontend/src/components/lineage/ParentPicker.tsx:110` · `frontend/src/components/lineage/ParentPicker.tsx:158` · `frontend/src/components/lineage/ParentPicker.tsx:161` · `frontend/src/components/lineage/ParentPicker.tsx:179` · `frontend/src/components/members/MemberPermissionGrid.tsx:113` · `frontend/src/components/members/MemberPermissionGrid.tsx:206` · `frontend/src/components/project/ProjectCloseModal.tsx:73` · `frontend/src/components/project/ProjectFormModal.tsx:217` · `frontend/src/components/upload/FileDropCard.tsx:195` · `frontend/src/components/upload/GridAttachEntry.tsx:43` · `frontend/src/components/upload/GridUploadBlock.tsx:99` · `frontend/src/components/upload/RegisterArea.tsx:1131` · `frontend/src/components/upload/RegisterArea.tsx:1144` · `frontend/src/components/upload/RegisterArea.tsx:446` · `frontend/src/components/upload/RegisterArea.tsx:760` · `frontend/src/components/upload/UploadModal.tsx:1268` · `frontend/src/components/upload/UploadModal.tsx:1288` · `frontend/src/components/upload/UploadModal.tsx:1295` · `frontend/src/components/upload/UploadModal.tsx:1314` · `frontend/src/components/upload/UploadModal.tsx:1396` · `frontend/src/components/upload/UploadModal.tsx:1431` · `frontend/src/components/upload/UploadModal.tsx:1598` · `frontend/src/routes/DatasetDetailPage.tsx:268` |
| `catalog` | 1 | `frontend/src/components/catalog/CatalogTable.tsx:77` |
| `chip--closed` | 3 | `frontend/src/components/project/ProjectCards.tsx:40` · `frontend/src/components/project/ProjectTable.tsx:32` · `frontend/src/routes/ProjectDetailPage.tsx:122` |
| `chip--info` | 1 | `frontend/src/components/upload/RegisterArea.tsx:715` |
| `chip--lineage` | 2 | `frontend/src/components/project/ProjectFormModal.tsx:186` · `frontend/src/routes/ProjectDetailPage.tsx:162` |
| `chip--success` | 1 | `frontend/src/components/upload/UploadModal.tsx:1244` |
| `chip--verified` | 1 | `frontend/src/components/approval/VerifiedBadge.tsx:16` |
| `cn` | 1 | `frontend/src/components/upload/FileDropCard.tsx:274` |
| `cta-a` | 1 | `frontend/src/components/project/ProjectCards.tsx:60` |
| `cta-t` | 1 | `frontend/src/components/project/ProjectCards.tsx:59` |
| `dash-bar-name` | 1 | `frontend/src/components/dashboard/DataMapCard.tsx:33` |
| `dash-recent-name` | 1 | `frontend/src/components/dashboard/RecentActivity.tsx:78` |
| `de-confirm` | 1 | `frontend/src/components/detail/DatasetEditForm.tsx:228` |
| `de-confirm-msg` | 1 | `frontend/src/components/detail/DatasetEditForm.tsx:229` |
| `de-note` | 2 | `frontend/src/components/detail/DatasetEditForm.tsx:175` · `frontend/src/components/detail/DatasetEditForm.tsx:193` |
| `dh-menu` | 1 | `frontend/src/components/approval/VerificationAction.tsx:90` |
| `dh-more` | 1 | `frontend/src/components/approval/VerificationAction.tsx:78` |
| `dsec` | 2 | `frontend/src/components/detail/UsageSection.tsx:56` · `frontend/src/components/lineage/LineageSection.tsx:340` |
| `dt-preview` | 1 | `frontend/src/components/datasetpreview/DatasetPreviewSection.tsx:230` |
| `err` | 1 | `frontend/src/components/upload/UploadModal.tsx:1418` |
| `fl-kind` | 1 | `frontend/src/components/detail/FileList.tsx:104` |
| `is-bundle` | 1 | `frontend/src/components/upload/FileDropCard.tsx:234` |
| `is-on` | 6 | `frontend/src/components/upload/RegisterArea.tsx:143` · `frontend/src/components/upload/RegisterArea.tsx:335` · `frontend/src/components/upload/RegisterArea.tsx:693` · `frontend/src/components/upload/RegisterArea.tsx:864` · `frontend/src/components/upload/UploadModal.tsx:1533` · `frontend/src/components/upload/UploadModal.tsx:1544` |
| `lab-info` | 1 | `frontend/src/components/dashboard/LabInfoModal.tsx:35` |
| `lin-candidate-files` | 1 | `frontend/src/components/lineage/ParentPicker.tsx:136` |
| `lin-mcard` | 1 | `frontend/src/components/lineage/LineageStep.tsx:516` |
| `lin-sec` | 1 | `frontend/src/components/lineage/LineageSection.tsx:340` |
| `lock` | 2 | `frontend/src/components/catalog/CatalogTable.tsx:150` · `frontend/src/components/search/SearchHitCard.tsx:29` |
| `mapbar` | 3 | `frontend/src/components/upload/PreviewPanel.tsx:403` · `frontend/src/components/upload/PreviewPanel.tsx:418` · `frontend/src/components/upload/UploadModal.tsx:1367` |
| `mapempty` | 1 | `frontend/src/components/upload/UploadModal.tsx:1370` |
| `modal-act` | 2 | `frontend/src/components/approval/AccessRequestPanel.tsx:74` · `frontend/src/components/approval/VerificationAction.tsx:128` |
| `modal-foot` | 1 | `frontend/src/components/dashboard/LabInfoModal.tsx:39` |
| `mono` | 7 | `frontend/src/components/catalog/CatalogTable.tsx:173` · `frontend/src/components/detail/FileList.tsx:106` · `frontend/src/components/project/ProjectDatasetTable.tsx:56` · `frontend/src/components/project/ProjectTable.tsx:36` · `frontend/src/components/upload/PeriodCalendarPopover.tsx:180` · `frontend/src/components/upload/PeriodCalendarPopover.tsx:191` · `frontend/src/components/upload/RegisterArea.tsx:243` |
| `mt` | 3 | `frontend/src/components/upload/PreviewPanel.tsx:404` · `frontend/src/components/upload/PreviewPanel.tsx:419` · `frontend/src/components/upload/UploadModal.tsx:1368` |
| `notfound` | 1 | `frontend/src/routes/NotFoundPage.tsx:10` |
| `pc-term` | 1 | `frontend/src/components/project/ProjectCards.tsx:41` |
| `pd` | 2 | `frontend/src/components/upload/PreviewPanel.tsx:663` · `frontend/src/components/upload/PreviewPanel.tsx:668` |
| `pd-closedbar` | 1 | `frontend/src/routes/ProjectDetailPage.tsx:127` |
| `pd-link` | 1 | `frontend/src/routes/ProjectDetailPage.tsx:159` |
| `pd-linkempty` | 1 | `frontend/src/routes/ProjectDetailPage.tsx:175` |
| `pd-sub` | 1 | `frontend/src/routes/ProjectDetailPage.tsx:123` |
| `pj-empty` | 1 | `frontend/src/routes/ProjectsPage.tsx:64` |
| `pname` | 1 | `frontend/src/components/project/ProjectTable.tsx:30` |
| `projrow` | 1 | `frontend/src/components/upload/RegisterArea.tsx:712` |
| `pt` | 2 | `frontend/src/components/upload/PreviewPanel.tsx:662` · `frontend/src/components/upload/PreviewPanel.tsx:667` |
| `pv-basic` | 1 | `frontend/src/components/preview/PreviewPanels.tsx:62` |
| `pv-preview` | 1 | `frontend/src/routes/UnregisteredPreviewPage.tsx:102` |
| `qh` | 1 | `frontend/src/components/upload/RegisterArea.tsx:785` |
| `show` | 1 | `frontend/src/components/members/MemberPermissionGrid.tsx:197` |
| `span` | 1 | `frontend/src/components/search/SearchHitCard.tsx:96` |
| `titem-name` | 3 | `frontend/src/components/dashboard/TodoInbox.tsx:121` · `frontend/src/components/dashboard/TodoInbox.tsx:163` · `frontend/src/components/dashboard/TodoInbox.tsx:85` |
| `up-cancel` | 1 | `frontend/src/components/upload/RegisterArea.tsx:1131` |
| `use-scope` | 1 | `frontend/src/components/detail/UsageSection.tsx:87` |
| `vc-impact` | 1 | `frontend/src/components/approval/VerificationAction.tsx:113` |
| `vc-reason` | 1 | `frontend/src/components/approval/VerificationAction.tsx:118` |
| `way` | 1 | `frontend/src/components/lineage/LineageSection.tsx:219` |
| `when` | 1 | `frontend/src/components/search/SearchHitCard.tsx:101` |

무해/단독 결함으로 채택하지 않은 대표 항목: `btn-secondary`(base `.btn` 적용), `catalog`, `dsec`, `pv-basic`, `pv-preview`, `dt-preview`, `fl-kind`, `span`, `when`(조상/태그 규칙 또는 의미 hook). `.btn-danger`, `.axis-*`, `.modal-foot`, `.notfound` 등은 사용 맥락까지 대조해 판정표에 따로 실었다.

## 동적 클래스 표현식 전수

25개는 자동 문자열 집계에서 빠지므로 아래 식과 상태별 CSS를 별도 확인했다. Lv0~3, conf 한글 enum, 정렬·필터·선택·계보 node·upload takeover 상태 정의가 존재한다. `is-editing` 같은 hook은 개별 선언 부재만으로 결함이 아니다.

| 위치 | 식 |
|---|---|
| `frontend/src/components/catalog/CatalogTable.tsx:84` | `[ sorted ? 'is-sorted' : '', sorted && state.query.sort.order === '오름' ? 'is-asc' : '', filtered ? 'is-filtered' : '', ] .filter(Boolean) .join(' ')` |
| `frontend/src/components/catalog/CatalogTable.tsx:143` | `clk${row.bodyAccessible ? '' : ' is-locked'}` |
| `frontend/src/components/catalog/CatalogTable.tsx:163` | `lvl lvl-${displayLevel(row)}` |
| `frontend/src/components/catalog/CatalogTable.tsx:175` | `lin lin--${row.lineageState === '확정' ? 'done' : row.lineageState === '확인 필요' ? 'wait' : 'none'}` |
| `frontend/src/components/catalog/ColumnMenu.tsx:30` | `cm-i${sort.column === column && sort.order === '오름' ? ' on' : ''}` |
| `frontend/src/components/catalog/ColumnMenu.tsx:38` | `cm-i${sort.column === column && sort.order === '내림' ? ' on' : ''}` |
| `frontend/src/components/catalog/ColumnMenu.tsx:56` | `cm-i${on ? ' on' : ''}${zero ? ' is-zero' : ''}` |
| `frontend/src/components/detail/BasicInfoGrid.tsx:111` | `ig${k === '구성' ? ' ig-variables' : ''}` |
| `frontend/src/components/detail/DatasetEditForm.tsx:52` | `dt-edit${props.fields ? " de-inline" : ""}` |
| `frontend/src/components/detail/DetailHeader.tsx:112` | `lvl lvl-${Math.min(lvShown, 3)}` |
| `frontend/src/components/lineage/LineageSection.tsx:101` | `lvl lvl-${lv}` |
| `frontend/src/components/lineage/LineageSection.tsx:126` | `cls` |
| `frontend/src/components/lineage/LineageSection.tsx:139` | `cls` |
| `frontend/src/components/lineage/LineageSection.tsx:232` | `lvl lvl-${displayLevel(node)}` |
| `frontend/src/components/lineage/LineageSection.tsx:479` | `lvl lvl-${displayLevel(selfNode)}` |
| `frontend/src/components/lineage/LineageStep.tsx:95` | `conf conf-${props.value}` |
| `frontend/src/components/members/MemberPermissionGrid.tsx:142` | `tbl memtbl${editing ? ' is-editing' : ''}` |
| `frontend/src/components/members/MemberPermissionGrid.tsx:171` | `pc${changed ? ' is-chg' : ''}` |
| `frontend/src/components/project/ProjectDatasetTable.tsx:53` | `lvl lvl-${displayLevel(row)}` |
| `frontend/src/components/search/SearchHitCard.tsx:23` | `hit${locked ? ' is-locked' : ''}${row.verified ? ' is-verified' : ''}` |
| `frontend/src/components/search/SearchHitCard.tsx:82` | `lvl lvl-${row.processingLevel}` |
| `frontend/src/components/upload/UploadModal.tsx:1118` | `modal-back mb-takeover${!registerOpen && !attach && !showingEarlyPreview && !previewFinalNotice ? ' up-empty' : ''}` |
| `frontend/src/routes/LabSettingsPage.tsx:23` | `st${tab === 'info' ? ' on' : ''}` |
| `frontend/src/routes/LabSettingsPage.tsx:32` | `st${tab === 'member' ? ' on' : ''}` |
| `frontend/src/routes/SearchResultsPage.tsx:55` | `vfilter${verifiedOnly ? ' on' : ''}` |

## 검사 한계

- 정적 JSX 클래스 사용 1,353곳, CSS에서 발견한 정의 이름 570종. 두 수의 단위는 다르다.
- 네이티브 control 250개 중 className 없는 요소 39개. 태그/조상 스타일이 있을 수 있어 누락 39건으로 보고하지 않는다.
- CSS selector 클래스 추출은 ASCII 클래스 이름 중심이다. 한글 conf 상태는 수동 확인했다.
- 전역 중복 규칙, selector 조건 미충족, 미도달 상태의 최종 외형은 이름 매칭만으로 합격 처리하지 않는다.
- 실물 사례: `RepresentativeImageSection.tsx`의 `.th-in`은 정의가 있지만 `.thumbrow .th-in` 조건에 맞지 않는다. `representative-selector.json`에서 matches=false, display=block을 측정했다.
- 전체 원값: `class-inventory.json`의 definitions/usages/nativeControls/imports. 재생성 도구: `class-inventory.mjs`.
