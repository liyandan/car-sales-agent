# flake8: noqa: E501
# pylint: disable=line-too-long

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_PRIMARY_MODEL = "MiniMax-M2.7"
DEFAULT_BACKUP_MODEL = "deepseek-v3-2-251201"
DEFAULT_PRIMARY_BASE_URL = "https://api.minimaxi.com/v1"
DEFAULT_BACKUP_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_PRIMARY_API_KEY = ("sk-cp-nW3g6GedoBqZX7yfxnBu1otI6l8-xRjig0ei5mrW7YAv7jBd3pwlaZXwratNNeX9ehJMvA5OH3zNU__h-ptx54f9VptqbN-CWkYK1ni-mZUeo7NuKTNX-SI")
DEFAULT_BACKUP_API_KEY = "7b234522-ff4d-480a-8ffa-730b51aafa24"


class LLMRouterConfig(BaseModel):
    primary_model: str = Field(default=DEFAULT_PRIMARY_MODEL)
    backup_model: str = Field(default=DEFAULT_BACKUP_MODEL)
    primary_base_url: str = Field(default=DEFAULT_PRIMARY_BASE_URL)
    backup_base_url: str = Field(default=DEFAULT_BACKUP_BASE_URL)
    primary_api_key: str = Field(default=DEFAULT_PRIMARY_API_KEY)
    backup_api_key: str = Field(default=DEFAULT_BACKUP_API_KEY)

    @classmethod
    def from_env(cls) -> "LLMRouterConfig":
        """Build config from environment variables with safe fallbacks."""
        load_dotenv(ENV_PATH)
        return cls(
            primary_model=os.getenv("LLM_PRIMARY_MODEL", DEFAULT_PRIMARY_MODEL),
            backup_model=os.getenv("LLM_BACKUP_MODEL", DEFAULT_BACKUP_MODEL),
            primary_base_url=os.getenv(
                "LLM_PRIMARY_BASE_URL",
                DEFAULT_PRIMARY_BASE_URL,
            ),
            backup_base_url=os.getenv(
                "LLM_BACKUP_BASE_URL",
                DEFAULT_BACKUP_BASE_URL,
            ),
            primary_api_key=os.getenv("LLM_PRIMARY_API_KEY", DEFAULT_PRIMARY_API_KEY),
            backup_api_key=os.getenv("LLM_BACKUP_API_KEY", DEFAULT_BACKUP_API_KEY),
        )


def load_llm_router_config() -> LLMRouterConfig:
    """
    Placeholder for loading LLM routing config.
    Later this can be sourced from env vars, config files, or remote config.
    """
    return LLMRouterConfig.from_env()
