from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import importlib.util
from pathlib import Path
from typing import Optional
import sys
import uuid
from pydantic import BaseModel, Field

from api import api_router
from common import logger
from common.schemas import HealthResponse

AGENT_FILE = Path(__file__).resolve().parent / "car-sales-agent" / "agent.py"
agent_module_dir = str(AGENT_FILE.parent)
if agent_module_dir not in sys.path:
    sys.path.insert(0, agent_module_dir)
_agent_spec = importlib.util.spec_from_file_location("car_sales_agent_runtime", AGENT_FILE)
if _agent_spec is None or _agent_spec.loader is None:
    raise RuntimeError(f"Failed to load agent module from {AGENT_FILE}")
_agent_module = importlib.util.module_from_spec(_agent_spec)
_agent_spec.loader.exec_module(_agent_module)
invoke_agent_reply = _agent_module.invoke_agent_reply


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User input message.")
    session_id: Optional[str] = Field(default=None, description="Conversation session id.")


class AgentChatResponse(BaseModel):
    session_id: str
    reply: str


def ensure_uuid_session_id(session_id: Optional[str]) -> str:
    if not session_id:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(session_id))
    except ValueError:
        return str(uuid.uuid4())


app = FastAPI(
    title="Car Sales Agent API",
    description="A basic FastAPI service for the car-sales-agent project.",
    version="0.1.0",
)

# Allow frontend pages served from another origin to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    logger.info("Received request at root endpoint")
    return {
        "message": "你好，我是一个二手车销售顾问，我可以帮助你找到适合你的二手车。"
    }


@app.get("/health")
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/agent-chat", response_model=AgentChatResponse)
def agent_chat(payload: AgentChatRequest) -> AgentChatResponse:
    safe_session_id = ensure_uuid_session_id(payload.session_id)
    logger.info(f"#==== session_id: {safe_session_id}")
    logger.info(f"#==== message: {payload.message}")
    result = invoke_agent_reply(payload.message, safe_session_id)
    return AgentChatResponse(**result)


app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
