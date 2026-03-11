class Cliproxyapi < Formula
  desc "CLI API proxy service"
  homepage "https://github.com/router-for-me/CLIProxyAPI"
  version "6.8.51"
  license "MIT"

  livecheck do
    url :stable
    strategy :github_latest
  end

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/router-for-me/CLIProxyAPI/releases/download/v#{version}/CLIProxyAPI_#{version}_darwin_arm64.tar.gz"
      sha256 "5addb483e45996d0103622b779c9f4d8fe7eb06ece17e12c1753ce8aea7741b9"
    else
      url "https://github.com/router-for-me/CLIProxyAPI/releases/download/v#{version}/CLIProxyAPI_#{version}_darwin_amd64.tar.gz"
      sha256 "f6e7a8abba4fda3709832980c083c149e8fa3e8398f7fd403a0009c1094b05b4"
    end
  end

  def install
    bin.install "cli-proxy-api" => "cliproxyapi"
    pkgshare.install "config.example.yaml" if File.exist?("config.example.yaml")
  end

  test do
    output = shell_output("#{bin}/cliproxyapi --help 2>&1")
    assert_match "usage", output.downcase
  end

  service do
    run opt_bin/"cliproxyapi"
    keep_alive true
    log_path var/"log/cliproxyapi.log"
    error_log_path var/"log/cliproxyapi.err.log"
  end
end
