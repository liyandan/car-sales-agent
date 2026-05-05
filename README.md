# Car Sales Agent

二手车销售智能体，基于 FastAPI + LangGraph + deepagents 构建。作为二手车销售顾问助手，回答用户关于车辆状况、费用、来源等问题。

## 功能特性

- **智能问答**：理解用户需求，提供专业的二手车咨询
- **技能系统**：模块化技能库，支持车辆状况分析、费用计算、车辆来源查询等
- **会话管理**：基于 PostgreSQL 的状态持久化，支持多会话并发
- **网络搜索**：集成 Tavily 搜索，获取最新行业资讯

## 技术栈

- **框架**：FastAPI + LangGraph + deepagents
- **大模型**：支持 Anthropic API 兼容模型（配置于 `car-sales-agent/.env`）
- **状态存储**：PostgreSQL（LangGraph Checkpoint）
- **日志**：结构化日志，记录到 `logs/app.log`

## 项目结构

```
car-sales-agent/
├── main.py                      # FastAPI 入口
├── car-sales-agent/
│   ├── agent.py                 # 核心 Agent（deepagents + LangGraph）
│   └── LLM_Factory.py           # LLM 初始化
├── api/                         # API 路由层
│   ├── routers/                 # 路由实现
│   └── services/                # 业务逻辑
├── common/                      # 公共模块
│   ├── logger.py                # 日志模块
│   └── schemas.py               # Pydantic 模型
├── skills/                      # 技能模块
│   ├── explaining-car-condition/
│   ├── explaining-car-costs/
│   └── explaining-car-source/
└── frontend/                     # 前端静态页面
```

## 快速开始

### 环境要求

- Python 3.12+
- PostgreSQL（用于状态持久化）

### 安装依赖

```bash
pip install -e .
```

### 配置

创建 `car-sales-agent/.env` 文件：

```env
# LLM 配置
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_BASE_URL=https://api.anthropic.com
LLM_PRIMARY_MODEL=claude-sonnet-4-20250514

# PostgreSQL 配置（LangGraph Checkpoint）
CHECKPOINT_DB_NAME=langgraph
CHECKPOINT_DB_USER=langgraph_user
CHECKPOINT_DB_PASSWORD=your_password
CHECKPOINT_DB_HOST=your_host
CHECKPOINT_DB_PORT=5432

# 可选：Tavily 搜索
TAVILY_API_KEY=your_tavily_key
```

### 运行

```bash
python main.py
```

服务启动后访问 `http://localhost:8000`

## API 接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 健康检查，返回欢迎信息 |
| `/health` | GET | 服务健康状态 |
| `/agent-chat` | POST | 与智能体对话 |
| `/chat` | POST | 聊天接口 |

### 对话示例

```bash
curl -X POST http://localhost:8000/agent-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我找一辆性价比高的二手车", "session_id": "可选的会话ID"}'
```

## 技能系统

项目包含三个核心技能模块：

- **explaining-car-condition**：车辆状况分析与说明
- **explaining-car-costs**：车辆费用计算与预估
- **explaining-car-source**：车辆来源查询

每个技能目录下包含 `SKILL.md` 使用指南和 `scripts/` 辅助脚本。

## 日志

日志文件位于 `logs/app.log`，采用滚动策略：

- 单文件最大 100MB
- 保留最近 3 天的日志
