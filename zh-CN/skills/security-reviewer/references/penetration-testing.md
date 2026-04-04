# 渗透测试

## 侦察

### 被动信息收集

```bash
# DNS enumeration
dig example.com ANY
nslookup -type=any example.com

# Subdomain discovery
subfinder -d example.com
amass enum -d example.com

# Certificate transparency
curl -s "https://crt.sh/?q=%.example.com&output=json"
```

### 主动扫描

```bash
# Port scanning
nmap -sV -p- target.com
nmap -sC -sV -oA scan target.com

# Web technology detection
whatweb target.com
```

## Web 应用测试

### 身份验证与授权

```bash
# Session analysis - Check for:
# - Session timeout, Secure/HttpOnly flags
# - Session fixation, concurrent sessions

# IDOR testing
GET /api/users/123  # Your ID
GET /api/users/124  # Another user - should fail

# Privilege escalation
GET /api/admin/users  # As standard user
```

### 输入验证

```bash
# SQL injection
sqlmap -u "http://target.com/search?q=test" --batch

# XSS payloads
<script>alert(document.domain)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>

# Command injection
; ls -la
| whoami
$(whoami)

# XXE
<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root>&xxe;</root>
```

## API 安全测试

### JWT & Token 安全

```bash
# Decode JWT
echo "eyJ..." | base64 -d

# Test none algorithm
# Modify header: {"alg": "none"}

# Weak secret brute force
hashcat -m 16500 jwt.txt wordlist.txt
```

### 速率限制 & 数据暴露

```bash
# Test rate limits
for i in {1..1000}; do
  curl https://api.target.com/login -d "user=test&pass=test"
done

# Check for excessive data exposure
GET /api/users/me
# Look for: password hashes, internal IDs, sensitive PII

# Mass assignment
POST /api/users/profile
{"email": "new@email.com", "isAdmin": true}
```

## 网络渗透

### 权限提升（Linux）

```bash
# SUID binaries
find / -perm -4000 -type f 2>/dev/null

# Sudo permissions
sudo -l

# Writable paths in PATH
echo $PATH | tr ':' '\n' | xargs -I {} ls -ld {}

# Kernel exploits
uname -a
searchsploit linux kernel $(uname -r)
```

### 横向移动

```bash
# Network enumeration
arp -a
netstat -ant

# Service discovery
nmap -sV 192.168.1.0/24

# Credential harvesting
grep -r "password" /home/*/
cat ~/.bash_history | grep -i "pass\|pwd\|secret"
```

## 移动应用测试

### Android

```bash
# Decompile APK
apktool d app.apk
jadx -d output app.apk

# Check for secrets
grep -r "api_key\|secret\|password" .

# Insecure storage
adb shell
run-as com.app.package
find . -type f -exec cat {} \;
```

### iOS

```bash
# Class dump
class-dump App.app

# Check data storage
sqlite3 /var/mobile/Applications/.../Library/Caches/data.db
```

## 云安全测试

### AWS

```bash
# S3 bucket enumeration
aws s3 ls s3://bucket-name --no-sign-request
aws s3api get-bucket-acl --bucket bucket-name

# IAM enumeration
aws iam get-user
aws iam list-attached-user-policies --user-name username
```

### 容器 & Kubernetes

```bash
# Docker escape testing
docker inspect container_id | grep -i privileged
docker inspect container_id | grep -A 5 Mounts

# Kubernetes
kubectl get pods --all-namespaces
kubectl get secrets --all-namespaces
kubectl auth can-i --list
```

## 漏洞利用验证

### 概念证明指南

```python
# Always demonstrate impact SAFELY

# SQL injection PoC
# DON'T: Extract actual data
# DO: Prove injection with sleep
payload = "' OR SLEEP(5)--"

# DON'T: Delete/modify production data
# DO: Show you COULD with SELECT
payload = "' UNION SELECT 'proof_of_concept'--"
```

### 行动规则

1. **范围验证** - 只测试授权目标
2. **时间窗口** - 遵守测试时间
3. **防止 DoS** - 避免资源耗尽
4. **数据处理** - 不要渗出真实数据
5. **发现即停止** - 不要超出概念证明
6. **立即报告** - 尽快报告关键发现
7. **文档记录** - 记录所有操作
8. **清理** - 移除测试工件

## 漏洞分类

### 严重性评分

| 严重性 | 可利用性 | 影响 | CVSS 范围 |
|----------|---------------|---------|------------|
| 严重 | 容易 | 完全 compromised | 9.0-10.0 |
| 高 | 中等 | 重要访问 | 7.0-8.9 |
| 中等 | 困难 | 有限访问 | 4.0-6.9 |
| 低 | 非常困难 | 最小影响 | 0.1-3.9 |

### 影响评估

- **严重**：远程代码执行、完整数据访问、管理员接管
- **高**：身份验证绕过、权限提升、敏感数据暴露
- **中等**：CSRF、XSS（非管理员）、信息泄露
- **低**：缺少安全头、详细错误、速率限制问题

## 测试清单

### OWASP Top 10 覆盖

- [ ] 破坏访问控制（IDOR、路径遍历）
- [ ] 加密失败（弱加密、明文）
- [ ] 注入（SQL、XSS、命令）
- [ ] 不安全设计（缺少认证流程）
- [ ] 安全错误配置（默认值、调试模式）
- [ ] 漏洞组件（过时依赖）
- [ ] 认证失败（弱密码、会话问题）
- [ ] 数据完整性（反序列化、缺少验证）
- [ ] 日志失败（缺少日志、暴露敏感数据）
- [ ] SSRF（未验证 URL）

## 快速参考

| 测试类型 | 工具 | 重点 |
|-----------|-------|-------|
| Web 应用 | Burp Suite, OWASP ZAP | OWASP Top 10 |
| API | Postman, curl | AuthN/AuthZ、数据暴露 |
| 网络 | nmap, Metasploit | 服务、漏洞利用 |
| 移动 | MobSF, Frida | 数据存储、加密 |
| 云 | ScoutSuite, Prowler | 错误配置 |

| 发现类型 | 验证方法 | 所需证据 |
|--------------|------------------|-------------------|
| SQL 注入 | 基于 sleep、基于错误 | 请求/响应、时间 |
| XSS | 警告框、DOM 操作 | 截图、载荷 |
| IDOR | 访问其他用户资源 | 两个用户账户、ID |
| 认证绕过 | 未授权访问 | 前/后截图 |
| RCE | 命令输出（安全） | whoami、id 命令输出 |