class Cliproxyapi < Formula
  desc "CLI API proxy service"
  homepage "https://github.com/router-for-me/CLIProxyAPI"
  version "6.8.50"
  license "MIT"

  livecheck do
    url :stable
    strategy :github_latest
  end

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/router-for-me/CLIProxyAPI/releases/download/v#{version}/CLIProxyAPI_#{version}_darwin_arm64.tar.gz"
      sha256 "ea546e28a9737bcdf233bff953837f32ad47ce26c19fe7576520e4dc1b4ed21d"
    else
      url "https://github.com/router-for-me/CLIProxyAPI/releases/download/v#{version}/CLIProxyAPI_#{version}_darwin_amd64.tar.gz"
      sha256 "367bb8a35edcad5fb13b19fd3416083dba6a2a6b300bfbfb7f5446e7949e52ab"
    end
  end

  def install
    bin.install "cli-proxy-api"
    pkgshare.install "config.example.yaml" if File.exist?("config.example.yaml")
  end

  test do
    output = shell_output("#{bin}/cli-proxy-api --help 2>&1")
    assert_match "usage", output.downcase
  end
end
