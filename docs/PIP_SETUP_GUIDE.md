# Pip-Based Setup Guide (Poetry-Free)

**Date:** 2025-11-04
**Purpose:** Fast development environment setup without Poetry overhead

---

## Quick Start (< 2 minutes)

```bash
# 1. Remove Poetry artifacts (optional, for clean start)
rm -rf .poetry-1.8/ .venv/

# 2. Create virtual environment with Python's built-in venv
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Upgrade pip (recommended)
pip install --upgrade pip

# 5. Install all dependencies (13 packages + dependencies)
pip install -r requirements.txt

# 6. Setup service paths for monorepo
python scripts/setup_dev_environment.py

# 7. Configure environment secrets (IMPORTANT!)
cp .env.example .env
# Edit .env and add your actual tokens (see Secrets Management section below)

# 8. Verify installation
python -c "from app.main import app; print('✅ Success!')"

# 9. Run tests
pytest services/analysis-service/tests/test_health.py -q
```

**Expected time:** 30-90 seconds (vs. 5-6 minutes with Poetry)

---

## What Gets Installed

From `requirements/dev.txt`:

**Core Dependencies:**
- `fastapi==0.120.4` - Web framework
- `starlette==0.49.1` - ASGI toolkit
- `uvicorn==0.30.3` - ASGI server
- `httpx==0.27.0` - HTTP client
- `canonicaljson==2.0.0` - RFC-8785 JSON encoding
- `jsonschema==4.23.0` - JSON Schema validation

**Dev Tools:**
- `pytest==8.3.2` + `pytest-asyncio==0.23.8` - Testing
- `black==24.4.2` - Code formatter
- `isort==5.13.2` - Import sorter
- `ruff==0.6.4` - Linter
- `mypy==1.11.1` - Type checker

**Total:** ~41 packages (including transitive dependencies)

---

## Secrets Management

### Setup Environment Variables

**1. Copy the example file:**
```bash
cp .env.example .env
```

**2. Edit `.env` with your actual credentials:**
```bash
# DO NOT commit this file to git!
GITHUB_TOKEN=ghp_your_actual_token_here
FIGMA_API_KEY=figd_your_actual_key_here
```

**3. Obtain tokens:**
- **GitHub Token**: https://github.com/settings/tokens (repo scope)
- **Figma API Key**: https://www.figma.com/developers/api#access-tokens

### Security Best Practices

**✅ DO:**
- Store secrets in `.env` (already in `.gitignore`)
- Use environment variables in your code: `os.getenv("GITHUB_TOKEN")`
- Rotate tokens regularly (every 90 days recommended)
- Use minimal scopes/permissions for tokens

**❌ DON'T:**
- Commit `.env` files to git
- Hard-code secrets in source code
- Share secrets via Slack/email
- Use production secrets for local development

### Claude Code MCP Integration

If using Claude Code with MCP servers:

```bash
# Create local settings (also gitignored)
mkdir -p .claude
cat > .claude/settings.local.json <<'EOF'
{
  "permissions": {
    "allow": [
      "Bash(export GITHUB_TOKEN=\"$GITHUB_TOKEN\")",
      "Bash(export FIGMA_API_KEY=\"$FIGMA_API_KEY\")"
    ]
  }
}
EOF
```

**Never hard-code tokens in `.claude/settings.local.json`** - always reference environment variables.

### Verifying Secret Safety

**Run gitleaks scan:**
```bash
# Install gitleaks (one-time)
curl -sSfL https://github.com/gitleaks/gitleaks/releases/download/v8.18.2/gitleaks_8.18.2_linux_x64.tar.gz | tar -xz -C /tmp

# Scan for secrets
/tmp/gitleaks detect --redact --config=gitleaks.toml --source .

# Expected output: "Finding: 0" (clean)
```

**Automated scanning:**
- GitHub Actions workflow: `.github/workflows/secret-scan.yml`
- Runs on every push/PR
- Blocks merge if secrets detected

### What If I Accidentally Commit a Secret?

**Immediate actions:**
1. **Revoke the exposed token** (GitHub settings, Figma settings)
2. **Generate a new token** and update `.env`
3. **Remove from git history** (see git history cleanup section below)
4. **Notify security team** if production credentials were exposed

**For more details, see:** `grand audit/phase1_secrets_plan.md`

---

## Development Workflow

### Activate Environment (every session)
```bash
source .venv/bin/activate
```

### Run Tests
```bash
# All tests
pytest services/analysis-service/tests/

# Specific test file
pytest services/analysis-service/tests/test_health.py -v

# Fast mode (quiet)
pytest services/analysis-service/tests/ -q
```

### Start Development Server
```bash
cd services/analysis-service
uvicorn app.main:app --reload
```

### Code Quality Tools
```bash
# Format code
black services/

# Sort imports
isort services/

# Lint
ruff check services/

# Type check
mypy services/analysis-service/
```

---

## Permanent Activation (Optional)

Add to `~/.bashrc` to auto-activate:

```bash
# Auto-activate saju-engine virtualenv when in project directory
if [ -f "$HOME/saju-engine/.venv/bin/activate" ]; then
    source "$HOME/saju-engine/.venv/bin/activate"
fi
```

Or use `direnv` for automatic activation:

```bash
# Install direnv
sudo apt-get install direnv  # Ubuntu/Debian

# Create .envrc in project root
echo "source .venv/bin/activate" > .envrc

# Allow direnv for this directory
direnv allow .
```

---

## Comparison: pip vs. Poetry

| Aspect | pip + venv | Poetry 1.8.4 |
|--------|------------|--------------|
| **Install Time** | 30-90s | 19s (lock) + 19s (install) |
| **Startup Time** | <5s | 4.8s (sandbox) / 5-6 min (production) |
| **Disk Space** | ~200MB (.venv) | ~200MB (.venv) + 50MB (.poetry-1.8) |
| **Complexity** | Low (standard Python) | Medium (custom tool) |
| **Compatibility** | Universal | Version-specific |
| **Lock File** | requirements.txt | poetry.lock (binary format) |
| **Offline Support** | ✅ (with wheel cache) | ✅ (with installer) |

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'app'`

**Solution:** Run the setup script:
```bash
python scripts/setup_dev_environment.py
```

This creates `.venv/lib/python3.12/site-packages/saju_services.pth` with service paths.

### Issue: Tests fail with import errors

**Solution:** Activate virtualenv first:
```bash
source .venv/bin/activate
pytest services/analysis-service/tests/
```

### Issue: Slow installation on Windows/WSL2

**Cause:** Slow filesystem I/O on `/mnt/c/` (Windows NTFS)

**Solution:** Move repo to native Linux filesystem:
```bash
cp -r /mnt/c/Users/PW1234/.vscode/sajuv2/saju-engine ~/saju-engine
cd ~/saju-engine
# Repeat setup steps
```

### Issue: `pytest` command not found

**Solution:** Activate virtualenv or use full path:
```bash
source .venv/bin/activate
# OR
.venv/bin/pytest services/analysis-service/tests/
```

---

## Updating Dependencies

### Add New Package
```bash
# Add to requirements/dev.txt
echo "new-package==1.0.0" >> requirements/dev.txt

# Install
pip install -r requirements.txt
```

### Update Existing Package
```bash
# Edit requirements/dev.txt manually
# Change version number

# Reinstall
pip install -r requirements.txt --upgrade
```

### Pin Current Versions
```bash
# Generate exact versions of all installed packages
pip freeze > requirements-lock.txt
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Setup monorepo paths
        run: |
          source .venv/bin/activate
          python scripts/setup_dev_environment.py

      - name: Run tests
        run: |
          source .venv/bin/activate
          pytest services/analysis-service/tests/ -v
```

---

## Migration from Poetry

If you have an existing Poetry setup:

```bash
# 1. Export Poetry dependencies (optional, for verification)
poetry export -f requirements.txt --without-hashes > requirements-poetry.txt

# 2. Remove Poetry artifacts
rm -rf .poetry-1.8/ poetry.lock

# 3. Keep existing virtualenv OR create new one
# Option A: Keep existing
source .venv/bin/activate

# Option B: Fresh start
rm -rf .venv/
python3 -m venv .venv
source .venv/bin/activate

# 4. Install from requirements.txt
pip install -r requirements.txt

# 5. Setup service paths
python scripts/setup_dev_environment.py

# 6. Verify
pytest services/analysis-service/tests/test_health.py -q
```

---

## Why pip + venv?

**Advantages:**
1. **Faster** - No lock file resolution, direct dependency installation
2. **Simpler** - Standard Python tooling, no third-party tools
3. **Universal** - Works everywhere Python works
4. **Transparent** - Plain text requirements.txt, easy to audit
5. **Lightweight** - No additional binaries or tools to install

**Disadvantages:**
1. **No automatic lock file** - Must manually pin versions
2. **Basic dependency resolution** - pip's resolver is simpler than Poetry's
3. **No build system** - For publishing packages, need setuptools separately

**For this project:** Development workflow benefits outweigh packaging features.

---

## Performance Benchmark

**Test:** Install dependencies + run health check test

**Results:**
```
pip + venv:
- Install: 60-90s (first time) / 10-20s (cached)
- Startup: 3-5s
- Test run: 0.5s
- Total: ~70s first time, ~15s subsequent

Poetry 1.8.4:
- Install: 38s (lock + install)
- Startup: 4.8s (sandbox) / 5-6 min (production WSL2)
- Test run: 0.5s
- Total: ~43s (sandbox) / 6+ min (production)
```

**Conclusion:** pip is comparable or faster, with more predictable performance.

---

## Git History Cleanup (Optional)

If you need to remove secrets from git history (e.g., after accidentally committing `.env`):

### Prerequisites

**⚠️ WARNING:** This rewrites git history. All team members must re-clone after force-push.

**Before starting:**
1. ✅ Create backup: `git clone saju-engine saju-engine-backup`
2. ✅ Notify team members
3. ✅ Ensure you have latest changes: `git pull`

### Install git-filter-repo

```bash
# Option 1: pip
pip install git-filter-repo

# Option 2: Download directly
curl -o /tmp/git-filter-repo https://raw.githubusercontent.com/newren/git-filter-repo/main/git-filter-repo
chmod +x /tmp/git-filter-repo
```

### Remove Secret Files from History

```bash
# Remove .env files
git filter-repo --path .env --invert-paths
git filter-repo --path .env.local --invert-paths

# Remove Claude settings with secrets
git filter-repo --path .claude/settings.local.json --invert-paths

# Or use a paths file for batch removal
cat > /tmp/paths-to-remove.txt <<EOF
.env
.env.local
.claude/settings.local.json
EOF

git filter-repo --paths-from /tmp/paths-to-remove.txt --invert-paths
```

### Verify Cleanup

```bash
# Re-scan with gitleaks
/tmp/gitleaks detect --redact --config=gitleaks.toml --source .

# Check specific files are gone from history
git log --all --full-history -- .env
# Should return: "fatal: ambiguous argument '.env': unknown revision or path"
```

### Force Push (Point of No Return)

```bash
# Force push to remote (requires write access)
git push origin --force --all
git push origin --force --tags

# Verify remote is clean
git clone https://github.com/dan914/saju-engine.git /tmp/verify-clean
cd /tmp/verify-clean
/tmp/gitleaks detect --redact --source .
```

### Team Coordination

After force-push, all team members must:

```bash
# 1. Save local uncommitted changes
git stash

# 2. Delete local repo
cd ..
rm -rf saju-engine

# 3. Fresh clone
git clone https://github.com/dan914/saju-engine.git
cd saju-engine

# 4. Restore uncommitted changes
git stash pop
```

**Reference:** `grand audit/phase1_secrets_plan.md` (WI-2.4)

---

**Prepared by:** Claude Code
**Date:** 2025-11-04
**Recommended for:** All development and CI/CD workflows
