import importlib.util
import io
import json
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "update_formula.py"

OFFICIAL_FORMULA_TEMPLATE = """\
class Cliproxyapi < Formula
  desc \"Wrap Gemini CLI, Codex, Claude Code, Qwen Code as an API service\"
  homepage \"https://github.com/router-for-me/CLIProxyAPI\"
  url \"https://github.com/router-for-me/CLIProxyAPI/archive/refs/tags/v6.8.50.tar.gz\"
  sha256 \"old-source-sha\"
  license \"MIT\"
  head \"https://github.com/router-for-me/CLIProxyAPI.git\", branch: \"main\"

  livecheck do
    throttle 5
  end

  bottle do
    sha256 arm64_sonoma: \"bottle-sha\"
    sha256 sonoma:       \"bottle-sha-2\"
  end

  depends_on \"go\" => :build

  def install
    ldflags = %W[
      -s -w
      -X main.Version=#{version}
      -X main.Commit=#{tap.user}
    ]

    system \"go\", \"build\", *std_go_args(ldflags:), \"cmd/server/main.go\"
    etc.install \"config.example.yaml\" => \"cliproxyapi.conf\"
  end

  service do
    run [opt_bin/\"cliproxyapi\"]
    keep_alive true
  end

  test do
    require \"pty\"
    PTY.spawn(bin/\"cliproxyapi\", \"-login\", \"-no-browser\") do |r, _w, pid|
      sleep 5
      Process.kill \"TERM\", pid
      assert_match \"accounts.google.com\", r.read_nonblock(1024)
    end
  end
end
"""


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
        payload = {"tag_name": "v6.8.51"}

        with (
            mock.patch.object(module, "gh_available", return_value=True),
            mock.patch.object(
                module,
                "run_gh_api",
                side_effect=module.subprocess.CalledProcessError(4, ["gh", "api"]),
            ),
            mock.patch.object(
                module.urllib.request,
                "urlopen",
                return_value=io.StringIO(json.dumps(payload)),
            ),
        ):
            result = module.fetch_json(module.RELEASE_API_URL)

        self.assertEqual(result, payload)

    def test_fetch_text_falls_back_to_urllib_when_gh_api_fails(self):
        module = load_update_module()

        with (
            mock.patch.object(module, "gh_available", return_value=True),
            mock.patch.object(
                module,
                "run_gh_api",
                side_effect=module.subprocess.CalledProcessError(4, ["gh", "api"]),
            ),
            mock.patch.object(
                module.urllib.request,
                "urlopen",
                return_value=io.BytesIO(b"formula text\n"),
            ),
        ):
            result = module.fetch_text(
                module.OFFICIAL_FORMULA_URL,
                accept="text/plain",
            )

        self.assertEqual(result, "formula text\n")

    def test_fetch_bytes_uses_curl(self):
        module = load_update_module()

        with (
            mock.patch.object(
                module.subprocess,
                "run",
                return_value=mock.Mock(stdout=b"tarball-bytes"),
            ) as run_command,
        ):
            result = module.fetch_bytes(
                "https://github.com/router-for-me/CLIProxyAPI/archive/refs/tags/v6.8.51.tar.gz"
            )

        self.assertEqual(result, b"tarball-bytes")
        run_command.assert_called_once_with(
            [
                "curl",
                "-fsSL",
                "--retry",
                "3",
                "--retry-delay",
                "1",
                "https://github.com/router-for-me/CLIProxyAPI/archive/refs/tags/v6.8.51.tar.gz",
            ],
            check=True,
            capture_output=True,
        )

    def test_update_formula_text_raises_when_top_level_url_missing(self):
        module = load_update_module()
        broken_template = OFFICIAL_FORMULA_TEMPLATE.replace(
            '  url "https://github.com/router-for-me/CLIProxyAPI/archive/refs/tags/v6.8.50.tar.gz"\n',
            "",
        )

        with self.assertRaisesRegex(ValueError, "top-level url"):
            module.update_formula_text(
                broken_template,
                version="6.8.51",
                source_sha256="new-source-sha",
            )

    def test_update_formula_text_raises_when_required_blocks_missing_after_transform(
        self,
    ):
        module = load_update_module()
        broken_template = OFFICIAL_FORMULA_TEMPLATE.replace("  service do\n", "")

        with self.assertRaisesRegex(ValueError, "missing required content"):
            module.update_formula_text(
                broken_template,
                version="6.8.51",
                source_sha256="new-source-sha",
            )

    def test_update_formula_text_raises_when_test_block_missing(self):
        module = load_update_module()
        broken_template = OFFICIAL_FORMULA_TEMPLATE.replace("  test do\n", "")

        with self.assertRaisesRegex(ValueError, "test block"):
            module.update_formula_text(
                broken_template,
                version="6.8.51",
                source_sha256="new-source-sha",
            )

    def test_update_formula_file_rejects_prerelease(self):
        module = load_update_module()
        release = {"tag_name": "v6.8.51", "prerelease": True}

        with mock.patch.object(module, "fetch_json", return_value=release):
            with self.assertRaisesRegex(ValueError, "published stable release"):
                module.update_formula_file(formula_path=ROOT / "Formula" / "ignored.rb")

    def test_update_formula_text_uses_official_template_removes_bottle_and_updates_source_tarball(
        self,
    ):
        module = load_update_module()

        updated_text, changed = module.update_formula_text(
            OFFICIAL_FORMULA_TEMPLATE,
            version="6.8.51",
            source_sha256="new-source-sha",
        )

        self.assertTrue(changed)
        self.assertIn(
            'url "https://github.com/router-for-me/CLIProxyAPI/archive/refs/tags/v6.8.51.tar.gz"',
            updated_text,
        )
        self.assertIn('sha256 "new-source-sha"', updated_text)
        self.assertNotIn("bottle do", updated_text)
        self.assertNotIn("livecheck do", updated_text)
        self.assertIn('system "go", "build"', updated_text)
        self.assertIn('run [opt_bin/"cliproxyapi"]', updated_text)
        self.assertIn('PTY.spawn(bin/"cliproxyapi"', updated_text)
        self.assertIn("Timeout.timeout(15)", updated_text)
        self.assertIn('assert_match "accounts.google.com", output', updated_text)

    def test_update_formula_text_is_noop_when_template_already_matches_target(self):
        module = load_update_module()
        formula_text, first_changed = module.update_formula_text(
            OFFICIAL_FORMULA_TEMPLATE,
            version="6.8.51",
            source_sha256="new-source-sha",
        )

        self.assertTrue(first_changed)

        updated_text, changed = module.update_formula_text(
            formula_text,
            version="6.8.51",
            source_sha256="new-source-sha",
        )

        self.assertFalse(changed)
        self.assertEqual(updated_text, formula_text)

    def test_update_formula_file_fetches_official_template_and_latest_release_tarball_sha(
        self,
    ):
        module = load_update_module()
        release = {"tag_name": "v6.8.51"}
        formula_path = ROOT / "Formula" / "test-cliproxyapi.rb"
        self.addCleanup(lambda: formula_path.unlink(missing_ok=True))
        formula_path.write_text("stale formula\n")

        with (
            mock.patch.object(module, "fetch_json", return_value=release),
            mock.patch.object(
                module, "fetch_text", return_value=OFFICIAL_FORMULA_TEMPLATE
            ),
            mock.patch.object(
                module, "fetch_bytes", return_value=b"source tarball bytes"
            ),
        ):
            changed = module.update_formula_file(formula_path=formula_path)

        self.assertTrue(changed)
        updated_text = formula_path.read_text()
        self.assertIn("v6.8.51.tar.gz", updated_text)
        self.assertNotIn("bottle do", updated_text)
        self.assertNotIn("livecheck do", updated_text)
        self.assertIn(
            module.hashlib.sha256(b"source tarball bytes").hexdigest(), updated_text
        )


if __name__ == "__main__":
    unittest.main()
