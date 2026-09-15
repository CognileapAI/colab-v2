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

## 원격 확인
- 준비 PR: https://github.com/CognileapAI/colab-v2/pull/61 (develop → product, 초안).
- promotion run 34909164276 성공. product-safety도 push/PR 모두 성공.
- 잘못된 head 시험 PR 62 / run 34909205702는 출처 오류로 exit 1. PR은 미병합 종료하고 이번 시험용 branch만 삭제했다.
- PR CI run 34909164280은 frontend-gates 실패로 전체 failure. 처음에는 오래된 시험 준비로 판단했으나, 독립 재검토에서 관측 간격·Lv0 출처의 필수화가 미승인임을 확인했다. 해당 필수화에 맞춰 시험을 수정하는 접근을 중단했다.
- 다른 CI job은 성공, dormant-tests는 기존 변경 경로 조건으로 skipped. compatibility 성공.
- 전체 CI 실패도 병합 차단에 반영하도록 ci-required를 추가한다. 기존 두 필수 검사는 유지한다.
- ci-required의 실제 run 명령에 실패·취소·누락·skip 결과를 넣는 3개 시험 RED→GREEN, 기존 CI 정책 2개 회귀 통과.

최종 원격 CI 통과 전에는 준비 PR을 병합 가능 완료로 보고하지 않는다.

## 사양 판정 대기
- 기준: `dev-package/intent/2026-09-13-upload-form-rev2.md`의 미승인·Ted 판정 필요 표기, UF-1 blocked/UF-3 회신 전 착수 금지. R-B의 Lv0 게이팅은 표시 조건이며 두 칸 필수·400 판정은 폐기됐다.
- 사용자 결정 필요: 새 등록의 관측 간격 값·단위, 새 Lv0 등록의 출처 주소·내려받은 날을 선택 입력으로 유지할지 화면/API 모두 필수로 바꿀지.
- 격리 사본의 시험 변경 실험은 원본 복원했다. 42→4 실험은 수용/통과 증거가 아니며 부모 브랜치에 반영하지 않았다.
- CI 출처·안전 검사 연결은 완료했지만, 준비 PR 전체 CI는 실패하므로 초안을 유지한다. product 보호를 완화하지 않는다.
- `ci-required` 이름은 PR에만 사용하고 push는 `ci-push-summary`로 분리한다. 좁은 push 차분의 성공이 전체 PR 검사 결과를 대체하지 않도록 한다.

## 2026-09-15 후속 사용자 결정

질문 “관측 간격과 Lv0 출처 정보는 기존 승인대로 선택 입력으로 되돌려서 수정할까요?”에 사용자 “엉”. 두 필드군의 새 필수화를 기각하고 화면/API 선택 입력 복원을 승인했다. 다른 미결 항목은 변경하지 않는다. 실제 변경과 CI 결과는 후속 기록한다.

## 선택 입력 복원 구현·로컬 검증
- 화면의 관측 간격/Lv0 출처 필수 배지와 빈 값 차단을 제거했다. 빈 선택 필드는 요청에서 빠지고, 기간 검사와 출처 표시 조건은 유지한다.
- 승인된 즉시 부모 연결 동작에 맞춰 사라진 확인 버튼을 누르던 시험을 정리했다. 연결 결과·전송값 검증은 유지한다.
- frontend-test: 123파일 / 1457시험 통과, 실패 0. worker task 75dd4d760eab4bffae43e58bbf0f6847 보고서를 부모가 직접 검증했다. green 1 / red(판정) 0 / red(준비) 0.
- 소유 11파일을 합류하기 전후 SHA256과 부모 복사본을 대조해 동일함을 확인했다. API 제품 코드는 변경하지 않았고 0/음수 간격의 400 거부 시험을 추가했다.
- 직접 API 시험의 환경 입력 부재는 준비 실패로 분리한다. 일회용 시험 DB 게이트 및 GitHub core-api 검사 결과가 나오기 전 API 통과를 주장하지 않는다.
- 원격 최종 CI 재검증 대기. 준비 PR은 아직 초안이다.

## 최신 통합 버전의 CI 증거 검사 수정
- 선택 입력 복원 커밋 `e65ae6289f1eb877d114ae562684e4cee7237388`의 GitHub core-api는 1295 passed / skipped 0 / E2E 6 deselected였다. 준비 실패였던 로컬 직접 실행과 구분한다.
- 다른 작업의 공통 하네스가 develop `84d0e9f5b165a0bc03c79568568e9f31062abdd3`에 합류했다. 선택 입력 수정 11파일의 SHA256은 그대로다.
- PR CI run `34911726733`: 제품·개별 검사 job은 성공했으나 `required-gates`는 `PR merge commit differs from checkout`으로 판정 실패했다. 전체 CI 통과나 병합 가능으로 판정하지 않는다.
- 실제 Actions checkout은 `76c15d58330199877aa1ce53303628a0592e8125`이며 GitHub commit API의 부모는 순서대로 product `6db30323a78a4e63f3e28810db0f325b69551979`, develop `84d0e9f5b165a0bc03c79568568e9f31062abdd3`다.
- 해당 run에서 내려받은 생산자 증거 40건은 모두 같은 commit/tree이며 exit 0이다. 집계 실패를 이 성공으로 덮지 않는다.
- 수정 범위: webhook의 merge SHA 단순 동일 검사 대신 실제 Git commit 객체의 base/head 부모를 검증한다. 실제 checkout·생산자 SHA/tree/run/attempt·오프라인 재검증 결속은 유지한다. 잘못된 부모와 변조 증거의 거부 회귀를 확인한 뒤 최신 원격 CI를 다시 실행한다.
- 최초 배포 연결과 운영 reseed는 여전히 미실행이다. 이 준비 PR은 배포 workflow나 승인 artifact를 포함하지 않는다.
- 수정 통합 후 `harness-contract-selftest` 42 tests / exit 0 / green 1 / red(판정) 0 / red(준비) 0. 부모가 worker 보고서의 task·파일 hash도 직접 검증했다.
- 실제 다운로드한 증거와 재구성한 PR 이벤트 fixture(null merge SHA)를 함께 로컬 재검증해 생산자 15건 green / 판정 0 / 준비 0 / N/A 0을 확인했다. 원래 GitHub run의 실패를 성공으로 변경한 것이 아니며, 수정 버전의 실제 원격 CI는 별도로 확인한다.
- 커밋 객체가 없는 과거 PR 증거는 새 검증에서 준비 실패다. 이를 새 성공 증거로 재사용하지 않는다.
