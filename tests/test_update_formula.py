import importlib.util
import io
import json
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "update_formula.py"


def load_update_module():
    if not SCRIPT_PATH.exists():
        raise AssertionError("scripts/update_formula.py not found")

    spec = importlib.util.spec_from_file_location("update_formula", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("Unable to load scripts/update_formula.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UpdateFormulaTests(unittest.TestCase):
    def test_fetch_json_falls_back_to_urllib_when_gh_api_fails(self):
        module = load_update_module()
        payload = {"tag_name": "v6.8.49"}

        with mock.patch.object(module, "gh_available", return_value=True), \
             mock.patch.object(module, "run_gh_api", side_effect=module.subprocess.CalledProcessError(4, ["gh", "api"])), \
             mock.patch.object(module.urllib.request, "urlopen", return_value=io.StringIO(json.dumps(payload))):
            result = module.fetch_json(module.RELEASE_API_URL)

        self.assertEqual(result, payload)

    def test_fetch_text_falls_back_to_urllib_when_gh_api_fails(self):
        module = load_update_module()

        with mock.patch.object(module, "gh_available", return_value=True), \
             mock.patch.object(module, "run_gh_api", side_effect=module.subprocess.CalledProcessError(4, ["gh", "api"])), \
             mock.patch.object(module.urllib.request, "urlopen", return_value=io.BytesIO(b"checksum  file.tar.gz\n")):
            result = module.fetch_text(
                "https://api.github.com/repos/router-for-me/CLIProxyAPI/releases/assets/123",
                accept="application/octet-stream",
            )

        self.assertEqual(result, "checksum  file.tar.gz\n")

    def test_parse_checksums_extracts_macos_hashes(self):
        module = load_update_module()
        checksums = """\
5dfa1e359d8e44601b3cc0aa6f665d4a376ec568187d24a62155dcae6515bdb3  CLIProxyAPI_6.8.49_darwin_arm64.tar.gz
ce555eb14b43eff3b3c06d53f592ac1cfa2edfe200f588f4b823c4083bbc22d8  CLIProxyAPI_6.8.49_darwin_amd64.tar.gz
c0ffee  CLIProxyAPI_6.8.49_linux_arm64.tar.gz
"""

        result = module.parse_checksums(checksums, "6.8.49")

        self.assertEqual(
            result,
            {
                "darwin_arm64": "5dfa1e359d8e44601b3cc0aa6f665d4a376ec568187d24a62155dcae6515bdb3",
                "darwin_amd64": "ce555eb14b43eff3b3c06d53f592ac1cfa2edfe200f588f4b823c4083bbc22d8",
            },
        )

    def test_update_formula_text_replaces_version_and_both_macos_checksums(self):
        module = load_update_module()
        formula_text = """\
class Cliproxyapi < Formula
  version \"6.8.45\"

  on_macos do
    if Hardware::CPU.arm?
      sha256 \"old-arm\"
    else
      sha256 \"old-amd\"
    end
  end
end
"""

        updated_text, changed = module.update_formula_text(
            formula_text,
            version="6.8.49",
            macos_checksums={
                "darwin_arm64": "new-arm",
                "darwin_amd64": "new-amd",
            },
        )

        self.assertTrue(changed)
        self.assertIn('version "6.8.49"', updated_text)
        self.assertIn('sha256 "new-arm"', updated_text)
        self.assertIn('sha256 "new-amd"', updated_text)
        self.assertNotIn('version "6.8.45"', updated_text)

    def test_update_formula_text_is_noop_when_formula_already_matches_latest_release(self):
        module = load_update_module()
        formula_text = """\
class Cliproxyapi < Formula
  version \"6.8.49\"

  on_macos do
    if Hardware::CPU.arm?
      sha256 \"arm-same\"
    else
      sha256 \"amd-same\"
    end
  end
end
"""

        updated_text, changed = module.update_formula_text(
            formula_text,
            version="6.8.49",
            macos_checksums={
                "darwin_arm64": "arm-same",
                "darwin_amd64": "amd-same",
            },
        )

        self.assertFalse(changed)
        self.assertEqual(updated_text, formula_text)


if __name__ == "__main__":
    unittest.main()
