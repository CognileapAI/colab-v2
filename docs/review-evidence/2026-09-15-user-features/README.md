# 이슈 33·41·42 검토용 agent-browser 증거

- 제품 코드: `8f966563cc35a4d0863c98fda9485a36b3bd1afa` (PR #67 실제 병합 SHA)
- 캡처 환경: 로컬 일회용 PostgreSQL + 실제 core-api/pipeline-worker/viz-render/frontend + agent-browser. A 연구실·A 연구원과 생성 GeoTIFF만 사용.
- 아래 PNG는 dev 사이트 캡처가 아닙니다. dev 현재 로그인 자격을 확보하지 못해 배포 후 로그인 사용자 여정은 미실행입니다.
- dev 배포는 2026-09-15 완료: doctor 15 통과 / 실패 0 / 제외 0, 서비스 4개 정상, 공개 웹 파일 96개 hash 일치.
- 브라우저 시나리오: scripts/user-feature-journey.py. 이번 캡처는 프로젝트 연결 영역의 스크롤과 화면 높이만 보강했으며, 실제 UI·DB 검증 9단계를 유지했습니다.
- journey.json은 이번 실행의 동일 uploadId·datasetId·projectId 및 실제 검증 결과입니다. 일회용 환경은 종료 시 정리했습니다.

| 파일 | 보여 주는 것 |
|---|---|
| 02-unfinished-after-reload.png | 업로드 후 닫고 새로고침해도 등록 이어하기 표시 |
| 03-registration-restored.png | 재전송 없이 파일이 복원된 등록 1단계 |
| 03b-registration-project-click.png | 등록 중 추가 버튼 클릭으로 연결된 프로젝트 |
| 04-detail-preview.png | 등록된 데이터셋의 실제 디코딩된 미리보기 |
| 05-project-linked.png | 상세에서 연결 후 새로고침해도 1건 유지 |
| 06-project-removed.png | 해제 후 새로고침하면 0건 유지 |

149 MB 실파일 RSS 및 dev 5종·3회 반복 측정은 이번 증거에 포함되지 않습니다.
