# frontend 소비 레인 검증 보고

## 작업 경계

- 작업 사본: `/home/ttlhi10/colab-ui-consumer`
- 브랜치: `codex/upload-preview-consumer`
- 기준 커밋: `a50a861ea71b51e23f6087eed3aa0fed62c5ab33`
- lifecycle task: `a4b7235310ce49069cbd74cc848b5c1c`
- 소유 범위: frontend 제품 코드와 시험, 이 보고서 디렉터리, 그리고 제품 변경으로 직접 요구된 `dev-package/sessions/P8-E01-APPLY-POINTS-DRAFT.md`의 PermissionGate 적용점 한 행
- 비소유 범위인 backend, DB, 계약, 생성 타입은 수정하지 않았다. `frontend/src/generated/fe-core.ts`는 생성물을 그대로 소비했다.

분리 브랜치에는 `scripts/agent-bridge.py`와 lifecycle 본체가 없다. 공유 루트의 bridge는 자기 루트를 공유 checkout으로 고정해 격리 작업 사본 경로를 거부하므로, 작업 사본 cwd와 payload를 유지한 채 공유 루트의 동일 fail-closed hook 본체를 직접 호출했다. lifecycle `begin`, 선언한 세 gate의 `run-gates`, `handoff`도 같은 이유로 공유 루트의 `lifecycle_contract.py` 본체를 작업 사본 cwd에서 실행했다.

## 구현한 외부 동작

- 등록 대표 그림은 실제 `File`을 모달 상태로 보존하고 object URL을 교체·해제한다. 데이터셋 등록이 성공한 뒤 대표 그림 PUT이 실패하면 같은 dataset ID와 File로 PUT만 재시도하며, 그림을 빼면 재등록 없이 자동 그림 상태로 상세에 이동한다.
- 상세 대표 그림은 인증된 Blob GET을 object URL로 표시하고 PUT 교체와 DELETE 자동 그림 복귀를 제공한다. 데이터셋 변경, 늦은 응답, 교체, unmount에서 이전 URL과 응답을 정리한다. GET 재시도는 읽기 사용자에게도 보이고 쓰기 동작은 기존 `업로드·편집` PermissionGate를 사용한다. PUT 성공 뒤 GET 실패는 저장 성공 상태와 불러오기 실패를 구분해 GET만 재시도한다.
- 사람 격자 설명은 등록 create body, 상세 draft/patch/apply에 연결했다. 빈 문자열은 `gridDescription: null`로 보낸다. 상세는 사람 값을 주값으로, 자동 판독값을 보조로 표시하며 사람 값을 지우면 자동값을 본문으로 되돌린다.
- 계보 후보는 생성 타입의 `/datasets/lineage-candidates` 페이지를 소비한다. 이름·파일명 검색, 분류, 주제, Lv, 기간, 자기 제외, cursor/limit를 서버에 전달하며 첫 페이지와 추가 페이지의 오류·재시도·늦은 응답을 분리한다. 서버 cursor로 중복 없이 이어 붙이고 서버가 준 파일명과 메타데이터만 표시한다.
- 계보 모달 최초 mount의 닫기 effect가 매우 빠른 열기 클릭을 덮는 경합을 고쳤다. dataset ID가 실제로 바뀔 때만 열린 모달을 닫는다.

## TDD와 검증 증거

- 첫 RED: 관련 시험 141건 중 123건 통과, 18건 실패, unhandled error 3건. 대표 그림 재시도, object URL 수명, 사람 격자 설명, 서버 페이지 계보 후보가 구현 전 외부 동작으로 실패했다.
- 관련 GREEN: 6파일 157/157 통과. 추가 대표 그림 회귀 묶음 9/9 통과. 최종 계보 모달 단독 회귀 12/12 통과.
- 최종 lifecycle: `frontend-test` 87파일 1,146/1,146, `frontend-typecheck` 오류 0, `generated-up-to-date` 등기부 10건 재생성 일치·등기부 밖 자칭 생성물 0건. 합계 green 3 / red(판정) 0 / red(준비) 0. 정본은 `gate-summary.json`이다.
- 첫 lifecycle 실행은 `frontend-test` 1,145/1,146과 나머지 두 gate GREEN이었다. 실패를 조사해 위 mount/클릭 경합을 재현·수정했다. 당시 보고서는 `gate-summary-first-red.json`에 보존했다. lifecycle의 이전 보고서 archive가 worktree와 공유 `.git` 사이 `os.replace`에서 cross-device 오류를 냈기 때문에, 이전 보고서를 같은 보고서 디렉터리로 옮긴 뒤 새 실행 ID로 재실행했다.
- `npm run build`: TypeScript 검사와 Vite production build 성공, 195 modules transformed. 기존 500 kB 초과 chunk 경고만 남았다.
- 대표 그림 API 경계 시험은 GET의 Blob 응답 소비, GET/PUT/DELETE의 Bearer 인증 middleware 경로, PUT `FormData`의 실제 File과 filename을 확인한다.
- CSS 정적 계측: `detail.css` 전체에서 신규 토큰 밖 값 0, 13px 미만 글자 0, 음수 여백 0, 신규 그림자·motion·대비 예외 0. 레인의 추가 규칙은 기존 radius/token만 쓴다.
- `frontend-visual`은 `COLAB_VISUAL_EXEMPT=1`로 명시적 면제 GREEN만 확인했다. 검수 페이지 수는 0이며 실제 브라우저 시각 검증으로 계산하지 않는다.

## 기존 오라클 개정 근거

- `thumb-nudge-20260905`의 “화면 전용·저장 안 함” 기대는 승인된 대표 그림 저장 계약과 충돌해 저장 동작으로 바꿨다. 넛지와 파일 선택기 기대는 유지했다.
- `lineage-continuation`의 `/datasets` 전 cursor 수집 기대는 승인된 전용 후보 페이지와 “다음 결과 보기” 동작으로 바꿨다. 서버 query/cursor, 중복 제거, 추가 실패 목록 보존을 더 강하게 고정했다.
- 상세 편집 입력 수는 사람 격자 설명 추가로 9에서 10으로 바꿨고, 빈 값의 null patch와 자동값 보존을 별도 시험으로 고정했다.
- 등록의 3열 짧은 행은 자동 판독 격자 표시 대신 저장 가능한 사람 격자 설명 입력을 받는다. 3열 구조와 기존 다른 입력 기대는 유지했다.
- 과거 후보 대역의 숫자 인자는 새 서버 query 객체로 정규화했다. 제품 경로는 생성 후보 페이지를 사용하고 `/datasets` fetch-all이나 브라우저 로컬 필터를 사용하지 않는다.
- 새 대표 그림 쓰기 PermissionGate 적용점을 `P8-E01-APPLY-POINTS-DRAFT.md` 표에 실제 파일과 동작 기준으로 추가했다.

## intent 대조

연결 intent `dev-package/intent/2026-09-09-upload-layout-preview.md`의 1~10을 이 레인 범위와 대조했다.

- 1~3: 기존 HTML 기반 업로드·상세 구성을 보존하면서 대표 그림, 사람 격자 설명, 계보 후보를 실제 저장·조회 흐름에 연결했다. 전체 화면 배치 재설계는 이 레인의 승인 범위가 아니다.
- 4: 이 레인의 create/PUT/GET/DELETE/patch/cursor 흐름은 행동 시험으로 검증했다. 실제 파일 업로드부터 다운로드까지의 통합 사용자 여정은 전체 작업의 후속 검증이다.
- 5~7: 포맷별 reader·렌더와 전송/분석 진행 상태는 backend·viz 및 다른 frontend 레인의 소유 범위이며 이 레인에서 완료를 주장하지 않는다.
- 8~9: 대표 그림 저장 단계를 등록과 분리하고 실패·재시도·삭제·늦은 응답을 검증했다. 계보 후보도 검색 세대와 추가 페이지 실패를 분리했다.
- 10: 정적 CSS 계측만 수행했다. 같은 장면의 실제 브라우저 시각 대조는 Astra/상위 작업의 후속 검증이다.

전체 intent 기준 미달은 실제 파일 통합 여정(4), 포맷별 reader/렌더(5~6), 전송·분석 진행 흐름(7), 실제 브라우저 시각 대조(10)이며 모두 이 소비 레인 밖에서 계속 검증해야 한다. 승인된 대표 그림·격자 설명·계보 후보 소비 범위에 대한 미달과 초과는 0건이다. 50MP/S3 제한, backend, 계약 생성, 배포 결과는 이 레인의 완료 근거로 주장하지 않는다.
