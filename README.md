# homebrew-cliproxyapi

Dedicated Homebrew tap for [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI).

## Install

```bash
brew tap cikichen/cliproxyapi
brew install cliproxyapi
```

Or use the fully qualified formula name:

```bash
brew install cikichen/cliproxyapi/cliproxyapi
```

## Upgrade

```bash
brew update
brew upgrade cliproxyapi
```

## Verify

```bash
cliproxyapi --help
```

## Automatic updates

This repository includes a GitHub Actions workflow at `.github/workflows/update-formula.yml`.

It can update the formula in two ways:

- scheduled run once per day
- manual run from the GitHub Actions tab

The workflow:

1. runs the unit tests for the update script
2. fetches the official homebrew-core formula as a template
3. fetches the latest upstream CLIProxyAPI release metadata
4. updates `Formula/cliproxyapi.rb` with the latest version and source tarball sha256
5. commits and pushes the formula update automatically

This tap reuses the official homebrew-core formula structure and only syncs version-related changes for faster releases.

## Manual local update

You can also run the updater locally:

```bash
python3 scripts/update_formula.py
```

If the formula is already on the latest release, the script exits without changing the file.
