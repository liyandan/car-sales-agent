import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

try:
    from common import logger
except ModuleNotFoundError:
    # Support running as: python car-sales-agent/agent.py
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from common import logger


def _mask_secret(secret: str) -> str:
    if not secret:
        return "<empty>"
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"


def create_llm():
    """Create and return the configured chat model instance."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    loaded = load_dotenv(env_path)

    llm_model_base_url = os.getenv("ANTHROPIC_BASE_URL", "")
    llm_model_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    llm_primary_model = os.getenv("LLM_PRIMARY_MODEL", "")

    logger.info("[LLM_Factory] .env path: %s", env_path)
    logger.info("[LLM_Factory] .env loaded: %s", loaded)
    logger.info("[LLM_Factory] LLM_PRIMARY_MODEL: %s", llm_primary_model or "<empty>")
    logger.info("[LLM_Factory] ANTHROPIC_BASE_URL: %s", llm_model_base_url or "<empty>")
    logger.info("[LLM_Factory] ANTHROPIC_API_KEY: %s", _mask_secret(llm_model_api_key))

    return init_chat_model(
        model=llm_primary_model,
        base_url=llm_model_base_url,
        api_key=llm_model_api_key,
        model_provider="anthropic",
        temperature=0.6,
    )
