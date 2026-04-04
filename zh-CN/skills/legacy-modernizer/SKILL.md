---
name: legacy-modernizer
description: Designs incremental migration strategies, identifies service boundaries, produces dependency maps and migration roadmaps, and generates API facade designs for aging codebases. Use when modernizing legacy systems, implementing strangler fig pattern or branch by abstraction, decomposing monoliths, upgrading frameworks or languages, or reducing technical debt without disrupting business operations.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: specialized
  triggers: legacy modernization, strangler fig, incremental migration, technical debt, legacy refactoring, system migration, legacy system, modernize codebase
  role: specialist
  scope: architecture
  output-format: code+analysis
  related-skills: test-master, devops-engineer
---

# Legacy Modernizer

## 核心工作流程

1. **评估系统** — 分析代码库、依赖关系、风险和业务约束。在继续之前生成依赖图和风险登记表。
   - *验证检查点：* 确认所有外部集成和数据契约已记录后再进入步骤 2。

2. **规划迁移** — 设计带有明确回滚策略的增量路线图。参考 `references/system-assessment.md` 中的代码分析模板。
   - *验证检查点：* 确认每个阶段都有明确的回滚触发器和负责人。

3. **构建安全网** — 在修改生产代码之前创建特征化测试和监控。目标覆盖现有行为 80% 以上。
   - *验证检查点：* 运行特征化测试套件，确认在未修改的遗留系统上全部通过后再继续。

4. **增量迁移** — 使用功能标志应用绞杀者模式。通过门面路由流量；逐步转移负载。
   - *验证检查点：* 验证每次流量增加后错误率和延迟指标保持在基线阈值内（例如 5% → 25% → 50% → 100%）。

5. **验证与迭代** — 运行完整测试套件，审查监控仪表板，在退役遗留代码之前确认业务行为已保留。
   - *验证检查点：* 新代码必须在 100% 流量下稳定运行至少一个发布周期后才能移除遗留路径。

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| 绞杀者模式 | `references/strangler-fig-pattern.md` | 增量替换、门面层、路由 |
| 重构 | `references/refactoring-patterns.md` | 提取服务、抽象分支、适配器 |
| 迁移 | `references/migration-strategies.md` | 数据库、UI、API、框架迁移 |
| 测试 | `references/legacy-testing.md` | 特征化测试、黄金大师、审批测试 |
| 评估 | `references/system-assessment.md` | 代码分析、依赖映射、风险评估 |

## 代码示例

### 绞杀者模式门面（Python）
```python
# facade.py — 根据功能标志将请求路由到遗留或新服务
import os
from legacy_service import LegacyOrderService
from new_service import NewOrderService

class OrderServiceFacade:
    def __init__(self):
        self._legacy = LegacyOrderService()
        self._new = NewOrderService()

    def get_order(self, order_id: str):
        if os.getenv("USE_NEW_ORDER_SERVICE", "false").lower() == "true":
            return self._new.fetch(order_id)
        return self._legacy.get(order_id)
```

### 功能标志包装器
```python
# feature_flags.py — 环境或配置标志的轻量包装
import os

def flag_enabled(flag_name: str, default: bool = False) -> bool:
    """检查迁移功能标志是否激活。"""
    return os.getenv(flag_name, str(default)).lower() == "true"

# 使用示例
if flag_enabled("USE_NEW_PAYMENT_GATEWAY"):
    result = new_gateway.charge(order)
else:
    result = legacy_gateway.charge(order)
```

### 特征化测试模板（pytest）
```python
# test_characterization_orders.py
# 捕获现有遗留行为作为黄金大师安全网。
import pytest
from legacy_service import LegacyOrderService

service = LegacyOrderService()

@pytest.mark.parametrize("order_id,expected_status", [
    ("ORD-001", "SHIPPED"),
    ("ORD-002", "PENDING"),
    ("ORD-003", "CANCELLED"),
])
def test_order_status_golden_master(order_id, expected_status):
    """如果遗留行为意外改变则大声失败。"""
    result = service.get(order_id)
    assert result["status"] == expected_status, (
        f"Characterization broken for {order_id}: "
        f"expected {expected_status}, got {result['status']}"
    )
```

## 约束

### 必须做
- 在所有迁移过程中保持零生产中断
- 在重构之前创建全面的测试覆盖（目标 80%+）
- 对所有增量发布使用功能标志
- 实现监控和回滚程序
- 记录所有迁移决策和理由
- 保留现有业务逻辑和行为
- 透明地传达进展和风险

### 不能做
- 大爆炸式重写或替换
- 在修改之前跳过遗留行为的测试
- 不具备回滚能力就部署
- 破坏现有集成或 API
- 在新代码中忽视技术债务
- 没有适当验证就仓促迁移
- 在新代码被证明稳定之前移除遗留代码

## 输出模板

实现现代化时，请提供：
1. 评估摘要（风险、依赖、方法）
2. 迁移计划（阶段、回滚策略、指标）
3. 实现代码（门面、适配器、新服务）
4. 测试覆盖（特征化、集成、端到端）
5. 监控设置（指标、告警、仪表板）

## 知识参考

绞杀者模式、抽象分支、特征化测试、增量迁移、功能标志、金丝雀部署、API 版本化、数据库重构、微服务提取、技术债务削减、零停机部署
