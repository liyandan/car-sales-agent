# Deep Agents 库中间件机制与问题解析流程分析

## 1. 概述

`deepagents` 是一个基于 LangChain 和 LangGraph 构建的 AI Agent 框架，提供了丰富的中间件机制来处理文件系统、子代理、技能、内存等功能。本文档详细分析中间件如何生效，以及用户问题如何一步步被解析处理。

## 2. 核心入口：`create_deep_agent`

`create_deep_agent` (定义于 `graph.py`) 是创建 Deep Agent 的主入口函数。它组装了完整的中间件栈，返回一个编译好的 `CompiledStateGraph`。

```python
def create_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: Sequence[SubAgent | CompiledSubAgent | AsyncSubAgent] | None = None,
    skills: list[str] | None = None,
    memory: list[str] | None = None,
    permissions: list[FilesystemPermission] | None = None,
    # ... 其他参数
) -> CompiledStateGraph
```

## 3. 中间件机制详解

### 3.1 中间件执行顺序

`create_deep_agent` 按照以下顺序组装中间件：

```
基础中间件栈:
├── TodoListMiddleware         # Todo列表管理
├── SkillsMiddleware           # (仅当 skills 参数提供)
├── FilesystemMiddleware       # 文件系统工具
├── SubAgentMiddleware         # 子代理支持
├── SummarizationMiddleware    # 对话压缩
├── PatchToolCallsMiddleware   # 工具调用修补
├── AsyncSubAgentMiddleware    # (仅当有异步子代理)
├── [用户提供的 middleware]     # 用户自定义中间件
├── [Provider特定 extra_middleware]  # 来自 harness profile
├── _ToolExclusionMiddleware   # (仅当 profile 有 excluded_tools)
├── AnthropicPromptCachingMiddleware  # (始终添加，对非 Anthropic 模型无操作)
├── MemoryMiddleware           # (仅当 memory 参数提供)
├── HumanInTheLoopMiddleware   # (仅当 interrupt_on 参数提供)
└── _PermissionMiddleware       # (仅当 permissions 参数提供，始终最后)
```

### 3.2 主要中间件功能

#### 3.2.1 TodoListMiddleware
LangChain 内置中间件，提供 `write_todos` 工具用于管理任务列表。

#### 3.2.2 FilesystemMiddleware
提供文件系统操作工具集：
- `ls`: 列出目录
- `read_file`: 读取文件（支持分页 offset/limit）
- `write_file`: 写入文件
- `edit_file`: 编辑文件（精确字符串替换）
- `glob`:  glob 模式匹配
- `grep`: 文本搜索
- `execute`:  shell 命令执行（需要后端支持）

#### 3.2.3 SubAgentMiddleware
通过 `task` 工具提供子代理调用能力。关键组件：

- `TASK_SYSTEM_PROMPT`: 告知主 agent 如何使用 task 工具
- `TASK_TOOL_DESCRIPTION`: 动态生成可用子代理列表（包含 `{available_agents}` 占位符）

默认自动添加 `general-purpose` 子代理，处理复杂独立任务。

#### 3.2.4 SkillsMiddleware
从配置源加载技能（skills），实现渐进式披露：

1. **加载时机**: `before_agent` 钩子，在 agent 执行前加载一次
2. **加载方式**: 从后端扫描技能目录，解析每个 SKILL.md 的 YAML frontmatter
3. **注入方式**: 在 `modify_request` / `wrap_model_call` 中向系统消息追加技能列表
4. **优先级**: 后来的源覆盖先前的同名技能（last one wins）

技能系统提示 (`SKILLS_SYSTEM_PROMPT`) 格式：
```
## Skills System

You have access to a skills library that provides specialized capabilities and domain knowledge.

{skills_locations}

**Available Skills:**

{skills_list}

**How to Use Skills (Progressive Disclosure):**
1. Recognize when a skill applies
2. Read the skill's full instructions: read_file(path, limit=1000)
3. Follow the skill's instructions
```

#### 3.2.5 MemoryMiddleware
从 AGENTS.md 文件加载持久上下文，在系统消息中注入 `<agent_memory>` 标签。

关键提示模板 (`MEMORY_SYSTEM_PROMPT`):
```
<agent_memory>
{agent_memory}
</agent_memory>

<memory_guidelines>
The above <agent_memory> was loaded in from files in your filesystem.
As you learn from your interactions with the user, you can save new knowledge...
[大量学习和记忆指导]
</memory_guidelines>
```

加载时机: `before_agent` 钩子，首次调用时从后端下载所有 memory 文件。

#### 3.2.6 SummarizationMiddleware
当对话长度超过阈值时自动压缩对话历史：
- `trigger`: 压缩触发阈值（默认 85% context 使用率）
- `keep`: 压缩后保留部分（默认 10%）
- `truncate_args_settings`: 工具参数截断设置

压缩后的消息存储到后端 `/conversation_history/{thread_id}.md`。

#### 3.2.7 _PermissionMiddleware
始终最后执行，拦截文件系统工具调用并根据规则允许/拒绝。

## 4. 问题解析流程

### 4.1 整体流程图

```
用户输入
    │
    ▼
invoke() ──────────────────────────────────────────┐
    │                                              │
    ▼                                              │
┌─────────────────────────────────────────────┐   │
│  LangGraph State Graph                       │   │
│                                             │   │
│  ┌──────────────────────────────────────┐   │   │
│  │  NODE: agent                         │   │   │
│  │                                      │   │   │
│  │  for middleware in middleware_stack:│   │   │
│  │    before_agent() ──────────────┐   │   │   │
│  │                                  │   │   │
│  │    ┌────────────────────────┐   │   │   │
│  │    │  modify_request()        │   │   │   │
│  │    │  (修改 system_message)  │   │   │   │
│  │    └──────────┬───────────────┘   │   │   │
│  │               │                   │   │   │
│  │    ┌──────────▼───────────────┐   │   │   │
│  │    │  wrap_model_call()       │   │   │   │
│  │    │  (注入提示词, 调用模型) │   │   │   │
│  │    └──────────┬───────────────┘   │   │   │
│  │               │                   │   │   │
│  │    ┌──────────▼───────────────┐   │   │   │
│  │    │  LLM Inference            │   │   │
│  │    │  (模型推理)              │   │   │
│  │    └──────────┬───────────────┘   │   │   │
│  │               │                   │   │   │
│  │    ┌──────────▼───────────────┐   │   │   │
│  │    │  after_agent()            │   │   │   │
│  │    │  (可选的状态更新)        │   │   │   │
│  │    └──────────────────────────┘   │   │   │
│  └──────────────────────────────────────┘   │   │
│                                             │   │
│  ┌──────────────────────────────────────┐   │   │
│  │  NODE: tools                         │   │   │
│  │                                      │   │   │
│  │  for middleware in middleware_stack:│   │   │
│  │    before_tool() ───────────────┐   │   │   │
│  │                                  │   │   │
│  │    wrap_tool_call() ────────────│   │   │
│  │    (权限检查, 参数修改)          │   │   │
│  │                                  │   │   │
│  │    after_tool() ────────────────┘   │   │   │
│  └──────────────────────────────────────┘   │   │
│                                             │   │
└─────────────────────────────────────────────┘   │
    │                                              │
    ▼                                              │
 返回结果 ─────────────────────────────────────────┘
```

### 4.2 详细步骤解析

#### Step 1: Agent 创建时 (`create_deep_agent`)

```python
# 1. 模型解析
model = resolve_model(model)  # 字符串 -> BaseChatModel 实例

# 2. 获取 harness profile
_profile = _harness_profile_for_model(model, _model_spec)

# 3. 组装系统提示词
base_prompt = _profile.base_system_prompt or BASE_AGENT_PROMPT
if system_prompt:
    final_system_prompt = system_prompt + "\n\n" + base_prompt
else:
    final_system_prompt = base_prompt

# 4. 组装中间件栈 (顺序非常重要!)
deepagent_middleware: list[AgentMiddleware] = [
    TodoListMiddleware(),
]
if skills:
    deepagent_middleware.append(SkillsMiddleware(backend=backend, sources=skills))
deepagent_middleware.extend([
    FilesystemMiddleware(backend=backend, ...),
    SubAgentMiddleware(backend=backend, subagents=inline_subagents, ...),
    create_summarization_middleware(model, backend),
    PatchToolCallsMiddleware(),
])
# ... 更多中间件 ...
deepagent_middleware.append(AnthropicPromptCachingMiddleware(...))
if memory:
    deepagent_middleware.append(MemoryMiddleware(backend=backend, sources=memory))

# 5. 创建 agent
agent = create_agent(
    model,
    system_prompt=final_system_prompt,
    tools=_tools,
    middleware=deepagent_middleware,
    ...
)
```

#### Step 2: 调用 `invoke()` 时

```python
result = agent.invoke(input_dict)
```

#### Step 3: Agent Node 执行

**阶段 A: `before_agent` 钩子**
```python
# 遍历中间件栈，依次调用 before_agent()
for middleware in middleware_stack:
    if hasattr(middleware, 'before_agent'):
        update = middleware.before_agent(state, runtime, config)
        if update:
            state.update(update)
```

关键中间件的 `before_agent` 行为：

| 中间件 | 行为 |
|--------|------|
| SkillsMiddleware | 扫描 skills 源目录，解析 SKILL.md，存储 `skills_metadata` 到 state |
| MemoryMiddleware | 下载 AGENTS.md 文件，存储 `memory_contents` 到 state |

**阶段 B: `modify_request` / `wrap_model_call` 钩子**

每个中间件都可以修改发给 LLM 的请求：

```python
request = ModelRequest(
    system_message=current_system_message,
    messages=conversation_history,
    ...
)

for middleware in middleware_stack:
    if hasattr(middleware, 'modify_request'):
        request = middleware.modify_request(request)
    elif hasattr(middleware, 'wrap_model_call'):
        request = middleware.wrap_model_call(request, handler)
```

提示词注入顺序：

1. **SkillsMiddleware**: 追加 `## Skills System\n\n{skills_list}`
2. **SubAgentMiddleware**: 追加 `## task (subagent spawner)\n\n...` 及可用子代理列表
3. **MemoryMiddleware**: 追加 `<agent_memory>...</agent_memory>`
4. **SummarizationMiddleware**: 无修改（仅监控）

#### Step 4: LLM 推理

模型根据完整的系统提示词（含注入内容）和对话历史生成响应。

#### Step 5: 工具调用处理（Tools Node）

如果 LLM 返回工具调用：

```python
for middleware in middleware_stack:
    if hasattr(middleware, 'wrap_tool_call'):
        result = middleware.wrap_tool_call(request, handler)
```

关键中间件行为：

| 中间件 | 行为 |
|--------|------|
| _PermissionMiddleware | 检查路径权限，返回拒绝或继续 |
| FilesystemMiddleware | 执行实际文件操作 |

## 5. 提示词加载时机汇总

| 提示词类型 | 来源 | 加载时机 | 注入方式 |
|-----------|------|----------|---------|
| **BASE_AGENT_PROMPT** | `graph.py` 硬编码 | Agent 创建时 | 直接作为 `system_prompt` |
| **system_prompt 参数** | 用户传入 | Agent 创建时 | 与 base prompt 拼接 |
| **profile.base_system_prompt** | Harness Profile | Agent 创建时 | 替代 BASE_AGENT_PROMPT |
| **profile.system_prompt_suffix** | Harness Profile | Agent 创建时 | 追加到 base prompt 末尾 |
| **Skills 列表** | SKILL.md 文件 | `before_agent` 钩子（首次） | `modify_request` 追加 |
| **Memory 内容** | AGENTS.md 文件 | `before_agent` 钩子（首次） | `modify_request` 追加 |
| **Task Tool 描述** | 子代理配置 | `SubAgentMiddleware.__init__` | 工具 description |
| **Summarization 提示** | `summarization.py` | `SummarizationMiddleware` | 无修改 |

## 6. 关键文件对应关系

| 功能 | 文件路径 |
|------|---------|
| 主入口/中间件组装 | `deepagents/graph.py` |
| 子代理中间件 | `deepagents/middleware/subagents.py` |
| 技能中间件 | `deepagents/middleware/skills.py` |
| 内存中间件 | `deepagents/middleware/memory.py` |
| 文件系统中间件 | `deepagents/middleware/filesystem.py` |
| 权限中间件 | `deepagents/middleware/permissions.py` |
| 压缩中间件 | `deepagents/middleware/summarization.py` |
| Provider Profile | `deepagents/profiles/_harness_profiles.py` |
| 模型解析 | `deepagents/_models.py` |
| 后端协议 | `deepagents/backends/protocol.py` |

## 7. 示例：完整的问题解析流程

假设用户调用：
```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    skills=["/skills/user/", "/skills/project/"],
    memory=["/memory/AGENTS.md"],
)

result = agent.invoke({"messages": [{"role": "user", "content": "帮我研究量子计算的最新进展"}]})
```

### 执行流程：

1. **Agent 创建阶段**:
   - `resolve_model("anthropic:claude-sonnet-4-6")` → ChatAnthropic 实例
   - `_harness_profile_for_model()` → 获取 Anthropic profile
   - 组装中间件栈：`[TodoListMiddleware, SkillsMiddleware, FilesystemMiddleware, SubAgentMiddleware, SummarizationMiddleware, PatchToolCallsMiddleware, AnthropicPromptCachingMiddleware, MemoryMiddleware]`

2. **首次 invoke 阶段**:

   a. **SkillsMiddleware.before_agent**:
      - 扫描 `/skills/user/` 和 `/skills/project/`
      - 发现 `web-research` 技能目录含 SKILL.md
      - 解析 YAML frontmatter，提取 name/description
      - 更新 state: `{"skills_metadata": [...]}`

   b. **MemoryMiddleware.before_agent**:
      - 后端下载 `/memory/AGENTS.md`
      - 更新 state: `{"memory_contents": {"/memory/AGENTS.md": "..."}}`

   c. **构建 ModelRequest**:
      - system_message = 基础 prompt + skills_section + memory_section
      - messages = 用户输入

   d. **中间件链式修改**:
      - SkillsMiddleware: 追加技能列表
      - SubAgentMiddleware: 追加 task 工具说明
      - MemoryMiddleware: 追加 `<agent_memory>` 块

   e. **LLM 推理**:
      - 检测到复杂研究任务
      - 返回 tool_call: `task(description="...", subagent_type="general-purpose")`

   f. **SubAgentMiddleware.wrap_tool_call**:
      - 创建新 state（含任务描述）
      - 调用 general-purpose 子代理

   g. **子代理执行**:
      - 加载子代理自己的 skills/memory
      - 执行研究任务
      - 返回结果

   h. **主代理整合结果**，返回最终响应

## 8. 中间件执行顺序可视化

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Model Request 构建流程                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────┐                                                    │
│  │ 1. Base Prompt    │  BASE_AGENT_PROMPT + profile.system_prompt_suffix    │
│  │   (create_deep_agent时)                                                  │
│  └─────────┬─────────┘                                                    │
│            │                                                              │
│            ▼                                                              │
│  ┌───────────────────┐                                                    │
│  │ 2. User Prompt    │  system_prompt 参数（如果提供）                       │
│  │   (create_deep_agent时)                                                  │
│  └─────────┬─────────┘                                                    │
│            │                                                              │
│            ▼                                                              │
│  ┌───────────────────┐                                                    │
│  │ 3. Skills Section  │  SkillsMiddleware.modify_request()                   │
│  │   (before_agent)   │  "## Skills System\n\n{skills_locations}..."       │
│  └─────────┬─────────┘                                                    │
│            │                                                              │
│            ▼                                                              │
│  ┌───────────────────┐                                                    │
│  │ 4. Task Section   │  SubAgentMiddleware.wrap_model_call()                │
│  │   (wrap_model_call)                                                │
│  │                    │  TASK_SYSTEM_PROMPT + available_agents              │
│  └─────────┬─────────┘                                                    │
│            │                                                              │
│            ▼                                                              │
│  ┌───────────────────┐                                                    │
│  │ 5. Memory Section  │  MemoryMiddleware.modify_request()                   │
│  │   (modify_request)│  "<agent_memory>\n{agent_memory}\n</agent_memory>"   │
│  └─────────┬─────────┘                                                    │
│            │                                                              │
│            ▼                                                              │
│  ┌───────────────────┐                                                    │
│  │ 6. Cached Prompt   │  AnthropicPromptCachingMiddleware (自动添加缓存标记）│
│  └─────────┬─────────┘                                                    │
│            │                                                              │
│            ▼                                                              │
│  ┌───────────────────┐                                                    │
│  │    LLM Inference  │  完整系统提示词 → 模型                               │
│  └───────────────────┘                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 9. 总结

`deepagents` 的中间件机制基于 LangChain 的 `AgentMiddleware` 接口，通过在关键节点（`before_agent`, `modify_request`, `wrap_model_call`, `wrap_tool_call`）插入自定义逻辑，实现了：

1. **技能渐进式披露**：技能元数据在启动时加载，但完整内容按需读取
2. **持久化内存**：通过 AGENTS.md 文件实现跨会话记忆
3. **子代理委托**：复杂任务通过 `task` 工具委托给独立子代理
4. **自动压缩**：对话过长时自动压缩历史
5. **权限控制**：细粒度文件系统访问控制

这种设计使得每个中间件职责单一，可组合性强，便于扩展和定制。