---
name: anthropic-diagram
description: 生成符合 Anthropic 博客视觉风格的编辑型图表，输出为 .drawio 文件。当用户想要创建图表、流程图、架构图、对比图、泳道图或任何看起来像 Anthropic 博客文章插图的视觉效果时使用此技能。在以下提示时触发："画流程图"、"画架构图"、"帮我画"、"创建流程图"、"可视化流程"，或将文本/流程描述转换为可视化的任何请求——即使没有明确说明使用 "Anthropic 风格"。此技能可生成 Anthropic 技术博客典型的平静、编辑、出版质量的外观。
tags: ["visualization", "diagram", "flowchart", "architecture", "utility", "drawing"]
triggers: ["画流程图", "画架构图", "帮我画", "创建流程图", "可视化流程", "生成图表", "画图", "架构图"]
priority: 6
---

# Anthropic 风格图表技能

生成符合 Anthropic 博客文章插图风格的 draw.io 图表——编辑型、温暖、极简主义。

## 工作流程

```
用户文本 → DiagramSpec（以文本形式写出）→ 带样式的 draw.io XML → .drawio 文件
```

---

## 步骤 1：分析请求

确定：
- **核心论点**：这个图表应该让什么变得显而易见？
- **模式**：哪种视觉模式最能服务于这个论点？（参见步骤 2 和 `references/pattern-library.md`）
- **阅读方向**：工作流/对比从左到右；堆栈/层级从上到下

当不确定模式时，默认规则：
- 顺序步骤 → 线性工作流
- 系统组件/包含关系 → 分组架构
- 前后对比或两种方法 → 分屏对比
- 多个参与者随时间交互 → 泳道图
- 重叠/共享所有权 → 维恩图
- 数值对比 → 编辑型图表

---

## 步骤 2：构建 DiagramSpec

在编写任何 XML 之前，先用文本明确写出图表计划——这有助于在提交 XML 之前捕获结构错误，并让用户看到你的推理过程。按以下格式输出 DiagramSpec：

```
**DiagramSpec**

main_claim: [一句话——这个图表要表达什么？]
pattern: [主要模式]
secondary_pattern: [可选，或 none]
reading_direction: [left-to-right / top-to-bottom]
title: "图表标题"

nodes:
  - id: n1
    label: "简短标签"
    semantic_type: [primary | secondary | tertiary | start | end | warning | decision | ai_llm | inactive | error]
    shape: [rect | pill | diamond | cylinder]
    group: [如果在容器内则为容器 ID，否则为 none]

connections:
  - from: n1
    to: n2
    label: ""          # 保持简短或为空
    style: [primary | optional | feedback | human | context | error]

groups:
  - id: g1
    label: "面板标题"
    type: [outer_panel | inner_panel | swimlane | soft_region]
    children: [n1, n2, ...]
```

这是一个内部规划步骤——在提交 XML 之前，在自己的推理中明确结构。编写 DiagramSpec 后，**立即继续步骤 3**，无需等待用户确认。阅读 `references/pattern-library.md` 了解每种模式类型的布局规则。

**语言一致性**：DiagramSpec 以及最终 XML 中的所有节点标签、标题和边标签都应使用用户相同的语言。如果用户用中文书写，图表文本也应该是中文。标签与用户语言匹配的图表感觉很自然，避免了混合语言视觉效果的不协调。

---

## 步骤 3：生成 draw.io XML

### 画布设置

```xml
<mxGraphModel background="#F2EFE8" grid="0" tooltips="0" connect="0" arrows="0" fold="0" page="0" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
  <!--
  !!! 重要提醒 !!!
  所有 XML 属性值都必须用引号括起来，包括数字类型的值！
  例如：pageScale="1" 而不是 pageScale=1
  -->
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- 所有单元格放在这里，parent="1"（或嵌套时 parent="container_id"） -->
  </root>
</mxGraphModel>
```

大多数图表使用 `background="#F2EFE8"`（温暖画布）。仅对于非常简单、元素稀少的图表使用 `background="#FFFFFF"`。

### 标题

```xml
<mxCell id="title" value="图表标题" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;overflow=hidden;fontStyle=1;fontSize=32;fontColor=#1F1F1C;" vertex="1" parent="1">
  <mxGeometry x="80" y="40" width="1200" height="50" as="geometry"/>
</mxCell>
```

### 按语义类型的节点样式字符串

根据语义角色应用这些样式，而不仅仅是美学。颜色编码含义。

| 语义类型 | draw.io 样式 |
|---|---|
| **主要 / 中性** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#E6E2DA;strokeColor=#8C867F;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **次要 / 上下文（文件、工具、文档）** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#EAF4FB;strokeColor=#6FA8D6;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **第三层 / 控制（路由、记忆、编排）** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#EEEAF9;strokeColor=#9A90D6;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **起始 / 触发（用户输入、外部触发）** | `rounded=1;whiteSpace=wrap;arcSize=50;fillColor=#F8E9E1;strokeColor=#D88966;strokeWidth=1.8;fontColor=#D88966;fontSize=20;fontStyle=1;` |
| **结束 / 成功** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#CFE8D7;strokeColor=#71AE88;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **警告 / 重置（重试、中断）** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#F3E4DA;strokeColor=#C88E6A;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **决策（分支、关卡、审批）** | `rhombus;whiteSpace=wrap;fillColor=#E6D7B4;strokeColor=#BFA777;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **AI / LLM（模型调用、代理工作者）** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#D7E6DC;strokeColor=#7FB08F;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **非活动 / 已禁用** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#EFECE6;strokeColor=#B4AEA6;strokeWidth=1.8;fontColor=#7A756E;fontSize=20;` |
| **错误** | `rounded=1;whiteSpace=wrap;arcSize=10;fillColor=#F8DFDA;strokeColor=#D96B63;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **胶囊标签** | `rounded=1;whiteSpace=wrap;arcSize=50;fillColor=#FAF8F4;strokeColor=#8C867F;strokeWidth=1.8;fontColor=#2D2B28;fontSize=20;` |
| **代码/证据块** | `rounded=1;whiteSpace=wrap;arcSize=6;fillColor=#EEF3F7;strokeColor=#B7C9D8;strokeWidth=1.5;fontColor=#44515C;fontSize=20;align=left;` |

每种类型的语义含义，请阅读 `references/color-palette.md` → 语义映射规则部分。

### 容器 / 面板样式

所有容器样式都包含 `html=1;`，以便 `value` 属性可以包含 HTML。在 `value` 中使用 `<font>` 标签来控制标签字体大小（通常比样式字符串中的 `fontSize` 大 2-4px，用于视觉层次）。

**外层面板**（大型系统边界）：
```
rounded=1;whiteSpace=wrap;arcSize=4;fillColor=#FAF8F4;strokeColor=#8C867F;strokeWidth=2;fontSize=18;fontStyle=1;fontColor=#5F5A54;swimlane;startSize=63;horizontal=1;html=1;
```
value: `<font style="font-size: 22px;">面板标题</font>`

**内层面板**（子系统或分组）：
```
rounded=1;whiteSpace=wrap;arcSize=6;fillColor=#FAF8F4;strokeColor=#8C867F;strokeWidth=1.8;fontSize=16;fontStyle=1;fontColor=#5F5A54;swimlane;startSize=50;horizontal=1;html=1;
```
value: `<font style="font-size: 20px;">面板标题</font>`

**软区域**（虚线分组，无强边界）：
```
rounded=1;fillColor=#F6F4EE;strokeColor=#B9B3AB;strokeWidth=1.5;dashed=1;dashPattern=6 6;fontSize=16;fontColor=#7A756E;html=1;
```
value: `<font style="font-size: 18px;">区域标签</font>`

### ⚠️ 容器布局重要注意事项

**问题：容器标题覆盖内容**

使用 `swimlane` 样式的容器时，必须正确设置 `horizontal` 参数，否则会导致标题覆盖内容。

#### 布局方向说明

| horizontal 值 | 布局方向 | 标题位置 | 适用场景 |
|--------------|----------|----------|----------|
| `horizontal=1` | **垂直布局** | 标题在**顶部** | 内容从上到下排列（推荐用于列表、参数） |
| `horizontal=0` | 水平布局 | 标题在**左侧** | 内容从左到右排列（用于泳道图） |

#### 正确示例：垂直布局（推荐）

```xml
<!-- 标题在顶部，内容竖排 -->
<mxCell id="panel" value="请求参数" 
  style="swimlane;startSize=50;horizontal=1;... 
  width=380 height=450">
  
  <!-- 子元素 y 坐标必须 > startSize -->
  <mxCell y="60" ...>  <!-- ✅ 正确：从标题下方开始 -->
</mxCell>
```

**布局结构：**
```
┌─────────────────┐
│    请求参数      │ ← 标题区域 (50px)
├─────────────────┤
│ 参数1           │ ← y=60
│ 参数2           │ ← y=110
│ 参数3           │ ← y=160
└─────────────────┘
```

#### 错误示例：水平布局（容易覆盖）

```xml
<!-- 标题在左侧，容易覆盖内容 -->
<mxCell id="panel" value="请求参数" 
  style="swimlane;startSize=50;horizontal=0;... 
  width=380 height=450">
  
  <!-- 子元素 y 坐标会被标题覆盖 -->
  <mxCell y="50" ...>  <!-- ❌ 可能被标题区域覆盖 -->
</mxCell>
```

**布局结构：**
```
┌─┬─────────────────┐
│标│    请求参数      │ ← 标题在左侧
│题├─────────────────┤
│区│ 内容1           │ ← 可能被覆盖
│域│ 内容2           │
└─┴─────────────────┘
```

#### 关键规则

1. **默认使用 `horizontal=1`**（垂直布局）- 这是大多数情况的安全选择
2. **子元素的 y 坐标必须 > startSize**
3. **建议 startSize 值：** 外层面板 63，内层面板 50
4. **容器高度 = startSize + 内容高度 + 间距**

#### 调试技巧

如果发现内容被标题覆盖：
1. 检查 `horizontal` 值，是否应该为 `1`
2. 检查子元素的 `y` 坐标是否 `> startSize`
3. 增加容器高度或调整 startSize
4. 考虑使用简单的分组框代替 swimlane

外层面板的 XML 示例：
```xml
<mxCell id="panel_server" parent="1" style="rounded=1;whiteSpace=wrap;arcSize=4;fillColor=#FAF8F4;strokeColor=#8C867F;strokeWidth=2;fontSize=18;fontStyle=1;fontColor=#5F5A54;swimlane;startSize=63;horizontal=1;html=1;" value="&lt;font style=&quot;font-size: 22px;&quot;&gt;面板标题&lt;/font&gt;" vertex="1">
  <mxGeometry x="580" y="110" width="480" height="920" as="geometry"/>
</mxCell>
```

容器的子元素使用 `parent="container_id"` 和相对于容器的坐标。

### 连接器样式

**最重要的样式规则**：所有箭头都使用开放式 V 形箭头。

```
endArrow=open;endSize=14;
```

这就是 Anthropic 图表具有干净、编辑外观的原因。永远不要使用实心/块状箭头。

所有连接器也使用 `edgeStyle=orthogonalEdgeStyle`——这使得线条以直角弯曲，给图表一种干净、结构化的感觉。结合 `rounded=1`，角部被软化为平滑曲线，而不是硬 90° 转弯。

| 连接器类型 | 完整样式 |
|---|---|
| **主要流程** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#7A756E;strokeWidth=1.8;rounded=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;` |
| **可选 / 推断** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#9A948C;strokeWidth=1.6;rounded=1;dashed=1;dashPattern=6 6;` |
| **反馈循环** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#8E8982;strokeWidth=1.8;rounded=1;curved=1;` |
| **人工干预** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#D88966;strokeWidth=1.8;rounded=1;dashed=1;dashPattern=6 6;` |
| **上下文 / 支持** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#7FB08F;strokeWidth=1.8;rounded=1;` |
| **错误路径** | `endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#D96B63;strokeWidth=1.8;rounded=1;` |

每个边单元格都必须有一个子几何元素——永远不要自闭合：
```xml
<mxCell id="e1" edge="1" source="n1" target="n2" style="endArrow=open;endSize=14;edgeStyle=orthogonalEdgeStyle;strokeColor=#7A756E;strokeWidth=1.8;rounded=1;" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

---

## 步骤 4：布局规则

这些规则保持图表感觉平静和构图良好：

- **节点间距**：相邻节点之间最小水平间距 80px；垂直间距 60px
- **推荐水平间距**：工作流步骤的中心到中心 200px
- **推荐垂直间距**：并行元素的中心到中心 120px
- **画布填充**：最外层内容周围 60px
- **网格对齐**：所有位置对齐到 10 的倍数
- **节点大小**：标准节点 140×60 到 180×70；宽容器 300-600+；标题栏高度 40
- **保持布局平坦**：最多 3 层嵌套；优先使用留白而不是额外的容器

特定于模式的布局规则（泳道车道宽度、比较面板大小、发散间距等），请阅读 `references/pattern-library.md` → 相关模式部分。

### 外边框

每个图表都有一个单一的外边框——一个细圆角矩形，框住整个构图（标题 + 所有内容）。这给图表一种海报般的完成感，使留白感觉是有意的而不是偶然的。

- 将此单元格放在 XML 的**第一位**，在所有其他节点之前，以便它渲染在所有内容的后面
- `x=20, y=20`；width = pageWidth − 40（标准 1654px 画布 → **1614**）
- 高度：在最底部节点下方延伸约 40px——足够紧凑以感觉连贯，足够宽松以呼吸
- 样式：微妙的暖色描边，无填充（画布背景显示出来）

```xml
<mxCell id="border" value="" style="rounded=0;arcSize=3;fillColor=none;strokeColor=#B9B3AB;strokeWidth=1.5;pointerEvents=0;" vertex="1" parent="1">
  <mxGeometry x="20" y="20" width="1614" height="1000" as="geometry"/>
</mxCell>
```

调整 `height` 使其在最底部元素下方约 40px 结束。`pointerEvents=0` 使其非交互，以便用户可以在 draw.io 中点击它。

---

## 步骤 5：写入并打开

1. 将完整的 XML 写入当前工作目录中描述性的 `.drawio` 文件。
   - 文件名：小写带连字符，例如 `agent-loop.drawio`、`context-engineering.drawio`
2. 打开文件：`start <filename>.drawio`（Windows）或 `open <filename>.drawio`（macOS）

如果用户要求 PNG/SVG 导出：
```bash
"C:\Program Files\draw.io\draw.io.exe" -x -f png -e -b 20 -o output.drawio.png input.drawio
```

---

## 质量检查清单

在最终确定 XML 之前，验证：

- [ ] 外边框存在（`id="border"`，XML 中的第一个单元格，x=20 y=20，width=1614，height 覆盖所有内容 + 40px）
- [ ] 标题大（fontSize≥28）、粗体、深色（#1F1F1C）、水平居中
- [ ] 画布背景设置（mxGraphModel 中的 `background="#F2EFE8"`）
- [ ] 每个箭头使用 `endArrow=open;endSize=14`
- [ ] 节点颜色遵循语义含义，而非装饰
- [ ] 主流程路径在 3 秒内视觉上占主导地位
- [ ] 一个图表中不超过 4 种语义强调色
- [ ] 每条边都有 `<mxGeometry relative="1" as="geometry"/>`
- [ ] 所有坐标都是 10 的倍数
- [ ] XML 注释中没有 `--`（无效 XML）
- [ ] 特殊字符转义：`&amp;` `&lt;` `&gt;`
- [ ] **所有 XML 属性值必须用引号括起**（包括数字类型）
- [ ] **容器布局正确**：使用 `horizontal=1`（垂直布局），子元素 y 坐标 > startSize
- [ ] **容器内容不被标题覆盖**：检查 swimlane 容器的 startSize 和子元素位置

---

## 常见错误与调试技巧

### 错误 1：属性值缺少引号

**错误示例**：
```xml
<!-- ❌ 错误：数字属性值没有引号 -->
<mxGraphModel pageScale=1 pageWidth=1654>
<mxGeometry x=20 y=20 width=1614>

<!-- ✅ 正确：所有属性值都必须有引号 -->
<mxGraphModel pageScale="1" pageWidth="1654">
<mxGeometry x="20" y="20" width="1614">
```

**错误提示**：`AttValue: " or ' expected`

### 错误 2：value 属性中的引号未转义

**错误示例**：
```xml
<!-- ❌ 错误：value 中直接使用双引号 -->
<mxCell value="<font style="font-size: 18px;">标题</font>">

<!-- ✅ 正确：使用 &quot; 转义双引号 -->
<mxCell value="&lt;font style=&quot;font-size: 18px;&quot;&gt;标题&lt;/font&gt;">
```

**错误提示**：`attributes construct error`

### 错误 3：value 内容过于复杂

**问题**：当 value 属性包含大量代码、特殊字符或多行文本时，容易导致解析错误。

**建议**：
- 将复杂内容拆分到多个节点
- 使用换行符 `&#10;` 代替真正的多行文本
- 代码示例应该放在独立的节点中，而不是 value 属性里

**错误示例**：
```xml
<!-- ❌ 不推荐：value 中包含复杂的代码片段 -->
<mxCell value="UrlBuilder urlBuilder = UrlBuilder.of(dingTalkUrl);
urlBuilder.addQuery(ACCESS_TOKEN, token);
String body = HttpRequest.post(url)...">

<!-- ✅ 推荐：简化 value，将详细内容放在单独的节点中 -->
<mxCell value="构建 URL">
<!-- 详细的代码说明放在另一个节点中 -->
```

### 错误 4：XML 注释中使用双横线

**错误示例**：
```xml
<!-- ❌ 错误：注释中包含 -- -->
<!-- 这是一个示例 -- 还有更多 -->

<!-- ✅ 正确：避免使用双横线 -->
<!-- 这是一个示例 - 还有更多 -->
```

**错误提示**：`--  within XML comments`

### 错误 5：容器标题覆盖内容

**错误示例**：
```xml
<!-- ❌ 错误：使用 horizontal=0（水平布局）导致标题覆盖内容 -->
<mxCell id="panel" value="请求参数" 
  style="swimlane;startSize=50;horizontal=0;... 
  width=380 height=450">
  <mxCell y="50" value="参数1" ...>  <!-- 被标题区域覆盖 -->
  <mxCell y="100" value="参数2" ...> <!-- 可能也被覆盖 -->
</mxCell>
```

**布局效果：**
```
┌─┬─────────────────┐
│标│    请求参数      │ ← 标题在左侧占据左侧区域
│题├─────────────────┤
│区│ 参数1           │ ← y=50，可能被标题区域覆盖
│域│ 参数2           │ ← y=100，也可能被覆盖
└─┴─────────────────┘
```

**正确示例**：
```xml
<!-- ✅ 正确：使用 horizontal=1（垂直布局），标题在顶部 -->
<mxCell id="panel" value="请求参数" 
  style="swimlane;startSize=50;horizontal=1;... 
  width=380 height=450">
  <mxCell y="60" value="参数1" ...>  <!-- 在标题下方 -->
  <mxCell y="110" value="参数2" ...> <!-- 垂直排列 -->
</mxCell>
```

**布局效果：**
```
┌─────────────────┐
│    请求参数      │ ← 标题在顶部 (50px)
├─────────────────┤
│ 参数1           │ ← y=60，从标题下方开始
│ 参数2           │ ← y=110，垂直排列
│ 参数3           │ ← y=160，继续向下
└─────────────────┘
```

**关键规则**：
1. **默认使用 `horizontal=1`**（垂直布局）- 适合大多数场景
2. **子元素的 y 坐标必须 > startSize**
3. **推荐 startSize 值**：50-60px
4. **容器高度** = startSize + 所有子元素高度 + 间距

**何时使用 horizontal=0**：
- 仅用于真正的泳道图（多个参与者按时间交互）
- 需要左侧显示参与者名称时

**何时使用 horizontal=1**：
- 参数列表、配置说明
- 功能模块分组
- 大多数分组场景

### 调试技巧

1. **使用 XML 验证器**：在保存文件前，使用在线 XML 验证器检查语法
2. **分步测试**：先创建简单的图表，确认可以打开后再添加复杂内容
3. **检查特殊字符**：确保所有 `<`、`>`、`&`、`"` 都已正确转义
4. **简化内容**：遇到解析错误时，尝试删除部分内容，定位问题所在

### 推荐的 value 内容格式

```xml
<!-- 简单文本 -->
<mxCell value="简单标签">

<!-- 带换行的文本 -->
<mxCell value="第一行&#10;第二行&#10;第三行">

<!-- HTML 格式（需要转义） -->
<mxCell value="&lt;b&gt;粗体&lt;/b&gt;和&lt;i&gt;斜体&lt;/i&gt;">

<!-- 避免在 value 中使用 -->
<!-- ❌ 复杂代码片段 -->
<!-- ❌ 多行代码块 -->
<!-- ❌ 大量特殊字符 -->
```

---

## 参考文件

- `references/color-palette.md` — 完整的语义颜色规则、文本层次、容器规范、背景值、几何标记。当需要选择颜色或验证语义映射时阅读。
- `references/pattern-library.md` — 12 种图表模式，包含布局规则、反模式和组合规则。当模式选择不明确或布局需要微调时阅读。
