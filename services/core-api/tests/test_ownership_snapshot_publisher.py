from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from colab_core.app import ownership_snapshot_publisher as pub

D3 = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
D5 = "01BX5ZZKBKACTAV9WEVGEMMVRZ"

class Rows:
    def __init__(self, values): self.values = values
    def scalars(self): return self
    def mappings(self): return self
    def all(self): return self.values
    def __iter__(self): return iter(self.values)
    def one(self): return self.values[0]
    def scalar_one(self): return self.values[0]

class Session:
    def __init__(self): self.sql=[]
    def execute(self, statement):
        text=str(statement); self.sql.append(text)
        if "clock_timestamp" in text: return Rows([datetime.now(timezone.utc)])
        if "rolsuper" in text: return Rows([("colab_backup", False, True, True)])
        if "FROM d3_dataset" in text: return Rows([])
        if "count(*)" in text: return Rows([1])
        if "FROM d3_file" in text: return Rows([D3])
        if "FROM d5_upload_file" in text: return Rows([D5])
        return Rows([])


def test_publisher는_권한을_실측하고_한_snapshot을_atomic_0440으로_쓴다(tmp_path):
    session=Session()
    snapshot=pub.collect(session)
    assert snapshot["scope"] == "all-tenants"
    assert snapshot["counts"] == {"d3_file": 1, "d5_upload_file": 1}
    assert any("rolbypassrls" in sql for sql in session.sql)
    assert next(i for i,q in enumerate(session.sql) if "clock_timestamp" in q) < next(i for i,q in enumerate(session.sql) if "rolsuper" in q)
    target=tmp_path/"ledger.json"
    pub.atomic_write(target, snapshot)
    assert json.loads(target.read_text())["content_sha256"]
    assert os.stat(target).st_mode & 0o777 == 0o440
    assert not list(tmp_path.glob("*.tmp"))


def test_publisher는_count와_dump가_다르면_발행하지_않는다():
    class Bad(Session):
        def execute(self, statement):
            text=str(statement)
            if "count(*)" in text: return Rows([99])
            return super().execute(statement)
    import pytest
    with pytest.raises(RuntimeError, match="count"):
        pub.collect(Bad())


def test_actual_db는_두_lab전수_readonly이고_app_role은_거절한다(app_db_url):
    import pytest
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import DBAPIError
    from sqlalchemy.orm import Session
    owner_url=make_url(app_db_url).set(username="postgres",password=None)
    with Session(create_engine(owner_url)) as session, session.begin():
        snapshot=pub.collect(session)
        assert session.execute(text("SHOW transaction_read_only")).scalar_one() == "on"
        assert session.execute(text("SELECT count(DISTINCT lab_id) FROM d3_file")).scalar_one() >= 2
        assert snapshot["counts"]["d3_file"] == len(snapshot["d3_file_ids"])
        assert snapshot["counts"]["d5_upload_file"] == len(snapshot["d5_upload_file_ids"])
        with pytest.raises(DBAPIError):
            session.execute(text("UPDATE d1_account SET name=name"))
    with Session(create_engine(app_db_url)) as session, session.begin():
        with pytest.raises(RuntimeError, match="전수 snapshot 권한"):
            pub.collect(session)
