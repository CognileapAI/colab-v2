#!/usr/bin/env bash
# prod 완료 판정 — `deploy_doctor` 14 항목을 **한 번의 실행으로** 돌린다. prod EC2 위에서.
#
# 왜 스크립트인가 — 이 실행에는 **혼자서는 못 맞히는 조건 넷**이 있고, 넷 다 2026-09-06 에
# 하나씩 red 를 내며 드러났다. 재현이 안 되면 판정이 아니므로 그대로 굳혀 둔다.
#
#   ⓵ **컨테이너 안에서 돈다.** EC2 의 파이썬은 3.9 이고 `colab_core` 도 없다. core-api 이미지는
#      3.12 ＋ 모듈이 들어 있다. ⚠ 그런데 **이미지에 `ops/` 는 없다** — 그래서 레포를 마운트한다.
#   ⓶ **레포를 통째로 마운트한다.** `ops/` 만으로는 부족하다 —
#        ⑥⑦ 은 `db/*/alembic.ini` 를, ⑧ 은 `gates/tools/rls_coverage.py` 를 읽는다.
#        `ops/` 만 주면 `NoSectionError: No section: 'alembic'` 로 죽는다.
#      ⟹ `/opt/colab-repo` 를 최신으로 두는 것이 판정의 전제다. **낡으면 ⑥ 이 거짓 red 를 낸다**
#        (dev 에서 실제로 겪었다 — 원인이 DB 인 줄 알고 한참 뒤졌다).
#   ⓷ **`/etc/colab` 을 디렉터리째 마운트하지 않는다.** 그 디렉터리는 `700 root` 라
#      uid 10001(컨테이너 유저)이 **지나갈 수 없다** → ④⑤ 가 `PermissionError` 로 죽는다.
#      compose 가 파일을 개별 마운트하는 이유가 같다. 여기서도 **파일 단위**로 건넨다.
#   ⓸ **운영자 키로 돈다. IMDS 로 돌면 안 된다.** 항목 ①의 이름이 「**운영자** 자격증명」이다.
#      prod 앱 역할은 `DiagnosticsDevOnly` 를 **일부러 뺐으므로**(`〈343〉`) IMDS 로 돌면
#      ③ 웹 버킷이 `HeadObject 403` 을 낸다 — 권한 설계가 옳은데 판정이 red 가 되는 자리다.
#      ⚠ env 파일은 `export ` 접두사를 **떼고** 만든다. `--env-file` 은 그걸 못 읽고,
#        조용히 빈 파일이 되어 **IMDS 로 떨어진다**(그 사고를 그대로 겪었다).
#
# 준비 (판정 직전마다):
#   rsync -az --delete -e "ssh -i <키>" \
#     --include='db/***' --include='gates/***' --include='contracts/***' \
#     --include='services/' --include='services/core-api/' --include='services/core-api/ops/***' \
#     --exclude='*/.venv/*' --exclude='*/node_modules/*' --exclude='__pycache__' --exclude='*' \
#     ./ ec2-user@<EIP>:/opt/colab-repo/
#   sed -E 's/^export //' ~/.config/colab-platform/prod.env | grep -E '^AWS_(ACCESS|SECRET)' \
#     | ssh -i <키> ec2-user@<EIP> 'sudo sh -c "umask 077; mkdir -p /root/colab-boot; cat > /root/colab-boot/ops.env"'
#
# 사용:  ssh -i <키> ec2-user@<EIP> 'sudo bash /opt/colab-v2/deploy-doctor.sh'
#
# ⛔ **끝나면 `/root/colab-boot/ops.env` 를 지운다.** 운영자 키를 서버에 상시로 두지 않는다 —
#    `CLAUDE.md` 배포 절 2번이 금지하는 「EC2 에 AWS 키」와 같은 모양이 된다.
# ⛔ **부분 실행 둘을 합쳐 green 이라 하지 않는다** — `─ 0` 이 나온 한 번의 결과만 근거다.
set -uo pipefail
TAG=$(sed -n 's/^COLAB_IMAGE_TAG=//p' /opt/colab-v2/prod.env | tail -1)
# ⚠ 레포를 **통째로** 마운트한다 — ⑥⑦ 은 db/*/alembic.ini 를, ⑧ 은 gates/tools/rls_coverage.py 를 읽는다.
# ⚠ /etc/colab 은 700 root 라 디렉터리째 마운트하면 uid 10001 이 못 지난다 → 파일 단위로.
# ⚠ 자격은 **운영자 키**다. IMDS(앱 역할)로 돌면 ③ 웹 버킷이 403 이다 — prod 앱 역할은 진단 권한을 일부러 뺐다.
docker run --rm --network host --env-file /root/colab-boot/ops.env \
  -v /opt/colab-repo:/repo:ro \
  -v /etc/colab/platform-owner-db.url:/secrets/platform-owner-db.url:ro \
  -v /etc/colab/ai-owner-db.url:/secrets/ai-owner-db.url:ro \
  "colab-v2/core-api:$TAG" \
  python /repo/services/core-api/ops/deploy_doctor.py --env prod \
    --endpoint https://d1aje00ns2hjsl.cloudfront.net \
    --app-base http://127.0.0.1:8000 --worker-base http://127.0.0.1:8001 \
    --viz-base http://127.0.0.1:8100 --ai-base http://127.0.0.1:8200 \
    --db-url-file /secrets/platform-owner-db.url \
    --ai-db-url-file /secrets/ai-owner-db.url \
    --bucket colab-platform-data-prod --web-bucket colab-platform-web-prod
