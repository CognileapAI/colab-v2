# ST 검색 브라우저 사용자 여정 — 2026-09-13

사용자 승인: 기존 admin 로그인 정보를 사용해 중단된 ST 검증을 진행. 기존 legacy admin 로그인에 성공하여 신규 계정은 생성하지 않았다. 앞선 DB 로그인 목록만의 확인으로 생긴 인증 준비 실패를 해소했다. 비밀번호·토큰은 기록하지 않는다.

## 대상과 범위

- URL: https://www.colab-hydro.com
- 실측 이미지: core-api / frontend / ai-service 모두 `acf2532f0f9d`. 현재 작업 사본 `6ff0eecd`와 구분한다.
- 도구: agent-browser, 전용 세션 `st-search-journey`.
- 계정: 기존 admin, accountId `000000000000000000HYMETSA1`, labId `00000000000000000000HYMETS`. 업로드·편집 true. 서비스 계정 관리 권한은 false이며 이름만으로 서비스 운영자로 판정하지 않았다.
- 신규 합성 4×4 GeoTIFF 430 bytes만 사용. datasetId `01M2BF9P79K1APP13JZAZE3J61`, fileId `01M2BF8BGDKDNY7W8XNH0DJN5N`.
- 자료명: `ST검색검증20260913 합성 강우`. 실제 연구용 아님을 설명에 명시. 최종 공개 범위는 연구실 구성원 전체. 테스트 자료는 보존했고 기존 자료 수정·삭제, 계정 변경, 배포는 하지 않았다.
- Sonnet 실제 호출 품질 평가는 계속 보류. 이번 검색 화면은 낱말 그대로 해석했음을 표시했다.

## 관측 결과

1. 실제 로그인 → 업로드 → 분류·메타데이터 입력 → 데이터셋 생성 성공.
2. 파일 관리에서 검색 근거를 열어 검증 역할, 직접 관측 아님, 합성 시험용 출처 원문을 입력하고 **확인하고 저장** 성공.
3. 새로고침 후 GET 근거 API 200, reviewed / revision 1 / fileRevision 1 및 원문 해시 확인. 검색 결과에서 상세로 복귀한 UI에서도 확인됨, 검증 체크, 동일 원문 유지 확인.
4. `ST검색검증20260913 검증용`: 연구실 15건 중 결과 1건. 신규 자료와 검증 파일 역할·출처가 표시됨. 결과 버튼을 눌러 같은 datasetId 상세로 이동 성공.
5. `ST검색검증20260913 검증용 결측률 0%`: 결과 12건. 신규 자료에는 검증 역할 확인 / 품질 미확인을 분리 표시하여 품질 충족을 단정하지 않음. 하지만 `0%` 낱말로 다른 자료까지 결과가 확대됨: 품질 문구와 별개인 검색 정확도 보강 항목.

## 실패 및 후속

- 작은 CSV는 파일 분석 단계에서 형식 인식 실패. 등록 성공으로 계수하지 않고 합성 GeoTIFF로 변경했다.
- **소유자 접근 결함:** 처음 나만 보기로 등록하자 올린 계정에서도 bodyAccessible=false, canDownload=false, canDelete=true. 새로고침에도 동일. 동일 신규 자료를 UI에서 연구실 구성원 전체로 변경한 후 나머지 검색 여정을 수행했다. 이 전환은 소유자 접근 시험을 통과시킨 것이 아니다.
- 독립 읽기 검토 결과: `dev-package/prd/PRD-260905-적용전기획.md`의 잠김=소유자만 의도와 달리 `d2_access.py`는 열림 또는 grant만 판정하고 소유자를 조회하지 않음. 배포판 acf2532f0f9d와 작업 사본 모두 같은 누락. 수정·회귀 검증은 미수행.
- 다음 개발: 소유자 본체 접근을 권한 경계 전반과 함께 수정·검증하고, 품질 수치 토큰이 후보를 넓히는 검색을 골든 사례로 보강. 전체 ST 수용 완료로 선언하지 않는다.

## 로컬 증거

`/home/ttlhi10/.cache/colab-st-search-journey-20260913/`에 사전 PLAN.json, evidence-after-reload.json, quality-results.json, private-own-locked.png, search-reviewed.png, search-quality.png, evidence-detail.png와 합성 입력 파일을 보존했다. 이들은 이번 브라우저 실측이며 이전 로컬 고정 API 골든 검사와 구분한다.
