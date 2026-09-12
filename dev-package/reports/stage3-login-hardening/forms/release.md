# Stage 3 비업로드 폼 작업 보호 레인

## 결과

`useWorkProtection`가 `SessionProvider`의 `/me` 확인 계정 ID로 합의된 `registerWork` 인터페이스를 호출한다. 계정 미확인 상태에서는 등록하지 않으며, 계정 컨텍스트가 바뀌면 effect가 다시 계산된다. 각 화면은 초기값과 실제 상태가 다를 때만 dirty, 요청 중에만 inFlight를 등록하고 저장·취소·폐기에 React 상태를 정리한다.

| 표면 | 연결 위치 | dirty / inFlight | 명시 폐기 |
|---|---|---|---|
| 프로젝트 | `ProjectFormModal.tsx` | 6개 입력의 초기값 비교 / `busy` | 모달 닫기 |
| 데이터셋 | `useDatasetEdit.ts` (`DatasetEditForm` 상태 정본) | `toDraft(detail)` 비교 / `saving` | 편집 draft·확인·오류 초기화 |
| 연구실 | `LabInfoPanel.tsx` | `draftOf(lab)` 비교 / `saving` | 모달 draft·오류 초기화 |
| 권한 | `MemberPermissionGrid.tsx` | `diffOf` 1건 이상 / `saving` | 서버값으로 draft 복구, 확인 닫기 |
| 계보 관계 | `LineageSection.tsx` | 방식 변경 또는 제거 확인 / `busy` | 방식·확인·오류 초기화 |
| 계보 추가 | `LineageFixModal.tsx` | 후보 선택 또는 방식 입력 / `saving` | 모달 닫기 |
| 접근 거절 | `TodoInbox.tsx` | 사유 입력 / `busy` | 거절 UI·사유·오류 초기화 |
| 승인 취소 | `VerificationAction.tsx` | 취소 사유 입력 / `busy` | 메뉴·모달·사유·오류 초기화 |

`DatasetEditForm.tsx`는 상태를 소유하지 않고 `useDatasetEdit`가 draft·saving·취소·저장을 단독 소유하므로 훅 한 곳에서 보호했다. 초기값으로 되돌리면 dirty가 false가 되며, 성공 저장은 draft 제거 또는 모달 unmount로 등록을 해제한다.

## TDD와 검증

- RED: 프로젝트 이름 변경 뒤 `canTransition()` 기대값 `false`, 실제값 `true`로 1건 실패.
- GREEN: `form-work-protection.test.tsx`에서 초기 clean, 변경 dirty, `discardAccountWork` 뒤 실제 `onClose`와 clean을 확인.
- 관련 시험: `form-work-protection`, `fe-small-rc8`, `lineage-continuation`, `toast-copy-20260906` 4파일 38건 통과.
- 전체 `frontend-test`: 96파일 1216건 통과, 4파일 4건 판정 실패. 실행 중 source hash가 바뀌었고 다른 레인의 `auth.test.tsx` 1건과 업로드 시험 timeout을 포함해 이 레인의 완료 근거로 사용하지 않는다. 부모 통합 사본에서 source 동결 후 재검증 대상이다.
- typecheck: 범위 밖 `frontend/src/auth/sessionCoordinator.ts:39`의 `() => void`/`() => undefined` 불일치 1건으로 실패. 이 레인 소유 파일은 수정하지 않았다.

## 파일 SHA-256

```
2aa382439f2343e8af08953598af1151bfae62c92799d7ccbeb48cd435cbf92f  frontend/src/auth/useWorkProtection.ts
81075722cf3109d84708d61bd7e7ae72872bf8537963a8e8218f508738ab540f  frontend/src/components/project/ProjectFormModal.tsx
065a0282a5e645d3ebff1449e4ef0874e5578677aada14b529d62f7e0008528a  frontend/src/components/detail/useDatasetEdit.ts
9ca5b314bf4663a84eaa3e163981558e861a3a0a0de0f40a35fed3532ea1bf89  frontend/src/components/lab/LabInfoPanel.tsx
4639edfd114f8c6fb7554ece8e501d107f21f4039d745518f95a63aa0b11adad  frontend/src/components/members/MemberPermissionGrid.tsx
c075ab6fa4e00ae2a12f91c815fd7236e4ba97961373bd204af3f7450b4ff54c  frontend/src/components/lineage/LineageSection.tsx
c59e8f0140acd0b7bcbc3cebac2288ef5bb87f99a9bc86822f0f21a464561a44  frontend/src/components/lineage/LineageFixModal.tsx
50a68c33bbfd54e9307b35f354bd403bcbf89d9b415ed76c1ab2d24d5cbe3c04  frontend/src/components/dashboard/TodoInbox.tsx
2553e2facde9652cfc6d47ab95beb4f5d0ec7ea998f6700fa326f8f322f8d22c  frontend/src/components/approval/VerificationAction.tsx
c92431f84db906f451430789fa870f4e57a4ab735ac9940be68963a237296910  frontend/test/form-work-protection.test.tsx
```

## Intent 대조

- 미달: 업로드·파일·대표 그림은 별도 레인 소유이며 이 레인 범위 밖이다. 전체 탭 전환·만료 overlay·로그아웃 조정은 상위 coordinator 레인 통합이 필요하다.
- 초과: 0건.
