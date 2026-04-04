# MCP 协议规范

## 协议概述

MCP 基于 JSON-RPC 2.0 构建，支持客户端（如 Claude Desktop）和提供资源、工具和提示的服务器之间的双向通信。

## 消息类型

### 请求/响应

```typescript
// Request format
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}

// Success response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_weather",
        "description": "Get weather for a location",
        "inputSchema": {
          "type": "object",
          "properties": {
            "location": { "type": "string" }
          },
          "required": ["location"]
        }
      }
    ]
  }
}

// Error response
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": { "details": "location is required" }
  }
}
```

### 通知

```typescript
// Server sends notification (no response expected)
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "file:///project/data.json"
  }
}
```

## 连接生命周期

```
1. Client initiates connection (stdio/HTTP/SSE)
2. Client sends initialize request
   → Server responds with capabilities
3. Client sends initialized notification
4. Normal operation (requests/notifications)
5. Client/server can ping for keepalive
6. Client sends shutdown request
7. Connection closes
```

### 初始化握手

```typescript
// Client initialize request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": { "listChanged": true },
      "sampling": {}
    },
    "clientInfo": {
      "name": "claude-desktop",
      "version": "1.0.0"
    }
  }
}

// Server response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "resources": { "subscribe": true, "listChanged": true },
      "tools": { "listChanged": true },
      "prompts": { "listChanged": true }
    },
    "serverInfo": {
      "name": "my-mcp-server",
      "version": "1.0.0"
    }
  }
}

// Client sends initialized notification
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

## 核心方法

### 资源

```typescript
// List available resources
resources/list → { resources: Resource[] }

// Read resource content
resources/read { uri: string } → { contents: ResourceContent[] }

// Subscribe to resource updates (if supported)
resources/subscribe { uri: string } → {}

// Unsubscribe
resources/unsubscribe { uri: string } → {}

// Server notifies of changes
notifications/resources/list_changed → {}
notifications/resources/updated { uri: string } → {}
```

### 工具

```typescript
// List available tools
tools/list → { tools: Tool[] }

// Execute tool
tools/call {
  name: string,
  arguments: object
} → { content: ToolResponse[] }

// Server notifies of tool changes
notifications/tools/list_changed → {}
```

### 提示

```typescript
// List available prompts
prompts/list → { prompts: Prompt[] }

// Get prompt with arguments
prompts/get {
  name: string,
  arguments?: object
} → { messages: PromptMessage[] }

// Server notifies of prompt changes
notifications/prompts/list_changed → {}
```

## 错误代码

标准 JSON-RPC 2.0 代码加 MCP 特定代码：

```typescript
const ERROR_CODES = {
  // JSON-RPC 2.0 standard
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,

  // MCP-specific (implementation defined)
  RESOURCE_NOT_FOUND: -32001,
  TOOL_EXECUTION_ERROR: -32002,
  UNAUTHORIZED: -32003,
  RATE_LIMIT_EXCEEDED: -32004
};
```

## 传输机制

### stdio（标准输入/输出）

```typescript
// Server reads from stdin, writes to stdout
// Each message is newline-delimited JSON
// Used for local integration (Claude Desktop default)
```

### HTTP with SSE（服务器发送事件）

```typescript
// Client POSTs JSON-RPC requests to endpoint
// Server streams responses and notifications via SSE
// Used for remote servers

POST /mcp HTTP/1.1
Content-Type: application/json

{"jsonrpc":"2.0","id":1,"method":"tools/list"}

// SSE response
GET /mcp/sse HTTP/1.1

event: message
data: {"jsonrpc":"2.0","id":1,"result":{...}}
```

## 协议版本

当前版本：`2024-11-05`

服务器必须在初始化响应中声明支持的版本。客户端应验证兼容性。

## 最佳实践

1. **验证**：始终使用 JSON Schema 验证参数
2. **错误处理**：返回带有有用消息的结构化错误
3. **版本控制**：在初始化时检查协议版本
4. **超时**：实现请求超时（推荐 30 秒）
5. **日志记录**：记录所有协议消息以供调试
6. **无状态**：设计工具/资源为无状态
7. **幂等性**：尽可能使工具调用具有幂等性
8. **通知**：使用通知进行实时更新

---