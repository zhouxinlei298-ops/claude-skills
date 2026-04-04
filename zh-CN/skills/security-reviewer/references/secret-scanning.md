# 密钥扫描

## Gitleaks

```bash
# Install
brew install gitleaks

# Scan current directory
gitleaks detect --source . --verbose

# Scan with report
gitleaks detect --source . -f json -r gitleaks-report.json

# Scan git history
gitleaks detect --source . --log-opts="--all"

# Use baseline (ignore known)
gitleaks detect --baseline-path .gitleaks-baseline.json
```

## TruffleHog

```bash
# Install
pip install trufflehog

# Scan filesystem
trufflehog filesystem .

# Scan git repo
trufflehog git file://. --since-commit HEAD~100

# Scan with JSON output
trufflehog filesystem . --json > trufflehog-report.json
```

## 手动 Grep 模式

```bash
# Common secret patterns
grep -rn "api_key\|apikey\|api-key" --include="*.{ts,js,py}" .
grep -rn "secret\|password\|passwd" --include="*.{ts,js,py}" .
grep -rn "private_key\|privatekey" --include="*.{ts,js,py}" .
grep -rn "access_token\|accesstoken" --include="*.{ts,js,py}" .

# AWS credentials
grep -rn "AKIA[0-9A-Z]{16}" .
grep -rn "aws_secret_access_key" .

# Base64 encoded (potential secrets)
grep -rn "[A-Za-z0-9+/]{40,}=" .

# JWT tokens
grep -rn "eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\." .
```

## 常见密钥模式

| 类型 | 模式 | 示例 |
|------|---------|---------|
| AWS 访问密钥 | `AKIA[0-9A-Z]{16}` | AKIAIOSFODNN7EXAMPLE |
| AWS 密钥 | 40 字符 base64 | wJalrXUtnFEMI/K7MDENG... |
| GitHub 令牌 | `ghp_[A-Za-z0-9]{36}` | ghp_xxxxxxxxxxxx |
| Slack 令牌 | `xox[baprs]-` | xoxb-xxx-xxx |
| Stripe 密钥 | `sk_live_[A-Za-z0-9]{24}` | sk_live_xxxx |
| 私钥 | `-----BEGIN.*PRIVATE KEY-----` | RSA/EC 密钥 |
| JWT | `eyJ[A-Za-z0-9_-]*\.eyJ` | 编码令牌 |

## Pre-commit 钩子

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

## CI/CD 集成

```yaml
# GitHub Actions
- name: Gitleaks
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# GitLab CI
secret_detection:
  image: zricethezav/gitleaks
  script:
    - gitleaks detect --source . -f sarif -r gl-secret-detection-report.sarif
  artifacts:
    reports:
      secret_detection: gl-secret-detection-report.sarif
```

## 修复步骤

1. **立即轮换** - 考虑密钥已泄露
2. **从历史中删除** - 使用 git filter-branch 或 BFG
3. **添加到 .gitignore** - 防止未来提交
4. **使用环境变量** - 移至环境
5. **使用密钥管理器** - AWS Secrets Manager、Vault

```bash
# Remove from git history (BFG)
bfg --replace-text passwords.txt repo.git

# Or git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/secret" \
  --prune-empty --tag-name-filter cat -- --all
```

## 快速参考

| 工具 | 最适合 | 速度 |
|------|----------|-------|
| Gitleaks | Git 历史 | 快 |
| TruffleHog | 深度扫描 | 中等 |
| grep | 快速检查 | 快 |
| GitHub Secret Scanning | GitHub 仓库 | 自动 |