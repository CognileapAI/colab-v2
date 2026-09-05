# WU-A1 · 권한 스위치 기본값 (PRD-25) — 레인 `p3-perm-default`

- 라운드 파일 = `dev-package/prd/rounds/R-A-2-server.md` §2 WU-A1 · §5
- 기점 = `origin/integration/r-a` (`0cb7587`) · 마이그레이션 **0건** · 계약 파일 변경 **0건**

## 1. 무엇을 고쳤나

| 자리 | 무엇 |
|---|---|
| `services/core-api/src/colab_core/domains/d2_access.py:28-34` | `DEFAULT_SWITCHES` 상수 신설 — 업로드·편집·프로젝트 생성 `True` / 승인 위임·연구실 설정 `False` |
| `…/d2_access.py:36-43` | `_resolve(stored)` — 저장 행에 기본값을 덮어씌운다. **행이 있으면 그 값이 이긴다** |
| `…/d2_access.py:109` | `permissions_of` 가 `_resolve` 를 쓴다 (종전 `stored.get(s, False)`) |
| `…/d2_access.py:172` | `member_permissions` 도 **같은 함수**를 쓴다 — 단건·격자 두 자리가 갈리지 않는다 |
| `services/core-api/tests/conftest.py:_RESTORE` | 스위치 되돌림을 `UPDATE` → `INSERT … ON CONFLICT` 로. 지운 행은 UPDATE 로 안 돌아온다 |
| `services/core-api/tests/test_permission_defaults.py` | 신규 회귀 시험 **7건** |
- **DB 변경 0** — 기본값 행을 만들지 않았다. 「행 없음 = 기본값」이라는 현행 의미를 유지해 마이그레이션이 0 이다.
- **계약·FE 는 대조만** — `contracts/schemas/common.json:52-57` `PermissionSwitchSet.default` 가 이미 정본 값이고 `frontend/src/components/members/permissions.ts:11-13` 은 그 위치를 가리키는 **주석뿐**이다. **두 파일 무수정.** 서버 상수 ↔ 계약 default 일치는 `test_the_default_constant_matches_the_contract` 가 잰다.

## 2. RED 선실측 → GREEN

```
(RED)  5 failed, 634 passed, 6 deselected in 94.22s
       실패 5 = 기본값 미적용 4 + `DEFAULT_SWITCHES` 부재 1 · 예: `업로드·편집 스위치가 꺼져 있다` / assert 403 == 201
(GREEN) 639 passed, 6 deselected in 87.91s
```
시험 7건 (`tests/test_permission_defaults.py`) — ① 행 없는 `/me` 가 정본 기본값 ② 격자도 같은 판정 ③ 명시 `false` 행은 안 켜진다 ④ 기본 꺼짐 칸의 명시 `true` 는 유지 ⑤ 일부만 저장된 계정 = 행 우선·나머지 기본값 ⑥ 교수 네 칸 전부 `true`(현행 유지) ⑦ 행 없는 연구원의 `POST /uploads` 가 **201**.

## 3. 게이트 (§5 WU-A1 분 — `all` 은 돌리지 않았다)

```
service-tests-core-api — 선택자 «not e2e» · 수집 639 · 실행 639 · skipped 0 · deselected 6 · failed 0 · errors 0 · 87.9초   → green
rls-effect — 본체 음성 · 메타 양성(P-13) · cross-tenant 전수 0행 · 판정 롤 우회 불가             → green
```

## 4. 실측 보고 — `d2_permission_switch` 현재 행 수 (읽기만 · 쓰기 0)

접속처 = `COLAB_AUTOMETA_STAGING_DB_URL`(`colab_platform`, 사설망 컨테이너). AWS staging 이 아니면 아래 값은 그 사본 기준이다.

| 항목 | 값 |
|---|---|
| `d2_permission_switch` 전체 행 수 | **8** |
| 스위치별 | 업로드·편집 `t` 2 · 프로젝트 생성 `t` 2 · 승인 위임 `f` 2 · 연구실 설정 `f` 2 |
| 계정 총수 | 6 (교수 4 · 연구원 2) |
| 행이 하나도 없는 계정 | **4 — 전원 교수** |
| **이 변경으로 실제 켜지는 (계정,스위치) 쌍** | **0** |

연구원 2명은 이미 네 행을 다 갖고 있어 저장값이 그대로 이긴다. 행 없는 4명은 교수라 P-5 판정으로 원래 전부 켜져 있었다. **배포로 바뀌는 계정 권한이 이 DB 기준 0건이다.**

측정 명령 (다른 DB 에 다시 재려면 그대로 쓴다):
```
psql "$URL" -Atc "SELECT switch, enabled, count(*) FROM d2_permission_switch GROUP BY 1,2 ORDER BY 1,2"
psql "$URL" -Atc "SELECT count(*)*2 FROM d1_account a JOIN d2_member_role r ON r.account_id=a.id
   WHERE r.role='연구원' AND NOT EXISTS (SELECT 1 FROM d2_permission_switch s WHERE s.account_id=a.id)"
```
⚠ `COLAB_APPLIED_DB_URL_PLATFORM` 은 계정 0·행 0 인 스키마 대조용 빈 DB 라 근거가 아니다. **AWS staging 실측은 `[미측정 — 접근 경로 없음]`** — 위 두 줄을 그 URL 로 돌리면 잰다.

## 5. PLAN-SoT §9 행 초안 (⚠ 초안 · 병합 직전 `〈N〉` 재실측 · 이 세션은 PLAN-SoT 를 고치지 않았다)

```
| 〈N〉 | **R-A-2 서버 계층 — 권한 기본값 반전(WU-A1 분)** | **집행 (2026-09-05 · 워크트리 `p3-perm-default` · 병합 `<sha>`).** ①회차 = **해당 없음**(WU-A1 은 계약을 열지 않는다 · 19차는 WU-A4 분) ②값 = `d2_access.DEFAULT_SWITCHES` = 업로드·편집·프로젝트 생성 `true` / 승인 위임·연구실 설정 `false`(서버 상수 한 자리 · DB 기본값 행 없음) ③근거 = PRD-25 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **비파괴**(계약 파일 변경 0 — `common.json#PermissionSwitchSet.default` 가 이미 이 값이었고 코드가 그것을 어기고 있었다) ⑤소비자 = `permissions_of`·`member_permissions` 두 자리 · 측정법 = `grep -rn 'permissions_of\|member_permissions' services/core-api/src` ⑥마이그레이션 = **0건** ⑦승인 = Ted · `<일자>` ⑧이번에 세지 않은 축 = AWS staging 실계정 권한 변동 폭 `[미측정 — 접근 경로 없음]`(사설망 `colab_platform` 사본 기준으로는 **0건** · 쓰기 0) |
```
