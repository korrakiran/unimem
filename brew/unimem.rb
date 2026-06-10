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
  sha256 "5f8758d59c4ad763b4f6da0f833c25007eee42ecd3d9037a0664097b9ac14ada"
  license "MIT"
  head "https://github.com/korrakiran/collector.git", branch: "main"

  depends_on "python@3.12"

  resource "annotated-doc" do
    url "https://files.pythonhosted.org/packages/57/ba/046ceea27344560984e26a590f90bc7f4a75b06701f653222458922b558c/annotated_doc-0.0.4.tar.gz"
    sha256 "fbcda96e87e9c92ad167c2e53839e57503ecfda18804ea28102353485033faa4"
  end

  resource "annotated-types" do
    url "https://files.pythonhosted.org/packages/ee/67/531ea369ba64dcff5ec9c3402f9f51bf748cec26dde048a2f973a4eea7f5/annotated_types-0.7.0.tar.gz"
    sha256 "aff07c09a53a08bc8cfccb9c85b05f1aa9a2a6f23728d790723543408344ce89"
  end

  resource "gitdb" do
    url "https://files.pythonhosted.org/packages/72/94/63b0fc47eb32792c7ba1fe1b694daec9a63620db1e313033d18140c2320a/gitdb-4.0.12.tar.gz"
    sha256 "5ef71f855d191a3326fcfbc0d5da835f26b13fbcba60c32c21091c349ffdb571"
  end

  resource "GitPython" do
    url "https://files.pythonhosted.org/packages/33/f6/354ae6491228b5eb40e10d89c4d13c651fe1cf7556e35ebdded50cff57ce/gitpython-3.1.50.tar.gz"
    sha256 "80da2d12504d52e1f998772dc5baf6e553f8d2fcfe1fcc226c9d9a2ee3372dcc"
  end

  resource "markdown-it-py" do
    url "https://files.pythonhosted.org/packages/06/ff/7841249c247aa650a76b9ee4bbaeae59370dc8bfd2f6c01f3630c35eb134/markdown_it_py-4.2.0.tar.gz"
    sha256 "04a21681d6fbb623de53f6f364d352309d4094dd4194040a10fd51833e418d49"
  end

  resource "mdurl" do
    url "https://files.pythonhosted.org/packages/d6/54/cfe61301667036ec958cb99bd3efefba235e65cdeb9c84d24a8293ba1d90/mdurl-0.1.2.tar.gz"
    sha256 "bb413d29f5eea38f31dd4754dd7377d4465116fb207585f97bf925588687c1ba"
  end

  resource "platformdirs" do
    url "https://files.pythonhosted.org/packages/d7/47/e4501f49c178ae1d9f4a75073fda4204f52647993f075a9db4d14930e0c5/platformdirs-4.10.0.tar.gz"
    sha256 "31e761a6a0ca04faf7353ea759bdba55652be214725111e5aac52dfa29d4bef7"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/18/a5/b60d21ac674192f8ab0ba4e9fd860690f9b4a6e51ca5df118733b487d8d6/pydantic-2.13.4.tar.gz"
    sha256 "c40756b57adaa8b1efeeced5c196f3f3b7c435f90e84ea7f443901bec8099ef6"
  end

  resource "pydantic_core" do
    url "https://files.pythonhosted.org/packages/19/95/6195171e385007300f0f5574592e467c568becce2d937a0b6804f218bc49/pydantic_core-2.46.4-cp312-cp312-macosx_11_0_arm64.whl"
    sha256 "962ccbab7b642487b1d8b7df90ef677e03134cf1fd8880bf698649b22a69371f"
  end

  resource "Pygments" do
    url "https://files.pythonhosted.org/packages/c3/b2/bc9c9196916376152d655522fdcebac55e66de6603a76a02bca1b6414f6c/pygments-2.20.0.tar.gz"
    sha256 "6757cd03768053ff99f3039c1a36d6c0aa0b263438fcab17520b30a303a82b5f"
  end

  resource "PyYAML" do
    url "https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz"
    sha256 "d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/c0/8f/0722ca900cc807c13a6a0c696dacf35430f72e0ec571c4275d2371fca3e9/rich-15.0.0.tar.gz"
    sha256 "edd07a4824c6b40189fb7ac9bc4c52536e9780fbbfbddf6f1e2502c31b068c36"
  end

  resource "shellingham" do
    url "https://files.pythonhosted.org/packages/58/15/8b3609fd3830ef7b27b655beb4b4e9c62313a4e8da8c676e142cc210d58e/shellingham-1.5.4.tar.gz"
    sha256 "8dbca0739d487e5bd35ab3ca4b36e11c4078f3a234bfce294b0a0291363404de"
  end

  resource "smmap" do
    url "https://files.pythonhosted.org/packages/1f/ea/49c993d6dfdd7338c9b1000a0f36817ed7ec84577ae2e52f890d1a4ff909/smmap-5.0.3.tar.gz"
    sha256 "4d9debb8b99007ae47165abc08670bd74cb74b5227dda7f643eccc4e9eb5642c"
  end

  resource "typer" do
    url "https://files.pythonhosted.org/packages/5e/ed/ef06584ccdd5c410df0837951ecd7e15d9a6144ea1bd4c73cecab1a89891/typer-0.26.7.tar.gz"
    sha256 "e314a34c617e419c091b2830dda3ea1f257134ff593061a8f5b9717ab8dddb3a"
  end

  resource "typing-inspection" do
    url "https://files.pythonhosted.org/packages/55/e3/70399cb7dd41c10ac53367ae42139cf4b1ca5f36bb3dc6c9d33acdb43655/typing_inspection-0.4.2.tar.gz"
    sha256 "ba561c48a67c5958007083d386c3295464928b01faa735ab8547c5692e87f464"
  end

  resource "typing_extensions" do
    url "https://files.pythonhosted.org/packages/72/94/1a15dd82efb362ac84269196e94cf00f187f7ed21c242792a923cdb1c61f/typing_extensions-4.15.0.tar.gz"
    sha256 "0cea48d173cc12fa28ecabc3b837ea3cf6f38c6d1136f85cbaaf598984861466"
  end

  resource "watchdog" do
    url "https://files.pythonhosted.org/packages/db/7d/7f3d619e951c88ed75c6037b246ddcf2d322812ee8ea189be89511721d54/watchdog-6.0.0.tar.gz"
    sha256 "9ddf7c82fda3ae8e24decda1338ede66e1c99883db93711d8fb941eaa2d8c282"
  end


  def install
    venv = virtualenv_create(libexec, "python3.12")
    
    # Symlink the cached wheel to a valid wheel filename format so pip accepts it
    valid_wheel = buildpath/"pydantic_core-2.46.4-cp312-cp312-macosx_11_0_arm64.whl"
    ln_s resource("pydantic_core").cached_download, valid_wheel

    # Install pydantic_core from the symlinked wheel file to avoid Maturin build dependency
    system Formula["python@3.12"].opt_bin/"python3.12", "-m", "pip", "--python", libexec/"bin/python", "install", "--no-deps", valid_wheel
    
    resources.each do |r|
      next if r.name == "pydantic_core"
      venv.pip_install r
    end
    
    venv.pip_install_and_link buildpath
  end

  def post_install
    home_dir = Dir.home
    rules_content = <<~EOS
      # Global Unimem Automation Rules

      Unimem is active in this project. You are resuming work from a previous session.

      Before you begin coding:
      1. Read the project memory file at `.unimem/memory.md` to get your full context:
         - Current Goal & Task focus
         - Completed and In-Progress features
         - Architectural decisions
         - Important files to locate
      2. Trust `.unimem/memory.md` as the source of truth for the project state.

      When you finish or pause work:
      - Update the Unimem state (e.g. by running `unimem summary` or updating `.unimem/state.json`) so the next agent can seamlessly take over.
    EOS

    begin
      File.write(File.join(home_dir, ".cursorrules"), rules_content)
      File.write(File.join(home_dir, ".clauderules"), rules_content)
      ohai "Successfully configured global agent rules in ~/.cursorrules and ~/.clauderules"
    rescue => e
      opoo "Could not write global agent rules: #{e.message}"
    end

    # Configure auto-injector hook in ~/.zshrc if not present
    zshrc_path = File.join(home_dir, ".zshrc")
    hook_code = <<~EOS

      # Unimem Auto-Rule Injector & Init
      unimem_inject_rules() {
        if [[ "$PWD" != "$HOME" && "$PWD" == "$HOME/"* ]]; then
          if [[ ! -f ".cursorrules" && -f "$HOME/.cursorrules" ]]; then
            cp "$HOME/.cursorrules" .cursorrules 2>/dev/null
          fi
          if [[ ! -f ".clauderules" && -f "$HOME/.clauderules" ]]; then
            cp "$HOME/.clauderules" .clauderules 2>/dev/null
          fi
          # Silently initialize Unimem if not present
          if [[ ! -d ".unimem" ]]; then
            unimem init --name "$(basename "$PWD")" >/dev/null 2>&1 &
          fi
        fi
      }
      autoload -U add-zsh-hook
      add-zsh-hook chpwd unimem_inject_rules
      add-zsh-hook precmd unimem_inject_rules
      unimem_inject_rules
    EOS

    if File.exist?(zshrc_path) && !File.read(zshrc_path).include?("unimem_inject_rules")
      begin
        File.open(zshrc_path, "a") { |f| f.write(hook_code) }
        ohai "Successfully configured auto-rule injector hook in ~/.zshrc"
      rescue => e
        opoo "Could not configure auto-rule injector hook: #{e.message}"
      end
    end
  end

  test do
    # Check if CLI displays version correctly
    assert_match "version", shell_output("#{bin}/unimem --version")
  end
end
