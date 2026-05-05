# DeepAgents 中间件架构与 Skill 加载机制深入分析

## 目录

1. [整体架构概览](#1-整体架构概览)
2. [中间件详解](#2-中间件详解)
3. [Skill 渐进加载流程](#3-skill-渐进加载流程)
4. [自定义提示词替换指南](#4-自定义提示词替换指南)
5. [Skill 命中执行指南](#5-skill-命中执行指南)
6. [Skill Scripts 高效设计](#6-skill-scripts-高效设计)
7. [实战代码示例](#7-实战代码示例)

---

## 1. 整体架构概览

### 1.1 DeepAgents 在 LLM 请求生命周期中的位置

DeepAgents 是一个基于 LangChain/LangGraph 的 Agent 框架，通过**中间件（Middleware）**模式在 LLM 与工具之间插入处理层。

```
User Request
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                      AgentGraph                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ Middleware  │───▶│    LLM      │───▶│    Tools    │    │
│  │   Stack     │    │             │    │             │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 中间件执行顺序（来自 graph.py）

在 `create_deep_agent()` 中，中间件按以下顺序组装：

**主 Agent 中间件栈顺序：**

```
1. TodoListMiddleware           # Todo列表管理
2. SkillsMiddleware              # 技能系统 (如果 skills 参数被提供)
3. FilesystemMiddleware          # 文件系统工具
4. SubAgentMiddleware            # 子代理管理
5. SummarizationMiddleware       # 对话压缩
6. PatchToolCallsMiddleware      # 工具调用补丁
7. AsyncSubAgentMiddleware       # 异步子代理 (如果有)
8. [用户自定义中间件]            # 用户传入的 middleware 参数
9. Profile extra_middleware      # Provider特定中间件
10. _ToolExclusionMiddleware     # 工具排除 (如果 profile 有 excluded_tools)
11. AnthropicPromptCachingMiddleware  # Anthropic 提示缓存
12. MemoryMiddleware              # 内存系统 (如果 memory 参数被提供)
13. HumanInTheLoopMiddleware      # 人机交互 (如果 interrupt_on 被设置)
14. _PermissionMiddleware         # 权限控制 (最后执行)
```

---

## 2. 中间件详解

### 2.1 SkillsMiddleware (`skills.py`)

**作用**：加载和管理 Agent Skills，实现渐进式信息披露（Progressive Disclosure）。

**核心功能**：

| 功能 | 说明 |
|------|------|
| 从 backend 加载 SKILL.md | 解析 YAML frontmatter 获取元数据 |
| 注入系统提示 | 将 skill 列表注入到每次 LLM 请求的系统消息中 |
| 渐进式披露 | 先显示 name/description，完整内容按需读取 |

**关键代码路径**：

```python
# 1. before_agent() 或 abefore_agent() - 加载阶段
#    扫描 sources 目录，找到所有包含 SKILL.md 的子目录
#    下载并解析每个 SKILL.md 的 frontmatter
#    将结果存入 state["skills_metadata"]

# 2. modify_request() / wrap_model_call() - 注入阶段
#    将 skills_metadata 格式化为系统提示的一部分
#    每次 LLM 请求都会携带这个信息
```

**SKILLS_SYSTEM_PROMPT 模板**：

```python
SKILLS_SYSTEM_PROMPT = """
## Skills System

You have access to a skills library that provides specialized capabilities.

{skills_locations}

**Available Skills:**

{skills_list}

**How to Use Skills (Progressive Disclosure):**
1. Recognize when a skill applies
2. Read the skill's full instructions via read_file
3. Follow the skill's instructions
4. Access supporting files via absolute paths
```

### 2.2 MemoryMiddleware (`memory.py`)

**作用**：从 AGENTS.md 文件加载持久上下文，注入到系统提示。

**MEMORY_SYSTEM_PROMPT 模板**：

```python
MEMORY_SYSTEM_PROMPT = """<agent_memory>
{agent_memory}
</agent_memory>

<memory_guidelines>
    # 学习指南：何时更新记忆、如何遗忘临时信息
</memory_guidelines>
"""
```

**与 SkillsMiddleware 的区别**：

| 特性 | MemoryMiddleware | SkillsMiddleware |
|------|------------------|------------------|
| 加载时机 | 每次请求都注入 | 只加载一次到 state |
| 内容性质 | 持久上下文 | 按需调用的工作流 |
| 触发方式 | 自动注入 | 需要 LLM 识别后主动读取 |

### 2.3 FilesystemMiddleware (`filesystem.py`)

**作用**：提供文件系统操作工具（ls, read_file, write_file, edit_file, glob, grep, execute）。

**工具列表**：

| 工具 | 功能 |
|------|------|
| `ls` | 列出目录内容 |
| `read_file` | 读取文件（支持分页 offset/limit） |
| `write_file` | 创建新文件 |
| `edit_file` | 精确字符串替换 |
| `glob` | Glob 模式匹配文件 |
| `grep` | 文本搜索 |
| `execute` | 执行 shell 命令（需要 backend 支持） |

### 2.4 SubAgentMiddleware (`subagents.py`)

**作用**：通过 `task` 工具启动子代理，实现任务隔离和并行执行。

**TASK_SYSTEM_PROMPT**：

```python
TASK_SYSTEM_PROMPT = """## `task` (subagent spawner)

When to use:
- 复杂多步骤任务
- 独立可并行任务
- 需要专注推理或大量 token 的任务
- 需要沙箱隔离的任务

When NOT to use:
- 需要看中间步骤
- 简单任务
- 委托不能减少 token 使用
```

### 2.5 SummarizationMiddleware (`summarization.py`)

**作用**：当对话 token 超过阈值时，自动压缩历史消息。

**关键参数**：

```python
trigger=("fraction", 0.85)  # 触发压缩的阈值（85% 上下文）
keep=("fraction", 0.10)     # 压缩后保留最近 10%
```

### 2.6 _PermissionMiddleware (`permissions.py`)

**作用**：在工具执行前/后检查文件系统权限。

**权限规则评估顺序**：

1. 按声明顺序遍历规则
2. 第一个匹配的规则生效
3. 如果无匹配，默认允许（permissive default）

### 2.7 _ToolExclusionMiddleware (`_tool_exclusion.py`)

**作用**：从模型请求中过滤掉指定工具。

**放置位置**：必须在所有工具注入中间件**之后**执行。

### 2.8 AnthropicPromptCachingMiddleware

**作用**：为 Anthropic 模型启用提示缓存（Beta）。

---

## 3. Skill 渐进加载流程

### 3.1 完整流程图

```
┌──────────────────────────────────────────────────────────────────┐
│                    create_deep_agent()                            │
│                                                                   │
│  1. 初始化 Backend                                                 │
│     └── StateBackend() 或 FilesystemBackend()                    │
│                                                                   │
│  2. 构建中间件栈                                                   │
│     └── SkillsMiddleware(backend=backend, sources=["/skills/"])  │
│                                                                   │
│  3. Agent 首次执行 → abefore_agent()                              │
│     │                                                              │
│     ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ SkillsMiddleware.abefore_agent()                            │  │
│  │                                                              │  │
│  │  for source_path in sources:                                │  │
│  │      backend.als(source_path)  # 列出目录                    │  │
│  │          │                                                   │  │
│  │          ▼                                                   │  │
│  │      找出所有子目录（每个代表一个 skill）                      │  │
│  │          │                                                   │  │
│  │          ▼                                                   │  │
│  │      backend.adownload_files([skill_dir/SKILL.md, ...])    │  │
│  │          │                                                   │  │
│  │          ▼                                                   │  │
│  │      _parse_skill_metadata()  # 解析 YAML frontmatter        │  │
│  │          │                                                   │  │
│  │          ▼                                                   │  │
│  │      all_skills[skill["name"]] = skill  # 后面的覆盖前面的   │  │
│  │                                                              │  │
│  │  return SkillsStateUpdate(skills_metadata=list(all_skills)) │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  4. 状态更新完成，skills_metadata 已填充                          │
│                                                                   │
│  5. 每次 LLM 请求 → modify_request()                              │
│     │                                                              │
│     ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ SkillsMiddleware.modify_request()                         │  │
│  │                                                              │  │
│  │  skills_list = _format_skills_list(skills_metadata)        │  │
│  │  # 格式化为：                                                │  │
│  │  # - **skill-name**: description                           │  │
│  │  #   -> Read `/path/to/skill/SKILL.md` for full instructions│  │
│  │                                                              │  │
│  │  append_to_system_message(request.system_message, ...)      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  6. LLM 看到 skill 列表，可决定何时读取                            │
│                                                                   │
│  7. LLM 执行 read_file(path, limit=1000)                          │
│     │                                                              │
│     ▼                                                              │
│  FilesystemMiddleware 处理 read_file 工具调用                      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Skill 目录结构

```
/skills/
├── base/                    # 基础技能（优先级最低）
│   ├── web-research/
│   │   └── SKILL.md
│   └── code-review/
│       └── SKILL.md
│
├── user/                    # 用户自定义技能
│   └── my-special-skill/
│       ├── SKILL.md
│       ├── scripts/         # 可执行脚本
│       │   └── run.sh
│       ├── references/      # 参考文档
│       │   └── api-docs.md
│       └── assets/          # 资源文件
│           └── template.md
│
└── project/                 # 项目特定技能（优先级最高）
    └── car-sales/
        └── SKILL.md
```

### 3.3 SKILL.md 文件格式

```markdown
---
name: skill-name                    # 必须：技能名称（必须与目录名相同）
description: >-                     # 必须：触发条件描述
  技能用途描述。使用场景描述。
  触发关键词：'xxx', 'yyy', 'zzz'
license: MIT                        # 可选：许可证
compatibility: Python 3.10+         # 可选：兼容性要求
allowed_tools:                      # 可选：推荐工具列表
  - read_file
  - execute
---

# Skill Title

## When to Use
- 详细的使用场景说明

## Process
1. 步骤一
2. 步骤二

## Output Format
期望的输出格式说明
```

---

## 4. 自定义提示词替换指南

### 4.1 系统提示词层次

DeepAgents 的系统提示词由多层组成：

```
final_system_prompt = system_prompt(用户传入) + "\n\n" + base_prompt
```

**base_prompt** 默认是 `BASE_AGENT_PROMPT`，可通过 `_HarnessProfile.base_system_prompt` 替换。

### 4.2 替换方法

#### 方法一：通过 system_prompt 参数

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    system_prompt="你是一个二手车销售顾问，帮助用户选车、购车。",
    skills=["/skills/car-sales/"],
)
```

#### 方法二：替换 base_system_prompt

```python
from deepagents.profiles import _get_harness_profile

profile = _get_harness_profile("anthropic")
profile.base_system_prompt = """
[你的自定义基础提示词]
"""

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    system_prompt="[可选的前置提示词]",
    skills=["/skills/car-sales/"],
)
```

#### 方法三：修改 SkillsMiddleware 的 system_prompt_template

```python
from deepagents.middleware.skills import SkillsMiddleware, SKILLS_SYSTEM_PROMPT

# 自定义 skill 注入模板
CUSTOM_SKILLS_TEMPLATE = """
## 我的自定义技能系统

{skills_list}

## 使用规则
1. ...
"""

middleware = SkillsMiddleware(
    backend=backend,
    sources=["/skills/"],
)
middleware.system_prompt_template = CUSTOM_SKILLS_TEMPLATE
```

#### 方法四：自定义 MemoryMiddleware 内容

```python
from deepagents.middleware.memory import MemoryMiddleware

# 创建自定义内存内容文件
memory_content = """
# 项目记忆

## 核心职责
- 你是专业的汽车销售顾问
- 熟悉各品牌车型的特点和优势

## 沟通风格
- 专业但亲切
- 注重倾听用户需求
"""

# 写入 AGENTS.md 文件
with open("/memory/AGENTS.md", "w") as f:
    f.write(memory_content)

middleware = MemoryMiddleware(
    backend=backend,
    sources=["/memory/AGENTS.md"],
)
```

### 4.3 修改 Middleware 系统提示的工具函数

```python
# deepagents/middleware/_utils.py
def append_to_system_message(system_message, content):
    """将内容追加到系统消息的末尾"""
    if isinstance(system_message, str):
        return SystemMessage(content=system_message.content + content)
    # 处理其他类型的 SystemMessage...
```

---

## 5. Skill 命中执行指南

### 5.1 Skill 匹配机制

LLM 决定是否使用某个 skill 的流程：

```
1. 系统提示包含：skill name + description + path
2. LLM 理解用户意图
3. 如果 description 中的关键词匹配，LLM 决定调用
4. LLM 执行 read_file(path, limit=1000) 读取完整内容
5. 按 skill 中的指示执行
```

### 5.2 提高命中率的策略

#### 策略一：优化 description

**好的描述**：

```markdown
description: >-
  二手车销售助手。当用户说：'我想买辆车'、'推荐一款车'、
  '这款车怎么样'、'落地价多少'、'分期付款'、'油耗'、
  '安全性'、'空间'等选车相关问题时触发。
```

**不好的描述**：

```markdown
description: >-
  车辆销售相关的帮助。
```

#### 策略二：在 base prompt 中强调

```python
agent = create_deep_agent(
    system_prompt="""
    你是一个专业的汽车销售顾问。
    当用户询问任何与汽车相关的问题时，应该先查看 car-sales skill。
    使用技能命令：read_file(/skills/car-sales/SKILL.md, limit=1000)
    """,
)
```

#### 策略三：使用 allowed_tools 引导

```markdown
---
name: car-sales
description: 汽车销售技能
allowed_tools:
  - read_file
  - execute
  - internet_search
---
```

### 5.3 调试 Skill 命中

查看 LLM 请求中是否包含 skill 信息：

```python
# 在 middleware 中打印调试信息
class DebugSkillsMiddleware(SkillsMiddleware):
    def modify_request(self, request):
        print("=== Skills in request ===")
        print(request.system_message)
        return super().modify_request(request)
```

---

## 6. Skill Scripts 高效设计

### 6.1 Scripts 目录用途

Scripts 用于：
1. **确定性任务**：每次运行结果一致
2. **重复性任务**：避免每次重写相同代码
3. **计算密集型**：不适合放在提示词中
4. **外部集成**：调用第三方 API

### 6.2 设计原则

```python
# scripts/analyze_car.py
#!/usr/bin/env python3
"""
汽车分析脚本 - 高效设计示例

设计要点：
1. 接受命令行参数，易于调用
2. 结果输出到 stdout，方便捕获
3. 错误处理完善
4. 日志记录关键步骤
"""

import sys
import json
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="分析汽车数据")
    parser.add_argument("--input", required=True, help="输入文件路径")
    parser.add_argument("--output", default="/docs/analysis.md", help="输出文件路径")
    args = parser.parse_args()

    # 读取输入
    with open(args.input) as f:
        data = json.load(f)

    # 分析逻辑
    results = analyze(data)

    # 输出到 docs 目录
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(results)

    # 同时输出到 stdout（供 LLM 捕获）
    print(json.dumps({"status": "success", "output": str(output_path)}))

def analyze(data):
    # ... 分析逻辑
    pass

if __name__ == "__main__":
    main()
```

### 6.3 SKILL.md 中引用 Scripts

```markdown
## 分析流程

### 步骤 1：数据准备
将用户提供的汽车信息整理为 JSON 格式

### 步骤 2：执行分析
使用内置脚本进行分析：
```
execute(command="python3 /skills/car-sales/scripts/analyze_car.py --input /tmp/car.json --output /docs/analysis.md")
```

### 步骤 3：解读结果
读取输出文件并向用户解释
```

### 6.4 高效运行技巧

1. **使用绝对路径**：避免 cwd 问题
2. **指定输出位置**：结果写入 `/docs/` 目录
3. **stdout + 文件双输出**：既能看到实时输出，也能保存结果
4. **超时控制**：设置合理的 timeout

```python
# 在 execute 时设置超时
execute(command="python3 /path/to/script.py", timeout=60)
```

---

## 7. 实战代码示例

### 7.1 完整示例：创建汽车销售 Skill

**目录结构**：

```
car-sales-agent/
├── skills/
│   └── car-sales/
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── analyze_requirement.py
│       │   └── generate_report.py
│       └── references/
│           └── car_specs.md
└── agent.py
```

**SKILL.md 内容**：

```markdown
---
name: car-sales
description: >-
  二手车销售顾问技能。当用户说：'我想买二手车'、'推荐一款车'、
  '这款车性价比'、'分期付款'、'车况检测'、'过户流程'、
  '保险费用'、'保养成本'等时触发。
  也适用于：选车咨询、购车预算分析、车型对比等场景。
allowed_tools:
  - read_file
  - execute
  - internet_search
---

# 二手车销售顾问

## 服务流程

### 1. 需求了解
- 询问预算范围
- 了解使用场景（家用/商用/通勤）
- 关注偏好（品牌/车型/配置）
- 了解购车时间计划

### 2. 车型推荐
根据需求从数据库或网络搜索合适的车型。

### 3. 对比分析
使用 `scripts/analyze_requirement.py` 进行多维度对比。

### 4. 生成报告
使用 `scripts/generate_report.py` 生成购车建议报告。

## 常用脚本

### 分析需求
```bash
python3 /skills/car-sales/scripts/analyze_requirement.py --budget 10 --usage family
```

### 生成报告
```bash
python3 /skills/car-sales/scripts/generate_report.py --car-id 123 --output /docs/report.md
```

## 参考资料
- 车系规格：`references/car_specs.md`
```

### 7.2 Agent 创建代码

```python
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

# 初始化 backend
backend = FilesystemBackend(root_dir=str(Path(__file__).parent))

# 创建 agent
agent = create_deep_agent(
    name="car-sales-agent",
    model="anthropic:claude-sonnet-4-6",  # 或使用 "openai:gpt-4o"
    backend=backend,
    skills=[
        str(Path(__file__).parent / "skills" / "base"),      # 基础技能
        str(Path(__file__).parent / "skills" / "car-sales"), # 业务技能
    ],
    system_prompt="你是一个专业的二手车销售顾问，帮助用户选车、购车。",
)

# 调用
response = agent.invoke({
    "messages": [{"role": "user", "content": "我预算15万，想买辆家用车，有什么推荐？"}]
})
```

### 7.3 自定义 Skill 提示词模板

```python
from deepagents.middleware.skills import SkillsMiddleware, SKILLS_SYSTEM_PROMPT

# 自定义模板，更强调业务场景
CUSTOM_SKILLS_TEMPLATE = """
## 🎯 业务技能库

您可以使用以下专业技能来更好地服务用户：

{skills_list}

---

**使用提示**：
- 当用户请求涉及特定领域时，先查看对应技能
- 使用 `read_file` 读取完整技能文档
- 按照技能中的流程执行，确保服务标准化

**可用技能位置**：
{skills_locations}
"""

middleware = SkillsMiddleware(
    backend=backend,
    sources=["/skills/business/"],
)
middleware.system_prompt_template = CUSTOM_SKILLS_TEMPLATE
```

### 7.4 多级 Skill 优先级配置

```python
from deepagents import create_deep_agent
from deepagents.backends.state import StateBackend

# 使用 StateBackend 进行内存存储
backend = StateBackend()

# sources 顺序：前面的会被后面的覆盖
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    backend=backend,
    skills=[
        "/skills/base/",        # 优先级1：基础技能（可能被覆盖）
        "/skills/industry/",     # 优先级2：行业技能
        "/skills/custom/",      # 优先级3：自定义技能（最高优先级）
    ],
)

# 验证加载的 skills
# 后面的 /skills/custom/ 中的同名 skill 会覆盖前面的
```

### 7.5 Skill 脚本执行并保存结果到 docs

```python
# scripts/generate_report.py
#!/usr/bin/env python3
"""生成购车报告并保存到 docs 目录"""

import argparse
import json
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--car-name", required=True)
    parser.add_argument("--budget", type=float, required=True)
    parser.add_argument("--output-dir", default="/docs")
    args = parser.parse_args()

    report = f"""# 购车建议报告

**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}**车型**：{args.car_name}
**预算**：{args.budget}万

## 分析结论

（根据脚本分析生成）

## 建议

（具体购车建议）
"""

    # 保存到 docs 目录
    output_path = Path(args.output_dir) / f"report_{args.car_name}_{datetime.now().strftime('%Y%m%d')}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)

    print(f"报告已生成：{output_path}")

if __name__ == "__main__":
    main()
```

### 7.6 完整项目集成示例

```python
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.memory import MemoryMiddleware

# 项目路径
PROJECT_ROOT = Path(__file__).parent
SKILLS_DIR = PROJECT_ROOT / "skills"
MEMORY_DIR = PROJECT_ROOT / "memory"
DOCS_DIR = PROJECT_ROOT / "docs"

# 确保 docs 目录存在
DOCS_DIR.mkdir(exist_ok=True)

# 初始化 backend
backend = FilesystemBackend(root_dir=str(PROJECT_ROOT))

# 加载内存（AGENTS.md）
memory_middleware = MemoryMiddleware(
    backend=backend,
    sources=[
        str(MEMORY_DIR / "AGENTS.md"),
    ],
)

# 创建 agent
agent = create_deep_agent(
    name="car-sales-agent",
    model="anthropic:claude-sonnet-4-6",
    backend=backend,
    skills=[
        str(SKILLS_DIR / "base"),
        str(SKILLS_DIR / "car-sales"),
    ],
    system_prompt="你是一个专业的二手车销售顾问。",
    middleware=[memory_middleware],  # 添加自定义中间件
)

# 对话循环
def chat():
    print("=== 汽车销售顾问 Agent ===")
    print("输入 'quit' 退出\n")

    messages = []
    while True:
        user_input = input("你: ")
        if user_input.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_input})

        response = agent.invoke({"messages": messages})
        assistant_msg = response["messages"][-1].content

        print(f"\n顾问: {assistant_msg}\n")
        messages.append({"role": "assistant", "content": assistant_msg})

if __name__ == "__main__":
    chat()
```

---

## 附录：关键文件路径

| 文件 | 路径 | 用途 |
|------|------|------|
| `skills.py` | `.venv/lib/python*/site-packages/deepagents/middleware/skills.py` | SkillsMiddleware 实现 |
| `memory.py` | `.venv/lib/python*/site-packages/deepagents/middleware/memory.py` | MemoryMiddleware 实现 |
| `filesystem.py` | `.venv/lib/python*/site-packages/deepagents/middleware/filesystem.py` | 文件系统工具 |
| `subagents.py` | `.venv/lib/python*/site-packages/deepagents/middleware/subagents.py` | 子代理管理 |
| `summarization.py` | `.venv/lib/python*/site-packages/deepagents/middleware/summarization.py` | 对话压缩 |
| `permissions.py` | `.venv/lib/python*/site-packages/deepagents/middleware/permissions.py` | 权限控制 |
| `graph.py` | `.venv/lib/python*/site-packages/deepagents/graph.py` | create_deep_agent 主入口 |
| `protocol.py` | `.venv/lib/python*/site-packages/deepagents/backends/protocol.py` | Backend 协议定义 |

---

*文档生成时间：2026-04-24*
*基于 deepagents 0.5.3 版本分析*
