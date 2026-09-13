# agent-browser CLI 능력 확인 — dev 프런트 구동 가능성

- 성격 = **도구 실측 기록.** 시나리오 `dev-package/scenarios/dev-minimal-data-setup.md` 는 「브라우저 자동화 도구는 이 회차 범위 밖」(라운드 결정 14)이라 적었고, 이 문서는 그 결정을 바꾸지 않는다. **가능 여부만 잰다.**
- 측정일 = 2026-09-13 · 측정 호스트 = WSL2(리눅스 6.18 · x86_64).
- 이번 측정에서 하지 않은 것 = 로그인 · 폼 제출 · 파일 업로드 · 자격 입력. **입력 칸에 한 글자도 넣지 않았다.**
- 레포 변경 = 이 문서 1건. 코드·설정 무변.

## 1. 설치

- 방법 = `npm i -g agent-browser` **전역 설치 성공**. 스크래치 prefix 폴백 미사용.
- 버전 = `agent-browser 0.27.0`. 실행기 자리 = 사용자 홈의 `.npm-global/bin`.
- Node = v22.22.1 · npm = 11.12.1.
- 설치 소요 = 약 2초(패키지 1건).

## 2. 브라우저 원천

- 실물 = **Google Chrome for Testing 152.0.7977.82** — CLI 가 **자체 캐시로 자동 내려받는다**. 자리 = 사용자 홈의 `.agent-browser/browsers/`.
- ⭑ **`npx playwright install chromium` 폴백은 쓰지 않았다** — 불필요했다. 이 CLI 는 Playwright·Puppeteer 의존이 없고 **CDP 로 직접 붙는다**(스킬 문서 축자 「Chrome/Chromium via CDP, no Playwright or Puppeteer dependency」).
- 시스템 Chrome 도 쓸 수 있다 — `--executable-path` · 환경변수 `AGENT_BROWSER_EXECUTABLE_PATH` · `--profile <경로>`(로그인 상태 존속) · `--auto-connect`(실행 중 Chrome 에 붙기).
- 기본값 = **헤드리스**. 창을 띄우려면 `--headed`.
- 자체 진단 `agent-browser doctor` = **10 pass · 0 warn · 0 fail**. 헤드리스 기동 + `about:blank` 실측 0.74초.
- 별도 `install` 하위명령 없음 — 첫 실행이 내려받는다. 수리는 `doctor --fix`.

## 3. 명령 (요청 대조)

| 요청 항목 | 실물 명령 | 비고 |
|---|---|---|
| open | `open <url>` (별칭 `goto`·`navigate`) | 프로토콜 생략 시 `https://` 자동 부착. URL 없이 열면 `about:blank` 대기 |
| snapshot | `snapshot -i` | 접근성 트리 + `@eN` 참조. `-u` href 병기 · `-c` 빈 노드 제거 · `-d <n>` 깊이 · `-s <css>` 범위 · `--json` |
| click | `click <선택자 또는 @ref>` | `dblclick`·`hover`·`focus`·`check`·`uncheck`·`select` 별도 |
| fill / type | `fill <선택자> <문자열>`(비우고 채움) · `type <선택자> <문자열>`(비우지 않음) | 선택자 없는 실제 키 입력 = `keyboard type` · `keyboard inserttext` |
| 파일 지정 | **`upload <선택자> <파일...>`** | 4절 |
| wait | `wait <선택자 또는 밀리초>` | `wait --load networkidle` · `wait --url "**/패턴"` |
| screenshot | `screenshot [경로]` | `pdf <경로>` · 동영상 `record start/stop`(WebM) |
| eval | `eval <js>` | 페이지 안에서 JS 실행 |

- 그 밖 = `find role|text|label|placeholder|alt|title|testid <값> <동작>`(참조 없이 의미 기반 지목) · `get text|html|value|attr|title|url|count|box` · `is visible|enabled|checked` · `back`·`forward`·`reload` · `tab` · `cookies`·`storage` · `console`·`errors` · `diff snapshot`·`diff screenshot` · `batch`(여러 명령 한 번에) · `set viewport|device|media dark|light`.
- ⭑ **`find testid` 가 있다** — 6절 표의 `data-testid` 를 그대로 지목할 수 있어 참조 재계산이 필요 없다.
- 시작점 = `agent-browser skills get core --full`(2,425줄). 버전 동봉이라 판본 어긋남이 없다.

### 참조(`@eN`)가 도는 방식

- `snapshot -i` 가 상호작용 요소마다 `@e1`·`@e2` 를 붙인다.
- ⚠ **참조는 스냅샷마다 새로 매긴다.** 페이지가 바뀌면 **무효**다 — 문서 축자 「Refs are assigned fresh on every snapshot」. 화면이 바뀔 때마다 다시 스냅샷을 뜬다.
- 안정적인 지목이 필요하면 참조 대신 `find testid <값>` 또는 CSS 선택자를 쓴다.

## 4. 파일 지정 능력

- 명령 = `agent-browser upload <선택자 또는 @ref> <파일...>` — `<input type="file">` 에 파일을 **직접 심는다**(파일 선택 대화창을 거치지 않는다).
- **다중 지정 성립** = 파일 인자를 여러 개 나열한다. 도움말 예 축자 = `agent-browser upload @e3 ./image1.png ./image2.png`.
- 외부 드라이브 경로 접근 = **성립**. 실측 = `03 Reference-Data` 아래 `02.File-format/file_format_1_grib/00.Data/surface.grib` · **149,514,336 B**(약 142.6 MiB) · 읽기 가능.
  - ⚠ 경로에 **공백이 있다**(`00 CoLAB` · `03 Reference-Data`). 인용부호 필수.
- **도구가 명시하는 파일 크기·건수 상한 = 없다.** 도움말·핵심 스킬 문서 어디에도 기재가 없다. 제약은 도구가 아니라 제품 쪽이다 — 시나리오 5절 축자 「1회 업로드 상한 = 파일 500건 · 파일명 255자」 · 16 MiB 이상은 멀티파트.
- `[미확인]` = 143건·72건 같은 대량 인자를 한 줄에 넘길 때의 셸 인자 길이 한계. **실행 시 측정한다.**

## 5. 로그인 화면 실측

- 주소 = dev CloudFront 배포본(시나리오 2절과 같은 주소). 루트 응답 = **HTTP 200**.
- 문서 제목 = `Co-Lab`. 화면 제목 = 「로그인」. 안내문 = 「운영자에게 받은 이메일과 초기 비밀번호를 넣어 주세요.」 — **시나리오 2절 문면과 일치**.
- 화면 갈무리 = 「세션 스크래치」의 `login.png`(17,520 B · 1280×577).

### 상호작용 요소 (`snapshot -i` 실측 축자)

| 참조 | 종류 | 이름 | DOM | 상태 |
|---|---|---|---|---|
| `@e2` | combobox | 「화면 테마」 | — | 선택지 3 = 「기기 설정」(선택됨)·「밝게」·「어둡게」 |
| `@e3` | heading | 「로그인」 | — | `level=1` |
| `@e4` | textbox | 「이메일」 | `id="accountName"` · `type="text"` · `autocomplete="username"` | `name` 속성 없음 |
| `@e5` | textbox | 「비밀번호」 | `id="password"` · `type="password"` | `name` 속성 없음 |
| `@e6` | button | 「들어가기」 | `type="submit"` | **`disabled`** — 두 칸이 차기 전에는 눌리지 않는다 |

- ⭑ **입력 `name` 속성이 없다** — 자동화는 `data-testid`(`login-account-name`·`login-password`·`login-submit`) 또는 `id` 로 지목한다. 참조 번호는 스냅샷마다 바뀌므로 근거로 삼지 않는다.
- 실패 문구 자리 = `login-error`(`role="alert"`).

## 6. DOM 지목점 — 시나리오 단계별

- 레포 전체 `data-testid` = **468건**. 시나리오가 밟는 화면은 대부분 덮인다.

| 시나리오 단계 | 화면·경로 | 지목점 | 안정성 |
|---|---|---|---|
| 2절 로그인 | `/` | `login-account-name` · `login-password` · `login-submit` · `login-error` | 고정 |
| 2절 첫 비밀번호 변경 | 같은 자리 | `new-password` · `confirm-password` · `change-password` · `password-relogin` | 고정 |
| 2절 진입 대기 | — | `auth-pending` | 고정 |
| 3절 계정 화면 | `/account-admin` | 라우트 존재 확인. 칸 단위 지목점 미확인 | **실행 시 확인** |
| 4절 프로젝트 생성 진입 | `/projects` | 여는 버튼 = 문구 「+ 새 프로젝트」(클래스 `pj-new` · **testid 없음**) | 문구 지목 |
| 4절 프로젝트 모달 | 모달 | `project-form-modal` · 오류 `project-form-error` · 안내 `project-form-scope-note` · 유형 고정표시 `project-form-type-fixed` · 연결 주소 묶음 `project-form-link-group` | 고정 |
| 4절 프로젝트 칸 | 모달 안 | **칸에 `data-testid` 가 없다.** `id` 접미 = `-type`(유형 · 버튼 묶음)·`-name`(이름)·`-desc`(설명)·`-start`／기간 둘째 칸·`-link`(연결 주소). 접두는 모달이 만드는 `titleId` 라 **고정값이 아니다** | **라벨로 지목**(`find label 이름`) |
| 5절 업로드 진입 | GNB | `gnb-upload`(`aria-label="업로드"`) | 고정 |
| 5절 업로드 모달 | 모달 | `upload-modal` · `upload-backdrop` · `upload-close` · `upload-lab` · 닫기 확인 `upload-close-confirm`·`upload-close-forget` | 고정 |
| 5절 **본문 파일 고르개** | ① 분류 | ⭑ **`up-drop-input`** — `<input type="file" multiple>` · 숨김 인풋. 놓는 자리 = `up-drop` · 목록 `up-files`·`up-bundle`·`up-slices`·`up-companion` | 고정 |
| 5절 다중 선택 | 같은 자리 | **`multiple` 성립.** ⚠ **폴더는 끌어다 놓아야만 된다** — 주석 축자 「인풋에 `webkitdirectory` 를 붙이면 낱개 파일 선택이 죽는다」. `upload` 명령은 **낱개 파일 나열**이므로 이 제약을 비껴간다 | 고정 |
| 5절 분석·전송 상태 | 모달 | `up-analyze` · `up-analyze-chip` · `up-analyze-spinner` · `up-analyze-elapsed` · `up-transfer-progress` · `up-transfer-percent` · `up-transfer-eta` | 고정 |
| 5절 실패 판정 | 모달 | `up-status-error` · `up-status-retry` · `up-analysis-failure` · `up-intake-error` · `up-intake-retry` | 고정 |
| 5절 **격자 파일 고르개** | 기준 격자 블록 | ⭑ **`up-grid-input`** — 본문 인풋과 **별개**의 `<input type="file" multiple>`. 여는 이름표 = `up-grid-pick`(문구 「격자 파일 올리기」／거절 뒤 「다른 파일 올리기」) | 고정 |
| 5절 격자 건너뛰기 | 같은 블록 | `up-grid-skip`(문구 「건너뛰기 — 나중에 올릴게요」) | 고정 |
| 5절 격자 판정 | 같은 블록 | `up-grid-block` · `up-grid-accept` · `up-grid-flip` · `up-grid-cancel` · `up-grid-mismatch` · `up-grid-expected-bounds` · `up-grid-detail` · 부착 게이트 `grid-attach-gate`·`grid-attach-confirm`·`grid-attach-cancel`·`grid-attach-error` | 고정 |
| 5절 이름·설명 | ② 메타데이터 | `reg-name`(이름) · `reg-summary`(설명) · 오류 `reg-name-error`·`reg-summary-error` | 고정 |
| 5절 분류 | ② | `reg-category` · `reg-datatype` · `reg-level` | 고정 |
| 5절 기간·간격 | ② | `reg-period-open` · `reg-interval-value` · `reg-interval-unit` · `reg-period-preview` · `reg-crs` · `reg-grid-description` | 고정 |
| 5절 프로젝트 연결 | ② 「연관 프로젝트·논문」 | ⭑ **`reg-proj-select`**(`<select>`) ＋ 더하기 버튼(문구 「추가」 · **testid 없음**) · 표 `reg-proj-table` · 중복 `reg-proj-dup` · 없음 `reg-proj-none` | 혼합 |
| 5절 모달 안 프로젝트 생성 | ② 아래 | `reg-proj-quick-open`(문구 「+ 새 프로젝트 만들기」) → `reg-proj-quick`(유형 `<select>` 2선택지 「국가과제」·「논문」 ＋ 이름 `<input>` · **둘 다 `aria-label` 로만** 지목) · 오류 `reg-proj-quick-error` | 혼합 |
| 5절 공개 범위 | ② | `reg-visibility` · `reg-visibility-slot` · 등록 게이트 `reg-gate`·`reg-viewonly`·`reg-open`·`reg-open-why` | 고정 |
| 5절 **등록 확정** | ③ | ⭑ **`reg-done`** — 문구 「데이터셋 만들기 →」／전송 중 「저장 중…」. ⚠ **자기 Lv 를 넘는 연결이 남으면 `disabled`** | 고정 |
| 6절 **부모 직접 고르기** | ③ 연결(`LineageStep`) | ⭑ **`lin-add`**(문구 「앞 데이터 직접 추가」) → 고르개 `lin-picker` → 행 **`lin-pick-<datasetId>`** · 층 거르개 `lin-lv-filter` · 더 보기 오류 `lin-load-more-error` | 고정(행은 데이터셋 id 파생) |
| 6절 AI 제안 | 같은 자리 | `lin-ask`(문구 「AI 제안 받기」／재요청 「AI 제안 다시 받기」) · 안내 `lin-ask-note` | 고정 |
| 6절 제안 판정 | 같은 자리 | `lin-card` · `lin-confirm` · `lin-reject` · `lin-edit` · `lin-rationale` · `lin-confidence` · `lin-role` · `lin-method` · `lin-method-card` | 고정 |
| 6절 부모 없음 | 같은 자리 | `lin-empty` · `lin-unknown` · `lin-unknown-check` · `lin-unknown-why` | 고정 |
| 6절 충돌 판정 | 같은 자리 | `lin-conflict-note` · `lin-lv-mismatch` · `lin-scope` · `lin-lv-scope` · `lin-need-check` | 고정 |
| 7절 데이터셋 계수 | `/datasets` | **`data-testid` 가 `dl-error` 하나뿐이다.** 목록 행·계수의 지목점 없음 | **실행 시 확인** |
| 7절 미리보기 렌더 | `/datasets/:datasetId` | `dataset-preview` · `preview-target-file` · `preview-source-grid` · **`preview-unavailable`**(렌더 실패 판정에 그대로 쓸 수 있다) | 고정 |
| 7절 프로젝트 목록 | `/projects` | `project-empty` 하나 | **실행 시 확인** |

- 라우트 실측(`frontend/src/app/routes.tsx`) = `/` → `/lab` 이동 · `/lab` · `/projects` · `/projects/:projectId` · `/datasets` · `/datasets/search` · `/datasets/:datasetId` · `/lab-settings` · `/account-admin`. **시나리오 2·3·4·5·7 절의 경로 표기와 일치**.
- ⭑ **`LV-2`(자동 조회를 버튼으로 바꾸기)가 이 워크트리 코드에는 이미 서 있다** — `LineageStep.tsx` 의 `lin-ask` 가 제안 조회를 사용자 클릭에서만 부르고, 주석 축자 「`LV-2` — **부르는 주체가 사용자다.** 호출은 업로드 1건당 1회가 아니라 누른 횟수만큼」. `CLAUDE.md` 의 「화면은 지금도 자동으로 부른다 · `LineageStep.tsx:90`」 표기와 어긋난다. **대장 대조가 필요하다**(이 문서는 판정하지 않는다).

### 덮임 계수

- 시나리오가 밟는 단계 **26** 기준 —
  - **고정 지목점 있음 = 20** (로그인 3 · 업로드 모달·파일·격자·메타데이터·확정 11 · 계보 5 · 미리보기 1).
  - **혼합**(일부만 덮임 · 라벨·문구 지목 병용 필요) = **3** — 프로젝트 생성 모달 칸 · 프로젝트 연결 더하기 버튼 · 모달 안 프로젝트 빠른 생성.
  - **실행 시 확인** = **3** — 계정 관리 화면 칸 · `/datasets` 목록 계수 · `/projects` 목록 계수.

### 시나리오가 `[미확인 · 실행 시 화면에서 확인]` 로 남긴 것

- **로그인 뒤에만 확인된다.** 이번 측정은 로그인을 하지 않았으므로 아래는 전부 미측정이다.
  1. 프로젝트 4건의 **유형** 선택값(「국가과제」／「논문」) — 정본에 지정이 없다.
  2. 순번 8~11(`HLS_S30_NDVI_mean_202305`·`DEM`·`Aspect`·`LULC_2023`)의 **기준 격자 부착 여부**.
  3. core-api 이미지 안 `psql` 가용 여부(1절 · 화면 밖).

## 7. 남은 물음

1. **이 도구를 시나리오 실행에 쓸 것인가** — 시나리오 머리말이 「브라우저 자동화 도구는 이 회차 범위 밖」(라운드 결정 14)이라 적었다. 이 문서는 **능력만 확인**했고 결정을 바꾸지 않는다. 사용하려면 그 결정부터 고친다.
2. **대량 인자 한계** — 143건을 한 `upload` 줄에 넘길 때 셸 인자 길이가 버티는가. 미측정.
3. **혼합·미확인 6단계의 지목 수단** — 프로젝트 모달 칸은 `id` 접두가 실행 시 생성값이라 라벨 지목으로 가야 한다. 목록 계수 2건은 지목점이 없어 화면 문구·행 세기로 대신한다. 안정적 자동화가 필요하면 `data-testid` 추가가 선행이다.
4. **`LV-2` 표기 어긋남** — 6절 끝 항목. 대장 `dev-package/work-items.yaml` 과 대조가 필요하다.
5. **비밀 취급** — 이 측정은 자격을 쓰지 않았다. 실제 구동에 쓴다면 비밀번호를 argv 에 싣지 않는 경로(`set credentials`·표준입력·`--profile` 재사용)를 먼저 정한다.

## 8. 근거

- 도구 = `agent-browser --help` · `agent-browser skills get core --full` · `agent-browser doctor` · `agent-browser upload --help` · `agent-browser snapshot --help` (측정 로그 자리 = 「세션 스크래치」).
- 화면 = `snapshot -i` · `get attr` · `screenshot`(「세션 스크래치」의 `login.png`).
- 코드 = `frontend/src/auth/LoginPage.tsx` · `frontend/src/auth/PasswordChangePage.tsx` · `frontend/src/app/routes.tsx` · `frontend/src/components/upload/FileDropCard.tsx` · `GridUploadBlock.tsx` · `RegisterArea.tsx` · `UploadModal.tsx` · `UploadEntry.tsx` · `frontend/src/components/lineage/LineageStep.tsx` · `ParentPicker.tsx` · `frontend/src/components/project/ProjectFormModal.tsx` · `frontend/src/routes/ProjectsPage.tsx` · `DatasetsPage.tsx` · `frontend/src/components/datasetpreview/DatasetPreviewSection.tsx`.
- 시나리오 = `dev-package/scenarios/dev-minimal-data-setup.md §2`~`§7`.
