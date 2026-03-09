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
cli-proxy-api --help
```

## Update formula

When upstream publishes a new release:

1. Update `version` in `Formula/cliproxyapi.rb`
2. Update the matching `sha256` values from upstream `checksums.txt`
3. Commit and push

## Upstream release assets

This tap uses the upstream GitHub release archives:

- `CLIProxyAPI_<version>_darwin_arm64.tar.gz`
- `CLIProxyAPI_<version>_darwin_amd64.tar.gz`
