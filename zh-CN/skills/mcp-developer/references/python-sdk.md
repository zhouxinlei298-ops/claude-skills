# Python SDK 实现

## 安装

```bash
pip install mcp pydantic
```

## 基础服务器设置

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    ListToolsRequest,
)
from pydantic import BaseModel, Field
import asyncio

# Create server instance
app = Server("example-server")

# Define tool input schema
class WeatherArgs(BaseModel):
    location: str = Field(..., description="City name or zip code")
    units: str = Field(default="celsius", pattern="^(celsius|fahrenheit)$")

# List available tools
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_weather",
            description="Get current weather for a location",
            inputSchema=WeatherArgs.model_json_schema(),
        )
    ]

# Handle tool execution
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_weather":
        # Validate arguments
        args = WeatherArgs(**arguments)

        # Execute tool logic
        weather_data = await fetch_weather(args.location, args.units)

        return [
            TextContent(
                type="text",
                text=f"Weather in {args.location}: {weather_data['temp']}°{
                    'C' if args.units == 'celsius' else 'F'
                }",
            )
        ]

    raise ValueError(f"Unknown tool: {name}")

# Run server
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## 资源提供者

```python
from mcp.types import (
    Resource,
    ResourceTemplate,
    TextResourceContents,
    ListResourcesRequest,
    ReadResourceRequest,
)
import json

@app.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="file:///config/settings.json",
            name="Application Settings",
            description="Current application configuration",
            mimeType="application/json",
        ),
        Resource(
            uri="db://users/schema",
            name="User Schema",
            description="Database schema for users table",
            mimeType="text/plain",
        ),
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "file:///config/settings.json":
        settings = await load_settings()
        return json.dumps(settings, indent=2)

    if uri.startswith("db://users/"):
        schema = await get_database_schema("users")
        return schema

    raise ValueError(f"Resource not found: {uri}")
```

## 资源模板（动态 URI）

```python
@app.list_resource_templates()
async def list_resource_templates() -> list[ResourceTemplate]:
    return [
        ResourceTemplate(
            uriTemplate="user://{user_id}/profile",
            name="User Profile",
            description="Get user profile by ID",
            mimeType="application/json",
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    # Parse template URI
    if uri.startswith("user://"):
        user_id = uri.split("/")[2]
        profile = await get_user_profile(user_id)
        return json.dumps(profile, indent=2)

    raise ValueError(f"Unknown resource: {uri}")
```

## 提示模板

```python
from mcp.types import (
    Prompt,
    PromptArgument,
    PromptMessage,
    GetPromptRequest,
)

@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="code_review",
            description="Generate code review comments",
            arguments=[
                PromptArgument(
                    name="language",
                    description="Programming language",
                    required=True,
                ),
                PromptArgument(
                    name="code",
                    description="Code to review",
                    required=True,
                ),
            ],
        )
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> list[PromptMessage]:
    if name == "code_review":
        language = arguments["language"]
        code = arguments["code"]

        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Review this {language} code and provide feedback:\n\n{code}",
                ),
            )
        ]

    raise ValueError(f"Unknown prompt: {name}")
```

## Pydantic 输入验证

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class WeatherArgs(BaseModel):
    location: str = Field(..., min_length=1, description="City name")
    units: Literal["celsius", "fahrenheit"] = Field(default="celsius")

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Location cannot be empty")
        return v.strip()

class DatabaseQueryArgs(BaseModel):
    table: str = Field(..., pattern="^[a-zA-Z_][a-zA-Z0-9_]*$")
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "query_database":
        # Pydantic validation happens here
        args = DatabaseQueryArgs(**arguments)

        results = await execute_query(args.table, args.limit, args.offset)
        return [TextContent(type="text", text=json.dumps(results))]

    raise ValueError(f"Unknown tool: {name}")
```

## 错误处理

```python
from mcp.types import McpError, INTERNAL_ERROR, INVALID_PARAMS

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "get_weather":
            args = WeatherArgs(**arguments)
            result = await fetch_weather(args.location, args.units)
            return [TextContent(type="text", text=str(result))]

        raise ValueError(f"Unknown tool: {name}")

    except ValueError as e:
        # Validation or tool not found
        raise McpError(INVALID_PARAMS, str(e))

    except Exception as e:
        # Unexpected errors
        raise McpError(INTERNAL_ERROR, f"Tool execution failed: {e}")
```

## 日志记录

```python
import logging
import sys

# Configure logging to stderr (stdout is used for protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger("mcp-server")

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    logger.info(f"Tool called: {name} with args: {arguments}")

    try:
        result = await execute_tool(name, arguments)
        logger.info(f"Tool {name} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        raise
```

## 上下文管理器和清理

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def database_connection():
    """Manage database connection lifecycle"""
    db = await connect_to_database()
    try:
        yield db
    finally:
        await db.close()

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "query_database":
        async with database_connection() as db:
            result = await db.execute(arguments["query"])
            return [TextContent(type="text", text=str(result))]

    raise ValueError(f"Unknown tool: {name}")
```

## 基础客户端设置

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_client():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            # Call a tool
            result = await session.call_tool(
                "get_weather",
                arguments={"location": "San Francisco"},
            )
            print(f"Result: {result.content}")

if __name__ == "__main__":
    asyncio.run(run_client())
```

## 通知

```python
from mcp.types import ResourceUpdatedNotification

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "update_config":
        # Update configuration
        await save_config(arguments["config"])

        # Notify clients of resource update
        await app.request_context.session.send_resource_updated(
            uri="file:///config/settings.json"
        )

        return [TextContent(type="text", text="Configuration updated")]

    raise ValueError(f"Unknown tool: {name}")
```

## 最佳实践

1. **类型安全**：对所有架构使用 Pydantic
2. **异步/等待**：所有处理程序必须是异步的
3. **验证**：尽早使用 Pydantic 验证输入
4. **日志记录**：记录到 stderr，绝不记录到 stdout
5. **错误处理**：将错误包装在 McpError 中
6. **资源清理**：使用上下文管理器
7. **测试**：对异步测试使用 pytest-asyncio
8. **性能**：缓存昂贵的操作
9. **安全**：清理所有输入和输出
10. **文档**：包含文档字符串和类型提示

---