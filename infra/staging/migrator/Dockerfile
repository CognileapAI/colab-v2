# 마이그레이션 러너 — 두 체인(db/platform · db/ai)을 **각각** 올린다.
#
# 왜 별도 이미지인가
#   · core-api 이미지에 alembic 을 넣으면 앱 컨테이너가 DDL 능력을 갖게 된다.
#     앱 롤은 CREATE 를 회수당했지만(ops/app-role.sql), 도구까지 같이 두면 그 의도가 흐려진다.
#   · db/ai 체인은 core-api 의 것이 아니다. 러너를 앱 이미지에 묶으면 배포 단위 경계가 어긋난다.
#
# 체인 분리는 이미지가 아니라 **실행 단위**로 지킨다 — 한 번에 한 체인만, 각자의 alembic.ini 로.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
RUN pip install "alembic==1.16.5" "SQLAlchemy==2.0.44" "psycopg[binary]==3.2.12"
WORKDIR /chain
ENTRYPOINT ["alembic"]
CMD ["upgrade", "head"]
