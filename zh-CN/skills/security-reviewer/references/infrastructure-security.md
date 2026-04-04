# 基础设施安全

## DevSecOps 集成

### CI/CD 安全管道

```yaml
# GitHub Actions - Security scanning
name: Security Pipeline
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: returntocorp/semgrep-action@v1
      - uses: gitleaks/gitleaks-action@v2
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
```

### 基础设施即代码安全

```bash
# Terraform/CloudFormation scanning
checkov -d terraform/ --framework terraform
tfsec terraform/
terrascan scan -d terraform/

# Kubernetes manifest scanning
kubesec scan deployment.yaml
```

## 云安全控制

### AWS 安全加固

```bash
# Enable security services
aws guardduty create-detector --enable
aws securityhub enable-security-hub
aws cloudtrail create-trail --name security-trail --s3-bucket-name logs

# Check S3 bucket security
aws s3api list-buckets --query "Buckets[].Name" | \
  xargs -I {} aws s3api get-bucket-acl --bucket {}

# IAM password policy
aws iam update-account-password-policy \
  --minimum-password-length 14 \
  --require-symbols --require-numbers \
  --require-uppercase-characters --require-lowercase-characters
```

### Azure 安全

```bash
# Enable Security Center
az security auto-provisioning-setting update --name default --auto-provision on

# Enable disk encryption
az vm encryption enable --resource-group myRG --name myVM --disk-encryption-keyvault myKV
```

### GCP 安全

```bash
# Enable Security Command Center
gcloud services enable securitycenter.googleapis.com

# Enable VPC Flow Logs
gcloud compute networks subnets update SUBNET --enable-flow-logs
```

## 容器安全

### 安全 Dockerfile

```dockerfile
FROM node:18-alpine
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
WORKDIR /app
COPY --chown=nodejs:nodejs package*.json ./
RUN npm ci --only=production
USER nodejs
EXPOSE 3000
HEALTHCHECK --interval=30s CMD node healthcheck.js
CMD ["node", "server.js"]
```

### Kubernetes 安全

```yaml
# Pod Security Standards
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: [ALL]
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"
---
# Network Policy - Default deny
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

## 合规自动化

### CIS 基准扫描

```bash
# Docker CIS benchmark
docker run --net host --pid host --cap-add audit_control \
  -v /var/lib:/var/lib -v /var/run/docker.sock:/var/run/docker.sock \
  docker/docker-bench-security

# Kubernetes CIS benchmark
kube-bench run --targets master,node

# Linux system hardening
lynis audit system --quick
```

### 合规即代码（InSpec）

```ruby
# controls/baseline.rb
control 'ssh-hardening' do
  impact 1.0
  title 'SSH Security Configuration'

  describe sshd_config do
    its('Protocol') { should eq '2' }
    its('PermitRootLogin') { should eq 'no' }
    its('PasswordAuthentication') { should eq 'no' }
  end
end

control 'encryption-at-rest' do
  impact 1.0
  title 'S3 Encryption Enabled'

  describe aws_s3_bucket('my-bucket') do
    it { should have_default_encryption_enabled }
  end
end
```

## 密钥管理

### HashiCorp Vault

```bash
# Initialize and configure
vault operator init
vault secrets enable -path=secret kv-v2

# Store secrets
vault kv put secret/app/config api_key="secret123"

# Dynamic database credentials
vault secrets enable database
vault write database/config/postgresql \
  plugin_name=postgresql-database-plugin \
  allowed_roles="app" \
  connection_url="postgresql://{{username}}:{{password}}@localhost:5432/" \
  username="vault" password="vaultpass"

vault write database/roles/app \
  db_name=postgresql \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}';" \
  default_ttl="1h" max_ttl="24h"
```

### Kubernetes Secrets 与 External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      auth:
        kubernetes:
          role: "app-role"
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
  target:
    name: app-secrets
  data:
  - secretKey: api_key
    remoteRef:
      key: secret/app/config
      property: api_key
```

## 安全监控

### SIEM 日志传输（Filebeat）

```yaml
filebeat.inputs:
- type: log
  paths:
    - /var/log/auth.log
    - /var/log/nginx/*.log
  fields:
    environment: production

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "security-logs-%{+yyyy.MM.dd}"
```

## 快速参考

| 领域 | 工具 | 用途 |
|------|------|---------|
| 云安全 | Prowler, ScoutSuite | AWS/Azure/GCP 审计 |
| 容器 | Trivy, Clair | 镜像扫描 |
| IaC | Checkov, tfsec | Terraform/CloudFormation |
| 密钥 | Vault, Sealed Secrets | 密钥管理 |
| 合规 | InSpec, OpenSCAP | CIS 基准 |
| 监控 | ELK, Splunk | SIEM |

| 框架 | 重点 | 关键控制 |
|-----------|-------|--------------|
| SOC 2 | 安全控制 | 访问、加密、监控 |
| ISO 27001 | ISMS | 策略、风险、审计 |
| PCI DSS | 支付安全 | 网络分段、加密 |
| HIPAA | 医疗保健 | 加密、访问日志 |
| GDPR | 数据隐私 | 同意、保留、DLP |