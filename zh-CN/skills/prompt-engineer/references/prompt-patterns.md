# 提示模式

---

## 模式选择指南

```
                        ┌─────────────────────────────────────┐
                        │        TASK CHARACTERISTICS         │
                        └─────────────────────────────────────┘
                                         │
           ┌─────────────────────────────┼─────────────────────────────┐
           │                             │                             │
    Simple, Common              Requires Reasoning            Requires Actions
           │                             │                             │
           ▼                             ▼                             ▼
    ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
    │  Zero-Shot  │              │    CoT or   │              │    ReAct    │
    │             │              │  Few-Shot   │              │             │
    └─────────────┘              └─────────────┘              └─────────────┘
```

| 模式 | 最适合 | 令牌成本 | 可靠性 |
|------|--------|----------|--------|
| 零样本 | 简单、定义明确的任务 | 低 | 中等 |
| 少样本 | 需要格式指导的任务 | 中等 | 高 |
| 思维链 | 推理、数学、逻辑 | 中等-高 | 高 |
| ReAct | 需要工具的多步任务 | 高 | 非常高 |
| 思维树 | 复杂问题解决 | 非常高 | 非常高 |

---

## 零样本提示

**何时使用**：简单的分类、提取、格式化或生成任务，模型具有很强的先验知识。

**何时不使用**：复杂推理、领域特定格式或需要特定输出结构的任务。

### 基本结构

```
<role>You are a [specific role with relevant expertise].</role>

<task>
[Clear, specific instruction]
</task>

<constraints>
- [Constraint 1]
- [Constraint 2]
</constraints>

<input>
{user_content}
</input>

<output_format>
[Expected format description]
</output_format>
```

### 示例：情感分类

```
You are a sentiment analysis expert.

Classify the following customer review as POSITIVE, NEGATIVE, or NEUTRAL.
Respond with only the classification label.

Review: "{review_text}"

Classification:
```

### 示例：实体提取

```
Extract all company names mentioned in the following text.
Return them as a JSON array of strings.
If no companies are mentioned, return an empty array.

Text: "{input_text}"

Companies:
```

### 零样本最佳实践

1. **任务要具体** - 避免模糊的指令
2. **指定输出格式** - 告诉模型确切返回什么
3. **包含约束** - 不做什么和做什么一样重要
4. **使用角色引导** - "你是一个专家..." 提高质量

---

## 少样本提示

**何时使用**：需要特定输出格式、领域特定推理或一致风格的任务。

**何时不使用**：简单的任务，示例增加不必要的令牌，或者示例可能限制创造力。

### 基本结构

```
<task>
[Task description]
</task>

<examples>
Input: [example 1 input]
Output: [example 1 output]

Input: [example 2 input]
Output: [example 2 output]

Input: [example 3 input]
Output: [example 3 output]
</examples>

<input>
{actual_input}
</input>

Output:
```

### 示例：代码审查评论

```
Generate a constructive code review comment for the given code issue.

Example 1:
Issue: Variable named 'x' in a function calculating total price
Comment: Consider renaming 'x' to 'totalPrice' or 'priceSum' to improve readability. Descriptive variable names help future maintainers understand the code's intent without needing to trace through the logic.

Example 2:
Issue: SQL query built with string concatenation using user input
Comment: This code is vulnerable to SQL injection attacks. Consider using parameterized queries or an ORM to safely handle user input. For example: `cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))`

Example 3:
Issue: Catch block that silently swallows exceptions
Comment: Empty catch blocks can hide bugs and make debugging difficult. Consider logging the exception or, if the exception is truly expected, add a comment explaining why it's safe to ignore.

Issue: {code_issue}
Comment:
```

### 少样本选择策略

| 策略 | 描述 | 最适合 |
|------|------|--------|
| 多样化 | 涵盖不同情况/类别 | 分类、归类 |
| 相似性 | 使示例与输入类型匹配 | 一致的格式 |
| 递增复杂性 | 从简单开始，逐步建立 | 复杂推理任务 |
| 边缘案例 | 包含边界情况 | 稳健处理 |

### 示例选择指南

1. **匹配分布** - 示例应代表真实输入
2. **通常 3-5 个示例最佳** - 在指导与令牌成本之间取得平衡
3. **顺序很重要** - 最近的示例影响更大
4. **包含边缘案例** - 展示如何处理异常输入
5. **保持格式一致** - 所有示例应遵循相同结构

### 动态少样本选择

```python
def select_examples(query: str, example_pool: list, k: int = 3) -> list:
    """Select most relevant examples using embedding similarity."""
    query_embedding = embed(query)

    scored = []
    for example in example_pool:
        score = cosine_similarity(query_embedding, example.embedding)
        scored.append((score, example))

    # Return top-k most similar examples
    scored.sort(reverse=True)
    return [ex for _, ex in scored[:k]]
```

---

## 思维链（CoT）提示

**何时使用**：数学问题、逻辑推理、多步分析、调试、规划。

**何时不使用**：简单的事实回忆、创造性生成或推理步骤没有帮助的任务。

### 零样本 CoT

简单添加"让我们一步步思考"或类似短语：

```
Solve the following problem step by step:

{problem}

Let's work through this systematically:
```

### 结构化 CoT

```
Analyze the following problem and solve it step by step.

Problem: {problem}

## Step 1: Understand the problem
[What are we trying to find?]

## Step 2: Identify relevant information
[What data do we have?]

## Step 3: Plan the approach
[What method will we use?]

## Step 4: Execute the solution
[Work through the calculations/logic]

## Step 5: Verify the answer
[Check if the answer makes sense]

Final Answer:
```

### 示例：使用 CoT 调试

````
Debug the following code by analyzing it step by step.

Code:
```python
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)
```

Error: ZeroDivisionError when called with empty list

## Analysis

### Step 1: Trace the execution path
Let me trace what happens when `numbers = []`:
1. `total = 0` - total is initialized to 0
2. `for num in numbers:` - loop doesn't execute (empty list)
3. `return total / len(numbers)` - returns `0 / 0`

### Step 2: Identify the root cause
The function doesn't handle the edge case of an empty list.
`len([])` returns 0, causing division by zero.

### Step 3: Propose fix
Add a check for empty input before division.

### Fixed Code:
```python
def calculate_average(numbers):
    if not numbers:
        return 0  # 或 raise ValueError("Cannot average empty list")
    total = sum(numbers)
    return total / len(numbers)
```
```

### CoT 变体

| 变体 | 技术 | 用途 |
|------|------|------|
| 零样本 CoT | "一步步思考" | 快速推理任务 |
| 手动 CoT | 明确的步骤示例 | 复杂领域问题 |
| 自洽性 | 生成多个路径，投票 | 高风险决策 |
| 由少到多 | 分解为子问题 | 复杂的多部分问题 |

---

## ReAct 模式（推理 + 行动）

**何时使用**：需要外部工具、信息检索或迭代解决问题的任务。

**何时不使用**：纯文本生成、简单的问答或没有行动组件的任务。

### ReAct 结构

```
You are an assistant that solves problems by thinking and taking actions.

Available tools:
- search(query): Search the web for information
- calculate(expression): Evaluate a mathematical expression
- lookup(term): Look up a definition or fact

Respond in this format:
Thought: [Your reasoning about what to do next]
Action: [tool_name(parameters)]
Observation: [Result from the tool - provided by system]
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information to answer.
Answer: [Final answer]

Question: {user_question}
```

### 示例：ReAct 用于研究

```
Question: What is the current market cap of the company that created ChatGPT?

Thought: I need to find out which company created ChatGPT, then look up their market cap.
Action: search("company that created ChatGPT")
Observation: ChatGPT was created by OpenAI, an AI research company.

Thought: Now I need to find OpenAI's current market cap.
Action: search("OpenAI market cap 2025")
Observation: OpenAI's valuation reached $157 billion in 2024 after their latest funding round.

Thought: I now have the information needed to answer.
Answer: ChatGPT was created by OpenAI, which has a valuation of approximately $157 billion (as of their 2024 funding round). Note: OpenAI is a private company, so this is a valuation rather than a public market cap.
```

### ReAct 实现模式

```python
def react_loop(question: str, tools: dict, max_iterations: int = 10) -> str:
    """Execute a ReAct reasoning loop."""
    context = f"Question: {question}\n\n"

    for i in range(max_iterations):
        # Get next thought and action from LLM
        response = llm.complete(REACT_PROMPT + context)

        # Parse thought and action
        thought, action = parse_react_response(response)
        context += f"Thought: {thought}\n"

        if action.startswith("Answer:"):
            return action.replace("Answer:", "").strip()

        # Execute action and get observation
        tool_name, params = parse_action(action)
        observation = tools[tool_name](*params)

        context += f"Action: {action}\n"
        context += f"Observation: {observation}\n\n"

    return "Max iterations reached without answer."
```

---

## 思维树（ToT）

**何时使用**：需要探索多个解决方案路径的复杂问题、创造性问题解决、战略规划。

**何时不使用**：简单任务、时间敏感操作或令牌预算有限的情况。

### ToT 结构

```
Problem: {complex_problem}

## Generate Candidate Approaches

### Approach A: [First strategy]
- Pros: [advantages]
- Cons: [disadvantages]
- Estimated success: [low/medium/high]

### Approach B: [Second strategy]
- Pros: [advantages]
- Cons: [disadvantages]
- Estimated success: [low/medium/high]

### Approach C: [Third strategy]
- Pros: [advantages]
- Cons: [disadvantages]
- Estimated success: [low/medium/high]

## Evaluate and Select

Based on the analysis, Approach [X] is most promising because [reasoning].

## Execute Selected Approach

[Detailed execution of chosen approach]

## Verify Solution

[Check if solution meets requirements]
```

### ToT 用于代码架构

```
Design a caching system for a high-traffic API endpoint.

## Candidate Architectures

### Option A: In-Memory Cache (Redis)
Thought: Use Redis for distributed caching
Evaluation:
- Latency: ~1ms (excellent)
- Scalability: Horizontal scaling supported
- Complexity: Low - well-established pattern
- Risk: Cache invalidation complexity
Score: 8/10

### Option B: CDN Edge Caching
Thought: Cache at CDN level for static/semi-static content
Evaluation:
- Latency: ~10-50ms (good)
- Scalability: Excellent - distributed globally
- Complexity: Medium - cache headers management
- Risk: Stale content for dynamic data
Score: 6/10

### Option C: Multi-Layer Cache
Thought: Combine L1 (local) + L2 (Redis) + L3 (CDN)
Evaluation:
- Latency: <1ms for hot data
- Scalability: Excellent
- Complexity: High - multiple invalidation points
- Risk: Consistency challenges
Score: 7/10

## Decision
Option A (Redis) selected for initial implementation:
- Lowest complexity for team's current expertise
- Sufficient performance for projected load
- Clear upgrade path to Option C if needed

## Implementation Plan
[Detailed implementation steps...]
```

---

## 模式比较快速参考

```
┌────────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│    Pattern     │   Tokens     │  Complexity  │  Reliability │   Best For   │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│   Zero-shot    │     Low      │     Low      │    Medium    │ Simple tasks │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│   Few-shot     │    Medium    │    Medium    │     High     │Format/style  │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│      CoT       │    Medium    │    Medium    │     High     │  Reasoning   │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│     ReAct      │     High     │     High     │  Very High   │ Tool usage   │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│      ToT       │  Very High   │  Very High   │  Very High   │Complex solve │
└────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 组合模式

模式可以组合以创建更强大的提示：

### 少样本 + CoT

```
Solve math word problems by showing your work.

Example 1:
Problem: If a train travels 60 mph for 2.5 hours, how far does it go?
Solution:
- Distance = Speed × Time
- Distance = 60 mph × 2.5 hours
- Distance = 150 miles
Answer: 150 miles

Example 2:
Problem: A store has a 20% off sale. If an item costs $45, what's the sale price?
Solution:
- Discount = Original × Discount Rate
- Discount = $45 × 0.20 = $9
- Sale Price = Original - Discount
- Sale Price = $45 - $9 = $36
Answer: $36

Problem: {new_problem}
Solution:
```

### ReAct + CoT

```
Thought: Let me break this down step by step.
First, I need to understand what information I'm looking for...
[reasoning]
Based on this analysis, I should search for...
Action: search("specific query based on reasoning")
```

---

## 相关技能

- **RAG 架构师** - 用于提示基础的检索模式
- **微调专家** - 当提示不足时
- **LLM 架构师** - 系统级提示编排