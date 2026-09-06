# 마이그레이션 러너(dev) — staging `../../staging/migrator/Dockerfile` + **체인을 이미지 안에 COPY** 한다.
#
# staging 은 레포를 볼륨으로 마운트하지만 dev EC2 에는 레포가 없다 — 배포되는 체인은 커밋의 산출이어야 하므로
# 이미지에 넣는다. 빌드 컨텍스트 = 레포 루트(`db/` 를 COPY 하려면) · `infra/dev/build.sh` 가 그렇게 부른다.
# 앱 이미지에 alembic 을 넣지 않는 이유는 staging 것과 같다(앱 컨테이너에 DDL 능력을 두지 않는다).
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
RUN pip install "alembic==1.16.5" "SQLAlchemy==2.0.44" "psycopg[binary]==3.2.12"
COPY db/platform /chain/platform
COPY db/ai /chain/ai
WORKDIR /chain
ENTRYPOINT ["alembic"]
CMD ["upgrade", "head"]
