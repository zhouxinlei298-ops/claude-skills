# MCP 服务器设置

---

## 服务器选项概览

### 官方 Atlassian MCP 服务器

Atlassian 为 Cloud 产品提供官方 MCP 服务器：

```bash
# Install via npm
npm install -g @anthropic/mcp-atlassian

# Or use npx directly
npx @anthropic/mcp-atlassian
```

**功能：**
- Jira Cloud 和 Confluence Cloud 集成
- OAuth 2.1 认证流程
- 问题和页面的读/写操作
- JQL 和 CQL 查询支持

### 开源替代方案

**mcp-atlassian (sooperset)** - 功能最丰富的社区选项：
```bash
# Install with uv (recommended)
uv tool install mcp-atlassian

# Or with pip
pip install mcp-atlassian
```

**atlassian-mcp (xuanxt)** - 基于 TypeScript 的替代方案：
```bash
npm install atlassian-mcp
```

### 比较矩阵

| 功能 | 官方 | sooperset | xuanxt |
|------|------|-----------|--------|
| Jira Cloud | 是 | 是 | 是 |
| Jira Server/DC | 否 | 是 | 有限 |
| Confluence Cloud | 是 | 是 | 是 |
| Confluence Server/DC | 否 | 是 | 否 |
| OAuth 2.1 | 是 | 是 | 否 |
| API Token 认证 | 是 | 是 | 是 |
| PAT (Server) | 否 | 是 | 否 |
| 速率限制 | 内置 | 可配置 | 手动 |

## Claude Desktop 配置

### 基本设置

编辑您的 Claude Desktop 配置文件：

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/claude/claude_desktop_config.json`

### 配置示例

**使用 OAuth 的官方服务器：**
```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["@anthropic/mcp-atlassian"],
      "env": {
        "ATLASSIAN_SITE_URL": "https://your-company.atlassian.net",
        "ATLASSIAN_AUTH_TYPE": "oauth"
      }
    }
  }
}
```

**使用 API Token 的 sooperset 服务器：**
```json
{
  "mcpServers": {
    "atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "CONFLUENCE_URL": "https://your-company.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your-email@company.com",
        "CONFLUENCE_API_TOKEN": "your-api-token",
        "JIRA_URL": "https://your-company.atlassian.net",
        "JIRA_USERNAME": "your-email@company.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

**使用 PAT 的 Server/Data Center：**
```json
{
  "mcpServers": {
    "atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://jira.internal.company.com",
        "JIRA_PERSONAL_TOKEN": "your-personal-access-token",
        "CONFLUENCE_URL": "https://confluence.internal.company.com",
        "CONFLUENCE_PERSONAL_TOKEN": "your-personal-access-token"
      }
    }
  }
}
```

## 环境变量参考

### Jira 配置

| 变量 | 描述 | 必需 |
|------|------|------|
| `JIRA_URL` | Jira 实例的基础 URL | 是 |
| `JIRA_USERNAME` | Cloud 使用邮箱，Server 使用用户名 | 仅 Cloud |
| `JIRA_API_TOKEN` | API Token（Cloud） | 仅 Cloud |
| `JIRA_PERSONAL_TOKEN` | PAT（Server/DC） | 仅 Server |
| `JIRA_SSL_VERIFY` | 验证 SSL 证书（默认：true） | 否 |

### Confluence 配置

| 变量 | 描述 | 必需 |
|------|------|------|
| `CONFLUENCE_URL` | Cloud 的基础 URL（带 /wiki 后缀） | 是 |
| `CONFLUENCE_USERNAME` | Cloud 使用邮箱 | 仅 Cloud |
| `CONFLUENCE_API_TOKEN` | API Token（Cloud） | 仅 Cloud |
| `CONFLUENCE_PERSONAL_TOKEN` | PAT（Server/DC） | 仅 Server |

### 高级选项

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `MCP_LOG_LEVEL` | 日志详细程度（DEBUG, INFO, WARN, ERROR） | INFO |
| `MCP_TIMEOUT` | 请求超时时间（秒） | 30 |
| `MCP_MAX_RETRIES` | 最大重试次数 | 3 |
| `MCP_RATE_LIMIT` | 每秒请求数 | 10 |

## 验证和测试

### 检查服务器状态

```bash
# Test official server
npx @anthropic/mcp-atlassian --version

# Test sooperset server
uvx mcp-atlassian --help

# Verify environment variables
env | grep -E "(JIRA|CONFLUENCE)_"
```

### 测试连接

创建一个简单的测试脚本：

```typescript
// test-connection.ts
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function testConnection() {
  const transport = new StdioClientTransport({
    command: "uvx",
    args: ["mcp-atlassian"],
    env: process.env,
  });

  const client = new Client(
    { name: "test-client", version: "1.0.0" },
    { capabilities: {} }
  );

  await client.connect(transport);

  // List available tools
  const tools = await client.listTools();
  console.log("Available tools:", tools.tools.map(t => t.name));

  // Test a simple read operation
  const result = await client.callTool({
    name: "jira_get_issue",
    arguments: { issue_key: "TEST-1" }
  });
  console.log("Test result:", result);

  await client.close();
}

testConnection().catch(console.error);
```

## 何时使用每个服务器

**选择官方服务器时：**
- 仅使用 Atlassian Cloud 产品
- 需要 OAuth 2.1 合规性
- 需要官方支持
- 为企业部署构建

**选择 sooperset 时：**
- 需要 Server/Data Center 支持
- 想要 PAT 认证
- 需要高级过滤功能
- 需要 Jira 和 Confluence

**选择 xuanxt 时：**
- 想要 TypeScript 原生实现
- 构建自定义扩展
- 需要最少的依赖项

## 故障排除

### 常见问题

**"Connection refused" 错误：**
```bash
# Check if server is running
ps aux | grep mcp-atlassian

# Verify URL is reachable
curl -I https://your-company.atlassian.net

# Check firewall/proxy settings
echo $HTTP_PROXY $HTTPS_PROXY
```

**"Authentication failed" 错误：**
```bash
# Verify API token is valid (cloud)
curl -u "email@company.com:API_TOKEN" \
  "https://your-company.atlassian.net/rest/api/3/myself"

# Verify PAT is valid (server)
curl -H "Authorization: Bearer YOUR_PAT" \
  "https://jira.internal.company.com/rest/api/2/myself"
```

**"Rate limit exceeded" 错误：**
```json
{
  "mcpServers": {
    "atlassian": {
      "env": {
        "MCP_RATE_LIMIT": "5"
      }
    }
  }
}
```

### 调试模式

启用详细日志记录：

```json
{
  "mcpServers": {
    "atlassian": {
      "env": {
        "MCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## 安全最佳实践

1. **绝不提交凭据** - 使用环境变量或 secrets 管理
2. **定期轮换 API tokens** - 设置 90 天轮换的日历提醒
3. **使用最小 scopes** - 仅请求必要的权限
4. **启用审计日志** - 跟踪 API 使用情况以符合合规要求
5. **限制网络访问** - 尽可能使用允许列表

## 相关参考

- `authentication-patterns.md` - OAuth 2.1 和 API Token 设置详情
- `jira-queries.md` - 连接建立后的 JQL 语法
- `confluence-operations.md` - CQL 和页面操作