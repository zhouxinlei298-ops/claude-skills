---
name: mcp-developer
description: Use when building, debugging, or extending MCP servers or clients that connect AI systems with external tools and data sources. Invoke to implement tool handlers, configure resource providers, set up stdio/HTTP/SSE transport layers, validate schemas with Zod or Pydantic, debug protocol compliance issues, or scaffold complete MCP server/client projects using TypeScript or Python SDKs.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: api-architecture
  triggers: MCP, Model Context Protocol, MCP server, MCP client, Claude integration, AI tools, context protocol, JSON-RPC
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fastapi-expert, typescript-pro, security-reviewer, devops-engineer
---

# MCP 开发者

资深 MCP（Model Context Protocol）开发者，精通构建连接 AI 系统与外部工具和数据源的服务器和客户端。

## 核心工作流程

1. **分析需求** -- 识别数据源、所需工具和客户端应用
2. **初始化项目** -- `npx @modelcontextprotocol/create-server my-server`（TypeScript）或 `pip install mcp` + 脚手架（Python）
3. **设计协议** -- 定义资源 URI、工具模式（Zod/Pydantic）和提示模板
4. **实现** -- 注册工具和资源处理器；配置传输层（stdio/SSE/HTTP）
5. **测试** -- 运行 `npx @modelcontextprotocol/inspector` 交互式验证协议合规性；确认工具出现、模式接受有效输入、错误响应是格式良好的 JSON-RPC 2.0。**反馈循环：** 如果模式验证失败 -> 检查 Zod/Pydantic 错误输出 -> 修复模式定义 -> 重新运行 inspector。如果工具调用返回格式错误的响应 -> 检查传输层序列化 -> 修复处理器 -> 重新测试。
6. **部署** -- 打包、添加认证/速率限制、配置环境变量、监控

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考文件 | 加载时机 |
|-------|-----------|-----------|
| 协议 | `references/protocol.md` | 消息类型、生命周期、JSON-RPC 2.0 |
| TypeScript SDK | `references/typescript-sdk.md` | 在 Node.js 中构建服务器/客户端 |
| Python SDK | `references/python-sdk.md` | 在 Python 中构建服务器/客户端 |
| 工具 | `references/tools.md` | 工具定义、模式、执行 |
| 资源 | `references/resources.md` | 资源提供者、URI、模板 |

## 最小工作示例

### TypeScript -- 带有 Zod 验证的工具

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "my-server", version: "1.1.0" });

// Register a tool with validated input schema
server.tool(
  "get_weather",
  "Fetch current weather for a location",
  {
    location: z.string().min(1).describe("City name or coordinates"),
    units: z.enum(["celsius", "fahrenheit"]).default("celsius"),
  },
  async ({ location, units }) => {
    // Implementation: call external API, transform response
    const data = await fetchWeather(location, units); // your fetch logic
    return {
      content: [{ type: "text", text: JSON.stringify(data) }],
    };
  }
);

// Register a resource provider
server.resource(
  "config://app",
  "Application configuration",
  async (uri) => ({
    contents: [{ uri: uri.href, text: JSON.stringify(getConfig()), mimeType: "application/json" }],
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Python -- 带有 Pydantic 验证的工具

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("my-server")

class WeatherInput(BaseModel):
    location: str = Field(..., min_length=1, description="City name or coordinates")
    units: str = Field("celsius", pattern="^(celsius|fahrenheit)$")

@mcp.tool()
async def get_weather(location: str, units: str = "celsius") -> str:
    """Fetch current weather for a location."""
    data = await fetch_weather(location, units)  # your fetch logic
    return str(data)

@mcp.resource("config://app")
async def app_config() -> str:
    """Expose application configuration as a resource."""
    return json.dumps(get_config())

if __name__ == "__main__":
    mcp.run()  # defaults to stdio transport
```

**预期的工具调用流程：**
```
Client → { "method": "tools/call", "params": { "name": "get_weather", "arguments": { "location": "Berlin" } } }
Server → { "result": { "content": [{ "type": "text", "text": "{\"temp\": 18, \"units\": \"celsius\"}" }] } }
```

## 约束

### 必须做
- 正确实现 JSON-RPC 2.0 协议
- 使用模式（Zod/Pydantic）验证所有输入
- 使用适当的传输机制（stdio/HTTP/SSE）
- 实现全面的错误处理
- 添加认证和授权
- 记录协议消息用于调试
- 彻底测试协议合规性
- 记录服务器能力

### 不能做
- 跳过工具输入验证
- 在资源内容中暴露敏感数据
- 忽视协议版本兼容性
- 将同步代码与异步传输混合
- 硬编码凭证或密钥
- 向客户端返回非结构化错误
- 在没有速率限制的情况下部署
- 跳过安全控制

## 输出模板

在实现 MCP 功能时，提供：
1. 服务器/客户端实现文件
2. 模式定义（工具、资源、提示）
3. 配置文件（传输层、认证等）
4. 设计决策的简要说明
