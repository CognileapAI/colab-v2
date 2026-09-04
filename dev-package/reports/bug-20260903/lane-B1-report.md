# Lane B-1 — viz-render 미리보기 warp 리샘플 수정 (버그 4·13·14)

- 브랜치: `worktree-agent-a9665558e0d0858c1`
- 워크트리: `.claude/worktrees/agent-a9665558e0d0858c1`
- 커밋: `40844ea`

## Step 0 — OLD 워크트리

`OLD2`(`agent-a47fd28c4dbdf5b96`)는 존재하지 않았다. `OLD1`(`agent-a7259c1f39faf2c0e`)에
`git status --porcelain`/`git log`(worktree 격리로 직접 조회 불가, non-git 파일 조회로 대체)
확인 결과 커밋 0건 · 수정 `preview.py` · 미추적 `tests/test_preview_warp_gaps.py` · `.venv-b1/`
가 있었다. `.venv-b1/`은 제외하고 두 파일만 그대로 복사했다.

## 근본 원인 확인

`preview.py` 를 전체 읽고 recon-B-preview.md §1·§4, 스크린샷(bug04·bug10·bug11)과 대조 —
`warp_to_3857`(옛 버전, `origin/main`)이 `np.add.at` 전방 산란이라 원본이 출력(1024px)보다
성기면 대부분 픽셀이 결측(알파0)으로 남고, 같은 해상도에서도 lat→y 비선형 때문에 전 결측
행이 남는다는 recon 판정을 코드로 재확인했다.

## RED (origin/main 원본, 신규 테스트 6건 전부 실패)

```
FAILED test_원본이_출력보다_성기면_출력이_점_격자가_된다는_결함 - 성긴 원본이 출력을 못 채운다: 0.0195
FAILED test_성긴_원본에서_전_결측_행과_열이_남지_않는다 - 전 결측 행이 남았다
FAILED test_같은_해상도에서도_가로_흰_줄이_남지_않는다 - assert 2 == 0
FAILED test_원본의_결측은_이웃_값으로_메워지지_않는다 - 원본 0.0558 / 출력 0.9816
FAILED test_원본이_출력보다_촘촘하면_여전히_평균이다 - min=0.0 max=10.0 (평균 안 됨)
FAILED test_곡선_격자의_발자국_밖은_채우지_않는다 - 발자국 안쪽 채움 0.094
6 failed, 269 passed (전체 스위트 기준)
```

## 알고리즘 (`warp_to_3857`)

1. 원본 긴 변이 `max_side` 초과면 `block_average`로 먼저 내린다(좌표는 `sample_centers`) —
   「촘촘→평균」 보존.
2. 원본 점을 3857로 변환해 출력 격자에 씨앗으로 놓되, 한 픽셀에 여럿이면 픽셀 중심에
   가장 가까운 것이 이긴다(값 NaN인 셀도 씨앗 자격 — NoData 도 자리를 차지한다).
3. 씨앗 없는 픽셀은 행 스윕 2회(좌우→상하 전파, 완전 벡터화)로 최근접 씨앗을 찾되,
   추정 원본 간격을 넘으면 채우지 않는다(발자국 밖 보존).

## 하베스트 테스트 평가

`test_preview_warp_gaps.py`(OLD1 하베스트)는 요구 (a)~(d)를 이미 전부 커버하고 있어
그대로 채택 — 수정 불필요. (a) 126×128 성긴 원본 채움률≥95% (b) 성긴/동해상도 두 케이스
모두 전 결측 행·열 0 (c) 결측 비율 보존 + 알려진 NaN 블록 중심이 그대로 NaN (d) 2048²
체크보드가 평균(5.0)됨. 곡선(회전) 격자 발자국 보존 테스트도 보너스로 포함.

## GREEN

신규 6건 GREEN. 전체 unit 스위트(`-m "not e2e and not perf"`): **269→275 통과, 실패 0**
(신규 6건 포함, deselected 40건은 e2e/perf).

## 지연 실측

`gates/tools/render-latency.sh`는 `COLAB_REFERENCE_DATA`(실원천 마운트) 필수라 이 워크트리엔
없어 **readiness red**(정상 — 못 돈 것을 통과로 세지 않는 설계)로 확인만 하고 대신 자체 측정:
1024×1024 원본(충청권 bbox)으로 `warp_to_3857` 5회 반복 — **평균 0.378 s · 최대 0.415 s**.
게이트 눈금(`render-latency.toml` p95 10.0 s, 상한 60.0 s) 및 지시된 budget(p95 3.06 s) 모두
여유롭게 충족.

## 촘촘 원본(>1024) 판정

docstring의 「촘촘→평균」 성질은 **그대로 유지된다** — `warp_to_3857` 1단계가
`downsample.steps_for`로 `block_average` 를 먼저 적용하고, `test_원본이_출력보다_촘촘하면_
여전히_평균이다`(2048² 체크보드→5.0)로 실측 확인했다.

## 캐비어트

staging 은 〈307〉 캐시 키 변경 후 재굽기(RC-1) 미실행 상태라, 이 수정 배포 뒤에도 구판
산출물이 보일 수 있다 — 배포 순서에 재굽기를 넣는다.
