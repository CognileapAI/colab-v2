# K3 계보 — 평가 재료와 러너

여기 있는 것은 **정답과 러너**다. 수치는 여기 없다 — 실측 결과는 `dev-package/reports/k3-lineage-probe/` 에 선다.

## 파일

| 파일 | 무엇인가 |
|---|---|
| `lineage-cases.json` | 사람이 등록한 실제 계보 엣지. `eval/k4-search/fixtures/reference/dev-data-snapshot.json` 의 `parents` 를 그대로 옮긴 것이고, 옮겨 적다 틀렸는지는 `services/core-api/tests/test_k3_candidate_recall.py::test_계보_정답이_참조_스냅샷과_한_글자도_어긋나지_않는다` 가 **매 게이트에서** 대조한다(측정 표식이 안 붙은 시험이다). |
| `llm_lineage_probe.py` | J2~J9 러너(WU4b). 기록된 후보에 **제품 `LlmLineageSuggester`** 로 순위·근거·확신도를 붙이고, 전송만 감싸 지연을 잰다. 후보는 여기서 고르지 않는다. |
| `test_llm_lineage_probe.py` | 러너 판정 함수의 **오판 방지** 시험(unittest · 망·모델·DB 0건). 실측 수치는 되돌려 셀 수 없으므로 판정 함수만 여기서 본다. |

## 두 절반

| 절반 | 어디서 도나 | 모델 호출 |
|---|---|---|
| 후보 절반 | `services/core-api/tests/test_k3_lineage_probe.py`(표식 `k3_probe`) — 일회용 DB 에서 제품 `routes/ingestion._lineage_candidates` 로 고른 후보를 `COLAB_K3_CANDIDATES_OUT` 에 적는다 | 0회 |
| 모델 절반 | `llm_lineage_probe.py --candidates <그 파일>` — DB 에 닿지 않는다 | 자식 4 × 2회 + 대조군 4 × 2회 = **16회** |

두 절반이 같은 후보를 봤다는 것은 그 JSON 파일 하나가 보증한다. 러너가 스스로 후보를 만들면
그 보증이 사라진다 — **후보를 고르는 것은 D3 의 주인인 core-api 다**(`〈72〉-㉮` 와 같은 분담).

## 대조군 (J5)

같은 자식 4건에서 **정답 부모를 후보에서 뺀다.** 후보에 없는 것을 억지로 고르면 red 다 —
「모른다고 말하는가」의 유일한 직접 측정이고, 다른 항목은 전부 「맞혔는가」만 잰다.

## J1 은 무엇인가

**J1 = 후보 포함률(recall@k).** core-api 가 D3 에서 고른 후보 k건 안에 그 자식의 **진짜 부모**가
들어 있는가. 그것 하나다.

측정하는 것:

- `select_lineage_candidates`(`services/core-api/src/colab_core/domains/d3_catalog.py`)가
  전략 두 벌(`recent` 무필터 최근순 · `filtered` 주제∪토큰)로 고른 순서.
- 정답 부모의 **순위**와 k=5·10·20 에서의 포함 여부.
- 무엇이 그 후보를 끌어왔는가(`matched_by` — 주제인가 · 어느 토큰인가 · 그냥 최근순인가).

## J1 은 무엇이 **아닌가**

- **모델 성능이 아니다.** 이 측정에는 모델 호출이 0회다. 순위·근거·확신도(J2~J9)는
  `llm_lineage_probe.py` 가 따로 잰다(WU4b · 2026-09-24 실측).
- **합격/불합격 게이트가 아니다.** 종료코드로 판정하지 않는다. 산출물은 수치와 표본 한계다.
- **일반화의 근거가 아니다.** 자식 4 · 엣지 6 · 후보 모집단 9(dev 가시 25건 중 9건)다.
  distractor 가 없다시피 하고, 6엣지로 승격·확대를 결정하지 않는다. 미달은 「불충분」이 아니라
  **「판정 보류 · 표본 확장」**으로 적는다.
- **`recent` 전략의 상위 순위는 신호가 아니다.** 참조 9건은 한 번에 적재돼
  `last_modified_at` 이 마이크로초로만 갈린다 — 그 순서는 실제 최신성이 아니라 적재 역순이다.
  recall@20(=모집단 전체 포함 여부)만 전략과 무관하게 읽을 수 있다.

## 어떻게 돌리나

```
# 후보 절반 — 표식 `k3_probe` 의 두 시험이 함께 돈다(J1 + 후보 기록). 둘 다 출력 경로를 요구한다.
COLAB_K3_PROBE_OUT=<절대경로.json> COLAB_K3_CANDIDATES_OUT=<절대경로.json> \
  bash gates/tools/service-tests.sh core-api k3_probe

# 모델 절반 — `OPENAI_API_KEY` 가 프로세스 환경에 있어야 한다(없으면 78).
services/ai-service/.venv/bin/python eval/k3-lineage/llm_lineage_probe.py \
  --repeats 2 --candidates <후보 JSON> --output <결과 JSON>

# 판정 함수를 고쳤을 때 — 기록된 원문에 판정만 다시 건다(모델 호출 0회).
... llm_lineage_probe.py --rejudge <기존 결과 JSON> --candidates <후보 JSON> --output <새 JSON>
```

환경변수가 없으면 **skip 이 아니라 error** 다. 출력 경로가 이미 있으면 준비 실패로 멈춘다.
러너의 종료코드는 0 = 측정 완료 · 78 = 준비 실패(키·입력 파일·출력 충돌)이고 **판정 게이트가 아니다.**
결과 원시 JSON 과 읽는 표는 `dev-package/reports/k3-lineage-probe/` 에 둔다.

### 판정 함수를 고치면 모델을 다시 부르지 않는다

모델을 다시 부르면 답까지 바뀌어 **고친 것이 판정인지 모델의 기분인지 갈리지 않는다.**
그래서 `--rejudge` 는 원문을 그대로 두고 판정만 다시 건다. 2026-09-24 1회차에서
근거 토크나이저가 라틴 어간에 붙은 한국어 조사(`npy가`·`tif는`)를 통째로 한 토큰으로 세어
J3 위반 12건을 만들었고, 그 12건 중 10건이 **러너의 오판**이었다 — 고친 뒤 2건이 남았다.
