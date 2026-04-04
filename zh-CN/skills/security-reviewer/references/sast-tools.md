# SAST 工具

## JavaScript/TypeScript

```bash
# Dependency vulnerabilities
npm audit
npm audit --json > npm-audit.json

# ESLint security plugin
npm install eslint-plugin-security --save-dev
npx eslint --ext .js,.ts . --plugin security

# Snyk
npx snyk test
npx snyk code test
```

## Python

```bash
# Bandit - Python SAST
pip install bandit
bandit -r . -f json -o bandit-report.json
bandit -r . -ll  # Only high severity

# Safety - Dependency check
pip install safety
safety check
safety check -r requirements.txt --json > safety-report.json

# Pyup Safety
pip install pyupio-safety
pyupio-safety check
```

## Go

```bash
# GoSec - Go security checker
go install github.com/securego/gosec/v2/cmd/gosec@latest
gosec ./...
gosec -fmt=json -out=gosec-report.json ./...

# Go vulnerability database
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

## 多语言工具

```bash
# Semgrep - Universal SAST
pip install semgrep
semgrep --config=auto .
semgrep --config=p/security-audit .
semgrep --config=p/owasp-top-ten .

# Trivy - Comprehensive scanner
brew install trivy
trivy fs .
trivy fs --security-checks vuln,secret,config .

# SonarQube (requires server)
sonar-scanner -Dsonar.projectKey=myproject
```

## CI/CD 集成

### GitHub Actions

```yaml
- name: Run Semgrep
  uses: returntocorp/semgrep-action@v1
  with:
    config: p/security-audit

- name: Run npm audit
  run: npm audit --audit-level=high

- name: Run Trivy
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    severity: 'CRITICAL,HIGH'
```

### GitLab CI

```yaml
security-scan:
  image: returntocorp/semgrep
  script:
    - semgrep --config=auto --json -o semgrep.json .
  artifacts:
    reports:
      sast: semgrep.json
```

## 快速参考

| 语言 | 主要工具 | 依赖项检查 |
|----------|--------------|------------------|
| JavaScript | ESLint + security | npm audit |
| TypeScript | ESLint + security | npm audit |
| Python | Bandit | Safety |
| Go | GoSec | govulncheck |
| Java | SpotBugs | OWASP Dependency-Check |
| Ruby | Brakeman | bundler-audit |

| 工具 | 优势 | 最适合 |
|------|-----------|----------|
| Semgrep | 多语言、自定义规则 | 通用 SAST |
| Trivy | 容器 + 代码 + 密钥 | 全面扫描 |
| Bandit | Python 专用 | Python 项目 |
| GoSec | Go 专用 | Go 项目 |
| npm audit | 内置、快速 | Node.js 依赖 |