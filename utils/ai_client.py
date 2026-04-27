import abc
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any
from config.settings import settings

logger = logging.getLogger("AIClient")

class BaseAIClient(abc.ABC):
    """
    Abstract base class for Async AI Clients.
    Supports single completion and streaming.
    """
    def __init__(self, model: str):
        self.model = model

    @abc.abstractmethod
    async def acomplete(self, prompt: str, system_prompt: Optional[str] = None, api_key: Optional[str] = None) -> str:
        """Asynchronous completion."""
        pass

    @abc.abstractmethod
    async def astream(self, prompt: str, system_prompt: Optional[str] = None, api_key: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Asynchronous streaming."""
        pass

class GeminiClient(BaseAIClient):
    def __init__(self, model: str = settings.gemini_model):
        super().__init__(model)
        self._clients = {} # Cache clients by API key

    def _get_client(self, api_key: str):
        if api_key not in self._clients:
            from google import genai
            self._clients[api_key] = genai.Client(api_key=api_key)
        return self._clients[api_key]

    async def acomplete(self, prompt: str, system_prompt: Optional[str] = None, api_key: Optional[str] = None) -> str:
        if not api_key:
            api_key = settings.gemini_api_key
            
        client = self._get_client(api_key)
        from google.genai import types
        
        contents = []
        if system_prompt:
             contents.append(types.Content(role="user", parts=[types.Part.from_text(text=f"System Instruction:\n{system_prompt}")]))
             contents.append(types.Content(role="model", parts=[types.Part.from_text(text="Understood.")]))
        
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=contents
        )
        return response.text

    async def astream(self, prompt: str, system_prompt: Optional[str] = None, api_key: Optional[str] = None) -> AsyncGenerator[str, None]:
        if not api_key:
            api_key = settings.gemini_api_key
            
        client = self._get_client(api_key)
        from google.genai import types
        
        contents = []
        if system_prompt:
             contents.append(types.Content(role="user", parts=[types.Part.from_text(text=f"System Instruction:\n{system_prompt}")]))
             contents.append(types.Content(role="model", parts=[types.Part.from_text(text="Understood.")]))
        
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        async for chunk in await client.aio.models.generate_content_stream(
            model=self.model,
            contents=contents
        ):
            if chunk.text:
                yield chunk.text

class GroqClient(BaseAIClient):
    def __init__(self, model: str = settings.groq_model):
        super().__init__(model)
        self._clients = {} # Cache clients by API key

    def _get_client(self, api_key: str):
        if api_key not in self._clients:
            from groq import AsyncGroq
            self._clients[api_key] = AsyncGroq(api_key=api_key)
        return self._clients[api_key]

    async def acomplete(self, prompt: str, system_prompt: Optional[str] = None, api_key: Optional[str] = None) -> str:
        if not api_key:
            api_key = settings.groq_api_key
            
        client = self._get_client(api_key)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        completion = await client.chat.completions.create(
            messages=messages,
            model=self.model,
        )
        return completion.choices[0].message.content

    async def astream(self, prompt: str, system_prompt: Optional[str] = None, api_key: Optional[str] = None) -> AsyncGenerator[str, None]:
        if not api_key:
            api_key = settings.groq_api_key
            
        client = self._get_client(api_key)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = await client.chat.completions.create(
            messages=messages,
            model=self.model,
            stream=True
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
