#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Tuple

RELEASE_API_URL = (
    "https://api.github.com/repos/router-for-me/CLIProxyAPI/releases/latest"
)
OFFICIAL_FORMULA_URL = "https://api.github.com/repos/Homebrew/homebrew-core/contents/Formula/c/cliproxyapi.rb?ref=HEAD"
FORMULA_PATH = Path(__file__).resolve().parents[1] / "Formula" / "cliproxyapi.rb"

TOP_LEVEL_BOTTLE_BLOCK_RE = re.compile(
    r"\n  bottle do\n(?:    .*\n)+?  end\n",
    flags=re.MULTILINE,
)
TOP_LEVEL_LIVECHECK_BLOCK_RE = re.compile(
    r"\n  livecheck do\n(?:    .*\n)+?  end\n",
    flags=re.MULTILINE,
)
TOP_LEVEL_URL_RE = re.compile(
    r'^  url "https://github\.com/router-for-me/CLIProxyAPI/archive/refs/tags/v[^"]+\.tar\.gz"$',
    flags=re.MULTILINE,
)
TOP_LEVEL_SHA256_RE = re.compile(
    r'^  sha256 "[^"]+"$',
    flags=re.MULTILINE,
)
TOP_LEVEL_TEST_BLOCK_RE = re.compile(
    r"\n+  test do\n.*?\n  end\nend\s*\Z",
    flags=re.DOTALL,
)

TEST_BLOCK = """
  test do
    require \"pty\"
    require \"timeout\"

    output = +\"\"
    PTY.spawn(bin/\"cliproxyapi\", \"-login\", \"-no-browser\") do |r, _w, pid|
      begin
        Timeout.timeout(15) do
          loop do
            output << r.readpartial(1024)
            break if output.include?(\"accounts.google.com\")
          end
        end
      ensure
        begin
          Process.kill \"TERM\", pid
        rescue Errno::ESRCH
          output << \"\"
        end
        begin
          Process.wait pid
        rescue Errno::ECHILD
          output << \"\"
        end
      end
    end

    assert_match \"accounts.google.com\", output
  end
end"""


def update_formula_text(
    formula_text: str, version: str, source_sha256: str
) -> Tuple[str, bool]:
    updated_text = TOP_LEVEL_LIVECHECK_BLOCK_RE.sub("\n", formula_text, count=1)
    updated_text = TOP_LEVEL_BOTTLE_BLOCK_RE.sub("\n", updated_text, count=1)

    updated_text, url_count = TOP_LEVEL_URL_RE.subn(
        f'  url "https://github.com/router-for-me/CLIProxyAPI/archive/refs/tags/v{version}.tar.gz"',
        updated_text,
        count=1,
    )
    if url_count != 1:
        raise ValueError("Official formula top-level url not found")

    updated_text, sha_count = TOP_LEVEL_SHA256_RE.subn(
        f'  sha256 "{source_sha256}"',
        updated_text,
        count=1,
    )
    if sha_count != 1:
        raise ValueError("Official formula top-level sha256 not found")

    updated_text, test_count = TOP_LEVEL_TEST_BLOCK_RE.subn(
        "\n\n" + TEST_BLOCK + "\n",
        updated_text,
        count=1,
    )
    if test_count != 1:
        raise ValueError("Official formula test block not found")

    validate_formula_text(updated_text, version=version)

    return updated_text, updated_text != formula_text


def validate_formula_text(formula_text: str, *, version: str) -> None:
    required_snippets = [
        "class Cliproxyapi < Formula",
        'homepage "https://github.com/router-for-me/CLIProxyAPI"',
        f'url "https://github.com/router-for-me/CLIProxyAPI/archive/refs/tags/v{version}.tar.gz"',
        'depends_on "go" => :build',
        'system "go", "build"',
        'etc.install "config.example.yaml" => "cliproxyapi.conf"',
        "service do",
        'run [opt_bin/"cliproxyapi"]',
        "test do",
        'PTY.spawn(bin/"cliproxyapi", "-login", "-no-browser")',
        "Timeout.timeout(15)",
        'assert_match "accounts.google.com", output',
    ]

    missing = [snippet for snippet in required_snippets if snippet not in formula_text]
    if missing:
        raise ValueError(f"Generated formula missing required content: {missing}")

    if "bottle do" in formula_text:
        raise ValueError("Generated formula still contains bottle block")

    if "livecheck do" in formula_text:
        raise ValueError("Generated formula still contains livecheck block")


def gh_available() -> bool:
    return shutil.which("gh") is not None


def run_gh_api(endpoint: str, *, accept: str | None = None) -> bytes:
    command = ["gh", "api"]
    if accept:
        command.extend(["-H", f"Accept: {accept}"])
    command.append(endpoint)
    result = subprocess.run(command, check=True, capture_output=True)
    return result.stdout


def api_endpoint_from_url(url: str) -> str | None:
    prefix = "https://api.github.com/"
    if url.startswith(prefix):
        return url[len(prefix) :]
    return None


def fetch_json(url: str) -> dict:
    endpoint = api_endpoint_from_url(url)
    if endpoint and gh_available():
        try:
            return json.loads(run_gh_api(endpoint).decode("utf-8"))
        except subprocess.CalledProcessError:
            pass

    with urllib.request.urlopen(url) as response:
        return json.load(response)


def fetch_text(url: str, *, accept: str | None = None) -> str:
    endpoint = api_endpoint_from_url(url)
    if endpoint and gh_available():
        try:
            return run_gh_api(endpoint, accept=accept).decode("utf-8")
        except subprocess.CalledProcessError:
            pass

    request = urllib.request.Request(url)
    if accept:
        request.add_header("Accept", accept)

    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


def fetch_bytes(url: str) -> bytes:
    result = subprocess.run(
        ["curl", "-fsSL", "--retry", "3", "--retry-delay", "1", url],
        check=True,
        capture_output=True,
    )
    return result.stdout


def update_formula_file(formula_path: Path = FORMULA_PATH) -> bool:
    release = fetch_json(RELEASE_API_URL)
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Latest release must be a published stable release")

    tag_name = release["tag_name"]
    version = tag_name.removeprefix("v")

    official_formula = fetch_text(
        OFFICIAL_FORMULA_URL,
        accept="application/vnd.github.raw",
    )

    source_tarball_url = f"https://github.com/router-for-me/CLIProxyAPI/archive/refs/tags/v{version}.tar.gz"
    source_tarball_bytes = fetch_bytes(source_tarball_url)
    source_sha256 = hashlib.sha256(source_tarball_bytes).hexdigest()

    updated_text, changed = update_formula_text(
        official_formula, version, source_sha256
    )

    if changed:
        formula_path.write_text(updated_text)

    return changed


def main() -> int:
    changed = update_formula_file()
    if changed:
        print("Formula updated")
    else:
        print("Formula already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
