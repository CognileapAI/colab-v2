# WU-C6 — EC2 잔존물 삭제 ＋ 회차 마감 뒤 Ted 판정 3건 등재

- 기점 = `origin/main` `c51639c4` · 브랜치 `lane/wu-c6-ec2-cleanup` · 2026-09-14.
- Ted 판정 3건(2026-09-14 마감 뒤) = ⓐ PI 비밀번호 재설정 완료(계정 관리 화면 · 값 미기록 · 운영자 초기 비밀번호 파일은 첫 로그인 변경 뒤 실행 기계에서 삭제) ⓑ 다음 회차 `GT-1`(`DR-4b` 는 그 뒤) ⓒ EC2 잔존물 「예 · 지운다」.
- EC2 정리(dev EC2 한정 · staging·prod·`_ops/`·S3·컨테이너·docker 이미지 무접촉) —
  - 사전 점검 = `compose.yml`·`dev.env` 의 `images/` 참조 0 · 실행 태그 `d5cd6ca971df`·직전 태그 `b955bece7384` 의 tar 각 2건은 목록에서 제외(guard grep 0).
  - 삭제 = 고정 목록 파일 26행(md5 `3733bc09…`)에서 `xargs -d '\n' rm -f` · glob 미사용 · 1,531,330,806 B(≈1.43 GiB) — `dev.env.bak-*` 7 · `images/colab-ops-source-*.tar.gz` 10 · `images/colab-v2-dev-*.tar` 5 · `images/repo-42e44c8990a3.tar.gz` 1 · `images/stage12-doctor-d56428d6945d.tar.gz` 1 · `/tmp/repo-rc.tgz`·`/tmp/repo.tgz` 2.
  - `df -h /` = before 14G 사용 · 6.1G 여유(70%) → after 13G 사용 · 7.5G 여유(63%).
  - 사후 = `dev.env.bak-*` 0 · `images/*.tar*` 4(유지 태그 2×2) · `/tmp` 대상 0 · docker `colab-v2` 이미지 20 무변 · 앱 4 `dev-d5cd6ca971df` Up (healthy).
  - 잔여(글롭 밖 · 다음 판정) = `images/*.manifest` 고아 10건 · `images/repo-42cffb328b1e.tgz` 31 MB · 로컬 web-backup 디렉터리.
- 편집 파일 4 = `dev-package/03-HANDOFF.md`(상단 마감 문단 다음 WU → `GT-1` · §4 블로커 75 ✅ 해소 · 2줄) · `dev-package/work-items.yaml`(`OPS-PI-PW` done · `LF-13`·`GT-1` note) · `dev-package/prd/rounds/R-DATA-CANON.md`(§13-8) · `dev-package/PLAN-SoT.md`(〈398〉-㉿′ · 새 번호 0).
- 게이트(이 트리 · 각 1회) = `work-item-consistency` green(불일치 0) · `planning-freshness` green(임베드 15 · 적용 상태 4) · `gate-summary.json` 은 gitignored(경로만). `git diff --check` 0건 · 추가 줄에 절대경로 0건 · 비밀값 0건.
