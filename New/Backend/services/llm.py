# Backend/services/llm.py
import asyncio
from openai import AsyncOpenAI
from Backend.config.settings import LLM_API_URL

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(base_url=LLM_API_URL, api_key="sk-local")
        self.is_active = True # Assumed active as it's started via .bat

    async def stream_chat(self, messages, temperature=0.7, **kwargs):
        """Streams response from llama-server."""
        extra_body = {
            "cache_prompt": True,
            "samplers": ["dry", "top_k", "top_p", "min_p", "temperature"],
            "dry_multiplier": 0.8,
            "dry_base": 1.75,
            "dry_allowed_length": 2,
            "min_p": 0.05,
            "repeat_penalty": 1.1
        }
        
        try:
            stream = await self.client.chat.completions.create(
                model="custom-model",
                messages=messages,
                temperature=temperature,
                stream=True,
                extra_body=extra_body,
                stop=kwargs.get("stop", [])
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"[LLM Error: {e}]"

llm_service = LLMService()
