# R-BUGFIX-260912 — GitHub 이슈 10건 버그·개선 묶음

- 회차 성격 = frontend 결함 수정 3 레인 ＋ 읽기 전용 실측 1 레인. 계약 변경 0 · 마이그레이션 0 · 서버 코드 변경 0.
- 통합 브랜치 = `integration/r-bugfix-260912` · 기점 HEAD = 스폰 지시문에 기재된 값(이 파일을 담은 커밋 이후의 통합 브랜치 tip).
- 입력 intent 4건(승인 2026-09-12 · 커밋 `567b830`) = `dev-package/intent/2026-09-12-issue-{upload-resume-discard,upload-analysis-notice,preview-controls,register-hints-parent-picker}.md`.
- 상세 명세 4건(레인별 1개씩) = `dev-package/prd/specs/2026-09-12-issue-{upload-resume-discard,upload-analysis-notice,preview-controls,register-hints-parent-picker}.md`.
- 판정 정본 = `dev-package/reports/issues/2026-09-12-ted-decisions.md` 11건(Ted · 2026-09-12 · 확인 문장 「좋아 전부권고안으로」).
- 조사 정본 = `dev-package/reports/issues/2026-09-12-survey-SUMMARY.md` §3(레인 분할·충돌) · §5(미확인 18건).
- 레인은 이 파일 ＋ 자기 spec 1건만 읽는다. `03-HANDOFF.md`·`PLAN-SoT.md`·`work-items.yaml` 은 열지 않는다.

## 목표와 완료점

- 목표 = GitHub 이슈 10건 중 판정으로 열린 항목을 기존 화면·기존 흐름 위에서 고치고, 판정에 필요한 두 소요값을 실측한다.
- 대상 이슈 = `#33`㉠ · `#34` · `#32` · `#24`㉯ (L1) / `#31` (L2) / `#26` · `#25`⑵ · `#27` · `#28` (L3) / `#24`㉮ · `#25`⑴ · `#29`⑴ · `#30`㈎ (L4 실측·재현).
- 범위 밖(명시) = `#33`㉡ 접수 완료분 등록 장면 복원 · 서버 즉시 삭제 창구 · 미리보기 고정 배치 재설계 · 「이미지에서 고르기」 · `#30` 화면 형태 재구성 · `#29`⑵ 수정 · `#31` 문면 삭제.
- 완료점 4 —
  1. L1·L2·L3 각 레인이 단독 게이트 green(아래 레인 표의 게이트·횟수 그대로).
  2. 통합 브랜치 트리에서 전수 게이트 1회 green(red 판정 0 · red 준비 0).
  3. L4 보고서 `dev-package/reports/issues/2026-09-12-measure-L4.md` 인계 완료.
  4. `#24`㉮·`#25`⑴ 소요 합격선을 Ted 가 지정하고 그 값이 원장 행에 기재된다.
- 완료점 4 는 이 회차 안에서 닫히지 않을 수 있다 — 값 회수까지가 이 회차의 책임이고, 합격선 미지정이면 `#24`㉮·`#25`⑴ 은 후속 항목으로 남긴다(수정 착수는 이번 회차 밖).
- 배포는 이 회차 레인의 일이 아니다 — 마감 조건으로만 기재한다(아래 「병합·원장」 6단계).

## 실행 순서

| 단계 | 작업 | 주체 | 의존 | 완료 근거 |
|---|---|---|---|---|
| 0 | 라운드 파일 작성 · 레인 절단 고정 | 오케스트레이터 | intent 4건 승인 | 이 파일 |
| 1 | L1·L2·L3·L4 동시 착수 | 레인 4 | 0 | 각 레인 최종 메시지 |
| 2 | 단독 게이트 green 회수 | 레인 3 | 1 | `gate-summary.json` 3계수 |
| 3 | 병합 L2 → L3 → L1 (rebase ＋ ff) | 오케스트레이터 | 2 | 통합 브랜치 로그 |
| 4 | 전수 게이트 1회 | 오케스트레이터 또는 `gate-runner` | 3 ＋ 실행 레인 0건 | 전수 요약줄 |
| 5 | 원장·대장·HANDOFF 기재 | 오케스트레이터 | 4 | 커밋 |
| 6 | `main` ff → dev 배포 ＋ `deploy_doctor` 15/15 한 번의 실행 | 오케스트레이터 | 5 | 배포 로그 |

## 레인 표

| 레인 | 에이전트 | 브랜치 | 범위 | 단독 게이트 | 주 수정 파일 |
|---|---|---|---|---|---|
| L1 업로드 모달 | `lane-worker` | `lane/bugfix-upload-modal` | spec I-1 전건(`#33`㉠ → `#34` → `#32`) ＋ spec I-2 의 `#24`㉯ 고지 | `frontend-test` 연속 2회 green ＋ `frontend-typecheck` 1회 | `frontend/src/components/upload/{UploadEntry,UploadModal,UnfinishedUploads}.tsx` · `pendingStore.ts` · `frontend/src/components/common/toastCopy.ts` · `upload.css`(끝 덧붙임 블록만) |
| L2 등록 카드 | `lane-worker` | `lane/bugfix-register-hints` | spec I-4 의 `#31` 한 건(설명문 순서 통일) | `frontend-test` 연속 2회 green | `frontend/src/components/upload/RegisterArea.tsx` |
| L3 미리보기 | `lane-worker` | `lane/bugfix-preview-controls` | spec I-3 전건(`#26` → `#25`⑵ → `#27`＋`#28`) | `frontend-test` 연속 2회 green ＋ `frontend-typecheck` 1회 ＋ `frontend-visual`(조건부) | `frontend/src/components/upload/{PreviewPanel,PreviewExpandOverlay}.tsx` · `frontend/src/components/preview/{PreviewPickRow,PreviewZoomControls}.tsx` · `frontend/src/components/datasetpreview/DatasetPreviewSection.tsx` · `upload.css`(기존 규칙) · `preview.css` |
| L4 실측·재현 | `researcher` | `lane/bugfix-measure` | spec I-2 측정(`#24`㉮ ＋ `#25`⑴) ＋ 재현 `#29`⑴ · `#30`㈎ | 게이트 실행 0 | `dev-package/reports/issues/2026-09-12-measure-L4.md` 만 |

- 병렬 = L1 ∥ L2 ∥ L3 ∥ L4 동시 4 레인. 근거 = 수정 파일 집합이 교차하지 않는다. 유일한 교차 `upload.css` 는 L1 의 덧붙임 규칙으로 분리한다.
- `upload.css` 규칙 = L1 은 파일 **끝에 구획 주석으로 감싼 블록 하나만** 덧붙인다(`/* == R-BUGFIX-260912 L1 == */` 시작 · `/* == /R-BUGFIX-260912 L1 == */` 끝). 기존 규칙 줄은 한 글자도 고치지 않는다. L3 은 기존 규칙만 고치고 파일 끝에 덧붙이지 않는다.
- 부하 = 4 레인 동시 실행 중 전수 게이트를 돌리지 않는다. 동시 실행 상태의 게이트는 `-j 2`(`.claude/rules/colab-rules.md §9`).

## 레인 공통 지시

- **첫 줄** = `git checkout -B lane/<이름> origin/integration/r-bugfix-260912`. 이어서 `git rev-parse --short HEAD` 로 스폰 지시문의 기대 HEAD 를 대조하고, 어긋나면 구현하지 말고 정지·보고한다(`.claude/rules/colab-rules.md §2-3` — 워크트리 기본 기준이 `origin/main` 이라 이 한 줄이 없으면 통합 선행분 위에 서지 않는다).
- 스폰 방식 = `isolation: "worktree"`. 손으로 만든 형제 워크트리를 쓰지 않는다.
- 순서 = 항목마다 ① red 시험 먼저(실패 로그 한 줄 인용) → ② 최소 구현 → ③ 단독 게이트. green 으로 시작한 시험은 오라클이 아니다.
- 게이트 실행 = `COLAB_GATE_REPORT_DIR=dev-package/reports/bugfix-260912/<레인> bash gates/run.sh <게이트>`. 배출처를 빠뜨리면 `gate-summary.json` 이 서지 않는다.
- red 판독 = 판정 red / 준비 red(exit 78 · `::gate-readiness-failure::`)를 갈라 적는다. 갈라 적지 않은 계수는 보고에 쓰지 않는다.
- 워크트리 게이트 환경 = `frontend` 는 `npm ci` 를 먼저 돌린다(워크트리는 `node_modules` 를 승계하지 않는다 · `§2-4`).
- 기존 결함 발견 시 「기존」이라 적지 않는다 — 그 결함이 어느 검사(게이트 · Dockerfile · 배포 스크립트 · 없음)에 걸리는지 적고 후속 항목으로 올린다(`§3-3`).
- 새 `.sh` 를 만들면 `git update-index --chmod=+x <파일>` 후 커밋한다(`§4-3`).
- 문서·보고에 절대경로를 적지 않는다. 행 번호 대신 앵커 문자열(함수명 · 상수명 · `data-testid`)을 쓴다.

## L1 — 업로드 모달 (`lane/bugfix-upload-modal`)

- spec = `dev-package/prd/specs/2026-09-12-issue-upload-resume-discard.md` ＋ 같은 폴더 `…-issue-upload-analysis-notice.md` 의 갈래 ㉯ 절만.
- 착수 순서 4단(직렬 · 같은 파일군이라 병렬 금지) —
  1. `#33`㉠ 재개 배선 — 배너 재개 요청의 재개 식별자를 업로드 진입 컴포넌트가 모달 props 로 전달하고 모달이 무장한다. 기존 경로(`resumeRef` · `resumeFromRef='banner'` · `resumeArm` · `seq` 재무장 규약) 재사용 · 신규 개념 0. red seam = `frontend/test/unfinished-uploads.test.tsx` 에 실물 렌더 시험 1건(컨텍스트 스텁 금지 · 하네스 선례 = `frontend/test/prd34-close-copy-20260907.test.tsx` 의 `UploadEntry` ＋ `SessionProvider` ＋ `MemoryRouter`).
  2. `#34` 닫기 확인의 세 번째 선택지 — 기존 두 버튼(`UPLOAD_CLOSE_KEEP` · `UPLOAD_CLOSE_LEAVE`) 옆에 1개 증설. 뜻 = **이 브라우저의 미완결 기억 삭제**이고 서버 접수 행은 24시간 만료 스윕이 정리한다. 문면이 그 사실을 그대로 말한다. 같은 단계에서 폐기 공통 헬퍼(`discardUpload`)를 추출해 세 자리가 같은 것을 부르게 한다. red seam = `prd34-close-copy-20260907.test.tsx` 에 3건(존재 · 동작 · 문면).
  3. `#32` 메인 배너 행 폐기 버튼 — 위 헬퍼 재사용. 폐기 후 배너가 비면 카드 자체가 사라진다. 등록을 마친 데이터셋에는 닿지 않는다. red seam = `unfinished-uploads.test.tsx` 에 2건(폐기 · 빈 카드).
  4. `#24`㉯ 분석 중 고지 — `다음 →`(대상은 `reg-open` · `reg-next` 아님) 은 **비활성 유지**하고 사유 한 줄과 `title`·`aria-describedby` 연결을 추가한다. 정책 6(분석 완료 전 비활성)과 기존 회귀 기준을 바꾸지 않는다. red seam = `frontend/test/upload.test.tsx` 5건(구현 전 실행에서 실패 5건 로그 보존 · 수집 0건이 아님).
- 문면 취급 = 세 번째 버튼 라벨·본문은 `toastCopy.ts` 에 **초안 상수**로 두고 바로 위에 `// PRD-34 문면표 개정 · Ted 확정 대기` 주석을 붙인다. 개발 세션이 문면을 확정하지 않는다(PRD-34 규칙). 개정 필요 항목 3건(버튼 라벨 줄 · 세 번째 선택지 본문 1행 · 수용 기준 1행)은 레인 최종 메시지에 열거만 하고 `dev-package/prd/PRD-260905-적용전기획.md` 를 고치지 않는다.
- `upload.css` = 배너 폐기 버튼 스타일이 필요하면 **파일 끝 덧붙임 블록** 안에만 쓴다(위 공통 규칙). `.up-banner` 기존 규칙을 고치지 않는다.
- 게이트 = `frontend-test` 연속 2회 green ＋ `frontend-typecheck` 1회. 대조 = 요약줄의 vitest 수집 건수가 착수 전 값보다 6건 이상 증가.

## L2 — 등록 카드 (`lane/bugfix-register-hints`)

- spec = `dev-package/prd/specs/2026-09-12-issue-register-hints-parent-picker.md` 의 `#31` 절만. 같은 spec 의 `#30` 재현은 L4 몫이다.
- 내용 = 등록 카드 기간 칸의 안내 문단을 달력 열기 버튼 뒤로 옮겨 카드 안 배치를 **라벨 → 컨트롤 → 설명문** 하나로 통일한다. 근거 = 카드 안 안내 문단 4건 중 3건이 이미 컨트롤 뒤이고, PRD-40 은 앞/뒤를 지정하지 않는다.
- 수정 = `frontend/src/components/upload/RegisterArea.tsx` 의 JSX 순서 이동 1건. 문면 상수 · `data-testid` · 클래스명 **무변**(문면 삭제는 범위 밖 — Ted 판정 목록에 없다).
- 스타일시트 미접촉 — `upload.css` 를 열지 않는다. `.fieldnote` 는 `margin-top` 만 두므로 DOM 순서 변경으로 화면 순서가 바뀐다.
- red seam = `frontend/test/register-steps-20260907.test.tsx`(묶음 `㈒ PRD-40 종료 비움` 이 같은 문단을 이미 문면으로 검사한다). 순서 단언을 같은 파일에 붙인다.
- 부모 찾기 모달 · 조회 훅 · 계보 후보 조회 경로는 읽기 전용. 이 레인 변경 0.
- 게이트 = `frontend-test` 연속 2회 green.
- 규모 추정 = 8~15행(추정치 · 실측 아님).

## L3 — 미리보기 (`lane/bugfix-preview-controls`)

- spec = `dev-package/prd/specs/2026-09-12-issue-preview-controls.md`.
- 착수 순서 3단(직렬 · 같은 파일군) —
  1. `#26` 64×64 축소본 이동 — 지도 자리(`.mapcanvas`)에서 빼고 접히는 자리(`up-preview-options` details 안 · `up-thumb-img` 옆)로 옮긴다. 결정 `〈88〉`-3 의 표시 목적을 유지하고 지도 위 중복만 제거한다(Ted 판정 ⑤ ⓑ · 재판정 기록 대상).
  2. `#25`⑵ 고르개 줄을 틀 밖으로 — 파일·변수·시각 고르개 줄을 `.pv-frame` 바깥 고정 줄로 옮긴다. 대상은 그 줄을 소유한 **두 화면**뿐 — 업로드 인라인(`PreviewPanel.tsx`) · 상세(`datasetpreview/DatasetPreviewSection.tsx`). **확장 오버레이에는 고르개 줄을 만들지 않는다.** 규약 `R-C-2` 개정 기록 대상(Ted 판정 ⑥).
  3. `#27`＋`#28` 확대 줄 접힘·가림 해소(한 단계) — 인라인에서 확대 줄이 스크롤 없이 보이게 하고, `.modal-b.pvx-b` 의 flex 방향과 `.pv-layers .pv-tile` 폭 상한으로 가림을 없앤다. **고정 배치 재설계는 범위 밖**(Ted 판정 ⑦ ⓐ 「접힘·가림 해소까지만」).
- 배치 판정 방법 = jsdom 이 레이아웃을 계산하지 않으므로 ㈎ DOM 조상·형제 관계 ㈏ CSS 원문 계측 두 가지로 세운다. 계측기는 주석을 제거한 뒤 잰다. 선례 = `frontend/test/design-fix-20260908.test.ts` · `frontend/test/css-residual-rc11.test.ts` · `frontend/test/preview-slot-4x3.test.tsx` 머리 주석.
- 재사용 시험 파일 = `frontend/test/{preview-slot-4x3,preview-pick-and-fallback,scale-ladder,dataset-preview-zoom,upload,grid-preview,thumb-nudge-20260905}.test.tsx`. Playwright 를 새로 들이지 않는다.
- `upload.css` = 기존 규칙만 고친다. 파일 끝에 새 블록을 덧붙이지 않는다(L1 자리).
- 게이트 = `frontend-test` 연속 2회 green ＋ `frontend-typecheck` 1회. `frontend-visual` 은 이 세 화면 주소를 `COLAB_VISUAL_URLS` 로 선언할 수 있을 때만 1회 실행하고, 선언 불가면 실행하지 않고 그 사실을 보고에 적는다(미선언 실행은 red(준비)).
- `#29`⑴ 재현은 이 레인이 아니라 L4 가 한다.
- 규모 추정 = 소스 65~135행 ＋ 시험 3묶음(추정치 · 실측 아님).

## L4 — 실측·재현 (`lane/bugfix-measure`)

- spec = `dev-package/prd/specs/2026-09-12-issue-upload-analysis-notice.md` 갈래 ㉮ ＋ `…-issue-register-hints-parent-picker.md` 의 `#30`㈎ 절.
- 성격 = **읽기 전용**. `frontend/**` · `services/**` · `contracts/**` · 게이트를 건드리지 않는다. 계측용 로그 추가 0. 게이트 실행 0. 산출은 보고서 1건뿐이다.
- 대상 업로드 = `gk2a_ami_le2_lst_ko_202005010000.nc` 계열 · 조각 141 · 합계 48 MB · 산출물 LST. 조각 표본 1 · 10 · 141 세 벌.
- 측정 두 구간(같은 업로드에서 연속) —
  - ㉠ 워커 분석 = 접수 수락 시각 → 분석 완료(`ready` 참) 시각.
  - ㉡ viz 렌더 = 렌더 요청 시각 → 그림 표시 시각.
- 단계별 시각을 함께 남긴다 — 순차 자재화 루프 · 형식 판별 · 워커 폴링 고정 지연 · 화면 상태 폴링 주기. 앵커 = `services/pipeline-worker/src/colab_pipeline/app/worker.py` 함수 `drive_uploads`(참조 1건마다 `blobs.materialize`) · 같은 파일 함수 `serve`(`interval_seconds: float = 5.0`) · `services/pipeline-worker/src/colab_pipeline/d5/detect.py` 함수 `detect_format` · `frontend/src/components/upload/UploadModal.tsx` 상수 `STATUS_POLL_MS = 1000`.
- 값의 출처 = 기존 워커 표준출력 이벤트 · 브라우저 네트워크 기록 · 벽시계. 방법과 환경을 보고서에 함께 적는다.
- 함께 기록 4 —
  - 상태 조회 오류 경로(재시도) 발생 여부·횟수. 앵커 = 같은 모달의 실패 시 재시도 분기(`STATUS_POLL_MS * failures`).
  - `createRender` 호출 횟수와 미리보기 컴포넌트 재마운트 발생 여부. 열쇠 = `UploadModal.tsx` 의 미리보기 `key` 산식(서명 · 미리보기 업로드 id · 격자 개정 3항 결합).
  - `#29`⑴ 확장보기 기간 라벨 겹침 — 확장보기를 열고 뷰포트 폭 1023px 초과·이하 두 벌에서 겹침 여부를 본다. **촬영 시 뷰포트 폭을 반드시 기록한다**(1열 접힘 여부가 판정 입력).
  - `#30`㈎ 부모 찾기 창 결과 0행 — 절차 = 로그인 → 업로드 등록 ③ 계보 단계 → 「가공 전 데이터 직접 찾기」 모달 → 필터 전부 비운 상태 1회 · 분류·주제 각 1값 1회 · 가공 단계 필터 1회. 선행조건 = 같은 연구실에 등록 완료 데이터셋 2건 이상(1건 이상은 등록 중인 자신이 아닐 것) — 데이터셋 목록 화면 건수로 먼저 확인. 기록 = 요청 질의 파라미터 전부 · 응답 본문(행 수 · 다음 커서) · 빈 상태 문면 두 갈래 중 어느 쪽 · 요청 주체의 연구실 식별자와 같은 주체의 목록 건수 · 자기 제외 파라미터 전달 여부와 값 · 등록 중 데이터셋의 가공 단계 기준값.
  - `#30` 판정 규칙 = 후보가 실재하는데 0행이면 조회 결함 ⟹ 신규 `BF-` 항목 등재 대상으로 **보고만** 한다. 후보 부재 · 필터가 결과를 비운 것 · 자기 제외로만 0행이면 사용법으로 닫고 등재하지 않는다. 연구실 경계(RLS) 동작은 관찰만 하고 바꾸지 않는다.
- 환경 선택 규칙 —
  - 우선 = **dev**. 조건 = 읽기 위주로 접근 가능할 것. 업로드 1건은 24시간 만료되는 접수 행을 만들고 **데이터셋으로 등록하지 않는다**. 시험용 연구실을 쓴다.
  - 대안 = 로컬 `docker compose`. 절차는 `docs/DEPLOY.md` · `dev-package/RESTART.md` 를 따른다.
  - 고른 환경과 그 이유를 보고서 첫 절에 적는다. 두 환경의 값을 섞지 않는다.
- 합격선은 이 레인이 정하지 않는다 — 값 회수 뒤 Ted 지정. `PLAN-SoT §9 〈241〉` 의 p95(대상 NDVI · 분포 통계)와 `gates/config/render-latency.toml` 눈금(서비스 시험 표본)을 합격선으로 유도하지 않는다.
- 배출물 = `dev-package/reports/issues/2026-09-12-measure-L4.md` 1건. 재지 않은 것은 `[미확인]` 로 적는다.

## 하지 말 것

- 게이트 우회·비활성화 · green 을 만들려고 검사 대상 축소 · 준비 red 를 green 으로 계수.
- 자기 spec 범위 밖 수정(범위 밖 목록은 「목표와 완료점」 3번째 항목).
- `upload.css` 를 규칙 밖으로 편집 — L1 은 파일 끝 구획 블록만, L3 은 기존 규칙만, L2 는 접촉 0.
- 문면 확정 — 세 번째 버튼 라벨·본문은 초안 상수 ＋ 대기 주석까지. PRD 문면표를 레인이 고치지 않는다.
- 원장·대장 편집 — `dev-package/work-items.yaml` · `dev-package/03-HANDOFF.md` · `dev-package/PLAN-SoT.md` 를 레인이 열지 않는다. 등재문은 자기 회차 파일에 적는다.
- 원장 번호 `〈N〉` 하드코딩 · 예약.
- `main`/`master` push · `gh pr merge` · 브랜치 병합 · 충돌 해소(오케스트레이터 몫).
- 레인 안에서 전수 게이트(`gates/run.sh all`) 실행 · 워크트리 하나에서 전수 두 벌 동시 실행.
- 요청되지 않은 시험 파일 신설 · 임시 스크립트 커밋 · 파일 전체 재작성.

## 보고 형식 (레인 최종 메시지 · ≤15행)

```
결론 = <레인 범위 항목별 완료/미달 한 줄씩>
게이트 = <게이트명> green N / red(판정) N / red(준비) N  (요약줄 축자 1행)
게이트 = <게이트명> …                                      (실행한 게이트마다 1행)
로그·요약 = dev-package/reports/bugfix-260912/<레인>/gate-summary.json
red 선실측 = <시험 파일 · 실패 건수 · 실패 로그 한 줄 인용>
원한 결과 대조 = 미달 <n>건 / 초과 <n>건 (각 한 줄)
남은 위험 = <항목 또는 없음>
후속 항목 = <발견한 기존 결함과 그것이 걸리는 검사 이름 · 없으면 0건>
COLAB_HANDOFF=<lifecycle-evidence handoff 가 낸 한 줄>
WORKTREE=<경로> BRANCH=<브랜치>
```

- 개조식 · 정성어 배제 · 기술 용어에 비유 금지 · 절대경로 금지. 계수를 낼 때 계수 기준을 함께 적는다.
- L4 는 게이트 줄 대신 `게이트 = 실행 0(읽기 전용 레인)` 과 보고서 경로를 적는다.

## 격리·변경 관리

- 레인은 전부 `isolation: "worktree"` 로 스폰하고 하네스가 만든 워크트리·브랜치를 쓴다. 자기 워크트리 밖 경로를 편집하지 않는다.
- 한 사본의 쓰기 주체는 하나. L4 는 코드 사본을 쓰지 않는 읽기 전용 레인이다.
- 병합·push·배포 완료를 이 라운드 파일 작성과 혼동하지 않는다.
- 병합된 `lane/*` 워크트리·브랜치는 즉시 정리한다 — `git worktree remove` ＋ `git worktree prune` · `git branch -d` · `git push origin --delete`(`.claude/rules/colab-rules.md §2-1`).
- 회차 산출물 폴더 = `dev-package/reports/bugfix-260912/` (게이트 요약) · `dev-package/reports/issues/` (L4 보고서) · `dev-package/sessions/` (등재문 초안).

## 병합·원장

- 병합 순서 = **L2 → L3 → L1**. 근거 = L2 가 가장 작고 `upload.css` 미접촉이며, `upload.css` 를 만지는 둘 중 기존 규칙을 고치는 L3 을 먼저 얹어 L1 의 파일 끝 덧붙임 블록이 충돌 없이 rebase 되게 한다. L4 보고서는 순서 무관.
- 복귀 방식 = 각 레인 브랜치를 `integration/r-bugfix-260912` 위로 rebase 한 뒤 ff. 레인은 자기 브랜치까지가 끝이고 병합은 오케스트레이터가 한다.
- 전수 게이트 = 병합 완료 후 통합 트리에서 **1회**. 다른 실행 레인이 남아 있으면 `-j 2`, 전부 종료했으면 `-j 4`. 실행 전 `set -a; . ~/.colab-v2-test.env; set +a`.
- 원장·대장 기재(오케스트레이터 직렬) —
  - `dev-package/work-items.yaml` = 기존 관행대로 **`BF-<n>` 개별 항목**을 쓴다(실측 = 현재 `BF-1` ~ `BF-13` 존재 · 번호는 병합 직전 재실측). 블록 모양은 기존 `BF-` 항목의 키 순서(`id` · `name` · `status` · `stage` · `owner` · `entry_conditions` · `depends_on` · `completion_def` · `evidence` · `deadline` · `note` · `sources`)를 그대로 따른다.
  - `dev-package/03-HANDOFF.md §1` = 해당 항목 상태 갱신 ＋ 상단 최종 갱신·현재 단계·다음 WU.
  - `dev-package/PLAN-SoT.md §9` = 결정 행 발급(번호는 `dev-package/prd/tools/max-decision.sh` 로 병합 직전 재실측 · 예약 금지). 기재 대상 4 = ⑤ 축소본 지도 자리 밖 이동(재판정) · ⑥ `R-C-2` 고르개 자리 규약 개정 · PRD-34 문면표 개정 · Ted 판정 11건 기록.
  - `CLAUDE.md §0` 세 번째 단 괄호 목록은 **새 `after_stage2` 항목이 실제로 생길 때만** 갱신한다(`#11` 등재 시 · 대장 id 제안 `PA-T` — 조사 D). 게이트 `work-item-consistency` ㈕ 가 대조한다.
  - 상태 변경은 대장을 먼저 고치고 산문을 그 반영본으로 갱신한다.
- 마감 조건(이 회차 레인 밖) = `main` ff → dev 배포 green ＋ `deploy_doctor` 15/15 를 **한 번의 실행으로**. 재시도해 모은 15 는 15 가 아니다.
- 후속 항목으로 남을 수 있는 것 = `#24`㉮·`#25`⑴ 수정(합격선 Ted 지정 뒤) · `#33`㉡ 설계 · `#30` 화면 형태 재구성 · `#31` 배치 규약의 정책 문서 기재 · L4 가 조회 결함으로 판정한 신규 `BF-` 항목.
