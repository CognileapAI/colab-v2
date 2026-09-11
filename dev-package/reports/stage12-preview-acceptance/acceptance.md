# 사용자 여정 증거 수용

이 폴더는 첫 검증 레인의 증거 사본이다. `summary.json`의 성공 수는 레인 관측값이며 전체 완료 조건 수용 수가 아니다. 원문을 보존하고 아래 판정으로 구분한다. raw HAR와 활성 gate-summary는 복사하지 않았다.

- BF-8·BF-9·WU-PREVIEW: 독립 검토와 부모 확인 후 완료 수용.
- BF-7: 실제 PNG 파일 저장은 확인했다. 명시된 non-headless Chrome 확인은 후속 검증 대상이다.
- BF-11: CSS 변수 값은 확인했다. 실제 다섯 사용 자리의 계산 스타일·시각 확인은 후속 검증 대상이다. BF-13은 이 선행 수용을 기다린다.
- U-1·F-3: 실제 S3 재개, 파일 관리와 폴더 저장 증거가 있다. 명시된 최종 전종 게이트는 아직 남는다.
- J1: 8/9 성공 표기는 일부 동작 확인을 전체 완료 조건으로 확대한 값이다. B 격자 후보 제외와 직접 재사용 404, 판별 가능한 다른 격자의 경고·계속·거리, 첫 렌더 도달 시각과 수렴 알림 1회를 추가 확인한다. 폴더 시험은 합성 FileSystemEntry의 실제 브라우저 드롭이며 OS 파일 관리자 드래그는 아니다.

dev 제품 SHA는 `f8ac7ee`다. CI `34572152548`은 정확한 `5aef8a3`에서 frontend 1204/core 1062/pipeline 275/viz 418 통과를 확인했으며 해당 제품 경로의 f8→5a 차이는 없다. CI 제외 core 6/pipeline 50/viz 42 및 dormant·harness 미실행을 최종 all 통과로 합산하지 않는다.

현재 판정은 `dev-package/work-items.yaml`, 후속 기록은 `dev-package/sessions/20260911-stage12-final-verification.md`를 따른다. 이 폴더의 TEST B 패킷은 미실행 초안 이력이며 후속 실행 패킷을 대신하지 않는다.
