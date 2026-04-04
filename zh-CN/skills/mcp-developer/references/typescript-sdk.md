# TypeScript SDK 实现

## 安装

```bash
npm install @modelcontextprotocol/sdk zod
```

## 基础服务器设置

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

// Create server instance
const server = new Server(
  {
    name: "example-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      resources: {},
      tools: {},
      prompts: {},
    },
  }
);

// Handle tools/list request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_weather",
        description: "Get current weather for a location",
        inputSchema: {
          type: "object",
          properties: {
            location: {
              type: "string",
              description: "City name or zip code",
            },
            units: {
              type: "string",
              enum: ["celsius", "fahrenheit"],
              default: "celsius",
            },
          },
          required: ["location"],
        },
      },
    ],
  };
});

// Handle tools/call request
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "get_weather") {
    const location = String(request.params.arguments?.location);
    const units = String(request.params.arguments?.units ?? "celsius");

    // Your tool logic here
    const weatherData = await fetchWeather(location, units);

    return {
      content: [
        {
          type: "text",
          text: `Weather in ${location}: ${weatherData.temp}°${units === "celsius" ? "C" : "F"}`,
        },
      ],
    };
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});

// Start server with stdio transport
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server running on stdio");
}

main().catch(console.error);
```

## 资源提供者

```typescript
import {
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// List resources
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "file:///config/settings.json",
        name: "Application Settings",
        description: "Current application configuration",
        mimeType: "application/json",
      },
      {
        uri: "db://users/schema",
        name: "User Schema",
        description: "Database schema for users table",
        mimeType: "text/plain",
      },
    ],
  };
});

// Read resource content
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;

  if (uri === "file:///config/settings.json") {
    const settings = await loadSettings();
    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(settings, null, 2),
        },
      ],
    };
  }

  if (uri.startsWith("db://users/")) {
    const schema = await getDatabaseSchema("users");
    return {
      contents: [
        {
          uri,
          mimeType: "text/plain",
          text: schema,
        },
      ],
    };
  }

  throw new Error(`Resource not found: ${uri}`);
});
```

## 提示模板

```typescript
import {
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: [
      {
        name: "code_review",
        description: "Generate code review comments",
        arguments: [
          {
            name: "language",
            description: "Programming language",
            required: true,
          },
          {
            name: "code",
            description: "Code to review",
            required: true,
          },
        ],
      },
    ],
  };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  if (request.params.name === "code_review") {
    const language = String(request.params.arguments?.language);
    const code = String(request.params.arguments?.code);

    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Review this ${language} code and provide feedback:\n\n${code}`,
          },
        },
      ],
    };
  }

  throw new Error(`Unknown prompt: ${request.params.name}`);
});
```

## Zod 输入验证

```typescript
import { z } from "zod";

// Define schemas for validation
const WeatherArgsSchema = z.object({
  location: z.string().min(1),
  units: z.enum(["celsius", "fahrenheit"]).default("celsius"),
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "get_weather") {
    // Validate and parse arguments
    const args = WeatherArgsSchema.parse(request.params.arguments);

    const weatherData = await fetchWeather(args.location, args.units);

    return {
      content: [
        {
          type: "text",
          text: `Temperature: ${weatherData.temp}°${args.units === "celsius" ? "C" : "F"}`,
        },
      ],
    };
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});
```

## 错误处理

```typescript
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    // Validate input
    if (!request.params.arguments?.location) {
      throw new McpError(
        ErrorCode.InvalidParams,
        "location parameter is required"
      );
    }

    const result = await executeTool(request.params.name, request.params.arguments);
    return { content: [{ type: "text", text: result }] };

  } catch (error) {
    if (error instanceof McpError) {
      throw error; // Re-throw MCP errors
    }

    // Wrap other errors
    throw new McpError(
      ErrorCode.InternalError,
      `Tool execution failed: ${error.message}`
    );
  }
});
```

## 基础客户端设置

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const client = new Client(
  {
    name: "example-client",
    version: "1.0.0",
  },
  {
    capabilities: {},
  }
);

// Connect to server
const transport = new StdioClientTransport({
  command: "node",
  args: ["./server.js"],
});

await client.connect(transport);

// List available tools
const toolsResponse = await client.request(
  { method: "tools/list" },
  ListToolsResultSchema
);

console.log("Available tools:", toolsResponse.tools);

// Call a tool
const result = await client.request(
  {
    method: "tools/call",
    params: {
      name: "get_weather",
      arguments: { location: "San Francisco" },
    },
  },
  CallToolResultSchema
);

console.log("Result:", result.content);
```

## 通知

```typescript
// Server sends notification
server.notification({
  method: "notifications/resources/updated",
  params: {
    uri: "file:///config/settings.json",
  },
});

// Client handles notifications
client.setNotificationHandler((notification) => {
  if (notification.method === "notifications/resources/updated") {
    console.log("Resource updated:", notification.params.uri);
  }
});
```

## 最佳实践

1. **类型安全**：使用 Zod 进行运行时验证
2. **错误处理**：始终将错误包装在 McpError 中
3. **异步/等待**：全程使用 async/await
4. **日志记录**：记录到 stderr，而不是 stdout（stdio 传输）
5. **清理**：处理优雅关闭
6. **测试**：使用模拟传输进行单元测试
7. **性能**：缓存昂贵的操作
8. **安全**：验证所有输入，清理输出

---