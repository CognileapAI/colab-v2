# p3-thumb-nudge — WU-A10 썸네일 넛지 (PRD-20 · R-A-3 §2)

- 레인 `p3-thumb-nudge` · 기점 `origin/integration/r-a` = `78a9a67`(WU-A12 방어선 포함 · 병합 완료)
- 범위 = **프론트 전용**. 계약 0 · 서버 0 · DB 0 · 마이그레이션 0 · staging 접촉 0.

## 1. 무엇을 고쳤나

| 파일 | 줄 | 내용 |
|---|---|---|
| `frontend/src/components/upload/PreviewPanel.tsx` | 80-81 | `pickedThumb` 상태 · `thumbInput` ref 신설 |
| 〃 | 208-224 | `autoThumb`(= 자동 미리보기 축소본) · `thumbSrc` · `pickThumb()` — 고른 그림은 `URL.createObjectURL` 로 화면에서만 바뀌고 앞 주소는 `revokeObjectURL` 로 놓아준다 |
| 〃 | 231-265 | `thumbrow` 블록 — 썸네일 버튼(`up-thumb-pick`) ＋ 넛지 한 줄 `눌러서 다른 그림으로 바꿀 수 있어요`(`up-thumb-nudge`) ＋ 숨은 `<input type="file" accept="image/*">`(`up-thumb-input`). 클릭이 입력칸의 `click()` 을 부른다 |
| `frontend/src/components/upload/upload.css` | 246-262 | `.thumbrow` 이하 — 64px 칸 · 안내 2줄 · `.th-in { display:none }` |
| `frontend/test/thumb-nudge-20260905.test.tsx` | 신규 79행 | 수용 기준 시험 3건 |

**저장 경로를 만들지 않았다.** `d3_dataset.representative_file_id` 를 읽지도 쓰지도 않는다 —
그 열은 조각 지정용이고 업로드 이미지 저장은 별건 `WU-C2` 다. 서버로 나가는 요청 **0건**.

## 2. RED 선실측 → GREEN

```
npx vitest run test/thumb-nudge-20260905.test.tsx   # 구현 전
  Test Files  1 failed (1)      Tests  3 failed (3)   ← up-thumb-* 없음
npx vitest run test/thumb-nudge-20260905.test.tsx   # 구현 후
  Test Files  1 passed (1)      Tests  3 passed (3)
```

시험 3건 = ⑴ ② 단계 진입 시 썸네일 자리 ＋ 교체 안내가 함께 읽힌다 ⑵ 썸네일 클릭이
파일 선택기의 `click()` 을 **1회** 부른다(`accept="image/*"` 확인 포함) ⑶ 고른 그림이 화면에서만
바뀐다(`createObjectURL` 1회 · 서버 호출 0).

## 3. 게이트

| 게이트 | 판정 | 계수 |
|---|---|---|
| `frontend-typecheck` | **green** | `tsc --noEmit`(include=src·test) 오류 **0건** |
| `frontend-test` | **green** | vitest run(jsdom) — 시험 파일 **44 passed** · 시험 **652 passed** · 실패 **0** |

`frontend/test/detail-edit.test.tsx` 는 이번 실행에서 흔들리지 않았다(재시행 불요).
회귀 방어선 `rev1-keep-regression.test.tsx` · `upload.test.tsx` · `project-panels-20260905.test.tsx`
전부 위 652건 안에서 green.

## 4. PLAN-SoT §9 초안 — 병합 직전에 `〈N〉` 을 다시 잰다

`git fetch origin main && bash dev-package/prd/tools/max-decision.sh` 의 최대값 ＋ 1.
착수 시점 참고값 = 〈326〉. **이 세션은 `PLAN-SoT.md` 를 고치지 않았다.**

```
| 〈N〉 | **R-A-3 FE 계층 — 상세 수정 진입점 신설 · 구역 메뉴 sticky(미결-9 ⓑ 최종형) · 종료 조건 개정** | **집행 (2026-09-05 · 워크트리 `p3-thumb-nudge` · 병합 `<sha>` · 계약 개정 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음 ③근거 = PRD-14·20·22·23·24 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **해당 없음** · `contract-breaking` 출력 = `<축자 · 변경 0 확인>` ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요(㉮ 밖 · 계약 미접촉) ⑧이번에 세지 않은 축 = 대표 그림 저장 경로(WU-C2 별건) `[미측정]` |
```

## 5. 남은 것 · 미상

- 대표 그림의 **저장**은 여전히 없다 — `WU-C2` 가 열어야 한다. 지금 고른 그림은 새로고침에 사라진다.
- `contract-breaking` 축자 출력은 이 레인이 재지 않았다 — 병합 담당이 채운다. `[미상]`
