import importlib.util
import pathlib
import unittest


class ShareTop10Tests(unittest.TestCase):
    def test_script_imports_from_repo_root(self) -> None:
        script_path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "share_top10.py"
        spec = importlib.util.spec_from_file_location("share_top10_test_module", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertTrue(hasattr(module, "run_agent"))


if __name__ == "__main__":
    unittest.main()
