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
                       max_attempts: int = 3,
                       bypass_cache: bool = False) -> str | T:
        """
        Asynchronously completes a request.
        - Races multiple API keys in parallel per provider.
        - On full exhaustion of primary provider, automatically falls back
          to the secondary provider (Gemini → Groq or Groq → Gemini).
        """
        if response_model:
            schema_instruction = generate_schema_prompt(response_model)
            system_prompt = f"{system_prompt}\n\n{schema_instruction}" if system_prompt else schema_instruction

        primary_provider = settings.ai_provider
        # Build the ordered list of providers to try
        all_providers = [primary_provider]
        fallback = "groq" if primary_provider == "gemini" else "gemini"
        if key_manager.keys.get(fallback):  # only add if we have fallback keys
            all_providers.append(fallback)

        for provider in all_providers:
            client = self.clients.get(provider)
            if not client:
                continue

            # Cache check (only on primary provider)
            if provider == primary_provider:
                cache_key = get_cache_key(provider, client.model, prompt, system_prompt)
                if not bypass_cache:
                    cached = get_cached_response(cache_key)
                    if cached:
                        logger.info("Cache hit.")
                        return parse_structured_response(cached, response_model) if response_model else cached
            else:
                cache_key = None
                logger.warning(f"⚡ PRIMARY PROVIDER EXHAUSTED — falling back to {provider.upper()}")

            last_exception = None
            succeeded = False

            for attempt in range(max_attempts):
                keys = key_manager.get_best_keys(provider, count=parallel_count)
                if not keys:
                    logger.error(f"No available keys for {provider} on attempt {attempt+1}")
                    break

                logger.info(f"[{provider}] Attempt {attempt+1}/{max_attempts}: Racing {len(keys)} keys...")

                try:
                    key, response_text = await self._race_keys(
                        client, prompt, system_prompt, keys, provider
                    )
                    key_manager.report_success(provider, key)
                    if cache_key and not bypass_cache:
                        set_cached_response(cache_key, response_text)
                    if response_model:
                        return parse_structured_response(response_text, response_model)
                    return response_text
                except Exception as e:
                    last_exception = e
                    logger.warning(f"[{provider}] Attempt {attempt+1} failed: {str(e)[:120]}")

            logger.error(f"[{provider}] ALL {max_attempts} attempts failed. Moving to next provider...")

        # All providers exhausted
        raise RuntimeError(
            f"ALL PROVIDERS EXHAUSTED. Last error: {last_exception}. "
            "Check your API keys and rate limits."
        )

    async def _race_keys(self, client, prompt, system_prompt, keys, provider):
        """
        Race a batch of API keys in parallel.
        Returns (key, response_text) on first success, or raises the last exception.
        Properly cleans up cancelled tasks to prevent CancelledError propagation.
        """
        tasks = {
            asyncio.create_task(
                self._execute_with_key(client, prompt, system_prompt, key, provider),
                name=f"{provider}-{key[:8]}"
            ): key for key in keys
        }

        last_exception = None
        pending = set(tasks.keys())

        try:
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    exc = task.exception() if not task.cancelled() else None
                    if exc is None and not task.cancelled():
                        # ✅ SUCCESS — cancel remaining and clean up safely
                        for t in pending:
                            t.cancel()
                        if pending:
                            await asyncio.gather(*pending, return_exceptions=True)
                        return task.result()
                    else:
                        last_exception = exc or Exception("Task was cancelled")
                        logger.warning(f"[{provider}] Key failed: {str(last_exception)[:120]}")
        except asyncio.CancelledError:
            # If we ourselves get cancelled, clean up children first
            for t in pending:
                t.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            raise

        raise last_exception or Exception(f"All {len(keys)} keys failed for {provider}")

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
                     provider: Optional[str] = None,
                     max_attempts: int = 5) -> AsyncGenerator[str, None]:
        """
        Streams AI response in real-time. 
        Rotates through keys if the stream fails to initialize (e.g. 429).
        """
        provider = provider or settings.ai_provider
        client = self.clients.get(provider)
        if not client:
             raise ValueError(f"Provider {provider} not supported.")

        last_exception = None
        for attempt in range(max_attempts):
            keys = key_manager.get_best_keys(provider, count=1)
            if not keys:
                break
            
            key = keys[0]
            try:
                # We try to start the stream. If it fails here (429), we catch and retry.
                # If it fails MID-STREAM, we might have already yielded data, 
                # so we can't easily retry without duplicate content.
                # However, most 429s happen at the start.
                async for chunk in client.astream(prompt, system_prompt, api_key=key):
                    yield chunk
                
                # If we successfully finished the stream
                key_manager.report_success(provider, key)
                return 
            except Exception as e:
                logger.warning(f"Stream attempt {attempt+1} failed with key: {str(e)[:100]}")
                key_manager.report_failure(provider, key, str(e))
                last_exception = e
                # Continue to next attempt with a new key
        
        if last_exception:
            raise last_exception
        raise RuntimeError(f"All {max_attempts} streaming attempts failed for {provider}.")

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
