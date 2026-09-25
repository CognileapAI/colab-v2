# K3 계보 제안 — WU5 재측정 (28건 코퍼스 · 2026-09-25)

> ⚠ K3 본래 목적 미달 — 업로드 쪽 메타가 fileName 뿐이라 새로 채운 period·crs·grid 축이 근거로 쓰이지 않았다(모델 침묵 38/38). K3 플래그는 켜지 않는다. 후속 intent: `dev-package/intent/2026-09-25-k3-upload-axes-remeasure.md`

측정이지 게이트가 아니다. 판정 기준은 측정 전에 등록한 `dev-package/reports/corpus-expansion/wu5-preregistration-2026-09-25.md`
(커밋 `82ecf733` · 등록 2026-09-25T08:07:10+09:00)의 §4·§5 를 그대로 읽는다. 이 문서는 새 선을 만들지 않는다.
등록에 없는 지표는 「사후 추가」로 표시했다.

## 요지

- 두 절반 모두 **78 없이 완주**했다. 후보 절반 종료코드 0 · 모델 절반 종료코드 0 · 모델 호출 **38회**(상한 50 · 후보 0건 칸 12 은 부르지 않음).
- 선행 결함(등록 §7): 수정 전 러너는 새 정답에서 **78** — `Preparation failure: ValueError unexpected case count: children=5 edges=10`. 건수 검사를 `sample_limits` 에서 읽게 고친 뒤 완주했다.
- 후보 쪽 자동 메타는 처음으로 채워졌다(period 28 · crs 24 · grid 26 · fileName 28 · variables 0). 그러나 **업로드 쪽 축은 `fileName` 하나뿐**이라(아래 「이상」 ①) 규칙 팔 근거 25건이 **전부 `fileName`** 이다. 채워진 period·crs·grid 는 이번 측정에서 근거로 한 번도 쓰이지 못했다.
- 모델 팔: 호출 38회 전부 `{"suggestions":[]}` — 침묵 **38/38**(과거 S6 29/30). J2 hit@3 **0/10 · 0/10**. 구조 누수 0 · 인용 오류 0 · 후보 밖 0 · 규격 위반 0 · 8초 초과 0/38.
- 규칙 팔: J2 hit@1 0/10 · hit@3 **2/10**. 대조군 ⑴′ `removed_and_siblings` **3/5 → red**(누수 2건 · 갈래 `other` = 참인 `fileName` 인용의 비부모). ⑵ `descendants` 5/5 green 이지만 **5/5 전부 공허**(후보 0건).

## 명령 (비밀값 없음)

```
# ⑴ 후보 절반 — 일회용 DB · 모델 호출 0
COLAB_K3_PROBE_OUT=<워크트리>/dev-package/reports/k3-lineage-probe/2026-09-25-corpus28/j1-2026-09-25-corpus28.json \
COLAB_K3_CANDIDATES_OUT=<워크트리>/dev-package/reports/k3-lineage-probe/2026-09-25-corpus28/candidates-2026-09-25-corpus28.json \
  bash gates/tools/service-tests.sh core-api k3_probe
# → 수집 2 · 실행 2 · failed 0 · errors 0 · 종료코드 0

# ⑵-a 수정 전 러너(선행 결함 확인) — 키 검사보다 앞에서 멈춘다 · 모델 호출 0
services/core-api/.venv/bin/python eval/k3-lineage/llm_lineage_probe.py --arm both --repeats 2 \
  --candidates dev-package/reports/k3-lineage-probe/2026-09-25-corpus28/candidates-2026-09-25-corpus28.json \
  --output dev-package/reports/k3-lineage-probe/2026-09-25-corpus28/luna-2026-09-25-corpus28-pre-fix.json
# → Preparation failure: ValueError unexpected case count: children=5 edges=10 · 종료코드 78 · 출력 파일 없음

# ⑵-b 수정 후 — OPENAI_API_KEY 는 운영자 로컬 환경 파일에서 이 프로세스에만 넣었다(값 미출력)
services/core-api/.venv/bin/python eval/k3-lineage/llm_lineage_probe.py --arm both --repeats 2 \
  --candidates dev-package/reports/k3-lineage-probe/2026-09-25-corpus28/candidates-2026-09-25-corpus28.json \
  --output dev-package/reports/k3-lineage-probe/2026-09-25-corpus28/luna-2026-09-25-corpus28.json
# → 종료코드 0 · model_calls 38
```

- 모델·설정 = 등록 §1 그대로: `--model gpt-5.6-luna`(기본값) · `--timeout 8.0` · `--repeats 2` · `--base-url` 기본 · `--groups` 기본(본군 + 대조군 4종).
- 제품 동일성: `system_prompt_sha256 0f71e746…` · `suggester_sha256 a2437a42…` · `verifier_sha256 b4d30a69…` · `signals_sha256 480de539…` — 2026-09-24 S6(`luna-2026-09-24d-structure.json`)와 네 값 모두 같다.
  `runner_sha256 5735c593…` 는 §7 수정을 담은 러너이고, 이 커밋의 `eval/k3-lineage/llm_lineage_probe.py` 와 같은 hash 다(실행 시점 `local_sha` 는 수정 커밋 전인 `82ecf733`).

### 등록과 다르게 한 것

| 항목 | 등록 | 실제 | 이유 |
|---|---|---|---|
| 출력 경로 | `dev-package/reports/k3-lineage-probe/{j1,candidates,luna}-<측정일>-corpus28.json` | 같은 파일명을 날짜 하위 폴더 `2026-09-25-corpus28/` 에 둠 | 작업 지시(새 날짜 하위 폴더). 파일명·새 파일 원칙은 같다 |
| 모델 절반 해석기 | `services/ai-service/.venv/bin/python` | `services/core-api/.venv/bin/python` | ai-service venv 는 모듈 머리의 `from colab_core.app import relay` 가 `colab_core.app.main` → FastAPI 라우트를 올리며 `python-multipart` 부재로 **종료코드 1**(러너의 78 처리 밖 · 모델 호출 0). core-api venv 는 두 `src` 를 다 읽고, 모델 전송은 표준 라이브러리 `urllib`(`suggest_wire.py:17`)라 해석기 선택이 요청·응답에 닿지 않는다 |

## §4-1 후보 절반 — J1 recall@k (`j1-2026-09-25-corpus28.json`)

| 전략 | recall@5 | @10 | @20 | missed@20 | 자식별 모집단 |
|---|---|---|---|---|---|
| `recent` | 0/10 | 0/10 | 4/10 | 6 | 29 · 29 · 29 · 29 · 29 |
| `filtered`(제품) | 8/10 | **10/10** | **10/10** | 0 | 8 · 8 · 7 · 6 · 6 |

- 등록 §5 ① — J1 원문 「6/6」 = 엣지 전건 → 이번 **10/10**. `filtered` @10·@20 이 충족. @5 는 8/10(선 없음).
- `filtered` 의 모집단이 전부 20 이하라 **@20 = 모집단 전체 포함 여부(동어반복)** 다. `recent` 의 순위는 적재 역순이라 신호가 아니다(`eval/k3-lineage/README.md`).
- 모집단 29 = 코퍼스 28 − 자식 자신 1 + 시험 시드 2(`DSA1`·`DSA2`). 시드는 사람이 고를 수 있는 후보라 세고, 케이스마다 `candidates_outside_corpus` 로 드러난다(자식 001·003·005 에 2건씩).

## §4-2 후보·대조군 기록 (`candidates-2026-09-25-corpus28.json`)

- `sample_limits` = 자식 5 · 엣지 10 · 모집단 28 · 스냅샷 계보 자식 13 · 엣지 18. 전략 `filtered` · k=20 · `local_sha 82ecf733`.
- `autometa_axes_present` = **period 28 · crs 24 · grid 26 · variables 0 · fileName 28** — 스냅샷 v2 `counts.autometa_fill`(등록 §0)과 같다. 지어낸 축 없음.
- `sibling_rules` = `["same_level"]` — 부모 공유 형제(`graph`)가 0건이라 같은 단계로 떨어졌다(과거 S6 와 같음).

### 후보별 비어 있지 않은 축 (본군 · 업로드 쪽 포함)

| 자식 (단계) | 업로드 쪽 축 | 본군 후보 | 후보 쪽 축 |
|---|---|---|---|
| 001 hsr_sample (1) | fileName | 7 (정답 1 · 시드 2) | 코퍼스 5건 = fileName·period·crs·grid · 시드 2건 = crs·variables |
| 002 GK2A_NDVI_mean_202305 (1) | fileName | 7 (정답 1) | 7건 전부 fileName·period·crs·grid |
| 003 pred_sample (2) | fileName | 7 (정답 2 · 시드 2) | 코퍼스 5건 = fileName·period·crs·grid · 시드 2건 = crs·variables |
| 004 Prediction (공간상세화) (2) | fileName | 6 (정답 5) | 6건 전부 fileName·period·crs·grid |
| 005 rn15_sample (1) | fileName | 5 (정답 1 · 시드 2) | 코퍼스 3건 = fileName·period·crs·grid · 시드 2건 = crs·variables |

- `variables` 가 찬 후보는 시험 시드 2건뿐이다(스냅샷 코퍼스는 0 · 등록 §0 과 같음).
- 업로드 쪽 `upload_axes` 는 다섯 자식 모두 `file_name` 외 `crs`·`grid`·`period_*`·`variables` 가 비어 있다 — 「이상」 ①.

### 군별 후보 수 (자식 001~005)

| 군 | 후보 수 | 공허(0건) |
|---|---|---|
| main | 7 · 7 · 7 · 6 · 5 | 0 |
| ⑴ removed | 6 · 6 · 5 · 1 · 4 | 0 |
| ⑵ descendants | 0 · 0 · 0 · 0 · 0 | **5** |
| ⑶ siblings | 12 · 12 · 1 · 0 · 12 | 1 |
| ⑴′ removed_and_siblings | 4 · 1 · 4 · 1 · 3 | 0 |

- 구조 단언(`test_k3_lineage_probe.py:342-368`)은 시험 통과로 성립 — 자식 수·엣지 수 = `sample_limits` · 후보 1~20 · 자식 자신 없음 · 군별 무결성.

## §4-3 대조군 4종 · §4-5 J5' (군별 빈 제안)

| 군 | 규칙 팔 (1회) | 규칙+모델 팔 (2회) | 판정 규칙 |
|---|---|---|---|
| main | 1/5 · 기록 | 10/10 · 기록 | — |
| ⑴ removed | 1/5 · 기록 | 10/10 · 기록 | 기록 |
| ⑵ descendants | 5/5 · green (**공허 5/5**) | 10/10 · green (**공허 10/10**) | 전건 아니면 red |
| ⑶ siblings | 2/5 · 기록 (공허 1) | 10/10 · 기록 (공허 2) | 기록 |
| ⑴′ removed_and_siblings | **3/5 · red** (누수 2) | 10/10 · green (공허 0) | 전건 아니면 red |

- 규칙 팔 ⑴′ 누수 2건 = 갈래 `other`(자기 자신·후손·후보 밖·인용 오류가 아님 · 참인 `fileName` 인용):
  001 hsr_sample → 「HSR 레이더합성 원자료」(`hsr_sample.npy` ↔ `RDR_CMP_HSR_PUB_202508131000.bin.gz`) ·
  002 GK2A_NDVI_mean_202305 → 「GK-2A LST 원자료」(`GK2A_NDVI_mean_202305.tif` ↔ `gk2a_ami_le2_lst_ko_202005010000.nc`). 둘 다 확신도 「애매」.
- ⑵ 는 두 팔 모두 green 이지만 후보가 전부 0건이라 **구조 보장을 실제로 시험하지 못했다**(과거 S6 도 공허 4/4).
- 구조 누수 갈래 합계: 모델 팔 0(self 0 · descendant 0 · outside 0 · citation_error 0 · other 0) · 규칙 팔 other 2.

## §4-4 두 팔 · §4-5 J1~J9

| # | 규칙 팔 (1회 · 모델 0) | 규칙+모델 팔 (2회 · 호출 38) | 선 (등록) |
|---|---|---|---|
| J1 적격 필터 뒤 정답 포함 | 10/10 | 10/10 | 전건 10/10 — 충족 |
| J2 hit@1 · hit@3 | 0/10 · 2/10 | 0/10 · 0/10 · 0/10 · 0/10 | descriptive only(4/6 선은 환산하지 않음) |
| J3' 최종 인용 오류 | 0 | 0 | 1건이라도 red — 0 |
| J3' 폐기율 (분모 = 주장 근거) | 0/25 = 0.0 | 0/0 = 없음 | 기록 |
| J3 근거 hard 토큰 | 0 | 0 | 위반 0 — 0 (규칙 팔 근거 한 줄은 core-api 고정 서식) |
| J4' 「확실」 정확도 | 확실 0건 · 애매 12건 중 정답 4 | 제안 0건 | 기록 |
| J6 후보 밖 ID | 0 | 0 (relay 폐기 0) | 0건 — 0 |
| J7 규격 위반 | 0 | 0 | 0건 — 0 |
| J8 지연 (8초 초과) | 호출 없음 | 38회 · 최소 1.17 · 중앙 1.89 · 최대 3.37초 · 초과 0 · 전송 오류 0 | 초과 건수 기록 — 0/38 |
| J9 결정성 (갈린 칸) | 0/25 | 0/25 | 기록만 |

- 규칙 팔 본군 제안(자식 001~005): 4 · 4 · 3 · 0 · 1건, 근거 25건 전부 `fileName`. hit@3 2건은 003 pred_sample 의 두 부모. 004 는 정답 5건이 후보 6건 안에 다 있는데도 규칙 팔이 「대조 축이 맞는 후보가 없습니다.」로 빈 제안을 냈다.
- 모델 팔 빈 제안 선언: 호출한 38칸 전부 「살펴본 후보 중에 가공 전 데이터로 볼 만한 것이 없었다…」, 부르지 않은 12칸(공허) 「살펴볼 가공 전 데이터 후보가 요청에 없다…」.
- **빈 제안 비율(사후 추가 · 본군+대조군 전체)**: 모델 팔 50/50 · 규칙 팔 12/25. **모델 침묵률**(호출한 왕복 중 원문 빈 배열): 38/38.

## 2026-09-24 실측과 나란히 (등록 §5 ③ — 개선·악화로 읽지 않는다)

| 항목 | 2026-09-24 S6 (`luna-2026-09-24d-structure.json` · 9건 · 엣지 6) | 2026-09-25 (28건 · 엣지 10) |
|---|---|---|
| 자동 메타 축 (후보 쪽) | fileName 9 · 나머지 0 | period 28 · crs 24 · grid 26 · variables 0 · fileName 28 |
| J1 후보 절반 `recent` @5/@10/@20 | 3/6 · 6/6 · 6/6 (`j1-2026-09-24b.json`) | 0/10 · 0/10 · 4/10 |
| J1 후보 절반 `filtered` @5/@10/@20 | 6/6 · 6/6 · 6/6 | 8/10 · 10/10 · 10/10 |
| 모델 호출 | 30 | 38 |
| J2 규칙 hit@1 · hit@3 | 1/6 · 2/6 | 0/10 · 2/10 |
| J2 모델 hit@3 (회차별) | 1/6 · 0/6 | 0/10 · 0/10 |
| 모델 침묵 (호출 중 빈 배열) | 29/30 | 38/38 |
| J5' ⑵ 규칙 · 모델 | 4/4 green (공허 4) · 8/8 green (공허 8) | 5/5 green (공허 5) · 10/10 green (공허 10) |
| J5' ⑴′ 규칙 · 모델 | 4/4 green (공허 1) · 8/8 green (공허 2) | **3/5 red** (공허 0) · 10/10 green (공허 0) |
| J3' 최종 인용 오류 | 0 · 0 | 0 · 0 |
| J3' 폐기율 규칙 · 모델 | 0/8 · 0/1 | 0/25 · 0/0 |
| J8 초과 · 중앙값 | 0/30 · 2.01초 | 0/38 · 1.89초 |
| J9 갈린 칸 (모델) | 1/20 | 0/25 |

## 이상 · 해석 주의

1. **업로드 쪽 축 부재.** 러너·후보 시험의 업로드 축은 `lineage-cases.json` 의 `upload_meta.file`(`fileName`·`kind`·`partCount`)에서 `UploadAxes.from_file_meta` 로 만든다. 제품 경로(`routes/ingestion.py:692`·`:709`)는 업로드 파일에서 읽은 `crs`·`gridDescription`·`periodStart/End`·`variables` 를 싣지만, 이 표본에는 그 값이 없다. 그래서 `signals.verify` 가 period·crs·grid 를 비교할 짝이 없고 규칙 팔 근거가 `fileName` 하나로 좁혀졌다. 이번 측정은 「후보 쪽 축이 채워진 코퍼스」는 쟀지만 「양쪽 축이 채워진 대조」는 재지 못했다. 등록은 정답·표본을 바꾸지 않게 했으므로 고치지 않았다(후속 ①).
2. **⑴′ 누수 2건의 원인은 `fileName` 토큰 공유다.** 새 코퍼스의 「파일 포맷 예제」 계열(HSR 레이더합성 · GK-2A LST)이 자식과 `hsr`·`gk2a` 토큰을 나눠, 인용은 참이지만 부모가 아니다. 두 후보의 기간은 자식 데이터셋의 기간과 겹치지 않는다(후보 JSON 의 축 값: hsr_sample 2019-07-28~2024-07-09 vs HSR 레이더합성 원자료 2025-08-13 · GK2A_NDVI_mean_202305 2023-05-01 vs GK-2A LST 원자료 2020-05-01). 업로드 쪽 period 가 있었다면 가를 수 있었을 축이다(①과 같은 뿌리 · 제품 규칙이 실제로 가르는지는 이번 측정으로 확인하지 않았다).
3. **모델 침묵 38/38.** 후보 쪽 축이 채워졌어도 모델은 한 번도 제안을 내지 않았다. 모델에 가는 업로드 쪽 정보도 ①처럼 파일명·이름 초안·주제·단계뿐이다.
4. **⑵ 전건 공허.** 다섯 자식 모두 후손 군 후보가 0건이다. 구조 보장의 녹색은 이번에도 실제 후보로 시험되지 않았다.
5. 시험 시드 `DSA1`·`DSA2` 가 자식 001·003·005 의 본군 후보에 들어 있다(각 2건). 제품 D3 가 고른 값 그대로다.

## 78 · 준비 실패 기록

| 실행 | 종료코드 | 원인 | 출력 |
|---|---|---|---|
| 후보 절반 `service-tests.sh core-api k3_probe` | 0 | — | j1·candidates 2건 |
| 모델 절반 · ai-service venv (설정 확인 중) | 1 | `python-multipart` 부재 — 모듈 import 단계에서 실패(러너 `main()` 진입 전 · 모델 호출 0) | 없음 |
| 모델 절반 · 수정 전 러너 | **78** | `unexpected case count: children=5 edges=10` (등록 §7 선행 결함) | 없음 (`...-pre-fix.json` 미생성) |
| 모델 절반 · 수정 후 러너 | 0 | — | `luna-2026-09-25-corpus28.json` |

- 78 뒤 자동 재시도하지 않았다. 원인(§7)을 고친 뒤 새 출력 경로로 한 번 돌렸다.

## 후속

- ① K3 표본의 업로드 쪽 자동 메타: `lineage-cases.json` `upload_meta.file` 에 자식 데이터셋의 실제 축(스냅샷 v2 autometa)을 싣는 것은 정답 파일 변경이라 이 측정 범위 밖이다. 어느 검사에도 걸리지 않는다.
- ② `eval/k3-lineage/README.md` 의 모델 절반 명령이 `services/ai-service/.venv/bin/python` 이지만 그 venv 로는 `python-multipart` 부재로 import 가 실패한다. 어느 게이트도 이 명령을 돌리지 않는다. 같은 README 의 「20회」도 낡은 값이다(등록 후속과 같음).
- ③ 러너 판정 함수 시험 `eval/k3-lineage/test_llm_lineage_probe.py`(51건 통과)는 어느 게이트에도 묶여 있지 않다.

## 파일

| 파일 | 무엇 |
|---|---|
| `j1-2026-09-25-corpus28.json` | 후보 절반 J1(전략 2 × k 5·10·20) |
| `candidates-2026-09-25-corpus28.json` | core-api 가 고른 본군·대조군 후보 · 축 · `sample_limits` (sha256 `55d687d9…`) |
| `luna-2026-09-25-corpus28.json` | 두 팔 원문 · 호출 38건 원문 · 판정 표 |
