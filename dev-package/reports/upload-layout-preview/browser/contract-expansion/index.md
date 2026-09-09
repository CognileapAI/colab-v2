# 업로드 계약 확장 실제 브라우저 검증

최신 대상은 `codex/upload-preview-finalfix` 구현 커밋 `6d1107c`의 화면과 `c2a2f0c`에 통합된 core-api·pipeline-worker·viz-render다. 1440×1000 headless Chrome을 agent-browser로 조작했고, 매 실행마다 일회용 PostgreSQL과 local upload/preview 저장소를 새로 만들었다. 운영 URL·운영 계정·공유 DB는 사용하지 않았다.

## TDD 실행

- RED: frontend focused 회귀는 날짜 전송·415 화면·415 source 계약 4건이 실패하고 140건이 통과했다. 413은 별도 RED에서 1건 실패했다.
- GREEN: 날짜를 UTC일 경계로 만들고 영구 이미지 오류를 보존·차단한 뒤 같은 focused 회귀 145/145와 typecheck가 통과했다.
- BROWSER GREEN: 실제 HDF 원천과 명시적 worker/viz/journey로 `finalfix-green3`를 실행해 종료코드 0과 25단계 PASS를 얻었다.
- 원천: `MOD15A2H.A2019273.h27v05.061.2020313082826.hdf`, 9,731,088 bytes, SHA256 `ab7eda26634a5e2f13016acc7e1f8d0cd1daf3924bdbc58538b066b12c12e8a6`.
- 실행 기록: [journey.json](finalfix-green3/contract/journey.json). 다운로드 파일은 저장소에 남기지 않고 브라우저 다운로드 직후 원천 SHA256과 대조했다.

## 계약 확장 결과

| 검증 | 실제 결과 | 근거 |
|---|---|---|
| 초기 업로드 크기 | 1440×1000에서 모달 폭 620px | [01-empty.png](finalfix-green3/contract/01-empty.png), [snapshot](finalfix-green3/contract/01-empty.txt) |
| 대표 그림 영구 오류 복구 | 가짜 PNG의 415 서버 이유를 그대로 표시하고 같은 파일 재시도를 비활성화해 새 그림이나 자동 그림을 요구했다. 같은 이름의 데이터셋은 1건, 사용자 그림 행은 0건이었다. | [07-recovery.png](finalfix-green3/contract/07-recovery.png), [snapshot](finalfix-green3/contract/07-recovery.txt), `journey.json.representativeRecoveryProof` |
| 같은 ID의 새 그림 저장 | 여정의 실제 PNG 캡처를 새로 골라 그림 PUT만 다시 실행했다. URL의 데이터셋 ID와 DB의 유일한 ID가 같고 사용자 그림 행은 1건이었다. | `journey.json.datasetCreateProof` |
| 파일명·기간 계보 검색 | `a1-body.csv`로 DSA1을 찾았다. `2026-09-09T23:59:59.999999Z` 후보가 9일 끝에는 포함되고 10일 시작에는 제외됐으며, 시작·끝 초기화 뒤 파일명 결과가 복귀했다. | [07-connections.png](finalfix-green3/contract/07-connections.png), [snapshot](finalfix-green3/contract/07-connections.txt), `journey.json.lineagePeriodBoundary` |
| 계보 cursor | 첫 서버 페이지 25건에서 `다음 결과 보기` 뒤 29건으로 늘고 뒤쪽 `페이지 후보 01`이 추가됐다. | `journey.json.lineageCursorPaging` |
| 사람 격자 설명 | `사람이 적은 HDF 격자 설명`이 주값, 자동 `2400x2400`이 보조로 표시됐다. 편집에서 사람값을 지운 뒤 DB가 NULL이고 reload 화면의 주값은 `2400x2400`으로 복귀했다. | `journey.json.gridBeforeClear`, `journey.json.gridAfterClear` |
| 대표 그림 상세 수명 | 인증 GET으로 받은 Blob이 실제 이미지로 decode됐고 reload 후 유지됐다. 다른 PNG로 교체해 새 object URL을 확인하고 reload했다. 자동 그림 복귀 뒤 사용자 그림 행 0건과 자동 preview decode를 확인했다. | [08-detail.png](finalfix-green3/contract/08-detail.png), [09-automatic-fallback.png](finalfix-green3/contract/09-automatic-fallback.png) |
| 기존 전체 여정 | HDF 업로드·분석·렌더·확장, 프로젝트·기간·변수·계보 CRUD, 상세 편집, 원본 다운로드 SHA256이 이어서 통과했다. | `journey.json.steps` 25건, [10-final.png](finalfix-green3/contract/10-final.png) |

finalfix의 실패 실행 세 건은 수용 근거와 분리해 보존한다. `finalfix`는 native date input에 `fill`이 값을 만들지 못해 6단계 뒤 30초 timeout, `finalfix-green1`은 cursor 버튼의 semantic click이 활성화되지 않아 5단계 뒤 30초 timeout, `finalfix-green2`는 새 cursor 시드가 기존 재연결 후보를 첫 페이지 밖으로 밀어 18단계 뒤 selector 실패였다. 각각 `failure.txt`·`failure.png`·`journey.json`을 남겼고 통과로 계산하지 않았다. `finalfix-green3`는 native date picker 키 입력, 접근성 ref 버튼 활성화, 재연결 파일명 검색을 사용해 종료코드 0으로 끝났다.
