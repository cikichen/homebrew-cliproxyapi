class Cliproxyapi < Formula
  desc "Wrap Gemini CLI, Codex, Claude Code, Qwen Code as an API service"
  homepage "https://github.com/router-for-me/CLIProxyAPI"
  url "https://github.com/router-for-me/CLIProxyAPI/archive/refs/tags/v6.9.31.tar.gz"
  sha256 "71ab6155432f876dea05477631761c668291d485f1c362e87b654b6dd38f4534"
  license "MIT"
  head "https://github.com/router-for-me/CLIProxyAPI.git", branch: "main"



  depends_on "go" => :build

  def install
    ldflags = %W[
      -s -w
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
