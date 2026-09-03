# recon-D — 버그 12건 범위 판정 (2026-09-03)

레포 루트 (SSOT: `dev-package/work-items.yaml`, 결정 로그: `dev-package/PLAN-SoT.md §9`)

## 1. 항목별 stage 1 범위 판정

| 버그 | 관련 WU id | status/stage | 판정 |
|---|---|---|---|
| A-1·A-2·A-3 (계보 그래프 화살표·빈칸) | `P3`(계보 그래프 · 2D 시각화) | `done` / `stage2` | **stage 1 범위 밖 스코프이지만 done 으로 배포된 기능의 결함 — 즉 결함이다.** `〈204〉`가 경계·점을 뺐을 뿐 격자 계보 그래프 자체는 배포·완료됨 |
| B-1 (Lv1 Bilinear 미리보기 회색 격자) | `〈74〉`(미리보기 3층) / `PV-1` | `〈74〉` stage1 정의·구현됨, `PV-1`(뒷단 고급 가공) `open`/stage2 | **부분적으로 stage1 결함.** 3층 중 ①②는 stage1 이미 구현·닫힘. Lv1 가공본은 `PV-1`(뒷단: 파싱·좌표계 통일)이 아직 `open` 이라 그 경계 안이면 stage2 미구현일 수 있음 — 원인 확인 필요(§2 참조) |
| B-2 (EPSG:4326 배경 지도 없음) | `POL-021`·`〈240〉` | 정본 정책 | **정책 위반 아님 — 정책이 명하는 대로 동작 중.** §2 참조 |
| B-3 (확대·축소·기본배율 버튼 미동작) | `P3` 확대(줌) 부분 | `done`(`〈232〉`·`〈233〉`·`〈241〉`로 닫힘) | **stage 1 범위의 결함.** 확대는 이미 구현·검증·배포 완료된 기능(§2 참조) — "아직 stage2라 안 됨"이 아니라 완료된 기능의 회귀 |
| B-4 (업로드 미리보기≠상세 미리보기, 기본배율 불명) | `P3`/`V-2` 인접 | `P3 done`, `V-2 in_progress` | 기본 배율 규칙 자체가 정본에 미기재로 보임 — 별도 확인 필요, 스코프상 stage1 화면(S-04/S-05) 결함 |
| B-5 (Co-Kriging Lv1 미리보기 값 범위 이상) | `〈74〉`(3층) / `〈307〉`(캐시 키 변경) / `RC-1` | `RC-1` `open`/stage2, `CR-1` `done` | **stale 캐시/구판 사이드카 의심 — §2 참조.** 원인 미확정이므로 "정상 동작"으로 단정 금지 |
| C-1 (카탈로그 좌측 padding 없음) | `P1`(카탈로그 S-03) | `done`/stage1 | **stage 1 결함** |
| C-2 (톱니 아이콘·글자 간격) | `연구실 설정` 화면 (E-01) | `done`류 배정 | **stage 1 결함(문안/레이아웃)** |
| C-3 (프로젝트 상세 raw HTML) | `P5`(S-02/S-02b, E-05) | `done`/`stage1` | **stage 1 결함.** `P5` 완료 정의 = "구현 + 게이트 green + staging 배포 green" 셋 다 충족(`〈230〉`)으로 닫힘 — raw 화면은 완료 판정된 기능의 회귀 |
| C-4 (`／` 구분자 과다) | 데이터셋 설명 문안 | 화면 문안 | **stage 1 문안 개선 요청** (버그라기보다 UX 제안 — 처리 원칙에서도 "제안 필요"로 명시) |

## 2. 지정 항목 상세

### B-2 — POL-021 / 〈240〉 축자 인용

`PLAN-SoT.md:591` 〈240〉 축자:
> 정본 260826 기획 정본 델타가 **축자**로 적은 것 둘 — 「서버 미리보기가 범위 안으로 들어왔다. PNG 한 장 + 경계 좌표 네 값 … **타일 서버도 바탕 지도도 쓰지 않는다**」(**POL-021** · 스펙 8·59) · 「미리보기 뷰어 = **타일 서버·바탕 지도 없이 PNG 한 장 + 경계 좌표 4값**」

`work-items.yaml:1150`(P3 completion_def)도 동일 축자 재인용. **POL-021 이 금지하는 것은 "타일 서버"와 "바탕 지도(basemap) 서비스"** — 즉 외부 타일/베이스맵 서비스 호출이다. 육지 윤곽 자체를 그리는 것을 명시로 금지한 문구는 없다. `〈240〉`은 「한 장」(imageUrl, PNG 단일 이미지 + bbox)을 기본값으로 두고 타일 갈래는 옵션으로만 허용하는데, 둘 다 **"바탕 지도 서비스 미사용"**이 전제다.

→ **판정**: 외부 타일 서버·베이스맵 API 호출은 정책 위반. 하지만 **자체 좌표 데이터로 그리는 정적(self-contained) 해안선 오버레이는 "타일 서버"도 "바탕 지도 서비스"도 아니므로 문면상 금지되지 않는다** — 다만 이는 텍스트 해석이며, 정본 문면에 "해안선 오버레이 허용" 같은 명시적 허가도 없다. **정책 변경 여부가 애매한 회색지대이므로 advisor 게이트에서 Ted 판정 필요** (버그 접수 문서의 처리 원칙과 일치).

### B-3 — 확대(줌)는 이미 stage 1(사실상 배포 완료) 범위, stage 2 대기 항목 아님

`〈78〉`(work-items.yaml에는 직접 id 없음, PLAN-SoT.md:348)은 **"편의 기능 지금 안 만든다"** 결정이며 그 묶음(`§J-1`~`§J-9`)은 "다른 데이터셋 격자 가져오기·연구실 기본 격자·격자 불일치 경고·팔레트 선택 UI·자동무효화(→ Y-1로 분리)·진행바 예측·동기 렌더·폴더 드래그" 등이다. **확대(줌)는 이 묶음에 없다.**

확대의 정본 근거는 `〈232〉`(`Policy_데이터셋_상세` v2.5, 닫는 조건 6개)이고, `〈233〉`(합격선: p95 100ms)·`〈238〉`(타일 전환 후 재검증)을 거쳐 `〈241〉`에서 **`P3`가 `done`으로 닫힐 때 "확대는 완료 정의 그대로" 충족 확인**됨(실측: 확대·축소 1회 p95 1.731~2.081ms, 15건 red→green 전환 시험 통과). CLAUDE.md의 stage 정의 줄(`§1`)에는 "확대"가 stage2 항목으로 나열되지만, 이는 **원래 신규 개발 항목으로서의 배정**이었고 실제로는 이미 구현·검증·배포됨(P3.status=done).

→ **판정**: "버튼이 있는데 stage2라 안 만들어졌다"가 아니라 **이미 만들어져 배포까지 검증된 기능이 지금 동작하지 않는 것** — 회귀/버그다. UI에 버튼을 숨기거나 비활성화할 사안이 아니라 원인 규명 후 수정 대상.

### B-1 / B-5 — RC-1·〈307〉과의 관계

`〈307〉`(코드리뷰 회차, 2026-09-03, 병합 `a1ff6af`)의 ㉱항: viz-render가 **"캐시 키에 시각·격자 digest"**를 추가했다. 이는 배포 순간 **기존 산출물·타일이 전량 캐시 미스**가 됨을 의미한다(`CR-1.note`, `RC-1` 진입조건 증보문 축자).

`RC-1`("구판 사이드카 재굽기 후 회수 1회", `status: open`, `stage: stage2`, `owner: D7/viz-render`)은 **아직 착수되지 않음** — "판정 불가 49건 → 19건"이 목표치이나 실행 0회. `RC-1`의 진입조건 증보(`〈307〉`-㉷⑶·㉸)는 명시적으로:
> "이 항목은 **배포 직후에 서야 하고**, 그 전에 소유 계수를 읽으면 안 된다 … 배포만 하고 재굽기를 건너뛴 채 읽은 계수는 **키가 갈려서 난 미스**이지 소유 판정이 아니다"

→ **판정**: B-1(Lv1 가공본 미리보기 사실상 없음)·B-5(Co-Kriging 미리보기 값 범위 이상·정체불명 밴드 의심)는 **stale/구판 사이드카 또는 캐시 키 불일치로 설명 가능한 강한 후보**다. `main`이 staging에 언제 배포됐고 `RC-1`(재굽기)이 그 뒤 돌았는지부터 확인해야 한다 — 확인 전에는 "코드 결함"과 "재굽기 미실행으로 인한 stale 상태"를 구분할 수 없다. 원인 규명이 수정보다 선행.

### C-3 — 프로젝트 상세(E-05)

`frontend/README.md` 화면표: `S-02 · S-02b 프로젝트 | E-05 | 5`. work-items.yaml의 `P5`("프로젝트 목록·상세(S-02/S-02b)", `status: done`, `stage: stage1`, `owner: D6`)가 이 화면을 진다. `〈230〉`에서 "구현 + 게이트 green + staging 배포 green" 셋 다 충족되어 닫힘. → **stage 1 완료 판정된 화면의 회귀 — 명백한 버그.**

## 3. 버그 등록 관행

- `work-items.yaml`에 `type`/`kind` 필드, "버그" 항목 관행 **없음** — 전 항목이 기능 단위(P1~P7, D-계열, V-, RC-, CR- 등)이고 결함은 해당 기능 항목의 `note`/`evidence`에 "⛔ 새 차단" 형태로 누적 기록되는 관행(`P3`의 ㈎㈏㈐ 등).
- `dev-package/reports/`는 세션 산출 HTML(진행 보고), `dev-package/sessions/`는 `<주제>-<날짜>.md` 네이밍(예: `V-2-CLOSE-20260903.md`, `X5-AUDIT.md`) — 워크트리·조사 세션 기록.
- follow-up 항목 id 네이밍 관행: **접두어 2글자 + 일련번호** — `CR-1`/`CR-2`(코드리뷰 후속), `RC-1`(재굽기·회수), `TL-1`(latency), `V-1`/`V-2`(값 조회). 신설 근거는 항상 `PLAN-SoT §9 〈N〉`을 등재 링크로 인용.

**권장**: 버그 12건을 `work-items.yaml`에 `BF-1`~`BF-N`(Bug Fix) 또는 유사 접두어로 개별 항목 등록(필드: id, name, status(open), stage(stage1), owner, entry_conditions, depends_on, completion_def(=재현→근본원인→실패시험 red→수정→green), evidence, deadline, note(원 버그 번호·스크린샷 경로 링크), sources). 동시에 `PLAN-SoT.md §9`에 등재 결정 1건(신규 버그 배치 판정)을 추가.

**다음 자유 결정 번호**: `〈309〉` (PLAN-SoT.md §9 전체에서 실측한 최댓값 = `〈307〉`).

## 4. `work-item-consistency` 게이트 (`gates/tools/work_item_consistency.py`, 문서 `gates/README.md`)

검사 8종(㈎~㈕, `〈268〉` 증보):
- ㈎ 대장 스키마 · ㈏ `WORK-UNITS.md §11` 완주 체크리스트 대조 · ㈐ `03-HANDOFF.md §1` 진실원 표 대조 · ㈑ `⏸`(보류) 항목의 착수 후보 표 혼입 · ㈒ 기한 발동인데 미개방 · ㈓ `status: conflict` 잔존 · ㈔ `PLAN-SoT §9` 결정번호 `〈n〉` 중복 · **㈕ `CLAUDE.md`의 `<!-- work-items:after_stage2 -->` 표지 블록 ↔ 대장 `stage: after_stage2` 집합 양방향 대조**(표지 부재·미폐쇄·`CLAUDE.md` 부재 = red).

→ 새 버그 항목 추가 시 지켜야 할 것: (1) `WORK-UNITS.md §11` 체크리스트에도 대응 줄 필요 여부 판단, (2) `03-HANDOFF.md §1` 진실원 표와 정합, (3) stage를 `after_stage2`로 지정한다면 `CLAUDE.md`의 `<!-- work-items:after_stage2 --> … <!-- /work-items:after_stage2 -->` 표지 블록에도 id를 반드시 추가(양방향 대조라 한쪽만 고치면 red).

## 5. 프런트 로컬 실행 / staging 접근 (명령만, 실행하지 않음)

**로컬 (`frontend/README.md`):**
```
npm ci             # node 22, 의존성 exact 핀
npm run generate   # contracts/seams/fe-core.yaml → src/generated/fe-core.ts
npm run typecheck  # tsc --noEmit
npm run build      # typecheck + vite build → dist/
npm test           # vitest
npm run dev
```

**staging 컨테이너 기동 (`dev-package/RESTART.md`):**
```
docker ps
docker compose -f infra/staging/compose.i2.yml --env-file ~/.colab-v2-staging.env up -d
docker ps --filter name=colab_v2_staging --format '{{.Names}}\t{{.Status}}'
```

**staging 헬스체크 (`dev-package/RESTART.md:156-158`):**
```
curl -s -o /dev/null -w 'root %{http_code}\n' -I https://www.colab-hydro.com/healthz
curl -s -o /dev/null -w "$u %{http_code}\n" https://www.colab-hydro.com/healthz/$u
```

staging 접근 주소 = `https://www.colab-hydro.com`(Cloudflare Tunnel 경유, `dev-package/DEPLOY-CURRENT.md §3`).
