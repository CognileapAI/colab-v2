# 제품 브라우저 E2E 실측

첫 검증은 `.codex/worktrees/product-finish`, base `ccf76ec`, 브랜치 `lane/product-finish`.
이후 루트에 통합하고 같은 전체 E2E를 렌더 포함 재실행해 PASS, DB 잔존0을 확인했다.
도구는 WSL agent-browser 0.27.0. 실제 core-api, 실제 pipeline-worker, 새 일회용 Postgres를 사용했다.
기존 staging 및 기존 design 브라우저 세션은 변경하지 않았다.

## 통과한 경로

- 빈 로그인 제출 비활성, 잘못된 비밀번호 거절, 올바른 로그인, reload 후 세션 유지, 로그아웃.
- 같은 임시 디렉터리에서 생성한 GeoTIFF 360,666바이트 업로드.
- 워커 로그에서 GeoTIFF 검출, EPSG:4326, 300x300, COG 생성, upload.ready 확인.
- 설명 미입력 등록 거절 후 설명 작성, 등록, 상세 reload 후 고유 이름·설명·CRS·격자·파일명 유지 확인.
- 앱·브라우저 회수 후 wrapper exit 0. 바로 이어 조회한 gatepg 컨테이너 0.

## 재실행

WSL에서 원래 `30 CoLAB-v2`를 cwd로 사용한다. 격리 사본에서도 실제 소스가 같으면 의존성을 재사용할 수 있다.

```bash
E2E_PYTHON="/mnt/f/00_Project/00 CoLAB/30 CoLAB-v2/services/core-api/.venv/bin/python" \
E2E_FRONTEND_ROOT="/mnt/f/00_Project/00 CoLAB/30 CoLAB-v2/frontend" \
bash scripts/e2e-login.sh --upload \
  --pipeline-python "/mnt/f/00_Project/00 CoLAB/30 CoLAB-v2/services/pipeline-worker/.venv/bin/python"
```

`--inspect-upload`는 조사 모드로 PASS를 출력하지 않는다.
위 명령에 `--viz-python "/mnt/f/00_Project/00 CoLAB/30 CoLAB-v2/services/viz-render/.venv/bin/python"`을 추가한 실행도 통과했다.
실제 렌더 API와 생성 PNG를 사용하며, 격리 서버의 `/previews` 정적 제공은 배포 웹서버 역할을 대신한다.
등록 후와 상세 reload 후 이미지의 complete 및 naturalWidth > 0을 검사했고, 스크린샷에서 실제 색상 지도를 확인했다.
증거 이미지: `.codex/artifacts/product-e2e-preview.png`.
빈 파일 사전 거절은 fixture 입력 검사이며 빈 파일을 UI에 넣은 음성 E2E가 아니다.
실제 S3, 지도 수치 정확도·상호작용 전부, 원격 CI, dev 배포는 위 통과 범위에 포함하지 않는다.

## 검증 과정에서 고친 시험 기반

- 실행마다 새 계정 비밀번호와 세션 secret 사용, credential hash 파일0600, 비밀번호는 CLI argv 대신 stdin.
- 응답 marker로 실제 backend 및 frontend proxy의 대상 확인.
- 브라우저 close 실패는 최종 실패. SIGTERM을 생성한 Python child로 전달해 정리.
- `_pg.sh` slot 획득의 no-command exec가 stderr를 영구 숨기던 문제를 실패 재현 후 수정.
- 없는 파일도 브라우저 업로드 명령이 성공으로 응답할 수 있어 실파일 존재·크기 검사 추가.
- agent-browser 0.27.0에서 `wait --state hidden`이 전역 state 옵션으로 해석되어 실패했다. DOM 조건 `wait --fn`으로 확인한다.
