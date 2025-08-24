from typing import Dict, List, Optional, Type

from openai import OpenAI
from PIL.Image import Image
from pydantic import BaseModel

from .schemas import ModelConfig
from .utils import image_to_base64


class OpenAiClient:
    """
    Minimal OpenAI client wrapper for structured data extraction.
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = OpenAI()
        print(f"Initialized OpenAiClient with model {config.model_name} and provider {config.provider}")

    def _build_messages(self, system_prompt: str, user_text: Optional[str], image: Optional[Image]) -> list[dict]:
        messages = [{"role": "system", "content": system_prompt}]

        content = []
        if user_text:
            content.append({"type": "input_text", "text": user_text})

        if image:
            image_base64 = image_to_base64(image)
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{image_base64}",
                }
            )

        messages.append({"role": "user", "content": content})
        return messages

    def _history_to_messages(
        self,
        system_prompt: str,
        history: List[Dict[str, str]],
        image: Optional[Image] = None,
    ) -> List[Dict]:
        messages: List[Dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        for m in history:
            role = m.get("role", "user")
            text = m.get("content", "") or ""
            messages.append({"role": role, "content": [{"type": "input_text", "text": text}]})

        if image is not None:
            image_base64 = image_to_base64(image)
            if messages and messages[-1]["role"] == "user" and isinstance(messages[-1].get("content"), list):
                messages[-1]["content"].append(
                    {"type": "input_image", "image_url": f"data:image/png;base64,{image_base64}"}
                )
            else:
                messages.append(
                    {
                        "role": "user",
                        "content": [{"type": "input_image", "image_url": f"data:image/png;base64,{image_base64}"}],
                    }
                )
        return messages

    def chat(
        self,
        system_prompt: str,
        user_text: Optional[str] = None,
        *,
        messages: Optional[List[Dict[str, str]]] = None,
        image: Optional[Image] = None,
        config: Optional[ModelConfig] = None,
    ) -> str:
        """
        General chat call. Accepts either a single user_text (with optional image) or a full chat history.
        Returns plain text.
        """
        cfg = config or self.config
        if messages is not None:
            input_messages = self._history_to_messages(system_prompt, messages, image=image)
        else:
            input_messages = self._build_messages(system_prompt, user_text, image)

        try:
            response = self.client.responses.create(
                model=cfg.model_name,
                input=input_messages,
                temperature=cfg.temperature,
            )
            # Prefer the convenience field if present
            text = getattr(response, "output_text", None)
            if isinstance(text, str) and text.strip():
                return text

            # Fallback extraction if SDK version doesn't expose output_text
            try:
                # response.output is a list of items; each has content with type 'output_text'
                parts = []
                for item in getattr(response, "output", []) or []:
                    for c in getattr(item, "content", []) or []:
                        if getattr(c, "type", None) == "output_text" and getattr(c, "text", None):
                            parts.append(c.text)
                return "\n".join(parts).strip()
            except Exception:
                return ""
        except Exception:
            return ""

    def invoke(
        self,
        user_text: str,
        *,
        image: Optional[Image] = None,
        system_prompt: Optional[str] = None,
        config: Optional[ModelConfig] = None,
    ) -> str:
        """
        Backwards-compatible single-turn call used by handlers/service.
        """
        return self.chat(system_prompt or "", user_text=user_text, image=image, config=config)

    def get_response(
        self,
        user_input: str,
        pydantic_schema: Type[BaseModel],
        system_prompt: str,
        image: Optional[Image] = None,
        config: Optional[ModelConfig] = None,
    ) -> BaseModel:
        """
        Get a structured response from the LLM based on a Pydantic schema using responses.parse.
        """
        cfg = config or self.config
        messages = self._build_messages(system_prompt, user_input, image)

        try:
            response = self.client.responses.parse(
                model=cfg.model_name, input=messages, text_format=pydantic_schema, temperature=cfg.temperature
            )

            return response.output_parsed

        except Exception as e:
            return pydantic_schema(success=False, data=[], error_message=f"OpenAiClient processing failed: {e}")
