# 이슈 화면 개선 검증 이미지

- 대상 제품 커밋: `d032887514d1d0637e1998df2217f8631625843d` (로컬 작업 버전). 운영 배포를 뜻하지 않습니다.
- 이미지 검토·추가 촬영: 2026-09-16 KST. 추가 촬영 약 23:38–23:41 KST, agent-browser 전용 세션 `issue-comment-evidence`, 로컬 Vite `http://127.0.0.1:4187`.
- 모든 이미지를 직접 열어 확인했습니다. 보이는 연구실·사용자·과제는 로컬 fixture 또는 격리 E2E 데이터이며 자격정보는 포함하지 않습니다.
- 이전 작업에서 남긴 원본 PNG는 그대로 복사했습니다. 촬영 당시 정확한 초 단위 시각과 수정 전 코드 SHA는 기존 이미지 자체만으로 확인할 수 없습니다. 수정 전 화면을 재구성하지 않았습니다.

## 이슈별 사용 범위

| 이슈 | 수정 전 | 수정 후 / 현재 | 조건과 한계 |
| --- | --- | --- | --- |
| #51 | detail-before.png | detail-after.png | 기존 로컬 audit fixture, 둘 다 1280×577. 같은 스크롤 위치에서 기존 탭이 가려졌다가 상단 메뉴 아래에 노출됨. 원본 촬영 재실행 아님. |
| #68 | project-description-before.png | project-description-after.png | 같은 audit-design project-dialog fixture. 전 1280×577, 후 1280×900으로 높이가 다름. 설명 라벨의 최대 500자 안내 비교. |
| #70 | 미확보 | project-table-long-title-after.png, project-table-narrow-after.png | 기존 로컬 audit fixture. 긴 제목을 넣은 1280×577 화면과 기본 제목인 768×900 화면은 데이터 조건이 다름. 후자는 작은 화면 배치의 보조 근거이며 긴 제목 검증으로 취급하지 않음. |
| #71 | 미확보 | project-dates-before-save.png, project-dates-after-reload.png | 이전 격리 E2E 실저장 증거. before-save는 수정 전 코드가 아니라 수정 후 저장 직전 화면. 입력 2026-09-16/2026-10-31, 저장 후 새로고침 화면에 2026.09.16~10.31. 둘 다 1280×900. |
| #72 | 해당 없음 (변경하지 않음) | visibility-current.png | 추가 촬영 audit-upload 모의 화면. 공개범위 UI 존재만 증명. 저장·접근 제어는 별도 core-api 테스트 근거를 봐야 하며 이 이미지는 ACL 증거가 아님. |
| #75 | 미확보 | classification-after.png | 추가 촬영 audit-upload, example.txt 선택→다음. 분류·유형에 실제 값 선택 상태. 브라우저 snapshot에서 분류 5종/유형 6종이며 ‘아직 고르지 않음’ 옵션 없음 확인. 이미지는 펼쳐진 전체 옵션 목록을 보여주지 않음. |
| #81 | 미확보 | project-select-after.png | 추가 촬영 audit-upload. 메타데이터 설명·기간·변수/단위를 채우고 대표 변수 선택→다음→연관 프로젝트로 스크롤. fixture의 긴 제목이 말줄임되며 +추가 버튼이 보임. 데이터셋 등록은 실행하지 않음. |

## 환경 구분과 제한

- audit-design/audit-upload는 로컬 모의 응답 화면입니다. 실제 파일 저장이나 배포된 서버의 검증이 아닙니다. 업로드 왼쪽 미리보기 오류는 fixture의 의도된 실패 응답이며 이번 UI 변경의 성공 근거로 쓰지 않습니다.
- 새로 촬영한 네 파일(classification-after, visibility-current, project-select-after, project-description-after)은 모두 1280×900입니다.
- #71 E2E는 기존 `/tmp/issue-71-e2e/journey.json`의 input과 stored 값이 같은 것을 읽어 확인한 재사용 증거입니다. 이번 이미지 정리 작업에서 저장 여정을 다시 실행하지 않았습니다. E2E의 서버 주소·테스트 실행 로그는 부모 작업 기록을 참조합니다.
- 기존 project-description-before는 기간 입력이 화면 밖이므로 #71의 수정 전 달력 근거로 사용하지 않습니다. 기존 project-select-after 원본은 선택기가 화면 밖이므로 게시용에서 제외하고 이번 촬영본을 사용했습니다.
- 서버와 전용 브라우저는 이미지 확보 후 정리합니다. 제품 코드는 변경하지 않습니다.

## 파일 무결성

| 파일 | 크기(px) | bytes | SHA-256 |
| --- | --- | ---: | --- |
| `detail-before.png` | 1280×577 | 76027 | `afb46a77a22f7a8c47f13e13f7fbc79186b51deafa013b9b85469af709b442f1` |
| `detail-after.png` | 1280×577 | 73572 | `66adf3286086cd829474c746cb0199509034d5eee32acb29f8c8de86b1cc13db` |
| `project-description-before.png` | 1280×577 | 87019 | `a111ac6cf18b435fedc528644ce6101a90284760957343b665c3b6790300e3e4` |
| `project-table-long-title-after.png` | 1280×577 | 69030 | `3fcb62d130d76e68b2af7d3fc96141de8f33d3534b39da5182b287f284b38f45` |
| `project-table-narrow-after.png` | 768×900 | 66950 | `4ca56977f6be33bdd7e68f0191cb29641910653b87cb5790333c46eeddda3ac3` |
| `project-dates-before-save.png` | 1280×900 | 81790 | `e05a5c5735eaacd1c382de16e40dbec69a4cfdb6c9ddf73310a740e4772c1b82` |
| `project-dates-after-reload.png` | 1280×900 | 68918 | `09df60a4e2ad87a59fe4b135450fe162b9fa51c18fe5bf9c27dbf1983319c506` |
| `classification-after.png` | 1280×900 | 98469 | `a90b879b2cf4f8712694131cd21b2ee4c002e0147588f614a97e4eff7a83dddd` |
| `visibility-current.png` | 1280×900 | 80132 | `7a804006f9bf429d47ab6d602a699f51a1a1ece4f86830cc08471e8802422ed8` |
| `project-select-after.png` | 1280×900 | 91110 | `e8c53bd8ea8a72503c7e7f82a5fddaecd1284a1b13fdc8ec26e9f30b2c1ace2f` |
| `project-description-after.png` | 1280×900 | 106747 | `8d7d6726b0586ca0947f9888e2d6e384d2ff331a9c1fa162938572f60f5f058d` |
