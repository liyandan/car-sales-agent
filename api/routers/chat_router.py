from fastapi import APIRouter

from api.services import ChatService
from common.schemas import ChatRequest, ChatResponse

router = APIRouter()
chat_service = ChatService()


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    reply = chat_service.chat(payload.message)
    return ChatResponse(reply=reply)
