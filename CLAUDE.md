# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Car sales AI agent using **FastAPI** + **LangGraph** + **deepagents** framework. The agent acts as a used-car sales specialist, answering questions about car conditions, costs, and sourcing.

## Tech Stack

- **API**: FastAPI (async web framework)
- **Agent Framework**: deepagents + LangGraph (stateful agent with checkpointing)
- **LLM**: Configurable via `car-sales-agent/.env` (supports Anthropic-compatible APIs)
- **Checkpoint Storage**: PostgreSQL via `ShallowPostgresSaver`
- **Web Search**: Tavily (optional, via `TAVILY_API_KEY`)
- **Logging**: Rotating file handler (`logs/app.log`), 100MB max, 3-day retention

## Architecture

```
main.py                     # FastAPI entry, loads agent via dynamic import
car-sales-agent/
  agent.py                  # Core agent: deepagents + LangGraph + middleware stack
  LLM_Factory.py            # LLM initialization from .env
api/                        # FastAPI routes
  routers/chat_router.py    # /chat endpoints
  services/chat_service.py   # Business logic
common/
  logger.py                 # Module-level singleton logger
  schemas.py                # Pydantic models
skills/                     # Skill modules (SKILL.md + scripts/)
  explaining-car-condition/
  explaining-car-costs/
  explaining-car-source/
frontend/                   # Static assets (HTML/JS/CSS)
```

## Agent Middleware Stack

Agent initialization in `agent.py` uses layered middleware:

1. **SkillsMiddleware** - Routes to skill modules in `/skills`; skill scripts executed via `shell_tool` (RobustShellTool) using real paths from `skills_real_root`
2. **MemoryMiddleware** - Loads `/AGENTS.md` for persistent agent memory
3. **CustomTodoListMiddleware** - Overrides `write_todos` tool prompts
4. **Checkpointing**: PostgreSQL via `ShallowPostgresSaver` with automatic reconnection on `OperationalError`

## Running

```bash
# Start API server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Key Conventions

- **Agent invocation**: `invoke_agent_reply(message, session_id)` in `agent.py` — handles checkpoint-aware LangGraph execution
- **Session IDs**: Validated as UUIDs; new UUID generated if invalid/missing
- **Shell tool**: Custom `RobustShellTool` captures stderr alongside stdout for debugging
- **Skills**: Located at absolute paths under `skills_real_root`; called via shell with `venv_python`
- **Environment**: `car-sales-agent/.env` for agent LLM config; `.env.online` for deployment vars
