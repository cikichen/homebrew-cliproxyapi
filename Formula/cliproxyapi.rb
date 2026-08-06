class Cliproxyapi < Formula
  desc "Wrap Gemini CLI, Codex, Claude Code, Qwen Code as an API service"
  homepage "https://github.com/router-for-me/CLIProxyAPI"
  url "https://github.com/router-for-me/CLIProxyAPI/archive/refs/tags/v7.2.120.tar.gz"
  sha256 "42e53015a7d5d4983f8ce086891aa4deb2385bd254d162ada753cdadae615796"
  license "MIT"
  head "https://github.com/router-for-me/CLIProxyAPI.git", branch: "main"



  depends_on "go" => :build

  def install
    ldflags = %W[
      -X main.Version=#{version}
      -X main.Commit=#{tap.user}
      -X main.BuildDate=#{time.iso8601}
      -X main.DefaultConfigPath=#{etc/"cliproxyapi.conf"}
    ]

    system "go", "build", *std_go_args(ldflags:), "cmd/server/main.go"
    etc.install "config.example.yaml" => "cliproxyapi.conf"
  end

  service do
    run [opt_bin/"cliproxyapi"]
    keep_alive true
  end


  test do
    require "pty"
    require "timeout"

    output = +""
    PTY.spawn(bin/"cliproxyapi", "-login", "-no-browser") do |r, _w, pid|
      begin
        Timeout.timeout(15) do
          loop do
            output << r.readpartial(1024)
            break if output.include?("accounts.google.com")
          end
        end
      ensure
        begin
          Process.kill "TERM", pid
        rescue Errno::ESRCH
          output << ""
        end
        begin
          Process.wait pid
        rescue Errno::ECHILD
          output << ""
        end
      end
    end

    assert_match "accounts.google.com", output
  end
end
