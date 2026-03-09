class Cliproxyapi < Formula
  desc "CLI API proxy service"
  homepage "https://github.com/router-for-me/CLIProxyAPI"
  version "6.8.49"
  license "MIT"

  livecheck do
    url :stable
    strategy :github_latest
  end

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/router-for-me/CLIProxyAPI/releases/download/v#{version}/CLIProxyAPI_#{version}_darwin_arm64.tar.gz"
      sha256 "5dfa1e359d8e44601b3cc0aa6f665d4a376ec568187d24a62155dcae6515bdb3"
    else
      url "https://github.com/router-for-me/CLIProxyAPI/releases/download/v#{version}/CLIProxyAPI_#{version}_darwin_amd64.tar.gz"
      sha256 "ce555eb14b43eff3b3c06d53f592ac1cfa2edfe200f588f4b823c4083bbc22d8"
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
