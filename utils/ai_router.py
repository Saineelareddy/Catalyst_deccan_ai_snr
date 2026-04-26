import asyncio
import logging
from typing import Type, TypeVar, Any, Optional, AsyncGenerator, List
from pydantic import BaseModel

from config.settings import settings
from utils.ai_client import GeminiClient, GroqClient
from utils.ai_cache import get_cache_key, get_cached_response, set_cached_response
from utils.ai_structured import generate_schema_prompt, parse_structured_response
from utils.key_manager import key_manager

logger = logging.getLogger("AIRouter")

T = TypeVar('T', bound=BaseModel)

class AIRouter:
    """
    High-Performance AI Orchestration Layer.
    Implements:
    - Parallel 'Racing' across multiple API keys (Promise.all equivalent)
    - Real-time Streaming
    - Smart Key Rotation & Rate-limit awareness
    - Robust Caching
    """
    def __init__(self):
        self.clients = {
            "gemini": GeminiClient(),
            "groq": GroqClient()
        }

    async def acomplete(self, 
                       prompt: str, 
                       system_prompt: Optional[str] = None, 
                       response_model: Optional[Type[T]] = None, 
                       parallel_count: int = 3,
                       bypass_cache: bool = False) -> str | T:
        """
        Asynchronously completes a request, racing multiple API keys in parallel.
        """
        if response_model:
            schema_instruction = generate_schema_prompt(response_model)
            system_prompt = f"{system_prompt}\n\n{schema_instruction}" if system_prompt else schema_instruction

        provider = settings.ai_provider
        client = self.clients.get(provider)
        if not client:
            raise ValueError(f"Provider {provider} not supported.")

        # 1. Cache Check
        cache_key = get_cache_key(provider, client.model, prompt, system_prompt)
        if not bypass_cache:
            cached = get_cached_response(cache_key)
            if cached:
                logger.info("Cache hit.")
                return parse_structured_response(cached, response_model) if response_model else cached

        # 2. Parallel Racing (The "Promise.all" equivalent logic)
        keys = key_manager.get_best_keys(provider, count=parallel_count)
        if not keys:
            raise RuntimeError(f"No available keys for {provider}")

        logger.info(f"Racing {len(keys)} keys in parallel for {provider}...")
        
        tasks = []
        for key in keys:
            # Explicitly create tasks from coroutines
            tasks.append(asyncio.create_task(self._execute_with_key(client, prompt, system_prompt, key, provider)))

        # Use wait with FIRST_COMPLETED to return as soon as one key succeeds
        done, pending = await asyncio.wait(
            tasks, 
            return_when=asyncio.FIRST_COMPLETED
        )

        result = None
        exception = None

        for task in done:
            try:
                key, response_text = task.result()
                result = response_text
                key_manager.report_success(provider, key)
                break # Take the first successful result
            except Exception as e:
                exception = e
                # The _execute_with_key already reports failure to key_manager

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

        if result is None:
            if exception:
                raise exception
            raise RuntimeError("All parallel tasks failed.")

        # 3. Cache & Parse
        if not bypass_cache:
            set_cached_response(cache_key, result)

        if response_model:
            return parse_structured_response(result, response_model)
        return result

    async def _execute_with_key(self, client, prompt, system_prompt, key, provider):
        """Helper to execute and report to key manager."""
        try:
            resp = await client.acomplete(prompt, system_prompt, api_key=key)
            return key, resp
        except Exception as e:
            key_manager.report_failure(provider, key, str(e))
            raise e

    async def astream(self, 
                     prompt: str, 
                     system_prompt: Optional[str] = None, 
                     provider: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Streams AI response in real-time. 
        Note: Parallel racing is not typically used for streaming to avoid multiple charges/streams.
        """
        provider = provider or settings.ai_provider
        client = self.clients.get(provider)
        
        # Get the single best key
        keys = key_manager.get_best_keys(provider, count=1)
        if not keys:
            raise RuntimeError(f"No available keys for {provider}")
        
        key = keys[0]
        try:
            async for chunk in client.astream(prompt, system_prompt, api_key=key):
                yield chunk
            key_manager.report_success(provider, key)
        except Exception as e:
            key_manager.report_failure(provider, key, str(e))
            raise e

    def complete(self, *args, **kwargs) -> Any:
        """Synchronous wrapper for acomplete for backward compatibility."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(self.acomplete(*args, **kwargs))
        else:
            # Already in a loop, we can't use asyncio.run. 
            # This case is rare in the current Streamlit setup but good for robustness.
            if loop.is_running():
                # We are in a running loop, we should probably use a different approach
                # but for simplicity in this sync wrapper:
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self.acomplete(*args, **kwargs))
            return asyncio.run(self.acomplete(*args, **kwargs))

# Global router instance
ai_router = AIRouter()
