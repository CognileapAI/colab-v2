# eval/k4-search — 자연어 검색 실측 하네스

## Stage 3 골든셋과 낱말 기준선

- `golden-set.md`: 12문항의 의미·정답·오답·근거 기준.
- `golden-cases.json`: 같은 질문의 제품 ID·후보 범위·필수 포함 조건. 의미 판정의 정본은 Markdown이다.
- `golden_baseline.py`: 로컬 LiteralInterpreter → dev의 실제 D3 검색 함수. LLM·사전·그래프·HTTP/UI·근거 생성은 평가하지 않는다.
- `test_golden_baseline.py`: 잘림·중복·복수 정답 누락·범위 밖 후보·의미 미판정의 오판 방지 시험.

기존 dev 운영자 환경에서 `COLAB_DEV_SSH`, `COLAB_DEV_KEY_FILE`을 프로세스에 제공한다. 값은 출력하지 않는다.

```bash
python3 -m unittest discover -s eval/k4-search -p test_golden_baseline.py
python3 eval/k4-search/golden_baseline.py --output dev-package/reports/stage3-ai-search-plan/literal-run-new.json
python3 eval/k4-search/golden_baseline.py --mode expanded --output dev-package/reports/stage3-ai-search-plan/expanded-run-new.json
```

출력 경로가 이미 존재하면 준비 실패로 종료한다. 전체 스코프 매치 전수(최대100)를 확인한 뒤 문항별 허용 ID로 제한한다.
따라서 전체 연구실 검색이 0건일 때만 발동하는 이름 유사도 폴백은 그대로 유지된다. 독립 9건 DB의 실행과 동일하다고 주장하지 않는다.
필수 정답 포함 여부/빈 후보 검사는 자동, 추천 이유·품질·조건 단정은 미판정으로 별도 기록한다.
종료코드 0=자동 포함 검사 실패 없음(전체 품질 통과 아님), 1=자동 판정 실패, 78=준비 실패.
코드·해석기·평가셋·자료 스냅샷 hash, 실행 시점의 후보25건 및 검색 벡터, 순위·소요시간을 결과에 보존한다.
소요시간은 D3 호출 시간이며 LLM 지연·API 왕복·사용자 체감 속도를 뜻하지 않는다.
`--mode expanded`는 dev AI의 실제 낱말 해석·기능어 제거·사전·그래프를 실행하며 LLM은 호출하지 않는다.
`--omit-topic-filter`는 expanded에서만 쓰는 분리 실험으로, 확장 검색어를 유지하고 topic을 None으로 전달한다. 제품 정책 변경이 아니다.
사전 snapshot은 한 번 읽어 재사용하며 원자료·해석 결과·소스 hash를 결과에 보존한다. degraded 확장은 준비 실패다.

## 기존 그래프 확장 비교

`sessions/K1b-ONTOLOGY-CONTENT §D` 의 질의 예시들은 **지면 대조**였다 — 그 절이 스스로
`[미확인]` 이라 적었다. 여기 있는 둘이 그 대조를 `SELECT` 로 바꾼다.

| 파일 | 무엇 |
|---|---|
| `seed-15.sql` | `SEED-DATA §3.1` 의 데이터셋 15건. **이름·주제·원천 표기 세 칸뿐**이다 — `0005` 의 tsvector 가 훑는 글자가 그 셋이다 |
| `measure.py` | 그래프 확장 **전/후**를 같은 질의로 돌려 결과 집합·순위·일한 엣지를 나란히 찍는다 |

**제품 코드가 아니다.** 배포 단위 둘을 한 프로세스에서 부르는 것은 측정을 위해서다.
제품에서 두 단위는 HTTP 로만 만나고, core-api 는 AI 체인에 붙지 않는다
(`PLAN-SoT §9-〈90〉-㉮`). 이 하네스도 그 성질을 지킨다 — 그래프는 `colab_ai` 만 읽는다.

## 돌리는 법

```
# ① 두 체인의 DB (RESTART.md ④ 와 같은 방식 — 호스트 포트를 열지 않는다)
docker run -d --name <레인>_pg --tmpfs /var/lib/postgresql/data:rw,size=512m \
  -e PGDATA=/var/lib/postgresql/data/pg -e POSTGRES_PASSWORD=<임시> postgres:16-alpine

# ② 플랫폼 — 선언 스키마 + 앱 롤 + 이 시드
#    ⚠ 소유자에게 GRANT CREATE ON DATABASE 가 필요하다 (schema.sql 이 pg_trgm 을 만든다)
# ③ AI     — db/ai/schema.sql + db/ai/seed/*.sql
# ④ 측정
python3 eval/k4-search/measure.py <platform-app-url> <ai-app-url>
```

## 2026-08-25 실측 (`K4-b` · `〈89〉`·`〈90〉`)

| 질의 | 그래프 없이 | 그래프 있음 | 판정 |
|---|---|---|---|
| 재격자화한 NDVI 자료 | 8건 · 1위 `D-01` | 8건 · **상위 3 = `D-03`·`D-04`·`D-05`** | `NDVI` 가 이미 8건을 물었으므로 **집합이 아니라 순위**가 바뀐다. 올라온 것이 **정확히 셋**이고 `D-06`(Co-Kriging)은 아니다 — `F-4d` 기각(`〈86〉`)이 결과에 그대로 보인다 |
| 전처리한 강우 자료 | 3건 | **3건 (그대로)** | 금지 목록이라 확장이 **시작되지 않는다**. 초안이 걱정한 「15건 중 12건」이 일어날 수 없다 |
| Bilinear 로 만든 자료 | 1건 | **1건 (그대로)** | 하향 전용. 상향으로 탔다면 `D-03`·`D-05` 가 오답으로 딸려 왔다 |
| 한반도 전체 식생 자료 | 9건 | 10건 (`D-02` 추가) | `E2-1`. §D-5 가 예고한 `D-02` 혼입까지 그대로 재현된다 |
| 25년도 낙동강 유역 강우 | 3건 | 3건 | **그래프는 0건을 없애 주지 않는다** — 낙동강 자료가 애초에 없다 |

접두 질의(`〈89〉`)가 새로 여는 것 — 「충청」 **0 → 5건** · 「가뭄」 **0 → 1건** · 「격자」 **0 → 1건**.
유사도 보조 팔이 받는 것 — 「HSR레이더견본」·「레이더견본」 → `D-15`(자리 = `이름(비슷한 말)`).
**여전히 0건인 것** — 「강수량」·「위성」·「다운스케」. 매칭은 표기를 넘지 못한다.

## 고정 snapshot 조건 결합 실험

`python3 eval/k4-search/structured_probe.py --output <새 JSON 경로>`

제품 검색과 분리된 오프라인 후보 실험이다. `unverified` 조건은 충족으로 표시하면 안 된다. 추가6문항은 구현 전 공개돼 blind holdout이 아니다. [범위와 결과](../../dev-package/sessions/20260912-ai-search-structured-probe.md)를 함께 읽는다.

## 조건·파일 역할과 로컬 제품 비교

- `file-role-evidence.json`, `condition-evidence.json`: 설명서 출처를 검토한 연구용 주석. 제품 DB 메타데이터가 아니다.
- `condition_assessment.py`: supported/contradicted/unknown 조건 컴포넌트.
- `heldout-cases.json`, `heldout_eval.py`: 최초 미공개6문항은3통과/3실패. 수정 후 결과는 개발 회귀 검사이며 파일 검색3개와 조건 컴포넌트3개를 구분한다.
- `search_journey.py`: 격리 DB와 실제 core/frontend를 사용하는 브라우저 여정. HTTP 해석 대역을 쓰므로 실제 AI/LLM 품질 평가가 아니다.

```bash
python3 -m unittest discover -s eval/k4-search -p 'test_*.py'
python3 eval/k4-search/heldout_eval.py --output <새 JSON 경로>
services/ai-service/.venv/bin/python eval/k4-search/golden_baseline.py --mode local-expanded --frozen-expansion dev-package/reports/stage3-ai-search-plan/expanded-baseline-01.json --output <새 JSON 경로>
```

`local-expanded`는 고정 사전/그래프를 실제 로컬 SearchService에 공급하고 dev D3를 읽기 전용 호출한다. 코드 hash를 기록하며 배포된 API나 전체 답변 검증으로 보고하지 않는다. 최신 결과와 미충족은 [실행 기록](../../dev-package/sessions/20260913-ai-search-execution.md)에 모은다.

## 설명서 원문 수집·변경 검사

`reference_evidence.py --reference-root <레퍼런스 루트> --output <새 JSON>`은 DOCX 문단과 내용 hash 및 snapshot 파일 ID 바인딩을 저장한다. 같은 이름 문서가 복수이면 임의 선택하지 않는다. `--verify <기존 JSON>`은 원문 변경·삭제를 검사한다. 자동 의미 추출이나 제품 저장이 아니며 대상 데이터 파일의 내용 버전까지 검사하지 않는다.
