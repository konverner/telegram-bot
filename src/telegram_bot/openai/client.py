from typing import Any, Optional, Union

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from PIL.Image import Image

from .schemas import Message, ModelConfig
from .utils import image_to_base64


class LLM:
    def __init__(
        self, config: ModelConfig, system_prompt: Optional[str] = None
    ):  # noqa: D107
        self.config = config
        self.system_prompt = system_prompt

    def invoke(
        self,
        chat_history: list[Message],
        config: Optional[ModelConfig] = None,
        image: Optional[Image] = None,
    ) -> Union[str, Any]:
        """Run the model with the given chat history and configuration"""

        if config is None and self.config is not None:
            config = self.config
        else:
            raise ValueError("Model configuration is required")

        llm_client = ChatOpenAI(
            model_name=config.model_name,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )

        chat_history = chat_history[-config.chat_history_limit :]
        role_message_map = {"user": HumanMessage, "assistant": AIMessage}
        messages = [
            role_message_map[message.role](
                content=[{"type": "text", "text": message.content}]
            )
            for message in chat_history
            if message.role in role_message_map
        ]

        # If system prompt is provided, add it to the messages
        if self.system_prompt:
            messages.insert(
                0, SystemMessage(content=[{"type": "text", "text": self.system_prompt}])
            )

        # Handle the image if provided
        if image:
            message = HumanMessage(
                content=[{"type": "text", "text": "Received the following image(s):"}]
            )
            image_base64 = image_to_base64(image)
            message.content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                }
            )
            messages.append(message)

        if config.stream:
            return llm_client.stream(messages)
        else:
            response = llm_client.invoke(messages)
            return response
