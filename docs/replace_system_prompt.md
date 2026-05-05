# DeepAgents 中间件提示词替换与稳定性实践

你提到的目录写法是 `.venv/lib/deepagets/Middleware`，实际代码位置是：

- `.venv/lib/python3.12/site-packages/deepagents/middleware/`

下面基于该目录下所有 Python 文件做逐项分析，并给出可直接参考的替换提示词代码。

## 1) 目录内各文件是做什么的

- `__init__.py`
  - 只是导出中间件入口和类型，不包含业务逻辑。

- `filesystem.py`（`FilesystemMiddleware`）
  - 提供 `ls/read_file/write_file/edit_file/glob/grep/execute` 工具。
  - 动态注入文件系统和执行工具相关系统提示词。
  - 自动把超大工具输出/超长消息 offload 到文件，避免上下文爆炸。

- `skills.py`（`SkillsMiddleware`）
  - 从多个 source 加载 skills 元数据（`SKILL.md` frontmatter）。
  - 将“有哪些 skill、何时使用、如何 progressive disclosure 读取”注入系统提示词。
  - source 按顺序覆盖，后者优先（last one wins）。

- `memory.py`（`MemoryMiddleware`）
  - 从 `AGENTS.md` 等 memory 源加载长期记忆。
  - 把 memory 与“何时写入记忆”的规则注入系统提示词。

- `subagents.py`（`SubAgentMiddleware`）
  - 注入 `task` 工具，用于同步短生命周期子代理。
  - 在系统提示词里告诉主代理何时该委派给子代理。

- `async_subagents.py`（`AsyncSubAgentMiddleware`）
  - 注入 `start_async_task/check_async_task/update_async_task/cancel_async_task/list_async_tasks`。
  - 用于远端 Agent Protocol 子代理的异步后台执行与状态跟踪。

- `summarization.py`（`SummarizationMiddleware` + `SummarizationToolMiddleware`）
  - 自动压缩会话上下文（达到阈值后摘要+保留最近消息）。
  - 可提供 `compact_conversation` 手动压缩工具。
  - 负责把被压缩的历史 offload 到 backend。

- `permissions.py`（`_PermissionMiddleware` + `FilesystemPermission`）
  - 对文件系统读写权限做 pre-check/post-filter。
  - 这不是提示词型中间件，主要是安全控制。

- `patch_tool_calls.py`（`PatchToolCallsMiddleware`）
  - 修补历史中“AI 发起了 tool call，但没有对应 ToolMessage 回执”的悬空调用。
  - 用于恢复消息序列一致性，不涉及提示词注入。

- `_tool_exclusion.py`（`_ToolExclusionMiddleware`）
  - 在模型调用前移除被排除的工具。
  - 是工具可见性控制，不注入提示词。

- `_utils.py`
  - 通用工具函数（如 `append_to_system_message`），被多个中间件复用。

## 2) 什么时候替换不同中间件的提示词

先记一个核心原则：**优先改“最靠近行为责任”的提示词**，而不是把所有规则塞进全局 system prompt。

- 全局 `system_prompt`（`create_deep_agent(system_prompt=...)`）
  - 适合：角色、语气、输出风格、全局工作原则。
  - 不适合：某个工具的细则（例如 `task` 的委派条件）。

- `FilesystemMiddleware(system_prompt=...)`
  - 适合：你想改变文件/命令工具使用规范（读写前先读、分页、命令习惯、超长输出处理）。
  - 触发时机：模型频繁误用文件工具或 `execute`。

- `SkillsMiddleware`
  - 适合：你希望模型更主动识别并读取 skill，或改变 skill 选择策略。
  - 触发时机：模型“知道有 skill 但不触发/触发不稳定”。

- `MemoryMiddleware`
  - 适合：你想改变“记什么、不记什么、什么时候立即写记忆”。
  - 触发时机：模型记忆过多噪音，或错过关键长期偏好。

- `SubAgentMiddleware(system_prompt/task_description)`
  - 适合：调整“何时开子代理、如何拆分并行任务、子代理返回格式”。
  - 触发时机：主代理过度/不足委派。

- `AsyncSubAgentMiddleware(system_prompt=...)`
  - 适合：异步任务生命周期策略（启动后是否立刻轮询、何时检查状态等）。
  - 触发时机：异步任务管理混乱，用户体验不稳定。

- `SummarizationToolMiddleware` / `SummarizationMiddleware(summary_prompt=...)`
  - 适合：上下文压缩策略与摘要质量。
  - 触发时机：上下文膨胀、摘要丢关键信息、成本过高。

- `permissions.py` / `patch_tool_calls.py` / `_tool_exclusion.py`
  - 主要是规则与安全，不建议通过提示词“间接控制”，应直接改参数/规则。

## 3) 每种中间件“替换提示词”示例代码

下面示例按“可直接参数替换”和“需子类覆写”分开。

### 3.1 全局系统提示词（推荐先做）

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-4o",
    system_prompt=(
        "你是车销业务代理。优先给可执行方案；"
        "输出保持简洁；关键步骤使用编号；"
        "涉及工具调用时先给一句目标说明。"
    ),
)
```

### 3.2 FilesystemMiddleware：替换文件/执行工具提示词

```python
from deepagents.middleware.filesystem import FilesystemMiddleware

fs_mw = FilesystemMiddleware(
    backend=my_backend,
    system_prompt=(
        "你可以使用文件与命令工具。"
        "任何编辑前必须先 read_file；"
        "大文件必须分页读取；"
        "执行命令时优先绝对路径。"
    ),
    custom_tool_descriptions={
        "execute": "执行 shell 命令；禁止使用 find/grep/cat/head/tail；优先 ls/read_file/glob/grep 工具。",
        "read_file": "读取文件，默认 limit=100；大文件请显式传 offset/limit。",
    },
)
```

### 3.3 SkillsMiddleware：增强 skill 触发说明

`SkillsMiddleware` 没有构造参数直接传 `system_prompt`，可在实例化后替换模板：

```python
from deepagents.middleware.skills import SkillsMiddleware

skills_mw = SkillsMiddleware(
    backend=my_backend,
    sources=["/skills/base/", "/skills/user/", "/skills/project/"],
)

skills_mw.system_prompt_template = """
## Skills System (Custom)

{skills_locations}

可用技能：
{skills_list}

规则：
1) 用户请求一旦命中 skill 描述，优先读取对应 SKILL.md（read_file limit=1000）。
2) 先遵循 skill，再做通用推理。
3) 若多个 skill 可用，优先与当前任务最强相关、且 allowed-tools 更匹配的 skill。
"""
```

### 3.4 MemoryMiddleware：自定义 memory 注入模板

`MemoryMiddleware` 默认用模块常量 `MEMORY_SYSTEM_PROMPT`。建议子类覆写格式化逻辑：

```python
from deepagents.middleware.memory import MemoryMiddleware

class CustomMemoryMiddleware(MemoryMiddleware):
    def _format_agent_memory(self, contents: dict[str, str]) -> str:
        body = "\n\n".join(f"{k}\n{v}" for k, v in contents.items()) or "(No memory loaded)"
        return f"""
<agent_memory>
{body}
</agent_memory>

<memory_guidelines>
- 仅记录长期有效偏好和稳定流程，不记录临时状态
- 用户纠错后，优先更新 memory，再继续执行
- 禁止存储凭据/密钥
</memory_guidelines>
""".strip()

memory_mw = CustomMemoryMiddleware(
    backend=my_backend,
    sources=["/memory/AGENTS.md", "/memory/project.md"],
)
```

### 3.5 SubAgentMiddleware：替换 task 工具说明与委派提示

```python
from deepagents.middleware.subagents import SubAgentMiddleware

subagent_mw = SubAgentMiddleware(
    backend=my_backend,
    subagents=[
        {
            "name": "researcher",
            "description": "做资料检索和事实核验",
            "system_prompt": "你是研究子代理。输出要点+来源。",
            "model": "openai:gpt-4o-mini",
            "tools": [],
        }
    ],
    system_prompt=(
        "你拥有 task 工具。"
        "复杂多步骤且可隔离任务优先委派；"
        "简单任务不要委派。"
    ),
    task_description=(
        "使用 task 调起子代理。可用类型如下：\n{available_agents}\n"
        "要求：独立任务并行；返回结构化结果。"
    ),
)
```

### 3.6 AsyncSubAgentMiddleware：替换异步子代理规则

```python
from deepagents.middleware.async_subagents import AsyncSubAgentMiddleware

async_sub_mw = AsyncSubAgentMiddleware(
    async_subagents=[
        {
            "name": "remote-research",
            "description": "远端深度研究",
            "graph_id": "research_graph",
            "url": "https://example.langgraph.app",
        }
    ],
    system_prompt=(
        "你可以启动异步任务。"
        "启动后立即把 task_id 返回给用户；"
        "只有用户要求时才 check；"
        "禁止循环轮询。"
    ),
)
```

### 3.7 SummarizationMiddleware：替换“摘要生成提示词”

这不是系统提示词，而是“摘要模型提示词”：

```python
from deepagents.middleware.summarization import SummarizationMiddleware

summ_mw = SummarizationMiddleware(
    model="openai:gpt-4o-mini",
    backend=my_backend,
    trigger=("fraction", 0.85),
    keep=("fraction", 0.10),
    summary_prompt=(
        "请压缩历史对话，保留："
        "用户目标、关键约束、已完成步骤、未决问题、下一步动作。"
        "避免重复与寒暄。"
    ),
)
```

### 3.8 SummarizationToolMiddleware：替换 compact_conversation 使用提醒

该中间件默认把固定提示 `SUMMARIZATION_SYSTEM_PROMPT` 追加到 system message。可子类覆写：

```python
from deepagents.middleware._utils import append_to_system_message
from deepagents.middleware.summarization import SummarizationToolMiddleware

class CustomSummToolMiddleware(SummarizationToolMiddleware):
    def wrap_model_call(self, request, handler):
        custom_prompt = (
            "当用户明确切换新话题、且旧上下文已不再需要时，"
            "优先调用 compact_conversation。"
        )
        new_sys = append_to_system_message(request.system_message, custom_prompt)
        return handler(request.override(system_message=new_sys))
```

### 3.9 不能通过“替换提示词”解决的中间件

- `permissions.py`：请通过 `FilesystemPermission` 规则控制行为。
- `patch_tool_calls.py`：是消息修复器，不靠提示词。
- `_tool_exclusion.py`：通过排除工具列表生效。

## 4) 如何让 agent 更稳定调用 skill

结合当前实现，稳定性最关键的是“skill 元数据质量 + source 管理 + 调用约束”。

- 让 skill “可判定”
  - `SKILL.md` frontmatter 的 `name/description` 要写清楚触发场景关键词。
  - `name` 与目录名一致；避免模糊描述（否则模型不容易命中）。

- 控制覆盖顺序
  - `sources` 后面的优先级更高（last one wins）。
  - 建议顺序：`base -> team -> project -> user`，让个性化规则覆盖通用规则。

- 限制可用工具
  - 在 frontmatter 用 `allowed-tools` 标记推荐工具，降低模型在 skill 内乱选工具。

- 降低 token 干扰
  - skill 内容精简到“触发条件 + 步骤 + 例外处理 + 输出模板”。
  - 对巨长说明拆到辅助文件，主 `SKILL.md` 保持可读。

- 强化主系统提示
  - 在全局 prompt 明确：命中 skill 时，先 `read_file` 读取 `SKILL.md` 再行动。
  - 可配合 `SkillsMiddleware.system_prompt_template` 自定义强调。

## 5) 让 skill 内脚本工具高效运行的做法

- 使用支持执行的 backend
  - 确保 backend 支持 `execute`（`SandboxBackendProtocol`），否则脚本无法真正跑起来。

- 脚本调用规范化
  - 一律绝对路径。
  - 先 `ls` 校验目录，再执行脚本。
  - 命令链使用 `&&`，避免中间失败被忽略。

- 设定超时与资源边界
  - `FilesystemMiddleware(max_execute_timeout=...)` 设上限。
  - 单次长任务传 `timeout`，防止卡死。

- 降低重复开销
  - 把安装依赖、构建索引、缓存目录放在可复用位置（如项目缓存目录）。
  - 避免每次 skill 调用都重复初始化环境。

- 并行化独立任务
  - 对可拆分任务，使用 `task` 子代理并行；长耗时可考虑 async subagents。

- 观测与回退
  - 关键脚本结果写入明确文件路径，失败时输出可复现命令。
  - 对高风险工具可加 `interrupt_on` 人工确认。

## 6) 一份更稳的组合配置示例

```python
from deepagents import create_deep_agent
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.skills import SkillsMiddleware
from deepagents.middleware.summarization import SummarizationMiddleware

agent = create_deep_agent(
    model="openai:gpt-4o",
    backend=my_backend,  # 需支持 execute 时请使用 sandbox backend
    system_prompt=(
        "你是车销智能代理。命中 skill 时必须先读 SKILL.md，再执行。"
        "输出优先给结论+下一步。"
    ),
    middleware=[
        FilesystemMiddleware(
            backend=my_backend,
            max_execute_timeout=900,
            custom_tool_descriptions={
                "execute": "运行脚本请使用绝对路径；先 ls 校验目录；必要时设置 timeout。",
            },
        ),
        SkillsMiddleware(
            backend=my_backend,
            sources=["/skills/base/", "/skills/project/", "/skills/user/"],
        ),
        SummarizationMiddleware(
            model="openai:gpt-4o-mini",
            backend=my_backend,
            trigger=("fraction", 0.85),
            keep=("fraction", 0.10),
            summary_prompt="保留目标、约束、决策、未完成事项。",
        ),
    ],
)
```

---

如果你愿意，我下一步可以基于你项目当前的 `create_deep_agent(...)` 实际初始化代码，给你改一版“可直接运行的最稳配置”（包括你现在的 skills/memory/permissions/subagents 具体参数）。
