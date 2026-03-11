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
2. fetches the latest upstream CLIProxyAPI release metadata
3. fetches upstream `checksums.txt`
4. updates `Formula/cliproxyapi.rb` when version or checksums changed
5. commits and pushes the formula update automatically

## Manual local update

You can also run the updater locally:

```bash
python3 scripts/update_formula.py
```

If the formula is already on the latest release, the script exits without changing the file.

## Update formula manually

When upstream publishes a new release and you want to update by hand:

1. Update `version` in `Formula/cliproxyapi.rb`
2. Update the matching `sha256` values from upstream `checksums.txt`
3. Commit and push

## Upstream release assets

This tap uses the upstream GitHub release archives:

- `CLIProxyAPI_<version>_darwin_arm64.tar.gz`
- `CLIProxyAPI_<version>_darwin_amd64.tar.gz`
