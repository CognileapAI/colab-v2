# D3 — 경계 강제 게이트 3종 (`import-boundary` · `banned-import` · `ai-no-lineage-write`)

D3의 완료 판정은 "게이트 self-test 전부 fail-closed 증명"(`WORK-UNITS.md §6`)이다.
이 세션은 **경계 게이트 3종과 그 증명**을 만들었다. RLS 커버리지·스키마 diff·alembic single-head는
D3의 나머지 절반이며 아직 red(미구현)다.

`contracts/`·`services/`·`db/`에는 **한 글자도 쓰지 않았다.** 게이트가 검사할 대상을 게이트 세션이
만들어 두면, 그 게이트는 자기가 만든 것을 검사하는 셈이 된다.

---

## 1. 무엇이 어디에 있는가

| 파일 | 역할 |
|---|---|
| `gates/config/boundaries.toml` | 배포 단위 ↔ 파이썬 패키지 대응 · **금지 import 목록의 유일한 정의처** · 음성 게이트의 금지 어휘 |
| `gates/config/importlinter.ini` | import-linter 계약 7개 (D1~D10 경계) |
| `gates/requirements.txt` | 도구 버전 핀 (`import-linter==2.13` · `PyYAML==6.0.2` + 전이 의존 7개) |
| `gates/tools/_venv.sh` | `gates/.venv` 확보. 설치 실패는 skip이 아니라 red |
| `gates/tools/import-boundary.sh` | import-linter 실행기 |
| `gates/tools/banned-import.py` | 배포 단위별 allow/deny (표준 라이브러리 `ast`만) |
| `gates/tools/ai-no-lineage-write.sh` · `ai_no_lineage_write.py` | 음성 게이트 |
| `gates/tools/boundary-selftest.sh` | 세 게이트의 fail-closed 증명 (30케이스) |

`gates/run.sh`에 `import-boundary` · `banned-import` · `ai-no-lineage-write` · `boundary-selftest`를 배선했다.
기존 관례(미구현은 red, 인자 없음은 usage + exit 2, 모르는 이름은 exit 2)는 그대로다.

**selftest는 `contract-selftest`와 합치지 않고 `boundary-selftest`로 분리했다.** 계약 게이트는 spectral·docker에,
경계 게이트는 파이썬 venv에 의존한다. 합치면 도커가 없는 환경에서 경계 증명까지 같이 죽는다 —
증명은 서로의 인프라 사고에 걸려 넘어지면 안 된다.

---

## 2. 모듈 경로 관례 (이 세션의 실제 산출 — **P0가 이 관례를 따른다**)

코드가 아직 없으므로 관례를 여기서 정하고, 게이트가 그 관례를 강제한다.

```
services/<배포 단위>/src/<패키지>/
    __init__.py
    app.py            조립 루트. 여러 도메인을 아는 유일한 자리
    domains/<Dn>_<이름>[.py|/]   도메인 하나 = 모듈 하나 또는 패키지 하나
    ports/            cross-domain 인터페이스. 여기에는 도메인 구현이 없다
    kernel/           스코프 커널 · 세션 · 설정. 가장 아래층
```

| 배포 단위 | 패키지 | 도메인 모듈 |
|---|---|---|
| `core-api` | `colab_core` | `d1_identity` `d2_access` `d3_catalog` `d4_lineage` `d6_project` `d8_insight` |
| `pipeline-worker` | `colab_pipeline` | `d5_ingestion` |
| `viz-render` | `colab_viz` | `d7_visualization` |
| `ai-service` | `colab_ai` | `d9_ontology` `d10_ai_services` |

정한 이유 셋.

1. **도메인 번호를 모듈 이름에 박는다.** `DOMAINS.md`의 D번호가 파일 경로에 그대로 보이면 계약 파일과 문서가
   같은 어휘를 쓰게 되고, 경계 위반이 diff에서 눈으로도 보인다.
2. **`src/` 레이아웃.** 배포 단위 루트가 곧 패키지가 되면 테스트가 설치되지 않은 소스를 우연히 import 한다.
   게이트는 `PYTHONPATH`에 `services/*/src`만 얹는다 — 그래서 배포 단위 사이의 import는 문법적으로도 사고가 아니다.
3. **`ports/`를 도메인 밖에 둔다.** Port가 도메인 안에 있으면 "누구의 Port인가"가 흐려지고,
   `ports → domains` 역참조를 층 계약으로 잡을 수 없다.

**DB 쪽 관례 하나** — D10의 제안 임시 저장소 테이블은 `ai_` 접두사를 쓴다(`ai_lineage_suggestion` 등).
D4 테이블은 `lineage_`·`d4_` 접두사다. 음성 게이트가 이 접두사로 두 소유를 구분한다.

---

## 3. `import-boundary` — 무엇을 어떻게 판정하나

`import-linter` 2.13이 실제 import 그래프를 만들어 계약 7개를 검사한다. grep이 아니다 —
`from x import y`의 y가 모듈인지 심볼인지, 재수출로 우회했는지를 grep은 구분하지 못한다.

| # | 계약 | 유형 | 막는 것 |
|---|---|---|---|
| 1 | `units-independent` | independence | 배포 단위 4개가 파이썬으로 서로 붙는 것. 단위 간 통신은 seam(HTTP)과 async 봉투뿐이다 |
| 2 | `core-layers` | layers | `app > domains > ports > kernel`. Port가 도메인을 참조하는 층 역전 |
| 3 | `core-domains-independent` | independence | D2·D3·D4·D6·D8 상호 직접 참조 (**D1은 shared kernel이라 목록에서 뺀다**) |
| 4 | `d1-knows-nobody` | forbidden | D1이 위층을 참조 — "모두가 읽는 커널"이 "모두와 얽힌 커널"이 되는 것 |
| 5 | `ai-layers` | layers | `app > d10 > ports > d9` |
| 6 | `pipeline-layers` · `viz-layers` | layers | D5·D7도 같은 관례 |
| 7 | `d10-reads-d9-via-port` | forbidden | **D10 → D9 직접 import.** layers 계약은 아래층 호출을 허용하므로 5번만으로는 못 막는다 |

7번은 selftest가 잡아낸 것이다. 처음엔 `ai-layers`만 두었고 D10→D9 직접 참조 fixture가 **green으로 통과했다.**
증명을 먼저 쓰지 않았으면 이 구멍은 P0까지 살아남았다.

**대상 0건 = red.** 패키지가 하나라도 없으면 실행 전에 red를 내고, 없는 경로를 그대로 찍어준다.
`contract-lint`가 seam 0건을 red로 본 것과 같은 판단이다 — 빈 검사 대상을 green으로 세면 그게 green-by-skip이다.

---

## 4. `banned-import` — 배포 단위별 allow/deny

`ast`로 파싱해 `import X` · `from X import` · `importlib.import_module("X")` · `__import__("X")`를 본다.
동적 import까지 보는 이유는, 정적 import만 막으면 우회가 한 줄이기 때문이다.

- **core-api deny 18개** — `rasterio` `osgeo` `gdal` `xarray` `pyproj` `shapely` `fiona` `geopandas`
  `rioxarray` `netCDF4` `h5py` `cfgrib` `eccodes` `pygrib` `cartopy` `rio_cogeo` `matplotlib` `affine`
- **ai-service deny 7개** — 래스터를 여는 일은 ai-service 것이 아니다
- **pipeline-worker · viz-render deny 0개** — geo 라이브러리가 이 둘의 **일**이다. 정본이 "여기에만 들어간다"고 못 박았다

목록은 `gates/config/boundaries.toml`에만 있다. 스크립트는 목록을 갖지 않는다 — 두 곳에 적으면 갈라진다.
`from . import x`(상대 import)는 패키지 내부라 검사 대상이 아니다.
파싱 실패도 red다. **읽지 못한 파일을 통과로 세지 않는다.**

`.py` 총합이 0이면 red. "금지 import가 없다"와 "코드가 없다"는 다른 사실이다.

---

## 5. `ai-no-lineage-write` — 음성 게이트

증명할 명제: **"D10 → D4 쓰기 경로가 존재하지 않는다"**(`CLAUDE.md §3-2`)와
**"db/ai와 db/platform의 체인이 섞이지 않는다"**(`§3-3`).

음성 명제는 "무엇이 있으면 red인가"를 구체적으로 적어야만 검사가 된다. 12개를 적었다.

### L1 계약층 — `contracts/seams/core-ai.yaml`

| 코드 | red 조건 |
|---|---|
| ① | 계보 명사(`lineage` `provenance` `derivation` `ancestry`)를 담은 경로에 `PUT`/`PATCH`/`DELETE`가 있다 |
| ② | `operationId`가 (확정 동사 × 계보 명사) 조합인데 허용 목록에 없다. 허용은 **`suggestLineage` 하나뿐** |
| ③ | `components.schemas` 이름이 같은 조합이다 (`LineageCommitRequest` 등 — 요청 본문으로 새는 경로) |
| ④ | core-ai seam 파일이 0건이다 |

확정 동사 14개: `commit` `confirm` `approve` `create` `persist` `save` `write` `record` `register`
`finalize` `update` `delete` `upsert` `materialize`.
현재 동결판(`suggestLineage` · `searchDatasets`)은 이 검사를 통과한다 — **L1은 지금 이미 green이다.**

### L2 코드층 — `services/ai-service`

| 코드 | red 조건 |
|---|---|
| ⑤ | 금지 패키지 import (`colab_core` · `alembic` · `db.platform`) |
| ⑥ | D4 테이블 접두사(`lineage_` `d4_`)가 코드에 등장 — **읽기여도 red다.** D4는 core-api의 것이고 ai-service는 seam으로만 말한다 |
| ⑦ | 쓰기 SQL 키워드가 같은 줄에서 D4 테이블을 가리킨다 |
| ⑧ | ai-service 코드가 0건이다 |

접두사 매칭은 앞에 단어 문자가 붙으면 제외한다 — `ai_lineage_suggestion`은 D10 소유라 red가 아니다(§2).

### L3 체인층 — `db/ai` ↔ `db/platform`

| 코드 | red 조건 |
|---|---|
| ⑨ | `db/ai` 아래 파일이 `db/platform`을 참조하거나 D4 테이블을 만든다 |
| ⑩ | `db/platform` 아래 파일이 `db/ai`를 참조한다 |
| ⑪ | 두 체인의 `alembic.ini`가 없거나, `version_table`이 미선언이거나, **둘이 같다** |
| ⑫ | 두 체인 중 하나라도 마이그레이션이 0건이다 |

⑪이 핵심이다. `version_table`을 선언하지 않으면 둘 다 기본값 `alembic_version`을 쓰고,
그 순간 "체인 분리"는 디렉터리 이름뿐인 관례가 된다. 관례는 v2에서 두지 않는다.

### 대상 0건을 green으로 세지 않은 근거

음성 명제는 대상이 없으면 공허하게 참이다. **"AI가 계보에 쓰지 않는다"와 "AI가 아직 없다"는 다른 사실**이고,
게이트가 둘을 구분하지 못하면 그게 green-by-skip이다 — v1 CI가 DB 없이 RLS 테스트를 통과시킨 것과 같은 실패다.
그래서 ⑧·⑫를 넣었다. 지금 이 게이트는 ⑧·⑪·⑫로 red이며, **red인 것이 정상이다.**

---

## 6. selftest가 증명하는 것 — 30케이스

`./gates/run.sh boundary-selftest` (전부 green = 세 게이트가 fail-closed).
실제 `services/`·`db/`·`contracts/`는 건드리지 않는다. 전부 `mktemp -d` 아래에 만들고 환경변수
(`COLAB_SERVICES_DIR` · `COLAB_DB_DIR` · `COLAB_SEAM_DIR` · `COLAB_BOUNDARY_CONFIG` ·
`COLAB_GATE_VENV` · `COLAB_GATE_REQUIREMENTS`)로 주입한다 — `contract-selftest`와 같은 형태다.

| 게이트 | 케이스 | 기대 |
|---|---|---|
| import-boundary | 관례대로 놓인 빈 패키지 | green |
| | D3 → D4 직접 참조 / ai-service → core-api / Port가 도메인 참조 / D1이 위층 참조 / D10 → D9 직접 | red ×5 |
| | 대상 패키지 0건 / 도구 설치 실패 | red ×2 |
| banned-import | geo 없는 core-api / **viz-render·pipeline-worker의 geo import** | green ×2 |
| | core-api의 `import rasterio` / `from osgeo import gdal` / 동적 `import_module("xarray")` | red ×3 |
| | `.py` 0건 / 파싱 불가 파일 | red ×2 |
| ai-no-lineage-write | 제안만 있는 기준 fixture (세 층 전부 갖춘 상태) | green |
| | ①~⑫ 각 조건 | red ×14 |

**green 케이스가 있어야 증명이 성립한다.** 전부 red를 내는 게이트는 fail-closed가 아니라 그냥 고장이다.
`viz-render·pipeline-worker의 geo import → green`이 특히 그렇다 — 이게 red면 금지가 전역 금지가 되고,
그건 정본이 정한 배포 단위 분할과 다른 규칙이다.

---

## 7. 지금의 실행 결과와 그 근거

| 게이트 | 지금 | 이유 |
|---|---|---|
| `import-boundary` | 🔴 red | `services/*/src/<패키지>` 가 없다. P0가 만든다 |
| `banned-import` | 🔴 red | `.py` 0건 |
| `ai-no-lineage-write` | 🔴 red | L1 계약층은 통과. L2(코드 0건)·L3(마이그레이션 0건·`alembic.ini` 없음)에서 red |
| `boundary-selftest` | 🟢 green | 30케이스 전부 의도대로 |
| `planning-freshness` · `contract-lint` | 🟢 green | 기존 게이트를 깨지 않았음을 확인 |

**red 3개는 버그가 아니라 설계다.** `CLAUDE.md §4`: 미구현 게이트는 red를 낸다.
P0가 위 관례대로 코드와 마이그레이션을 놓는 순간 셋 다 green으로 돌아설 수 있다 —
그 전환이 이 게이트들의 인수 시험이다.

---

## 8. 남은 한계 (다음이 알아야 할 것)

1. **`import-boundary`는 파이썬만 본다.** `frontend`는 배포 단위 5개 중 하나지만 TS다.
   FE의 경계는 `generated-up-to-date`(생성된 타입만 소비)가 다른 축에서 맡는다. 여기서 겹쳐 잡지 않았다.
2. **layers 계약은 모듈이 없으면 오류다.** P0가 `app`·`ports`·`kernel` 중 일부만 만들면 그 계약이 red를 낸다.
   빈 `__init__.py`라도 자리를 먼저 만들어야 한다 — selftest fixture가 그 최소 형태다.
3. **테이블 접근은 아직 이름 규칙으로만 본다.** "타 도메인 테이블 직접 FK 금지"의 진짜 강제는
   D3 나머지 절반(`schema-diff` · `rls-coverage`)에서 선언 스키마를 대상으로 해야 한다.
4. **음성 게이트의 L2는 정적 문자열까지 본다.** ORM이 테이블명을 런타임에 조립하면 놓친다.
   ai-service에 그런 코드가 들어오면 그건 게이트를 우회하려는 코드이므로, 리뷰에서 막는다.
5. **`gates/.venv`는 게이트가 스스로 만든다**(`requirements.txt` 해시가 바뀌면 재생성). 첫 실행은 네트워크가 필요하고,
   오프라인 첫 실행은 red다 — 이건 skip을 만들지 않기 위한 의도된 비용이다.
