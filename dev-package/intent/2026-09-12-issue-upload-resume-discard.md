# Intent: 미완결 업로드의 이어가기와 버리기
메타 — 발의자: Ted(GitHub 이슈 작성 sungwooHa 회수) · 작성 2026-09-12 · 승인 미승인

## 문제
- 전송이 덜 끝난 업로드에서 메인 화면 배너의 「이어서 하기」를 눌러도 파일을 다시 고르는 첫 단계가 열린다(`CognileapAI/colab-v2#33`).
- 업로드 창을 닫을 때 뜨는 확인 모달의 선택지가 「계속하기」·「닫고 나가기」 둘이고, 올린 것을 함께 버리는 선택지가 없다(`CognileapAI/colab-v2#34`).
- 메인 화면 배너에 「이어서 하기」만 있고 올리다 만 업로드를 버리는 경로가 없다. 같은 폐기 버튼이 모달 안 배너에는 존재한다(`CognileapAI/colab-v2#32`).

## 원한 결과 (proposed outcome)
1. 전송이 덜 끝난 항목의 메인 배너 「이어서 하기」를 누르면 `UploadEntry.tsx` 가 `resumeUploadId` 를 모달에 전달하고, 모달이 기존 `resumeFromRef='banner'` 재개 경로로 그 업로드를 이어받는다. `frontend/test/unfinished-uploads.test.tsx` 에 추가한 실물 렌더 단언 1건이 green 이다(#33 ㉠).
2. 업로드 창 닫기 확인 모달에 세 번째 선택지가 표시되고, 그 선택지를 누르면 이 브라우저의 미완결 항목 기억이 지워지며 배너 목록에서 사라진다(#34).
3. 세 번째 선택지의 문면이 「이 브라우저에서 감춘다 · 서버에 접수된 항목은 24시간 만료로 정리된다」는 사실을 그대로 말한다. 서버 즉시 삭제를 뜻하는 문면을 쓰지 않는다(#34 · 판정 ②).
4. 메인 화면 배너에 폐기 버튼이 표시되고, 누르면 2·3 과 같은 동작·같은 문면으로 처리된다(#32 안 A).
5. 폐기 동작을 세 자리(닫기 확인 · 모달 안 배너 · 메인 배너)가 공통 헬퍼 `discardUpload` 로 호출한다.

## 영향 범위
- 사용자 / 화면: 메인 화면 미완결 업로드 배너 · 업로드 모달 닫기 확인 모달 · 업로드 모달 안 미완결 배너.
- 서비스 · 스키마 · 계약: frontend 단독. 대상 = `frontend/src/components/upload/UploadEntry.tsx` · `UploadModal.tsx` · `UnfinishedUploads.tsx` · `pendingStore.ts` · `frontend/src/components/common/toastCopy.ts` · 배너 버튼이 `.up-banner` 를 접촉하면 `frontend/src/components/upload/upload.css`. core-api·pipeline-worker·viz-render 변경 0.
- 계약 파괴 여부: 아니오. 근거 = `dev-package/reports/issues/2026-09-12-survey-SUMMARY.md` §7 — 이번 회차 착수 후보 범위에서 `contracts/` 변경 0건 · DB 마이그레이션 0건 · 동결 해제 서명 불요. 조사 A `#34` §5 축자 「계약 변경 여부 — frontend 전용안은 0건(기존 `abortUploadTransfer` 재사용)」 · 조사 A `#33` §5 축자 「계약 변경 — 0건」 · 조사 A `#32` §5 안 A 축자 「계약 0건 · 마이그레이션 0건 · backend 0건」.

## 제약
- `CLAUDE.md §2`·`§3` 불변 규칙 중 걸리는 것 없음 — 도메인 참조·D10→D4 쓰기·마이그레이션 체인 분리·geo 라이브러리·연구실 경계·정규 ID·생성물 수정 어느 항목도 접촉하지 않는다.
- 「AI 없이도 v2 는 완결된 제품이다」 유지 — 이번 변경에 AI 제안 경로가 개입하지 않는다.
- 대화형 UI 도입 금지 — 선택지 추가는 기존 확인 모달의 버튼 1개 증설이고 대화 정문을 만들지 않는다.
- 문면 추가는 PRD-34 문면표 개정을 동반한다. 문면표를 고치지 않고 화면 문자열만 바꾸지 않는다.
- 공유 파일 충돌 — `UploadModal.tsx` 는 `#25 ⑴` 후속 수정(I-3 뒤 L5)과 공유하므로 이 intent 병합 뒤에 그 수정을 얹는다. `UnfinishedUploads.tsx`·`toastCopy.ts` 는 이 intent 내부에서만 직렬로 만진다. `upload.css` 는 I-3(`#28`·`#29 ⑴`)·I-4 갈래 ⓑ 와 잠재 충돌이며, 조치 = I-4 를 갈래 ⓐ 로 한정하고 `#32` 안 A 착수 시 `.up-banner` 접촉 여부를 먼저 확인해 접촉하면 I-3 뒤로 직렬(`dev-package/reports/issues/2026-09-12-survey-SUMMARY.md` §3 충돌표).
- 레인 순서 = ① #33 ㉠ 배선 → ② #34 세 번째 선택지 ＋ `discardUpload` 공통 헬퍼 추출 → ③ #32 안 A 메인 배너 폐기(그 헬퍼 재사용). 4단 직렬 갈래 甲(같은 취합본 §3 「L1 레인 절단의 두 갈래」). ④ #24 ㉯ 고지는 I-2 로 분리한다.

## 설계트리 (grill-me 결과)
- Q1 「올리다 만 것 지우기」(#32)를 이번 묶음에 넣을 것인가 → A ⓐ 이번에 함께 고친다 (권장안 수용). 결과 = 레인 4단 · 공통 헬퍼 `discardUpload` 추출 근거 성립.
- Q2 창을 닫을 때의 세 번째 선택지를 만들 것인가, 「취소」는 무엇을 지우는가 → A ⓐ 선택지를 만들고, 「취소」는 이 브라우저에서 감추는 것으로 하며(서버 행은 24시간 만료) 문면이 그 사실을 말한다 (권장안 수용). PRD-34 문면표 개정 동반.
  - Q2a 서버 즉시 삭제 창구(`DELETE /uploads/{uploadId}`)를 함께 여는가 → A 열지 않는다. 이번 범위 밖.
  - Q2b 조사 A 의 제안 문면 「등록 취소(올린 것도 버림)」를 채택하는가 → A 채택하지 않는다. 같은 조사본의 처리 초안(접수 완료면 `forgetPending` 만)과 어긋나고, Q2 의 답이 브라우저 기억 삭제이므로 문면이 서버 삭제를 뜻하지 않게 쓴다(취합본 §8 「#34 「취소」의 뜻」).
- Q3 「이어서 하기」를 두 경우로 갈라 다룰 것인가 → A ⓐ 둘로 갈라 ㉠(전송 미완 배선)만 이번에 고치고 ㉡(접수 완료분 등록 장면 복원)은 설계 뒤로 돌린다 (권장안 수용).
  - Q3a ㉠ 의 수정 형태 → A prop 1개 배선. 근거 = `UploadEntry.tsx` 가 `resumeUploadId` 를 전달하지 않고 `UploadModal.tsx` props 에 재개 필드 0건이며, 잇는 즉시 기존 `resumeFromRef='banner'` 경로가 재사용된다(취합본 §1 · `[advisor 앵커 · 미재확인]`).
- Q4 #34 를 문면·동작 불일치 결함으로 다루는가 → A 다루지 않는다. 확인 모달은 `hasHumanInput`/`submitLock`/`committed` 에서만 열리고 「올린 파일이 취소돼요」 문면은 `!hasHumanInput` 갈래(`UPLOAD_CLOSE_FILE_ONLY`)이므로 이 장면의 문면은 `UPLOAD_CLOSE_INPUT_ONLY` 다. 남는 것은 선택지 신설 제안이다(취합본 §4-② · `[advisor 앵커 · 미재확인]`).
- Q5 `#32` 안 B(서버 즉시 삭제)를 채택하는가 → A 채택하지 않는다. 계약 신설 6+파일 / 250+행이고 24시간 만료 스윕이 계약에 백스톱으로 존재한다.

## 미해결 질문
- 없음.

## 범위 밖 (명시 제외)
- `#33 ㉡` 접수 완료분의 등록 장면 복원 — 파일 실물(`File`) 없이 등록 장면을 세우는 경로가 없어 신규 설계가 선행한다. 설계 뒤 별도 항목.
- 서버 즉시 삭제 계약 `DELETE /uploads/{uploadId}` 신설(`contracts/seams/fe-core.yaml`) — 채택 시 동결 해제 서명 선행.
- 확대·축소 버튼의 고정 배치 재설계.
- `#30` 부모 찾기 창의 화면 형태 재구성.
- 미리보기에서 「이미지에서 고르기」로 기간을 지정하는 설계(`#29 ⑵`).
- `#31` 설명문 자체의 삭제 — I-4 에서 문면은 유지한다.
- `#10`(경위도 격자선 · backlog `BF-10`) · `#11`(로그인 실패 제한 공유화 ＋ 신뢰 프록시 판정 · 대장 등재만 하고 착수 없음) · `#12`(구글 로그인 · backlog `PA-G`).

## 확인
- 프론티어 공집합 확인: 2026-09-12
- Ted 확인 문장(원문 그대로): "좋아 전부권고안으로"
- 재개봉 금지: 예

## 참조
- 이슈 원문: `CognileapAI/colab-v2#33` · `CognileapAI/colab-v2#34` · `CognileapAI/colab-v2#32` — 회수본 `dev-package/reports/issues/2026-09-12-github-open-issues.md`
- 조사본: `dev-package/reports/issues/2026-09-12-survey-A-upload-progress.md`
- 취합본: `dev-package/reports/issues/2026-09-12-survey-SUMMARY.md` §1 · §2 I-1 · §3 · §4-①②④ · §7 · §8
- 판정 기록: `dev-package/reports/issues/2026-09-12-ted-decisions.md`
- 결정: 〈N〉 (병합 시 기입) — 같은 행에 「PRD-34 문면표 개정」 기재
