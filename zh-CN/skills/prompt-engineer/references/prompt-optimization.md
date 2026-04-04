# 提示优化

---

## 优化循环

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROMPT OPTIMIZATION CYCLE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐        │
│    │ Baseline │────▶│  Measure │────▶│ Diagnose │────▶│  Change  │        │
│    │  Prompt  │     │ Results  │     │  Issues  │     │   One    │        │
│    └──────────┘     └──────────┘     └──────────┘     └────┬─────┘        │
│         ▲                                                   │              │
│         │                                                   │              │
│         └───────────────────────────────────────────────────┘              │
│                           (Iterate until target met)                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **关键规则：一次只改变一个变量。** 同时进行多个变更会使无法识别有效的方法。

---

## 建立基线

在优化之前，建立明确的指标和基线性能。

### 基线检查清单

```markdown
## Prompt Baseline Document

### Prompt Version: v1.0.0
### Date: YYYY-MM-DD
### Model: claude-opus-4-5-20251101

### Task Definition
[What should the prompt accomplish?]

### Success Criteria
- Primary metric: [e.g., accuracy >= 95%]
- Secondary metrics: [e.g., latency < 2s, cost < $0.01/request]

### Test Set
- Size: [number of test cases]
- Source: [how test cases were collected]
- Categories: [breakdown by type/difficulty]

### Baseline Results
| Metric | Value | Target |
|--------|-------|--------|
| Accuracy | 82% | 95% |
| Avg latency | 1.8s | <2s |
| Avg tokens | 450 | <300 |
| Cost/request | $0.015 | <$0.01 |
```

### 创建代表性测试集

```python
def create_test_set(task_type: str, size: int = 100) -> list:
    """Create a diverse test set for prompt evaluation."""
    test_cases = []

    # Include different categories
    categories = {
        "typical": 0.60,      # Common cases (60%)
        "edge_case": 0.20,    # Boundary conditions (20%)
        "adversarial": 0.10,  # Tricky inputs (10%)
        "malformed": 0.10,    # Invalid/unusual inputs (10%)
    }

    for category, proportion in categories.items():
        count = int(size * proportion)
        test_cases.extend(generate_cases(task_type, category, count))

    return test_cases
```

---

## 诊断框架

当提示表现不佳时，在更改任何内容之前诊断根本原因。

### 失败类别分析

| 失败类型 | 症状 | 常见原因 |
|----------|------|----------|
| **格式错误** | 错误的结构，缺少字段 | 格式规范不明确，没有示例 |
| **幻觉** | 编造事实，错误答案 | 缺乏基础，指令模糊 |
| **不一致性** | 相同输入，不同输出 | 模糊指令，高温度 |
| **过度冗长** | 解释过多 | 没有长度限制，错误的受众 |
| **性能不足** | 全面准确率低 | 错误的模式选择，上下文不足 |
| **边缘案例失败** | 在异常输入上失败 | 缺少约束处理 |

### 诊断问题

```markdown
## Prompt Diagnostic Checklist

### 1. Instruction Clarity
- [ ] Is the task unambiguously defined?
- [ ] Are constraints explicit?
- [ ] Is the output format specified?

### 2. Context Sufficiency
- [ ] Does the model have all needed information?
- [ ] Are examples representative of real inputs?
- [ ] Is domain knowledge assumed correctly?

### 3. Edge Case Coverage
- [ ] Empty inputs?
- [ ] Maximum length inputs?
- [ ] Invalid/malformed inputs?
- [ ] Ambiguous cases?

### 4. Instruction Conflicts
- [ ] Do any instructions contradict each other?
- [ ] Do examples match the instructions?
- [ ] Are constraints achievable together?
```

### 错误分析模板

```python
def analyze_failures(results: list) -> dict:
    """Categorize and analyze prompt failures."""
    analysis = {
        "total": len(results),
        "passed": 0,
        "failed": 0,
        "failure_categories": {},
        "examples": []
    }

    for result in results:
        if result["passed"]:
            analysis["passed"] += 1
        else:
            analysis["failed"] += 1
            category = categorize_failure(result)
            analysis["failure_categories"][category] = \
                analysis["failure_categories"].get(category, 0) + 1

            # Keep first 3 examples per category
            if len([e for e in analysis["examples"] if e["category"] == category]) < 3:
                analysis["examples"].append({
                    "category": category,
                    "input": result["input"],
                    "expected": result["expected"],
                    "actual": result["actual"],
                    "hypothesis": generate_hypothesis(result)
                })

    return analysis
```

---

## 优化技术

### 技术 1：指令细化

**问题**：模糊或模糊的指令导致不一致的输出。

**优化前：**
```
Summarize this article.

{article}
```

**优化后：**
```
Summarize the following article in exactly 2-3 sentences.
Focus on the main conclusion and key supporting evidence.
Do not include quotes or specific numbers unless essential.
Write for a general audience with no assumed domain knowledge.

Article:
{article}

Summary:
```

### 技术 2：约束收紧

**问题**：输出在技术上是正确的，但不满足实际需求。

**优化前：**
```
Extract the email addresses from this text.

{text}
```

**优化后：**
```
Extract all valid email addresses from the following text.

Requirements:
- Return as a JSON array of strings
- Return empty array [] if no emails found
- Only include properly formatted emails (user@domain.tld)
- Deduplicate - each email appears once
- Sort alphabetically

Text:
{text}

Emails:
```

### 技术 3：示例校准

**问题**：少样本示例与真实世界输入分布不匹配。

```python
def calibrate_examples(example_pool: list, real_inputs: list, k: int = 5) -> list:
    """Select examples that match the distribution of real inputs."""
    # Cluster real inputs
    real_clusters = cluster_by_embedding(real_inputs, n_clusters=k)

    # For each cluster, find best matching example
    calibrated = []
    for cluster_center in real_clusters:
        best_match = max(
            example_pool,
            key=lambda ex: cosine_similarity(embed(ex["input"]), cluster_center)
        )
        calibrated.append(best_match)

    return calibrated
```

### 技术 4：输出脚手架

**问题**：模型产生正确的内容但错误的结构。

**优化前：**
```
Analyze this code for security issues.
```

**优化后：**
```
Analyze this code for security issues using the following structure:

## Summary
[One sentence overview]

## Issues Found
For each issue:
- **Severity:** [Critical/High/Medium/Low]
- **Location:** [file:line or function name]
- **Description:** [What's wrong]
- **Fix:** [How to remediate]

## Recommendation
[Overall assessment and priority order for fixes]

Code:
{code}
```

---

## 令牌优化

### 令牌减少策略

| 策略 | 节省 | 风险 | 何时使用 |
|------|------|------|----------|
| 移除冗余指令 | 10-20% | 低 | 总是 |
| 缩短示例 | 20-40% | 中等 | 令牌限制时 |
| 使用缩写/符号 | 5-15% | 中等 | 技术受众 |
| 压缩上下文 | 30-50% | 高 | 非常长的输入 |
| 切换到零样本 | 40-60% | 高 | 简单任务 |

### 优化前后：令牌减少

**优化前（180 个令牌）：**
```
You are a helpful assistant that specializes in analyzing customer feedback
and extracting sentiment information. Your task is to read the customer
review provided below and determine whether the overall sentiment expressed
in the review is positive, negative, or neutral. Please respond with exactly
one word: either "positive", "negative", or "neutral". Do not include any
other text, explanations, or formatting in your response.

Customer Review:
{review}

Sentiment:
```

**优化后（45 个令牌）：**
```
Classify sentiment as: positive, negative, or neutral.
Reply with one word only.

Review: {review}

Sentiment:
```

### 测量令牌影响

```python
import tiktoken

def compare_token_usage(prompt_v1: str, prompt_v2: str, model: str = "gpt-4") -> dict:
    """Compare token usage between two prompt versions."""
    enc = tiktoken.encoding_for_model(model)

    v1_tokens = len(enc.encode(prompt_v1))
    v2_tokens = len(enc.encode(prompt_v2))

    return {
        "v1_tokens": v1_tokens,
        "v2_tokens": v2_tokens,
        "difference": v1_tokens - v2_tokens,
        "reduction_pct": ((v1_tokens - v2_tokens) / v1_tokens) * 100,
        "cost_impact": estimate_cost_savings(v1_tokens, v2_tokens, model)
    }
```

### 上下文压缩技术

```python
def compress_context(text: str, target_ratio: float = 0.5) -> str:
    """Compress context while preserving key information."""

    # Strategy 1: Extractive summarization
    key_sentences = extract_key_sentences(text, ratio=target_ratio)

    # Strategy 2: Remove redundancy
    deduplicated = remove_redundant_info(key_sentences)

    # Strategy 3: Use LLM for compression
    compressed = llm.complete(f"""
    Compress the following text to {int(target_ratio * 100)}% of its length.
    Preserve all facts, numbers, and key details.
    Remove only redundant or low-information content.

    Text: {deduplicated}

    Compressed:
    """)

    return compressed
```

---

## A/B 测试框架

### 测试设计

```python
class PromptABTest:
    """Framework for A/B testing prompt variants."""

    def __init__(self, prompt_a: str, prompt_b: str, test_cases: list):
        self.prompt_a = prompt_a
        self.prompt_b = prompt_b
        self.test_cases = test_cases
        self.results = {"a": [], "b": []}

    def run(self, sample_size: int = 100) -> dict:
        """Run A/B test with randomized assignment."""
        import random

        for test_case in random.sample(self.test_cases, sample_size):
            # Randomize order to avoid position bias
            if random.random() < 0.5:
                result_a = self.evaluate(self.prompt_a, test_case)
                result_b = self.evaluate(self.prompt_b, test_case)
            else:
                result_b = self.evaluate(self.prompt_b, test_case)
                result_a = self.evaluate(self.prompt_a, test_case)

            self.results["a"].append(result_a)
            self.results["b"].append(result_b)

        return self.analyze_results()

    def analyze_results(self) -> dict:
        """Statistical analysis of A/B test results."""
        from scipy import stats

        scores_a = [r["score"] for r in self.results["a"]]
        scores_b = [r["score"] for r in self.results["b"]]

        t_stat, p_value = stats.ttest_ind(scores_a, scores_b)

        return {
            "prompt_a_mean": sum(scores_a) / len(scores_a),
            "prompt_b_mean": sum(scores_b) / len(scores_b),
            "p_value": p_value,
            "significant": p_value < 0.05,
            "winner": "a" if sum(scores_a) > sum(scores_b) else "b",
            "confidence": 1 - p_value
        }
```

### 最小样本量计算

```python
def calculate_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    significance_level: float = 0.05,
    power: float = 0.80
) -> int:
    """Calculate required sample size for detecting a given effect."""
    from scipy import stats

    # Effect size (Cohen's h for proportions)
    p1 = baseline_rate
    p2 = baseline_rate + minimum_detectable_effect
    h = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))

    # Required sample size per group
    z_alpha = stats.norm.ppf(1 - significance_level / 2)
    z_beta = stats.norm.ppf(power)

    n = 2 * ((z_alpha + z_beta) / h) ** 2

    return math.ceil(n)

# Example: Detect 5% improvement from 80% baseline
# sample_size = calculate_sample_size(0.80, 0.05)  # ~783 per group
```

---

## 提示的版本控制

### 提示版本控制模式

```yaml
# prompt_registry.yaml
prompts:
  sentiment_classifier:
    current: v2.1.0
    versions:
      v1.0.0:
        file: prompts/sentiment/v1.0.0.txt
        date: 2024-01-15
        metrics:
          accuracy: 0.82
          latency_p50: 1.2s
        status: deprecated

      v2.0.0:
        file: prompts/sentiment/v2.0.0.txt
        date: 2024-02-01
        metrics:
          accuracy: 0.89
          latency_p50: 1.1s
        changes:
          - Added few-shot examples
          - Tightened output format
        status: deprecated

      v2.1.0:
        file: prompts/sentiment/v2.1.0.txt
        date: 2024-02-15
        metrics:
          accuracy: 0.94
          latency_p50: 1.0s
        changes:
          - Optimized examples for edge cases
          - Reduced token count by 30%
        status: production
```

### 变更文档模板

```markdown
## Prompt Change Record

### Version: v2.0.0 -> v2.1.0
### Date: 2024-02-15
### Author: [name]

### Problem Statement
Accuracy dropped to 85% on sarcastic reviews (edge case category).

### Hypothesis
Current examples don't include sarcastic tone, causing misclassification.

### Changes Made
1. Added 2 sarcastic review examples
2. Added instruction: "Consider tone and context, not just words"
3. Removed verbose instruction paragraph (token optimization)

### Test Results
| Metric | v2.0.0 | v2.1.0 | Change |
|--------|--------|--------|--------|
| Overall accuracy | 89% | 94% | +5% |
| Sarcasm accuracy | 62% | 91% | +29% |
| Tokens | 156 | 109 | -30% |

### Rollback Plan
Revert to v2.0.0 if accuracy drops below 90% in production.
```

---

## 常见优化错误

| 错误 | 为什么错误 | 更好的方法 |
|------|----------|-----------|
| 同时进行多个变更 | 无法识别有效的方法 | 每次迭代只变更一项 |
| 在训练示例上测试 | 对测试集过拟合 | 保留验证集 |
| 优先优化边缘案例 | 可能损害常见情况 | 先修复常见情况 |
| 忽视延迟/成本 | 生产环境约束很重要 | 跟踪所有指标 |
| 没有基线测量 | 无法证明改进 | 总是先测量 |
| 跳过错误分析 | 症状 vs 根本原因 | 更改前先诊断 |

---

## 优化决策树

```
                    ┌──────────────────────────┐
                    │   Prompt Underperforms   │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  What's the failure mode? │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
  Format Issues            Wrong Content           Inconsistent
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ Add output    │      │ Improve       │      │ Add examples  │
│ scaffolding   │      │ instructions  │      │ Lower temp    │
│ Add examples  │      │ Add context   │      │ Add constraints│
└───────────────┘      │ Use CoT       │      └───────────────┘
                       └───────────────┘
```

---

## 相关技能

- **评估框架** - 系统性地测量提示性能
- **微调专家** - 当优化达到极限时
- **成本工程师** - 大规模令牌和延迟优化