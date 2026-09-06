# R-B-4 · 검증 계층 ＋ R-B 종료 검증 — WU-B11

> 이 파일 하나로 세션을 시작한다. 라운드 = **R-B** · 계층 = **검증(FE·CSS)** · WU **1건** ＋ **라운드 종료 검증**.
> `dev-package/prd/rounds/R-B.md` §6 의 분할 지시에 따라 갈라 나온 **네 번째이자 마지막 파일**이다.
> **진입조건 = ⑴ R-A 병합 완료 ⑵ WU-A11 판정표 회수 — 둘 다 충족.** 판정표 = `dev-package/sessions/p3-design-audit-20260905.md`(대장 `WU-A11` `status: done` · `evidence` 가 이 경로를 가리킨다). ⛔ **판정 없이 고치지 않는다.**
> ⚠ 의도 문서 = `dev-package/intent/2026-09-07-r-b.md` (**미승인 초안** — 승인 전에는 이 파일의 문면이 우선이다).

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.** 세션이 느려지는 원인이 이것이다.
> `dev-package/03-HANDOFF.md`(다이어트 후 약 127 KB, 그래도 통째로 열지 않는다) · `dev-package/PLAN-SoT.md`(1.17 MB) · `dev-package/work-items.yaml`(513 KB) · `dev-package/WORK-UNITS.md`(138 KB)

- **허용된 접근은 아래 세 줄뿐이다.**
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-B11' dev-package/work-items.yaml`
  3. 게이트 이름 확인 — `sed -n '12,30p' gates/run.sh` (`ALL_GATES` 배열)
- 판정표(`dev-package/sessions/p3-design-audit-20260905.md`)는 **통째로 읽는다** — 46행이고 이 WU 의 범위 정의서다.
- `03-HANDOFF.md` · `CLAUDE.md` · `RESTART.md` 는 **머리 부분만** 읽는다. 본문 통독 금지.
- 요구사항 정본은 이 파일과 `dev-package/prd/PRD-260905-적용전기획.md` 다. 더 필요하면 PRD 사본에서 **`#### PRD-29` 절만** 읽는다.
- **코드 파일은 고칠 때만 연다.** CSS 전수 정찰은 **서브에이전트에 위임**하고 `path:line` 표만 회수한다.
- ⭑ **이 파일의 `path:line` 은 `integration/r-b` `ccd9372` 실측이다.** 앞선 세 파일(B1·B2·B4·B6 / B5·B7·B8 / B3·B10)이 CSS 를 건드리면 **다시 잰다.** 옛 줄번호를 옮겨 적지 않는다.
- 못 읽으면 `[미상]` 이고 실패다. 지어내지 않는다.

---

## 1. 확정 결정 — 다시 열지 않는다 (PRD §1 · Ted 2026-09-05)

미결 18건이 전부 닫혔다 = 확정 16 ＋ 해소 1(미결-8) ＋ 개발 실측 1(미결-10). **기획자에게 받아야 하는 답은 0건이다.**
아래 16줄이 요구사항이다. 다르게 구현할 사유를 찾으면 **고치지 말고 보고한다.**

- 미결-1 ⓐ — 공개 범위는 **연구실 내부 3값**(`연구실 구성원 전체`/`나만 보기`/`지정한 사람만`), 기본 선택 `연구실 구성원 전체`. 저장은 `열림`·`잠김`·`지정 공개`. RLS 경계를 열지 않고 PRD-37·WU-C5 를 열지 않는다
- 미결-2 ⓐ — 가공 단계를 **사람이 고르고**, 계보 계산값과 어긋나면 **경고만** 낸다(등록을 막지 않는다). `processing_level_user_set` 재신설 ＋ 원장에 `〈194〉` 반전 기재
- 미결-3 ⓐ — 기존 13행의 3축은 **전 행 NULL**, 자동 매핑 없음. 표기 「분류를 아직 안 골랐어요」, `topic` 열은 남긴다
- 미결-4 ⓐ — 관측 간격은 **선택 입력**. 저장은 수치＋단위 두 칸, 표기는 기간 뒤 괄호 (R-A 에서 닫힘)
- 미결-5 ⓐ — 설명 필수화 후 빈 기존 행은 **그대로 두고** 그 행을 수정할 때 채우게 한다 (R-A 에서 닫힘)
- 미결-6 ⓐ — 확정 부모 1건 이상이면 체크박스 **잠금＋사유 한 줄**. 라벨 = `가공 전 데이터를 못 찾았어요 — 기록 없이 등록할게요`
- 미결-7 ⓐ — 가공 단계 **Lv0~Lv3 네 단**(CHECK 4값 · 계약 enum 4값 · 화면 칩 4단)
- 미결-9 ⓑ — 상세는 **한 페이지 스크롤 유지 ＋ sticky 구역 메뉴** (R-A WU-A8 이 최종형)
- 미결-11 ⓐ — 원천 표기(`sourceLabel`)는 **Lv 무관 상시 노출**, `sourceUrl`·`sourceDownloadedOn` 두 칸만 Lv0 게이팅
- 미결-12 ⓐ — 유형별 주의 문구는 **선택기 아래 보조 문구 ＋ 설명란 힌트**(저장 칸 없음 · 표시층 문자열)
- 미결-13 ⓐ — 분류·유형은 **표시만 국문＋영문 병기**(`기상·기후 인자 (Meteorological & Climatic Factors)`), 저장·CHECK·필터·색인은 국문 단일
- 미결-14 ⓐ — 유형↔가공 단계 **제약 없음**(조합 검증을 만들지 않는다)
- 미결-15 ⓐ — 종료 모달은 조건만 고치고 문면 유지 (R-A 에서 닫힘)
- 미결-16 ⓐ — 등록 ③ 의 쓰임 한 줄은 **받지 않는다**(PRD-36 · WU-C4 범위 밖)
- 미결-17 ⓐ — pdf 항목 8 잘린 1행은 원문 요청 중. **회신 대기가 WU-B2 착수를 막지 않는다** — 변수 표 본문은 `T-38`~`T-44` 로 확보돼 있다. ⛔ **추정 전사를 하지 않는다**
- 미결-18 ⓐ — 기간은 시각값 저장 유지, 화면만 구조화 (R-A 에서 닫힘)
- ⭑ **미결-10 = 개발 실측** — **WU-A11 판정표가 곧 이 파일 WU-B11 의 범위다.** 미결-8 = 해소(값 표가 pdf 원문).

---

## 2. 범위 — WU 1건 ＋ 라운드 종료 검증

### §A · WU-B11 · 디자인 검수 수정 (PRD-29 후속) — 계층 FE · 크기 **M** · 레인 `p3-design-fix`

- **크기 근거** — 판정표 「있음」 **6건** · CSS 6종 중 4종(`lineageGraph`·`catalog`·`detail`·`upload`)이 대상 · 고칠 선언이 **13(⑦) ＋ 7(⑧) ＋ 4(⑨) ＋ 11(⑩) ＋ 12(⑪) 규모**. 계약·스키마·서버 0. ⟹ **M**. (`R-B.md` §2 표의 `[미상]` 을 이 실측으로 닫는다.)
- **의존** — **WU-A11**(판정표 회수 · 충족). 같은 CSS 를 건드리는 **WU-B3·B10 뒤**에 돈다 — 앞서 돌면 재작성으로 지워진다.
- **계약 0 · 스키마 0 · 마이그레이션 0** — ⛔ **20차 해제를 쓰지 않는다.** `contracts/` 를 열면 §5-㉰-6(묶음 쪼개기) 위반이다.

**놓치면 안 되는 것 (`R-B.md` §2 축자)** — 「**WU-A11 이 `있음` 으로 판정한 항목만** 고친다. 대비 3건(**Lv 칩 · 연결 불가 후보 · 그래프 라벨**)이 접근성 합격선이라 **먼저 돈다**. ⛔ **판정 없이 고치지 않는다.**」
⭑ 그 대비 3건 중 **살아남은 것은 ⑦ 하나뿐이다**(①·③ = `없음`). ⟹ **⑦부터 돈다.**

**범위 = 「있음」 6건.** 아래 `path:line` 은 `ccd9372` 재측정값이고, 괄호 안이 판정표 기재값이다.

| # | 항목 | 재측정 `path:line` (`frontend/src/` 이하) | 판정표 기재 |
|---|---|---|---|
| ⑥ | 카드 그림자 제거 | `components/catalog/catalog.css:31` `.catalog-page .card { … box-shadow: var(--shadow-sm) … }` | `catalog.css:31` **일치** |
| ⑦ | 계보 그래프 라벨 **13px 이상** | `components/lineage/lineageGraph.css` 13px 미만 선언 **13건** — `:10`·`:14`·`:58`·`:81`·`:95`(11px) · `:31`·`:72`·`:82`·`:83`·`:85`(10px) · `:44`(10.5px) · `:45`(12.5px) · `:76`(12px). 최소 **10px** | 동일 13건 **일치** |
| ⑧ | 캡션 눌림 **7곳** 승격 | 아래 별표 | 4유형 7곳 |
| ⑨ | 보더 2층 토큰 분리 | 컨테이너 `components/detail/detail.css:66` ↔ 칸 구분선 `:69` 가 **같은 `--color-border`** · `components/catalog/catalog.css:30` 바깥선 `--color-border` vs `:41`·`:45` 안쪽선 `--color-border-strong` = **역전** | `detail.css:59/62` · `catalog.css:30/41` (detail 은 **이동**) |
| ⑩ | 여백 소유권 컨테이너 이관 ＋ **음수 상쇄 2건 제거** | 음수 — `components/detail/detail.css:100` `margin: -12px 0 …` · `shell/shell.css:58` `margin-left: -7px`. 자식 소유 — `components/lineage/lineageGraph.css:7` `margin-top:34px` ＋ `components/upload/upload.css` `margin-top` 다수(`:113`·`:135`·`:145`·`:148`·`:157`·`:166`·`:168`·`:189`·`:232`~`:235`·`:241`·`:249`) | `detail.css:93` · `shell.css:58` (detail 은 **이동**) |
| ⑪ | 죽은 스타일 제거 | 덮인 선언 1 — `components/lineage/lineageGraph.css:33` `display:inline-block` 이 `:29` `display:inline-flex` 를 덮는다. 미정의 토큰 참조 **11건**(폴백 없음 → 선언 무효화) — `:30`(`--color-accent-50`·`-200`)·`:31`(`--color-accent-700`)·`:48`·`:49`(`--color-gray-300`)·`:51`(`--color-primary-800`)·`:57`(`--color-primary-200`·`-800`)·`:83`(`--color-accent-700`·`-50`)·`:84`(`--color-ai`). `shell/tokens.css`(43행)에 이 이름들이 **0건** | **일치** |

⭑ **⑧ 캡션 7곳 — 재측정에서 두 자리가 어긋난다.**
- 파일명 — `components/detail/detail.css:108` `.filelist .fl-x`(11px). 판정표의 `detail.css:101` 은 이 트리에서 보더 선언이다 ⟹ **재측정값을 쓴다**. 같은 블록의 `:104` `.fl-k`(10px)도 같은 유형이다.
- 업로드 안내 — `components/upload/upload.css:109` `.up-note`(12px). (판정표 `upload.css:106`.)
- 빈 화면 안내 — `components/lineage/lineageGraph.css:95` `.lin-empty .muted`(11px) **일치**.
- 목록 링크 — `components/lineage/lineageGraph.css:81` `.lrow .ln-sub`(11px) · `:76` `.lrow .ln-name`(12px) **일치**.
- 오류 본문 — 판정표 `upload.css:92`(12px). **현재 `components/upload/upload.css:156-162` `.vizerr, .warn` 이 `font-size: 13px` 다 ⟹ 이 한 자리는 R-A′ 중에 이미 충족됐다.** ⛔ **다시 고치지 않는다.**
- 판정표 미지목 자리(`upload.css:168` `.vizph`)는 **현재 `font-size` 선언이 없다** — 대응 선언 `[미상]`. **지목 목록에 없으므로 손대지 않는다.**
- 6종 합계 13px 미만 선언 — 재측정 **60건**(9px 포함 · `tokens.css` 0 · `shell.css` 1 · `lineageGraph.css` 13 · `catalog.css` 14 · `detail.css` 11 · `upload.css` 21). 판정표는 **47건**이라 적었다 — **셈법 차이**이고 착수 시 다시 잰다. ⛔ **승격 대상은 지목된 7곳뿐이다** — 60건을 일괄로 올리지 않는다.

**⛔ 「없음」 5건은 범위 밖이다 — 없는 결함을 고치지 않는다.**
- ① Lv 칩 글자색 — `detail.css` 실측 **4.66:1**(Lv3·Lv2) · **4.94:1**(Lv1) · **5.70:1**(Lv0) = **AA 통과**. 목업 결함이 v2 로 넘어오지 않았다.
- ③ 연결 불가 후보 행 흐림 — **요소 자체가 없다**(흐리게 할 자리를 PRD-08 이 만든다 = WU-B5 소관).
- ② 제약 안내 색 · ④ 활성 탭 밑줄 · ⑤ 상단 버튼 모양 — 판정 `없음`.

**수용 기준**
- Given `.catalog-page .card`, When 목록 조회, Then **그림자가 없다**(팝오버 `catalog.css:80` 은 그대로 그림자를 진다).
- Given 계보 그래프, When 렌더, Then **13px 미만 선언이 `lineageGraph.css` 에 0건**이다.
- Given 지목된 캡션 7곳(위 별표 · 오류 본문 제외 6곳 ＋ 판정표 축자 1곳), When 렌더, Then **13px 이상**이고 **레이아웃이 깨지지 않는다**.
- Given `detail.css` 컨테이너와 칸 구분선, When 토큰 확인, Then **서로 다른 토큰**이고 `catalog.css` 는 **바깥선이 안쪽선보다 진하거나 같다**(역전 해소).
- Given 음수 상쇄 2건, When 코드 확인, Then **0건**이고 여백을 **컨테이너가 소유**한다.
- Given `lineageGraph.css`, When 코드 확인, Then **덮인 `display` 선언 0건** ＋ **미정의 토큰 참조 0건**(토큰을 `tokens.css` 에 세우거나 정의된 토큰으로 바꾼다 — 둘 중 하나를 고르고 근거를 세션 노트에 적는다).
- Given 위 전부, When `frontend-typecheck`·`frontend-test`·`frontend-fixture-reach`, Then **green**.

**⭑ 판정 대기 2건 — 「추가 발견 (R-19~R-29 밖)」 · 이 WU 의 완료 판정이 아니다**
- `catalog.css` 에 **`.lvl-3` 클래스가 없다** — 재측정 `components/catalog/catalog.css:125·126·127` 에 `.lvl-0`·`.lvl-1`·`.lvl-2` 만 있다. 마크업은 `components/catalog/CatalogTable.tsx:159` 이 `` `lvl lvl-${row.processingLevel}` `` 로 **Lv3 을 낸다** ⟹ Lv3 칩에 배경·글자색이 붙지 않는다.
  ⭑ **미결-7 ⓐ(Lv0~Lv3 **네 단**)와 정면으로 맞물린다 ⟹ Ted 판정 대상으로 올린다.** 이 WU 가 임의로 4단째 색을 정하지 않는다.
- `components/catalog/catalog.css:135` `.lin--none` = `--color-gray-400` on 흰 배경 → **3.41:1**(AA 미달). **11건 밖 · 판정 대기.**
- 둘 다 **「판정 대기 · 이 WU 의 완료 판정 아님」** 으로 라운드 보고에 적고 끝낸다. ⛔ **판정 없이 고치지 않는다.**

### §B · R-B 라운드 종료 검증 — 이 파일이 라운드의 마지막이다

- **경계 증명 2건** — `cross-tenant 음성 0건`(WU-B2 · WU-B4) · `state='잠김' ∧ 유효 grant ≥1 인 행이 **어느 시점에도 0건**`(WU-B4).
- **회귀 증명 3건** — 변수명 검색이 종전과 같이 잡힌다(B2) · 매핑 후 기존 허용자의 접근이 종전과 같다(B4 · **양성·음성 둘 다**) · 부모 ≥1 경로의 계보 판정이 종전과 같다(B8).
- **R-A 이월 1건** — PRD-21 「`nc` 로도 찾는다」가 **WU-B7 뒤 `M-10` 으로 닫혔음**을 라운드 종료 보고에 **명시**한다.
- **게이트** — 라운드 끝에 `bash gates/run.sh all -j 1` **green** ＋ **staging 배포 green**(`CLAUDE.md §0`).
- **절차 검증 4항** — §5 에 적는다.

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 워크트리 레인

- WU 하나에 레인 하나. 레인 이름 = `p3-design-fix`. `origin/main` 에서 딴 자기 워크트리에서 돈다.
- 병합은 **ff-merge**, 병합 뒤 워크트리·로컬/원격 브랜치를 정리한다. 한 레인 = 한 WU.
- ⭑ **순서는 이 레인이 R-B 의 마지막이다** — WU-B3·B10 이 같은 CSS 를 건드린 뒤에 돈다.

### ㉯ 착수 전 — `work-items.yaml` **등재 확인**(등재는 끝났다)

WU-B11 을 포함한 R-B **10건의 대장 등재는 이미 끝났다.** 이 세션은 **확인만** 한다.

```bash
grep -n -A14 '^  - id: WU-B11' dev-package/work-items.yaml
```
확인 항목 — `entry_conditions` 에 **「WU-A11 판정표 회수」**가 있다 · `depends_on` 에 `WU-A11` 이 있다 · `evidence` 가 세션 노트 경로다.
⛔ **없으면 착수하지 않는다.** 완료 시 `status: done` ＋ `evidence` 를 갱신한다. **이 WU 는 마이그레이션이 0이라 마이그레이션 원장 행이 없다.**

### ㉰ 계약 동결 해제 — **이 파일은 계약을 열지 않는다**

근거 문서 = `dev-package/sessions/X2-FREEZE-PROTOCOL.md` §5. 라운드 회차 = **20차**이지만 **그 회차가 여는 것은 WU-B1·B2·B4·B6·B8 뿐이다.**
⛔ **WU-B11 은 `contracts/` 를 건드리지 않는다** — 건드리면 20차 요청문에 실리지 않은 값을 여는 것이고 **§5-㉰-6(묶음 쪼개기) 위반**이다.
- 종료 검증(§B)은 **20차 등재가 `PLAN-SoT §9` 에 실려 있는지**와 **`〈194〉` 반전 행이 원문을 지우지 않고 덧붙여져 있는지**를 확인한다 — 하나라도 아니면 **라운드를 닫지 않는다.**

### ㉱ 결정 번호 〈N〉 — 예약하지 않는다

```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전에 다시 잰다
```
2026-09-07 실측 최대 = **〈372〉**(참고값). **R-B 가 번호를 여럿 쓰므로 병합 직전에 반드시 다시 잰다.**
WU-B11 의 수정은 판정표 집행이라 결정 1행을 남긴다 — `PLAN-SoT §9` 에 **병합 직전** 덧붙인다(필드 8개 · X2 §5-㉲).

```
| 〈N〉 | **R-B-4 디자인 검수 수정 — WU-A11 판정 「있음」 6건 집행. 「없음」 5건은 고치지 않았다** | **집행 (2026-MM-DD · 워크트리 `p3-design-fix` · 병합 `<sha>` · 계약 0 · 스키마 0 · 마이그레이션 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음(CSS 만) ③근거 = PRD-29 · 미결-10 · 판정표 `dev-package/sessions/p3-design-audit-20260905.md` ④가·파 판정 = 해당 없음 ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요 ⑧이번에 세지 않은 축 = 추가 발견 2건(`.lvl-3` 부재 · `.lin--none` 3.41:1) `[판정 대기]` — `.lvl-3` 은 **미결-7 ⓐ 와 맞물려 Ted 판정 대상** |
```
⛔ **HANDOFF 에는 값을 적지 않는다**(`CLAUDE.md §6-3`).

### ㉲ 게이트 — 작업 중엔 단독, 라운드 끝엔 전건

```bash
# 작업 중 (WU-B11)
bash gates/run.sh frontend-typecheck
bash gates/run.sh frontend-test
bash gates/run.sh frontend-fixture-reach
# R-B 라운드 종료 (한 번)
bash gates/run.sh all -j 1
```
⭑ **`all -j 1` 은 호스트 12GB 규정이다 — 도는 동안 다른 레인 0**(`.claude/rules/colab-rules.md` §9).
⛔ **게이트를 끄거나 검사 대상을 줄이지 않는다.** `frontend-test` 는 **수집된 시험 0건도 red** 다.
⭑ **`all` 이 red(준비)를 내면 판정 red 와 가른다** — 입력 미선언은 판정이 아니다. **가른 근거를 출력으로 남긴다.**

### ㉳ 커밋 문면

```
FE R-B-4 — 디자인 검수 「있음」 6건 수정 (WU-B11)

- 판정표 6건만 고쳤다 — 「없음」 5건과 추가 발견 2건은 손대지 않았다
- 계약 0 · 스키마 0 · 마이그레이션 0 · PLAN-SoT §9 〈N〉 등재
- RED 선실측 → GREEN: <시험 파일>:<건수>
```

### ㉴ 금지

- ⛔ `main` 에 직접 push. ⛔ staging DB 직접 쓰기. ⛔ `contracts/` 수정(이 WU 는 계약 0).
- ⛔ **판정 없이 고치기** · ⛔ **없는 결함 고치기**(①·③ 을 포함한 「없음」 5건).
- ⛔ 추가 발견 2건(`.lvl-3` 부재 · `.lin--none`)을 이 WU 에서 고치기 — **판정 대기**다.
- ⛔ 13px 미만 선언 **일괄 승격** — 지목된 7곳만 올린다. ⛔ 이미 충족된 자리 다시 고치기(`upload.css:156-162` 13px).
- ⛔ WU-B3·B10 이 세운 화면 구조를 CSS 정리 명목으로 재작성. ⛔ 토큰을 지우고 값을 하드코드로 박기.
- ⛔ `40 COLAB-기획/` 문서 수정. ⛔ 문서·주석에 절대경로. ⛔ 이 세션이 `03-HANDOFF.md` 를 직접 고치기 — §4 의 5줄만 넘긴다.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| CSS 수정 | `frontend/src/components/lineage/lineageGraph.css` · `catalog/catalog.css` · `detail/detail.css` · `upload/upload.css` · `shell/shell.css`(⑩ 음수 1건) · `shell/tokens.css`(⑪ 토큰 세울 때만) |
| 판정 대비표 | 세션 노트 안 — **6건 각각에 `수정 전 path:line → 수정 후` 한 줄** ＋ 「없음」 5건 **미착수 사유** |
| 판정 대기 2건 | 세션 노트 ＋ 라운드 보고 — `.lvl-3` 부재(**Ted 판정 대상 · 미결-7 ⓐ**) · `.lin--none` 3.41:1 |
| 회귀 시험 | `frontend/test/` — 그림자 0건 · `lineageGraph.css` 13px 미만 0건 · 미정의 토큰 참조 0건을 **grep 계측으로** 잰다 |
| 세션 노트 | `dev-package/sessions/p3-design-fix-<YYYYMMDD>.md` — **≤ 60행** |
| 대장 | `dev-package/work-items.yaml` — `WU-B11` 확인 후 완료 시 `status: done` ＋ `evidence` |
| 원장 | `PLAN-SoT §9` 한 행(㉱ 문안) — **병합 직전** |
| 라운드 종료 | `bash gates/run.sh all -j 1` 출력 ＋ staging 배포 green ＋ **경계 2 · 회귀 3 · 이월 1 · 절차 4** 보고 |

**오케스트레이터에 넘기는 HANDOFF 갱신문 — 5줄 이하. 세션이 `03-HANDOFF.md` 를 직접 고치지 않는다.**

```
R-B-4(검증) 완료 — WU-B11, 레인 p3-design-fix, 병합 <sha>
디자인 검수 「있음」 6건 수정 · 「없음」 5건 미착수(없는 결함) · 계약 0 · 스키마 0 · 마이그레이션 0
판정 대기 2건 — catalog.css .lvl-3 부재(미결-7 ⓐ 와 맞물림 · Ted 판정 대상) · .lin--none 3.41:1 AA 미달
R-B 종료: bash gates/run.sh all -j 1 = green <n>/<n> · staging 배포 green · 20차 등재 〈N〉·〈194〉 반전 확인
R-A 이월 1건 종결 — PRD-21 「nc 로도 찾는다」가 WU-B7 뒤 M-10 으로 닫혔다
```

---

## 5. 완료 판정

- **WU-B11** — 판정표 **「있음」 6건(⑥⑦⑧⑨⑩⑪)**이 §A 수용 기준대로 닫혔다 · **⑦을 먼저 돌았다**(살아남은 유일한 접근성 합격선) · **「없음」 5건을 고치지 않았다** · **추가 발견 2건을 고치지 않고 판정 대기로 넘겼다** · 계약 0 · 스키마 0 · 마이그레이션 0 · `frontend-typecheck`·`frontend-test`·`frontend-fixture-reach` green.
- **경계 증명 2건** — `cross-tenant 음성 0건`(B2·B4) · `state='잠김' ∧ 유효 grant ≥1` 인 행이 **어느 시점에도 0건**(B4).
- **회귀 증명 3건** — 변수명 검색 종전과 동일(B2) · 매핑 후 기존 허용자 접근 종전과 동일(B4 · **양성·음성 둘 다**) · 부모 ≥1 경로 계보 판정 종전과 동일(B8).
- **R-A 이월 1건** — PRD-21 「`nc` 로도 찾는다」가 **WU-B7 뒤 `M-10` 으로 닫혔음**이 라운드 종료 보고에 적혀 있다.
- **게이트** — 라운드 끝 `bash gates/run.sh all -j 1` **green**(판정 red **0** · 준비 red 는 가른 근거를 출력으로 남긴다 · 도는 동안 **다른 레인 0**) ＋ **staging 배포 green**.
- **절차 검증 4항**
  1. **20차 승인이 `contracts/` 첫 수정보다 먼저** 있었음이 **커밋 순서로 보인다**.
  2. **`〈N〉` 이 병합 직전 실측값**이다(예약값이 아니다).
  3. **`〈194〉` 반전이 원문을 지우지 않고 덧붙여져 있다**(`0011` 삭제 근거 주석 포함).
  4. **마이그레이션 head 가 1개다** — 착수 시점 실측 head = `0014_merge_ra1_and_topic_vocab`. R-B 가 그 위에 한 head 를 잇는다.

---

### 다음 파일

**없다 — 이 파일이 R-B 의 마지막이다.** 라운드 종료 절차는 아래 순서로 돈다.

1. WU-B11 병합 → **§5 의 WU 판정** 통과 확인.
2. **경계 2 · 회귀 3 · 이월 1** 증명을 라운드 보고에 모은다(각 증명의 시험 파일·건수를 축자로).
3. `PLAN-SoT §9` — 20차 해제 1행 ＋ `〈194〉` 반전 1행 ＋ 이 파일의 〈N〉 1행이 **전부 등재됐는지** 확인.
4. **다른 레인을 전부 멈추고** `bash gates/run.sh all -j 1` 을 **한 번** 돌린다 → **staging 배포 green**.
5. **절차 검증 4항**을 커밋 순서·원장 diff·`migration-single-head` 출력으로 확인.
6. `dev-package/prd/README.md` 상태표의 R-B 4행을 닫고 HANDOFF 5줄을 오케스트레이터에 넘긴다.
7. **판정 대기 2건을 Ted 에게 올린다** — `.lvl-3` 부재는 **미결-7 ⓐ(Lv0~Lv3 네 단)와 맞물린 판정 요청**이다. ⛔ 답 없이 다음 라운드에서 임의로 고치지 않는다.
