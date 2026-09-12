# 이슈 조사 D묶음 — 범위 판정 (#30 · #12 · #11 · #10)

- 조사 기준 커밋 `10a3fb8`
- 작성자 researcher
- 승인 미승인
- 입력 = `dev-package/reports/issues/2026-09-12-github-open-issues.md` 의 `## #30`·`## #12`·`## #11`·`## #10`
- 원문 대조 = 이슈 회수본 · 대장 `dev-package/work-items.yaml` · `dev-package/PLAN-SoT.md` · 코드 앵커
- 표기 = 행 번호 미기재(앵커 문자열) · 경로는 레포 루트 기준 상대경로

---

## #30 [개선] 가공 전 데이터 직접 찾기?

### 1. 이슈 요지

- 등록 ③ 계보 확정 화면의 모달 「가공 전 데이터 직접 찾기」로 부모 데이터를 고르는 방식의 개선 요구.
- 이슈 본문 축자 —
  > 데이터 셋 검색을 해야지, 이런형태의 찾기는 찾기가 어려움
- 요지(자기 말) = 필터 6칸(이름·파일명 / 분류 / 주제 / 가공 단계 / 기간 시작 / 기간 끝)만 있는 폼 대신, 데이터셋 검색 화면과 같은 찾기 방식을 요구.
- 첨부 스크린샷 1건 열람 완료 — 모달 결과 목록 0행, 빈 상태 문구 「고를 수 있는 연구실 데이터가 아직 없어요.」 표시.
- 라벨 `improvemet` = 레포 GitHub 라벨에 실재. `gh label list -R CognileapAI/colab-v2` 출력 축자 `improvemet	개선하면 좋을듯	#bdc608`. 오타 그대로 등록됐고 `enhancement` 와 별개.

### 2. 현재 범위 위치

- 부모 찾기 모달 자체는 완료 항목의 산출물이다.
  - `dev-package/work-items.yaml` `id: WU-B5`(`status: done` · `stage: stage2`) completion_def 축자 일부
    > 찾기 모달이 초과 후보를 보이되 못 고르게 하며
  - 같은 파일 `id: WU-B10`(`status: done` · `stage: stage2`) note 축자 일부
    > ParentPicker 공통화(등록 ③·상세 재사용)
- 「찾기 방식을 검색 화면과 같게」에 해당하는 대장 항목 부재 — `부모 후보`·`찾기 모달`·`ParentPicker`·`직접 찾기` 검색 결과는 위 두 done 항목 서술뿐.
- 「가공」 용어의 자리 = `dev-package/PLAN-SoT.md` `〈189〉`-㉰.
  - 요지 = 「가공」은 새 데이터셋을 만드는 쪽 하나만 가리키고, 그 기능은 신설 항목 「데이터 프로세스」이며 시점은 stage 2 다음.
  - 대장 `id: DP-1`(`status: open` · `stage: after_stage2`) entry_conditions 축자
    > **stage 2 다음**(Ted 판정 `〈189〉`-㉰) — 지금 만들지 않는다
  - [추론] 모달 제목의 「가공 전 데이터」는 계보 부모를 가리키는 화면 문구이고 `DP-1` 기능과 대상이 다르다. #30 은 `DP-1` 요구가 아니다.
- 검색 쪽 자리 = 자연어 검색 `K4` 는 `stage: after_stage2`, 조건 검색 화면(카탈로그)은 stage 1 산출물.

### 3. 코드 현황

- 모달 본체 = `frontend/src/components/lineage/ParentPicker.tsx`
  - 제목 문자열 `가공 전 데이터 직접 찾기`
  - 필터 = `이름·파일명`(`type="search"`) · `분류` · `주제` · `가공 단계`(`data-testid="lin-lv-filter"`) · `기간 시작` · `기간 끝`
  - 빈 상태 두 갈래 = 조건 있음 `검색 조건에 맞는 데이터가 없어요. 조건을 바꿔 주세요.` / 조건 없음 `고를 수 있는 연구실 데이터가 아직 없어요.`
  - 결과 표시 = `<ul>` 안 버튼 한 행에 이름 ＋ `Lv{n}`. 열(분류·주제·기간·파일 수) 없음. 정렬 선택 없음.
  - 초과 Lv 행은 `is-over` 클래스로 남되 `disabled`.
- 조회 훅 = `frontend/src/components/lineage/useParentCandidates.ts` — `loadCandidates`·`loadMore`(`nextCursor` 이어 받기) 존재.
- 서버 = `services/core-api/src/colab_core/app/routes/catalog.py` `@router.get("/lineage-candidates", name="listLineageCandidates")` → `services/core-api/src/colab_core/domains/d3_catalog.py` `list_lineage_candidate_cores`(인자 `topic`·`period_start`·`period_end`·`exclude_id`·`cursor_at`).
  - 연구실 경계 = RLS. 함수 주석 축자
    > 연구실 경계는 RLS 가 이미 걸었다 — 여기에 lab_id 조건을 다시 적지 않는다.
- 비교 대상 화면 = `frontend/src/components/catalog/`(`CatalogTable.tsx`·`AxisFilterBar.tsx`·`AppliedConditions.tsx`·`ColumnMenu.tsx`) · `frontend/src/routes/DatasetsPage.tsx` · 자연어 검색 입력 `frontend/src/components/search/SearchHero.tsx`.
- 상세 화면 부모 표시·해제 = `frontend/src/components/lineage/LineageSection.tsx`(문구 `이 데이터와의 연결만 제거해요. 원본 데이터는 남아요.`). 「원본 데이터로 이동」 문자열 미발견 — 부모 노드 클릭 이동 여부 `[미확인]`.
- 스크린샷의 결과 0행 원인 `[미확인]` — dev 실물에서 후보 유무·RLS 범위·`exclude_id` 동작을 재현하지 않았다.

### 4. 범위 판정 후보

- ㈎ **v2 버그** — 조건 = 해당 연구실에 후보 데이터가 실재하는데 목록이 0행이면 조회 결함. 현재 `[미확인]`.
- ㈏ **편의 기능(후일 묶음)** — 「검색 화면과 같은 표·열·정렬로 고르기」는 사용성 개선이고, 등록·연결 동작 자체는 현재 폼으로 성립.
- 배제 — 대화형 UI 도입은 `CLAUDE.md §5` 금지. 자연어 검색을 모달에 붙이는 안은 `K4`(`after_stage2`) 범위 확대라 정본 개정 없이 배제.

### 5. 이번 bugfix 회차 포함 여부 제안

- **부분 포함** — ㈎ 재현 확인 1건만 포함(dev 실물에서 후보 0행 재현 여부 측정). 재현되면 별도 `BF-` 항목 등재.
- UI 형태 변경(㈏)은 **제외** — 대장 신설 후보로 제출.

### 6. 크기

- ㈎ 재현 확인 = 소(조사 1회 · 코드 변경 0). 결함 확인 시 크기 재산정.

---

## #12 백로그: Google 로그인

### 1. 이슈 요지

- 구글 계정 로그인 경로 신설 요구.
- 이슈 본문 축자
  > 2026-09-11 사용자 결정으로 Stage 1·2·3 어디에도 배정하지 않는 백로그로 이관한다.

### 2. 현재 범위 위치

- 대장 `dev-package/work-items.yaml` `id: PA-G`(`name: 구글 IdP 어댑터` · `status: open` · `stage: backlog` · `depends_on: [PA]`).
  - entry_conditions 축자
    > 2026-09-11 사용자 결정: Stage1·2·3 미배정 백로그. 단계·착수 범위·시점을 정하기 전 자동 착수하지 않는다.
    > 2026-09-10 사용자 결정으로 이번 개발 제외. 이슈 #12의 재착수 범위·일정 별도 승인 후 설계한다.
- `dev-package/PLAN-SoT.md` 「2026-09-11 Stage 보류 해소 승인」 절 축자
  > BF-10·PA-G는 Stage1/2/3에 배정하지 않는 backlog/open으로 옮기고 기존 이슈10/12를 유지한다.
- 근거 결정문 = `dev-package/sessions/20260910-stage12-decisions.md` Q6 축자
  > Google 로그인 이번 개발 제외, PA-G deferred 및 종전 자동 개시 기한 해제.
- intent 대조 = `dev-package/intent/2026-09-12-login-backoffice-closeout.md` 의 범위 밖 열거에 `Google 로그인` 명시.
- `PLAN-SoT §9` 번호 결정행(`〈N〉`) 중 Google 로그인 전용 행 미발견 — 근거는 위 셋.

### 3. 코드 현황

- 현행 로그인 = `frontend/src/auth/LoginPage.tsx` · `services/core-api/src/colab_core/app/routes/session.py` · `services/core-api/src/colab_core/kernel/authn.py`.
- OAuth·Google 구현 부재 — 코드 검색에서 해당 문자열 미발견(문서·대장 언급만 존재).

### 4. 범위 판정 후보

- **범위 밖(백로그)** — `PA-G`(`stage: backlog`)로 이미 등재, 사용자 결정으로 stage 미배정.

### 5. 이번 bugfix 회차 포함 여부 제안

- **제외** — 신설 불요. 기존 `PA-G` 유지.

### 6. 크기

- 해당 없음(포함 후보 아님).

---

## #11 후속: 다중 서버용 공유 로그인 제한과 신뢰 프록시 처리

### 1. 이슈 요지

- 로그인 실패 제한 계수를 여러 서버·워커가 공유하도록 하고, 프록시가 전달한 클라이언트 IP 를 신뢰 판정 후 사용하도록 하는 후속 요구.
- 이슈 본문 축자
  > 현재 클라이언트 키는 X-Forwarded-For 마지막 홉에 의존한다.
  > prod/다중 서버 도입 전 검토·검증 관문으로 둔다.

### 2. 현재 범위 위치

- 대장 `dev-package/work-items.yaml` `id: CR-2`(`status: done` · `stage: stage2`) completion_def 축자
  > dev 로그인 제한은 현행 프로세스 메모리·자격/클라이언트 각각 5회/15분·성공 시 초기화 수용.
  > 공유 limiter는 https://github.com/CognileapAI/colab-v2/issues/11 로 유예하며 다중 서버·prod 전 해결한다.
- 유예는 done 항목의 완료 정의 문장에만 있고, **후속을 담을 열린 대장 항목이 없다** — `공유 로그인`·`다중 서버`·`프록시` 로 별도 `id` 미발견.
- intent 대조 = `dev-package/intent/stage3-login-hardening.md` 축자
  > 실패 제한의 기존 승인(자격/클라이언트 각각5회/15분·성공 시 초기화·프로세스 메모리)은 유지하며 수치를 재질문하지 않는다.
  - 공유 저장소·신뢰 프록시 항목은 이 intent 에 없다.
- `dev-package/PLAN-SoT.md` 에서 `X-Forwarded-For`·`신뢰 프록시`·`trusted-proxy` 일치 0 — 근거는 대장 `CR-2` 와 세션 결정문.
- prod 배포는 `PLAN-SoT §9-㊻` 로 보류이므로 이 이슈의 관문 시점은 미도래.

### 3. 코드 현황

- 제한기 = `services/core-api/src/colab_core/kernel/throttle.py`
  - 생성자 인자 `max_failures`·`window_seconds`, 메서드 `record_failure`·`clear`·`_prune`·`_drop_expired`.
  - 저장소 = 프로세스 메모리(`deque`).
  - 파일 머리 주석 축자
    > **IP 를 유일한 열쇠로 쓰지 않는다.** 프록시 뒤라 `X-Forwarded-For` 를 믿어야 하는데,
  - `blocked` 주석 축자
    > **쓰지 않는다** (`CODE-REVIEW-20260903` #5).
- 클라이언트 키 산출 = `services/core-api/src/colab_core/app/routes/session.py` 의 `client = client_key(request.headers.get("x-forwarded-for"))`, 구현은 `services/core-api/src/colab_core/kernel/authn.py` `client_key`.
- 공유 저장소(Redis 등) 연결 코드 부재.

### 4. 범위 판정 후보

- **stage 3 계열 대장 항목 신설** — 사용자 결정이 「prod/다중 서버 도입 전 관문」으로 못박았고, 단일 인스턴스 dev 에서는 판정 대상이 아니다.
- v2 버그 아님 — 현행 동작(프로세스 메모리 5회/900초)은 승인된 수용 상태.

### 5. 이번 bugfix 회차 포함 여부 제안

- **제외 ＋ 대장 항목 신설 제안** — 구현은 제외하고, 유예가 done 항목 문장에만 있는 상태를 항목으로 세운다.

### 6. 크기

- 해당 없음(구현 포함 후보 아님). 등재만 하면 소.

---

## #10 백로그: 화면과 저장 PNG의 경위도 격자선·눈금

### 1. 이슈 요지

- 미리보기 화면과 저장 PNG 양쪽에 경위도 격자선·눈금을 기본 off 토글로 표시하고, 두 결과의 격자 위치·라벨을 일치시키는 요구.
- 이슈 본문 축자
  > frontend의 SVG 배경은 저장 PNG에 포함되지 않는다. ScreenshotRequest와 렌더러 변경이 필요하며

### 2. 현재 범위 위치

- 대장 `dev-package/work-items.yaml` `id: BF-10`
  - `name: "바탕지도 대안 — 격자선·눈금 옵션 (POL-021 준수 · Ted 6 · 접수 B-2)"`
  - `status: open` · `stage: backlog` · `owner: "frontend (D7 화면) — 착수 시점은 Ted"`
  - entry_conditions 축자
    > 2026-09-11 사용자 결정: Stage1·2·3 미배정 백로그. 단계·착수 범위·시점을 정하기 전 자동 착수하지 않는다.
- `dev-package/PLAN-SoT.md` 「2026-09-11 Stage 보류 해소 승인」 절이 `BF-10` 을 backlog 로 옮긴 근거.
- 대안 수용 = `dev-package/sessions/20260910-stage12-decisions.md` Q1 축자 일부
  > 기존 해안선·국경 배경과 커서 좌표 수용. BF-10 격자선 자체는 미구현 deferred
- 배경 허용 범위 = `PLAN-SoT §9 〈375〉` 제목 축자
  > POL-021 부분 반전 — 「타일 서버도 바탕 지도도 쓰지 않는다」 중 자립형 벡터 배경만 허용 (WU-C5)

### 3. 코드 현황

- 격자선 구현 부재 — `frontend/src`·`services/viz-render/src`·`contracts` 에서 `graticule`·`gridline`·`격자선` 검색 결과는 `frontend/src/components/detail/detail.css` 의 표 셀 테두리 주석 1건뿐(지도 격자와 무관).
- 화면 배경 = `frontend/src/components/preview/BasemapLayer.tsx`
  - 주석 축자 일부
    > **자립형 벡터 배경 지도** (WU-C5 · 축 ①-⑤b · Ted 2026-09-08 판정)
    > ⛔ **도시 표기 0** — 자산이 해안선·국경 두 장뿐이라 표기할 점이 아예 없다.
  - 자산 = `frontend/src/assets/basemap/ne_110m_coastline.json` · `ne_110m_admin_0_boundary_lines_land.json`(정적 import).
  - 좌표 변환 정본 = `frontend/src/components/preview/projection.ts`(`lonFractionOf`·`latFractionOf`, 커서 역산 `pvLonOf`/`pvLatOf`).
- 저장 PNG = `services/viz-render/src/colab_viz/domains/d7_visualization/screenshot.py`(`compose`·`_over`·`_sample_rgba`) — 입력은 렌더 층 배열이고 프런트 SVG 미포함.
- 계약 = `contracts/seams/core-viz.yaml` `ScreenshotRequest`(`required: [layers, viewport]` · `additionalProperties: false` · `layers` `maxItems: 8`).
  - [추론] 격자선 옵션을 PNG 에 반영하려면 `additionalProperties: false` 때문에 계약 필드 추가가 필요하고, 그 시점에 동결 해제 절차 대상이 된다.

### 4. 범위 판정 후보

- **범위 밖(백로그)** — 사용자 결정으로 stage 미배정, 대체 수단(해안선·국경 ＋ 커서 좌표) 수용됨.
- v2 버그 아님 — 미구현 기능이고 기존 동작의 결함이 아니다.

### 5. 이번 bugfix 회차 포함 여부 제안

- **제외** — 신설 불요. 기존 `BF-10` 유지.

### 6. 크기

- 해당 없음(포함 후보 아님).

---

## 요약표

| 이슈 | 요지 | 기존 대장·결정 | 판정 후보 | 이번 회차 |
|---|---|---|---|---|
| #30 | 부모 데이터 찾기 모달의 찾기 방식 개선 | 담을 항목 없음(산출물은 `WU-B5`·`WU-B10` done) · 용어 근거 `〈189〉`-㉰ · `DP-1` 별건 | 재현 시 v2 버그(후보 0행) ／ 형태 변경은 편의 기능(후일 묶음) | 부분 포함 — 재현 확인만 |
| #12 | 구글 로그인 | `PA-G` `open`/`backlog` · 2026-09-11 절 | 범위 밖(백로그) | 제외 |
| #11 | 공유 로그인 실패 제한 ＋ 신뢰 프록시 | 담을 항목 없음 · `CR-2`(done) 완료 정의에 유예 문장만 | stage 3 계열 신설 항목 | 제외 ＋ 신설 제안 |
| #10 | 화면·저장 PNG 경위도 격자선·눈금 | `BF-10` `open`/`backlog` · 2026-09-11 절 | 범위 밖(백로그) | 제외 |

- 계수 기준 = 이슈 4건 중 「이번 회차 코드 변경 후보」 0건, 「재현 확인 후보」 1건(#30), 「대장 신설 후보」 2건(#11 · #30 형태 변경분).

## 대장 신설 후보

| 제안 `id` | 제안 `stage` | 한 줄 제목 | 근거 이슈 |
|---|---|---|---|
| `PA-T` | `after_stage2` | 로그인 실패 제한의 공유 저장소화 ＋ 신뢰 프록시 판정(다중 서버·prod 전 관문) | #11 |
| `LV-5` | `after_stage2` | 계보 부모 찾기 모달을 데이터셋 목록 화면과 같은 표·열·정렬로 재구성 | #30 |

- 제안일 뿐이며 번호 발급·등재는 하지 않았다. 최종 판정은 Ted.
- `after_stage2` 로 세우면 `CLAUDE.md §0` stage 표의 `<!-- work-items:after_stage2 -->` 괄호 목록을 같은 회차에 갱신해야 한다 — 그 괄호를 게이트 `work-item-consistency` ㈕ 가 대장과 대조한다(`CLAUDE.md §0` 축자).
- `LV-5` 는 「편의 기능 — 후일 묶음」으로 두고 `stage: backlog` 로 세우는 선택지도 성립한다(선택지 둘, 판정 대상).

## 후속 항목 (이 조사에서 고치지 않은 것)

- `frontend/src/components/lineage/ParentPicker.tsx` 의 빈 상태 문구는 조건 유무로만 갈린다 — 서버 오류와 「연구실 데이터 0」의 구분은 `props.error` 경로에만 있다. 재현 조사 시 함께 확인 대상.
- #11 유예 문장이 done 항목(`CR-2`) completion_def 안에만 있어 열린 작업으로 세어지지 않는다 — 항목 신설 전까지 집계에서 누락된다.
- 상세 화면에서 부모 데이터로 이동하는 경로 존재 여부 `[미확인]` — `frontend/src/components/lineage/LineageSection.tsx` 확인 필요.
