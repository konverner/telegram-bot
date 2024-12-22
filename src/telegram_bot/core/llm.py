from typing import Any, Optional, Union

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_fireworks import ChatFireworks
from langchain_openai import ChatOpenAI
from PIL.Image import Image
from pydantic import BaseModel

from telegram_bot.core.utils import image_to_base64


class ModelConfig(BaseModel):
    """Model configuration for the language model"""

    model_name: Optional[str] = None
    provider: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.5
    stream: Optional[bool] = True
    system_prompt: Optional[str] = None


class LLM:
    def __init__(self, config: ModelConfig):  # noqa: D107
        self.config = config
        self.clients = {"openai": ChatOpenAI, "fireworksai": ChatFireworks}

    def invoke(
        self, user_input: str, config: Optional[ModelConfig] = None, image: Optional[Image] = None
    ) -> Union[str, Any]:
        """Run the model with the given chat history and configuration"""

        if config is None and self.config is not None:
            config = self.config
        else:
            raise ValueError("Model configuration is required")

        provider = config.provider
        if provider not in self.clients:
            raise ValueError(f"Invalid provider: {provider}. Available providers: {', '.join(self.clients.keys())}")

        client = self.clients[provider](
            model_name=config.model_name, max_tokens=config.max_tokens, temperature=config.temperature
        )

        messages = [
            SystemMessage(content=[{"type": "text", "text": config.system_prompt}]),
            HumanMessage(content=[{"type": "text", "text": user_input}]),
        ]

        # Handle the image if provided
        if image:
            message = HumanMessage(content=[{"type": "text", "text": "Received the following image(s):"}])
            image_base64 = image_to_base64(image)
            message.content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                }
            )
            messages.append(message)

        if config.stream:
            return client.stream(messages)
        else:
            response = client.invoke(messages)
            return response.content.replace("<end_of_turn>", "")
