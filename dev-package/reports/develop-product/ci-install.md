# CI·승격 검사 최초 설치 — 2026-09-15

- 준비용 product-promotion workflow는 검토한 tooling commit `1899505de2affe2c006361dd726e04f8c9750214`에서 Python validator를 실행한다.
- 같은 저장소 develop → product와 유효한 head/base SHA만 검사한다. 공개 GitHub 호스팅 runner와 contents:read만 사용한다.
- 준비 PR에는 운영 배포 workflow를 설치하지 않는다. manifest 승인 artifact도 생성하지 않아 운영 배포 승인으로 재사용할 수 없다.
- product-safety는 배포 경계 및 최초 초기화 실패·중복 방지 시험을 각각 실행한다. 신규 게이트 실행 비트를 Git 인덱스에 기록했다.
- product 보호는 유지하며, 준비 PR 자동 병합은 하지 않는다. 사용자가 검사 결과를 확인하고 직접 병합한다.
- 실제 배포 연결은 별도 단계다. 정상 manifest/artifact workflow를 검토·설치하고 product/base와 develop/head의 workflow hash 일치를 확보한 뒤 첫 배포 PR을 준비해야 한다.

## 로컬 검증
- product-release-selftest: 74 passed, skip 0, green 1 / red(판정) 0 / red(준비) 0.
- product-reseed-selftest: 87 passed, skip 0, green 1 / red(판정) 0 / red(준비) 0.
- work-item-consistency: green 1 / red(판정) 0 / red(준비) 0, 기존 파싱 대상 밖 10건 미검사.
- scripts unittest: 247건, exit 0, 기존 skip 10건은 통과 건수와 구분.
- 실제 workflow의 pin에서 validator 추출 후 run 명령 실행: 정상 develop→product exit 0; 다른 head/fork/다른 base exit 1. 4/4 확인.
- 고정 tooling 커밋에 product-deploy.yml이 없음을 Git tree로 확인.

원격 CI·준비 PR 상태는 실행 후 추가한다. 로컬 결과를 GitHub 검증 완료로 해석하지 않는다.
