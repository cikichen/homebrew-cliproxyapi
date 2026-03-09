#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Dict, Tuple

RELEASE_API_URL = "https://api.github.com/repos/router-for-me/CLIProxyAPI/releases/latest"
FORMULA_PATH = Path(__file__).resolve().parents[1] / "Formula" / "cliproxyapi.rb"
ARM_FILENAME_TEMPLATE = "CLIProxyAPI_{version}_darwin_arm64.tar.gz"
AMD_FILENAME_TEMPLATE = "CLIProxyAPI_{version}_darwin_amd64.tar.gz"


def parse_checksums(checksums_text: str, version: str) -> Dict[str, str]:
    expected_files = {
        ARM_FILENAME_TEMPLATE.format(version=version): "darwin_arm64",
        AMD_FILENAME_TEMPLATE.format(version=version): "darwin_amd64",
    }
    result: Dict[str, str] = {}

    for line in checksums_text.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        checksum, filename = parts
        arch_key = expected_files.get(filename)
        if arch_key:
            result[arch_key] = checksum

    missing = sorted(set(expected_files.values()) - set(result))
    if missing:
        raise ValueError(f"Missing checksums for: {', '.join(missing)}")

    return result


def update_formula_text(formula_text: str, version: str, macos_checksums: Dict[str, str]) -> Tuple[str, bool]:
    updated_text = re.sub(r'version ".*?"', f'version "{version}"', formula_text, count=1)

    sha_pattern = re.compile(
        r'(?P<indent>\s+)if Hardware::CPU\.arm\?\n(?P<arm_block>(?:.*\n)*?)(?P=indent)else\n(?P<amd_block>(?:.*\n)*?)(?P=indent)end',
        re.MULTILINE,
    )
    match = sha_pattern.search(updated_text)
    if not match:
        raise ValueError("Unable to locate macOS checksum block in formula")

    arm_block = re.sub(
        r'sha256 ".*?"',
        f'sha256 "{macos_checksums["darwin_arm64"]}"',
        match.group("arm_block"),
        count=1,
    )
    amd_block = re.sub(
        r'sha256 ".*?"',
        f'sha256 "{macos_checksums["darwin_amd64"]}"',
        match.group("amd_block"),
        count=1,
    )

    replacement = (
        f'{match.group("indent")}if Hardware::CPU.arm?\n'
        f'{arm_block}'
        f'{match.group("indent")}else\n'
        f'{amd_block}'
        f'{match.group("indent")}end'
    )
    updated_text = f'{updated_text[:match.start()]}{replacement}{updated_text[match.end():]}'

    return updated_text, updated_text != formula_text


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
        return url[len(prefix):]
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


def update_formula_file(formula_path: Path = FORMULA_PATH) -> bool:
    release = fetch_json(RELEASE_API_URL)
    tag_name = release["tag_name"]
    version = tag_name.removeprefix("v")

    checksums_asset = next(
        (asset for asset in release.get("assets", []) if asset.get("name") == "checksums.txt"),
        None,
    )
    if checksums_asset is None:
        raise ValueError("checksums.txt asset not found in latest release")

    checksums = parse_checksums(
        fetch_text(checksums_asset["url"], accept="application/octet-stream"),
        version,
    )
    original_text = formula_path.read_text()
    updated_text, changed = update_formula_text(original_text, version, checksums)

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
