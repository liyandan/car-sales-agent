import os
import re
import sys
import uuid
import atexit
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from psycopg import OperationalError
try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None
from LLM_Factory import create_llm
from deepagents import create_deep_agent
from langfuse.langchain import CallbackHandler
from langchain_community.tools import ShellTool
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware import FilesystemMiddleware
from deepagents.middleware import SkillsMiddleware
from langgraph.checkpoint.postgres import ShallowPostgresSaver
import deepagents.graph as deepagents_graph
from langchain.agents.middleware.todo import TodoListMiddleware
from deepagents.middleware.memory import MemoryMiddleware
from common import logger



import subprocess
from typing import Optional, Type
from langchain_community.tools import ShellTool
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

class RobustShellTool(ShellTool):
    """始终捕获 stdout/stderr 并返回完整结果。"""
    
    def _run(
        self,
        commands: list[str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        results = []
        for cmd in commands:
            try:
                # shell=True 保持与原始 ShellTool 一致，但显式捕获 stderr
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )
                out = proc.stdout.strip()
                err = proc.stderr.strip()
                if err:
                    # 将 stderr 也合并到输出中，方便排查
                    results.append(f"{out}\n[STDERR]: {err}")
                else:
                    results.append(out)
            except Exception as e:
                results.append(f"Error executing command: {str(e)}")
        return "\n".join(results)

# 使用自定义工具
shell_tool = RobustShellTool(verbose=True)
# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_ROOT = Path(__file__).resolve().parents[0]
ENV_PATH = AGENT_ROOT / ".env"

# 加载Agent的相关环境配置
logger.info(f"#==== ENV_PATH: {ENV_PATH}")
logger.info(f"#==== PROJECT_ROOT: {PROJECT_ROOT}")
logger.info(f"#==== AGENT_ROOT: {AGENT_ROOT}")
load_dotenv(ENV_PATH)

# 初始化Tavily客户端（可选依赖）
tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily_client = (
    TavilyClient(api_key=tavily_api_key)
    if TavilyClient is not None and tavily_api_key
    else None
)

# 定义互联网搜索工具
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    if tavily_client is None:
        raise RuntimeError(
            "Tavily search is unavailable. Install 'tavily' and set TAVILY_API_KEY."
        )
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

# 安全打印
def safe_print(text: object) -> None:
    output = str(text)
    try:
        print(output)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        sanitized = output.encode(encoding, errors="replace").decode(encoding)
        print(sanitized)

llm = create_llm()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

# 初始化Langfuse回调处理器
langfuse_handler=CallbackHandler()

# 初始化Shell工具
#shell_tool = ShellTool(verbose=True)


# 获取技能目录路径（传给 deepagents 时必须是虚拟路径）
skills_dir = (PROJECT_ROOT / "skills").as_posix()
logger.info(f"#==== skills_dir: {str(skills_dir)}")

memory_file = (PROJECT_ROOT / "AGENTS.md").as_posix()
logger.info(f"#==== memory_file: {str(memory_file)}")

checkpoint_db_name      =    os.getenv("CHECKPOINT_DB_NAME","langgraph")
checkpoint_db_user      =    os.getenv("CHECKPOINT_DB_USER","langgraph_user")
checkpoint_db_password  =    os.getenv("CHECKPOINT_DB_PASSWORD","~1q~1q~1q")
checkpoint_db_host      =    os.getenv("CHECKPOINT_DB_HOST","38.47.121.109")
checkpoint_db_port      =    os.getenv("CHECKPOINT_DB_PORT","5456")
# PostgreSQL 配置
DATABASE_URL = f"postgresql://{checkpoint_db_user}:{checkpoint_db_password}@{checkpoint_db_host}:{checkpoint_db_port}/{checkpoint_db_name}"

print(f"#==== DATABASE_URL: {DATABASE_URL}")
# ShallowPostgresSaver.from_conn_string 是「上下文管理器」，必须用 with 进入，
# 才能得到真正的 checkpointer 实例；不可写成 checkpointer = X.from_conn_string(url)。
# 与同步的 agent.invoke 搭配请用 ShallowPostgresSaver（非 Async*）。
_checkpointer_cm = None
_checkpointer = None
_agent = None

# 创建FilesystemBackend，用于管理文件系统操作,virtual_mode=True 表示使用虚拟路径，以root_dir为根目录,以/workspace/开头
backend = FilesystemBackend( 
                            root_dir=str(PROJECT_ROOT.as_posix()),
                            virtual_mode=True 
                            )
logger.info(f"#==== backend filesystem root dir : {str(PROJECT_ROOT.as_posix())}")

skills_middleware = SkillsMiddleware(backend=backend, sources=[f"/skills"])
logger.info(f"#==== skills_middleware: {str(skills_middleware)}")


skills_real_root = (PROJECT_ROOT / "skills").as_posix()
logger.info(f"#==== skills_real_root: {str(skills_real_root)}")


venv_python = (PROJECT_ROOT / ".venv" / "Scripts" / "python.exe").as_posix()

prompt_addition = f"""
你是以个有用的AI助手。
所有技能脚本的真实系统路径为：{skills_real_root}
调用 terminal 执行脚本时，请使用上述真实路径，例如：
python {skills_real_root}/explaining-car-source/scripts/tools/get_car_type_info_without_clue_id.py --question "..." --env online

这里的python也换成虚拟环境的python，{venv_python}，实际执行的命令为：
{venv_python} {skills_real_root}/explaining-car-source/scripts/tools/get_car_type_info_without_clue_id.py --question "..." --env online
"""

skills_middleware.system_prompt_template = """
# 技能系统
你可调用技能库，获取专项能力与专业领域知识。
{skills_locations}

### 可用技能
{skills_list}

### 技能使用规则（渐进式展示）
技能采用**渐进式展示**机制：你仅可查看上方的技能名称与简介，仅在需要时读取完整使用说明：
1. **判断适用场景**：核对用户需求是否匹配对应技能的功能描述
2. **读取完整指引**：一旦判定有匹配到合适的技能功能描述，务必通过上方技能列表中标注的路径，执行`read_file`指令，读取完整的技能使用说明。
   需传入参数`limit=1000`，默认100行的读取限制无法满足大多数技能文件的阅读需求。
3. **遵循流程执行**：技能说明文档（SKILL.md）包含分步操作流程、最佳实践与实操示例
4. **调取配套文件**：技能可能附带辅助脚本、配置文件、参考文档，需使用绝对路径访问

### 何时需要使用技能
- 用户需求属于某一技能的专属业务领域（例如：“调研X相关内容”→调用网络调研技能）
- 任务需要专业知识或标准化流程支撑
- 处理复杂任务时，需依托成熟、可复用的执行方案

### 技能脚本运行规范
部分技能内含Python脚本或其他可执行文件，调用时**必须使用技能列表中的绝对路径**。

### 实操示例流程
用户提问：“请调研量子计算领域的最新发展动态。”
1. 查看可用技能 → 找到「网络调研」技能及对应路径
2. 读取完整技能文档：执行 `read_file(文件路径, limit=1000)` 加载SKILL.md文件内容
3. 按照调研流程逐步操作（检索信息→整理内容→整合输出）
4. 通过绝对路径调用所需辅助脚本

温馨提示：合理使用技能，能大幅提升任务处理能力与输出规范性。遇到不确定的任务时，优先确认是否有匹配的专属技能！

---
### 补充说明
1. 保留原文指令代码格式（`read_file`），保证功能指令准确无误
2. 专业术语统一规范化翻译，贴合办公/AI系统使用语境
3. 句式精简通顺，符合中文阅读习惯，同时完整保留所有规则逻辑 """

WRITE_TODOS_SYSTEM_PROMPT = """
## `write_todos` 待办清单工具
你可以使用 **`write_todos`** 工具，协助管理与规划复杂任务目标。
面对复杂需求时，请使用该工具，确保跟进每一个必要步骤，同时让用户清晰了解你的工作进度。
该工具非常适合拆解大型、复杂的目标，将其拆分为多个简易小步骤。

**关键要求**：每完成一个步骤，必须立即标记对应待办为已完成，禁止积攒多个步骤后统一批量标记。
仅需少量步骤即可完成的简单任务，**请勿使用此工具**，直接完成即可。
创建待办会消耗时间与字符配额，仅在处理**多步骤、高复杂度**任务时使用；简单少量步骤的需求无需启用。

## 待办清单重要使用须知
- 禁止并行多次调用 `write_todos` 工具。
- 支持随时动态修改待办清单：新信息可能会产生新增任务，或使原有任务失效、不再需要执行，可灵活调整。
"""
WRITE_TODOS_TOOL_DESCRIPTION = """

使用本工具，可为当前工作会话创建并管理结构化任务清单。这能帮助你跟进工作进度、梳理复杂任务，并向用户体现工作的严谨性。

仅在有助于保持工作条理时使用该工具。如果用户需求简单琐碎、只需不到3个步骤就能完成，建议**不要使用本工具**，直接处理任务即可。

## 适用场景
出现以下情况时，请使用本工具：
1. 多步骤复杂任务 —— 任务需要3个及以上独立操作步骤
2. 高难度复杂工作 —— 需要周密规划、多项操作配合完成的任务
3. 用户明确要求 —— 用户主动要求生成待办清单
4. 多项合并需求 —— 用户一次性给出多项待办事项（带编号或逗号分隔）
5. 方案需动态调整 —— 后续需根据前期执行结果，修改或更新整体计划

## 使用方法
1. 开始处理任务前 —— **先行标记为进行中**，再开展工作。
2. 任务完成后 —— 标记为已完成，并补充执行过程中发现的新增后续任务。
3. 可灵活调整后续任务：删除无用任务、新增必要任务；**禁止修改已完成的历史任务**。
4. 支持批量更新清单：例如完成当前任务后，可同步将下一项待办任务标记为进行中。

## 禁用场景
以下情况请勿使用本工具：
1. 仅有单一、简单直白的任务
2. 内容琐碎，记录进度毫无意义
3. 仅需少量简易步骤即可完成
4. 纯聊天对话、信息咨询类需求

## 任务状态与管理规范
### 1. 任务状态
通过以下状态跟进进度：
- 待处理：尚未开始的任务
- 进行中：正在执行的任务（互不关联、可并行的任务，可同时多项进行中）
- 已完成：顺利办结的任务

### 2. 任务管理规则
- 工作过程中实时更新任务状态
- 任务完成后**立即单独标记**，禁止批量集中完结
- 优先办结当前任务，再开启新任务
- 彻底移除清单中已失效、无关的任务
- 重要要求：生成待办清单时，需立刻将首个（或首批）任务标记为进行中
- 重要要求：未全部办结前，必须至少保留一项进行中任务，向用户展示正在推进工作

### 3. 任务完成判定要求
- 仅在**完全办结**后，才可标记为已完成
- 遇到报错、阻碍、无法推进时，保持任务为进行中状态
- 任务受阻时，新建专项任务，记录需要解决的问题
- 出现以下情况，**严禁标记为已完成**：
  - 存在未解决的问题或错误
  - 工作仅完成部分、内容不完整
  - 遭遇阻碍导致无法收尾
  - 缺少必要资源或依赖条件
  - 未达到质量标准

### 4. 任务拆解要求
- 任务内容需具体、可落地执行
- 将复杂大任务拆解为简短、易执行的小步骤
- 任务名称清晰易懂、描述准确

主动规范管理任务，能体现工作细致度，保障所有要求圆满落地。

请牢记：若完成任务只需少量工具调用、执行路径清晰明确，建议直接处理任务，完全无需调用本工具。
"""

class CustomTodoListMiddleware(TodoListMiddleware):
    """Override built-in write_todos prompts without duplicate registration."""

    def __init__(self) -> None:
        super().__init__(
            system_prompt=WRITE_TODOS_SYSTEM_PROMPT,
            tool_description=WRITE_TODOS_TOOL_DESCRIPTION,
        )

memory_middleware = MemoryMiddleware(backend=backend, sources=["/AGENTS.md"])

def _install_todo_prompt_override() -> None:
    # create_deep_agent() pulls TodoListMiddleware from deepagents.graph globals.
    deepagents_graph.TodoListMiddleware = CustomTodoListMiddleware

MEMORY_SYSTEM_PROMPT = """

<agent_memory>
{agent_memory}
<agent_memory>

<memory_guidelines>
    上方<agent_memory>内容从本地文件加载。在与用户交流的过程中，你可以通过调用 `edit_file` 工具，保存新学到的知识。

    **从反馈中学习：**
    - 你的**核心首要任务**之一，就是从和用户的互动中持续学习。这类学习内容分为显性与隐性两类，确保日后能够牢记这些关键信息。
    - 但凡需要记录、留存信息时，**必须第一时间立刻更新记忆**——优先于回复用户、调用其他工具以及所有其他操作，即刻完成记忆更新。
    - 当用户评价内容好坏、优劣时，要提炼背后**原因**，并总结固化为固定行为规范。
    - 每一次修正都是永久优化的机会：不要只解决当下问题，同时要同步更新自身执行规范。
    - 若用户中途中断工具调用并给出反馈，是更新记忆的最佳时机。请先立即更新记忆，再修改并重新发起工具调用。
    - 聚焦问题背后的底层逻辑与原则，不要只局限于表面的单一错误。
    - 即便用户没有明确要求你记住某件事，只要该信息对后续工作有用，就需要立刻更新记忆。

    **主动询问信息：**
    - 若缺少执行操作所需的关键背景信息（例如发送斯拉普私信需要用户ID、邮箱等），必须主动向用户明确询问。
    - 未知信息切勿主观臆断，主动询问是最优选择。
    - 用户提供可长期复用的信息时，务必马上更新记忆存档。

    **需要更新记忆的场景：**
    - 用户明确要求你记住内容（例如：“记住我的邮箱”“保存我的偏好设置”）
    - 用户对你的定位、行为规范提出要求（例如：“你是网页调研专员”“务必按X方式执行”）
    - 用户对你的输出内容提出反馈，需记录问题原因与优化方式
    - 用户提供工具调用必备信息（例如：频道ID、邮箱地址等）
    - 用户告知可复用的背景规则，如工具使用方法、特定场景的处理方式
    - 你总结出新的行为模式、使用偏好（编码风格、书写规范、工作流程等）

    **无需更新记忆的场景：**
    - 临时、短期的一次性临时信息（例如：“我要迟到了”“我现在在用手机”）
    - 单次临时任务需求（例如：“帮我找个菜谱”“计算25乘4等于多少”）
    - 无长期参考价值的简单问答（例如：“今天周几”“解释一下X概念”）
    - 日常寒暄、简单应答类内容（例如：“好的”“你好”“谢谢”）
    - 过时、后续对话不会用到的无效信息
    - **严禁**在任何文件、记忆库、系统指令中存储API密钥、访问令牌、密码等各类私密凭证。
    - 若用户询问密钥存放位置，或是直接提供密钥，严禁复述、保存该类敏感信息。

    **示例参考：**
    示例1（记录用户信息）：
    用户：你能绑定我的谷歌账号吗？
    智能体：没问题，需要提供你的谷歌账号邮箱。
    用户：john@example.com
    智能体：我将把该信息保存至记忆库。
    工具调用：edit_file(……) → 记录用户谷歌邮箱为 john@example.com

    示例2（记录用户隐性偏好）：
    用户：帮我写一个LangChain深度智能体的创建示例。
    智能体：好的，为你提供Python版本代码示例。
    用户：换成JavaScript版本。
    智能体：我将记录你的使用偏好。
    工具调用：edit_file(……) → 记录用户优先使用JavaScript获取LangChain代码示例
    智能体：收到，这是为你编写的JavaScript版本示例代码。

    示例3（不记录临时信息）：
    用户：我今晚要去打篮球，接下来几小时不在线。
    智能体：收到，我为你添加日历提醒。
    工具调用：create_calendar_event(……) → 仅执行工具操作，不存入记忆，该内容属于临时信息
</memory_guidelines>

"""
class CustomMemoryMiddleware(MemoryMiddleware):
    def _format_agent_memory(self, contents: dict[str, str]) -> str:
        """Format memory with locations and contents paired together.

        Args:
            contents: Dict mapping source paths to content.

        Returns:
            Formatted string with location+content pairs wrapped in <agent_memory> tags.
        """
        if not contents:
            return MEMORY_SYSTEM_PROMPT.format(agent_memory="(No memory loaded)")

        sections = [f"{path}\n{contents[path]}" for path in self.sources if contents.get(path)]

        if not sections:
            return MEMORY_SYSTEM_PROMPT.format(agent_memory="(No memory loaded)")

        memory_body = "\n\n".join(sections)
        return MEMORY_SYSTEM_PROMPT.format(agent_memory=memory_body)

memory_middleware = CustomMemoryMiddleware(backend=backend, sources=["/AGENTS.md"])
        
def get_agent():
    global _checkpointer_cm, _checkpointer, _agent
    if _agent is None:
        _install_todo_prompt_override()
        _checkpointer_cm = ShallowPostgresSaver.from_conn_string(DATABASE_URL)
        _checkpointer = _checkpointer_cm.__enter__()
        _checkpointer.setup()
        logger.info(f"#==== skills_dir: {str(skills_dir)}")
        logger.info(f"#==== db_checkpoint_url: {DATABASE_URL}")
        _agent = create_deep_agent(
            name="car-sales-agent",
            model=llm,
           # memory=[str(memory_file)],
            tools=[shell_tool],
            backend=backend,
            #skills=["/skills"], 
            middleware=[ skills_middleware,memory_middleware],#str(skills_dir)
            system_prompt=prompt_addition,#"你是一个乐于助人的助手。",
            checkpointer=_checkpointer,
        )
    return _agent


def _close_agent() -> None:
    global _checkpointer_cm, _checkpointer, _agent
    if _checkpointer_cm is not None:
        _checkpointer_cm.__exit__(None, None, None)
    _checkpointer_cm = None
    _checkpointer = None
    _agent = None


atexit.register(_close_agent)


def invoke_agent_reply(user_message: str, session_id: str | None = None) -> dict[str, str]:
    thread_id = session_id or str(uuid.uuid4())
    logger.info(f"#==== thread_id: {thread_id}")
    invoke_input = {
        "messages": [
            {"role": "user", "content": user_message}
        ],
    }
    invoke_config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [langfuse_handler],
    }
    try:
        response = get_agent().invoke(invoke_input, config=invoke_config)
    except OperationalError:
        # Rebuild broken DB checkpointer connection once and retry.
        logger.exception("Checkpoint connection failed, rebuilding agent and retrying.")
        _close_agent()
        response = get_agent().invoke(invoke_input, config=invoke_config)
    if isinstance(response, dict):
        messages = response.get("messages", [])
        if messages:
            reply = str(messages[-1].content)
        else:
            reply = str(response)
    else:
        reply = str(response.content)
    return {"session_id": thread_id, "reply": reply}


def main() -> None:
    result = invoke_agent_reply("请问这周新能源车企推出了哪些新车型？")
    safe_print(result["reply"])


if __name__ == "__main__":
    main()
    print("Finished")