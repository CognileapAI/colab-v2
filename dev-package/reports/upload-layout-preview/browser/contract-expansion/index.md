# 업로드 계약 확장 실제 브라우저 검증

대상은 통합 브랜치 `71e6592`의 화면·core-api·pipeline-worker·viz-render다. 1440×1000 headless Chrome을 agent-browser로 조작했고, 매 실행마다 일회용 PostgreSQL과 local upload/preview 저장소를 새로 만들었다. 운영 URL·운영 계정·공유 DB는 사용하지 않았다.

## TDD 실행

- RED: `COLAB_UI_CASES=contract`로 격리 스택을 실행했을 때 `upload-preview-suite.py`가 미등록 사례를 `KeyError: 'contract'`로 거절했다.
- GREEN: 같은 focused 사례를 실제 HDF 원천과 명시적 worker/viz/journey로 다시 실행해 종료코드 0과 21단계 PASS를 얻었다.
- 원천: `MOD15A2H.A2019273.h27v05.061.2020313082826.hdf`, 9,731,088 bytes, SHA256 `ab7eda26634a5e2f13016acc7e1f8d0cd1daf3924bdbc58538b066b12c12e8a6`.
- 실행 기록: [journey.json](final/contract/journey.json). 다운로드 파일은 저장소에 남기지 않고 브라우저 다운로드 직후 원천 SHA256과 대조했다.

## 계약 확장 결과

| 검증 | 실제 결과 | 근거 |
|---|---|---|
| 초기 업로드 크기 | 1440×1000에서 모달 폭 620px | [01-empty.png](final/contract/01-empty.png), [snapshot](final/contract/01-empty.txt) |
| 대표 그림 실패 복구 | 가짜 PNG 바이트는 이미지 PUT에서 거절되고 복구 화면에 남았다. 같은 이름의 데이터셋은 1건, 사용자 그림 행은 0건이었다. 저장된 등록 입력과 원본 관리 UI는 제거됐다. | [07-recovery.png](final/contract/07-recovery.png), [snapshot](final/contract/07-recovery.txt) |
| 같은 ID 재시도 | 여정의 실제 PNG 캡처로 그림 PUT만 다시 실행했다. URL의 데이터셋 ID와 DB의 유일한 ID가 같고 사용자 그림 행은 1건이었다. | `journey.json.datasetCreateProof` |
| 파일명 계보 검색 | 이름 대신 `a1-body.csv`를 입력해 DSA1 `A 강우 원자료`와 본체 파일명을 확인한 뒤 연결했다. 수정·제거·재연결도 reload 후 유지됐다. | [07-connections.png](final/contract/07-connections.png), [snapshot](final/contract/07-connections.txt) |
| 사람 격자 설명 | `사람이 적은 HDF 격자 설명`이 주값, 자동 `2400x2400`이 보조로 표시됐다. 편집에서 사람값을 지운 뒤 DB가 NULL이고 reload 화면의 주값은 `2400x2400`으로 복귀했다. | `journey.json.gridBeforeClear`, `journey.json.gridAfterClear` |
| 대표 그림 상세 수명 | 인증 GET으로 받은 Blob이 실제 이미지로 decode됐고 reload 후 유지됐다. 다른 PNG로 교체해 새 object URL을 확인하고 reload했다. 자동 그림 복귀 뒤 사용자 그림 행 0건과 자동 preview decode를 확인했다. | [08-detail.png](final/contract/08-detail.png), [09-automatic-fallback.png](final/contract/09-automatic-fallback.png) |
| 기존 전체 여정 | HDF 업로드·분석·렌더·확장, 프로젝트·기간·변수·계보 CRUD, 상세 편집, 원본 다운로드 SHA256이 이어서 통과했다. | `journey.json.steps` 21건, [10-final.png](final/contract/10-final.png) |

실행 중 드러난 두 번의 대기는 제품 실패가 아니라 브라우저 harness 활성 방식이었다. 이미 decode된 그림이 남은 상태에서 비동기 교체를 기다리도록 기존 `drawn` 판정을 새 URL 전환 대기로 좁혔고, 상세의 파일 버튼은 snapshot ref에 초점을 둔 뒤 Enter로 실제 활성화했다. 격자 빈 값은 `fill('')` 대신 Ctrl+A/Backspace로 입력 이벤트를 발생시키고 DOM 값과 격리 DB의 NULL을 함께 확인했다.
