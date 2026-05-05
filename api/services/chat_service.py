from agents import generate_reply
from api.models import load_llm_router_config


class ChatService:
    def __init__(self) -> None:
        self.llm_config = load_llm_router_config()

    def chat(self, user_message: str) -> str:
        # Current implementation still uses local agent logic.
        # llm_config is prepared for future primary/backup model routing.
        _ = self.llm_config
        return generate_reply(user_message)
