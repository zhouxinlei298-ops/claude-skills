# 认证模式

---

## 认证方法概览

| 方法 | 平台 | 使用场景 | 安全级别 |
|------|------|----------|----------|
| OAuth 2.1 | Cloud | 面向用户的应用、集成 | 最高 |
| API Token | Cloud | 个人自动化、脚本 | 中等 |
| PAT | Server/DC | Server 集成 | 中等 |
| Basic Auth | Legacy | 已弃用，避免使用 | 低 |

## OAuth 2.1 (Atlassian Cloud)

### 授权码流程

适用于代表用户操作的应用程序。

**步骤 1：注册应用**

1. 访问 [developer.atlassian.com](https://developer.atlassian.com/console/myapps/)
2. 创建新应用
3. 配置 OAuth 2.0（3LO）
4. 添加回调 URL
5. 请求必要的 scopes

**步骤 2：授权请求**

```typescript
const authUrl = new URL('https://auth.atlassian.com/authorize');
authUrl.searchParams.set('audience', 'api.atlassian.com');
authUrl.searchParams.set('client_id', CLIENT_ID);
authUrl.searchParams.set('scope', 'read:jira-work write:jira-work read:confluence-content.all write:confluence-content');
authUrl.searchParams.set('redirect_uri', REDIRECT_URI);
authUrl.searchParams.set('state', generateState());
authUrl.searchParams.set('response_type', 'code');
authUrl.searchParams.set('prompt', 'consent');

// Redirect user to authUrl.toString()
```

**步骤 3：交换代码获取令牌**

```typescript
async function exchangeCodeForToken(code: string): Promise<TokenResponse> {
  const response = await fetch('https://auth.atlassian.com/oauth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      code,
      redirect_uri: REDIRECT_URI,
    }),
  });

  if (!response.ok) {
    throw new Error(`Token exchange failed: ${response.statusText}`);
  }

  return response.json();
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  scope: string;
  token_type: 'Bearer';
}
```

**步骤 4：刷新令牌**

```typescript
async function refreshAccessToken(refreshToken: string): Promise<TokenResponse> {
  const response = await fetch('https://auth.atlassian.com/oauth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      grant_type: 'refresh_token',
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      refresh_token: refreshToken,
    }),
  });

  return response.json();
}
```

**步骤 5：获取可访问资源**

```typescript
async function getAccessibleResources(accessToken: string): Promise<Resource[]> {
  const response = await fetch(
    'https://api.atlassian.com/oauth/token/accessible-resources',
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'application/json',
      },
    }
  );

  return response.json();
}

interface Resource {
  id: string;        // Cloud ID
  name: string;      // Site name
  url: string;       // https://your-site.atlassian.net
  scopes: string[];
  avatarUrl: string;
}
```

### OAuth Scopes 参考

**Jira Scopes:**

| Scope | 描述 |
|-------|------|
| `read:jira-work` | 读取问题、项目、看板 |
| `write:jira-work` | 创建/更新问题 |
| `manage:jira-project` | 管理项目设置 |
| `manage:jira-configuration` | 管理全局设置 |
| `read:jira-user` | 读取用户配置文件 |
| `manage:jira-data-provider` | 数据提供者集成 |

**Confluence Scopes:**

| Scope | 描述 |
|-------|------|
| `read:confluence-content.all` | 读取所有内容 |
| `write:confluence-content` | 创建/更新内容 |
| `read:confluence-content.summary` | 读取内容摘要 |
| `read:confluence-space.summary` | 读取空间摘要 |
| `write:confluence-space` | 创建/管理空间 |
| `read:confluence-user` | 读取用户配置文件 |

**精细 Scopes (v2):**

```
read:issue-details:jira
write:issue:jira
read:sprint:jira-software
write:sprint:jira-software
read:page:confluence
write:page:confluence
read:comment:confluence
write:comment:confluence
```

## API Tokens (Atlassian Cloud)

### 创建 API Token

1. 访问 [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. 点击 "Create API token"
3. 给它描述性标签
4. 立即复制令牌（仅显示一次）

### 使用 API Token

```typescript
// Basic authentication with API token
const credentials = Buffer.from(`${email}:${apiToken}`).toString('base64');

const response = await fetch('https://your-site.atlassian.net/rest/api/3/myself', {
  headers: {
    Authorization: `Basic ${credentials}`,
    Accept: 'application/json',
  },
});

// For MCP server configuration
const config = {
  JIRA_URL: 'https://your-site.atlassian.net',
  JIRA_USERNAME: 'your-email@company.com',
  JIRA_API_TOKEN: 'your-api-token',
};
```

### Token 安全最佳实践

```typescript
// Store tokens securely
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

// Option 1: Environment variables (development only)
const token = process.env.ATLASSIAN_API_TOKEN;

// Option 2: GCP Secret Manager
async function getTokenFromGCP(secretName: string): Promise<string> {
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: `projects/my-project/secrets/${secretName}/versions/latest`,
  });
  return version.payload?.data?.toString() || '';
}

// Option 3: AWS Secrets Manager
async function getTokenFromAWS(secretName: string): Promise<string> {
  const client = new SecretsManager({ region: 'us-east-1' });
  const response = await client.getSecretValue({ SecretId: secretName });
  return response.SecretString || '';
}

// Option 4: HashiCorp Vault
async function getTokenFromVault(path: string): Promise<string> {
  const response = await fetch(`${VAULT_ADDR}/v1/${path}`, {
    headers: { 'X-Vault-Token': VAULT_TOKEN },
  });
  const data = await response.json();
  return data.data.data.token;
}
```

## Personal Access Tokens (Server/Data Center)

### 创建 PAT

**Jira Server/DC：**
1. 个人资料 > Personal Access Tokens
2. 创建令牌
3. 设置过期日期
4. 选择权限

**Confluence Server/DC：**
1. 个人资料 > Settings > Personal Access Tokens
2. 创建令牌
3. 配置权限

### 使用 PAT

```typescript
// Bearer token authentication
const response = await fetch('https://jira.internal.company.com/rest/api/2/myself', {
  headers: {
    Authorization: `Bearer ${personalAccessToken}`,
    Accept: 'application/json',
  },
});

// MCP server configuration
const config = {
  JIRA_URL: 'https://jira.internal.company.com',
  JIRA_PERSONAL_TOKEN: 'your-personal-access-token',
};
```

### PAT 权限

| 权限 | Jira | Confluence |
|------|------|------------|
| Read | 浏览项目、查看问题 | 查看页面 |
| Write | 创建/编辑问题 | 创建/编辑页面 |
| Admin | 项目管理 | 空间管理 |

## Token 管理

### Token 生命周期管理器

```typescript
interface TokenInfo {
  accessToken: string;
  refreshToken?: string;
  expiresAt: Date;
  scopes: string[];
}

class TokenManager {
  private tokenInfo: TokenInfo | null = null;
  private refreshThreshold = 5 * 60 * 1000; // 5 minutes

  async getValidToken(): Promise<string> {
    if (!this.tokenInfo) {
      throw new Error('Not authenticated');
    }

    // Check if token needs refresh
    const timeUntilExpiry = this.tokenInfo.expiresAt.getTime() - Date.now();

    if (timeUntilExpiry < this.refreshThreshold) {
      await this.refreshToken();
    }

    return this.tokenInfo.accessToken;
  }

  private async refreshToken(): Promise<void> {
    if (!this.tokenInfo?.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await refreshAccessToken(this.tokenInfo.refreshToken);

    this.tokenInfo = {
      accessToken: response.access_token,
      refreshToken: response.refresh_token || this.tokenInfo.refreshToken,
      expiresAt: new Date(Date.now() + response.expires_in * 1000),
      scopes: response.scope.split(' '),
    };
  }

  isAuthenticated(): boolean {
    return this.tokenInfo !== null && this.tokenInfo.expiresAt > new Date();
  }

  getScopes(): string[] {
    return this.tokenInfo?.scopes || [];
  }

  hasScope(scope: string): boolean {
    return this.getScopes().includes(scope);
  }
}
```

### Token 轮换策略

```typescript
class TokenRotationManager {
  private rotationInterval = 30 * 24 * 60 * 60 * 1000; // 30 days

  async checkAndRotate(tokenCreatedAt: Date): Promise<boolean> {
    const age = Date.now() - tokenCreatedAt.getTime();

    if (age > this.rotationInterval) {
      console.warn('API token is due for rotation');
      return true;
    }

    return false;
  }

  async sendRotationReminder(email: string, tokenLabel: string): Promise<void> {
    // Integrate with your notification system
    await sendEmail({
      to: email,
      subject: 'Atlassian API Token Rotation Reminder',
      body: `Your API token "${tokenLabel}" is due for rotation.
             Please create a new token and update your integrations.`,
    });
  }
}
```

## 权限验证

### 检查当前权限

```typescript
async function verifyPermissions(
  client: MCPClient,
  requiredOperations: string[]
): Promise<PermissionReport> {
  const report: PermissionReport = {
    hasAllPermissions: true,
    details: [],
  };

  for (const operation of requiredOperations) {
    try {
      switch (operation) {
        case 'read:jira':
          await client.callTool({
            name: 'jira_get_issue',
            arguments: { issue_key: 'TEST-1' },
          });
          break;
        case 'write:jira':
          // Create and immediately delete a test issue
          const created = await client.callTool({
            name: 'jira_create_issue',
            arguments: {
              project_key: 'TEST',
              issue_type: 'Task',
              summary: '[Permission Test] Delete me',
            },
          });
          // Clean up
          await client.callTool({
            name: 'jira_delete_issue',
            arguments: { issue_key: JSON.parse(created.content[0].text).key },
          });
          break;
        case 'read:confluence':
          await client.callTool({
            name: 'confluence_search',
            arguments: { cql: 'type = page', limit: 1 },
          });
          break;
      }

      report.details.push({ operation, status: 'granted' });
    } catch (error: any) {
      report.hasAllPermissions = false;
      report.details.push({
        operation,
        status: 'denied',
        error: error.message,
      });
    }
  }

  return report;
}
```

## 安全检查清单

### 应该做：
- 对面向用户的应用使用 OAuth 2.1
- 在专门的 secrets 管理系统中存储 secrets
- 实现 token 轮换策略
- 使用最小必需的 scopes
- 记录认证事件（不含 secrets）
- 在应用级别实现速率限制
- 使用前验证 tokens

### 不应该做：
- 在源代码中硬编码 tokens
- 记录 tokens 或 secrets
- 在环境之间共享 tokens
- 使用 Basic Auth（已弃用）
- 请求超过需要的 scopes
- 在浏览器 localStorage 中存储 tokens
- 提交包含真实凭证的 `.env` 文件

### 环境配置模板

```bash
# .env.example (commit this)
ATLASSIAN_SITE_URL=https://your-site.atlassian.net
ATLASSIAN_AUTH_TYPE=oauth  # or 'api_token' or 'pat'

# OAuth settings (if using OAuth)
ATLASSIAN_CLIENT_ID=
ATLASSIAN_CLIENT_SECRET=

# API Token settings (if using API token)
ATLASSIAN_USERNAME=
ATLASSIAN_API_TOKEN=

# PAT settings (if using Server/DC)
ATLASSIAN_PERSONAL_TOKEN=
```

```bash
# .gitignore
.env
.env.local
.env.*.local
credentials.json
**/secrets/**
```

## 故障排除

### 常见认证错误

**401 Unauthorized:**
- 无效或过期的 token
- 错误的认证方法
- 缺少 Authorization header

**403 Forbidden:**
- token 有效但缺少所需 scope
- 资源级权限被拒绝
- IP 允许列表阻止请求

**Token 刷新失败：**
- Refresh token 过期（90 天不活动后）
- Client secret 已更改
- 应用权限被撤销

### 调试认证

```typescript
async function debugAuth(token: string): Promise<void> {
  // Check token validity
  const meResponse = await fetch(
    'https://api.atlassian.com/me',
    { headers: { Authorization: `Bearer ${token}` } }
  );

  console.log('Token status:', meResponse.status);

  if (meResponse.ok) {
    const me = await meResponse.json();
    console.log('Authenticated as:', me.email);
  }

  // Check accessible resources
  const resourcesResponse = await fetch(
    'https://api.atlassian.com/oauth/token/accessible-resources',
    { headers: { Authorization: `Bearer ${token}` } }
  );

  if (resourcesResponse.ok) {
    const resources = await resourcesResponse.json();
    console.log('Accessible sites:', resources.map((r: any) => r.name));
  }
}
```

## 相关参考

- `mcp-server-setup.md` - 使用凭据的服务器配置
- `jira-queries.md` - 需要认证的操作
- `confluence-operations.md` - 内容操作与认证