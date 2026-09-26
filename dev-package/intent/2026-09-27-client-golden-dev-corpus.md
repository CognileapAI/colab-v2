# Intent: 구서영 7문항 골든이 dev 실데이터로 검색되게 하는 근거 보강 — 시험 코퍼스 등록 + 검토 사실 적재
메타 — 발의자: Ted · 작성 2026-09-27 · 승인: @sungwooHa 2026-09-27 "답 5건대로 승인한다"(미해결 질문 1~5 답 반영 · dev 쓰기 GO는 적용 직전 별도 · handle = 이 머신 gh 로그인 = CODEOWNERS)
<!-- 승인 시 메타 줄의 「승인: 미승인」을 승인: @<GitHub handle> <YYYY-MM-DD> "<원문>" 으로 바꾼다 · 새 꼴 승인은 첫 `메타` 줄 한 줄 안에 적는다 · 승인자 = develop 리뷰 권한자 · 이 줄을 담은 커밋을 사람이 병합하면 승인이고 그 뒤 이 파일은 줄 추가만 허용된다(게이트 intent-ref · ADR-0007) -->

## 문제
- 발의: Ted, 2026-09-27. 원문 「저게 검색되게하려면 어떤 데이터」 → 「intent만 하고 새로운세션에서 하려고하는데 가능하나」.
  - 「저게」 = 실무자(구서영 석사) 요구 7문항. 골든셋 `eval/k4-search/client-golden.json` CLIENT-001~007(출처 「2026-09-13 실무자 요구」).
- 요지: 7문항을 받는 코드 경로는 있다. dev에 그 조건을 만족하는 **검토된 파일 근거**가 없어 dev에서는 7문항 모두 결과 0건이 예상된다.
  - 코드 판정(2026-09-26 읽기 전용 평가 · 입력 파일은 임시라 필요한 사실을 이 절에 옮긴다): 부분 6 · 충족 1(CLIENT-007).
  - dev 실측은 아직 없다. 「0건」은 아래 사실 분포에서 나온 추론이다 `[추론 · dev 조회 전]`.
- 7문항은 LLM 해석이 아니라 규칙 플래너(경로 1)가 받는다.
  - `services/core-api/src/colab_core/app/routes/catalog.py:507-509` — `client_search.plan_query()`가 `recognized`면 모델을 부르지 않고 `_client_search`로 간다.
  - 2026-09-27 기준 `plan_query` 실측(core-api venv · now=2026-09-27T03:00Z · 질의는 골든 원문 그대로):

| 문항 | intent | 뽑힌 조건 | 확인 질문 |
|---|---|---|---|
| CLIENT-001 | recommend | variable=land_surface_temperature | 연구 조건 요청 1건 |
| CLIENT-002 | compare | variable=land_surface_temperature · platform=satellite | 연구 조건 요청 1건 |
| CLIENT-003 | discover | variable=precipitation · region=seoul · representation=spatial | 없음 |
| CLIENT-004 | reference_match | variable=wind_speed · region=jeju · 기준 변수 precipitation | 기준 파일 선택 1건 |
| CLIENT-005 | discover | descriptionAll=[수질, 한강] · coverageYear=2025 | 없음 |
| CLIENT-006 | latest | variable=particulate_matter · directObservation=true · provider=환경부 · uploadedMonth=2026-09 | 없음 |
| CLIENT-007 | finest | region=korean_peninsula · platform=satellite · representation=spatial_grid · maxResolutionM=10.0 | 없음 |

- 경로 1이 결과를 내는 조건(코드 근거)
  - 판정 원천은 `d3_search_evidence` 중 `status='reviewed'`이고 현재 파일 판(`file_revision=content_revision`)인 **본체 파일** 행뿐이다(`domains/d3_client_search.py:100-106`).
  - 모든 조건이 **같은 파일 한 개**에서 성립해야 한다(`d3_client_search.py:48-50` 주석 · `contracts/search/semantics.json:29` invariant 「all constraints must hold on one current reviewed file」).
  - 근거 행이 없는 데이터셋은 `JOIN LATERAL` 내부 조인이라 후보에서 빠진다(`d3_client_search.py:116`).
  - 확인 질문이 하나라도 있으면 후보 조회를 하지 않는다(`catalog.py:699-701`). 그래서 CLIENT-001·002는 연구 조건(`context.research`), CLIENT-004는 기준 파일(`context.referenceFileId`)을 준 두 번째 요청에서만 결과가 난다.
  - 결과는 본문 접근 가능(`bodyAccessible`) 자료만 남긴다(`catalog.py:713-714`).
- dev 적재 근거의 사실 분포(dev 현재 = 1회차 승격 payload `dev-package/reports/evidence-promotion/round-1-2026-09-26/promotion-plan/promoted-payload.json` sha256 `41f488a4…` · 28 데이터셋 · 반영 기록 `dev-package/intent/2026-09-21-evidence-promotion.md:230-236`)
  - variable: 반사도 4 · 강수량 3 · NDVI 4 · 엽면적지수 4 · 지표온도 2 · 표고·경사향·토지피복·SPI·SPEI 각 1 — **풍속·수질·미세먼지 0**.
  - region: 경기남부충청 1 · 대한민국시군구 2 · 타일 코드(T51SYB·T52SCE·h27v05·h28v05) 각 2 — **서울·제주·한반도 0**. 2회차 지역(남한·한반도 5칸)은 dev 반영 GO 대기다(`2026-09-21-evidence-promotion.md` 「판정 결과 — 2회차 지역」 끝 문단).
  - provider: 기상청 6 · Copernicus 2 · 국가기상위성센터 1 — **환경부 0**.
  - platform: ground 8 · model 4 · satellite 14(1회차 승격으로 생김). 2026-09-26 평가 문서의 「platform 0」은 승격 전 원본 payload 기준이라 dev 현재와 다르다.
  - representation: **0**(규칙 `representation-from-shape`는 초안 · 미측정 보류).
  - statistics: `monthly_mean` 2 — 일최고·일최저의 월평균 0.
  - nativeResolutionM: 30 2 · 500 2 · 2000 2 — **10 이하 0**.
  - 지표온도 2건(seq 17·18 GK-2A LST)은 region이 없다(2회차 기록 「없음 3(15·17·18)」). 연구 조건의 지역을 만족할 수 없다.
- 문항별 막힌 자리

| 문항 | dev에 없는 사실 |
|---|---|
| CLIENT-001·002 | 지역이 있는 지표면 온도 파일 · 일최고·일최저 월평균 통계 |
| CLIENT-003 | region 서울 · representation(spatial_grid / point_observations) |
| CLIENT-004 | 제주 강수량 기준 파일 · 같은 기간의 제주 풍속 파일 |
| CLIENT-005 | 요약에 「수질」「한강」이 함께 있는 자료 · 2025와 겹치는 기간 |
| CLIENT-006 | provider 환경부 · 미세먼지 변수 · 이번 달 업로드 |
| CLIENT-007 | region 한반도(또는 하위) · representation spatial_grid · nativeResolutionM ≤ 10 |

## 원한 결과 (proposed outcome)
- dev에 **시험 코퍼스**(데이터셋·본체 파일·검토된 파일 근거)를 더한다. 그 뒤 CLIENT-001~007 각각이 경로 1에서 `supported` 결과를 1건 이상 낸다.
  - CLIENT-001·002는 아래 고정 연구 조건을 준 두 번째 요청 기준이다. CLIENT-004는 기준 파일을 준 두 번째 요청 기준이다. 첫 요청의 확인 질문 응답은 그대로 유지된다(설계상 의도 · `client_search.py:190-203`).
- 문항별 필요 자료와 사실(facts 키 = `d3_search_evidence.facts` · 값은 경로 1이 비교하는 형태)

| 문항 | 자료(역할) | 필수 facts | 기대 히트 |
|---|---|---|---|
| CLIENT-001 | LST-A 위성 지표면 온도 월 통계 | variable 「지표면 온도」 · region 「한반도」 · platform "satellite" · period ⊇ 연구 기간 · statistics ["monthly_mean","monthly_mean_daily_max","monthly_mean_daily_min"] · nativeResolutionM 1000 | LST-A 1건 → 「이 조건의 추천 후보는 ‘LST-A’」 |
| CLIENT-001 | LST-B 위성 지표면 온도 월평균만 | LST-A와 같되 statistics ["monthly_mean"] · nativeResolutionM 2000 | 통계 조건으로 제외(대조군) |
| CLIENT-002 | LST-A · LST-B | 위와 같음 | 2건 → 「하나를 최적이라고 단정하지 않습니다」 |
| CLIENT-003 | 서울 강수량 격자 npy | variable 「강수량」 · region 「서울」 · representation "spatial_grid" · format "npy" | 히트 |
| CLIENT-003 | 서울 강수량 지점 csv | variable 「강수량」 · region 「서울」 · representation "point_observations" · format "csv" | 히트(공간 CSV 포함 확인) |
| CLIENT-003 | 서울 강수량 집계표 csv(대조군) | 위와 같되 representation "table" | 제외(포맷 ≠ 공간 표현 확인) |
| CLIENT-004 | 제주 강수량(기준 파일) | variable 「강수량」 · region 「제주」 · period P | 기준 파일로 선택 |
| CLIENT-004 | 제주 풍속 | variable 「풍속」 · region 「제주」 · period = P(시작·끝 문자열 동일) | 히트 |
| CLIENT-004 | 제주 풍속 다른 기간(대조군) | period ≠ P | 제외(기간 완전 일치 확인) |
| CLIENT-005 | 한강 수질 ×2 | 요약(`dd.summary`)에 「수질」「한강」 둘 다 · period가 2025와 겹침 | 2건 |
| CLIENT-005 | 낙동강 수질(대조군) | 요약에 「수질」만 · period 2025 겹침 | 제외(AND 확인) |
| CLIENT-006 | 환경부 미세먼지 관측 | variable 「PM10」 또는 「미세먼지」 · provider 「환경부」(정확히) · directObservation true · **업로드 월 = 검증 월** | 히트 |
| CLIENT-007 | Sentinel-2 10 m 한반도 격자 | region 「한반도」(또는 하위 「남한」) · platform "satellite" · representation "spatial_grid" · nativeResolutionM 10 | 히트(동률 포함 · 작은 순 1위) |

- 고정 연구 조건(검증 때 화면 「연구 조건 입력·변경」 폼에 넣는 값 · 폼 필드 `frontend/src/components/search/SearchAssessment.tsx:55-80`)
  - CLIENT-001: 변수 지표면 온도 · 지역 한반도 · 기간 2025-07-01~2025-07-31 · 통계 「일최고값의 월평균」「일최저값의 월평균」.
  - CLIENT-002: 같은 변수·지역·기간 · 통계 없음.
  - LST-A·B의 period는 이 기간을 포함해야 한다(`client_search.py:229-231` · `d3_client_search.py:85-87`).
- 규칙(모든 자료 공통)
  - 사실은 `status: reviewed`로만 싣는다. 초안(draftFacts)은 경로 1이 읽지 않는다(`d3_client_search.py:103`).
  - 한 데이터셋의 조건 사실은 전부 같은 본체 파일에 있어야 한다. 적재기는 데이터셋의 모든 본체 파일에 같은 facts를 쓴다(`dev-package/tools/dataset_evidence_apply.py:42-43` · `:97-120`). 그래서 **데이터셋당 본체 파일 1개**로 만든다.
  - 지역 값은 어휘표의 표기만 쓴다 — 서울 = 「서울」「서울시」「서울특별시」, 제주 = 「제주」「제주도」「제주특별자치도」, 한반도 = 「한반도」와 하위 「남한」「대한민국」「충청권」(`contracts/search/semantics.json:11-25` · 비교는 공백·`_`·`-` 제거 후 정확 일치 `services/core-api/src/colab_core/kernel/region_scope.py:23-50`). 「서울 강서구」 같은 값은 맞지 않는다.
  - 변수 값은 어휘표 별칭과 공백 제거 후 같아야 한다(`semantics.json:3-10` · `d3_client_search.py:64-68`). 예: 「지표면 온도」·「지표 온도」·「LST」 · 「강수량」 · 「풍속」 · 「수질」 · 「미세먼지」·「PM10」·「PM2.5」.
  - platform·provider·representation·directObservation은 JSON 값 정확 일치다(`d3_client_search.py:94-96`). provider 「환경부」는 별칭 없이 그대로 맞아야 한다.
  - 데이터셋 이름은 dev 안에서 유일해야 한다. 적재기가 이름으로 데이터셋을 찾고 겹치면 멈춘다(`dataset_evidence_apply.py:38-40` · `:79`).
  - 합성 자료는 실제 관측 제품처럼 보이지 않게 표기한다(Q1 · 아래 「표기」).
- 표기(지어내지 않음)
  - 근거 규칙: 「못 찾으면 정직한 빈 상태. 억지 제안 금지」(`.agents/rules/product.md:78`) · 골든 교정문 CLIENT-007 「제품명/건수 추정 금지」 · CLIENT-002 「세계 전체 제품을 조사했다고 말하지 않음」(`eval/k4-search/client-golden.json`).
  - 참고: 발의 메모의 「P-9/P-10(지어내지 않음)」은 원문과 다르다. P-9·P-10은 연구실 경계 규칙이다(`dev-package/PERMISSION-PRINCIPLES.md:56` · `:59`). 이 intent에는 P-9가 다른 방식으로 걸린다 — 시험 코퍼스는 검증 계정이 볼 수 있는 연구실에 등록해야 결과에 나온다.
  - 기존 dev 자료에 합성 표기 관례는 찾지 못했다(`dev-package/tools`·`dev-package/reports` 검색 · `ownerManaged`는 운영자 계정 비밀번호 관리 표시다 `dev-package/tools/dev-reseed/accounts.py:7`). 테스트 목적 프로젝트로는 「포멧테스트」가 있다(`dev-package/tools/dev-seed/plan-manifest.yaml` projects).
  - 제안: 새 프로젝트 「검색골든-시험」에 모은다. 합성 자료는 이름 앞에 「[dev 시험]」을 붙이고, 요약 첫 문장을 「dev 검색 골든 시험용 합성 자료 — 실제 관측 제품이 아니다」로 쓴다. 실자료 표본은 원 출처·라이선스를 요약과 근거 `source.text`에 적는다. 이름에 대괄호가 허용되는지는 구현 때 확인한다 `[미확인]`.

### 검증(적용 뒤 확인 절차)
- 전(before): 적용 전에 dev에서 7문항을 경로 1로 실행해 건수를 기록한다(CLIENT-001·002는 고정 연구 조건 포함 요청 · CLIENT-004는 기존 강수량 파일 1개를 기준으로 준 요청 포함).
- 후(after): 같은 요청을 다시 실행한다.
  - API: `POST /api/v1/dataset-searches`(검증 계정 = #167 캡처와 같은 운영자 계정 또는 등록 연구실 구성원). 응답 `assessment.status` · `totalCount` · `items[].datasetId` · `assessment.comparisons[].fileId`를 기록한다.
  - 화면: agent-browser로 문항별 결과 화면 캡처 7+2장(001·002·004는 두 번째 요청 화면 포함).
  - 대조군이 결과에 없는지 확인한다(서울 표 CSV · 제주 다른 기간 풍속 · 낙동강 수질 · LST-B(CLIENT-001)).
- 표(PR 요약에 싣는다)

| 문항 | 전 | 후 | 히트 데이터셋 | 대조군 제외 |
|---|---:|---:|---|---|
| CLIENT-001 … 007 | 실측 | 실측 | 이름 · dev id | 예/아니오 |

- 게이트: `bash gates/run.sh intent-ref`(이 문서) · 문서·데이터만 바뀌므로 `search_golden` 표식 pytest(`services/core-api/tests/test_client_search.py`)는 불변 확인용으로 한 번 실행한다.
- 적재 증거: dry-run·적용·재 dry-run 셈 · 스냅숏 sha256 · payload sha256을 PR 요약에 적는다(#169와 같은 꼴).

## 가치 가설
- 실무자(구서영)와 Ted는 7문항을 dev 화면에서 실제로 쳐서 조건 검색이 무엇을 답하고 무엇을 되묻는지 볼 수 있게 된다. 그래서 코드 판정(부분 6 · 충족 1)을 실데이터 화면으로 확인하고, 남은 플래너 공백(범위 밖 목록)의 우선순위를 실측으로 정할 수 있다.
- 확인 방법: 검증 절의 전후 표(0건 → n건)와 문항별 캡처. 대조군이 모두 빠지면 불변식(포맷 ≠ 공간 표현 · 기간 완전 일치 · AND · 해상도 상한)도 dev에서 확인된다.

## 영향 범위
- 사용자 / 화면: dev 카탈로그·검색 결과에 시험 코퍼스 데이터셋이 보인다(검색골든-시험 프로젝트). 화면 코드 변경 없음.
- 서비스 · 스키마 · 계약: 제품 코드·스키마·계약 변경 없음. dev 데이터만 바뀐다.
  - 새 파일(저장소): 시험 코퍼스 정의·payload·적용 기록을 `dev-package/reports/client-golden-dev-corpus-<날짜>/` 아래에 둔다(payload 꼴 = `colab-dataset-evidence/1` · 예시 `promoted-payload.json`의 `datasets[]` 행).
  - 적재 경로: 기존 적재기 `dev-package/tools/dataset_evidence_apply.py --payloads <새 payload> --reviewer <ULID>`(#169와 같은 꼴 · `promotion-plan/apply-plan.md:43-60`).
  - 파일 바이트: Q2 권장안이면 dev S3에 시험 파일이 올라간다(제품 업로드 경로).
- 계약 파괴 여부: 아니오.

## 제약
- dev reset·재시드 금지. ops 수정 전 reset/재시드는 거부 상태다 `[오케스트레이터 전달 · 2026-09-25 dev 배포 기록]`. 기존 28 데이터셋·543 근거 행은 건드리지 않는다.
- prod(`www.colab-hydro.com`)에는 쓰지 않는다.
- dev 쓰기는 사용자 승인 범위다(`dataset_evidence_apply.py:19` 「DEV 적용은 사용자 몫」 · `:137`). 이 intent 승인이 dev 쓰기 GO를 겸하는지는 미해결 질문 1이다.
- 적재는 #169 꼴을 따른다(`apply-plan.md:43-60`).
  - dev 호스트에서 배포 이미지 `colab-v2/core-api:dev-<sha>` · 소유자 롤 URL 파일 · `PGOPTIONS=-c app.current_lab=<등록 연구실>`.
  - 되돌림 스냅숏 → dry-run(기대 missing 0) → 적용(한 트랜잭션) → 재 dry-run(evidence 0 · 멱등).
  - 검토자 `--reviewer` = 판정자 Ted의 dev 계정 ULID `01M398TXPKDM2GJP7T6GWHNDXX`(`2026-09-21-evidence-promotion.md:230`).
- 적재기는 데이터셋·파일을 만들지 않는다. 이름으로 찾은 데이터셋의 본체 파일(`d3_file.kind='본체'`)에만 근거를 쓴다(`dataset_evidence_apply.py:38-43`). 그래서 **데이터셋·본체 파일 등록이 적재보다 먼저**다(Q2).
- S3에 파일을 올리면 `.agents/rules/s3-upload.md`를 따른다 — 버킷 루트 스캔 금지 · 에뮬레이터 검증 금지 · 시크릿 비노출. 업로드는 제품 화면 경로로 한다(dev-seed 러너와 같은 방식 · `dev-package/tools/dev-seed/README.md` 「서버 API 직접 호출 없음」).
- CLIENT-006은 시간에 묶인다 — 업로드 월(서울 시간 `d.uploaded_at`)이 검증 시점 월과 같아야 한다(`d3_client_search.py:37-39` · `client_search.py:154-155`). 9월에 등록하고 10월에 검증하면 0건이다. 업로드 시각은 화면 경로로는 과거로 돌릴 수 없다.
- 기존 조건 검색 의미를 바꾸지 않는다: LST ≠ 기온 · 포맷 ≠ 공간 표현 · 원관측 해상도 ≠ 재격자 간격 · 미확인 ≠ 충족(`semantics.json:29`).
- 검증 도구 제약: `eval/k4-search/client_journey.py:1-4`는 「Never run against a deployment or production account」다. dev 검증은 API 호출과 agent-browser 캡처로 따로 한다.

## 설계트리 (grill-me 결과)
- Q1 자료 원천 — 실자료 표본인가, 표기된 합성 샘플인가
  - ⓐ 라이선스가 분명한 공공 실자료의 작은 표본 + 없는 칸만 표기된 합성 → **권장**
    - 후보(라이선스 조건은 구현 때 원문으로 확인 `[미확인]`): 기상청 ASOS 서울(108)·제주(184) 일자료 — 같은 관측소 파일에서 강수량·풍속을 나누면 CLIENT-004의 「같은 기간」이 자연히 선다 · 물환경정보시스템 한강 수계 수질측정망 2025 · 에어코리아 PM10 시간자료 · Copernicus Sentinel-2 L2A 1타일 10 m 밴드 · MODIS LST 월 합성.
    - 이유: 화면에서 보이는 이름·요약·미리보기가 실제 관측값이라 실무자 확인에 쓸 수 있다. 「지어낸 제품」 위험이 가장 작다.
  - ⓑ 전부 표기된 합성 샘플 → 반대 관점(기록): 준비가 가장 빠르고 라이선스 확인이 없다. 대신 미리보기·다운로드 내용이 실제 값이 아니고, 실무자 시연에서 「이 자료가 실제로 있나」를 다시 설명해야 한다.
  - Q1a 에어코리아 자료의 provider 값 → 원 출처 문면을 그대로 쓴다 → **권장**
    - 사실: 조건 검색은 provider 「환경부」 정확 일치만 인정한다(`d3_client_search.py:94-96`). 에어코리아 운영 주체가 원문에서 「환경부」가 아니라 「한국환경공단」 등으로 적혀 있으면 CLIENT-006은 0건이다 `[미확인 · 원문 확인 필요]`.
    - 반대 관점(기록): 시연을 위해 provider를 「환경부」로 적으면 원문과 다른 사실을 reviewed로 싣게 된다. 그 경우 CLIENT-006 자료만 합성으로 두고 「[dev 시험]」 표기를 붙이는 편이 정직하다. 기관 별칭 사전은 범위 밖(아래)이다.
  - Q1b CLIENT-007 지역 값 → Sentinel-2 타일이 한반도 상자(위도 33~39 · 경도 124~132) 안에 온전히 들면 「한반도」, 아니면 「남한」 → **권장**
    - 근거: 같은 기준이 `bbox-korea-peninsula` 규칙이다(`promoted-payload.json` `rules`). 「남한」은 `regionWithin`으로 한반도 조건에 맞는다(`semantics.json:16-24`).
    - 반대 관점(기록): 기존 타일 자료(seq 21~24)는 확정값이 타일 코드이고 「한반도」는 초안으로만 서 있다(2회차 판정). 새 자료만 「한반도」를 reviewed로 받으면 같은 성격의 자료가 다른 등급을 갖는다. 새 자료의 정본 문면(요약·근거 text)에 지역을 사람이 확정한 문장으로 적어 구분한다.
- Q2 파일 실업로드(S3)인가, 사실표만인가
  - ⓐ 데이터셋마다 작은 본체 파일 1개를 제품 업로드 화면으로 올린다(dev S3) → **권장**
    - 이유: 사실표만으로는 불가능하다. 경로 1은 `d3_file` 본체 행과 `file_revision=content_revision`을 요구하고(`d3_client_search.py:100-104`), 적재기도 본체 파일이 있어야 근거를 쓴다(`dataset_evidence_apply.py:42-43`). 제품 경로 업로드가 이 행들을 만드는 정상 경로다. 미리보기·다운로드도 함께 확인된다.
  - ⓑ DB에 데이터셋·파일 행만 직접 넣는다(바이트 없음) → 반대: 제품 경로를 우회하고(`d5_upload`·원장 없음), 다운로드 티켓이 실패하는 자료가 화면에 선다. S3 원장과 어긋나 정리 규칙(원장이 아는 것만 지움 · `s3-upload.md`)과도 충돌한다.
  - Q2a 업로드 수단 → agent-browser로 제품 화면을 밟는다(자료 10~13건) → **권장**. dev-seed 러너 확장(새 계획 파일)은 반복 필요가 생기면 별건.
    - 반대 관점(기록): 러너를 쓰면 상태 파일·재개가 생긴다. 대신 러너는 28/18 총계와 참조자료 뿌리를 전제로 한다(`dev-seed/README.md` 판정 3단). 1회성 13건에 맞추는 수정 비용이 크다.
- Q3 근거 적재 경로 — #169 payload 방식인가, dev-reseed 개선 뒤인가
  - ⓐ #169 방식: 새 payload(시험 코퍼스 행만)를 기존 적재기 `--payloads`로 싣는다 → **권장**
    - 이유: reset·재시드 없이 멱등 적재가 이미 dev에서 한 번 돌았다(`2026-09-21-evidence-promotion.md:230-236`). 새 payload에는 기존 28행을 넣지 않으므로 기존 근거 543행은 바뀌지 않는다 `[추론 · 적재기는 payload 행만 돈다 :73]`.
    - 되돌림: 새 자료만 대상이다 — 데이터셋 삭제(제품 삭제 경로)로 근거 행도 함께 사라지는지는 구현 때 확인한다 `[미확인]`.
  - ⓑ dev-reseed 개선 뒤 재시드에 포함 → 반대: 재시드가 ops 수정 전 거부 상태라 일정이 그쪽에 묶인다. 재시드 정본(DATASETS.md 4건 → 28/18)에 시험 코퍼스를 섞는 결정도 따로 필요하다.
  - Q3a payload 생성 → 손으로 쓴 정의 파일(`corpus.json`: 이름·요약·facts·provenance·source) → 작은 스크립트가 `colab-dataset-evidence/1` 꼴로 변환 → **권장**. `dataset_evidence_backfill.py`는 DATASETS.md 정본 전용이라 쓰지 않는다.
    - 반대 관점(기록): 생성기를 거치지 않으면 provenance 문구 규칙(「정본전재 · … 축자」)을 사람이 맞춰야 한다. 합성 행은 provenance를 「dev 시험 코퍼스 정의 · <파일> · 합성」으로 명시한다.
- Q4 골든 기대 히트를 `client-golden.json`에 dev id로 고정하나
  - ⓐ 고정하지 않는다. dev 기대 히트는 이 intent 산출 폴더의 별도 파일(`expected-hits.json` · 데이터셋 이름 기준 + 적용 뒤 dev id 기록)에 둔다 → **권장**
    - 이유: `client-golden.json`은 합성 픽스처 회귀(`services/core-api/tests/test_client_search.py:10` `search_golden`)의 입력이고 scope 문구가 「예시 제품/건수는 사실로 고정하지 않음」이다. dev id는 재시드마다 바뀐다.
  - ⓑ `client-golden.json`에 dev id 칸을 더한다 → 반대: 한 파일이 환경 독립 판정과 dev 스냅숏을 함께 싣게 된다. 재시드 뒤 골든이 틀린 상태가 된다.

## 미해결 질문
- 1. 이 intent 승인이 dev 쓰기(업로드 + 근거 적재) GO를 겸하는가, 적용 직전에 따로 GO를 받는가. → **적용 직전 별도 GO**(Ted 2026-09-27). 업로드·적재 전에 되돌림 스냅숏·dry-run 결과를 보이고 GO를 받는다.
- 2. Q1 실자료 표본 채택 시 라이선스 원문 확인 담당과 CLIENT-006 provider 처리(Q1a). → **Q1ⓐ 실자료 표본 + 빈 칸만 합성**(Ted 2026-09-27). 라이선스 원문은 구현 에이전트가 확인해 출처·조건을 요약과 `source.text`에 적는다. CLIENT-006은 provider를 원문대로 두고, 원문이 「환경부」가 아니면 이 1건만 「[dev 시험]」 합성으로 대체한다(Q1a 권장안).
- 3. 등록 연구실 — HYMETS(기존 28건과 같은 곳)인가, 시험 전용 연구실인가. 시험 전용이면 검증 계정의 가시 범위를 따로 맞춰야 한다(P-9). → **HYMETS**(Ted 2026-09-27). 프로젝트 「검색골든-시험」으로 구분한다.
- 4. CLIENT-006 검증 시점 — 등록과 검증을 같은 달에 끝내는가, 매달 재업로드가 필요한 문항으로 기록하는가. → **2026-09 안에 등록·검증을 끝내고 월 의존을 기록한다**(Ted 2026-09-27). `expected-hits.json`·PR 요약에 「달이 바뀌면 재업로드 없이는 0건」을 적는다.
- 5. CLIENT-004 기준 파일 선택 화면은 `GET /datasets` 한 번의 결과에서 고른다(`SearchAssessment.tsx:91`). 첫 쪽 밖이면 목록에 안 보일 수 있다 `[미확인 · 쪽 크기 미조회]`. 검증 때 확인하고 막히면 API 요청으로 대신 기록할지. → **막히면 API 요청(`context.referenceFileId`)으로 대신 기록하고 화면 제약을 PR 요약에 적는다**(Ted 미지정 · 권장 기본값 2026-09-27).

## 범위 밖 (명시 제외)
- 아래는 플래너·제품 공백이다. 이 intent에서 고치지 않고 별도 intent 후보로 기록한다.
  - CLIENT-005 따옴표 필수 — 따옴표 없는 「설명에 수질과 한강 둘 다」는 recognized=False로 LLM 갈래 OR 검색이 된다(`client_search.py:145-151` · 평가 실측).
  - CLIENT-007 「10m보다 해상도 좋은」 표현은 해상도 조건이 빠진 채 recognized=True가 된다(`client_search.py:137-139` · `:204-207`).
  - CLIENT-006 기관 별칭 사전(환경부 ↔ 한국환경공단·국립환경과학원 등) · 「관측」이 directObservation=true를 자동 강제하는 규칙(`client_search.py:133-136`).
  - 플래너가 인식하지 못하면 만든 확인 질문이 버려진다(`catalog.py:507-509`는 recognized만 본다).
  - LLM 경로 `totalCount`가 현재 쪽 건수다(`catalog.py:663`) — 조건 경로는 전체 일치 건수(`:746`).
  - 연구 맥락 저장소 부재 — 연구 조건은 요청 1회용(`client_search.py:22-64`). CLIENT-001 원 기대답변의 「현재 연구를 살펴보았을 때」는 이것이 필요하다.
  - 대화형 응답(되묻고 이어가기)은 하지 않는다 — 정본 Policy_데이터_찾기 §1.3-5 · `.agents/rules/product.md` §3·§5 판단 그대로.
- 기존 dev 자료의 사실 수정(seq 17·18 LST 지역 · 2회차 지역 반영 · representation 규칙 승격)은 각 승격 회차 몫이다.
- `client-golden.json`·합성 픽스처·회귀 시험 변경(Q4).
- dev-reseed 절차 개선과 재시드 정본(DATASETS.md 4건)에 시험 코퍼스를 넣는 일(Q3ⓑ).
- prod 반영.

## 확인
- 프론티어 공집합 확인: 2026-09-27 — 미해결 질문 5건 답 완료(1~4 Ted · 5 권장 기본값). 남은 분기 없음.
- 승인자 확인 문장(원문 그대로 · 메타 줄의 "<원문>" 과 같다): 답 5건대로 승인한다
- 재개봉 금지: 아니오

## 참조
- 발의 입력: 2026-09-26 읽기 전용 평가(임시 파일 · 필요한 사실은 「문제」 절에 옮김) · 골든 `eval/k4-search/client-golden.json`
- 선행 intent: `dev-package/intent/2026-09-21-evidence-promotion.md`(1회차 dev 반영 `:230-236` · 2회차 지역 GO 대기) · `dev-package/intent/2026-09-26-region-containment-expansion.md`(`regionWithin`)
- 적재 선례: `dev-package/reports/evidence-promotion/round-1-2026-09-26/promotion-plan/apply-plan.md:43-69` · `promoted-payload.json`(schema `colab-dataset-evidence/1`)
- 코드
  - 플래너: `services/core-api/src/colab_core/app/client_search.py:22-64`·`:85-209`·`:212-259`·`:278-298`
  - 후보 SQL: `services/core-api/src/colab_core/domains/d3_client_search.py:28-129`·`:146-152`
  - 라우트: `services/core-api/src/colab_core/app/routes/catalog.py:507-509`·`:679-747`
  - 어휘: `contracts/search/semantics.json:1-30` · `services/core-api/src/colab_core/kernel/search_semantics.py` · `services/core-api/src/colab_core/kernel/region_scope.py:23-50`
  - 화면: `frontend/src/components/search/SearchAssessment.tsx:8-9`·`:55-80`·`:82-91`
  - 적재기: `dev-package/tools/dataset_evidence_apply.py:1-24`·`:38-43`·`:68-121`
  - 스키마: `db/platform/schema.sql:466`(topic CHECK 6값 — 새 자료는 강수 외 NULL)
- 규칙: `.agents/rules/product.md:78` · `.agents/rules/s3-upload.md` · `dev-package/PERMISSION-PRINCIPLES.md:56-59`
- 결정: 〈N〉 (병합 시 기입)
