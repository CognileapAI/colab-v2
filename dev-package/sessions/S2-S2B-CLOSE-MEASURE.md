# `S2`·`S2b` 종결 회차 — 실측 근거 산출 (2026-08-29)

판정과 값의 정본 = `dev-package/PLAN-SoT.md §9 〈208〉`. 이 파일은 그 회차의 **원시 측정 기록**이고, 값을 새로 세우지 않는다.

## 1. 측정 시점·경계

- 시점 = **2026-08-29 21:01 KST** (측정 명령 직전 `date -Iseconds` 출력)
- staging 접촉 = **읽기 전용 `COUNT` 만.** 컨테이너 정지·재기동·재생성 0회 · `DELETE`/`UPDATE`/DDL 0건 · 접속 문자열·비밀번호 미출력
- 경로 = `docker exec colab_v2_staging_pg psql -U postgres -d colab_platform -At -c "SELECT …"`
- 선행 회차가 남긴 일회용 컨테이너 둘(`a2_pg`·`ai_pg`)은 **건드리지 않았다**

## 2. 산출물 실재 확인 — 레포 파일

| 대상 | 경로 | 실측 |
|---|---|---|
| 검색 평가셋 | `eval/s2b-alayer/evalset.json` | `items` **16** ＋ `out_of_layer` **2** = **18건** |
| 실행기 | `eval/s2b-alayer/run.py` | 실재 (21 KB) |
| 기준선 | `eval/s2b-alayer/baseline.json` | `시점` = `2026-08-29T17:37:03+09:00` · `results` 16건 · `미실행` = `Q-19`·`Q-20`·B층 16건 |
| 계보 제안 평가 하네스 | `eval/k4-search/` | 실재(`measure.py`·`seed-15.sql`) — 이번 판정 대상 아님 |

⚠ `eval/README.md` 축자 — `s2b-alayer/` 는 **합격선을 걸지 않는다 · 값만 기록한다.** 그래서 `gates/` 가 아니라 `eval/` 에 있다.

## 3. 산출물 실재 확인 — staging 실물

| 값 | 실측 | 기준 |
|---|---|---|
| 데이터셋 | **12** | `d3_dataset` 전체 행 (`deleted_at IS NULL` 도 12) |
| 파일 | **129** | `d3_file` 전체 행 (본체 123 ＋ 기준 격자 6 — 계수 기준은 `〈184〉`·`sessions/S2-COUNT.md`) |
| 계보 간선 | **6** | `d4_lineage_edge` 전체 행 |
| 설명 | **12행 · 빈 요약 0** | `d3_dataset_description` (`btrim(summary) <> ''` 12/12) |
| `topic IS NULL` | **0** | `d3_dataset_description` |

세 값(12·129·6)은 `〈184〉`(2026-08-28) 와 **동일**하다 — 그 사이 증감 0.

## 4. 이번에 재지 않은 것

- **A층 통과 8 / 실패 8** — 이 회차에 `run.py` 를 돌리지 않았다. 푸는 법 = `python3 eval/s2b-alayer/run.py` 1회. **그것이 `K4` 완료 조건 ⑴ 이다.**
- **로그인 뒤 카탈로그 화면의 브라우저 확인** — 확인하려면 비밀번호를 작업 기록에 남겨야 한다(`03-HANDOFF §4` `#30`·`#34`). 하지 않았다. `[미확인]` 으로 남긴다.
- **검색 품질 합격선의 수치** — 이번 판정 대상이 아니다. `K4` 가 정한다.

## 5. 게이트 (이 회차 실행)

| 게이트 | 전 | 후 |
|---|---|---|
| `work-item-consistency` | 불일치 **3**(`S2b`·`R-1`·`S2`) | 불일치 **1**(`R-1`) · ㈐ 대조 67→**69** 행 · ㈏ 대조 47→**49** 건 |
| `work-item-selftest` | — | **green — 10 케이스**(대조군 1 · red 증명 9) |
| `planning-freshness` | — | **green — 임베드 15블록 전건 일치** |

게이트를 끄거나 검사 대상을 줄이지 않았다. `work-item-consistency` 는 여전히 red 이고 사유는 `R-1` 하나다.
