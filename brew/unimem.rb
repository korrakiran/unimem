# Homebrew Formula for Unimem CLI tool
# To release:
# 1. Tag and release Unimem on GitHub (e.g. v0.1.0).
# 2. Get the tarball URL and calculate its SHA256 using: curl -sL <url> | shasum -a 256
# 3. Update the url and sha256 fields below.
# 4. Copy this file into your tap repository (e.g., github.com/korrakiran/homebrew-unimem/Formula/unimem.rb).

class Unimem < Formula
  include Language::Python::Virtualenv

  desc "Universal Project Memory Layer for AI Coding Agents"
  homepage "https://github.com/korrakiran/collector"
  url "https://github.com/korrakiran/collector/archive/refs/tags/v0.1.0.tar.gz"
  # Note: Replace this placeholder SHA256 with the actual release archive SHA256
  sha256 "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  license "MIT"
  head "https://github.com/korrakiran/collector.git", branch: "main"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    # Check if CLI displays version correctly
    assert_match "version", shell_output("#{bin}/unimem --version")
  end
end
