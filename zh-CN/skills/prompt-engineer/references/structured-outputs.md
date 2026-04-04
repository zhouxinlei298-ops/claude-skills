# 结构化输出

---

## 结构化输出方法

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRUCTURED OUTPUT APPROACHES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   Prompt-Based  │  │   JSON Mode     │  │ Function Calling│            │
│  │                 │  │                 │  │ (Tool Use)      │            │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤            │
│  │ Reliability: ~  │  │ Reliability: ++ │  │ Reliability: +++│            │
│  │ Flexibility: +++│  │ Flexibility: ++ │  │ Flexibility: +  │            │
│  │ Validation: --- │  │ Validation: +   │  │ Validation: +++ │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│  Use when:          Use when:             Use when:                        │
│  - Simple extracts  - Need valid JSON     - Strict schemas required        │
│  - Flexible schemas - Moderate complexity - Tool orchestration             │
│  - Quick prototypes - Claude/GPT models   - Type-safe parsing              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 基于提示的结构化输出

### 基本 JSON 请求

```
Extract the following information from the text and return as JSON:
- person_name: string
- company: string
- role: string
- email: string or null

Text: {text}

Return only valid JSON, no other text:
```

### 带模式定义

```
Extract meeting information from the transcript.

Return a JSON object matching this schema:
{
  "meeting_title": "string - the main topic discussed",
  "date": "string - ISO 8601 format (YYYY-MM-DD) or null if not mentioned",
  "attendees": ["array of strings - names of participants"],
  "action_items": [
    {
      "task": "string - what needs to be done",
      "assignee": "string - who is responsible",
      "due_date": "string - ISO 8601 format or null"
    }
  ],
  "decisions": ["array of strings - key decisions made"],
  "next_meeting": "string - ISO 8601 datetime or null"
}

Rules:
- Use null for fields not mentioned in the transcript
- Use empty arrays [] for list fields with no items
- Dates must be in ISO 8601 format
- Return ONLY the JSON object, no explanation

Transcript:
{transcript}
```

### 输出包装技术

```
Analyze the code and identify issues. Return your analysis in this exact format:

<analysis>
{
  "summary": "one sentence overview",
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "type": "bug|security|performance|style",
      "location": "file:line or function name",
      "description": "what's wrong",
      "suggestion": "how to fix"
    }
  ],
  "quality_score": 1-10
}
</analysis>

Code:
{code}
```

使用标签解析：

```python
import re
import json

def extract_tagged_json(response: str, tag: str = "analysis") -> dict:
    """Extract JSON from tagged output."""
    pattern = rf"<{tag}>\s*(.*?)\s*</{tag}>"
    match = re.search(pattern, response, re.DOTALL)

    if not match:
        raise ValueError(f"No <{tag}> tags found in response")

    return json.loads(match.group(1))
```

---

## JSON 模式（Claude & OpenAI）

### Claude JSON 模式

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": """Extract entities from this text and return as JSON.

            Required fields:
            - people: array of {name, role}
            - organizations: array of {name, type}
            - locations: array of strings

            Text: {text}"""
        }
    ],
    # Claude uses system prompt to enforce JSON
    system="You are a JSON extraction assistant. Always respond with valid JSON only, no other text."
)

# Parse the response
result = json.loads(response.content[0].text)
```

### OpenAI JSON 模式

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    response_format={"type": "json_object"},  # Enforces JSON output
    messages=[
        {
            "role": "system",
            "content": "Extract information and return as JSON."
        },
        {
            "role": "user",
            "content": f"Extract people and companies from: {text}"
        }
    ]
)

result = json.loads(response.choices[0].message.content)
```

### JSON 模式最佳实践

| 实践 | 原因 |
|------|------|
| 始终描述期望的模式 | 模型需要知道结构 |
| 指定 null 处理 | "对缺失字段使用 null" |
| 定义数组行为 | "如果没有找到则返回空数组" |
| 包含字段描述 | 提高提取准确性 |
| 添加类型注解 | "date: YYYY-MM-DD 格式的字符串" |

---

## 函数调用/工具使用

### Claude 工具使用

```python
import anthropic

client = anthropic.Anthropic()

# Define the tool schema
tools = [
    {
        "name": "extract_contact",
        "description": "Extract contact information from text",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full name of the person"
                },
                "email": {
                    "type": "string",
                    "description": "Email address"
                },
                "phone": {
                    "type": "string",
                    "description": "Phone number in E.164 format"
                },
                "company": {
                    "type": "string",
                    "description": "Company or organization name"
                },
                "title": {
                    "type": "string",
                    "description": "Job title or role"
                }
            },
            "required": ["name"]
        }
    }
]

response = client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "tool", "name": "extract_contact"},  # Force tool use
    messages=[
        {
            "role": "user",
            "content": f"Extract contact info from: {business_card_text}"
        }
    ]
)

# Get structured output from tool call
for block in response.content:
    if block.type == "tool_use":
        contact = block.input  # Already parsed as dict
        print(f"Name: {contact['name']}")
        print(f"Email: {contact.get('email', 'N/A')}")
```

### OpenAI 函数调用

```python
from openai import OpenAI

client = OpenAI()

functions = [
    {
        "name": "analyze_sentiment",
        "description": "Analyze sentiment of customer feedback",
        "parameters": {
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral", "mixed"]
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                },
                "key_phrases": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Phrases that indicate sentiment"
                },
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Main topics discussed"
                }
            },
            "required": ["sentiment", "confidence"]
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "user", "content": f"Analyze this feedback: {feedback}"}
    ],
    functions=functions,
    function_call={"name": "analyze_sentiment"}  # Force specific function
)

# Parse function call
fn_call = response.choices[0].message.function_call
result = json.loads(fn_call.arguments)
```

---

## 模式设计模式

### 枚举约束

```json
{
  "type": "object",
  "properties": {
    "priority": {
      "type": "string",
      "enum": ["critical", "high", "medium", "low"],
      "description": "Issue priority level"
    },
    "status": {
      "type": "string",
      "enum": ["open", "in_progress", "blocked", "resolved", "closed"]
    },
    "category": {
      "type": "string",
      "enum": ["bug", "feature", "improvement", "documentation"]
    }
  }
}
```

### 嵌套对象

```json
{
  "type": "object",
  "properties": {
    "order": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "total": {"type": "number"},
        "currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
        "items": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "product_id": {"type": "string"},
              "name": {"type": "string"},
              "quantity": {"type": "integer", "minimum": 1},
              "unit_price": {"type": "number", "minimum": 0}
            },
            "required": ["product_id", "quantity", "unit_price"]
          }
        },
        "shipping_address": {
          "$ref": "#/definitions/address"
        }
      },
      "required": ["id", "items"]
    }
  },
  "definitions": {
    "address": {
      "type": "object",
      "properties": {
        "street": {"type": "string"},
        "city": {"type": "string"},
        "state": {"type": "string"},
        "postal_code": {"type": "string"},
        "country": {"type": "string", "pattern": "^[A-Z]{2}$"}
      },
      "required": ["street", "city", "country"]
    }
  }
}
```

### 条件字段

```json
{
  "type": "object",
  "properties": {
    "contact_method": {
      "type": "string",
      "enum": ["email", "phone", "mail"]
    },
    "email": {"type": "string", "format": "email"},
    "phone": {"type": "string"},
    "address": {"$ref": "#/definitions/address"}
  },
  "required": ["contact_method"],
  "allOf": [
    {
      "if": {"properties": {"contact_method": {"const": "email"}}},
      "then": {"required": ["email"]}
    },
    {
      "if": {"properties": {"contact_method": {"const": "phone"}}},
      "then": {"required": ["phone"]}
    },
    {
      "if": {"properties": {"contact_method": {"const": "mail"}}},
      "then": {"required": ["address"]}
    }
  ]
}
```

---

## 验证和错误处理

### Pydantic 验证（Python）

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CodeIssue(BaseModel):
    severity: Severity
    type: str = Field(..., pattern="^(bug|security|performance|style)$")
    location: str
    description: str = Field(..., min_length=10, max_length=500)
    suggestion: Optional[str] = None

    @validator('location')
    def validate_location(cls, v):
        if ':' not in v and '(' not in v:
            raise ValueError('Location must be file:line or function()')
        return v

class CodeAnalysis(BaseModel):
    summary: str = Field(..., max_length=200)
    issues: List[CodeIssue]
    quality_score: int = Field(..., ge=1, le=10)

    @validator('issues')
    def critical_issues_first(cls, v):
        return sorted(v, key=lambda x: list(Severity).index(x.severity))

# Usage
def parse_analysis(llm_response: str) -> CodeAnalysis:
    """Parse and validate LLM response."""
    try:
        data = json.loads(llm_response)
        return CodeAnalysis(**data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    except ValidationError as e:
        raise ValueError(f"Schema validation failed: {e}")
```

### Zod 验证（TypeScript）

```typescript
import { z } from 'zod';

const SeveritySchema = z.enum(['critical', 'high', 'medium', 'low']);

const CodeIssueSchema = z.object({
  severity: SeveritySchema,
  type: z.enum(['bug', 'security', 'performance', 'style']),
  location: z.string().regex(/[:()]/, 'Must be file:line or function()'),
  description: z.string().min(10).max(500),
  suggestion: z.string().optional(),
});

const CodeAnalysisSchema = z.object({
  summary: z.string().max(200),
  issues: z.array(CodeIssueSchema),
  quality_score: z.number().int().min(1).max(10),
});

type CodeAnalysis = z.infer<typeof CodeAnalysisSchema>;

function parseAnalysis(llmResponse: string): CodeAnalysis {
  const data = JSON.parse(llmResponse);
  return CodeAnalysisSchema.parse(data);
}
```

### 重试和纠正

```python
def get_structured_output(
    prompt: str,
    schema: dict,
    max_retries: int = 3
) -> dict:
    """Get structured output with automatic retry on validation failure."""

    for attempt in range(max_retries):
        response = llm.complete(prompt)

        try:
            data = json.loads(response)
            validate(data, schema)  # JSON Schema validation
            return data
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON at position {e.pos}: {e.msg}"
        except ValidationError as e:
            error_msg = format_validation_error(e)

        # Retry with error feedback
        if attempt < max_retries - 1:
            prompt = f"""Your previous response had an error:
{error_msg}

Please fix and try again. Return only valid JSON matching the schema.

Original request:
{prompt}"""

    raise ValueError(f"Failed to get valid output after {max_retries} attempts")
```

---

## 复杂提取模式

### 多实体提取

```
Extract all entities from the following document.

Return JSON with this structure:
{
  "people": [
    {
      "name": "full name",
      "aliases": ["nicknames or alternate names"],
      "role": "their role/position if mentioned",
      "mentioned_with": ["names of people they're associated with"]
    }
  ],
  "organizations": [
    {
      "name": "organization name",
      "type": "company|nonprofit|government|education|other",
      "location": "headquarters if mentioned"
    }
  ],
  "events": [
    {
      "name": "event name",
      "date": "YYYY-MM-DD or null",
      "location": "where it happened",
      "participants": ["people or organizations involved"]
    }
  ],
  "relationships": [
    {
      "entity1": "name",
      "entity2": "name",
      "type": "works_at|acquired|partnered|competed|invested",
      "details": "additional context"
    }
  ]
}

Document:
{document}
```

### 分层数据提取

```
Parse this organizational structure and return as JSON:

{
  "organization": {
    "name": "company name",
    "departments": [
      {
        "name": "department name",
        "head": "department head name",
        "teams": [
          {
            "name": "team name",
            "lead": "team lead name",
            "members": ["member names"],
            "responsibilities": ["key responsibilities"]
          }
        ]
      }
    ]
  }
}

Text:
{org_description}
```

### 表单数据提取

```
Extract form data from this image/document.

Return JSON:
{
  "form_type": "detected form type",
  "fields": {
    "field_name": {
      "value": "extracted value",
      "confidence": 0.0-1.0,
      "location": "where on form (if applicable)"
    }
  },
  "checkboxes": {
    "checkbox_label": true/false
  },
  "signatures": [
    {
      "signer": "name if readable",
      "date": "date if present",
      "location": "signature location on form"
    }
  ],
  "missing_fields": ["fields that appear required but are empty"]
}

Document content:
{document}
```

---

## 性能优化

### 批量处理

```python
async def extract_structured_batch(
    items: list,
    schema: dict,
    batch_size: int = 10
) -> list:
    """Process multiple items efficiently."""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]

        # Create batch prompt
        prompt = f"""Extract information from each item below.
Return a JSON array with one object per item, matching this schema:
{json.dumps(schema, indent=2)}

Items:
{json.dumps([{"index": j, "content": item} for j, item in enumerate(batch)])}

Response (JSON array only):"""

        response = await llm.complete_async(prompt)
        batch_results = json.loads(response)
        results.extend(batch_results)

    return results
```

### 模式简化

**过于复杂的模式（昂贵）：**
```json
{
  "analysis": {
    "sentiment": {
      "overall": {"score": -1 to 1, "label": "string"},
      "aspects": [{"aspect": "string", "sentiment": {...}}]
    },
    "entities": [...],
    "topics": [...],
    "summary": {...}
  }
}
```

**简化的模式（经济）：**
```json
{
  "sentiment": "positive|negative|neutral",
  "confidence": 0.0-1.0,
  "key_points": ["string"]
}
```

---

## 常见陷阱

| 陷阱 | 问题 | 解决方案 |
|------|------|----------|
| 提示中没有模式 | 模型发明结构 | 始终指定期望的模式 |
| 模糊的字段名 | 不一致的提取 | 使用描述性名称和示例 |
| 缺少 null 处理 | 可选字段错误 | 明确说明"未找到则为 null" |
| 复杂的嵌套模式 | 不一致的输出 | 尽可能扁平化 |
| 没有验证 | 静默失败 | 始终使用 Pydantic/Zod 验证 |
| 大的模式 | 令牌浪费，混淆 | 分成多个调用 |

---

## 相关技能

- **API 设计师** - API 的模式设计
- **数据工程师** - 数据验证管道
- **RAG 架构师** - 用于检索的结构化提取