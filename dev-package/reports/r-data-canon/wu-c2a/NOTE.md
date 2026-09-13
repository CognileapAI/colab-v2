# WU-C2a — 분석에 실패한 업로드도 등록할 수 있다 (`#40`)

- 바뀐 것 = `frontend/src/components/upload/UploadModal.tsx` 두 자리. ⑴ `다음 →`(`reg-open`) 비활성 식에서 `!status?.ready || Boolean(status?.failure)` 를 `!(status?.ready || status?.failure)` 로 — 워커가 실패에 `ready=False` 를 함께 쓰므로(`services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py` `_fail`) `failure` 항만 빼면 `ready:false` 가 그대로 막는다. ⑵ 실패 안내(`up-analysis-failure`) 문면을 「… — 지도로 못 그려요 · 등록은 됩니다」로.
- 근거 = 정본 `Policy_업로드와_계보_확정:192` · 서버 `services/core-api/tests/test_dataset_registration.py` `test_a_failed_pipeline_does_not_block_registration`(실패 업로드 등록 201).
- 무변 = 격자 검사항(`gridReuseBusy`) · `!uploadId` · `statusIssue` · `intakeError` · 실패 시 상태 폴링 중단(`if (!s.ready && !s.failure)`) · `data-testid` 전건.
- 새 시험 = `frontend/test/upload-register-on-analysis-failure.test.tsx` 3건 — 「`다음 →` 을 누를 수 있다」·「안내가 등록 가능을 함께 말한다」·「누르면 등록 단계가 열린다」. red 축자 = `expect(element).toBeEnabled()` · `expect(element).toHaveTextContent()` · `Unable to find an element by: [data-testid="reg-steps"]`.
- 고친 기존 시험 = `frontend/test/upload.test.tsx` 「분석 실패 원인을 안내하고 같은 파일 재전송 후 복구할 수 있다」 — 종전 `expect(screen.getByTestId('reg-open')).toBeDisabled()` 가 정본 `:192` 위반을 고정하고 있었다. `toBeEnabled()` 로 바꾸고, 복구 판정은 실패 안내 소멸로 옮겼다.
- 게이트(2회 연속) = `frontend-test green — 통과 1329건 · 실패 0건` / `frontend-typecheck green — 오류 0건` / `── 계 : green 2 / red(판정) 0 / red(준비) 0`.
- 관측 1건 = 첫 실행에서 `test/upload-transfer.test.tsx:326`(`표준 격자 가져오기` 조회)이 대기 초과로 1건 red. 단독 실행 16/16 green, 재실행 2회 전건 green — 전수 부하에서의 대기 초과로 판독. 뒤 항 `reg-open` 비활성 판정은 `gridReuseBusy` 소관이고 이번 변경 대상이 아니다.
