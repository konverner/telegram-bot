from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Message(BaseModel):  # noqa: D101
    id: int
    chat_id: int
    role: str
    content: str
    created_at: datetime


class User(BaseModel):  # noqa: D101
    id: int
    name: str


class Chat(BaseModel):  # noqa: D101
    id: int
    user_id: int
    name: Optional[str] = None


class ModelConfig(BaseModel):  # noqa: D101
    model_name: Optional[str] = None
    provider: Optional[str] = None
    max_input_length: Optional[int] = None
    max_tokens: Optional[int] = None
    chat_history_limit: int = 10
    temperature: float = 0.5
    stream: Optional[bool] = False
    system_prompt: Optional[str] = None


class ModelResponse(BaseModel):  # noqa: D101
    response_content: str
    config: ModelConfig
