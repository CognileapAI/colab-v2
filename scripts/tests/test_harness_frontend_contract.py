import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class FrontendContractLocationTests(unittest.TestCase):
    def test_permission_gate_input_is_not_a_session_document(self):
        test_source = (ROOT / "frontend/test/e01-apply-points.test.ts").read_text(encoding="utf-8")
        vite_source = (ROOT / "frontend/vite.config.ts").read_text(encoding="utf-8")
        self.assertNotIn("dev-package/sessions", test_source)
        self.assertNotIn("../dev-package/sessions", vite_source)

    def test_permission_gate_contract_has_nonempty_unique_sites(self):
        value = json.loads((ROOT / "contracts/ui/e01-permission-gates.json").read_text(encoding="utf-8"))
        sites = [(item["path"], item["requires"]) for item in value["sites"]]
        self.assertGreater(len(sites), 0)
        self.assertEqual(len(sites), len(set(sites)))
        self.assertEqual(set(value["switches"]), {
            "업로드·편집", "프로젝트 생성", "승인 위임", "연구실 설정",
        })


if __name__ == "__main__":
    unittest.main()
