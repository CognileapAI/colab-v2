# 업로드 입력 안내·필수 조건 전후 화면

같은 surface.grib 파일, 1440×1000 브라우저, Lv0 기본 상태로 실제 촬영했다. before는 develop 기준 e77374ec, after는 #78/#79 로컬 구현이다. 입력값은 예시를 확인할 수 있도록 비워 두었다. 촬영 후 제품 화면 코드는 변경하지 않았다.

| 화면 | 변경 전 | 변경 후 |
|---|---|---|
| 등록 시작 | [전](images/entry-before.png) | [후](images/entry-after.png) |
| 메타데이터 | [전](images/metadata-before.png) | [후](images/metadata-after.png) |
| 변수 | [전](images/variables-before.png) | [후](images/variables-after.png) |
| 출처 | [전](images/source-before.png) | [후](images/source-after.png) |

신규 등록은 관측 간격의 숫자·단위, Lv0 출처 주소·내려받은 날을 필수로 받는다. 기획의 입력 예시와 안내를 반영하고 보기 전용 선택을 제거했다. 기존 데이터의 빈 값·수정 API·입력칸 폭은 유지한다.

검증 절차는 `scripts/issue-78-79-journey.py`다. 실제 업로드·등록 복원·누락 안내·등록·새로고침 값 보존을 검사한다. 최신 검증 수치와 게시 후보 SHA는 PR 본문 및 task runtime에 기록한다.
