# ai-service

**담는 도메인** — D9 Ontology & Knowledge Graph · D10 AI Services

별도 배포 단위인 이유는 성능이 아니라 **격리**다. 모델 호출이 느리거나 실패해도 카탈로그 조회와 업로드는 계속 돌아야 한다.

> **AI 없이도 v2는 완결된 제품이다.** 이 성질을 잃는 설계는 거부한다.

## D9 — Ontology & Knowledge Graph  (소유: 수문학 도메인)

| 층 | 내용 |
|---|---|
| 개념 | 변수 · 좌표계 · 공간 위계(유역 ⊃ 소유역 ⊃ 행정구역) · 관측소 · 가공 방식 계열 · 출처 기관. 관계와 동의어 |
| 인스턴스 | 실제 데이터셋·파일 엔티티를 개념에 건 링크 |
| 색인 | 개념·설명 임베딩 — 그래프 탐색의 **진입점** |

**인스턴스는 D3 Catalog의 사본이 아니라 참조다.** 본문은 D3에 있고 여기는 ID와 개념 링크만 든다. 사본을 두면 두 개가 갈라진다.

`ontology/` 아래의 의미 체계는 **수문학 소유자가 정한다.** "낙동강 유역이 어떤 행정구역을 포함하는가"는 개발 판단이 아니다.

## D10 — AI Services  (소유: AI 엔지니어링)

두 지점만 담당한다.

| 지점 | 하는 일 |
|---|---|
| **계보 제안** (E-04) | 업로드 파일 메타 + KG 조회 → 가공 전 데이터 후보 + 가공 방식 제안 |
| **자연어 검색** (E-02) | 질의 해석 → 관련도 + 근거 한 줄 |

## 🔴 절대 규칙 — 이 서비스는 기록하지 않는다

```
D10 제안  →  제안 저장소(임시, D10 소유)  →  화면에서 사람이 확인
                                                    │
                                                    ▼
                                     D4 Lineage 커밋 (사람 행위로만)
```

- **D4(Lineage) 쓰기 Port가 존재하지 않는다.** `ai-no-lineage-write` 음성 테스트가 강제한다
- 확신도는 `확실 | 애매 | 모름` enum. **퍼센트 금지**
- 근거 필드 **필수**
- **[모두 승인] 없음** — 배치 승인 엔드포인트를 노출하지 않는다
- 못 찾으면 **정직한 빈 상태**. 억지 제안 금지
- 검색은 뒤진 범위를 먼저 밝히고, 근거는 한 줄 고정

## 저장소 분리

`db/ai/` 를 쓴다. **플랫폼(`db/platform/`)과 마이그레이션 체인이 분리된다** — 온톨로지 한 줄 추가가 플랫폼 마이그레이션을 기다리면 안 되고, 그 반대도 안 된다.

**이 단위가 카탈로그 쪽 DB 에 붙는 것은 검색 하나뿐이고, 붙는 방식이 좁다** — 읽기 전용 트랜잭션 · D3 검색 열만 · 경계는 세션 GUC 로 심고 RLS 가 지운다(`kernel/db.py` · `app/catalog_search.py`). 마이그레이션 체인은 여전히 만지지 않는다.

## 자연어 검색 — `K4-a` (`POST /searches`)

`PLAN-SoT §9-〈72〉-㉮`·`〈81〉` 이 그은 선 그대로다.

| 층 | 하는 일 | 파일 |
|---|---|---|
| **질의 해석기** | 자연어 → **검색어·필터**. LLM 의 일은 여기까지다 | `app/interpret.py` |
| **사전 3종** | 검색어를 D9 로 넓힌다 (방법 용어 13 · 주제 동의어 5 · 지명 별칭 4 = 22행) | `domains/d9_ontology.py` · `app/dictionaries.py` |
| **`tsvector` 실행기** | `0005` 의 생성 열 3 + GIN 3 으로 찾고 **순위를 낸다** | `app/catalog_search.py` |
| **조립** | 계약 모양으로 접는다. 근거 한 줄을 만든다 | `domains/d10_ai_services.py` |

- **LLM 은 순위를 정하지 않고 결과 본문을 쓰지 않는다.** 응답에서 읽는 값은 `isDataQuery`·`terms`·`topic` 셋뿐이다.
- **키가 없어도 검색은 돈다** — 질문의 낱말이 그대로 검색어가 되고 `degraded: true` 로 그 사실을 밝힌다.
- **한계**: `ts_config` 가 `'simple'` 이라 형태소를 자르지 않는다. 「강수량」은 한 낱말이고 **「강수」로는 안 잡힌다**(`〈81〉-㉲`). 접두 질의·`pg_trgm` 은 매칭 규칙을 바꾸는 일이라 이 레인이 혼자 넣지 않는다.

### 돌리기

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
COLAB_AI_TEST_PLATFORM_DB_URL=... COLAB_AI_TEST_DICT_DB_URL=... .venv/bin/python -m pytest
```

일회용 DB 는 `services/core-api/tests/fixtures/setup-db.sh`(플랫폼) + `db/ai/schema.sql`·`db/ai/seed/k2_ontology_seed.sql`(사전) 로 만든다.
⚠ `ai-no-lineage-write` 게이트의 L2 층은 이 디렉터리의 **모든 텍스트 파일**을 훑는다 — `.venv/` 도 포함이다(현재 의존 17개로 green).

### 런타임 환경변수

| 이름 | 없으면 |
|---|---|
| `COLAB_AI_CATALOG_DB_URL` | 검색이 **뒤진 범위를 먼저 밝힌 빈 결과 + `degraded`** 를 낸다 |
| `COLAB_AI_DB_URL` | 사전으로 넓히지 않고 질문의 낱말 그대로 찾는다 |
| `OPENAI_API_KEY` · `COLAB_MODEL_HELPER` | 문자열 해석으로 떨어진다. **검색 자체는 산다** |

⚠ 앞의 둘은 **아직 `infra/staging/compose.i2.yml` 에 없다.** 배선은 인프라 레인의 일이다.
