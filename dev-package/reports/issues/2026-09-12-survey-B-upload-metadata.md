# 조사 B — 업로드 메타데이터 탭·레이아웃 (이슈 #31 · #24)

- 조사 기준 커밋: `10a3fb8` (작업 사본 HEAD `1f1f58b` = `10a3fb8` ＋ 이슈 회수 파일)
- 작성자: researcher
- 승인: 미승인
- 입력: `dev-package/reports/issues/2026-09-12-github-open-issues.md` `## #31`·`## #24`
- 스크린샷: 이슈 첨부 2건 열람 완료(#31 1건 · #24 1건)
- 참조: 형제 체크아웃 조사본 2026-09-12 upload-download-inventory (행 번호는 다른 브랜치 기준이라 인용하지 않음)

---

## #31 — 메타데이터 입력 탭 설명문 위치 불일치

### 1. 이슈 요지
- 사용자 행위: 업로드 모달 → 「다음 →」 → 등록 카드 2단계(메타데이터 입력)에서 세 칸(`기간`·`좌표계`·`격자 설명`)을 본다.
- 관측: 설명문이 어떤 칸은 **라벨 바로 아래·입력 컨트롤 위**, 어떤 칸은 **입력 컨트롤 아래**에 위치한다.
- 스크린샷 실물: `기간 (조각 합집합) (선택)` 라벨 아래에 「한 시점이면 비워 둬요」가 오고 그 아래 `달력에서 고르기` 버튼. `격자 설명 (선택)` 은 textarea 아래에 「자동 판독과 별도로 연구자가 설명을 남겨요.」.

### 2. 재현 경로
| 단계 | 내용 | 근거 |
|---|---|---|
| 1 | 업로드 모달 열기 → 파일 놓기 → 분석 완료 대기 | 코드에 존재 (`UploadModal.tsx` · `data-testid="up-analyze"` 블록) |
| 2 | `다음 →`(`data-testid="reg-open"`) 클릭 → 등록 카드 열림, `setStep(1)` | 코드에 존재 (`UploadModal.tsx` · `reg-open` 핸들러) |
| 3 | 단계 표시기 ② 클릭 → 메타데이터 입력 | 코드에 존재 (`frontend/test/register-steps-20260907.test.tsx` `stepBtn('②')`) |
| 4 | 3열 행(`data-testid="reg-short-row"`) 관측 | 코드에 존재 (`RegisterArea.tsx` · `className="form-3"`) |
| 관측 | 기간 칸 = 설명문이 컨트롤 위 / 좌표계 = 설명문 없음 / 격자 설명 = 설명문이 컨트롤 아래 | 코드에 존재 |
| 기대 | 한 칸 안에서 설명문 위치가 한 규약으로 고정 | 규약 문서 부재 — 「미확인」 |

### 3. 관련 코드 앵커 (행 번호 없음)
- `frontend/src/components/upload/RegisterArea.tsx`
  - 앵커 `export const PERIOD_SINGLE_POINT_HINT = '한 시점이면 비워 둬요'` — 문면 상수.
  - 앵커 `data-testid="reg-short-row"` 를 가진 `<div className="form-3">` — 3열 격자 행. 그 안의 세 `<div className="form-row">` 각각이 JSX 로 손수 작성돼 있다.
  - 앵커 `data-testid="reg-period-single-hint"` — `<label htmlFor="reg-period-open">` **다음**, `<button id="reg-period-open">` **앞**에 위치.
  - 앵커 `자동 판독과 별도로 연구자가 설명을 남겨요.` — `<textarea id="reg-grid-description">` **다음**에 위치.
  - 앵커 `data-testid="reg-visibility-note"` — `<select id="reg-visibility">` 다음(컨트롤 아래).
  - 앵커 `data-testid="reg-summary-hint"` — `form-row` **바깥**(칸 밖 문단).
  - 앵커 `data-testid="reg-datatype-note"` (`className="axis-note muted"`) — 셀렉트 + `AxisDefLine` 다음.
- `frontend/src/components/upload/upload.css`
  - 앵커 `.fieldnote{margin-top:5px;` — 위치를 결정하지 않는 여백 규칙만 있다(`margin-top` 만). 순서는 전적으로 JSX DOM 순서.
  - 앵커 `.form-row { display: flex; flex-direction: column;` — 세로 흐름이라 DOM 순서 = 화면 순서.
- **잘못된 순서를 만드는 자료구조**: 존재하지 않는다. 설명문 ↔ 필드 결합은 배열 index 도 key 사전도 아니고 **필드마다 인라인 JSX 로 직접 배치**된다. 즉 「순서가 뒤섞이는 로직」이 아니라 **작성 시점의 배치 불일치**다.

### 4. 원인 가설
- 가설 1 (증거: 코드에 존재) — 설명문 배치 규약이 코드에 없고 각 `form-row` 가 개별 작성돼, `reg-period-single-hint` 만 컨트롤 앞에 놓였다. 다른 `fieldnote` 3종은 모두 컨트롤 뒤다.
- 가설 2 (증거: 미확인) — 기간 칸은 값 표시 칸이 없고 버튼 하나뿐이라(주석 앵커 「값 칸이 없다 — 누르면 달력 팝오버가 뜨고」) 안내를 버튼 위에 둔 의도적 배치일 가능성. 그 의도를 적은 판정 문서는 확인되지 않음 — 「미확인」.

### 5. 수정 범위 초안
- 대상 파일: `frontend/src/components/upload/RegisterArea.tsx` 1개(필수). 규약을 CSS 로 고정하면 `frontend/src/components/upload/upload.css` 1개 추가.
- 방향 ⓐ 위치 통일 — `reg-period-single-hint` 를 `reg-period-open` 버튼 **뒤**로 이동(다른 3종과 동일 규약: 라벨 → 컨트롤 → 설명문).
- 방향 ⓑ 설명에서 제거 — 이슈 본문 「설명에서 빼던가」. 다만 문면 자체는 PRD-40 판정 ⓐ 근거(`RegisterArea.tsx` 주석 앵커 「⟨PRD-40 · 판정 ⓐ⟩ 종료는 비울 수 있다. 필수 표시를 걷고 안내 한 줄을 둔다」)라 **삭제는 판정 재개봉**에 해당. 권고는 ⓐ.
- `contracts/` 변경: 없음. DB 마이그레이션: 없음. 동결 해제 서명: 불필요.
- 백엔드: 무관. 프런트엔드 전용.

### 6. red 테스트 후보
- 기존 파일: `frontend/test/register-steps-20260907.test.tsx` (describe 앵커 `㈒ PRD-40 종료 비움` 이 `reg-period-single-hint` 문면을 이미 검사한다).
- 먼저 쓸 실패 테스트: 같은 파일에 「3열 행의 모든 설명문이 자기 칸의 입력 컨트롤 뒤에 온다」 — `reg-short-row` 안의 각 `form-row` 에서 `.fieldnote` 의 `compareDocumentPosition` 이 그 칸의 `input|textarea|button[id^="reg-"]` 보다 뒤임을 단언. 현재 코드에서 기간 칸 1건 실패 예상.
- 보조: `frontend/test/interval-period-20260906.test.tsx` (같은 3열 행을 다루는 기존 시험).

### 7. 겹침·순서 의존
- 같은 파일 `RegisterArea.tsx` 를 쓰는 다른 이슈: 이 그룹 안에는 없음(#24 는 `UploadModal.tsx`).
- 그룹 A(#32·#33·#34) = `UploadModal.tsx` 중심 — `RegisterArea.tsx` 와 파일이 갈리므로 **병렬 가능**.
- 그룹 C(#25~#29) = `PreviewPanel.tsx`·`PeriodCalendarPopover.tsx` — #29(미리보기 달력에서 고르기)가 `PeriodCalendarPopover.tsx` 를 만지면 기간 칸 UI 와 인접하나 파일은 다름. `RegisterArea.tsx` 를 함께 고칠 경우 직렬 필요 — 「미확인」(#29 본문 미조사).
- 그룹 D(#10·#11·#12·#30) = 백로그·로그인·검색. 겹침 없음.

### 8. 범위 판정 후보
- `v2 버그` — 같은 카드 안에서 같은 성격의 설명문이 두 위치로 갈리는 표시 불일치. 추천·스마트 기본값이 아니고 대화형 UI 도 아니다. 최종 판정은 Ted.

### 9. 크기
- 파일 1(＋테스트 1). 변경 행 추정 8~15행 — 근거: 이동 대상은 `<p className="fieldnote" data-testid="reg-period-single-hint">` 3행 블록 1건 ＋ 주석 조정, 테스트 신규 1건 10행 내외.

### 10. 대장 대조
- `dev-package/work-items.yaml` — `id: WU-C8` / `status: done`. `completion_def` 축자 일부: 「인라인 기간 칸 0＋팝오버 1」. 기간 칸이 버튼 하나가 된 근거 항목.
- `dev-package/work-items.yaml` — `id: WU-B4` / `status: done` (공개 범위 3값 · `reg-visibility-note` 소유), `id: WU-B6` / `status: done` (Lv0 출처 칸).
- `dev-package/intent/2026-09-09-upload-layout-preview.md` — 설명문 위치를 정한 문장 **없음**(grep 「설명문」·「fieldnote」·「안내 문구」·「힌트」 무결과, 「기간」은 상세 화면 항목 나열 1건).
- `dev-package/reports/upload-layout-preview/policy-map.md` — 정책 16(메타데이터 입력 카드)·정책 22(좌표계 입력)에 **설명문 위치 규정 없음**. 정책 22 축자 「좌표계를 사람이 적는다. 자유 입력이다. 예시 안내: EPSG:5179.」
- 판정 역전 위험: **위치 이동(ⓐ)은 역전 아님**. **문면 삭제(ⓑ)는 PRD-40 판정 ⓐ 역전** — 채택 시 Ted 재판정 필요. 플래그.

---

## #24 — 업로드: 파일 처리 중 「다음」 미동작 · 성능

이슈 본문이 두 항목을 나눠 적었다 — ㉮ 성능 확인 ㉯ 다음 버튼 미동작과 사용자 고지. 아래에서 갈라 적는다.

### #24-㉯ 「분석 중」 동안 `다음 →` 비활성 · 사유 미고지

#### 1. 이슈 요지
- 사용자 행위: 업로드 모달에서 파일(스크린샷 = `gk2a_ami_le2_lst_ko_202005010000.nc` · 조각 141 · 합계 48 MB)을 올린 뒤 `다음 →` 를 누른다.
- 관측: 「분석 중 · 확장자·용량 확인 중…」 표시 동안 `다음 →` 이 눌리지 않고, **왜 눌리지 않는지 버튼 자리에서 알 수 없다**.

#### 2. 재현 경로
| 단계 | 내용 | 근거 |
|---|---|---|
| 1 | 업로드 모달에 파일 놓기 → 접수(`createUpload`) | 코드에 존재 (`UploadModal.tsx`) |
| 2 | 상태 폴링 1초 간격 시작 | 코드에 존재 (앵커 `const STATUS_POLL_MS = 1000;` · 앵커 `if (!s.ready && !s.failure) statusTimer.current = window.setTimeout(tick, STATUS_POLL_MS);`) |
| 3 | `analyzeStage` 2 표시 = 「확장자·용량 확인 중…」 | 코드에 존재 (앵커 `const analyzeStage: 1 \| 2 \| 3 = !uploadId ? 1 : status?.ready ? 3 : 2;` · 앵커 `ANALYZE_STAGES`) |
| 4 | `다음 →` 클릭 시도 | 코드에 존재 |
| 관측 | 버튼 `disabled` — 조건에 `!status?.ready` 포함 | 코드에 존재 (앵커 `data-testid="reg-open"` 의 `disabled={gridReuseBusy \|\| !uploadId \|\| !status?.ready \|\| Boolean(status?.failure) \|\| Boolean(statusIssue) \|\| Boolean(intakeError)}`) |
| 관측 | 버튼에 `title`·`aria-describedby`·비활성 사유 문구 **없음** | 코드에 존재(해당 속성 부재) |
| 기대 | 비활성 사유가 버튼 근처에서 읽힌다 | 이슈 요구 |

#### 3. 관련 코드 앵커
- `frontend/src/components/upload/UploadModal.tsx`
  - 앵커 `data-testid="reg-open"` (문면 `다음 →`) — 비활성 조건식이 여기 인라인으로 있다.
  - 앵커 `<div className="reggate" data-testid="reg-gate">` — 등록 결정 게이트 블록. 안내 문구는 `rg-t`/`rg-s` 두 줄(「이 파일을 연구실에 등록할까요?」·「등록하면 계보가 쌓이고 검색·공유가 돼요.」)뿐이고 비활성 사유가 없다.
  - 앵커 `data-testid="up-analyze"` (`role="status"` · `aria-live="polite"`) — 진행 표시. 등록 게이트와 **DOM 상 떨어진 별도 블록**이고 버튼과 `aria` 로 연결돼 있지 않다.
  - 앵커 `export const ANALYZE_STAGES = [` — 3단계 문면 배열. 「잘못된 배치를 만드는 자료구조」에 해당하는 것은 이 배열이 아니라 **버튼 인라인 조건식과 진행 표시 블록이 서로 참조하지 않는 구조**다.
- `frontend/src/components/common/toastCopy.ts` — 앵커 `export const ANALYZING_CHIP = '분석 중';`.

#### 4. 원인 가설
- 가설 1 (증거: 코드에 존재 ＋ 문서 존재) — 「분석 완료 전 다음 비활성」은 **의도된 정책**이다. `dev-package/reports/upload-layout-preview/policy-map.md` 정책 6 축자: 「분석이 끝나야 다음 버튼이 켜진다」·「분석 완료 전 다음 비활성; 전송100%와 분석완료 구분」. 결함은 비활성 자체가 아니라 **사유 미고지**다.
- 가설 2 (증거: 미확인) — 사용자가 「눌리지 않는다」로 인지한 구간이 실제로는 상태 폴링 실패 재시도 구간(`statusIssue` 경로)일 가능성. 스크린샷은 `분석 중` 칩만 보이므로 판별 불가 — 「미확인」.

#### 5. 수정 범위 초안
- 대상 파일: `frontend/src/components/upload/UploadModal.tsx` 1개(필수) ＋ 문면 상수를 쓰면 `frontend/src/components/common/toastCopy.ts` 1개.
- 방향: 비활성 사유 한 줄을 등록 게이트 안에 두고 버튼에 `aria-describedby` 로 연결. 문면은 진행 단계값을 재사용(분석 중이면 「분석이 끝나면 눌러요」, 접수 오류면 기존 `up-intake-error` 경로 유지).
- ⛔ **비활성 자체를 해제하지 않는다** — 정책 6 역전.
- `contracts/` 변경: 없음. DB 마이그레이션: 없음. 동결 해제 서명: 불필요. 프런트엔드 전용.

#### 6. red 테스트 후보
- 기존 파일: `frontend/test/upload.test.tsx` (앵커 `expect(screen.getByTestId('reg-open')).toBeDisabled();` · 앵커 `data-stage', '2'`).
- 먼저 쓸 실패 테스트: 「`analyzeStage` 2 에서 `reg-open` 이 비활성이고, 버튼의 `aria-describedby` 가 가리키는 요소에 분석 중 사유 문면이 있다」 — 현재 `aria-describedby` 부재로 실패.

#### 7. 겹침·순서 의존
- `UploadModal.tsx` 는 **그룹 A(#32·#33·#34)와 같은 파일**이다 — 취소·이어서 하기·중단 삭제가 모두 이 파일의 상태 기계를 만진다. **같은 레인에서 직렬 처리 필수**(병렬 레인 금지).
- 그룹 C(#25 업로드 화면 진입 시 지도 지연)도 `UploadModal.tsx` 가 `PreviewPanel` 을 부르는 지점과 인접 — `PreviewPanel.tsx` 만 고치면 병렬 가능, `UploadModal.tsx` 를 만지면 직렬. 「미확인」(#25 본문 미조사).
- #31 과는 파일이 갈려 병렬 가능.

#### 8. 범위 판정 후보
- `v2 버그` — 화면이 사용자에게 「왜 못 누르는가」를 말하지 않는 고지 누락. 추천·단축 경로가 아니다.

#### 9. 크기
- 파일 1~2. 변경 행 추정 10~20행 — 근거: 조건식 재사용 1건, 안내 문단 1건 신설, `aria-describedby` 속성 1건, 문면 상수 1건, 테스트 1건.

### #24-㉮ 성능 — 분석이 오래 걸리는 원인

#### 1. 이슈 요지
- 사용자 행위: 조각 141개 · 합계 48 MB 를 한 데이터셋으로 올린다.
- 관측: 「분석 중」 구간이 길다. 이슈 요구는 「성능에 어떤 문제가 있는지 확인」.

#### 2. 재현 경로
| 단계 | 내용 | 근거 |
|---|---|---|
| 1 | 141 조각 접수 → `d5_upload.ready = false` | 코드에 존재 (`services/core-api/src/colab_core/domains/d5_ingestion.py` 앵커 `UPDATE d5_upload SET ready = false`) |
| 2 | 워커 루프가 5초 주기로 pending 을 집는다 | 코드에 존재 (`services/pipeline-worker/src/colab_pipeline/app/worker.py` 앵커 `def serve(interval_seconds: float = 5.0)` · 앵커 `time.sleep(interval_seconds)`) |
| 3 | 한 바퀴 최대 20건 | 코드에 존재 (앵커 `BATCH = 20`) |
| 4 | 업로드 1건의 **모든 조각을 순차로 내려받아 로컬에 materialize** | 코드에 존재 (앵커 `path = blobs.materialize(key=key, dest=holder, file_name=name)` 가 `for ref in ledger.accepted_files(upload_id):` 안에 있다) |
| 5 | 본체 파일마다 헤더 판독 | 코드에 존재 (`services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py` 앵커 `for f in bodies:` ＋ `det = detect_format(f.path)`) |
| 6 | 완료 시 `upload.ready` 발행 → FE 폴링이 `ready` 수신 | 코드에 존재 (앵커 `self._emit(work, res, "upload.ready", upload_ready_payload(`) |
| 실측 소요 | 조각 수별 실제 시간 | **미측정 — 「미확인」** |

#### 3. 관련 코드 앵커
- `services/pipeline-worker/src/colab_pipeline/app/worker.py` — 앵커 `def drive_uploads`(내부 `for row in ledger.pending_uploads(limit=limit):` → `for ref in ledger.accepted_files(upload_id):` **이중 순차 루프**), 앵커 `BATCH = 20`, 앵커 `def serve(interval_seconds: float = 5.0)`.
- `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py` — 앵커 `bodies = [f for f in work.files if f.kind == "본체"]`, 앵커 `for f in bodies:` ＋ `detect_format(f.path)`.
- `frontend/src/components/upload/UploadModal.tsx` — 앵커 `const STATUS_POLL_MS = 1000;` (완료 감지 지연 최대 1초 추가).

#### 4. 원인 가설
- 가설 1 (증거: 코드에 존재) — 지연의 지배 항은 **조각 수에 선형인 순차 다운로드**다. 141 조각이면 `materialize` 가 141회 순차 호출되고, 그 뒤 본체마다 `detect_format` 이 다시 순차로 돈다. 병렬화·조기 시작이 없다.
- 가설 2 (증거: 코드에 존재) — 고정 지연이 더해진다. 워커 루프 주기 5초 ＋ FE 폴링 1초. 접수 직후 최악 6초는 파일 크기와 무관하게 발생한다.
- 실제 기여 비율: **미측정 — 「미확인」**. 실측 없이 원인을 확정하지 않는다.

#### 5. 수정 범위 초안
- 조사 선행이 필요하다 — 실측(조각 수 1·10·141 에 대한 접수→`ready` 소요) 없이 코드를 고치지 않는다.
- 후보 대상: `services/pipeline-worker/src/colab_pipeline/app/worker.py`(다운로드 병렬화 또는 진행 이벤트 세분화), `frontend/src/components/upload/UploadModal.tsx`(단계 문면에 조각 진행 수 표시).
- `contracts/` 영향: 진행 이벤트 페이로드를 늘리면 `contracts/` 변경 → **동결 해제 서명 필요**. 표시 문면만 바꾸면 계약 무변.
- 백엔드 ＋ 프런트엔드 양쪽.

#### 6. red 테스트 후보
- 기존 파일: `services/pipeline-worker` 의 `drive_uploads` 시험(파일명 「미확인」 — 이번 조사에서 열람하지 않음), `frontend/test/upload-progress-recovery.test.tsx`.
- 먼저 쓸 실패 테스트: 「조각 N 건의 업로드에서 `materialize` 호출이 순차 N 회가 아니라 상한 동시성으로 수행된다」 또는 「진행 표시가 조각 처리 진행 수를 노출한다」. 방향 확정은 실측 후.

#### 7. 겹침·순서 의존
- 프런트 표시 변경분은 `UploadModal.tsx` 를 만지므로 그룹 A 및 #24-㉯ 와 **같은 레인 직렬**.
- 워커 변경분은 `services/pipeline-worker/**` 단독이라 프런트 레인과 **병렬 가능**.

#### 8. 범위 판정 후보
- ㉮ 성능 = **판정 보류 후보** — 실측 전에는 `v2 버그`(사용 불가 수준 지연)인지 `편의 기능(후일 묶음)`(체감 개선)인지 갈린다. 권고: 실측 1회를 별도 조사 항목으로 세우고, 그 값으로 Ted 가 판정.
- ㉯ 고지 = `v2 버그`.

#### 9. 크기
- ㉮ 실측 조사 = 코드 변경 0. 후속 구현은 파일 1~3 · 행 30~80 추정(근거: 순차 루프 1개를 동시성 상한 구조로 바꾸는 변경 ＋ 시험). **추정 근거 약함 — 실측 후 재산정 필요**.

#### 10. 대장 대조 (#24 공통)
- `dev-package/work-items.yaml` — `id: PV-1` / `status: done` / `stage: stage2`. 미리보기 뒷단(헤더 파싱·좌표계 통일) 소유 항목. `evidence` 에 워커 배선 실측 기록.
- `dev-package/work-items.yaml` — `id: LV-2` / `status: done` / `stage: stage1`.
- `dev-package/prd/rounds/R-UPLOAD-PREVIEW.md` 축자 — 「원본 초기 모달은 620px이고 분석 완료 후 사용자가 다음을 누르기까지 작게 유지한다. 기존 720px 수정과 파일 선택 즉시 확장은 미달이다. 해당 장면 경계와 **등록 조기 활성**부터 회귀 검증한다.」
- `dev-package/reports/upload-layout-preview/policy-map.md` 정책 6 축자 — 「분석이 끝나야 다음 버튼이 켜진다」·「분석 완료 전 다음 비활성; 전송100%와 분석완료 구분」.
- `dev-package/reports/upload-layout-preview/frontend-continuation.md` 축자 — 「분석 완료 뒤 사용자가 다음을 눌러야 전폭 입력으로 바뀐다. 실패/분석 중 진입 비활성.」
- **판정 역전 위험: 높음.** `다음 →` 을 분석 중에 활성화하는 수정은 정책 6 과 R-UPLOAD-PREVIEW 회귀 기준(「등록 조기 활성」)을 뒤집는다. 고지 추가로 한정할 것을 권고하고, 활성화를 택하려면 Ted 재판정.
- `dev-package/intent/2026-09-09-upload-layout-preview.md` — 「다음 버튼」·「분석」 비활성 규정 문장 없음(grep 무결과 · 상세 화면 항목 1건만).

---

## 그룹 요약

| 이슈 | 판정 후보 | 크기(파일/행) | 겹치는 파일 | 병렬 가능 여부 |
|---|---|---|---|---|
| #31 설명문 위치 | v2 버그 | 1~2 / 8~15 | `RegisterArea.tsx` (그룹 내 단독) | 가능 — A·C·D 와 병렬 |
| #24-㉯ 다음 비활성 고지 | v2 버그 | 1~2 / 10~20 | `UploadModal.tsx` (그룹 A 공유) | 불가 — 그룹 A 와 직렬 |
| #24-㉮ 분석 성능 | 실측 후 판정(v2 버그 ↔ 후일 묶음) | 조사 0 / 후속 30~80 | `pipeline-worker/**`(단독) ＋ `UploadModal.tsx`(공유) | 워커분 병렬 가능 · 프런트 표시분 직렬 |

### 레인 분할안
1. **레인 B-1 (독립 · 즉시 병렬)** — #31. `frontend/src/components/upload/RegisterArea.tsx` ＋ `frontend/test/register-steps-20260907.test.tsx`. 다른 어느 그룹과도 파일 충돌 없음.
2. **레인 A+B-2 (합침 · 직렬)** — #24-㉯ 를 그룹 A(#32·#33·#34)와 **한 레인**으로 묶는다. 근거: 넷 다 `UploadModal.tsx` 의 같은 상태 기계(`status`·`uploadId`·`intakeError`)를 만진다. 순서 = 취소·이어서 하기 상태 정리 먼저, 고지 문구 나중(고지 문면이 그 상태값을 읽는다).
3. **레인 B-3 (조사 전용 · 병렬)** — #24-㉮ 실측 1회(조각 1·10·141 접수→`ready` 소요). 코드 변경 0이라 어느 레인과도 충돌 없음. 결과로 Ted 판정 입력 생성.

### 후속 항목 (이 조사에서 고치지 않음)
- `RegisterArea.tsx` 의 `fieldnote` 배치 규약이 코드·문서 어디에도 없다. 규약을 정하면 정책 문서(정책 16 계열)에 한 줄 추가가 필요하다.
- 그룹 C(#25·#29) 본문 미조사로 `PeriodCalendarPopover.tsx`·`PreviewPanel.tsx` 충돌 여부는 「미확인」.
- #24-㉮ 의 워커 시험 파일 경로 미확인.
