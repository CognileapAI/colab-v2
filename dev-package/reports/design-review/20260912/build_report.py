"""Assemble review evidence; does not modify product code."""
import json
from pathlib import Path
from collections import Counter, defaultdict

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
inventory=json.loads((OUT/'class-inventory.json').read_text())
audit=json.loads((OUT/'css_audit.json').read_text())
manifest=[json.loads(s) for s in (OUT/'live-manifest.jsonl').read_text().splitlines()]
rejected={'dataset-detail-desktop','dataset-detail-mobile'}
accepted=[r for r in manifest if r['name'] not in rejected]

def lane(file):
    if any('/components/'+p+'/' in file for p in ['catalog','search','detail','datasetpreview','preview']) or file.endswith(tuple('/routes/'+p+'.tsx' for p in ['DatasetsPage','SearchResultsPage','DatasetDetailPage','UnregisteredPreviewPage'])): return 'L2'
    if any('/components/'+p+'/' in file for p in ['upload','lineage','project','lab','members','approval']) or file.endswith(tuple('/routes/'+p+'.tsx' for p in ['ProjectsPage','ProjectDetailPage','LabSettingsPage'])): return 'L3'
    return 'L1'

coverage=['# 스타일 정의와 파일 커버리지', '',
    '기준: 현재 작업 사본 HEAD c329c32. CSS 16개, TSX 82개를 전수 대상으로 삼았다. 라이브에서 모든 조건 분기를 실행했다는 의미는 아니다.', '',
    '## CSS import 도달성', '', '| 파일 | main에서 도달 | 직접 import 주체 |','|---|---|---|']
for r in inventory['cssReachability']:
    coverage.append(f"| `{r['file']}` | {'예' if r['reachableFromMain'] else '아니오'} | {' · '.join('`'+x+'`' for x in r['importedBy'])} |")
coverage+=['','`shell.css`의 CSS `@import`도 추적했다. `tokens.css`가 미연결이라는 초기 기계 후보는 JS import만 추적해 생긴 오탐으로 폐기했다. 모든 라우트가 정적으로 import되므로 타 화면의 전역 CSS도 최초 화면부터 도달한다. 도달한다고 해당 DOM에 맞는다는 보장은 없다.', '',
    '## TSX 담당과 전수 확인', '', '| 파일 | 검토 담당 |', '|---|---|']
for f in inventory['scope']['tsxFiles']:coverage.append(f'| `{f}` | {lane(f)} |')
coverage+=['', 'TS/타입·서비스 보조 파일은 import 및 동작 근거로 참조했다. 연구자의 총 읽기 파일 수는 이 TSX 82개와 단위가 달라 합산하지 않는다.', '',
    '## CSS 정의가 없는 정적 클래스 이름 전수', '',
    '65종 / 마크업 사용 136곳. 아래는 **클래스명 직접 정의 부재 목록**이며 65개의 결함 목록이 아니다. 조상·태그 선택자, 의미/시험용 hook, 기본 클래스가 대신 스타일을 제공할 수 있다.', '',
    '| 이름 | 사용 수 | 소유 파일·행 |', '|---|---:|---|']
missing=defaultdict(list)
for r in inventory['missingCandidates']:missing[r['class']].append(r)
for name,uses in sorted(missing.items()):
    refs=sorted(set(f"{r['file']}:{r['line']}" for r in uses))
    coverage.append(f"| `{name}` | {len(uses)} | {' · '.join('`'+x+'`' for x in refs)} |")
coverage+=['', '무해/단독 결함으로 채택하지 않은 대표 항목: `btn-secondary`(base `.btn` 적용), `catalog`, `dsec`, `pv-basic`, `pv-preview`, `dt-preview`, `fl-kind`, `span`, `when`(조상/태그 규칙 또는 의미 hook). `.btn-danger`, `.axis-*`, `.modal-foot`, `.notfound` 등은 사용 맥락까지 대조해 판정표에 따로 실었다.', '',
    '## 동적 클래스 표현식 전수', '',
    '25개는 자동 문자열 집계에서 빠지므로 아래 식과 상태별 CSS를 별도 확인했다. Lv0~3, conf 한글 enum, 정렬·필터·선택·계보 node·upload takeover 상태 정의가 존재한다. `is-editing` 같은 hook은 개별 선언 부재만으로 결함이 아니다.', '',
    '| 위치 | 식 |','|---|---|']
for r in inventory['dynamicExpressions']:
    expr=' '.join((r['expression'] or '').split()).replace('|','&#124;').replace('`','')
    coverage.append(f"| `{r['file']}:{r['line']}` | `{expr}` |")
coverage+=['', '## 검사 한계', '',
    '- 정적 JSX 클래스 사용 1,353곳, CSS에서 발견한 정의 이름 570종. 두 수의 단위는 다르다.',
    '- 네이티브 control 250개 중 className 없는 요소 39개. 태그/조상 스타일이 있을 수 있어 누락 39건으로 보고하지 않는다.',
    '- CSS selector 클래스 추출은 ASCII 클래스 이름 중심이다. 한글 conf 상태는 수동 확인했다.',
    '- 전역 중복 규칙, selector 조건 미충족, 미도달 상태의 최종 외형은 이름 매칭만으로 합격 처리하지 않는다.',
    '- 실물 사례: `RepresentativeImageSection.tsx`의 `.th-in`은 정의가 있지만 `.thumbrow .th-in` 조건에 맞지 않는다. `representative-selector.json`에서 matches=false, display=block을 측정했다.',
    '- 전체 원값: `class-inventory.json`의 definitions/usages/nativeControls/imports. 재생성 도구: `class-inventory.mjs`.']
(OUT/'coverage.md').write_text('\n'.join(coverage)+'\n')

# Each row is a review topic, not a count of repeated DOM nodes or independent bugs.
rows=[
('D01','있음','우선 수정','본문과 폼 글꼴 불일치','shell/shell.css:85, components/catalog/AxisFilterBar.tsx:27, components/search/search.css:8','lab-desktop / catalog-desktop / dataset-detail-verified-mobile: body Pretendard, 일부 button/select Arial. 실제 한글 glyph fallback까지 측정한 것은 아님.'),
('D02','있음','우선 수정','카탈로그 필터 스타일·그룹 여백 누락','components/catalog/AxisFilterBar.tsx:21, routes/DatasetsPage.tsx:109','axis-bar/pick/k CSS 0. 데스크톱 select 높이 19px; 모바일 label과 select가 서로 다른 줄에 걸침. 지도 상태는 별도 형제.'),
('D03','있음','우선 수정','대시보드 카탈로그 버튼 외형 누락','components/dashboard/EmptyLabOnboarding.tsx:32, components/dashboard/DataMapCard.tsx:112, components/dashboard/dashboard.css:158','규칙은 margin-top만. 라이브 동일 CTA: Arial 13.3333px, padding 1px 6px, 브라우저 기본 버튼. 빈 연구실 분기는 사용자 첨부 증거.'),
('D04','있음','우선 수정','연구실 정보 모달 본문·하단 여백 누락','components/dashboard/LabInfoModal.tsx:34','lab-info-mobile: modal width375/x0/padding0, modal-foot padding0, 닫기 기본 버튼. desktop도 padding0.'),
('D05','있음','수정 후보','연구실 설정 화면 바깥 여백 누락','routes/LabSettingsPage.tsx:21','settings-desktop/mobile에서 tab/card가 화면 왼쪽 x0. root에 page 컨테이너 스타일 없음.'),
('D06','있음','우선 수정','프로젝트 생성의 모바일 날짜 입력 잘림','components/project/project.css:351, components/project/project.css:376, components/project/project.css:417','project-create-mobile: 375px에서 날짜 행 right334, 종료 input right375. body right350/overflowX auto. 두 month input min-width auto와 flex 배치.'),
('D07','있음','우선 수정','대표 그림 파일 선택기에 스타일 적용 조건 불일치','components/detail/RepresentativeImageSection.tsx:174, components/upload/upload.css:400','대표 그림 input.th-in은 .thumbrow 밖. 유일 .thumbrow .th-in 규칙 matches=false, display:block. 모바일 label right382, document scrollWidth382 > viewport375.'),
('D08','있음','우선 수정','로그인 카드가 모바일 가로폭 초과','auth/login.css:4, auth/login.css:12','login-mobile: viewport375, form x24/width360/right384. grid의 intrinsic 최소폭/입력 최소폭을 축소하지 못해 9px 페이지 초과.'),
('D09','있음','우선 수정','프로젝트 모달보다 상단 내비가 위에 표시','components/project/project.css:307, shell/shell.css:96','pj-modal-back z40 < GNB z100; project-create-mobile 실화면 확인. LabInfoPanel 편집 모달 z60도 정적 형제 후보이며 dashboard의 LabInfoModal(z200)과 혼동하지 않는다.'),
('D10','있음','우선 수정','모달 키보드 포커스가 배경으로 빠짐','components/dashboard/LabInfoModal.tsx:34, components/project/ProjectFormModal.tsx:84','연구실 정보 닫기 버튼 focus→Tab: BODY, 다음 Tab: 배경 Co-Lab 링크. dialog는 열린 채다. dialog-tab*.json. 프로젝트의 trap/initial focus/Escape 부재는 코드 근거.'),
('D11','있음','수정 후보','여러 화면의 읽는 글자가 11~12px','components/catalog/catalog.css:117, components/dashboard/dashboard.css:140, components/project/project.css, components/lineage/lineage.css','전수 정적 원시58선언. 장식/후속 override를 제외해 판정. 공식 4페이지 게이트에서 <13px 요소95회; 반복 DOM 포함이며 95개 독립 결함 아님.'),
('D12','있음','기존 판정 대조','상태/보조 글자 대비가 프로젝트 합격선보다 낮음','components/catalog/catalog.css:140, components/project/project.css:528, components/preview/preview.css','카탈로그 pending 4.23:1. 4페이지 gate 대비<4.5 요소23회. aria-disabled인 승인 대기 표현은 기존 승인 문안과 WCAG 비활성 예외를 대조해야 하므로 접근성 위반으로 일괄 단정하지 않는다.'),
('D13','있음','코드 기준 수정 후보','승인·접근 요청 UI의 개별 스타일 누락','components/approval/AccessRequestPanel.tsx:30, components/approval/VerificationAction.tsx:78','ar-*, vc-*, modal-act, dh-more/dh-menu, btn-danger 정의0. base btn/modal은 전역에서 도달하므로 승인 UI 전체가 무스타일이라고 표현하지 않는다. 권한별 실화면 미측정.'),
('D14','있음','코드 기준 수정 후보','업로드 미리보기 안내·일부 빈 상태 스타일 누락','components/upload/PreviewPanel.tsx:403, components/upload/UploadModal.tsx:1367, components/project/ProjectDetailPage.tsx','mapbar/mt/mapempty/err 및 일부 pj-empty/pd-closedbar/pd-linkempty 정의0. 실제 사용하는 branch와 조상 규칙 검토. 처리 후 상태는 실화면 미측정; 뜻만 붙인 class는 결함에서 제외.'),
('D15','있음','수정 후보','없는 주소 화면에 페이지 스타일 없음','routes/NotFoundPage.tsx:10','notfound 정의0. 라이브에서 문장이 x0에 붙고 링크가 브라우저 기본 visited 색으로 표시.'),
('D16','있음','코드 기준 수정 후보','잠긴 카탈로그 행의 키보드 상세 진입 없음','components/catalog/CatalogTable.tsx:143, components/catalog/CatalogTable.tsx:199','tr onClick만 있고 focus/key handler 없음. 접근 가능한 행은 엿보기 button으로 상세 진입 가능하므로 전체 행이 키보드 불가라는 초안 주장은 폐기. 잠긴 행에서는 이 button도 빠진다.'),
('D17','있음','공통화 설계 후보','같은 이름의 전역 control/card/modal 규칙이 여러 파일에 정의','components/upload/upload.css:291, components/members/members.css:30, components/catalog/catalog.css:127, components/project/project.css:287','btn/chip/card/modal의 다중 소유와 모든 route의 eager import 확인. 정의 중복 자체를 모든 화면의 렌더링 결함으로 세지 않는다. 현재 라이브가 각 element에 적용한 값과 이후 분리 위험을 구별.'),
('D18','있음','공통화 설계 후보','화면별 대체 토큰과 정본 토큰 혼용','components/dashboard/dashboard.css, components/preview/preview.css, shell/tokens.css:29','미정의 변수 이름18종/참조64회, 모두 fallback 있음. CSS 무효가 아니라 정본과 색 어휘가 갈라지는 설계 문제. 컴포넌트 고유 up/lin/pv 변수는 정상.'),
('D19','있음','낮은 우선순위','동작 줄이기 설정에서도 셸 transition 유지','shell/shell.css:137, auth/login.css:54, components/catalog/catalog.css:56','reduced-motion.json: reduce=true인데 labswitch/gnb-upload/avatar/logout duration0.14s. 업로드에는 reduce 분기3개가 있으므로 앱 전체 대응0으로 보고하지 않는다. 명시 :active 규칙0은 UA feedback 소실과 다르다.'),
('D20','있음','기존 판정 대조','카드 그림자·음수 여백 규칙 잔존','auth/login.css:12, components/project/project.css:243, components/project/project.css:436, components/members/members.css:5','project margin 음수1, login/project/members 카드 shadow 후보. 팝오버·모달·inset hover marker는 카드 그림자 금지와 분리. 최소 변경 범위와 이전 승인 의도를 대조한다.'),
('D21','미상','디자인 선택','모바일 대시보드 밀도와 줄바꿈의 적정 수준','components/dashboard/dashboard.css:161, components/dashboard/dashboard.css:211','375px에서 summary4열과 최근 활동 다열이 남아 긴 제목/라벨이 여러 줄로 쪼개진다. 화면 밖 overflow는0. 2열 전환/행 재배치는 디자인 선택.'),
('D22','미상','권한별 추가 계측','멤버 권한표·승인 취소·잠긴 데이터 요청의 최종 외형','components/members/MemberPermissionGrid.tsx, components/approval','현재 검수 계정의 members tab은 본문이 표시되지 않음. 멤버표를 실제로 검수했다고 세지 않는다. 승인/취소/접근 요청 제출0.'),
('D23','미상','데이터 상태별 추가 계측','업로드 처리·오류·등록 및 S-08 성공 미리보기 전 상태','components/upload, components/preview','파일 업로드/등록 제출0. 초기 업로드 modal, 기존 HDF5 상세 preview, S-08 이어받은 정보 없음만 라이브 확인. 상세 진입은 앱의 자동 preview 요청을 발생시킨다. 처리중/성공/실패 전수 외형 합격 아님.'),
('D24','미상','첨부와 실화면 구분','빈 연구실 안내 문장의 우측 잘림 원인','components/dashboard/EmptyLabOnboarding.tsx, components/dashboard/dashboard.css:133','사용자 첨부는 잘림처럼 보이나 원본 viewport/조상폭은 미측정. dash-lead 자체 nowrap/overflow 제약 없음. 빈 연구실을 만들거나 데이터를 삭제하지 않았다.'),
('D25','없음','—','CSS 파일이 앱에서 통째로 미연결','main.tsx, app/routes.tsx, shell/shell.css:1','16/16 도달. 클래스별 누락·적용조건 오류는 별도 있음.'),
('D26','없음','—','미정의 변수64곳이 모두 무효 선언','css_audit.json','64/64 fallback. 실제 선언 무효0으로 분류. 간격값 미정의라는 초기 설명을 정정했다.'),
('D27','없음','—','상세의 옛 소형 글자 후보가 전부 잔존','components/detail/detail.css:263','5개 기계 후보는 후속 13px override 존재. 캡처한 상세 기본·inline 편집·계보 편집의 probe small0.'),
('D28','없음','—','카탈로그 표가 모바일 페이지 전체를 가로로 넘김','components/catalog/catalog.css:40','table 폭은1151px이지만 tblwrap 안에서 스크롤; document375 유지. 외부 viewport 밖 cell을 전부 잘림 결함으로 세지 않는다.'),
('D29','없음','—','WU-C11 수정 항목이 다시 빠짐','components/catalog/catalog.css:134, components/detail/detail.css:69, components/lineage/lineageGraph.css','Lv3 구분/기록없음 대비/음수상쇄 제거/상세 여백·라벨 보정 유지. 완료 WU를 재개봉하지 않음.'),
('D30','미상','요구사항 대조','다크 테마 디자인의 완결성','gate/frontend-visual/*.dark.png','운영체제 dark 선호 스크린샷4장 확보. 제품이 별도 다크 테마를 요구하는지 이번 범위에서 확정하지 않았으므로 light 외형 유지 자체를 결함으로 세지 않음.'),
('D31','없음','—','미정의 클래스65종이 모두 디자인 결함','class-inventory.json, coverage.md','semantic hooks/기본 클래스/조상 규칙/상태 이름을 구분. 포커스 outline을 지우지 않은 native 요소를 focus 표시0으로 판정하지 않음.'),
]
counts=Counter(r[1] for r in rows)
findings=['# 전체 디자인 판정표', '',f"검토 주제 {len(rows)}개: 있음 {counts['있음']} / 없음 {counts['없음']} / 미상 {counts['미상']}. 이는 DOM 반복 수나 독립 버그 수가 아니다. '있음'에는 화면 결함과 명시한 구조 정리 후보가 포함된다.", '',
    '| ID | 판정 | 처리 | 항목 | 코드 근거(frontend/src 기준) | 실측·한계 |', '|---|---|---|---|---|---|']
for r in rows:findings.append('| '+' | '.join(r)+' |')
findings+=['', '## 우선 고칠 묶음', '',
    '1. 화면이 잘리는 문제: 로그인 카드, 프로젝트 날짜 행, 대표 그림 input의 조건 불일치. 수용: 375/768/1440px에서 의도한 내부 표 스크롤 외 페이지 overflow0.',
    '2. 기본 control 체계: 버튼·입력·선택 상자의 글꼴/높이/disabled/focus, 카탈로그 필터, dashboard CTA. 모든 control 일괄 reset으로 기존 화면을 깨지 않도록 공통 소유와 예외를 먼저 고정한다.',
    '3. 화면 공간 체계: 연구실 정보 modal 본문/하단, 연구실 설정 page, 404, mobile dashboard. 제목·내용·동작 영역의 여백을 컨테이너가 소유하게 한다.',
    '4. dialog 체계: stacking, 초기 focus, Tab 가두기/복귀, Escape, 내부 scroll. 승인/취소 같은 상태 변경은 실제 데이터를 바꾸지 않는 별도 검증 환경에서 확인한다.',
    '5. 잔여 접근성/일관성: 작은 글자, 대비 판정, 모션 줄이기, fallback 토큰과 중복 전역 선택자. 이미 승인된 상태 표현과 무해 hook은 일괄 수정하지 않는다.',
    '', '## 수정 작업 후보(미등재·미승인)', '',
    '- DESIGN-CONTROLS: 공통 control과 카탈로그/대시보드 누락 보완.',
    '- DESIGN-LAYOUT: 로그인·프로젝트 날짜·대표 그림·설정·정보 modal·404 공간 수정.',
    '- DESIGN-DIALOGS: modal 층위와 키보드 접근.',
    '- DESIGN-STATES: 승인/요청/업로드 상태 화면 및 가독성·토큰 정리.',
    '대장 work-items.yaml의 기존 완료 상태는 변경하지 않았다. 실제 WU 식별자 발급/수용 범위는 후속 구현 계획에서 확정한다.',
    '', '## 조사 초안의 정정', '',
    '- L2의 카탈로그 모든 행 키보드 불가 주장을 축소: 열린 행에는 엿보기 버튼이 있다. 잠긴 행 문제만 남긴다.',
    '- L3의 LabInfo 모달 z60 주장은 LabInfoPanel 편집 모달에 해당한다. dashboard 읽기 modal은 전역 z200이며 실제 결함은 padding0/기본 버튼이다.',
    '- 조사자의 P0 표기는 사용하지 않는다. 전사 중단/데이터 손실 증거가 없는 디자인 결함이다.',
    '- 미정의 변수는 간격이 아닌 주로 색상 어휘이며 모두 fallback 존재. 무효 선언으로 세지 않는다.',
    '- 연구자 자동 인계 훅 일부는 baseline/identity 문제로 차단됐다. 그 훅의 성공은 검수 근거로 쓰지 않고 코드·원자료·실화면을 대조했다.']
(OUT/'findings.md').write_text('\n'.join(findings)+'\n')

live=['# 실제 화면 확인 범위', '',
    '대상: 기존 검수용 로그인 프로필이 가리키는 개발 서비스 https://d31zgpff2091oh.cloudfront.net. 사용자에게 별도 주소를 문의했고 회신 전 기존 개발 환경을 사용했다. 소스맵에 포함된 TS/TSX 158/158 내용이 현재 작업 사본과 같음을 대조했다. 서버 Git SHA를 검증했다는 의미는 아니다.', '',
    f'수동 캡처 {len(manifest)}회 중 의도한 화면에 도달한 증거 {len(accepted)}회. 상세 진입 실패로 카탈로그에 남은 2회는 제외했다. 별도 공식 게이트는 4개 URL × light/dark 스크린샷 8장이다.', '',
    '| 캡처 | 화면/실제 상태 | 폭 | 문서 scrollWidth | <13px 원시 요소 | 대비<4.5 원시 요소 | 이미지 |', '|---|---|---:|---:|---:|---:|---|']
for r in manifest:
    state='대상 도달 실패: 실제 카탈로그' if r['name'] in rejected else (r['screen'] or '로그인')
    if r['name'].startswith('members-'):state+=' · 탭 진입만/권한표 미표시'
    if r['name'].startswith('preview-expired-'):state+=' · 이어받은 미리보기 없음(만료 아님)'
    image='live/'+r['name']+'.png'
    live.append(f"| {r['name']} | {state} | {r['viewport']['width']} | {r['document']['scrollWidth']} | {r['counts']['small']} | {r['counts']['lowContrast']} | [화면]({image}) |")
live+=['', '## 데이터/상태 경계', '',
    '- 저장·삭제·등록·승인·업로드 제출·권한 변경 조작0. 화면 진입과 modal 열기/닫기, tab/filter/view 변경을 수행했다. 앱이 조회 시 남기는 최근 열어봄 브라우저 기록과 로그인 세션은 발생한다.',
    '- 상세 화면은 진입 시 DatasetPreviewSection.tsx:143 및 datasetPreviewSource.ts:93에서 자동 POST /previews를 요청한다. 따라서 백엔드 요청 전체가 읽기 전용이거나 새 렌더0이었다고 주장하지 않는다. 서버의 캐시 재사용/새 렌더 작업 수는 미계측이다.',
    '- 모든 화면을 매번 실제 URL/data-screen과 대조했다. 멤버 탭 빈 본문은 멤버 UI 합격이 아니다.',
    '- 업로드 초기 상태는 파일을 고르지 않고 확인. 기존 HDF5 상세의 preview를 읽었고 팔레트/구간 변경으로 렌더 요청하지 않았다.',
    '- preview-expired라는 파일명의 두 캡처는 실제로 이어받은 정보 없음 상태이다. 실제 TTL 만료 상태 검증으로 재사용하지 않는다.',
    '- live_probe는 배경 overlay 뒤 요소와 표 내부 가로스크롤 요소도 수집한다. 여러 상태·폭의 원시 수를 합산해 독립 결함 수로 보고하지 않는다.',
    '- light/dark media는 공식 게이트에서 측정. reduce=true에서도 셸 transition이 남는 값은 reduced-motion.json.',
    '- 375px 기본 폭과 1440px 데스크톱을 확인했다. 768px·200% 확대·실제 iOS Safari·모든 긴 문자열과 권한별 상태는 미측정이다.',
    '', '## 공식 frontend-visual 게이트', '',
    '4 URL(lab/datasets/projects/lab-settings), 실제 exit1. green0 / red(판정)1 / red(준비)0. 13px 미만95회 / 대비4.5 미만23회 / 스크린샷8장 / 허용 접두사0. 독립 결함 수가 아니라 4페이지의 반복 요소 포함 관측이다. 게이트 기준을 완화하거나 허용 목록을 늘리지 않았다.',
    '근거: gate/gate-summary.json, gate/frontend-visual/index.md. 관련 검사는 이번 감사의 결함을 확인한 것이며 제품 수정 검증 성공이 아니다.',
    '', '## 검사 준비/실행 오류와 처리', '',
    '- 정적 감사 첫 실행은 출력 폴더가 없어 실패. 폴더 생성 후 정상 재실행했다.',
    '- 로그인 캡처 기록기가 data-screen 없는 페이지를 처리하지 못해 실패. 감사 도구의 optional field 처리를 고쳐 재실행했다. 제품 코드는 바꾸지 않았다.',
    '- 처음 상세 행 클릭은 모바일 넓은 표의 클릭 위치 때문에 카탈로그에 남았다. 두 캡처를 실패로 보존하고 데스크톱의 이름 셀 클릭 후 S-05 도달을 확인해 다시 측정했다.',
    '- 검색 URL의 셸 특수문자와 지원하지 않는 focus subaction은 실제 페이지 변경 전에 실패. 올바른 인자/CLI focus 명령으로 재실행했다.']
(OUT/'live-index.md').write_text('\n'.join(live)+'\n')

summary=f'''# 전체 디자인 검수 — 2026-09-12

상태: 검수 완료 · advisor② approve. 제품 코드 수정·커밋·배포 없음.
사용자 요청: 전체 스타일 정의 유무와 디자인 검수. 입력은 카탈로그 및 빈 연구실 안내 스크린샷이다.
기준 HEAD: c329c32. 기존 미커밋 변경은 다른 작업 소유로 보존했다.

## 결과

CSS 파일 16개는 모두 앱에 연결돼 있다. 하지만 개별 control 스타일 누락, selector가 현재 DOM에 맞지 않는 경우, 폰트 상속 누락, 모바일 최소폭·modal 층위·키보드 문제가 여러 화면에 있다.

- 정적 범위: CSS16 / TSX82 전수. 클래스 직접 정의 부재65종은 후보이며 모두 결함이 아니다.
- 실제 화면: 수동 캡처{len(manifest)}회 중 대상 도달{len(accepted)}회; 잘못 도달한2회 별도 표시. 권한표 미표시·숨은 처리 상태는 합격으로 세지 않는다.
- 공식 시각 검사: 4페이지에서 exit1, green0 / red(판정)1 / red(준비)0. 작은 글자95회·대비 미달23회(반복 요소 포함).
- 판정표 주제{len(rows)}개: 있음{counts['있음']} / 없음{counts['없음']} / 미상{counts['미상']}. 구조 정리 후보와 실제 화면 결함을 분리했다.

## 바로 볼 근거

- [전체 판정표와 수정 순서](../reports/design-review/20260912/findings.md)
- [스타일 정의·CSS 연결·82개 TSX 커버리지](../reports/design-review/20260912/coverage.md)
- [실제 화면별 결과와 스크린샷](../reports/design-review/20260912/live-index.md)
- [모바일 프로젝트 날짜 잘림](../reports/design-review/20260912/live/project-create-mobile.png)
- [안쪽 여백이 없는 연구실 정보 모달](../reports/design-review/20260912/live/lab-info-mobile.png)
- [모바일 로그인 가로폭 초과](../reports/design-review/20260912/live/login-mobile.png)
- [대표 그림의 selector 조건 불일치](../reports/design-review/20260912/representative-selector.json)

## 범위와 진행

- [x] 계획 advisor①: approve-with-changes. 미정의 클래스는 후보로만 집계하고 import/cascade/실화면 대조.
- [x] CSS16 전수 정적 계측, TSX82 클래스/control/CSS 도달성 재고.
- [x] L1 셸·로그인·공통·권한·대시보드, L2 목록·검색·상세·preview, L3 업로드·계보·프로젝트·연구실·멤버·승인 읽기 검토.
- [x] 실제 화면·375/1440px 확인 및 도달 실패/미확인 분리.
- [x] 통합 판정표와 수정 작업 후보 작성.
- [x] advisor② 수용 검토 반영: approve, 필수 수정 없음.

## 승인·수정 경계

검수 요청에 따라 결함과 제안을 기록했다. 새 WU 등재·기존 완료 항목 재개봉·제품 수정·커밋·배포는 하지 않았다. 코드 검수와 실제 화면의 실패를 숨기지 않으며 디자인 전체가 합격했다고 보고하지 않는다.
다음 구현은 findings.md의 우선 수정 항목에서 범위와 수용 기준을 확정한다. 커밋 SHA는 새로 없으며 검수 기준 SHA만 기록했다.

## 독립 검토

advisor② approve. 스크린샷4장과 코드·계측을 대조해 핵심 결론을 수용했다. 코드 기준 후보(D13/14), 대비 기준과 WCAG 판정(D12), 권한별 미측정, 축소 이미지와 computed 크기의 구분을 유지한다. 이 판정은 구현·배포 승인이 아니다.
조사자의 과도한 P0 분류, 열린 행의 키보드 대체 버튼 누락 주장, 두 연구실 모달 혼동, fallback을 무효 선언으로 본 가능성은 부모가 실물 대조해 수정했다. 마지막 증거 점검에서 상세 진입 시 자동 POST /previews가 있음을 확인하고 렌더 요청0이라는 초안을 정정했다.

## 요청과 산출 대조

별도 승인 intent 파일이 지정되지 않아 현재 대화의 “스타일 정의 다 들어가 있는지 … 디자인 전체검수”를 기준으로 삼았다.
충족: CSS/TSX 전수 재고, 정의 누락과 조건 불일치 확인, 화면별 글꼴·간격·반응형·키보드 검수, 오탐 분리, 수정 우선순위와 실제 증거.
미달/미확인: 권한별 숨은 화면·파일 처리 후 모든 상태, 빈 연구실의 동일 조건 재현, 768px/200%/실제 모바일 브라우저, 다크 요구사항. 이 범위를 전수 실화면 합격으로 주장하지 않는다.
초과 구현0: 제품 기능·디자인 수정은 없고 추가 파일은 검수 보고서와 재현 도구/증거다.
'''
(ROOT/'dev-package/sessions/design-review-20260912.md').write_text(summary)
print(json.dumps({'reviewTopics':len(rows),'judgments':counts,'captures':len(manifest),'acceptedCaptureTargets':len(accepted),'tsxByLane':Counter(lane(f) for f in inventory['scope']['tsxFiles'])},ensure_ascii=False))
