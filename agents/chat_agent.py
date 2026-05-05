def generate_reply(user_message: str) -> str:
    """Generate a simple sales reply for now."""
    cleaned = user_message.strip()
    if not cleaned:
        return "你好，请告诉我你的预算、品牌偏好和用车场景，我来帮你推荐二手车。"
    return f"收到你的需求：{cleaned}。请告诉我预算区间，我将为你筛选合适的二手车。"
