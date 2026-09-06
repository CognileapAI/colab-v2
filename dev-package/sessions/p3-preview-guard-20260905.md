# WU-A2 · 미리보기 생성 권한 구멍 (PRD-26) — 레인 `p3-preview-guard`

- 라운드 파일 = `dev-package/prd/rounds/R-A-2-server.md` §2 WU-A2 · §5
- 기점 = `origin/integration/r-a` (`262f00a`, WU-A1 병합분) · 마이그레이션 **0건** · 계약 파일 변경 **0건** · FE 변경 **0건**

## 1. 무엇을 고쳤나

| 자리 | 무엇 |
|---|---|
| `services/core-api/src/colab_core/app/routes/preview.py:56-79` | `_target_in_lab`(bool·경계만) → `_require_target_access` — 데이터셋은 `catalog.require_body_access`(:74 · **값 조회·내려받기와 같은 함수**), 업로드는 원장 `uploader_account_id` 대조 후 남이면 **404**(:77-79) |
| `…/preview.py:128-135` | `create_preview_render` 에 ⑴ `업로드·편집` 403 ⑵ 대상 접근 판정 두 줄 추가 |
| `services/core-api/tests/test_preview_render_guard.py` | 신규 회귀 시험 **5건** |

- **새 판정 로직 0** — `permissions_of`·`require_body_access` 둘 다 기존 호출자(스크린샷 중계·값 조회)와 **같은 이름**이고, 권한을 대상보다 먼저 보는 순서도 스크린샷 중계(`preview.py:209-212`)와 같다.

## 2. 판정 함수 재사용 diff 증명

```
$ git diff -- services/core-api/src/colab_core/app/routes/preview.py | grep '^[+-].*require_body_access\|^[+-].*permissions_of'
+    쓰는 `catalog.require_body_access` 를 **그대로** 부른다 — ⑴ 경계 밖이면 404(존재를
+        catalog.require_body_access(db, Ulid(dataset_ref))
+    permissions = d2_access.permissions_of(db, subject.account_id, role)
$ grep -n 'catalog.require_body_access' services/core-api/src/colab_core/app/routes/preview.py
74:        catalog.require_body_access(db, Ulid(dataset_ref))     ← 생성 (신규)
298:    catalog.require_body_access(db, dataset_id)               ← 값 조회 (종전)
```

## 3. RED 선실측 → GREEN

```
(RED)  3 failed, 2 passed in 9.65s
       실패 3 = ⓐ 스위치 없는 사람이 렌더 시작(assert 202 == 403)
              · ⓑ 잠긴 DSA2 를 그려 줌(assert 202 == 403)
              · ⓔ 재사용 없음(assert 1 >= 2)
(GREEN) 20 passed in 11.71s   (신규 5 + test_preview_relay 10 + test_preview_screenshot_relay 5)
```
시험 5건 (`tests/test_preview_render_guard.py`) — ⓐ `업로드·편집` 없으면 **403** ⓑ 잠긴 `DSA2` 대상 **403**
ⓒ 자기 등록 전 업로드 **202**(회귀 방지) ⓓ 다른 연구실 `DSB1` **404**(현행 유지) ⓔ 재사용 코드 검사.
ⓐⓑⓓ 는 **가짜 viz 가 요청을 한 건도 안 받았음**도 함께 잰다(판정 전에 중계가 나가면 red).

## 4. 게이트 (§5 WU-A2 분 — `all` 은 돌리지 않았다)

```
service-tests-core-api — 선택자 «not e2e» · 수집 644 · 실행 644 · skipped 0 · deselected 6 · failed 0 · errors 0 · 88.9초   → green
rls-effect — 본체 음성 · 메타 양성(P-13) · lab_id 보유 표 23개 전수 남의 연구실 0행 · cross-tenant 전수 0행 · 판정 롤 우회 불가   → green
```
644−639(WU-A1 병합 시점) = 신규 5건. FE 변경 0 이라 프론트 게이트는 A2 대상이 아니다.

## 5. 계약 실측 — **403 이 없다 · 이 레인은 계약을 열지 않았다**

`contracts/seams/fe-core.yaml:1678-1681` `createPreviewRender.responses` = `202·400·401·404·413·500` — **`403` 미선언**
(라운드 파일 §2 실측과 일치). §3-㉴ 가 WU-A1·A2·A13 의 계약 파일 수정을
금지하므로 **여기서 고치지 않았다** — X2 §5 등급 판정이 오케스트레이터 몫으로 남는다. 서버는 정본대로 403 을 내고,
「계약 변경 0」은 사실이되 **미선언 상태가 남는다** = `[미해소 — 등급 판정 대기]`.

## 6. PLAN-SoT §9 행 초안 (⚠ 초안 · 병합 직전 `〈N〉` 재실측 · 이 세션은 PLAN-SoT 를 고치지 않았다)

```
| 〈N〉 | **R-A-2 서버 계층 — 미리보기 생성 권한 구멍 폐쇄(WU-A2 분)** | **집행 (2026-09-05 · 워크트리 `p3-preview-guard` · 병합 `<sha>`).** ①회차 = **해당 없음**(WU-A2 는 계약을 열지 않는다 · 19차는 WU-A4 분) ②값 = `createPreviewRender` 가 ⑴ `업로드·편집` 없으면 403 ⑵ 대상 데이터셋에 `catalog.require_body_access`(값 조회·내려받기와 같은 함수) ⑶ 등록 전 업로드는 소유자 아니면 404 ③근거 = PRD-26 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **비파괴**(계약 파일 변경 0 — 새 상태 403 이 `fe-core.yaml#createPreviewRender.responses` 에 **미선언**이다 `[미해소 — X2 §5 등급 판정 대기]`) ⑤소비자 = `require_body_access` 3자리(`downloadDataset`·`lookupDatasetValue`·`createPreviewRender`) · 측정법 = `grep -rn 'require_body_access' services/core-api/src` ⑥마이그레이션 = **0건** ⑦승인 = Ted · `<일자>` ⑧이번에 세지 않은 축 = FE 가 권한 없는 사용자에게 미리보기 버튼을 숨기는지 `[미측정 — FE 변경 0 · R-A-3 몫]` |
```
