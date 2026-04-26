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
    Resilient AI Orchestration Layer.
    Strategy: Sequential key rotation (avoids asyncio.CancelledError from parallel racing).
    - Tries each key one by one until one succeeds.
    - On full provider exhaustion, automatically falls back to the other provider.
    - Supports caching and real-time streaming.
    """
    def __init__(self):
        self.clients = {
            "gemini": GeminiClient(),
            "groq": GroqClient()
        }

    def _get_provider_order(self) -> List[str]:
        """Returns [primary, fallback] provider list."""
        primary = settings.ai_provider
        fallback = "groq" if primary == "gemini" else "gemini"
        providers = [primary]
        if key_manager.keys.get(fallback):
            providers.append(fallback)
        return providers

    async def acomplete(self,
                        prompt: str,
                        system_prompt: Optional[str] = None,
                        response_model: Optional[Type[T]] = None,
                        parallel_count: int = 3,   # kept for API compat, unused
                        max_attempts: int = 3,
                        bypass_cache: bool = False) -> str | T:
        """
        Complete a request using sequential key rotation + cross-provider fallback.
        Sequential approach eliminates asyncio.CancelledError from parallel task cancellation.
        """
        if response_model:
            schema_instruction = generate_schema_prompt(response_model)
            system_prompt = f"{system_prompt}\n\n{schema_instruction}" if system_prompt else schema_instruction

        primary_provider = settings.ai_provider

        # Cache check
        primary_client = self.clients.get(primary_provider)
        if primary_client:
            cache_key = get_cache_key(primary_provider, primary_client.model, prompt, system_prompt)
            if not bypass_cache:
                cached = get_cached_response(cache_key)
                if cached:
                    logger.info("Cache hit.")
                    return parse_structured_response(cached, response_model) if response_model else cached
        else:
            cache_key = None

        last_exception = None

        for provider in self._get_provider_order():
            client = self.clients.get(provider)
            if not client:
                continue

            if provider != primary_provider:
                logger.warning(f"⚡ Falling back to {provider.upper()} — Gemini exhausted.")

            # Get all available keys for this provider
            all_keys = key_manager.get_best_keys(provider, count=max(10, max_attempts * 3))
            if not all_keys:
                logger.error(f"[{provider}] No keys available. Skipping.")
                continue

            for key in all_keys:
                try:
                    logger.info(f"[{provider}] Trying key {key[:8]}...")
                    resp = await client.acomplete(prompt, system_prompt, api_key=key)
                    key_manager.report_success(provider, key)

                    # Cache the raw response
                    if cache_key and not bypass_cache:
                        set_cached_response(cache_key, resp)

                    if response_model:
                        return parse_structured_response(resp, response_model)
                    return resp

                except asyncio.CancelledError:
                    # Re-raise immediately — this means Streamlit is shutting down the script
                    # DO NOT try next key, the entire context is being torn down
                    logger.warning(f"[{provider}] Request was cancelled (Streamlit rerun). Aborting.")
                    raise

                except Exception as e:
                    err_str = str(e)
                    key_manager.report_failure(provider, key, err_str)
                    last_exception = e
                    logger.warning(f"[{provider}] Key {key[:8]}... failed: {err_str[:100]}")
                    # Continue to next key

            logger.error(f"[{provider}] All keys exhausted.")

        # All providers and all keys failed
        raise RuntimeError(
            f"ALL PROVIDERS EXHAUSTED. Last error: {last_exception}. "
            "Check your API keys and rate limits in Streamlit Secrets."
        )

    async def astream(self,
                      prompt: str,
                      system_prompt: Optional[str] = None,
                      provider: Optional[str] = None,
                      max_attempts: int = 10) -> AsyncGenerator[str, None]:
        """
        Streams AI response. Rotates keys on 429/failure.
        """
        provider = provider or settings.ai_provider
        client = self.clients.get(provider)
        if not client:
            raise ValueError(f"Provider {provider} not supported.")

        all_keys = key_manager.get_best_keys(provider, count=max_attempts)
        last_exception = None

        for key in all_keys:
            try:
                logger.info(f"[{provider}] Streaming with key {key[:8]}...")
                async for chunk in client.astream(prompt, system_prompt, api_key=key):
                    yield chunk
                key_manager.report_success(provider, key)
                return
            except Exception as e:
                logger.warning(f"[{provider}] Stream key {key[:8]}... failed: {str(e)[:100]}")
                key_manager.report_failure(provider, key, str(e))
                last_exception = e

        if last_exception:
            raise last_exception
        raise RuntimeError(f"All streaming attempts failed for {provider}.")

    def complete(self, *args, **kwargs) -> Any:
        """Synchronous wrapper for acomplete."""
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(self.acomplete(*args, **kwargs))
            else:
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    return loop.run_until_complete(self.acomplete(*args, **kwargs))
                return asyncio.run(self.acomplete(*args, **kwargs))
        except asyncio.CancelledError:
            logger.warning("Sync operation cancelled.")
            return None


# Global router instance
ai_router = AIRouter()
