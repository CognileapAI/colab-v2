from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.e2e_preview_static import PreviewStaticFiles


def test_preview_static_files_serves_image_but_hides_render_state(tmp_path):
    (tmp_path / "image.png").write_bytes(b"png")
    (tmp_path / ".render-journal.json").write_text("secret")
    (tmp_path / ".render-journal.tmp").write_text("secret")
    (tmp_path / ".render-journal.lock").write_text("secret")
    state = tmp_path / ".render-state"
    state.mkdir()
    (state / "render.npy").write_bytes(b"private array")
    app = FastAPI()
    app.mount("/previews", PreviewStaticFiles(directory=tmp_path))
    client = TestClient(app)

    assert client.get("/previews/image.png").content == b"png"
    for path in (".render-journal.json", ".render-journal.tmp",
                 ".render-journal.lock", ".render-state/render.npy"):
        assert client.get(f"/previews/{path}").status_code == 404


def test_staging_nginx_denies_render_state_before_preview_alias():
    config = (Path(__file__).resolve().parents[2] / "infra/staging/nginx.i2.conf").read_text()

    deny = "location ~ ^/previews/(?:\\.render-journal[^/]*|\\.render-state(?:/|$))"
    assert deny in config
    assert config.index(deny) < config.index("location /previews/")
