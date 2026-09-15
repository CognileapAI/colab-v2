from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.e2e_preview_static import PreviewStaticFiles


class PreviewStaticFilesTests(unittest.TestCase):
    def test_preview_static_files_serves_image_but_hides_render_state(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "image.png").write_bytes(b"png")
            (root / ".render-journal.json").write_text("secret")
            (root / ".render-journal.tmp").write_text("secret")
            (root / ".render-journal.lock").write_text("secret")
            state = root / ".render-state"
            state.mkdir()
            (state / "render.npy").write_bytes(b"private array")
            app = FastAPI()
            app.mount("/previews", PreviewStaticFiles(directory=root))
            with TestClient(app) as client:
                self.assertEqual(client.get("/previews/image.png").content, b"png")
                for path in (".render-journal.json", ".render-journal.tmp",
                             ".render-journal.lock", ".render-state/render.npy"):
                    with self.subTest(path=path):
                        self.assertEqual(client.get(f"/previews/{path}").status_code, 404)

    def test_staging_nginx_denies_render_state_before_preview_alias(self):
        config = (Path(__file__).resolve().parents[2] / "infra/staging/nginx.i2.conf").read_text()

        deny = "location ~ ^/previews/(?:\\.render-journal[^/]*|\\.render-state(?:/|$))"
        self.assertIn(deny, config)
        self.assertLess(config.index(deny), config.index("location /previews/"))


if __name__ == "__main__":
    unittest.main()
