# 이슈 조사 A군 — 업로드 진행·취소·재개 (#34 · #33 · #32)

- 조사 기준 커밋 `10a3fb8` (조사 워크트리 HEAD `1f1f58b` = `10a3fb8` ＋ 이슈 회수본 등재)
- 작성자 researcher · 승인 **미승인**
- 입력 = `dev-package/reports/issues/2026-09-12-github-open-issues.md` 절 `## #34`·`## #33`·`## #32`
- 첨부 이미지 = #33·#32 는 **같은 파일**(바이트 21,418 · PNG 동일 크기). 열람 완료 — 메인 화면 상단 배너 「올리다 만 것이 있어요」 ／ 행 「gk2a_ami_le2_lst_ko_202005010000.nc — 등록만 남았어요」 ／ 우측 버튼 **「이어서 하기」 하나뿐**.
- 참조 = 형제 체크아웃 조사본 2026-09-12 upload-download-inventory (행 번호는 다른 브랜치 기준이라 채택하지 않음 · 본 보고의 앵커는 이 워크트리 재확인분)

---

## 공통 사실 (세 이슈가 공유하는 구조)

- 업로드는 두 걸음 — ㉠ 바이트 전송(전송 원장 `d5_upload_transfer*` · 72시간) ㉡ 접수 후 설정 입력 → 「연구실에 등록하기」(접수 원장 · 24시간). 근거 = `frontend/src/components/upload/UnfinishedUploads.tsx` 머리 주석 「업로드는 두 걸음이다」.
- 미완결 목록의 자리가 **둘**이다 — ⑴ 메인 화면 배너 `UnfinishedUploads`(`frontend/src/routes/LabPage.tsx` 가 마운트) ⑵ 업로드 모달 안 배너(`UploadModal.tsx` · `data-testid="up-incomplete"`).
- 두 자리의 **버튼 구성이 다르다** — 모달 안 배너는 `up-resume-*` ＋ `up-discard-*` 둘, 메인 배너는 `unfinished-resume-*` / `unfinished-register-*` **하나씩만**. 「코드에 존재」.
- 계약 창구 = `contracts/seams/fe-core.yaml` — `DELETE /uploads/transfers/{uploadId}`(`abortUploadTransfer`)는 **전송 원장 전용**이고 축자 「완결된 전송은 중단할 수 없다(409) — 그것은 이미 접수다」. `/uploads/{uploadId}` 는 **`get`(`getUploadStatus`)만** 있고 delete 가 없다. 「코드에 존재」.
- ⇒ **접수 완료·등록 미완(㉡)을 서버에서 지우는 op 이 계약에 없다.** 세 이슈의 수정 범위 판정이 전부 이 사실 위에 선다.

---

## #34 — 업로드 취소시 등록 취소 버튼 필요

### 1. 이슈 요지
- 업로드를 닫으려 할 때 뜨는 확인 모달에 **「전부 취소」에 해당하는 선택지가 없음**. 사용자는 「계속하기」와 「닫고 나가기」 둘만 보고, 올린 것을 함께 버리는 길을 찾지 못함.

### 2. 재현 경로
| 단계 | 화면·행위 | 관측 | 기대 | 근거 |
|---|---|---|---|---|
| 1 | GNB 「업로드」 → 파일 드롭 | 접수 성공 · `uploadId` 발급 | — | 코드에 존재 |
| 2 | 이름·설명 등 입력 | `hasHumanInput` = true | — | 코드에 존재 |
| 3 | × 또는 Esc 또는 배경 클릭 | 확인 모달 `upload-close-confirm` 표시 | — | 코드에 존재 |
| 4 | 확인 모달 관찰 | 버튼 **2개** — 「계속하기」·「닫고 나가기」 | 3번째 「등록 취소(올린 것도 버림)」 | 코드에 존재 |
| 5 | 「닫고 나가기」 | `props.onClose()` 만 실행 · 서버 원장 유지 · `pendingStore` 유지 | 올린 바이트·원장 정리 | 코드에 존재 |
| 6 | 메인 화면 복귀 | 「올리다 만 것이 있어요 — 등록만 남았어요」 배너 재출현 | 취소했으면 배너 없음 | 코드에 존재 (#32·#33 스크린샷이 이 상태) |

### 3. 관련 코드 앵커
- `frontend/src/components/upload/UploadModal.tsx`
  - `function requestClose()` — 판정식 `if (submitLock.current || committedDatasetIdRef.current || hasHumanInput) setConfirmClose(true); else props.onClose();`
  - 상태 `const [confirmClose, setConfirmClose] = useState(false);`
  - 확인 모달 블록 — 앵커 `data-testid="upload-close-confirm"`, 버튼 둘의 `onClick` = `() => setConfirmClose(false)` 와 `props.onClose`
  - 접수 성공 분기 — 앵커 `if (account?.labId) rememberPending(account.labId, receipt.uploadId);`
  - 모달 안 배너의 폐기 버튼(참조 구현) — 앵커 `data-testid={\`up-discard-${item.uploadId}\`}` · 본문 `forgetPending` ＋ `upload.abortTransfer?.(item.uploadId).then(refreshIncomplete)`
- `frontend/src/components/common/toastCopy.ts` — `UPLOAD_CLOSE_TITLE`·`UPLOAD_CLOSE_KEEP`·`UPLOAD_CLOSE_LEAVE`·`uploadCloseMessage`·`UPLOAD_CLOSE_FILE_ONLY`
- 잘못된 동작을 만드는 분기 = 「닫고 나가기」의 `onClick={props.onClose}` — 원장 정리 호출이 **없음**.

### 4. 원인 가설
- 가설 ①(주) — **문면과 동작의 불일치**. `UPLOAD_CLOSE_FILE_ONLY` 축자 「올린 파일이 취소돼요. 원본 파일은 그대로라 다시 올리면 돼요.」인데 닫기 경로에 `abortTransfer`·`forgetPending` 호출이 0건. 등급 **「코드에 존재」**(`UploadModal.tsx` 전체에서 `abortTransfer` 출현 위치는 모달 안 배너 폐기 버튼 한 곳뿐).
- 가설 ②(부) — **선택지 설계 자체가 2지선다**. PRD-34 는 문면 3종·버튼 2종을 고정했고 시험이 그 2종을 검증함. 등급 **「테스트 존재」** — `frontend/test/prd34-close-copy-20260907.test.tsx` 「입력 있음 · 계보 0 → … · 버튼은 계속하기 · 닫고 나가기」·「「계속하기」는 확인만 닫는다 — 업로드는 그대로 남는다」.
- ⇒ 3번째 버튼 추가는 **PRD-34 문면표 개정을 동반**한다(문면의 자리는 `toastCopy.ts` 하나 · PRD-43).

### 5. 수정 범위 초안
- frontend 전용안(권고) — `UploadModal.tsx`(버튼 추가 ＋ 폐기 핸들러) · `toastCopy.ts`(3번째 버튼 문면 상수) · 시험 2종.
  - 폐기 동작 = ㉠ 미완결 전송이면 `upload.abortTransfer(uploadId)`(계약 op 기존) ㉡ 접수 완료면 `forgetPending` 만 가능 — 서버 행은 24시간 만료에 맡김.
- 계약 변경 여부 — **frontend 전용안은 0건**(기존 `abortUploadTransfer` 재사용).
- 서버에서도 접수분을 즉시 지우려면 **`DELETE /uploads/{uploadId}` 신설 = 계약 개정 ⇒ 동결 해제 서명 필요**. ⚠ 플래그.
- DB 마이그레이션 — frontend 전용안 0건 / op 신설안도 스키마 무변경 예상(기존 원장 행 삭제) 「미확인」.

### 6. red 테스트 후보
- 기존 인접 파일 — `frontend/test/prd34-close-copy-20260907.test.tsx`(닫기 확인 전담) · `frontend/test/close-guard-20260905.test.tsx` · `frontend/test/upload-transfer.test.tsx`.
- 첫 red — `prd34-close-copy-20260907.test.tsx` 에 추가: 「접수된 업로드에서 닫기 확인의 **세 번째 버튼**을 누르면 `abortTransfer` 가 그 `uploadId` 로 1회 호출되고 `listPending` 에서 사라진다」.

### 7. 겹침·순서 의존
- A군 내부 — #34 와 #32 는 **같은 폐기 동작**을 다른 자리에 세운다. 공통 헬퍼(예 `discardUpload(labId, uploadId)`)를 먼저 두면 둘이 갈리지 않음. **#34 → #32 순서 권고**.
- #33 과 파일 충돌 — `UploadModal.tsx` 공유. **직렬**.
- B군(#31·#24) — `UploadModal.tsx`·`RegisterArea.tsx` 를 만짐. **`UploadModal.tsx` 공유 ⇒ 병렬 불가**.
- C군(#25~#29) — `PreviewPanel.tsx`·`preview/**` 중심. #25 는 업로드 화면 안이라 `UploadModal.tsx` 접촉 가능성 「미확인」.
- D군(#10·#11·#12·#30) — 접점 없음.

### 8. 범위 판정 후보
- **v2 버그**. 사유 = 화면이 「올린 파일이 취소돼요」라 말하고 실제로는 취소하지 않음(문면과 동작 불일치).

### 9. 크기
- 파일 3~4 (`UploadModal.tsx`·`toastCopy.ts`·시험 1~2)
- 변경 행 추정 **60~110행**. 근거 = 모달 안 배너 폐기 버튼(버튼 마크업 ＋ 핸들러) 실측 약 18행 ＋ 문면 상수 2~3행 ＋ 갈래 판정 분기 ＋ 시험 2건 약 40행.

### 10. 대장 대조
- `dev-package/work-items.yaml` — `id: WU-A9` / `name: 종료 확인 조건 (PRD-14)` / `status: done` / `stage: stage2` / `completion_def` 축자 「빈 상태 닫기는 안 묻고, 한 글자라도 적었거나 계보 부모 1건이면 묻는다. **문면은 종전 그대로다**」 / `note` 축자 「미결-15 ⓐ — 조건만 고치고 문면 유지. PRD-34 는 §4 범위 밖」.
  - ⇒ 문면·버튼 구성을 바꾸는 것은 `WU-A9` 의 완료 정의 **밖**이다. 새 항목이 필요하다.
- `dev-package/work-items.yaml` — `id: U-1` / `name: "업로드 S3 직행 + 중단 재개"` / `status: done` / `completion_def` 에 「이어올리기」 포함.
- `dev-package/intent/2026-09-09-upload-layout-preview.md` — 관련 문장 = 「9. 느린 처리, … 취소·재시도, 단계 이동 중에도 상태가 누락되지 않는다. 오류를 알리고 **복구 경로를 제공**하며 …」 / 범위 밖 절 「기존 데이터 삭제, 공개·권한 정책의 임의 변경, 기존 기능의 무단 제거.」
  - ⇒ 폐기 버튼 신설은 「기존 기능 제거」가 아니라 복구 경로 추가라 intent 의 범위 밖 절에 걸리지 않음. **[추론]**

---

## #33 — 「이어서 하기」로 들어와도 업로드부터 다시 진행

### 1. 이슈 요지
- 메인 화면 배너의 「이어서 하기」를 눌러도 **파일을 다시 고르는 첫 단계**로 열림. 바이트는 이미 서버에 있으므로 **설정 입력 단계로 바로 가야 함**.

### 2. 재현 경로
| 단계 | 화면·행위 | 관측 | 기대 | 근거 |
|---|---|---|---|---|
| 1 | 업로드 접수 후 등록 전 이탈 | `pendingStore` 에 `uploadId` 기록 | — | 코드에 존재 |
| 2 | 메인 화면(S-01) 진입 | 배너 「… — 등록만 남았어요」 표시 | — | 코드에 존재 · 스크린샷 일치 |
| 3 | 「이어서 하기」 클릭 | `openUpload({ resumeUploadId })` 호출 | — | 코드에 존재 |
| 4 | `AppLayout` | `setRequest({ seq+1, resumeUploadId })` | — | 코드에 존재 |
| 5 | `Gnb` → `UploadEntry` | `openRequest` 수신 | — | 코드에 존재 |
| 6 | `UploadEntry` | **`setOpen(true)` 만 실행 · `resumeUploadId` 를 `UploadModal` 에 넘기지 않음** | 모달이 그 업로드를 복원 | 코드에 존재 |
| 7 | 모달 표시 | 빈 파일 드롭 화면(`data-scene="pick"`) | 설정 입력(등록) 장면 | 코드에 존재 |

### 3. 관련 코드 앵커
- `frontend/src/components/upload/UnfinishedUploads.tsx` — 앵커 `data-testid={\`unfinished-register-${p.uploadId}\`}` · `onClick={() => openUpload({ resumeUploadId: p.uploadId })}` (전송 행은 `unfinished-resume-*`)
- `frontend/src/shell/AppLayout.tsx` — 앵커 `const open = useCallback((req?: OpenUploadRequest) =>` · `setRequest((cur) => ({ seq: cur.seq + 1, ...` (여기까지는 값이 살아 있음)
- `frontend/src/shell/Gnb.tsx` — 앵커 `<UploadEntry openRequest={props.openRequest} />`
- `frontend/src/components/upload/UploadEntry.tsx` — **결함 지점**. 앵커 `const seq = props.openRequest?.seq ?? 0;` ＋ `useEffect(() => { if (seq > 0) setOpen(true); }, [seq]);` ＋ 렌더 `<UploadModal sources={sources} lineageStep={props.lineageStep} onClose={...} />` — **`resumeUploadId` 가 전달되지 않음**.
- `frontend/src/components/upload/UploadModal.tsx` — 재개 상태 `const [resumeId, setResumeId] = useState<string | null>(null);` · `const resumeRef = useRef<string | null>(null);` · `const resumeFromRef = useRef<'banner' | 'failure' | null>(null);` · `const [resumeArm, setResumeArm] = useState(0);`. **이 넷을 세우는 경로는 ⑴ 모달 안 배너 버튼 ⑵ `TransferInterrupted` 실패 자동 무장 둘뿐** — 외부 prop 경로 0건.
- `uploadId` 를 세우는 유일한 자리 = `void upload.create(picked, {...}).then((receipt) => { … setUploadId(receipt.uploadId);` — **기존 `uploadId` 로 복원하는 분기 없음**.

### 4. 원인 가설
- 가설 ①(주) — **배선 누락**. `UploadEntry` 가 `openRequest.resumeUploadId` 를 소비하지 않아 신호가 여기서 끊김. 등급 **「코드에 존재」**.
- 가설 ②(보강) — **㉡(접수 완료·등록 미완) 복원 경로가 애초에 없음**. 모달의 재개 개념은 ㉠(전송 미완)만 다루고, 그 흐름도 축자 「같은 파일을 다시 끌어다 놓으면 남은 조각부터 이어서 올라가요」로 **파일 재선택을 전제**함. `getUploadStatus`(`upload.status`)로 등록 장면을 세우는 코드는 0건. 등급 **「코드에 존재」**.
- 시험이 이 결함을 못 잡은 이유 — `frontend/test/unfinished-uploads.test.tsx` 의 「[이어서 올리기]가 모달을 **그 전송으로** 연다」가 검증하는 것은 `expect(onOpen).toHaveBeenCalledWith({ resumeUploadId: T1 })` **뿐**(`OpenUploadContext.Provider value={onOpen}` 스텁). 모달 실물이 그 값을 쓰는지는 어느 시험도 보지 않음. 등급 **「테스트 존재」**(결함을 통과시키는 시험).
- 이슈 본문의 두 번째 요구 「업로드가 안되어있으면 등록 취소하고 다시 진행해야함」 = 전송 미완 행에 폐기 선택지 요구 ⇒ **#32 와 동일 요구**.

### 5. 수정 범위 초안
- frontend 전용.
  - `UploadEntry.tsx` — `resumeUploadId` 를 `UploadModal` 로 전달(prop 신설).
  - `UploadModal.tsx` — prop 수신 시 ㉠/㉡ 갈래 분기. ㉡ 이면 `upload.status(uploadId)` 로 `uploadId`·`files`·이름 초안을 세우고 등록 장면(`registerOpen`)으로 진입, `picked` 재선택을 요구하지 않음.
  - `types.ts` — 필요 시 `UploadSources`·모달 props 타입 확장 「미확인」.
- 계약 변경 — **0건**. `GET /uploads/{uploadId}`(`getUploadStatus`)가 이미 있고 `UploadStatus.files`·`registered` 를 냄. 「코드에 존재」.
- DB 마이그레이션 — 0건.
- ⚠ 주의 — 접수 상태 복원 시 파일 실물(`File` 객체)이 브라우저에 없다. 미리보기·대표 그림 등 `picked` 를 전제하는 분기의 재검토 필요. 범위 확대 위험 지점. 「미확인」.

### 6. red 테스트 후보
- 기존 인접 파일 — `frontend/test/unfinished-uploads.test.tsx`(배너 4건) · `frontend/test/upload-transfer.test.tsx` · `frontend/test/register-steps-20260907.test.tsx` · `frontend/test/upload.test.tsx`.
- 첫 red — `unfinished-uploads.test.tsx` 에 추가: 「`OpenUploadContext` 를 스텁하지 않고 `AppLayout`(또는 `UploadEntry`) 실물로 렌더한 뒤 `unfinished-register-<id>` 를 누르면, 모달이 `data-scene="register"` 로 열리고 `upload.status` 가 그 id 로 호출된다」. 현행 코드에서 `data-scene="pick"` 이 나오므로 red.

### 7. 겹침·순서 의존
- A군 내부 — `UploadModal.tsx` 를 #34 와 공유 ⇒ **병렬 불가**. `UnfinishedUploads.tsx` 를 #32 와 공유 ⇒ **병렬 불가**.
- #33 이 A군의 **중심 파일 집합을 전부 건드림**(UploadEntry · UploadModal · UnfinishedUploads).
- B군 — `UploadModal.tsx` 공유 ⇒ **병렬 불가**.
- C군 — #25(업로드 화면 미리보기 지연)가 같은 모달 안이라 접촉 가능 「미확인」.
- D군 — 접점 없음.

### 8. 범위 판정 후보
- **v2 버그**. 사유 = 버튼이 있고 눌리는데 선언된 동작(그 업로드로 이어가기)이 일어나지 않음. 편의 기능 신설이 아니라 이미 붙은 경로의 미배선.

### 9. 크기
- 파일 3~5 (`UploadEntry.tsx`·`UploadModal.tsx`·`types.ts`·시험 1~2)
- 변경 행 추정 **120~200행**. 근거 = 배선 자체는 10행 미만이나, ㉡ 복원 분기가 `upload.create` 가 세우던 상태(`uploadId`·`nameDraft`·`status`·등록 장면 진입) 4종을 파일 없이 세워야 함 — 접수 성공 `.then` 블록 실측 약 20행에 대응하는 별도 경로 ＋ `picked` 전제 분기 방어.

### 10. 대장 대조
- `dev-package/work-items.yaml` — `id: U-1` / `status: done` / `completion_def` 축자 「저장 Port(로컬/S3 분기) · 프리사인드 전송 9 op · 전송 원장 `d5_upload_transfer*`(0008) · FE 전송 엔진 · **이어올리기**. …」.
  - ⇒ 「이어올리기」는 ㉠(전송 재개)를 가리키고 ㉡ 복원은 완료 정의에 없음. 판정 재개봉이 아니라 **새 항목** 대상. **[추론]**
- `dev-package/work-items.yaml` — `id: U-2` / `name: "S3 고아 바이트 정리"` / `status: done` — 접수 원장 만료 스윕 쪽. 완료 정의 축자에 「**등록된 업로드는 안 건드린다**」 포함.
- `dev-package/intent/2026-09-09-upload-layout-preview.md` — 「… 단계 이동 중에도 상태가 누락되지 않는다. 오류를 알리고 **복구 경로를 제공**하며 오래된 응답이 새 파일의 상태를 덮지 않는다.」

---

## #32 — 업로드 중간에 멈췄을 때 삭제하는 행위 필요

### 1. 이슈 요지
- 메인 화면의 「올리다 만 것이 있어요」 배너에 **「이어서 하기」만** 있고 버리는 선택지가 없음. 이어갈 생각이 없는 항목이 계속 남음.

### 2. 재현 경로
| 단계 | 화면·행위 | 관측 | 기대 | 근거 |
|---|---|---|---|---|
| 1 | 업로드를 중간에 중단 | 전송 원장(㉠) 또는 접수 원장(㉡)이 남음 | — | 코드에 존재 |
| 2 | 메인 화면 진입 | 배너 표시 · 행마다 버튼 **1개** | 폐기 버튼도 함께 | 코드에 존재 · 스크린샷 일치 |
| 3 | 폐기 시도 | 경로 없음 | 「지우기」 클릭 → 행 소멸 | 코드에 존재 |
| 4 | 우회 경로 확인 | 모달을 열면 `up-discard-*` 가 있음 — **㉠ 전송 미완 행에만** | ㉡ 행도 지울 수 있음 | 코드에 존재 |
| 5 | ㉡ 행의 서버측 폐기 | `DELETE /uploads/transfers/{uploadId}` 는 완결 전송에 409 | — | 계약에 존재 |

### 3. 관련 코드 앵커
- `frontend/src/components/upload/UnfinishedUploads.tsx` — **결함 지점**. 전송 행 앵커 `data-testid={\`unfinished-resume-${t.uploadId}\`}`, 접수 행 앵커 `data-testid={\`unfinished-register-${p.uploadId}\`}`. **두 행 모두 폐기 버튼 마크업 0건**. 상태 = `const [transfers, setTransfers] = useState<IncompleteTransferItem[]>([]);` · `const [pending, setPending] = useState<PendingRow[]>([]);`
- `frontend/src/components/upload/pendingStore.ts` — `export function forgetPending(labId: string, uploadId: string): void` (FE 기억만 지움)
- `frontend/src/components/upload/uploadSource.ts` — `async abortTransfer(uploadId: string)` → `api.DELETE('/uploads/transfers/{uploadId}', …)`
- `frontend/src/components/upload/transferSource.ts` — `async function abortTransfer(uploadId: string)` 주석 축자 「원장을 되돌린다 — S3 조각·객체·행을 서버가 함께 지운다. … 72h 뒤 지연 정리가 백스톱이다.」
- `contracts/seams/fe-core.yaml` — `operationId: abortUploadTransfer` · 축자 「완결된 전송은 중단할 수 없다(409) — 그것은 이미 접수다.」 / `/uploads/{uploadId}` 는 `getUploadStatus` 만.
- 참조 구현(그대로 옮길 대상) = `UploadModal.tsx` 앵커 `data-testid={\`up-discard-${item.uploadId}\`}`.

### 4. 원인 가설
- 가설 ①(주) — **모달 안 배너에만 폐기 버튼을 세우고 메인 배너로 옮기지 않음**(구현 누락). 등급 **「코드에 존재」** — 두 배너 마크업 대조로 확인.
- 가설 ②(구조) — **㉡ 행에는 서버측 폐기 op 자체가 없음**. `forgetPending` 만 부르면 배너에서는 사라지나 서버 원장·S3 바이트는 24시간(또는 스윕)까지 남음. 등급 **「코드에 존재」**(계약에 delete 부재).
- ⇒ ㉠ 행은 기존 op 로 완전 폐기 가능, ㉡ 행은 **화면에서만 지우기** 또는 **계약 개정** 둘 중 하나를 골라야 함. 판정 필요 사항.

### 5. 수정 범위 초안
- 안 A(frontend 전용 · 권고) — `UnfinishedUploads.tsx` 에 폐기 버튼 2종 추가. ㉠ = `upload.abortTransfer(id)` ＋ 목록 갱신, ㉡ = `forgetPending(labId, id)` ＋ 목록 갱신. `UploadModal.tsx` 의 폐기 핸들러를 공통 함수로 추출(#34 와 공유).
  - 계약 0건 · 마이그레이션 0건 · backend 0건.
  - ⚠ ㉡ 는 「이 브라우저에서 감추기」이지 서버 삭제가 아님. **문면이 그 사실을 말해야 한다**(「올린 파일이 취소돼요」류 문장을 ㉡ 에 그대로 쓰면 #34 와 같은 불일치가 재발).
- 안 B — `DELETE /uploads/{uploadId}` 신설(접수 원장 + S3 객체 폐기). **계약 변경 ⇒ 동결 해제 서명 필요** ⚠. backend `services/core-api` 라우트 ＋ 저장 Port 삭제 경로 ＋ 생성물 재생성. DB 마이그레이션은 불필요 예상 「미확인」.
- 권고 = 안 A 를 먼저 내고, 안 B 는 별도 intent 로 분리.

### 6. red 테스트 후보
- 기존 인접 파일 — `frontend/test/unfinished-uploads.test.tsx` · `frontend/test/upload-transfer.test.tsx` · `services/core-api/tests/`(안 B 채택 시).
- 첫 red — `unfinished-uploads.test.tsx` 에 추가: 「전송 미완 행의 `unfinished-discard-<id>` 를 누르면 `upload.abortTransfer` 가 1회 호출되고 그 행이 사라진다」 ＋ 「접수 완료 행의 `unfinished-discard-<id>` 를 누르면 `listPending` 에서 그 id 가 사라진다」. 현행은 버튼이 없어 query 실패로 red.

### 7. 겹침·순서 의존
- A군 내부 — `UnfinishedUploads.tsx` 를 #33 과 공유 ⇒ **병렬 불가**. 폐기 핸들러를 #34 와 공유 ⇒ **직렬 권고**.
- B군·C군 — 파일 접점 없음(`UnfinishedUploads.tsx` 단독이면 병렬 가능). 단 공통 함수를 `UploadModal.tsx` 에서 추출하는 순간 B군과 충돌.
- D군 — 접점 없음.

### 8. 범위 판정 후보
- 안 A 부분(㉠ 전송 폐기 버튼) = **v2 버그**. 사유 = 같은 목록이 모달 안에서는 지울 수 있고 메인 화면에서는 못 지움(같은 기능의 두 자리가 갈림).
- 안 B 부분(㉡ 서버측 즉시 폐기 op 신설) = **편의 기능(후일 묶음)** 후보. 사유 = 24시간 만료 스윕(`U-2`)이 이미 백스톱이고, 즉시 삭제는 단축 경로에 해당. 최종 판정은 Ted.

### 9. 크기
- 안 A — 파일 2~3 (`UnfinishedUploads.tsx`·(공통 추출 시)`UploadModal.tsx`·시험 1)
- 변경 행 추정 **50~90행**. 근거 = 모달 안 폐기 버튼 실측 약 18행을 두 행 종류에 이식 ＋ 목록 갱신 함수 ＋ 시험 2건 약 35행.
- 안 B — 파일 6+ (계약·라우트·저장 Port·생성물·시험 2종), 추정 **250행 이상** 「미확인」.

### 10. 대장 대조
- `dev-package/work-items.yaml` — `id: U-2` / `name: "S3 고아 바이트 정리"` / `status: done` / `completion_def` 축자 「ⓐ 만료 스윕이 원장 행과 **S3 객체를 함께** 지운다 ⓑ **S3 삭제가 실패하면 행이 남는다**(다음 바퀴 재시도 …) ⓒ **등록된 업로드는 안 건드린다**」.
  - ⇒ 자동 정리는 있음. **사람이 지금 지우는 길**이 없다는 것이 이 이슈. **[추론]**
- `dev-package/work-items.yaml` — `id: U-1` / `status: done`.
- `dev-package/intent/2026-09-09-upload-layout-preview.md` — 범위 밖 절 축자 「기존 데이터 삭제, 공개·권한 정책의 임의 변경, 기존 기능의 무단 제거.」
  - ⇒ 안 B(서버측 삭제 op)는 이 절과의 관계를 판정받아야 함. 안 A 는 화면 표시 범위라 해당 없음. **[추론]**

---

## A군 요약

| 이슈 | 판정 후보 | 크기 (파일 / 추정 행) | 겹치는 파일 | 병렬 가능 여부 |
|---|---|---|---|---|
| #34 등록 취소 버튼 | v2 버그 | 3~4 / 60~110 | `UploadModal.tsx`(#33·B군) · `toastCopy.ts` | 불가 (#33·B군과 직렬) |
| #33 이어서 하기 복원 | v2 버그 | 3~5 / 120~200 | `UploadEntry.tsx` · `UploadModal.tsx`(#34·B군) · `UnfinishedUploads.tsx`(#32) | 불가 (A군 전체와 직렬) |
| #32 폐기 버튼 | 안 A = v2 버그 / 안 B = 편의 기능(후일 묶음) | 안 A 2~3 / 50~90 · 안 B 6+ / 250+ | `UnfinishedUploads.tsx`(#33) · 공통 추출 시 `UploadModal.tsx` | 조건부 (`UnfinishedUploads.tsx` 단독이면 B·C군과 병렬) |

### 병렬 판정
- **A군 세 건은 서로 병렬 불가.** 근거 = `UploadModal.tsx` 를 #34·#33 이 공유하고, `UnfinishedUploads.tsx` 를 #33·#32 가 공유. `.claude/rules/colab-rules.md §4-2` 축자 「코드가 겹치지 않는 레인만 병렬(같은 파일군은 직렬)」.
- **A군 ↔ B군(#31·#24) 도 병렬 불가** — `UploadModal.tsx` 공유.
- **A군 ↔ C군(#25~#29)** — #25 의 `UploadModal.tsx` 접촉 여부 「미확인」. #26~#29 는 `PreviewPanel.tsx`·`preview/**` 라 병렬 가능 추정 **[추론]**.
- **A군 ↔ D군(#10·#11·#12·#30)** — 접점 없음, 병렬 가능.

### 레인 분할 제안 (단일 레인 · 3단계 직렬)
1. **단계 1 — #33** (배선 ＋ ㉡ 복원 경로). 사유 = A군 파일 집합을 가장 넓게 건드리므로 먼저 두어야 뒤 두 건의 리베이스가 없다. red 시험 = `unfinished-uploads.test.tsx` 실물 렌더 1건.
2. **단계 2 — #34** (닫기 확인 세 번째 버튼 ＋ 폐기 헬퍼 추출). 사유 = 여기서 `discardUpload` 공통 함수가 서고, 단계 3 이 그것을 재사용한다.
3. **단계 3 — #32 안 A** (메인 배너 폐기 버튼 2종). 사유 = 단계 2 의 헬퍼를 부르는 화면 작업만 남는다.
- #32 안 B(계약 op 신설)는 이 레인에 넣지 않고 **별도 intent 초안**으로 분리 — 동결 해제 서명이 선행 조건.
- ⚠ B군 착수는 이 레인 병합 이후. 동시 착수 시 `UploadModal.tsx` 충돌.

## 후속 항목 (이 조사에서 고치지 않음)
- `frontend/test/unfinished-uploads.test.tsx` 의 「[이어서 올리기]가 모달을 **그 전송으로** 연다」는 컨텍스트 스텁만 검증하고 모달 실물 동작을 보지 않음 — 결함 #33 을 통과시킨 시험. 실물 렌더 시험으로 승격 대상.
- `UPLOAD_CLOSE_FILE_ONLY` 문면과 닫기 동작의 불일치 — #34 수정에서 함께 정리하지 않으면 문면만 남음.
