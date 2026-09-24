# K3 계보 — 평가 재료

여기 있는 것은 **정답**뿐이다. 러너도 판정 기준도 수치도 여기 없다.

## 파일

| 파일 | 무엇인가 |
|---|---|
| `lineage-cases.json` | 사람이 등록한 실제 계보 엣지. `eval/k4-search/fixtures/reference/dev-data-snapshot.json` 의 `parents` 를 그대로 옮긴 것이고, 옮겨 적다 틀렸는지는 `services/core-api/tests/test_k3_candidate_recall.py::test_계보_정답이_참조_스냅샷과_한_글자도_어긋나지_않는다` 가 **매 게이트에서** 대조한다(측정 표식이 안 붙은 시험이다). |

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
  `LlmLineageSuggester` 가 선 뒤(WU2) 잰다.
- **합격/불합격 게이트가 아니다.** 종료코드로 판정하지 않는다. 산출물은 수치와 표본 한계다.
- **일반화의 근거가 아니다.** 자식 4 · 엣지 6 · 후보 모집단 9(dev 가시 25건 중 9건)다.
  distractor 가 없다시피 하고, 6엣지로 승격·확대를 결정하지 않는다. 미달은 「불충분」이 아니라
  **「판정 보류 · 표본 확장」**으로 적는다.
- **`recent` 전략의 상위 순위는 신호가 아니다.** 참조 9건은 한 번에 적재돼
  `last_modified_at` 이 마이크로초로만 갈린다 — 그 순서는 실제 최신성이 아니라 적재 역순이다.
  recall@20(=모집단 전체 포함 여부)만 전략과 무관하게 읽을 수 있다.

## 어떻게 돌리나

```
COLAB_K3_PROBE_OUT=<절대경로.json> bash gates/tools/service-tests.sh core-api k3_probe
```

환경변수가 없으면 **skip 이 아니라 error** 다. 출력 경로가 이미 있으면 준비 실패로 멈춘다.
결과 원시 JSON 과 읽는 표는 `dev-package/reports/k3-lineage-probe/` 에 둔다.
