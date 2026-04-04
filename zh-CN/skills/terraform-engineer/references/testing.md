# Terraform 测试策略

## Terraform Plan 验证

**基本 Plan 工作流**
```bash
# Initialize and validate syntax
terraform init
terraform fmt -check
terraform validate

# Plan with output
terraform plan -out=tfplan

# Show plan in JSON for automated review
terraform show -json tfplan | jq .

# Apply specific plan
terraform apply tfplan
```

**使用变量文件的 Plan**
```bash
# Plan with specific tfvars
terraform plan -var-file="production.tfvars"

# Plan with inline variables
terraform plan -var="instance_count=5"

# Plan with multiple var files
terraform plan \
  -var-file="common.tfvars" \
  -var-file="production.tfvars"
```

**Plan 分析**
```bash
# Resource targeting for specific resources
terraform plan -target=aws_vpc.main

# Refresh only (check drift)
terraform plan -refresh-only

# Destroy plan
terraform plan -destroy

# Save plan output
terraform plan -out=tfplan 2>&1 | tee plan-output.txt
```

## Terraform Test (1.6+)

**测试文件结构**
```
tests/
├── unit/
│   ├── vpc_test.tftest.hcl
│   └── security_group_test.tftest.hcl
└── integration/
    └── complete_test.tftest.hcl
```

**基本测试**
```hcl
# tests/vpc_test.tftest.hcl
run "validate_vpc_cidr" {
  command = plan

  variables {
    cidr_block = "10.0.0.0/16"
    name       = "test-vpc"
  }

  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "VPC CIDR block did not match expected value"
  }

  assert {
    condition     = aws_vpc.main.enable_dns_hostnames == true
    error_message = "DNS hostnames should be enabled"
  }
}

run "validate_tags" {
  command = plan

  variables {
    cidr_block = "10.0.0.0/16"
    name       = "test-vpc"
    tags = {
      Environment = "test"
    }
  }

  assert {
    condition     = aws_vpc.main.tags["Environment"] == "test"
    error_message = "Environment tag not set correctly"
  }
}
```

**集成测试**
```hcl
# tests/integration/complete_test.tftest.hcl
run "create_full_stack" {
  command = apply

  variables {
    cidr_block = "10.0.0.0/16"
    name       = "integration-test"

    private_subnets = {
      app = { cidr_block = "10.0.1.0/24", az = "us-east-1a" }
    }
  }

  assert {
    condition     = length(aws_subnet.private) == 1
    error_message = "Should create exactly one private subnet"
  }

  assert {
    condition     = output.vpc_id != ""
    error_message = "VPC ID should not be empty"
  }
}
```

**运行测试**
```bash
# Run all tests
terraform test

# Run specific test file
terraform test tests/vpc_test.tftest.hcl

# Verbose output
terraform test -verbose

# Keep test resources (for debugging)
terraform test -no-cleanup
```

## Terratest (基于 Go 的测试)

**测试结构**
```
tests/
├── go.mod
├── go.sum
└── vpc_test.go
```

**go.mod**
```go
module github.com/example/terraform-modules/tests

go 1.21

require (
    github.com/gruntwork-io/terratest v0.45.0
    github.com/stretchr/testify v1.8.4
)
```

**基本 Terratest**
```go
// tests/vpc_test.go
package test

import (
    "testing"

    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVPCCreation(t *testing.T) {
    t.Parallel()

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../examples/complete",

        Vars: map[string]interface{}{
            "name":       "test-vpc",
            "cidr_block": "10.0.0.0/16",
        },

        EnvVars: map[string]string{
            "AWS_DEFAULT_REGION": "us-east-1",
        },
    })

    defer terraform.Destroy(t, terraformOptions)

    terraform.InitAndApply(t, terraformOptions)

    vpcID := terraform.Output(t, terraformOptions, "vpc_id")
    assert.NotEmpty(t, vpcID)

    vpcCIDR := terraform.Output(t, terraformOptions, "vpc_cidr_block")
    assert.Equal(t, "10.0.0.0/16", vpcCIDR)
}
```

**带有 AWS SDK 的高级 Terratest**
```go
package test

import (
    "testing"

    "github.com/aws/aws-sdk-go/aws"
    "github.com/aws/aws-sdk-go/service/ec2"
    "github.com/gruntwork-io/terratest/modules/terraform"
    aws_helper "github.com/gruntwork-io/terratest/modules/aws"
    "github.com/stretchr/testify/assert"
)

func TestVPCConfiguration(t *testing.T) {
    t.Parallel()

    awsRegion := "us-east-1"

    terraformOptions := &terraform.Options{
        TerraformDir: "../examples/complete",
        Vars: map[string]interface{}{
            "name":       "test-vpc",
            "cidr_block": "10.0.0.0/16",
        },
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    vpcID := terraform.Output(t, terraformOptions, "vpc_id")

    // Verify VPC configuration using AWS SDK
    vpc := aws_helper.GetVpcById(t, vpcID, awsRegion)
    assert.Equal(t, "10.0.0.0/16", *vpc.CidrBlock)
    assert.True(t, *vpc.EnableDnsSupport)
    assert.True(t, *vpc.EnableDnsHostnames)

    // Verify tags
    tags := convertEC2TagsToMap(vpc.Tags)
    assert.Equal(t, "test-vpc", tags["Name"])
}

func convertEC2TagsToMap(tags []*ec2.Tag) map[string]string {
    result := make(map[string]string)
    for _, tag := range tags {
        result[*tag.Key] = *tag.Value
    }
    return result
}
```

**运行 Terratest**
```bash
cd tests
go mod download
go test -v -timeout 30m
```

## 策略即代码 - OPA/Sentinel

**Open Policy Agent (OPA)**

**policy.rego**
```rego
package terraform.analysis

import input as tfplan

# Deny if resources are not tagged
deny[msg] {
    r := tfplan.resource_changes[_]
    r.change.actions[_] == "create"
    not r.change.after.tags.Environment
    msg := sprintf("Resource %s is missing Environment tag", [r.address])
}

# Require encryption for S3 buckets
deny[msg] {
    r := tfplan.resource_changes[_]
    r.type == "aws_s3_bucket"
    r.change.actions[_] == "create"
    not r.change.after.server_side_encryption_configuration
    msg := sprintf("S3 bucket %s must have encryption enabled", [r.address])
}

# Ensure VPC flow logs are enabled
deny[msg] {
    r := tfplan.resource_changes[_]
    r.type == "aws_vpc"
    r.change.actions[_] == "create"
    vpc_id := r.change.after.id
    not has_flow_log(vpc_id)
    msg := sprintf("VPC %s must have flow logs enabled", [r.address])
}

has_flow_log(vpc_id) {
    r := tfplan.resource_changes[_]
    r.type == "aws_flow_log"
    r.change.after.vpc_id == vpc_id
}
```

**运行 OPA 策略**
```bash
# Generate plan in JSON
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json

# Run OPA policy check
opa eval -i tfplan.json -d policy.rego "data.terraform.analysis.deny"
```

**Conftest (用于测试的 OPA 包装器)**
```bash
# Install conftest
brew install conftest

# Test plan against policies
conftest test tfplan.json

# With specific namespace
conftest test tfplan.json --namespace terraform.analysis
```

## TFLint

**安装和配置**
```bash
# Install tflint
brew install tflint

# Initialize tflint plugins
tflint --init
```

**.tflint.hcl**
```hcl
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

plugin "aws" {
  enabled = true
  version = "0.27.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_naming_convention" {
  enabled = true

  format = "snake_case"
}

rule "terraform_required_version" {
  enabled = true
}

rule "terraform_required_providers" {
  enabled = true
}

rule "aws_instance_invalid_type" {
  enabled = true
}

rule "aws_s3_bucket_encryption" {
  enabled = true
}
```

**运行 TFLint**
```bash
# Run linter
tflint

# With specific config
tflint --config=.tflint.hcl

# Recursive (all subdirectories)
tflint --recursive

# Output format
tflint --format=json
```

## Pre-commit 钩子

**.pre-commit-config.yaml**
```yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.83.6
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
        args:
          - --args=--config=__GIT_WORKING_DIR__/.tflint.hcl
      - id: terraform_docs
        args:
          - --hook-config=--path-to-file=README.md
          - --hook-config=--add-to-existing-file=true
      - id: terraform_checkov
        args:
          - --args=--quiet
          - --args=--skip-check CKV_AWS_*
```

**设置**
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run -a
```

## CI/CD 管道测试

**GitHub Actions 示例**
```yaml
name: Terraform Test

on: [pull_request]

jobs:
  terraform-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.6.0

      - name: Terraform Format
        run: terraform fmt -check -recursive

      - name: Terraform Init
        run: terraform init

      - name: Terraform Validate
        run: terraform validate

      - name: TFLint
        uses: terraform-linters/setup-tflint@v3
        with:
          tflint_version: latest

      - name: Run TFLint
        run: tflint --recursive

      - name: Terraform Test
        run: terraform test

      - name: Checkov
        uses: bridgecrewio/checkov-action@master
        with:
          directory: .
          framework: terraform
```

## 最佳实践

- 每次提交前运行 `terraform validate`
- 使用 `terraform test` 进行单元测试和集成测试
- 为安全合规实现策略即代码
- 在 CI/CD 管道中运行 TFLint
- 使用 pre-commit 钩子进行自动检查
- 对关键基础设施使用 Terratest 测试模块
- 应用前始终审查计划输出
- 在隔离环境中测试 provider 升级
- 记录测试场景和预期结果
- 在拉取请求工作流中自动化测试
